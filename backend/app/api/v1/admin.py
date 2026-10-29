from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.rbac import require_roles, RoleNameEnum
from app.models.models import (
    Club,
    ClubProposal,
    Event,
    EventRegistration,
    Attendance,
    Branch,
    Program,
    User,
    AuditLog,
)
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    BranchMetricItem,
)
from app.schemas.audit import (
    AuditLogResponse,
    AuditLogListResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin & Analytics"])


@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(
    current_user: User = Depends(require_roles(RoleNameEnum.ADMINISTRATOR.value, RoleNameEnum.HOD.value)),
    db: Session = Depends(get_db),
):
    """Retrieve institutional analytics calculated from actual database records (powers Power BI & Admin dashboard)."""
    total_clubs = db.query(func.count(Club.ClubId)).scalar() or 0
    active_clubs = db.query(func.count(Club.ClubId)).filter(Club.Status == "active").scalar() or 0

    pending_proposals = db.query(func.count(ClubProposal.ProposalId)).filter(
        ClubProposal.Status.in_(["submitted", "changes_requested"])
    ).scalar() or 0

    total_events = db.query(func.count(Event.EventId)).scalar() or 0
    published_events = db.query(func.count(Event.EventId)).filter(Event.Status == "published").scalar() or 0

    total_registrations = db.query(func.count(EventRegistration.RegistrationId)).scalar() or 0
    confirmed_registrations = db.query(func.count(EventRegistration.RegistrationId)).filter(
        EventRegistration.Status == "confirmed"
    ).scalar() or 0

    total_attendance = db.query(func.count(Attendance.AttendanceId)).scalar() or 0

    avg_attendance_rate = 0.0
    if confirmed_registrations > 0:
        avg_attendance_rate = round(total_attendance / confirmed_registrations, 4)

    total_students = db.query(func.count(User.UserId)).join(User.role).filter(
        User.role.has(RoleName=RoleNameEnum.STUDENT.value)
    ).scalar() or 0

    # Branch breakdown (master programs)
    branches = db.query(Branch).all()
    branch_metrics: List[BranchMetricItem] = []

    for b in branches:
        b_active_clubs = (
            db.query(func.count(Club.ClubId))
            .join(Program, Club.ProgramId == Program.ProgramId)
            .filter(Program.BranchId == b.BranchId, Club.Status == "active")
            .scalar()
            or 0
        )

        b_events = (
            db.query(func.count(Event.EventId))
            .join(Event.club)
            .join(Program, Club.ProgramId == Program.ProgramId)
            .filter(Program.BranchId == b.BranchId)
            .scalar()
            or 0
        )

        b_registrations = (
            db.query(func.count(EventRegistration.RegistrationId))
            .join(EventRegistration.event)
            .join(Event.club)
            .join(Program, Club.ProgramId == Program.ProgramId)
            .filter(Program.BranchId == b.BranchId)
            .scalar()
            or 0
        )

        branch_metrics.append(
            BranchMetricItem(
                branch_id=b.BranchId,
                branch_name=b.Name,
                active_clubs=b_active_clubs,
                events_hosted=b_events,
                total_registrations=b_registrations,
            )
        )

    return AnalyticsOverviewResponse(
        total_clubs=total_clubs,
        active_clubs=active_clubs,
        pending_proposals=pending_proposals,
        total_events=total_events,
        published_events=published_events,
        total_registrations=total_registrations,
        confirmed_registrations=confirmed_registrations,
        total_attendance=total_attendance,
        avg_attendance_rate=avg_attendance_rate,
        total_students=total_students,
        branch_metrics=branch_metrics,
        department_metrics=branch_metrics,
    )


@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    actor_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_roles(RoleNameEnum.ADMINISTRATOR.value)),
    db: Session = Depends(get_db),
):
    """Query immutable audit log of sensitive system operations. Restricted strictly to Administrator."""
    query = db.query(AuditLog)

    if actor_id:
        query = query.filter(AuditLog.ActorUserId == actor_id)
    if entity_type:
        query = query.filter(AuditLog.EntityType == entity_type)
    if from_date:
        query = query.filter(AuditLog.CreatedAt >= from_date)
    if to_date:
        query = query.filter(AuditLog.CreatedAt <= to_date)

    total = query.count()
    logs = query.order_by(AuditLog.CreatedAt.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        AuditLogResponse(
            audit_log_id=log.AuditLogId,
            actor_user_id=log.ActorUserId,
            actor_email=log.actor.Email if log.actor else None,
            actor_name=log.actor.FullName if log.actor else None,
            action=log.Action,
            entity_type=log.EntityType,
            entity_id=log.EntityId,
            details=log.Details,
            created_at=log.CreatedAt,
        )
        for log in logs
    ]

    return AuditLogListResponse(items=items, total=total, page=page, page_size=page_size)
