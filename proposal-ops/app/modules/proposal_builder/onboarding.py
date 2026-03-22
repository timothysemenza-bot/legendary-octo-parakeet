from __future__ import annotations

import json
import mimetypes
import re
import shutil
import uuid
import zipfile
from datetime import UTC, date, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.config import ARTIFACTS_DIR
from app.modules.opportunity_intake.models import Opportunity
from app.modules.proposal_builder.client_profiles import ClientProfileError, ClientProfileService
from app.modules.proposal_builder.models import (
    ClientBehaviorProfile,
    ClientOnboardingAsset,
    ClientOnboardingPack,
    ClientPlaybook,
    ClientProfile,
)
from app.modules.proposal_builder.schemas import (
    ClientBehaviorProfileArtifact,
    ClientOnboardingAssetResponse,
    ClientOnboardingAssetUpdateRequest,
    ClientOnboardingPackActionRequest,
    ClientOnboardingPackApproveRequest,
    ClientOnboardingPackCreateRequest,
    ClientOnboardingPackResponse,
    ClientOnboardingPackUploadResponse,
    ClientPlaybookUpdateRequest,
    ClientPlaybookResponse,
    OnboardingValidationReport,
)
from app.modules.rfp_parser.document_reader import extract_text_from_upload


CLIENT_ONBOARDING_STORAGE_DIR = ARTIFACTS_DIR / "client_onboarding"
CLIENT_ONBOARDING_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

RUNTIME_CONTENT_ROLE_MAP = {
    "resume": "resume",
    "reference": "reference",
    "insurance": "insurance",
    "certification": "insurance",
    "sample_proposal": "sample_proposal",
    "service_offering": "service_description",
    "approved_content": "generic_content",
}

STANDARD_PROPOSAL_SECTIONS = [
    "Transmittal Letter",
    "Executive Summary",
    "Technical Approach",
    "Management and Staffing Plan",
    "Transition and Mobilization Plan",
    "Past Performance",
    "Pricing and Commercials",
    "Compliance and Attachments",
]
EDITABLE_ASSET_ROLES = {
    "approved_content",
    "brand_asset",
    "certification",
    "form_template",
    "insurance",
    "operational_guidance",
    "playbook_doc",
    "pricing_artifact",
    "proposal_template",
    "reference",
    "resume",
    "sample_proposal",
    "service_offering",
    "unknown",
}


class ClientOnboardingError(RuntimeError):
    pass


def _parse_json(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _dump_json(value: Any) -> str:
    return json.dumps(value, default=str)


def _normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _normalize_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _normalize_space(value).lower()).strip("_")


def _unique_strings(values: list[str] | tuple[str, ...]) -> list[str]:
    ordered: list[str] = []
    for value in values:
        cleaned = _normalize_space(value)
        if cleaned and cleaned not in ordered:
            ordered.append(cleaned)
    return ordered


def _safe_slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    return "-".join(part for part in normalized.split("-") if part)[:80] or "client-onboarding-pack"


def _guess_media_type(filename: str) -> str:
    guessed, _encoding = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def _storage_dir_for_pack(pack_id: str, *parts: str) -> Path:
    target = CLIENT_ONBOARDING_STORAGE_DIR / pack_id
    for part in parts:
        target = target / part
    target.mkdir(parents=True, exist_ok=True)
    return target


def _manifest_asset_roles(manifest: dict[str, Any]) -> dict[str, str]:
    raw = manifest.get("asset_roles", {})
    if not isinstance(raw, dict):
        return {}
    return {_normalize_key(key): str(value).strip() for key, value in raw.items() if str(value).strip()}


def _manifest_profile_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    raw = manifest.get("client", {})
    return raw if isinstance(raw, dict) else {}


def _extract_text_from_file(path: Path) -> str | None:
    try:
        return extract_text_from_upload(path.name, path.read_bytes()).strip() or None
    except RuntimeError:
        return None


def _classify_role(filename: str, *, manifest_roles: dict[str, str]) -> tuple[str, str]:
    normalized_name = _normalize_key(filename)
    suffix = Path(filename).suffix.lower()
    if normalized_name in manifest_roles:
        return manifest_roles[normalized_name], "manifest"

    lowered = filename.lower()
    if any(token in lowered for token in ("playbook", "readme", "shipley", "apmp", "proposal-process")):
        return "playbook_doc", "heuristic"
    if any(token in lowered for token in ("capture", "discovery", "transcript", "meeting", "buyer-notes")):
        return "operational_guidance", "heuristic"
    if any(token in lowered for token in ("logo", "brand", "font", "palette", "style-guide")):
        return "brand_asset", "heuristic"
    if suffix == ".docx" and any(token in lowered for token in ("template", "rfp-shell", "proposal-shell", "response-shell")):
        return "proposal_template", "heuristic"
    if suffix in {".xlsx", ".csv", ".json"} and any(token in lowered for token in ("pricing", "rate-card", "rate_card", "workbook")):
        return "pricing_artifact", "heuristic"
    if suffix in {".xlsx", ".docx", ".pdf"} and any(token in lowered for token in ("form", "attachment", "certification", "certifications", "representation")):
        return "form_template", "heuristic"
    if "resume" in lowered:
        return "resume", "heuristic"
    if any(token in lowered for token in ("reference", "past-performance", "past_performance")):
        return "reference", "heuristic"
    if any(token in lowered for token in ("insurance", "certificate-of-insurance", "coi", "bond")):
        return "insurance", "heuristic"
    if any(token in lowered for token in ("certification", "certified", "license")):
        return "certification", "heuristic"
    if any(token in lowered for token in ("service-offering", "capability", "offering", "service-description")):
        return "service_offering", "heuristic"
    if any(token in lowered for token in ("proposal", "response", "section")) and suffix in {".pdf", ".docx", ".txt", ".md"}:
        return "sample_proposal", "heuristic"
    if suffix in {".txt", ".md", ".docx", ".pdf"}:
        return "approved_content", "heuristic"
    return "unknown", "heuristic"


