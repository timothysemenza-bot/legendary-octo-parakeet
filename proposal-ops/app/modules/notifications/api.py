import json

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.session_auth import get_session_user
from app.modules.notifications.schemas import (
    EmailConnectionCreateRequest,
    EmailConnectionResponse,
    EmailConnectionSyncRequest,
    EmailConnectionSyncResult,
    EmailConnectionUpdateRequest,
    OutlookTokenRefreshRequest,
    OutlookTokenSetRequest,
    EmailSignalDecisionRequest,
    EmailSignalIngestRequest,
    EmailSignalUpdateResponse,
    NotificationAckRequest,
    NotificationDeliveryResponse,
    NotificationDispatchRequest,
    NotificationEventResponse,
    NotificationPolicyCloneRequest,
    NotificationPolicyClientMappingResponse,
    NotificationPolicyClientMappingUpsertRequest,
    NotificationPolicyConfigResponse,
    NotificationPolicyCreateRequest,
    NotificationPolicyUpdateRequest,
    NotificationScanRequest,
)
from app.modules.notifications.service import NotificationService


api_router = APIRouter(prefix="/api/notifications", tags=["notifications"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.post("/scan", response_model=list[NotificationEventResponse])
def scan_notifications(payload: NotificationScanRequest, db: Session = Depends(get_db)) -> list[NotificationEventResponse]:
    rows = NotificationService(db).scan_and_emit(actor=payload.actor)
    return [NotificationEventResponse.model_validate(r, from_attributes=True) for r in rows]


@api_router.post("/email/ingest", response_model=EmailSignalUpdateResponse)
def ingest_email_signal(payload: EmailSignalIngestRequest, db: Session = Depends(get_db)) -> EmailSignalUpdateResponse:
    row = NotificationService(db).ingest_email_signal(
        actor=payload.actor,
        external_message_id=payload.external_message_id,
        opportunity_id=payload.opportunity_id,
        from_address=payload.from_address,
        subject=payload.subject,
        body=payload.body,
        auto_apply=payload.auto_apply,
    )
    return EmailSignalUpdateResponse.model_validate(row, from_attributes=True)


@api_router.get("/email/connections", response_model=list[EmailConnectionResponse])
def list_email_connections(
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[EmailConnectionResponse]:
    service = NotificationService(db)
    rows = service.list_email_connections(status=status)
    return [EmailConnectionResponse.model_validate(service.connection_response_payload(r)) for r in rows]


@api_router.post("/email/connections", response_model=EmailConnectionResponse)
def create_email_connection(
    payload: EmailConnectionCreateRequest, db: Session = Depends(get_db)
) -> EmailConnectionResponse:
    service = NotificationService(db)
    row, errors = service.create_email_connection(
        provider=payload.provider,
        inbox_address=payload.inbox_address,
        config=payload.config,
        actor=payload.actor,
    )
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    assert row is not None
    return EmailConnectionResponse.model_validate(service.connection_response_payload(row))


@api_router.post("/email/connections/{connection_id}/sync", response_model=EmailConnectionSyncResult)
def sync_email_connection(
    connection_id: str, payload: EmailConnectionSyncRequest, db: Session = Depends(get_db)
) -> EmailConnectionSyncResult:
    result, errors = NotificationService(db).sync_email_connection(connection_id, actor=payload.actor)
    if errors:
        if "not found" in errors[0]:
            raise HTTPException(status_code=404, detail={"validation_errors": errors})
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    assert result is not None
    return EmailConnectionSyncResult.model_validate(result)


@api_router.post("/email/connections/{connection_id}/outlook/token", response_model=EmailConnectionResponse)
def set_outlook_token(
    connection_id: str, payload: OutlookTokenSetRequest, db: Session = Depends(get_db)
) -> EmailConnectionResponse:
    service = NotificationService(db)
    row, errors = service.set_outlook_connection_token(
        connection_id=connection_id,
        access_token=payload.access_token,
        refresh_token=payload.refresh_token,
        expires_at=payload.expires_at,
        actor=payload.actor,
    )
    if errors:
        if "not found" in errors[0]:
            raise HTTPException(status_code=404, detail={"validation_errors": errors})
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    assert row is not None
    return EmailConnectionResponse.model_validate(service.connection_response_payload(row))


@api_router.post("/email/connections/{connection_id}/outlook/refresh", response_model=EmailConnectionResponse)
def refresh_outlook_token_api(
    connection_id: str, payload: OutlookTokenRefreshRequest, db: Session = Depends(get_db)
) -> EmailConnectionResponse:
    service = NotificationService(db)
    row, errors = service.refresh_outlook_connection_token(
        connection_id=connection_id,
        actor=payload.actor,
        force=payload.force,
    )
    if errors:
        if "not found" in errors[0]:
            raise HTTPException(status_code=404, detail={"validation_errors": errors})
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    assert row is not None
    return EmailConnectionResponse.model_validate(service.connection_response_payload(row))


@api_router.put("/email/connections/{connection_id}", response_model=EmailConnectionResponse)
def update_email_connection(
    connection_id: str, payload: EmailConnectionUpdateRequest, db: Session = Depends(get_db)
) -> EmailConnectionResponse:
    service = NotificationService(db)
    row, errors = service.update_email_connection(
        connection_id=connection_id,
        status=payload.status,
        config=payload.config,
        actor=payload.actor,
    )
    if errors:
        if "not found" in errors[0]:
            raise HTTPException(status_code=404, detail={"validation_errors": errors})
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    assert row is not None
    return EmailConnectionResponse.model_validate(service.connection_response_payload(row))


@api_router.delete("/email/connections/{connection_id}")
def delete_email_connection(connection_id: str, actor: str = Query("operator"), db: Session = Depends(get_db)) -> dict:
    deleted, errors = NotificationService(db).delete_email_connection(connection_id=connection_id, actor=actor)
    if errors:
        if "not found" in errors[0]:
            raise HTTPException(status_code=404, detail={"validation_errors": errors})
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    return {"deleted": deleted, "connection_id": connection_id}


@api_router.get("/email/updates", response_model=list[EmailSignalUpdateResponse])
def list_email_signal_updates(
    status: str | None = Query(None),
    opportunity_id: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[EmailSignalUpdateResponse]:
    rows = NotificationService(db).list_email_signal_updates(
        status=status,
        opportunity_id=opportunity_id,
        limit=limit,
    )
    return [EmailSignalUpdateResponse.model_validate(r, from_attributes=True) for r in rows]


@api_router.post("/email/updates/{update_id}/apply", response_model=EmailSignalUpdateResponse)
def apply_email_signal_update(
    update_id: str, payload: EmailSignalDecisionRequest, db: Session = Depends(get_db)
) -> EmailSignalUpdateResponse:
    row = NotificationService(db).apply_email_signal_update(update_id, actor=payload.actor)
    if not row:
        raise HTTPException(status_code=404, detail="Email update not found")
    return EmailSignalUpdateResponse.model_validate(row, from_attributes=True)


@api_router.post("/email/updates/{update_id}/dismiss", response_model=EmailSignalUpdateResponse)
def dismiss_email_signal_update(
    update_id: str, payload: EmailSignalDecisionRequest, db: Session = Depends(get_db)
) -> EmailSignalUpdateResponse:
    row = NotificationService(db).dismiss_email_signal_update(update_id, actor=payload.actor)
    if not row:
        raise HTTPException(status_code=404, detail="Email update not found")
    return EmailSignalUpdateResponse.model_validate(row, from_attributes=True)


@api_router.get("/policy/schema")
def get_notification_policy_schema(db: Session = Depends(get_db)) -> dict:
    return NotificationService(db).get_policy_schema()


@api_router.get("/policy", response_model=NotificationPolicyConfigResponse)
def get_notification_policy(db: Session = Depends(get_db)) -> NotificationPolicyConfigResponse:
    row = NotificationService(db).get_policy_config()
    return NotificationPolicyConfigResponse.model_validate(row, from_attributes=True)


@api_router.get("/policy/configs", response_model=list[NotificationPolicyConfigResponse])
def list_notification_policy_configs(db: Session = Depends(get_db)) -> list[NotificationPolicyConfigResponse]:
    rows = NotificationService(db).list_policy_configs()
    return [NotificationPolicyConfigResponse.model_validate(r, from_attributes=True) for r in rows]


@api_router.post("/policy/configs", response_model=NotificationPolicyConfigResponse)
def create_notification_policy_config(
    payload: NotificationPolicyCreateRequest, db: Session = Depends(get_db)
) -> NotificationPolicyConfigResponse:
    row, errors = NotificationService(db).create_policy_config(
        policy_key=payload.policy_key, policy=payload.policy, actor=payload.actor
    )
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    assert row is not None
    return NotificationPolicyConfigResponse.model_validate(row, from_attributes=True)


@api_router.post("/policy/configs/{policy_key}/clone", response_model=NotificationPolicyConfigResponse)
def clone_notification_policy_config(
    policy_key: str, payload: NotificationPolicyCloneRequest, db: Session = Depends(get_db)
) -> NotificationPolicyConfigResponse:
    row, errors = NotificationService(db).clone_policy_config(
        source_policy_key=policy_key,
        target_policy_key=payload.target_policy_key,
        actor=payload.actor,
    )
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    assert row is not None
    return NotificationPolicyConfigResponse.model_validate(row, from_attributes=True)


@api_router.delete("/policy/configs/{policy_key}")
def delete_notification_policy_config(policy_key: str, db: Session = Depends(get_db)) -> dict:
    deleted, errors = NotificationService(db).delete_policy_config(policy_key=policy_key)
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    if not deleted:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"deleted": True, "policy_key": policy_key}


@api_router.put("/policy", response_model=NotificationPolicyConfigResponse)
def update_notification_policy(
    payload: NotificationPolicyUpdateRequest, db: Session = Depends(get_db)
) -> NotificationPolicyConfigResponse:
    row, errors = NotificationService(db).update_policy_config(payload.policy, actor=payload.actor)
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    assert row is not None
    return NotificationPolicyConfigResponse.model_validate(row, from_attributes=True)


@api_router.get("/policy/mappings", response_model=list[NotificationPolicyClientMappingResponse])
def list_notification_policy_mappings(db: Session = Depends(get_db)) -> list[NotificationPolicyClientMappingResponse]:
    rows = NotificationService(db).list_client_mappings()
    return [NotificationPolicyClientMappingResponse.model_validate(r, from_attributes=True) for r in rows]


@api_router.put("/policy/mappings", response_model=NotificationPolicyClientMappingResponse)
def upsert_notification_policy_mapping(
    payload: NotificationPolicyClientMappingUpsertRequest, db: Session = Depends(get_db)
) -> NotificationPolicyClientMappingResponse:
    row, errors = NotificationService(db).upsert_client_mapping(
        client_name=payload.client_name, policy_key=payload.policy_key, actor=payload.actor
    )
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    assert row is not None
    return NotificationPolicyClientMappingResponse.model_validate(row, from_attributes=True)


@api_router.delete("/policy/mappings/{client_name}")
def delete_notification_policy_mapping(
    client_name: str, actor: str = Query("operator"), db: Session = Depends(get_db)
) -> dict:
    deleted = NotificationService(db).delete_client_mapping(client_name=client_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return {"deleted": True, "client_name": client_name, "actor": actor}


@api_router.get("", response_model=list[NotificationEventResponse])
def list_notifications(
    status: str = Query("OPEN"),
    severity: str | None = Query(None),
    notification_type: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[NotificationEventResponse]:
    rows = NotificationService(db).list_events(
        status=status,
        severity=severity,
        notification_type=notification_type,
        limit=limit,
    )
    return [NotificationEventResponse.model_validate(r, from_attributes=True) for r in rows]


@api_router.post("/dispatch", response_model=list[NotificationDeliveryResponse])
def dispatch_notifications(
    payload: NotificationDispatchRequest, db: Session = Depends(get_db)
) -> list[NotificationDeliveryResponse]:
    rows = NotificationService(db).dispatch(actor=payload.actor, channels=payload.channels)
    return [NotificationDeliveryResponse.model_validate(r, from_attributes=True) for r in rows]


@api_router.get("/deliveries", response_model=list[NotificationDeliveryResponse])
def list_deliveries(
    status: str | None = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> list[NotificationDeliveryResponse]:
    rows = NotificationService(db).list_deliveries(status=status, limit=limit)
    return [NotificationDeliveryResponse.model_validate(r, from_attributes=True) for r in rows]


@api_router.post("/deliveries/{delivery_id}/retry", response_model=NotificationDeliveryResponse)
def retry_delivery(
    delivery_id: str, payload: NotificationAckRequest, db: Session = Depends(get_db)
) -> NotificationDeliveryResponse:
    row = NotificationService(db).retry_delivery(delivery_id, actor=payload.actor)
    if not row:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return NotificationDeliveryResponse.model_validate(row, from_attributes=True)


@api_router.post("/{notification_id}/ack", response_model=NotificationEventResponse)
def acknowledge_notification(
    notification_id: str, payload: NotificationAckRequest, db: Session = Depends(get_db)
) -> NotificationEventResponse:
    row = NotificationService(db).acknowledge(notification_id, actor=payload.actor)
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationEventResponse.model_validate(row, from_attributes=True)


@web_router.get("/notifications/digest", response_class=HTMLResponse)
def notifications_digest(request: Request, status: str = "OPEN", db: Session = Depends(get_db)) -> HTMLResponse:
    rows = NotificationService(db).list_events(status=status, limit=500)
    deliveries = NotificationService(db).list_deliveries(limit=200)
    return templates.TemplateResponse(
        request=request,
        name="notifications_digest.html",
        context={"rows": rows, "status": status.upper(), "deliveries": deliveries},
    )


@web_router.get("/notifications/policy", response_class=HTMLResponse)
def notifications_policy_editor(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = NotificationService(db)
    row = service.get_policy_config()
    return templates.TemplateResponse(
        request=request,
        name="notifications_policy.html",
        context={
            "policy_json": row.policy_json,
            "errors": [],
            "saved": False,
            "policies": service.list_policy_configs(),
            "mappings": service.list_client_mappings(),
            "policy_key_errors": [],
            "mapping_errors": [],
        },
    )


@web_router.get("/notifications/email", response_class=HTMLResponse)
def notifications_email_updates(request: Request, status: str = "PENDING", db: Session = Depends(get_db)) -> HTMLResponse:
    service = NotificationService(db)
    rows = service.list_email_signal_updates(status=status, limit=500)
    return templates.TemplateResponse(
        request=request,
        name="notifications_email_updates.html",
        context={"rows": rows, "status": status.upper(), "connections": service.list_email_connections()},
    )


@web_router.get("/notifications/email/connections", response_class=HTMLResponse)
def notifications_email_connections(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    service = NotificationService(db)
    return templates.TemplateResponse(
        request=request,
        name="notifications_email_connections.html",
        context={"connections": service.list_email_connections(), "errors": [], "saved": False},
    )


@web_router.post("/notifications/policy")
def notifications_policy_save(
    request: Request,
    policy_json: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    try:
        parsed = json.loads(policy_json)
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="notifications_policy.html",
            context={
                "policy_json": policy_json,
                "errors": ["Policy JSON is invalid."],
                "saved": False,
                "policies": NotificationService(db).list_policy_configs(),
                "mappings": NotificationService(db).list_client_mappings(),
                "policy_key_errors": [],
                "mapping_errors": [],
            },
            status_code=422,
        )
    row, errors = NotificationService(db).update_policy_config(parsed, actor=actor)
    if errors:
        return templates.TemplateResponse(
            request=request,
            name="notifications_policy.html",
            context={
                "policy_json": policy_json,
                "errors": errors,
                "saved": False,
                "policies": NotificationService(db).list_policy_configs(),
                "mappings": NotificationService(db).list_client_mappings(),
                "policy_key_errors": [],
                "mapping_errors": [],
            },
            status_code=422,
        )
    assert row is not None
    return templates.TemplateResponse(
        request=request,
        name="notifications_policy.html",
        context={
            "policy_json": row.policy_json,
            "errors": [],
            "saved": True,
            "policies": NotificationService(db).list_policy_configs(),
            "mappings": NotificationService(db).list_client_mappings(),
            "policy_key_errors": [],
            "mapping_errors": [],
        },
    )


@web_router.post("/notifications/policy/mappings")
def notifications_policy_mapping_save(
    request: Request,
    client_name: str = Form(...),
    policy_key: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = NotificationService(db)
    policy_row = service.get_policy_config()
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    row, errors = service.upsert_client_mapping(client_name=client_name, policy_key=policy_key, actor=actor)
    if errors:
        return templates.TemplateResponse(
            request=request,
            name="notifications_policy.html",
            context={
                "policy_json": policy_row.policy_json,
                "errors": [],
                "saved": False,
                "policies": service.list_policy_configs(),
                "mappings": service.list_client_mappings(),
                "policy_key_errors": [],
                "mapping_errors": errors,
            },
            status_code=422,
        )
    assert row is not None
    return templates.TemplateResponse(
        request=request,
        name="notifications_policy.html",
        context={
            "policy_json": policy_row.policy_json,
            "errors": [],
            "saved": True,
            "policies": service.list_policy_configs(),
            "mappings": service.list_client_mappings(),
            "policy_key_errors": [],
            "mapping_errors": [],
        },
    )


@web_router.post("/notifications/policy/configs")
def notifications_policy_config_create(
    request: Request,
    policy_key: str = Form(...),
    policy_json: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = NotificationService(db)
    base_row = service.get_policy_config()
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    try:
        policy = json.loads(policy_json)
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="notifications_policy.html",
            context={
                "policy_json": base_row.policy_json,
                "errors": [],
                "saved": False,
                "policies": service.list_policy_configs(),
                "mappings": service.list_client_mappings(),
                "policy_key_errors": ["Policy JSON is invalid for new policy."],
                "mapping_errors": [],
            },
            status_code=422,
        )
    _, errors = service.create_policy_config(policy_key=policy_key, policy=policy, actor=actor)
    if errors:
        return templates.TemplateResponse(
            request=request,
            name="notifications_policy.html",
            context={
                "policy_json": base_row.policy_json,
                "errors": [],
                "saved": False,
                "policies": service.list_policy_configs(),
                "mappings": service.list_client_mappings(),
                "policy_key_errors": errors,
                "mapping_errors": [],
            },
            status_code=422,
        )
    return RedirectResponse(url="/notifications/policy", status_code=303)


@web_router.post("/notifications/policy/configs/{policy_key}/clone")
def notifications_policy_config_clone(
    request: Request,
    policy_key: str,
    target_policy_key: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = NotificationService(db)
    base_row = service.get_policy_config()
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    _, errors = service.clone_policy_config(
        source_policy_key=policy_key, target_policy_key=target_policy_key, actor=actor
    )
    if errors:
        return templates.TemplateResponse(
            request=request,
            name="notifications_policy.html",
            context={
                "policy_json": base_row.policy_json,
                "errors": [],
                "saved": False,
                "policies": service.list_policy_configs(),
                "mappings": service.list_client_mappings(),
                "policy_key_errors": errors,
                "mapping_errors": [],
            },
            status_code=422,
        )
    return RedirectResponse(url="/notifications/policy", status_code=303)


@web_router.post("/notifications/policy/configs/{policy_key}/delete")
def notifications_policy_config_delete(
    request: Request, policy_key: str, db: Session = Depends(get_db)
) -> HTMLResponse:
    service = NotificationService(db)
    base_row = service.get_policy_config()
    deleted, errors = service.delete_policy_config(policy_key=policy_key)
    if errors or not deleted:
        return templates.TemplateResponse(
            request=request,
            name="notifications_policy.html",
            context={
                "policy_json": base_row.policy_json,
                "errors": [],
                "saved": False,
                "policies": service.list_policy_configs(),
                "mappings": service.list_client_mappings(),
                "policy_key_errors": errors or ["Policy deletion failed."],
                "mapping_errors": [],
            },
            status_code=422,
        )
    return RedirectResponse(url="/notifications/policy", status_code=303)


@web_router.post("/notifications/policy/mappings/{client_name}/delete")
def notifications_policy_mapping_delete(
    request: Request, client_name: str, db: Session = Depends(get_db)
) -> RedirectResponse:
    NotificationService(db).delete_client_mapping(client_name=client_name)
    return RedirectResponse(url="/notifications/policy", status_code=303)


@web_router.post("/notifications/scan")
def notifications_scan_web(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    NotificationService(db).scan_and_emit(actor=actor)
    return RedirectResponse(url="/notifications/digest", status_code=303)


@web_router.post("/notifications/dispatch")
def notifications_dispatch_web(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    NotificationService(db).dispatch(actor=actor)
    return RedirectResponse(url="/notifications/digest", status_code=303)


@web_router.post("/notifications/email/ingest")
def notifications_email_ingest_web(
    request: Request,
    from_address: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    opportunity_id: str = Form(""),
    external_message_id: str = Form(""),
    auto_apply: bool = Form(False),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "email-agent"
    NotificationService(db).ingest_email_signal(
        actor=actor,
        external_message_id=external_message_id or None,
        opportunity_id=opportunity_id or None,
        from_address=from_address,
        subject=subject,
        body=body,
        auto_apply=auto_apply,
    )
    return RedirectResponse(url="/notifications/email?status=PENDING", status_code=303)


@web_router.post("/notifications/email/connections")
def notifications_email_connection_create_web(
    request: Request,
    provider: str = Form(...),
    inbox_address: str = Form(...),
    config_json: str = Form("{}"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = NotificationService(db)
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    try:
        parsed_config = json.loads(config_json)
    except Exception:
        parsed_config = None
    if not isinstance(parsed_config, dict):
        return templates.TemplateResponse(
            request=request,
            name="notifications_email_connections.html",
            context={
                "connections": service.list_email_connections(),
                "errors": ["config_json must be a JSON object."],
                "saved": False,
            },
            status_code=422,
        )
    _, errors = service.create_email_connection(
        provider=provider,
        inbox_address=inbox_address,
        config=parsed_config,
        actor=actor,
    )
    if errors:
        return templates.TemplateResponse(
            request=request,
            name="notifications_email_connections.html",
            context={"connections": service.list_email_connections(), "errors": errors, "saved": False},
            status_code=422,
        )
    return RedirectResponse(url="/notifications/email/connections", status_code=303)


@web_router.post("/notifications/email/connections/{connection_id}/sync")
def notifications_email_connection_sync_web(
    request: Request, connection_id: str, db: Session = Depends(get_db)
) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "email-agent"
    NotificationService(db).sync_email_connection(connection_id, actor=actor)
    return RedirectResponse(url="/notifications/email?status=PENDING", status_code=303)


@web_router.post("/notifications/email/connections/{connection_id}/outlook/token")
def notifications_email_connection_outlook_token_web(
    request: Request,
    connection_id: str,
    access_token: str = Form(...),
    refresh_token: str = Form(""),
    expires_at: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    NotificationService(db).set_outlook_connection_token(
        connection_id=connection_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        actor=actor,
    )
    return RedirectResponse(url="/notifications/email/connections", status_code=303)


@web_router.post("/notifications/email/connections/{connection_id}/outlook/refresh")
def notifications_email_connection_outlook_refresh_web(
    request: Request, connection_id: str, force: bool = Form(False), db: Session = Depends(get_db)
) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    NotificationService(db).refresh_outlook_connection_token(
        connection_id=connection_id,
        actor=actor,
        force=force,
    )
    return RedirectResponse(url="/notifications/email/connections", status_code=303)


@web_router.post("/notifications/email/connections/{connection_id}/status")
def notifications_email_connection_status_web(
    request: Request,
    connection_id: str,
    status: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    NotificationService(db).update_email_connection(
        connection_id=connection_id,
        status=status,
        config=None,
        actor=actor,
    )
    return RedirectResponse(url="/notifications/email/connections", status_code=303)


@web_router.post("/notifications/email/connections/{connection_id}/delete")
def notifications_email_connection_delete_web(
    request: Request, connection_id: str, db: Session = Depends(get_db)
) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    NotificationService(db).delete_email_connection(connection_id=connection_id, actor=actor)
    return RedirectResponse(url="/notifications/email/connections", status_code=303)


@web_router.post("/notifications/email/updates/{update_id}/apply")
def notifications_email_apply_web(
    request: Request, update_id: str, db: Session = Depends(get_db)
) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    row = NotificationService(db).apply_email_signal_update(update_id, actor=actor)
    if not row:
        raise HTTPException(status_code=404, detail="Email update not found")
    return RedirectResponse(url="/notifications/email?status=PENDING", status_code=303)


@web_router.post("/notifications/email/updates/{update_id}/dismiss")
def notifications_email_dismiss_web(
    request: Request, update_id: str, db: Session = Depends(get_db)
) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    row = NotificationService(db).dismiss_email_signal_update(update_id, actor=actor)
    if not row:
        raise HTTPException(status_code=404, detail="Email update not found")
    return RedirectResponse(url="/notifications/email?status=PENDING", status_code=303)


@web_router.post("/notifications/deliveries/{delivery_id}/retry")
def notifications_retry_web(request: Request, delivery_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    row = NotificationService(db).retry_delivery(delivery_id, actor=actor)
    if not row:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return RedirectResponse(url="/notifications/digest", status_code=303)


@web_router.post("/notifications/{notification_id}/ack")
def notifications_ack_web(
    request: Request, notification_id: str, status: str = Form("OPEN"), db: Session = Depends(get_db)
) -> RedirectResponse:
    session_user = get_session_user(request, db)
    actor = session_user.display_name if session_user else "operator"
    row = NotificationService(db).acknowledge(notification_id, actor=actor)
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    return RedirectResponse(url=f"/notifications/digest?status={status}", status_code=303)
