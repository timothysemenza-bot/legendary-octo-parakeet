from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import SESSION_SECRET
from app.core.db import engine
from app.core.startup_checks import validate_schema_state
from app.modules.auth_stub.api import api_router as auth_api_router
from app.modules.auth_stub.api import web_router as auth_web_router
from app.modules.capture_plan.api import api_router as capture_api_router
from app.modules.capture_plan.api import web_router as capture_web_router
from app.modules.compliance_matrix.api import api_router as compliance_api_router
from app.modules.compliance_matrix.api import web_router as compliance_web_router
from app.modules.identity.api import api_router as identity_api_router
from app.modules.identity.api import web_router as identity_web_router
from app.modules.knowledge.api import api_router as knowledge_api_router
from app.modules.knowledge.api import web_router as knowledge_web_router
from app.modules.notifications.api import api_router as notifications_api_router
from app.modules.notifications.api import web_router as notifications_web_router
from app.modules.ops_reporting.api import api_router as ops_api_router
from app.modules.ops_reporting.api import web_router as ops_web_router
from app.modules.opportunity_intake.api import api_router, web_router
from app.modules.proposal_outline.api import api_router as outline_api_router
from app.modules.proposal_outline.api import web_router as outline_web_router
from app.modules.review_manager.api import api_router as review_api_router
from app.modules.review_manager.api import web_router as review_web_router
from app.modules.rfp_parser.api import api_router as rfp_api_router
from app.modules.rfp_parser.api import web_router as rfp_web_router
from app.modules.submission_checklist.api import api_router as submission_api_router
from app.modules.submission_checklist.api import web_router as submission_web_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    validate_schema_state(engine)
    yield


app = FastAPI(title="Boss Key Pursuit OS", version="0.1.0", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.include_router(auth_api_router)
app.include_router(auth_web_router)
app.include_router(api_router)
app.include_router(web_router)
app.include_router(capture_api_router)
app.include_router(capture_web_router)
app.include_router(rfp_api_router)
app.include_router(rfp_web_router)
app.include_router(compliance_api_router)
app.include_router(compliance_web_router)
app.include_router(identity_api_router)
app.include_router(identity_web_router)
app.include_router(knowledge_api_router)
app.include_router(knowledge_web_router)
app.include_router(notifications_api_router)
app.include_router(notifications_web_router)
app.include_router(ops_api_router)
app.include_router(ops_web_router)
app.include_router(outline_api_router)
app.include_router(outline_web_router)
app.include_router(review_api_router)
app.include_router(review_web_router)
app.include_router(submission_api_router)
app.include_router(submission_web_router)
