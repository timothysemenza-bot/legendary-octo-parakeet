from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from typing import Any

from app.core.config import APP_DIR


APPROVED_ASSETS_PATH = APP_DIR / "knowledge" / "apmp_framework" / "approved_content_assets.json"
FORM_TEMPLATES_PATH = APP_DIR / "knowledge" / "apmp_framework" / "form_templates.json"


@dataclass(frozen=True)
class ApprovedContentAsset:
    id: str
    title: str
    asset_type: str
    approval_status: str
    effective_date: str
    expiry_date: str | None
    client_tags: tuple[str, ...]
    service_tags: tuple[str, ...]
    region_tags: tuple[str, ...]
    source_of_truth: str
    body: str
    metadata: dict[str, Any]

    @property
    def is_approved(self) -> bool:
        return self.approval_status.lower() == "approved"

    @property
    def is_current(self) -> bool:
        if not self.expiry_date:
            return True
        try:
            return date.fromisoformat(self.expiry_date) >= date.today()
        except ValueError:
            return True


def _asset_from_payload(item: dict[str, Any]) -> ApprovedContentAsset | None:
    if not isinstance(item, dict):
        return None
    identifier = str(item.get("id", "")).strip()
    if not identifier:
        return None
    metadata = item.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    return ApprovedContentAsset(
        id=identifier,
        title=str(item.get("title", "")).strip() or identifier,
        asset_type=str(item.get("asset_type", "")).strip(),
        approval_status=str(item.get("approval_status", "")).strip() or "approved",
        effective_date=str(item.get("effective_date", "")).strip() or date.today().isoformat(),
        expiry_date=str(item.get("expiry_date", "")).strip() or None,
        client_tags=tuple(str(value).strip().lower() for value in item.get("client_tags", []) if str(value).strip()),
        service_tags=tuple(str(value).strip().lower() for value in item.get("service_tags", []) if str(value).strip()),
        region_tags=tuple(str(value).strip().lower() for value in item.get("region_tags", []) if str(value).strip()),
        source_of_truth=str(item.get("source_of_truth", "")).strip(),
        body=str(item.get("body", "")).strip(),
        metadata=metadata,
    )


def _asset_pool(assets: list[dict[str, Any]] | None = None) -> tuple[ApprovedContentAsset, ...]:
    if assets is None:
        return load_approved_assets()
    return tuple(item for item in (_asset_from_payload(asset) for asset in assets) if item is not None)


def _load_json(path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


@lru_cache(maxsize=1)
def load_approved_assets() -> tuple[ApprovedContentAsset, ...]:
    payload = _load_json(APPROVED_ASSETS_PATH)
    assets: list[ApprovedContentAsset] = []
    for item in payload.get("assets", []):
        if not isinstance(item, dict):
            continue
        assets.append(
            ApprovedContentAsset(
                id=str(item.get("id", "")).strip(),
                title=str(item.get("title", "")).strip(),
                asset_type=str(item.get("asset_type", "")).strip(),
                approval_status=str(item.get("approval_status", "")).strip(),
                effective_date=str(item.get("effective_date", "")).strip(),
                expiry_date=str(item.get("expiry_date", "")).strip() or None,
                client_tags=tuple(str(value).strip().lower() for value in item.get("client_tags", []) if str(value).strip()),
                service_tags=tuple(str(value).strip().lower() for value in item.get("service_tags", []) if str(value).strip()),
                region_tags=tuple(str(value).strip().lower() for value in item.get("region_tags", []) if str(value).strip()),
                source_of_truth=str(item.get("source_of_truth", "")).strip(),
                body=str(item.get("body", "")).strip(),
                metadata={key: value for key, value in item.items() if key not in {
                    "id", "title", "asset_type", "approval_status", "effective_date", "expiry_date",
                    "client_tags", "service_tags", "region_tags", "source_of_truth", "body",
                }},
            )
        )
    return tuple(asset for asset in assets if asset.id)


@lru_cache(maxsize=1)
def load_form_templates() -> list[dict[str, Any]]:
    payload = _load_json(FORM_TEMPLATES_PATH)
    templates = payload.get("templates", [])
    return templates if isinstance(templates, list) else []


def approved_assets_inventory(assets: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    return [
        {
            "id": asset.id,
            "title": asset.title,
            "asset_type": asset.asset_type,
            "approval_status": asset.approval_status,
            "effective_date": asset.effective_date,
            "expiry_date": asset.expiry_date,
            "client_tags": list(asset.client_tags),
            "service_tags": list(asset.service_tags),
            "region_tags": list(asset.region_tags),
            "source_of_truth": asset.source_of_truth,
            "body": asset.body,
            "metadata": asset.metadata,
        }
        for asset in _asset_pool(assets)
    ]


def select_assets(
    *,
    asset_type: str | None = None,
    tags: list[str] | None = None,
    require_current: bool = True,
    assets: list[dict[str, Any]] | None = None,
) -> list[ApprovedContentAsset]:
    tag_set = {tag.strip().lower() for tag in (tags or []) if tag.strip()}
    selected: list[ApprovedContentAsset] = []
    for asset in _asset_pool(assets):
        if asset_type and asset.asset_type != asset_type:
            continue
        if not asset.is_approved:
            continue
        if require_current and not asset.is_current:
            continue
        asset_tags = set(asset.client_tags) | set(asset.service_tags) | set(asset.region_tags)
        if tag_set and not (tag_set & asset_tags):
            continue
        selected.append(asset)
    return selected


def required_asset_blockers(*, tags: list[str], assets: list[dict[str, Any]] | None = None) -> list[str]:
    blockers: list[str] = []
    required_types = (
        ("resume", "Missing approved resume assets for the proposal package."),
        ("reference", "Missing approved reference assets for the proposal package."),
        ("insurance", "Missing current approved insurance or certification assets."),
        ("pricing_profile", "Missing approved pricing profile and rate-card assets."),
    )
    for asset_type, message in required_types:
        if not select_assets(asset_type=asset_type, tags=tags, assets=assets):
            blockers.append(message)
    return blockers
