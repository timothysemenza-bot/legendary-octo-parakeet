from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROPOSAL_OPS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROPOSAL_OPS_ROOT.parent
if str(PROPOSAL_OPS_ROOT) not in sys.path:
    sys.path.insert(0, str(PROPOSAL_OPS_ROOT))

from app.core.db import SessionLocal  # noqa: E402
from app.modules.company_os.service import CompanyOsService, founder_decisions, snapshot_cash_rows, snapshot_revenue_rows  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402


def _json_default(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Company OS Wave 1 manual ingestion and projection jobs.")
    parser.add_argument("--mode", choices=["run", "project", "scoreboard", "brief"], default="run")
    parser.add_argument("--source-config-path")
    parser.add_argument("--marketing-agents-root")
    parser.add_argument("--owner", default="Timmy Semenza")
    args = parser.parse_args()

    with SessionLocal() as db:
        service = CompanyOsService(db)
        try:
            if args.mode == "run":
                summary = service.run_manual_cycle(
                    source_config_path=args.source_config_path,
                    marketing_agents_root=args.marketing_agents_root,
                    owner=args.owner,
                )
                payload = {
                    "run_id": summary.run_id,
                    "sources_scanned": summary.sources_scanned,
                    "items_discovered": summary.items_discovered,
                    "signals_created": summary.signals_created,
                    "engagements_created": summary.engagements_created,
                    "engagements_updated": summary.engagements_updated,
                    "actions_created": summary.actions_created,
                    "approvals_created": summary.approvals_created,
                    "commitments_created": summary.commitments_created,
                    "knowledge_candidates_created": summary.knowledge_candidates_created,
                    "scoreboard_snapshot_id": summary.scoreboard_snapshot_id,
                    "founder_brief_id": summary.founder_brief_id,
                    "projections_written": summary.projections_written or [],
                    "created_at": summary.created_at,
                }
            elif args.mode == "project":
                written = service.run_projection_cycle(marketing_agents_root=args.marketing_agents_root, owner=args.owner)
                payload = {"mode": "project", "projections_written": written}
            elif args.mode == "scoreboard":
                snapshot = service.generate_scoreboard_snapshot(owner=args.owner)
                payload = {
                    "id": snapshot.id,
                    "snapshot_date": snapshot.snapshot_date,
                    "pipeline_value": snapshot.pipeline_value,
                    "weighted_pipeline": snapshot.weighted_pipeline,
                    "urgent_risks": snapshot.urgent_risks,
                    "revenue_rows": [row.model_dump(mode="json") for row in snapshot_revenue_rows(snapshot)],
                    "cash_rows": [row.model_dump(mode="json") for row in snapshot_cash_rows(snapshot)],
                }
            else:
                brief = service.generate_founder_brief(owner=args.owner)
                payload = {
                    "id": brief.id,
                    "brief_date": brief.brief_date,
                    "executive_control_summary": brief.executive_control_summary,
                    "decisions_needed": [row.model_dump(mode="json") for row in founder_decisions(brief)],
                    "scoreboard_snapshot_id": brief.scoreboard_snapshot_id,
                }
        except OperationalError as exc:
            message = str(exc).lower()
            if "no such table" in message:
                sys.stderr.write(
                    "Company OS tables are missing. Run `python -m alembic upgrade head` from `proposal-ops` before using this tool.\n"
                )
                return 1
            raise

    sys.stdout.write(json.dumps(payload, indent=2, default=_json_default))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
