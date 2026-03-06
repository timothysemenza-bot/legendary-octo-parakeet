import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.startup_checks import validate_schema_state


def test_validate_schema_state_raises_when_tables_exist_without_alembic(tmp_path: Path) -> None:
    db_file = tmp_path / "bad_state.sqlite3"
    conn = sqlite3.connect(db_file.as_posix())
    conn.execute("CREATE TABLE opportunities (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE capture_plans (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE gate_decisions (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE audit_events (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE solicitations (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE requirements (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE compliance_matrix_rows (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE review_cycles (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE review_comments (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE submission_checklists (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE submission_checklist_items (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE lessons_learned_records (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE knowledge_promotions (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE users (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE user_role_assignments (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE notification_events (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE notification_deliveries (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE notification_policy_configs (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE notification_policy_client_mappings (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE email_signal_updates (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE email_connections (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE proposal_outlines (id TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_file.as_posix()}")
    with pytest.raises(RuntimeError, match="not Alembic-stamped|no alembic_version|has app tables"):
        validate_schema_state(engine)


def test_validate_schema_state_passes_with_alembic_stamp(tmp_path: Path) -> None:
    db_file = tmp_path / "good_state.sqlite3"
    conn = sqlite3.connect(db_file.as_posix())
    conn.execute("CREATE TABLE opportunities (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE capture_plans (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE gate_decisions (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE audit_events (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE solicitations (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE requirements (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE compliance_matrix_rows (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE review_cycles (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE review_comments (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE submission_checklists (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE submission_checklist_items (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE lessons_learned_records (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE knowledge_promotions (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE users (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE user_role_assignments (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE notification_events (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE notification_deliveries (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE notification_policy_configs (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE notification_policy_client_mappings (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE email_signal_updates (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE email_connections (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE proposal_outlines (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
    conn.execute("INSERT INTO alembic_version (version_num) VALUES ('0018_proposal_outlines')")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_file.as_posix()}")
    validate_schema_state(engine)
    with engine.connect() as check:
        assert check.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar_one() == 1


def test_validate_schema_state_raises_on_empty_database(tmp_path: Path) -> None:
    db_file = tmp_path / "empty_state.sqlite3"
    sqlite3.connect(db_file.as_posix()).close()
    engine = create_engine(f"sqlite:///{db_file.as_posix()}")
    with pytest.raises(RuntimeError, match="not initialized"):
        validate_schema_state(engine)
