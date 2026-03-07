import shutil

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import DB_PATH, RFP_SOURCE_STORAGE_DIR, SECRET_STORE_PATH
from app.core.db import Base, engine
from app.main import app
from app.modules.identity import models as identity_models  # noqa: F401
from app.modules.janitorial_os import models as janitorial_models  # noqa: F401
from app.modules.opportunity_intake import models  # noqa: F401
from app.modules.knowledge import models as knowledge_models  # noqa: F401
from app.modules.notifications import models as notification_models  # noqa: F401
from app.modules.proposal_outline import models as proposal_outline_models  # noqa: F401
from app.modules.rfp_parser import models as rfp_models  # noqa: F401
from app.modules.review_manager import models as review_models  # noqa: F401
from app.modules.submission_checklist import models as submission_models  # noqa: F401


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
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0025_janitorial_capture_os_foundation')"))
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
