from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.rbac import (
    get_current_active_user,
    check_club_ownership,
    RoleNameEnum,
    normalize_role,
)
from app.core.audit import record_audit_log
from app.models.models import (
    Event,
    EventRegistration,
    Attendance,
    EventOutcome,
    Club,
    User,
    Notification,
)
from app.schemas.event import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    EventListResponse,
    RegistrationResponse,
    RegistrationRosterItem,
    RegistrationListResponse,
    AttendanceRecordRequest,
    AttendanceResponse,
    EventOutcomeCreateRequest,
    EventOutcomeResponse,
)

router = APIRouter(prefix="/events", tags=["Events & Registrations"])


def check_event_management_authority(event: Event, user: User, db: Session) -> None:
    """Verify that user is the manager of the event's club or an administrator."""
    user_role = normalize_role(user.role.RoleName if user.role else "")
    if user_role == RoleNameEnum.ADMINISTRATOR.value:
        return

    club = db.query(Club).filter(Club.ClubId == event.ClubId).first()
    if not club or club.ManagerUserId != user.UserId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have management authority over this event",
        )


@router.get("", response_model=EventListResponse)
def list_events(
    club_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List and filter university events with pagination and real-time seat availability."""
    query = db.query(Event)

    if club_id:
        query = query.filter(Event.ClubId == club_id)
    if status_filter:
        query = query.filter(Event.Status == status_filter)
    else:
        # Default public listing shows published events
        query = query.filter(Event.Status == "published")

    if from_date:
        query = query.filter(Event.EventDate >= from_date)
    if to_date:
        query = query.filter(Event.EventDate <= to_date)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(Event.Title.ilike(search_fmt) | Event.VenueText.ilike(search_fmt))

    total = query.count()
    events = query.order_by(Event.EventDate.asc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for ev in events:
        confirmed_count = db.query(func.count(EventRegistration.RegistrationId)).filter(
            EventRegistration.EventId == ev.EventId,
            EventRegistration.Status == "confirmed"
        ).scalar() or 0

        seats_left = max(0, ev.Capacity - confirmed_count)

        items.append(
            EventResponse(
                event_id=ev.EventId,
                club_id=ev.ClubId,
                club_name=ev.club.Name if ev.club else None,
                title=ev.Title,
                venue_text=ev.VenueText,
                event_date=ev.EventDate,
                registration_deadline=ev.RegistrationDeadline,
                capacity=ev.Capacity,
                status=ev.Status,
                created_by_user_id=ev.CreatedByUserId,
                confirmed_registrations=confirmed_count,
                seats_left=seats_left,
            )
        )

    return EventListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/my-registrations", response_model=List[RegistrationResponse])
def get_my_registrations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve all active confirmed registrations for the current student."""
    regs = (
        db.query(EventRegistration)
        .filter(
            EventRegistration.UserId == current_user.UserId,
            EventRegistration.Status == "confirmed",
        )
        .all()
    )
    return [
        RegistrationResponse(
            registration_id=r.RegistrationId,
            event_id=r.EventId,
            user_id=r.UserId,
            status=r.Status,
            registered_at=r.RegisteredAt,
        )
        for r in regs
    ]


@router.get("/{event_id}", response_model=EventResponse)
def get_event_details(
    event_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve event details, deadline, and live seat count."""
    event = db.query(Event).filter(Event.EventId == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found",
        )

    confirmed_count = db.query(func.count(EventRegistration.RegistrationId)).filter(
        EventRegistration.EventId == event.EventId,
        EventRegistration.Status == "confirmed"
    ).scalar() or 0

    return EventResponse(
        event_id=event.EventId,
        club_id=event.ClubId,
        club_name=event.club.Name if event.club else None,
        title=event.Title,
        venue_text=event.VenueText,
        event_date=event.EventDate,
        registration_deadline=event.RegistrationDeadline,
        capacity=event.Capacity,
        status=event.Status,
        created_by_user_id=event.CreatedByUserId,
        confirmed_registrations=confirmed_count,
        seats_left=max(0, event.Capacity - confirmed_count),
    )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new event under the manager's club. Restricted to Club Manager or Administrator."""
    club = check_club_ownership(club_id=payload.club_id, user=current_user, db=db)

    # Clean timezone if needed for comparison
    event_dt = payload.event_date.replace(tzinfo=None) if payload.event_date.tzinfo else payload.event_date
    deadline_dt = payload.registration_deadline.replace(tzinfo=None) if payload.registration_deadline.tzinfo else payload.registration_deadline

    if deadline_dt > event_dt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Registration deadline cannot be after the event date",
        )

    new_event = Event(
        ClubId=club.ClubId,
        Title=payload.title.strip(),
        VenueText=payload.venue_text,
        EventDate=event_dt,
        RegistrationDeadline=deadline_dt,
        Capacity=payload.capacity,
        Status=payload.status or "published",
        CreatedByUserId=current_user.UserId,
    )
    db.add(new_event)
    db.flush()

    record_audit_log(
        db=db,
        actor_user_id=current_user.UserId,
        action="EVENT_CREATED",
        entity_type="Events",
        entity_id=new_event.EventId,
        details={"title": new_event.Title, "club_id": club.ClubId, "capacity": new_event.Capacity},
    )

    db.commit()
    db.refresh(new_event)

    return EventResponse(
        event_id=new_event.EventId,
        club_id=new_event.ClubId,
        club_name=club.Name,
        title=new_event.Title,
        venue_text=new_event.VenueText,
        event_date=new_event.EventDate,
        registration_deadline=new_event.RegistrationDeadline,
        capacity=new_event.Capacity,
        status=new_event.Status,
        created_by_user_id=new_event.CreatedByUserId,
        confirmed_registrations=0,
        seats_left=new_event.Capacity,
    )


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    payload: EventUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update event information or status. Restricted to event's club manager or administrator."""
    event = db.query(Event).filter(Event.EventId == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    check_event_management_authority(event=event, user=current_user, db=db)

    if payload.title is not None:
        event.Title = payload.title.strip()
    if payload.venue_text is not None:
        event.VenueText = payload.venue_text

    target_event_date = payload.event_date.replace(tzinfo=None) if (payload.event_date and payload.event_date.tzinfo) else (payload.event_date or event.EventDate)
    target_deadline = payload.registration_deadline.replace(tzinfo=None) if (payload.registration_deadline and payload.registration_deadline.tzinfo) else (payload.registration_deadline or event.RegistrationDeadline)

    if target_deadline > target_event_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Registration deadline cannot be after event date",
        )

    if payload.event_date:
        event.EventDate = target_event_date
    if payload.registration_deadline:
        event.RegistrationDeadline = target_deadline

    if payload.capacity is not None:
        event.Capacity = payload.capacity

    if payload.status:
        event.Status = payload.status

    record_audit_log(
        db=db,
        actor_user_id=current_user.UserId,
        action="EVENT_UPDATED",
        entity_type="Events",
        entity_id=event.EventId,
        details={"status": event.Status, "title": event.Title},
    )

    db.commit()
    db.refresh(event)

    confirmed_count = db.query(func.count(EventRegistration.RegistrationId)).filter(
        EventRegistration.EventId == event.EventId,
        EventRegistration.Status == "confirmed"
    ).scalar() or 0

    return EventResponse(
        event_id=event.EventId,
        club_id=event.ClubId,
        club_name=event.club.Name if event.club else None,
        title=event.Title,
        venue_text=event.VenueText,
        event_date=event.EventDate,
        registration_deadline=event.RegistrationDeadline,
        capacity=event.Capacity,
        status=event.Status,
        created_by_user_id=event.CreatedByUserId,
        confirmed_registrations=confirmed_count,
        seats_left=max(0, event.Capacity - confirmed_count),
    )


@router.post("/{event_id}/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_for_event(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Register the current student for an event. Enforces capacity cap, deadline, and duplicate check."""
    event = db.query(Event).filter(Event.EventId == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if event.Status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registrations are closed because event status is '{event.Status}'",
        )

    # Registration Deadline Check
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    deadline_utc = event.RegistrationDeadline.replace(tzinfo=None) if event.RegistrationDeadline.tzinfo else event.RegistrationDeadline

    if now_utc > deadline_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration deadline for this event has passed",
        )

    # Duplicate Registration Check
    existing_reg = db.query(EventRegistration).filter(
        EventRegistration.EventId == event_id,
        EventRegistration.UserId == current_user.UserId
    ).first()

    if existing_reg:
        if existing_reg.Status == "confirmed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already registered for this event",
            )
        elif existing_reg.Status == "cancelled":
            # Re-activate if capacity allows
            pass

    # Capacity Check inside transaction
    confirmed_count = db.query(func.count(EventRegistration.RegistrationId)).filter(
        EventRegistration.EventId == event_id,
        EventRegistration.Status == "confirmed"
    ).scalar() or 0

    if confirmed_count >= event.Capacity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event capacity has been reached. No more seats available.",
        )

    if existing_reg and existing_reg.Status == "cancelled":
        existing_reg.Status = "confirmed"
        registration = existing_reg
    else:
        registration = EventRegistration(
            EventId=event_id,
            UserId=current_user.UserId,
            Status="confirmed",
        )
        db.add(registration)

    db.flush()

    # Create notification for student
    notif = Notification(
        UserId=current_user.UserId,
        Type="REGISTRATION_CONFIRMATION",
        Message=f"You have successfully registered for '{event.Title}' scheduled on {event.EventDate.strftime('%Y-%m-%d %H:%M')}.",
    )
    db.add(notif)

    db.commit()
    db.refresh(registration)

    return RegistrationResponse(
        registration_id=registration.RegistrationId,
        event_id=registration.EventId,
        user_id=registration.UserId,
        status=registration.Status,
        registered_at=registration.RegisteredAt,
    )


