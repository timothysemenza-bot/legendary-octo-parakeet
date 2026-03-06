import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import SECRET_STORE_PATH
from app.core.db import Base, engine
from app.main import app
from app.modules.identity import models as identity_models  # noqa: F401
from app.modules.opportunity_intake import models  # noqa: F401
from app.modules.knowledge import models as knowledge_models  # noqa: F401
from app.modules.notifications import models as notification_models  # noqa: F401
from app.modules.proposal_outline import models as proposal_outline_models  # noqa: F401
from app.modules.rfp_parser import models as rfp_models  # noqa: F401
from app.modules.review_manager import models as review_models  # noqa: F401
from app.modules.submission_checklist import models as submission_models  # noqa: F401


@pytest.fixture(autouse=True)
def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    if SECRET_STORE_PATH.exists():
        SECRET_STORE_PATH.unlink()
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0018_proposal_outlines')"))
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
