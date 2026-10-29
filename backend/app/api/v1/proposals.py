from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rbac import (
    get_current_active_user,
    require_roles,
    RoleNameEnum,
    normalize_role,
)
from app.core.audit import record_audit_log
from app.models.models import (
    ClubProposal,
    Approval,
    Club,
    ClubMembership,
    Program,
    User,
    Notification,
)
from app.schemas.proposal import (
    ProposalCreateRequest,
    ProposalReviewRequest,
    ApprovalResponse,
    ProposalResponse,
    ProposalListResponse,
)

router = APIRouter(prefix="/proposals", tags=["Club Proposals & Approvals"])


def build_proposal_response(p: ClubProposal, created_club_id: Optional[int] = None) -> ProposalResponse:
    approvals_list = [
        ApprovalResponse(
            approval_id=a.ApprovalId,
            proposal_id=a.ProposalId,
            reviewer_user_id=a.ReviewerUserId,
            reviewer_name=a.reviewer.FullName if a.reviewer else None,
            stage=a.Stage,
            decision=a.Decision,
            comment=a.Comment,
            decided_at=a.DecidedAt,
        )
        for a in (p.approvals or [])
    ]

    return ProposalResponse(
        proposal_id=p.ProposalId,
        applicant_user_id=p.ApplicantUserId,
        applicant_name=p.applicant.FullName if p.applicant else None,
        proposed_name=p.ProposedName,
        program_id=p.ProgramId,
        program_name=p.program.FullName if p.program else None,
        branch_id=p.program.BranchId if p.program else None,
        branch_name=p.program.branch.Name if p.program else None,
        description=p.Description,
        status=p.Status,
        submitted_at=p.SubmittedAt,
        approvals=approvals_list,
        created_club_id=created_club_id,
    )