def _asset_metadata(
    *,
    role: str,
    filename: str,
    manifest: dict[str, Any],
    profile: ClientProfile,
    extracted_text: str | None,
) -> dict[str, Any]:
    playbook = manifest.get("playbook", {}) if isinstance(manifest.get("playbook"), dict) else {}
    metadata: dict[str, Any] = {
        "asset_type": RUNTIME_CONTENT_ROLE_MAP.get(role, role),
        "approval_status": "draft",
        "effective_date": date.today().isoformat(),
        "expiry_date": None,
        "client_tags": [profile.display_name],
        "service_tags": _parse_json(profile.service_tags_json, []),
        "region_tags": _parse_json(profile.region_tags_json, []),
        "source_pack_id": None,
        "source_of_truth": filename,
        "preferred_terminology": playbook.get("preferred_terminology", []),
        "avoid_terminology": playbook.get("avoid_terminology", []),
    }
    if extracted_text:
        metadata["excerpt"] = extracted_text[:600]
    return metadata


class ClientOnboardingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _profile_service(self) -> ClientProfileService:
        return ClientProfileService(self.db)

    def _profile(self, profile_id: str) -> ClientProfile:
        profile = self.db.get(ClientProfile, profile_id)
        if profile is None:
            raise ClientOnboardingError("Client profile not found.")
        return profile

    def _pack(self, pack_id: str) -> ClientOnboardingPack:
        pack = self.db.get(ClientOnboardingPack, pack_id)
        if pack is None:
            raise ClientOnboardingError("Client onboarding pack not found.")
        return pack

    def _playbook_for_pack(self, pack_id: str) -> ClientPlaybook | None:
        stmt = (
            select(ClientPlaybook)
            .where(ClientPlaybook.onboarding_pack_id == pack_id)
            .order_by(ClientPlaybook.version.desc(), ClientPlaybook.updated_at.desc())
        )
        return self.db.scalars(stmt).first()

    def _behavior_profile_for_pack(self, pack_id: str) -> ClientBehaviorProfile | None:
        stmt = select(ClientBehaviorProfile).where(ClientBehaviorProfile.onboarding_pack_id == pack_id)
        return self.db.scalars(stmt).first()

    def _assets_for_pack(self, pack_id: str) -> list[ClientOnboardingAsset]:
        stmt = (
            select(ClientOnboardingAsset)
            .where(ClientOnboardingAsset.onboarding_pack_id == pack_id)
            .order_by(ClientOnboardingAsset.created_at.asc(), ClientOnboardingAsset.source_filename.asc())
        )
        return list(self.db.scalars(stmt))

    def _asset(self, pack_id: str, asset_id: str) -> ClientOnboardingAsset:
        asset = self.db.get(ClientOnboardingAsset, asset_id)
        if asset is None or asset.onboarding_pack_id != pack_id:
            raise ClientOnboardingError("Client onboarding asset not found.")
        return asset

    def _next_pack_version(self, profile_id: str) -> int:
        stmt = select(func.max(ClientOnboardingPack.version)).where(ClientOnboardingPack.client_profile_id == profile_id)
        current = self.db.execute(stmt).scalar_one_or_none()
        return int(current or 0) + 1

    def _find_profile_by_name(self, display_name: str) -> ClientProfile | None:
        stmt = select(ClientProfile).where(func.lower(ClientProfile.display_name) == display_name.lower())
        return self.db.scalars(stmt).first()

    def _ensure_profile(self, *, client_display_name: str, manifest: dict[str, Any]) -> tuple[ClientProfile, bool]:
        profile = self._find_profile_by_name(client_display_name)
        created = False
        manifest_profile = _manifest_profile_payload(manifest)
        if profile is None:
            profile = ClientProfile(
                display_name=client_display_name,
                aliases_json=_dump_json(_unique_strings([str(item) for item in manifest_profile.get("aliases", [])])),
                approved_content_tags_json=_dump_json(
                    _unique_strings([str(item) for item in manifest_profile.get("approved_content_tags", [])])
                ),
                region_tags_json=_dump_json(_unique_strings([str(item) for item in manifest_profile.get("region_tags", [])])),
                service_tags_json=_dump_json(_unique_strings([str(item) for item in manifest_profile.get("service_tags", [])])),
                status="ACTIVE",
                client_environment_status="SETUP_REQUIRED",
            )
            self.db.add(profile)
            self.db.flush()
            created = True
        return profile, created

    def _serialize_validation(self, payload: dict[str, Any] | None) -> OnboardingValidationReport | None:
        if not payload:
            return None
        return OnboardingValidationReport.model_validate(payload)

    def _serialize_asset(self, asset: ClientOnboardingAsset) -> ClientOnboardingAssetResponse:
        return ClientOnboardingAssetResponse(
            id=asset.id,
            onboarding_pack_id=asset.onboarding_pack_id,
            asset_role=asset.asset_role,
            asset_status=asset.asset_status,
            classification_source=asset.classification_source,
            source_filename=asset.source_filename,
            source_path=asset.source_path,
            media_type=asset.media_type,
            extracted_text=asset.extracted_text,
            normalized_metadata=_parse_json(asset.normalized_metadata_json, {}),
            validation_report=self._serialize_validation(_parse_json(asset.validation_report_json, {})),
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )

    def _serialize_playbook(self, playbook: ClientPlaybook | None) -> ClientPlaybookResponse | None:
        if playbook is None:
            return None
        return ClientPlaybookResponse(
            id=playbook.id,
            onboarding_pack_id=playbook.onboarding_pack_id,
            version=playbook.version,
            status=playbook.status,
            title=playbook.title,
            narrative_guidance_md=playbook.narrative_guidance_md,
            structured_rules=ClientBehaviorProfileArtifact.model_validate(_parse_json(playbook.structured_rules_json, {})),
            approved_at=playbook.approved_at,
            created_at=playbook.created_at,
            updated_at=playbook.updated_at,
        )

    def _serialize_pack(self, pack: ClientOnboardingPack) -> ClientOnboardingPackResponse:
        profile = self._profile(pack.client_profile_id)
        behavior_profile = self._behavior_profile_for_pack(pack.id)
        return ClientOnboardingPackResponse(
            id=pack.id,
            client_profile_id=pack.client_profile_id,
            client_profile_name=profile.display_name,
            pack_name=pack.pack_name,
            version=pack.version,
            status=pack.status,
            source_mode=pack.source_mode,
            source_filename=pack.source_filename,
            storage_dir=pack.storage_dir,
            manifest=_parse_json(pack.manifest_json, {}),
            classification_report=self._serialize_validation(_parse_json(pack.classification_report_json, {})),
            validation_report=self._serialize_validation(_parse_json(pack.validation_report_json, {})),
            setup_gaps=_parse_json(pack.setup_gaps_json, []),
            assets=[self._serialize_asset(asset) for asset in self._assets_for_pack(pack.id)],
            playbook=self._serialize_playbook(self._playbook_for_pack(pack.id)),
            behavior_profile=ClientBehaviorProfileArtifact.model_validate(_parse_json(behavior_profile.behavior_profile_json, {}))
            if behavior_profile
            else None,
            approved_at=pack.approved_at,
            activated_at=pack.activated_at,
            created_at=pack.created_at,
            updated_at=pack.updated_at,
        )

    def _write_uploaded_file(self, directory: Path, filename: str, content: bytes) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        candidate = directory / filename
        if candidate.exists():
            candidate = directory / f"{candidate.stem}-{uuid.uuid4().hex[:8]}{candidate.suffix}"
        candidate.write_bytes(content)
        return candidate

    def _pack_manifest(self, pack_dir: Path) -> dict[str, Any]:
        manifest_path = pack_dir / "originals" / "client-onboarding.json"
        if not manifest_path.exists():
            manifest_path = pack_dir / "client-onboarding.json"
        if not manifest_path.exists():
            return {}
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _archive_into_pack(self, *, pack_dir: Path, filename: str, payload: bytes) -> list[Path]:
        originals_dir = pack_dir / "originals"
        originals_dir.mkdir(parents=True, exist_ok=True)
        extension = Path(filename).suffix.lower()
        if extension == ".zip":
            extracted_paths: list[Path] = []
            with zipfile.ZipFile(BytesIO(payload)) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    member_name = Path(member.filename)
                    if member_name.name.startswith(".") or "__macosx" in member.filename.lower():
                        continue
                    target = originals_dir / member_name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(member))
                    extracted_paths.append(target)
            if not extracted_paths:
                raise ClientOnboardingError("The uploaded zip did not contain any usable files.")
            return extracted_paths
        return [self._write_uploaded_file(originals_dir, filename, payload)]

    def _validate_pack(self, *, assets: list[ClientOnboardingAsset], playbook: ClientPlaybook | None) -> tuple[OnboardingValidationReport, list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        setup_gaps: list[str] = []
        roles = {asset.asset_role for asset in assets}
        if "proposal_template" not in roles:
            setup_gaps.append("Upload at least one proposal template to make client-facing export match the client brand.")
        if "pricing_artifact" not in roles:
            setup_gaps.append("Upload a pricing workbook, rate card, or canonical pricing file for deterministic pricing.")
        if "playbook_doc" not in roles and not playbook:
            setup_gaps.append("Add a playbook, README, or proposal-process guide so the client environment can shape tone and approach.")
        if "brand_asset" not in roles:
            warnings.append("No explicit brand asset was detected; the client environment can still run, but branding will be thinner.")
        if "resume" not in roles:
            setup_gaps.append("Add approved resume content so staffing and forms can complete cleanly.")
        if "reference" not in roles:
            setup_gaps.append("Add approved reference content so past performance and attachment packets are complete.")
        if not assets:
            errors.append("No onboarding assets were parsed from the uploaded pack.")
        return (
            OnboardingValidationReport(
                status="VALID" if not errors else "INVALID",
                warnings=_unique_strings(warnings),
                errors=_unique_strings(errors),
                details={"asset_role_counts": {role: sum(1 for asset in assets if asset.asset_role == role) for role in sorted(roles)}},
            ),
            _unique_strings(setup_gaps),
        )

    def _playbook_title(self, profile: ClientProfile) -> str:
        return f"{profile.display_name} Proposal Playbook"

    def _generated_behavior_profile(
        self,
        *,
        profile: ClientProfile,
        manifest: dict[str, Any],
        assets: list[ClientOnboardingAsset],
    ) -> ClientBehaviorProfileArtifact:
        manifest_playbook = manifest.get("playbook", {}) if isinstance(manifest.get("playbook"), dict) else {}
        required_attachments = _unique_strings(
            [
                *[asset.source_filename for asset in assets if asset.asset_role in {"form_template", "pricing_artifact"}],
                "Pricing workbook",
                "Proposal template",
                *manifest_playbook.get("required_attachments", []),
            ]
        )
        preferred_terminology = _unique_strings([str(item) for item in manifest_playbook.get("preferred_terminology", [])])
        avoid_terminology = _unique_strings([str(item) for item in manifest_playbook.get("avoid_terminology", [])])
        approval_requirements = _unique_strings(
            [
                "Pricing requires human approval before final export.",
                "Final export requires a human readiness check.",
                *[str(item) for item in manifest_playbook.get("approval_requirements", [])],
            ]
        )
        evaluation_emphasis = _unique_strings(
            [
                "Buyer focus",
                "Compliance responsiveness",
                "Relevant past performance",
                *[str(item) for item in manifest_playbook.get("evaluation_emphasis", [])],
            ]
        )
        service_boundaries = _unique_strings(
            [
                *[str(item) for item in manifest_playbook.get("service_offering_boundaries", [])],
                "Do not invent company facts or unsupported service commitments.",
            ]
        )
        return ClientBehaviorProfileArtifact(
            default_tone=_normalize_space(manifest_playbook.get("default_tone") or "formal, buyer-focused, and evidence-based"),
            proposal_sections=STANDARD_PROPOSAL_SECTIONS,
            approval_requirements=approval_requirements,
            required_attachments=required_attachments,
            evaluation_emphasis=evaluation_emphasis,
            preferred_terminology=preferred_terminology,
            avoid_terminology=avoid_terminology,
            service_offering_boundaries=service_boundaries,
            pricing_defaults={
                "use_client_pricing_model": True,
                "finance_review_required": True,
            },
            export_defaults={
                "use_client_template": True,
                "hide_internal_notes": True,
            },
        )

    def _generated_playbook_markdown(
        self,
        *,
        profile: ClientProfile,
        pack: ClientOnboardingPack,
        manifest: dict[str, Any],
        assets: list[ClientOnboardingAsset],
        behavior_profile: ClientBehaviorProfileArtifact,
    ) -> str:
        manifest_playbook = manifest.get("playbook", {}) if isinstance(manifest.get("playbook"), dict) else {}
        narrative_lines = [
            f"# {profile.display_name} Proposal Playbook",
            "",
            f"- Onboarding pack: {pack.pack_name} v{pack.version}",
            f"- Default tone: {behavior_profile.default_tone}",
            "",
            "## Proposal approach",
            "",
            _normalize_space(str(manifest_playbook.get("narrative_guidance") or manifest.get("notes") or "Use the approved client assets and templates as the source of truth for proposal generation.")),
            "",
            "## Preferred terminology",
            "",
        ]
        if behavior_profile.preferred_terminology:
            narrative_lines.extend(f"- {item}" for item in behavior_profile.preferred_terminology)
        else:
            narrative_lines.append("- Use the client’s brand and service terminology from approved assets when available.")
        narrative_lines.extend(["", "## Avoid", ""])
        if behavior_profile.avoid_terminology:
            narrative_lines.extend(f"- {item}" for item in behavior_profile.avoid_terminology)
        else:
            narrative_lines.append("- Avoid unsupported claims, invented differentiators, and mismatched service descriptions.")
        narrative_lines.extend(["", "## Required attachments", ""])
        narrative_lines.extend(f"- {item}" for item in behavior_profile.required_attachments)
        guidance_assets = [asset for asset in assets if asset.asset_role in {"playbook_doc", "operational_guidance"} and asset.extracted_text]
        if guidance_assets:
            narrative_lines.extend(["", "## Source guidance excerpts", ""])
            for asset in guidance_assets[:3]:
                excerpt = _normalize_space(asset.extracted_text or "")[:600]
                narrative_lines.append(f"### {asset.source_filename}")
                narrative_lines.append("")
                narrative_lines.append(excerpt or "No text preview available.")
                narrative_lines.append("")
        return "\n".join(narrative_lines).strip() + "\n"

    def _refresh_pack_outputs(
        self,
        pack: ClientOnboardingPack,
        *,
        preserve_narrative_guidance: bool = True,
        title_override: str | None = None,
        narrative_override: str | None = None,
    ) -> None:
        profile = self._profile(pack.client_profile_id)
        manifest = self._pack_manifest(Path(pack.storage_dir))
        assets = self._assets_for_pack(pack.id)
        behavior_profile = self._generated_behavior_profile(profile=profile, manifest=manifest, assets=assets)

        behavior = self._behavior_profile_for_pack(pack.id)
        if behavior is None:
            behavior = ClientBehaviorProfile(
                onboarding_pack_id=pack.id,
                status="DRAFT",
                behavior_profile_json=_dump_json(behavior_profile.model_dump()),
            )
            self.db.add(behavior)
        else:
            behavior.behavior_profile_json = _dump_json(behavior_profile.model_dump())
            if behavior.status != "APPROVED":
                behavior.status = "DRAFT"

        playbook = self._playbook_for_pack(pack.id)
        generated_narrative = self._generated_playbook_markdown(
            profile=profile,
            pack=pack,
            manifest=manifest,
            assets=assets,
            behavior_profile=behavior_profile,
        )
        if playbook is None:
            playbook = ClientPlaybook(
                onboarding_pack_id=pack.id,
                version=1,
                status="DRAFT",
                title=title_override or self._playbook_title(profile),
                narrative_guidance_md=narrative_override or generated_narrative,
                structured_rules_json=_dump_json(behavior_profile.model_dump()),
            )
            self.db.add(playbook)
        else:
            playbook.title = title_override or playbook.title or self._playbook_title(profile)
            playbook.structured_rules_json = _dump_json(behavior_profile.model_dump())
            if not preserve_narrative_guidance:
                playbook.narrative_guidance_md = narrative_override or generated_narrative
            elif narrative_override is not None:
                playbook.narrative_guidance_md = narrative_override
            elif not playbook.narrative_guidance_md:
                playbook.narrative_guidance_md = generated_narrative
            if playbook.status != "APPROVED":
                playbook.status = "DRAFT"

        validation_report, setup_gaps = self._validate_pack(assets=assets, playbook=playbook)
        pack.validation_report_json = _dump_json(validation_report.model_dump())
        pack.setup_gaps_json = _dump_json(setup_gaps)
        if pack.status not in {"APPROVED", "SUPERSEDED"}:
            pack.status = "VALIDATED" if validation_report.status == "VALID" else "DRAFT"
        self.db.flush()

    def _classify_pack_internal(self, pack: ClientOnboardingPack) -> None:
        pack_dir = Path(pack.storage_dir)
        manifest = self._pack_manifest(pack_dir)
        manifest_roles = _manifest_asset_roles(manifest)
        self.db.execute(delete(ClientOnboardingAsset).where(ClientOnboardingAsset.onboarding_pack_id == pack.id))
        self.db.execute(delete(ClientPlaybook).where(ClientPlaybook.onboarding_pack_id == pack.id))
        self.db.execute(delete(ClientBehaviorProfile).where(ClientBehaviorProfile.onboarding_pack_id == pack.id))
        self.db.flush()

        profile = self._profile(pack.client_profile_id)
        file_paths = [
            path
            for path in (pack_dir / "originals").rglob("*")
            if path.is_file() and path.name != "client-onboarding.json"
        ]
        assets: list[ClientOnboardingAsset] = []
        classification_errors: list[str] = []
        for path in sorted(file_paths):
            role, source = _classify_role(path.name, manifest_roles=manifest_roles)
            extracted_text = _extract_text_from_file(path)
            asset_status = "REVIEW_REQUIRED" if role == "unknown" else "CANDIDATE"
            metadata = _asset_metadata(
                role=role,
                filename=path.name,
                manifest=manifest,
                profile=profile,
                extracted_text=extracted_text,
            )
            metadata["source_pack_id"] = pack.id
            validation_payload = {
                "status": "VALID" if role != "unknown" else "INVALID",
                "warnings": ["No extractable text preview available."] if extracted_text is None and path.suffix.lower() in {".pdf", ".docx"} else [],
                "errors": ["File could not be classified automatically."] if role == "unknown" else [],
                "details": {"asset_role": role},
            }
            if role == "unknown":
                classification_errors.append(f"Review and classify {path.name} manually.")
            asset = ClientOnboardingAsset(
                onboarding_pack_id=pack.id,
                asset_role=role,
                asset_status=asset_status,
                classification_source=source,
                source_filename=path.name,
                source_path=path.as_posix(),
                media_type=_guess_media_type(path.name),
                extracted_text=extracted_text,
                normalized_metadata_json=_dump_json(metadata),
                validation_report_json=_dump_json(validation_payload),
            )
            self.db.add(asset)
            assets.append(asset)
        self.db.flush()

        pack.manifest_json = _dump_json(manifest)
        pack.classification_report_json = _dump_json(
            OnboardingValidationReport(
                status="VALID" if not classification_errors else "INVALID",
                warnings=[],
                errors=classification_errors,
                details={"asset_count": len(assets)},
            ).model_dump()
        )
        self._refresh_pack_outputs(pack, preserve_narrative_guidance=False)
        self.db.flush()

    def _import_runtime_assets(self, pack: ClientOnboardingPack, actor: str) -> None:
        profile = self._profile(pack.client_profile_id)
        service = self._profile_service()
        for asset in self._assets_for_pack(pack.id):
            metadata = _parse_json(asset.normalized_metadata_json, {})
            role = asset.asset_role
            if role == "proposal_template":
                try:
                    template = service.upload_proposal_template(
                        profile.id,
                        name=Path(asset.source_filename).stem.replace("-", " ").replace("_", " "),
                        filename=asset.source_filename,
                        content=Path(asset.source_path).read_bytes(),
                    )
                    metadata["imported_proposal_template_id"] = template.id
                except ClientProfileError:
                    pass
            elif role == "pricing_artifact":
                try:
                    pricing_model = service.import_pricing_model(
                        profile.id,
                        name=Path(asset.source_filename).stem.replace("-", " ").replace("_", " "),
                        filename=asset.source_filename,
                        content=Path(asset.source_path).read_bytes(),
                    )
                    metadata["imported_pricing_model_id"] = pricing_model.id
                except (ClientProfileError, json.JSONDecodeError):
                    pass
            if role != "unknown":
                metadata["approval_status"] = "approved"
                asset.asset_status = "APPROVED"
            asset.normalized_metadata_json = _dump_json(metadata)
        playbook = self._playbook_for_pack(pack.id)
        if playbook is not None:
            playbook.status = "APPROVED"
            playbook.approved_at = datetime.now(UTC).replace(tzinfo=None)
        behavior = self._behavior_profile_for_pack(pack.id)
        if behavior is not None:
            behavior.status = "APPROVED"
        pack.status = "APPROVED"
        pack.approved_at = datetime.now(UTC).replace(tzinfo=None)
        profile.client_environment_status = "SETUP_GAPS" if _parse_json(pack.setup_gaps_json, []) else "READY"
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=actor,
            action="client_onboarding_pack_approved",
            after_state_json=_dump_json({"pack_id": pack.id, "client_profile_id": pack.client_profile_id}),
        )

    def list_packs(self) -> list[ClientOnboardingPackResponse]:
        stmt = select(ClientOnboardingPack).order_by(ClientOnboardingPack.updated_at.desc(), ClientOnboardingPack.created_at.desc())
        return [self._serialize_pack(pack) for pack in self.db.scalars(stmt)]

    def get_pack(self, pack_id: str) -> ClientOnboardingPackResponse:
        return self._serialize_pack(self._pack(pack_id))

    def create_pack(
        self,
        payload: ClientOnboardingPackCreateRequest,
        *,
        archive: tuple[str, bytes] | None = None,
        files: list[tuple[str, bytes]] | None = None,
    ) -> ClientOnboardingPackUploadResponse:
        if archive is None and not files:
            raise ClientOnboardingError("Upload a zip archive or one or more onboarding files.")
        temp_pack_name = payload.pack_name or (Path(archive[0]).stem if archive else "client-onboarding-pack")
        temp_dir = CLIENT_ONBOARDING_STORAGE_DIR / f"staging-{uuid.uuid4().hex[:8]}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            if archive is not None:
                self._archive_into_pack(pack_dir=temp_dir, filename=archive[0], payload=archive[1])
            for filename, content in files or []:
                self._archive_into_pack(pack_dir=temp_dir, filename=filename, payload=content)
            manifest = self._pack_manifest(temp_dir)
            manifest_profile = _manifest_profile_payload(manifest)
            client_display_name = _normalize_space(
                payload.client_display_name
                or str(manifest_profile.get("display_name") or "")
                or temp_pack_name.replace("-", " ").replace("_", " ")
            )
            if not client_display_name:
                raise ClientOnboardingError("Client display name could not be inferred from the onboarding pack.")
            profile, created_profile = self._ensure_profile(client_display_name=client_display_name, manifest=manifest)
            pack = ClientOnboardingPack(
                client_profile_id=profile.id,
                pack_name=_normalize_space(payload.pack_name or temp_pack_name.replace("-", " ").replace("_", " ")),
                version=self._next_pack_version(profile.id),
                status="DRAFT",
                source_mode="ZIP" if archive is not None else "MULTI_FILE",
                source_filename=archive[0] if archive is not None else None,
                storage_dir="",
                manifest_json=_dump_json(manifest),
            )
            self.db.add(pack)
            self.db.flush()
            final_dir = _storage_dir_for_pack(pack.id, f"{pack.version:02d}-{_safe_slug(pack.pack_name)}")
            if final_dir.exists():
                shutil.rmtree(final_dir)
            shutil.move(temp_dir.as_posix(), final_dir.as_posix())
            pack.storage_dir = final_dir.as_posix()
            self._classify_pack_internal(pack)
            log_audit_event(
                self.db,
                opportunity_id=None,
                actor=payload.actor,
                action="client_onboarding_pack_created",
                after_state_json=_dump_json({"pack_id": pack.id, "client_profile_id": profile.id}),
            )
            self.db.commit()
            self.db.refresh(pack)
            return ClientOnboardingPackUploadResponse(pack=self._serialize_pack(pack), created_profile=created_profile)
        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    def classify_pack(self, pack_id: str, payload: ClientOnboardingPackActionRequest) -> ClientOnboardingPackResponse:
        pack = self._pack(pack_id)
        self._classify_pack_internal(pack)
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=payload.actor,
            action="client_onboarding_pack_classified",
            after_state_json=_dump_json({"pack_id": pack.id}),
        )
        self.db.commit()
        self.db.refresh(pack)
        return self._serialize_pack(pack)

    def update_asset(
        self,
        pack_id: str,
        asset_id: str,
        payload: ClientOnboardingAssetUpdateRequest,
    ) -> ClientOnboardingPackResponse:
        pack = self._pack(pack_id)
        if pack.status == "APPROVED":
            raise ClientOnboardingError("Create a new onboarding pack snapshot before changing approved asset roles.")
        asset = self._asset(pack_id, asset_id)
        normalized_role = _normalize_key(payload.asset_role)
        if normalized_role not in EDITABLE_ASSET_ROLES:
            raise ClientOnboardingError("Unsupported onboarding asset role.")
        asset.asset_role = normalized_role
        asset.asset_status = payload.asset_status.upper()
        asset.classification_source = "manual"
        metadata = _parse_json(asset.normalized_metadata_json, {})
        metadata["asset_type"] = RUNTIME_CONTENT_ROLE_MAP.get(normalized_role, normalized_role)
        metadata["source_pack_id"] = pack.id
        asset.normalized_metadata_json = _dump_json(metadata)
        asset.validation_report_json = _dump_json(
            {
                "status": "VALID" if normalized_role != "unknown" else "INVALID",
                "warnings": [],
                "errors": ["File still needs a concrete asset role."] if normalized_role == "unknown" else [],
                "details": {"asset_role": normalized_role, "updated_manually": True},
            }
        )
        self._refresh_pack_outputs(pack, preserve_narrative_guidance=True)
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=payload.actor,
            action="client_onboarding_asset_updated",
            after_state_json=_dump_json({"pack_id": pack.id, "asset_id": asset.id, "asset_role": asset.asset_role}),
        )
        self.db.commit()
        self.db.refresh(pack)
        return self._serialize_pack(pack)

    def save_playbook(
        self,
        pack_id: str,
        payload: ClientPlaybookUpdateRequest,
    ) -> ClientOnboardingPackResponse:
        pack = self._pack(pack_id)
        playbook = self._playbook_for_pack(pack.id)
        behavior = self._behavior_profile_for_pack(pack.id)
        structured_rules_json = getattr(behavior, "behavior_profile_json", None)
        if playbook is None:
            playbook = ClientPlaybook(
                onboarding_pack_id=pack.id,
                version=1,
                status="DRAFT",
                title=payload.title or self._playbook_title(self._profile(pack.client_profile_id)),
                narrative_guidance_md=payload.narrative_guidance_md.strip(),
                structured_rules_json=structured_rules_json or _dump_json({}),
            )
            self.db.add(playbook)
        elif playbook.status == "APPROVED":
            self.db.add(
                ClientPlaybook(
                    onboarding_pack_id=pack.id,
                    version=playbook.version + 1,
                    status="DRAFT",
                    title=payload.title or playbook.title,
                    narrative_guidance_md=payload.narrative_guidance_md.strip(),
                    structured_rules_json=structured_rules_json or playbook.structured_rules_json,
                )
            )
            pack.status = "VALIDATED"
            pack.approved_at = None
        else:
            playbook.title = payload.title or playbook.title
            playbook.narrative_guidance_md = payload.narrative_guidance_md.strip()
            playbook.status = "DRAFT"

        self._refresh_pack_outputs(
            pack,
            preserve_narrative_guidance=True,
            title_override=payload.title or None,
            narrative_override=payload.narrative_guidance_md.strip(),
        )
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=payload.actor,
            action="client_onboarding_playbook_saved",
            after_state_json=_dump_json({"pack_id": pack.id}),
        )
        self.db.commit()
        self.db.refresh(pack)
        return self._serialize_pack(pack)

    def approve_pack(self, pack_id: str, payload: ClientOnboardingPackApproveRequest) -> ClientOnboardingPackResponse:
        pack = self._pack(pack_id)
        playbook = self._playbook_for_pack(pack.id)
        if payload.narrative_guidance_md and playbook is not None:
            playbook.narrative_guidance_md = payload.narrative_guidance_md.strip()
        self._import_runtime_assets(pack, payload.actor)
        self.db.commit()
        self.db.refresh(pack)
        return self._serialize_pack(pack)

    def activate_pack(self, pack_id: str, payload: ClientOnboardingPackActionRequest) -> ClientOnboardingPackResponse:
        pack = self._pack(pack_id)
        if pack.status != "APPROVED":
            raise ClientOnboardingError("Approve the onboarding pack before activating the client environment.")
        profile = self._profile(pack.client_profile_id)
        for sibling in self.db.scalars(select(ClientOnboardingPack).where(ClientOnboardingPack.client_profile_id == profile.id)):
            if sibling.id != pack.id and sibling.status == "APPROVED":
                sibling.status = "SUPERSEDED"
        playbook = self._playbook_for_pack(pack.id)
        profile.active_onboarding_pack_id = pack.id
        profile.active_playbook_id = playbook.id if playbook else None
        profile.client_environment_status = "SETUP_GAPS" if _parse_json(pack.setup_gaps_json, []) else "READY"
        pack.activated_at = datetime.now(UTC).replace(tzinfo=None)
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=payload.actor,
            action="client_onboarding_pack_activated",
            after_state_json=_dump_json({"pack_id": pack.id, "client_profile_id": profile.id}),
        )
        self.db.commit()
        self.db.refresh(pack)
        return self._serialize_pack(pack)

    def active_environment_for_profile(self, profile_id: str) -> dict[str, Any]:
        profile = self._profile(profile_id)
        pack = self.db.get(ClientOnboardingPack, profile.active_onboarding_pack_id) if profile.active_onboarding_pack_id else None
        playbook = self.db.get(ClientPlaybook, profile.active_playbook_id) if profile.active_playbook_id else None
        return {
            "client_profile": profile,
            "pack": pack,
            "playbook": playbook,
            "behavior_profile": self._behavior_profile_for_pack(pack.id) if pack else None,
            "setup_gaps": _parse_json(pack.setup_gaps_json, []) if pack else [],
            "status": profile.client_environment_status,
        }

    def active_environment_for_opportunity(self, opportunity_id: str) -> dict[str, Any]:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if opportunity is None:
            return {"client_profile": None, "pack": None, "playbook": None, "behavior_profile": None, "setup_gaps": [], "status": "MISSING"}
        try:
            resolved = self._profile_service().resolve_opportunity_config(opportunity_id)
        except ClientProfileError:
            return {"client_profile": None, "pack": None, "playbook": None, "behavior_profile": None, "setup_gaps": [], "status": "MISSING"}
        if not resolved.config.client_profile_id:
            return {"client_profile": None, "pack": None, "playbook": None, "behavior_profile": None, "setup_gaps": [], "status": "MISSING"}
        return self.active_environment_for_profile(resolved.config.client_profile_id)

    def runtime_asset_inventory(self, opportunity_id: str) -> list[dict[str, Any]]:
        environment = self.active_environment_for_opportunity(opportunity_id)
        pack = environment.get("pack")
        profile = environment.get("client_profile")
        if pack is None or profile is None:
            return []
        inventory: list[dict[str, Any]] = []
        for asset in self._assets_for_pack(pack.id):
            if asset.asset_status != "APPROVED":
                continue
            metadata = _parse_json(asset.normalized_metadata_json, {})
            inventory.append(
                {
                    "id": asset.id,
                    "title": Path(asset.source_filename).stem.replace("-", " ").replace("_", " ").strip().title(),
                    "asset_type": metadata.get("asset_type", asset.asset_role),
                    "approval_status": metadata.get("approval_status", "approved"),
                    "effective_date": metadata.get("effective_date", date.today().isoformat()),
                    "expiry_date": metadata.get("expiry_date"),
                    "client_tags": metadata.get("client_tags", [profile.display_name]),
                    "service_tags": metadata.get("service_tags", _parse_json(profile.service_tags_json, [])),
                    "region_tags": metadata.get("region_tags", _parse_json(profile.region_tags_json, [])),
                    "source_of_truth": asset.source_path,
                    "body": asset.extracted_text or Path(asset.source_filename).stem.replace("-", " ").replace("_", " "),
                    "metadata": metadata,
                }
            )
        return inventory

    def runtime_form_templates(self, opportunity_id: str) -> list[dict[str, Any]]:
        environment = self.active_environment_for_opportunity(opportunity_id)
        pack = environment.get("pack")
        if pack is None:
            return []
        templates: list[dict[str, Any]] = []
        for asset in self._assets_for_pack(pack.id):
            if asset.asset_status != "APPROVED" or asset.asset_role not in {"form_template", "pricing_artifact"}:
                continue
            templates.append(
                {
                    "id": asset.id,
                    "name": asset.source_filename,
                    "path": asset.source_path,
                }
            )
        return templates
