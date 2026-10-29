from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator


class ProposalCreateRequest(BaseModel):
    proposed_name: str = Field(..., min_length=2, max_length=150)
    program_id: int
    description: str = Field(..., min_length=10)


class ProposalReviewRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject|changes_requested)$")
    comment: Optional[str] = None

    @model_validator(mode="after")
    def validate_comment_on_rejection(self) -> "ProposalReviewRequest":
        if self.decision in ("reject", "changes_requested"):
            if not self.comment or not self.comment.strip():
                raise ValueError(f"A descriptive comment is required when decision is '{self.decision}'")
        return self


class ApprovalResponse(BaseModel):
    approval_id: int
    proposal_id: int
    reviewer_user_id: int
    reviewer_name: Optional[str] = None
    stage: str
    decision: str
    comment: Optional[str] = None
    decided_at: datetime

    class Config:
        from_attributes = True


class ProposalResponse(BaseModel):
    proposal_id: int
    applicant_user_id: int
    applicant_name: Optional[str] = None
    proposed_name: str
    program_id: int
    program_name: Optional[str] = None
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    description: str
    status: str
    submitted_at: datetime
    approvals: List[ApprovalResponse] = []
    created_club_id: Optional[int] = None

    class Config:
        from_attributes = True


class ProposalListResponse(BaseModel):
    items: List[ProposalResponse]
    total: int
    page: int
    page_size: int
