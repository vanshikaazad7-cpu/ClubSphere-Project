from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import AuditLog, Club, Event, EventRegistration, User

router = APIRouter(tags=["Platform Metadata"])


def _iso(value: Optional[datetime]) -> Optional[str]:
    """Serialize a naive-UTC datetime to an ISO-8601 string."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _source(latest, last_audit, last_club, last_user) -> Optional[str]:
    """Name the table that produced the most recent timestamp."""
    if latest is None:
        return None
    if last_audit is not None and latest == last_audit:
        return "audit_log"
    if last_club is not None and latest == last_club:
        return "club"
    if last_user is not None and latest == last_user:
        return "user"
    return None


@router.get("/meta/last-updated")
def last_updated(db: Session = Depends(get_db)):
    """Report the most recent change to platform content.

    The landing page renders this as a "Last updated" stamp so visitors can
    see how current the seeded data is. Public by design -- it exposes no
    record content, only aggregate timestamps and counts.
    """
    last_audit = db.query(func.max(AuditLog.CreatedAt)).scalar()
    last_club = db.query(func.max(Club.CreatedAt)).scalar()
    last_user = db.query(func.max(User.CreatedAt)).scalar()

    # Events have no CreatedAt column; EventDate is the closest thing to
    # "when this event was added to the platform".
    last_event_date = db.query(func.max(Event.EventDate)).scalar()

    candidates = [d for d in (last_audit, last_club, last_user) if d is not None]
    latest = max(candidates) if candidates else None

    return {
        "last_updated": _iso(latest),
        "last_updated_source": _source(latest, last_audit, last_club, last_user),
        "last_club_created_at": _iso(last_club),
        "last_user_created_at": _iso(last_user),
        "latest_event_date": _iso(last_event_date),
        "counts": {
            "clubs": db.query(func.count(Club.ClubId)).scalar() or 0,
            "events": db.query(func.count(Event.EventId)).scalar() or 0,
            "registrations": db.query(func.count(EventRegistration.RegistrationId)).scalar() or 0,
            "students": db.query(func.count(User.UserId)).scalar() or 0,
        },
        "generated_at": _iso(datetime.now(timezone.utc)),
    }
