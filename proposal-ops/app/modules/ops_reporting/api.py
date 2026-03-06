import csv
from io import StringIO

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.ops_reporting.schemas import OpsMetricsResponse
from app.modules.ops_reporting.service import OpsReportingService


api_router = APIRouter(prefix="/api/ops", tags=["ops-reporting"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


@api_router.get("/metrics", response_model=OpsMetricsResponse)
def ops_metrics(db: Session = Depends(get_db)) -> OpsMetricsResponse:
    return OpsReportingService(db).metrics()


@api_router.get("/metrics/export.csv")
def ops_metrics_csv(db: Session = Depends(get_db)) -> Response:
    metrics = OpsReportingService(db).metrics()
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["metric", "value"])
    writer.writerow(["generated_at", metrics.generated_at.isoformat()])
    writer.writerow(["opportunities_total", metrics.opportunities_total])
    writer.writerow(["open_opportunities", metrics.open_opportunities])
    writer.writerow(["rework_events", metrics.rework_velocity.rework_events])
    writer.writerow(["resolved_reworks", metrics.rework_velocity.resolved_reworks])
    writer.writerow(["unresolved_reworks", metrics.rework_velocity.unresolved_reworks])
    writer.writerow(["rework_resolution_rate", metrics.rework_velocity.resolution_rate])
    writer.writerow(["avg_hours_to_rework_resolve", metrics.rework_velocity.avg_hours_to_resolve])
    writer.writerow(["defect_total_comments", metrics.defect_rates.total_comments])
    writer.writerow(["defect_open_comments", metrics.defect_rates.open_comments])
    writer.writerow(["defect_high_or_critical_open", metrics.defect_rates.high_or_critical_open])
    writer.writerow(["pending_gate_items", metrics.blocker_aging.pending_gate_items])
    writer.writerow(["breached_sla_items", metrics.blocker_aging.breached_sla_items])
    writer.writerow(["items_with_blockers", metrics.blocker_aging.items_with_blockers])
    for row in metrics.gate_latency:
        writer.writerow([f"{row.gate_code}_approvals", row.approvals])
        writer.writerow([f"{row.gate_code}_avg_hours_to_approval", row.avg_hours_to_approval])
    for top in metrics.blocker_aging.top_blockers:
        writer.writerow([f"top_blocker::{top['blocker']}", top["count"]])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ops-metrics.csv"},
    )


@web_router.get("/ops/dashboard", response_class=HTMLResponse)
def ops_dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    metrics = OpsReportingService(db).metrics()
    return templates.TemplateResponse(
        request=request,
        name="ops_dashboard.html",
        context={"metrics": metrics},
    )