@router.delete("/{event_id}/register", status_code=status.HTTP_200_OK)
def cancel_registration(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cancel a student's confirmed registration for an event."""
    reg = db.query(EventRegistration).filter(
        EventRegistration.EventId == event_id,
        EventRegistration.UserId == current_user.UserId,
        EventRegistration.Status == "confirmed"
    ).first()

    if not reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active confirmed registration found for this event",
        )

    reg.Status = "cancelled"
    db.commit()
    return {"message": "Registration successfully cancelled", "event_id": event_id}


@router.get("/{event_id}/registrations", response_model=RegistrationListResponse)
def get_event_roster(
    event_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve full registrant roster with attendance flags. Restricted to event manager or admin."""
    event = db.query(Event).filter(Event.EventId == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    check_event_management_authority(event=event, user=current_user, db=db)

    query = db.query(EventRegistration).filter(EventRegistration.EventId == event_id)
    total = query.count()
    regs = query.order_by(EventRegistration.RegisteredAt.asc()).offset((page - 1) * page_size).limit(page_size).all()

    # Pre-fetch attendance for this event
    attended_user_ids = {
        att.UserId
        for att in db.query(Attendance.UserId).filter(Attendance.EventId == event_id).all()
    }

    items = [
        RegistrationRosterItem(
            registration_id=r.RegistrationId,
            event_id=r.EventId,
            user_id=r.UserId,
            full_name=r.user.FullName,
            email=r.user.Email,
            status=r.Status,
            registered_at=r.RegisteredAt,
            attended=(r.UserId in attended_user_ids),
        )
        for r in regs
    ]

    return RegistrationListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/{event_id}/attendance", response_model=AttendanceResponse)
def record_attendance(
    event_id: int,
    payload: AttendanceRecordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark attendance for confirmed registered students. Rejects unconfirmed attendees."""
    event = db.query(Event).filter(Event.EventId == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    check_event_management_authority(event=event, user=current_user, db=db)

    # Fetch all confirmed registrations for this event
    confirmed_regs = db.query(EventRegistration).filter(
        EventRegistration.EventId == event_id,
        EventRegistration.Status == "confirmed"
    ).all()
    confirmed_user_map = {r.UserId: r for r in confirmed_regs}

    # Verify that all user_ids in payload are confirmed registrants
    for uid in payload.user_ids:
        if uid not in confirmed_user_map:
            user_obj = db.query(User).filter(User.UserId == uid).first()
            user_desc = user_obj.FullName if user_obj else f"User ID {uid}"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Attendance recording failed: {user_desc} is not confirmed registered for this event",
            )

    marked_count = 0
    for uid in set(payload.user_ids):
        # Check if already marked
        existing = db.query(Attendance).filter(
            Attendance.EventId == event_id,
            Attendance.UserId == uid
        ).first()

        if not existing:
            att = Attendance(
                EventId=event_id,
                UserId=uid,
                RecordedByUserId=current_user.UserId,
            )
            db.add(att)
            marked_count += 1

    record_audit_log(
        db=db,
        actor_user_id=current_user.UserId,
        action="ATTENDANCE_RECORDED",
        entity_type="Events",
        entity_id=event_id,
        details={"marked_count": marked_count, "user_ids": payload.user_ids},
    )

    db.commit()

    return AttendanceResponse(
        event_id=event_id,
        marked_present=marked_count,
        total_confirmed=len(confirmed_regs),
    )


@router.get("/{event_id}/outcomes", response_model=EventOutcomeResponse)
def get_event_outcome(
    event_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve post-event outcome summary and verified attendance metrics."""
    outcome = db.query(EventOutcome).filter(EventOutcome.EventId == event_id).first()
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event outcome report has not yet been submitted for this event",
        )

    return EventOutcomeResponse(
        outcome_id=outcome.OutcomeId,
        event_id=outcome.EventId,
        summary=outcome.Summary,
        attendance_count_snapshot=outcome.AttendanceCountSnapshot,
        submitted_by_user_id=outcome.SubmittedByUserId,
        submitted_at=outcome.SubmittedAt,
    )


@router.post("/{event_id}/outcomes", response_model=EventOutcomeResponse, status_code=status.HTTP_201_CREATED)
def create_event_outcome(
    event_id: int,
    payload: EventOutcomeCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Submit post-event summary report. Restricted to event manager or administrator."""
    event = db.query(Event).filter(Event.EventId == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    check_event_management_authority(event=event, user=current_user, db=db)

    existing = db.query(EventOutcome).filter(EventOutcome.EventId == event_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An outcome report has already been submitted for this event",
        )

    # Snapshot verified attendance count from Attendance table
    actual_attendance = db.query(func.count(Attendance.AttendanceId)).filter(
        Attendance.EventId == event_id
    ).scalar() or 0

    snapshot_count = payload.attendance_count_snapshot if payload.attendance_count_snapshot is not None else actual_attendance

    outcome = EventOutcome(
        EventId=event_id,
        Summary=payload.summary,
        AttendanceCountSnapshot=snapshot_count,
        SubmittedByUserId=current_user.UserId,
    )
    db.add(outcome)

    # Update event status to completed
    event.Status = "completed"

    record_audit_log(
        db=db,
        actor_user_id=current_user.UserId,
        action="EVENT_OUTCOME_SUBMITTED",
        entity_type="Events",
        entity_id=event_id,
        details={"summary": payload.summary, "attendance_snapshot": snapshot_count},
    )

    db.commit()
    db.refresh(outcome)

    return EventOutcomeResponse(
        outcome_id=outcome.OutcomeId,
        event_id=outcome.EventId,
        summary=outcome.Summary,
        attendance_count_snapshot=outcome.AttendanceCountSnapshot,
        submitted_by_user_id=outcome.SubmittedByUserId,
        submitted_at=outcome.SubmittedAt,
    )
