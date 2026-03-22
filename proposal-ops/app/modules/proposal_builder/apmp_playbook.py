from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import APP_DIR
from app.modules.proposal_builder.schemas import ReviewFindingArtifact


APMP_FRAMEWORK_DIR = APP_DIR / "knowledge" / "apmp_framework"


def _load_json_file(file_name: str) -> dict[str, Any]:
    path = APMP_FRAMEWORK_DIR / file_name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


@lru_cache(maxsize=1)
def load_apmp_playbook() -> dict[str, Any]:
    return {
        "hard_gates": _load_json_file("hard_gates.json"),
        "quality_rubrics": _load_json_file("quality_rubrics.json"),
        "package_controls": _load_json_file("package_controls.json"),
    }


def apmp_topics(bucket: str) -> list[dict[str, Any]]:
    payload = load_apmp_playbook().get(bucket, {})
    topics = payload.get("topics", [])
    return topics if isinstance(topics, list) else []


def summarize_apmp_topics() -> list[dict[str, str]]:
    summary: list[dict[str, str]] = []
    for bucket in ("hard_gates", "quality_rubrics", "package_controls"):
        for topic in apmp_topics(bucket):
            topic_id = str(topic.get("id", "")).strip()
            title = str(topic.get("title", "")).strip()
            description = str(topic.get("description", "")).strip()
            if topic_id and title:
                summary.append(
                    {
                        "bucket": bucket,
                        "id": topic_id,
                        "title": title,
                        "description": description,
                    }
                )
    return summary


def apmp_findings_for_gaps(*, stage_name: str, gaps: list[str]) -> list[ReviewFindingArtifact]:
    findings: list[ReviewFindingArtifact] = []
    topic_lookup = {topic["id"]: topic for topic in summarize_apmp_topics()}
    gap_topic_map = {
        "missing approved resume": "proof_points",
        "missing approved reference": "proof_points",
        "submission": "compliance_responsiveness",
        "pricing": "price_to_win",
        "form": "production_management",
        "insurance": "knowledge_management",
    }
    for gap in gaps:
        lowered = gap.lower()
        matched_topic = None
        for marker, topic_id in gap_topic_map.items():
            if marker in lowered:
                matched_topic = topic_id
                break
        matched_topic = matched_topic or "proposal_organization"
        topic = topic_lookup.get(matched_topic, {})
        findings.append(
            ReviewFindingArtifact(
                review_stage=stage_name,
                title=topic.get("title", "APMP quality gap"),
                severity="medium",
                disposition="needs_revision",
                recommendation=gap,
                apmp_topic_id=matched_topic,
                source_refs=[stage_name],
            )
        )
    return findings