@router.post("", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
def submit_club_proposal(
    payload: ProposalCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Submit a new university club proposal for Faculty and HOD review."""
    # Check duplicate active club name
    existing_club = db.query(Club).filter(Club.Name.ilike(payload.proposed_name.strip())).first()
    if existing_club:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A club named '{payload.proposed_name}' already exists",
        )

    # Check pending duplicate proposal
    existing_prop = db.query(ClubProposal).filter(
        ClubProposal.ProposedName.ilike(payload.proposed_name.strip()),
        ClubProposal.Status.in_(["submitted", "changes_requested"])
    ).first()
    if existing_prop:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A proposal for '{payload.proposed_name}' is already currently under review",
        )

    dept = db.query(Program).filter(Program.ProgramId == payload.program_id).first()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Program with ID {payload.program_id} not found",
        )

    new_proposal = ClubProposal(
        ApplicantUserId=current_user.UserId,
        ProposedName=payload.proposed_name.strip(),
        ProgramId=payload.program_id,
        Description=payload.description.strip(),
        Status="submitted",
    )
    db.add(new_proposal)
    db.flush()

    record_audit_log(
        db=db,
        actor_user_id=current_user.UserId,
        action="PROPOSAL_SUBMITTED",
        entity_type="ClubProposals",
        entity_id=new_proposal.ProposalId,
        details={"proposed_name": new_proposal.ProposedName, "program_id": payload.program_id},
    )

    db.commit()
    db.refresh(new_proposal)

    return build_proposal_response(new_proposal)


@router.get("", response_model=ProposalListResponse)
def list_proposals(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List proposals accessible to the caller's role (Students see own; Reviewers see pending/all)."""
    user_role = normalize_role(current_user.role.RoleName if current_user.role else "")

    query = db.query(ClubProposal)

    if user_role in (RoleNameEnum.STUDENT.value, RoleNameEnum.CLUB_MANAGER.value):
        # Students and Club Managers only see their own submitted proposals
        query = query.filter(ClubProposal.ApplicantUserId == current_user.UserId)
    elif user_role == RoleNameEnum.FACULTY.value:
        # Faculty sees proposals in their department or all submitted
        if current_user.ProgramId and current_user.program:
            qdept = db.query(Program).filter(Program.ProgramId == current_user.ProgramId).first()
            if qdept:
                query = query.join(Program, ClubProposal.ProgramId == Program.ProgramId)
                query = query.filter(Program.BranchId == qdept.BranchId)
    elif user_role == RoleNameEnum.HOD.value:
        # HOD sees department proposals or all
        if current_user.ProgramId and current_user.program:
            qdept = db.query(Program).filter(Program.ProgramId == current_user.ProgramId).first()
            if qdept:
                query = query.join(Program, ClubProposal.ProgramId == Program.ProgramId)
                query = query.filter(Program.BranchId == qdept.BranchId)
    # Administrator sees all

    if status_filter:
        query = query.filter(ClubProposal.Status == status_filter)

    total = query.count()
    proposals = query.order_by(ClubProposal.SubmittedAt.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [build_proposal_response(p) for p in proposals]
    return ProposalListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{proposal_id}", response_model=ProposalResponse)
def get_proposal_details(
    proposal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve full proposal record with recorded review decisions."""
    proposal = db.query(ClubProposal).filter(ClubProposal.ProposalId == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    user_role = normalize_role(current_user.role.RoleName if current_user.role else "")
    if user_role in (RoleNameEnum.STUDENT.value, RoleNameEnum.CLUB_MANAGER.value):
        if proposal.ApplicantUserId != current_user.UserId:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this proposal",
            )

    created_club = db.query(Club).filter(Club.Name == proposal.ProposedName).first()
    created_club_id = created_club.ClubId if created_club else None

    return build_proposal_response(proposal, created_club_id=created_club_id)


@router.post("/{proposal_id}/review", response_model=ProposalResponse)
def review_proposal(
    proposal_id: int,
    payload: ProposalReviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Record a Faculty or HOD review decision. Final HOD approval activates the club automatically.

    CRITICAL WORKFLOW & SECURITY RULES:
    1. Students & Club Managers are strictly rejected with 403 Forbidden.
    2. Faculty reviewer records stage='faculty'.
    3. HOD reviewer records stage='hod'. Administrator can act at either stage.
    4. Reject / changes_requested decisions require a mandatory comment.
    5. HOD approval activates the new club, assigns the applicant as Manager, and writes an AuditLog.
    """
    user_role = normalize_role(current_user.role.RoleName if current_user.role else "")

    if user_role not in (RoleNameEnum.FACULTY.value, RoleNameEnum.HOD.value, RoleNameEnum.ADMINISTRATOR.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Faculty, HOD, or Administrator accounts are authorized to review proposals",
        )

    proposal = db.query(ClubProposal).filter(ClubProposal.ProposalId == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    if proposal.Status in ("approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Proposal has already been finalized with status '{proposal.Status}'",
        )

    # Determine Review Stage
    stage = "faculty" if user_role == RoleNameEnum.FACULTY.value else "hod"

    # Validate Comment on rejection or changes_requested
    if payload.decision in ("reject", "changes_requested") and (not payload.comment or not payload.comment.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A non-empty comment is mandatory when decision is '{payload.decision}'",
        )

    # Record the Approval entity
    approval_record = Approval(
        ProposalId=proposal.ProposalId,
        ReviewerUserId=current_user.UserId,
        Stage=stage,
        Decision=payload.decision,
        Comment=payload.comment.strip() if payload.comment else None,
    )
    db.add(approval_record)

    created_club_id = None

    if payload.decision == "reject":
        proposal.Status = "rejected"
        action_name = f"PROPOSAL_REJECTED_{stage.upper()}"
    elif payload.decision == "changes_requested":
        proposal.Status = "changes_requested"
        action_name = f"PROPOSAL_CHANGES_REQUESTED_{stage.upper()}"
    elif payload.decision == "approve":
        if stage == "faculty":
            # Faculty recommendation — stays in progress towards HOD
            action_name = "PROPOSAL_FACULTY_RECOMMENDED"
            # Proposal remains available for HOD
        elif stage == "hod":
            # Final Approval by HOD / Admin: Activate Club!
            proposal.Status = "approved"
            action_name = "PROPOSAL_HOD_APPROVED_AND_ACTIVATED"

            # Check duplicate before creating club
            existing_club = db.query(Club).filter(Club.Name.ilike(proposal.ProposedName.strip())).first()
            if not existing_club:
                new_club = Club(
                    Name=proposal.ProposedName.strip(),
                    ProgramId=proposal.ProgramId,
                    ManagerUserId=proposal.ApplicantUserId,
                    Description=proposal.Description,
                    Status="active",
                )
                db.add(new_club)
                db.flush()

                # Add applicant as active Lead member
                lead_membership = ClubMembership(
                    ClubId=new_club.ClubId,
                    UserId=proposal.ApplicantUserId,
                    Status="active",
                    Role="Lead",
                )
                db.add(lead_membership)
                created_club_id = new_club.ClubId
            else:
                existing_club.Status = "active"
                created_club_id = existing_club.ClubId

    # Create notification for applicant
    notif = Notification(
        UserId=proposal.ApplicantUserId,
        Type=f"PROPOSAL_{payload.decision.upper()}",
        Message=f"Your club proposal '{proposal.ProposedName}' was reviewed by {current_user.FullName} ({stage.upper()}): {payload.decision}." + (f" Note: {payload.comment}" if payload.comment else ""),
    )
    db.add(notif)

    # SYNCHRONOUS AUDIT LOG IN THE SAME TRANSACTION
    record_audit_log(
        db=db,
        actor_user_id=current_user.UserId,
        action=action_name,
        entity_type="ClubProposals",
        entity_id=proposal.ProposalId,
        details={
            "stage": stage,
            "decision": payload.decision,
            "comment": payload.comment,
            "new_status": proposal.Status,
            "created_club_id": created_club_id,
        },
    )

    db.commit()
    db.refresh(proposal)

    return build_proposal_response(proposal, created_club_id=created_club_id)
