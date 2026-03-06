from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


REQUIRED_TABLES = {
    "opportunities",
    "capture_plans",
    "gate_decisions",
    "audit_events",
    "solicitations",
    "requirements",
    "compliance_matrix_rows",
    "review_cycles",
    "review_comments",
    "submission_checklists",
    "submission_checklist_items",
    "lessons_learned_records",
    "knowledge_promotions",
    "users",
    "user_role_assignments",
    "notification_events",
    "notification_deliveries",
    "notification_policy_configs",
    "notification_policy_client_mappings",
    "email_signal_updates",
    "email_connections",
    "proposal_outlines",
}


def validate_schema_state(engine: Engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    has_required = REQUIRED_TABLES.issubset(tables)
    has_alembic = "alembic_version" in tables

    if not has_required and not has_alembic:
        raise RuntimeError(
            "Database schema is not initialized. Run: `python -m alembic upgrade head`."
        )

    if has_required and not has_alembic:
        raise RuntimeError(
            "Database has app tables but no alembic_version. "
            "Run: `python -m alembic stamp head` (preserve data) or "
            "`Remove-Item .\\.artifacts\\bosskey_pursuit_os.sqlite3 -Force; python -m alembic upgrade head`."
        )

    if has_alembic:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one_or_none()
        if not version:
            raise RuntimeError(
                "alembic_version table is empty. Run `python -m alembic stamp head`."
            )
        if not has_required:
            raise RuntimeError(
                "Alembic revision exists but required tables are missing. "
                "Run: `python -m alembic upgrade head` or reset local DB."
            )
