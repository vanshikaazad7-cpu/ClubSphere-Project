"""Public endpoints exposing the academic structure (branches + programs).

Serves the cascading dropdowns: first select a master branch, then pick a specialization.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.models import Branch
from app.schemas.academics import BranchListResponse, BranchResponse, ProgramInBranchResponse

router = APIRouter(prefix="/branches", tags=["academics"])


def _to_branch_response(b: Branch) -> BranchResponse:
    """Map a Branch ORM row (PascalCase columns) onto the API schema (snake_case fields)."""
    return BranchResponse(
        branch_id=b.BranchId,
        branch_key=b.BranchKey,
        name=b.Name,
        degree_level=b.DegreeLevel,
        sort_order=b.SortOrder,
        programs=[
            ProgramInBranchResponse(
                program_id=p.ProgramId,
                program_key=p.ProgramKey,
                name=p.Name,
                full_name=p.FullName,
                collaboration_partner=p.CollaborationPartner,
                sort_order=p.SortOrder,
            )
            for p in sorted(b.programs, key=lambda x: (x.SortOrder, x.Name))
        ],
    )


@router.get("", response_model=BranchListResponse)
def list_branches(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all branches with their nested programs, sorted for UI display."""
    q = (
        db.query(Branch)
        .options(joinedload(Branch.programs))
        .order_by(asc(Branch.SortOrder), asc(Branch.Name))
    )
    total = q.count()
    offset = (page - 1) * page_size
    rows = q.offset(offset).limit(page_size).all()
    items = [_to_branch_response(r) for r in rows]
    return BranchListResponse(items=items, total=total)


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(branch_id: int, db: Session = Depends(get_db)):
    branch = (
        db.query(Branch)
        .options(joinedload(Branch.programs))
        .filter(Branch.BranchId == branch_id)
        .first()
    )
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found",
        )
    return _to_branch_response(branch)
