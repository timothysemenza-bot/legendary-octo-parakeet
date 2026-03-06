from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import AUTH_AUTO_PROVISION
from app.core.db import get_db
from app.core.session_auth import get_session_user
from app.modules.identity.schemas import AuthPermissionResponse, UserResponse
from app.modules.identity.service import IdentityService


api_router = APIRouter(prefix="/api/auth", tags=["auth-stub"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.get("/me", response_model=UserResponse | None)
def auth_me(request: Request, db: Session = Depends(get_db)) -> UserResponse | None:
    user = get_session_user(request, db)
    if not user:
        return None
    return UserResponse.model_validate(user, from_attributes=True)


@api_router.get("/permissions", response_model=AuthPermissionResponse)
def auth_permissions(opportunity_id: str, request: Request, db: Session = Depends(get_db)) -> AuthPermissionResponse:
    user = get_session_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    identity = IdentityService(db)
    return AuthPermissionResponse.model_validate(
        {
        "user_id": user.id,
        "opportunity_id": opportunity_id,
            "reports": identity.gate_permission_reports(user.id, opportunity_id),
        }
    )


@web_router.get("/auth/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    user = get_session_user(request, db)
    return templates.TemplateResponse(
        request=request,
        name="auth_login.html",
        context={"current_user": user},
    )


@web_router.post("/auth/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    display_name: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    service = IdentityService(db)
    user = service.get_user_by_email(email.strip())
    if not user:
        if not AUTH_AUTO_PROVISION:
            raise HTTPException(status_code=403, detail="User is not provisioned")
        user = service.create_user(display_name=display_name.strip() or email.split("@")[0], email=email.strip())

    request.session["user_id"] = user.id
    request.session["email"] = user.email
    request.session["display_name"] = user.display_name
    roles = service.global_roles(user.id)
    request.session["global_roles"] = roles
    request.session["is_admin"] = any(r.lower() in {"admin", "identity_admin"} for r in roles)
    return RedirectResponse(url="/", status_code=303)


@web_router.post("/auth/logout")
def logout_submit(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=303)
