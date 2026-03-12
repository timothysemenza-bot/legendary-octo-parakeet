import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# Force tests onto isolated temp artifacts before importing app config/DB modules.
TEST_ARTIFACTS_DIR = Path(tempfile.mkdtemp(prefix="bosskey-tests-"))
os.environ["BOSSKEY_ARTIFACTS_DIR"] = TEST_ARTIFACTS_DIR.as_posix()

from app.core.config import DB_PATH, RFP_SOURCE_STORAGE_DIR, SECRET_STORE_PATH
from app.core.db import Base, engine
from app.main import app
from app.modules.identity import models as identity_models  # noqa: F401
from app.modules.janitorial_os import models as janitorial_models  # noqa: F401
from app.modules.opportunity_intelligence import models as intelligence_models  # noqa: F401
from app.modules.opportunity_intake import models  # noqa: F401
from app.modules.knowledge import models as knowledge_models  # noqa: F401
from app.modules.notifications import models as notification_models  # noqa: F401
from app.modules.proposal_outline import models as proposal_outline_models  # noqa: F401
from app.modules.rfp_parser import models as rfp_models  # noqa: F401
from app.modules.review_manager import models as review_models  # noqa: F401
from app.modules.submission_checklist import models as submission_models  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts() -> None:
    yield
    shutil.rmtree(TEST_ARTIFACTS_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def reset_db() -> None:
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()
    Base.metadata.create_all(bind=engine)
    if RFP_SOURCE_STORAGE_DIR.exists():
        shutil.rmtree(RFP_SOURCE_STORAGE_DIR)
    RFP_SOURCE_STORAGE_DIR.mkdir(exist_ok=True)
    if SECRET_STORE_PATH.exists():
        SECRET_STORE_PATH.unlink()
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0031_pilot_hardening_release')"))
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
