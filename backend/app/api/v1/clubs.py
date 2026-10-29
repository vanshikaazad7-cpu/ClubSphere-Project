from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.rbac import (
    get_current_active_user,
    require_roles,
    check_club_ownership,
    RoleNameEnum,
    normalize_role,
)
from app.core.audit import record_audit_log
from app.models.models import (
    Club,
    ClubMembership,
    Program,
    User,
    Notification,
)
from app.schemas.club import (
    ClubCreateRequest,
    ClubUpdateRequest,
    ClubResponse,
    ClubListResponse,
    MembershipJoinResponse,
    MembershipUpdateRequest,
    MembershipMemberResponse,
    MembershipListResponse,
)

router = APIRouter(prefix="/clubs", tags=["Clubs & Memberships"])


@router.get("", response_model=ClubListResponse)
def list_clubs(
    program_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List and search university clubs with program and status filters."""
    query = db.query(Club).join(Program, Club.ProgramId == Program.ProgramId)

    if program_id:
        query = query.filter(Club.ProgramId == program_id)
    if branch_id:
        query = query.filter(Program.BranchId == branch_id)
    if status_filter:
        query = query.filter(Club.Status == status_filter)
    else:
        query = query.filter(Club.Status == "active")

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(Club.Name.ilike(search_fmt) | Club.Description.ilike(search_fmt))

    total = query.count()
    clubs = query.order_by(Club.Name.asc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for c in clubs:
        member_cnt = (
            db.query(func.count(ClubMembership.MembershipId))
            .filter(ClubMembership.ClubId == c.ClubId, ClubMembership.Status == "active")
            .scalar()
            or 0
        )

        items.append(
            ClubResponse(
                club_id=c.ClubId,
                name=c.Name,
                program_id=c.ProgramId,
                program_name=c.program.FullName if c.program else None,
                branch_id=c.program.BranchId if c.program else None,
                branch_name=c.program.branch.Name if c.program else None,
                manager_user_id=c.ManagerUserId,
                manager_name=c.manager.FullName if c.manager else None,
                description=c.Description,
                status=c.Status,
                created_at=c.CreatedAt,
                member_count=member_cnt,
            )
        )

    return ClubListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{club_id}", response_model=ClubResponse)
def get_club_details(
    club_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve full details and statistics for a specific club."""
    club = db.query(Club).filter(Club.ClubId == club_id).first()
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club with ID {club_id} not found",
        )

    member_cnt = (
        db.query(func.count(ClubMembership.MembershipId))
        .filter(ClubMembership.ClubId == club.ClubId, ClubMembership.Status == "active")
        .scalar()
        or 0
    )

    return ClubResponse(
        club_id=club.ClubId,
        name=club.Name,
        program_id=club.ProgramId,
        program_name=club.program.FullName if club.program else None,
        branch_id=club.program.BranchId if club.program else None,
        branch_name=club.program.branch.Name if club.program else None,
        manager_user_id=club.ManagerUserId,
        manager_name=club.manager.FullName if club.manager else None,
        description=club.Description,
        status=club.Status,
        created_at=club.CreatedAt,
        member_count=member_cnt,
    )


@router.post("", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
def create_club_admin_override(
    payload: ClubCreateRequest,
    current_user: User = Depends(require_roles(RoleNameEnum.ADMINISTRATOR.value)),
    db: Session = Depends(get_db),
):
    """Directly create an active club (Administrator override; regular flow is via proposals)."""
    existing = db.query(Club).filter(Club.Name.ilike(payload.name.strip())).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A club named '{payload.name}' already exists",
        )

    dept = db.query(Program).filter(Program.ProgramId == payload.program_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Program with ID {payload.program_id} not found",
        )

    mgr = db.query(User).filter(User.UserId == payload.manager_user_id).first()
    if not mgr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Manager user with ID {payload.manager_user_id} not found",
        )

    new_club = Club(
        Name=payload.name.strip(),
        ProgramId=payload.program_id,
        ManagerUserId=payload.manager_user_id,
        Description=payload.description,
        Status=payload.status,
    )
    db.add(new_club)
    db.flush()

    # Automatically add manager as an active Lead member
    membership = ClubMembership(
        ClubId=new_club.ClubId,
        UserId=payload.manager_user_id,
        Status="active",
        Role="Lead",
    )
    db.add(membership)

    # Synchronous audit log
    record_audit_log(
        db=db,
        actor_user_id=current_user.UserId,
        action="CLUB_CREATED_DIRECT",
        entity_type="Clubs",
        entity_id=new_club.ClubId,
        details={"name": new_club.Name, "manager_user_id": payload.manager_user_id},
    )

    db.commit()
    db.refresh(new_club)

    return ClubResponse(
        club_id=new_club.ClubId,
        name=new_club.Name,
        program_id=new_club.ProgramId,
        program_name=dept.FullName,
        branch_id=dept.BranchId,
        branch_name=dept.branch.Name,
        manager_user_id=new_club.ManagerUserId,
        manager_name=mgr.FullName,
        description=new_club.Description,
        status=new_club.Status,
        created_at=new_club.CreatedAt,
        member_count=1,
    )


