from datetime import datetime

from pydantic import BaseModel


class GateLatencyMetric(BaseModel):
    gate_code: str
    approvals: int
    avg_hours_to_approval: float


class ReworkVelocityMetric(BaseModel):
    rework_events: int
    resolved_reworks: int
    unresolved_reworks: int
    resolution_rate: float
    avg_hours_to_resolve: float


class DefectRatesMetric(BaseModel):
    total_comments: int
    open_comments: int
    high_or_critical_open: int
    by_severity: dict[str, int]


class BlockerAgingMetric(BaseModel):
    pending_gate_items: int
    breached_sla_items: int
    items_with_blockers: int
    top_blockers: list[dict[str, int | str]]


class OpsMetricsResponse(BaseModel):
    generated_at: datetime
    opportunities_total: int
    open_opportunities: int
    gate_latency: list[GateLatencyMetric]
    rework_velocity: ReworkVelocityMetric
    defect_rates: DefectRatesMetric
    blocker_aging: BlockerAgingMetric

