from typing import List, Optional
from pydantic import BaseModel


class BranchMetricItem(BaseModel):
    branch_id: int
    branch_name: str
    active_clubs: int
    events_hosted: int
    total_registrations: int


class AnalyticsOverviewResponse(BaseModel):
    total_clubs: int
    active_clubs: int
    pending_proposals: int
    total_events: int
    published_events: int
    total_registrations: int
    confirmed_registrations: int
    total_attendance: int
    avg_attendance_rate: float
    total_students: int
    branch_metrics: List[BranchMetricItem] = []
    department_metrics: List[BranchMetricItem] = []  # Backwards compatibility alias