@router.put("/{club_id}", response_model=ClubResponse)
def update_club(
    club_id: int,
    payload: ClubUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update club profile or status. Restricted to Club Manager of this club or Administrator."""
    club = check_club_ownership(club_id=club_id, user=current_user, db=db)

    if payload.name and payload.name.strip() != club.Name:
        duplicate = db.query(Club).filter(
            Club.Name.ilike(payload.name.strip()),
            Club.ClubId != club_id
        ).first()
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A club named '{payload.name}' already exists",
            )
        club.Name = payload.name.strip()

    if payload.description is not None:
        club.Description = payload.description

    if payload.status:
        # Only Administrator can suspend or reactivate clubs
        user_role = normalize_role(current_user.role.RoleName if current_user.role else "")
        if payload.status != club.Status and user_role != RoleNameEnum.ADMINISTRATOR.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only an Administrator can change club status",
            )
        club.Status = payload.status

    if payload.manager_user_id:
        user_role = normalize_role(current_user.role.RoleName if current_user.role else "")
        if user_role != RoleNameEnum.ADMINISTRATOR.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only an Administrator can transfer club ownership",
            )
        new_mgr = db.query(User).filter(User.UserId == payload.manager_user_id).first()
        if not new_mgr:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target manager user does not exist",
            )
        club.ManagerUserId = payload.manager_user_id

    record_audit_log(
        db=db,
        actor_user_id=current_user.UserId,
        action="CLUB_UPDATED",
        entity_type="Clubs",
        entity_id=club.ClubId,
        details={"name": club.Name, "status": club.Status},
    )

    db.commit()
    db.refresh(club)

    member_cnt = (
        db.query(func.count(ClubMembership.MembershipId))
        .filter(ClubMembership.ClubId == club.ClubId, ClubMembership.Status == "active")
        .scalar()
        or 0
    )

    return ClubResponse(
        club_id=club.ClubId,
        name=club.Name,
        program_id=club.ProgramId,
        program_name=club.program.FullName if club.program else None,
        branch_id=club.program.BranchId if club.program else None,
        branch_name=club.program.branch.Name if club.program else None,
        manager_user_id=club.ManagerUserId,
        manager_name=club.manager.FullName if club.manager else None,
        description=club.Description,
        status=club.Status,
        created_at=club.CreatedAt,
        member_count=member_cnt,
    )


@router.post("/{club_id}/join", response_model=MembershipJoinResponse, status_code=status.HTTP_201_CREATED)
def request_join_club(
    club_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Submit a membership request to join a club."""
    club = db.query(Club).filter(Club.ClubId == club_id).first()
    if not club or club.Status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Club not found or is currently not active",
        )

    existing = db.query(ClubMembership).filter(
        ClubMembership.ClubId == club_id,
        ClubMembership.UserId == current_user.UserId
    ).first()

    if existing:
        if existing.Status == "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already an active member of this club",
            )
        elif existing.Status == "requested":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted a pending membership request for this club",
            )
        else:
            # If previously removed, reinstate as requested
            existing.Status = "requested"
            db.commit()
            db.refresh(existing)
            return MembershipJoinResponse(
                membership_id=existing.MembershipId,
                club_id=existing.ClubId,
                user_id=existing.UserId,
                status=existing.Status,
                joined_at=existing.JoinedAt,
            )

    membership = ClubMembership(
        ClubId=club_id,
        UserId=current_user.UserId,
        Status="requested",
        Role="Member",
    )
    db.add(membership)
    db.flush()

    # Notify club manager of membership request
    notification = Notification(
        UserId=club.ManagerUserId,
        Type="MEMBERSHIP_REQUEST",
        Message=f"{current_user.FullName} submitted a membership request for {club.Name}.",
    )
    db.add(notification)

    db.commit()
    db.refresh(membership)

    return MembershipJoinResponse(
        membership_id=membership.MembershipId,
        club_id=membership.ClubId,
        user_id=membership.UserId,
        status=membership.Status,
        joined_at=membership.JoinedAt,
    )


@router.get("/{club_id}/members", response_model=MembershipListResponse)
def list_club_members(
    club_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List members and applicants for a club. Restricted to Club Manager or Administrator."""
    check_club_ownership(club_id=club_id, user=current_user, db=db)

    query = db.query(ClubMembership).filter(ClubMembership.ClubId == club_id)
    if status_filter:
        query = query.filter(ClubMembership.Status == status_filter)

    total = query.count()
    members = query.order_by(ClubMembership.JoinedAt.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        MembershipMemberResponse(
            membership_id=m.MembershipId,
            club_id=m.ClubId,
            user_id=m.UserId,
            full_name=m.user.FullName,
            email=m.user.Email,
            status=m.Status,
            role=m.Role,
            joined_at=m.JoinedAt,
        )
        for m in members
    ]

    return MembershipListResponse(items=items, total=total, page=page, page_size=page_size)


@router.put("/{club_id}/members/{membership_id}", response_model=MembershipMemberResponse)
def update_membership_status(
    club_id: int,
    membership_id: int,
    payload: MembershipUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Approve, reject, or update role of a club member. Restricted to Club Manager or Administrator."""
    club = check_club_ownership(club_id=club_id, user=current_user, db=db)

    membership = db.query(ClubMembership).filter(
        ClubMembership.MembershipId == membership_id,
        ClubMembership.ClubId == club_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership record not found in this club",
        )

    if payload.status:
        membership.Status = payload.status
        # Notify the student
        notif = Notification(
            UserId=membership.UserId,
            Type="MEMBERSHIP_STATUS_UPDATE",
            Message=f"Your membership request for '{club.Name}' has been updated to: {payload.status}.",
        )
        db.add(notif)

    if payload.role:
        membership.Role = payload.role

    record_audit_log(
        db=db,
        actor_user_id=current_user.UserId,
        action="MEMBERSHIP_UPDATED",
        entity_type="ClubMemberships",
        entity_id=membership.MembershipId,
        details={"status": membership.Status, "role": membership.Role, "user_id": membership.UserId},
    )

    db.commit()
    db.refresh(membership)

    return MembershipMemberResponse(
        membership_id=membership.MembershipId,
        club_id=membership.ClubId,
        user_id=membership.UserId,
        full_name=membership.user.FullName,
        email=membership.user.Email,
        status=membership.Status,
        role=membership.Role,
        joined_at=membership.JoinedAt,
    )
