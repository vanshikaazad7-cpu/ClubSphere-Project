from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ClubCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    program_id: int
    manager_user_id: int
    description: Optional[str] = None
    status: str = Field(default="active", pattern="^(pending|active|suspended)$")


class ClubUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|active|suspended)$")
    manager_user_id: Optional[int] = None


class ClubResponse(BaseModel):
    club_id: int
    name: str
    program_id: int
    program_name: Optional[str] = None
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    manager_user_id: int
    manager_name: Optional[str] = None
    description: Optional[str] = None
    status: str
    created_at: datetime
    member_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ClubListResponse(BaseModel):
    items: List[ClubResponse]
    total: int
    page: int
    page_size: int


class MembershipJoinResponse(BaseModel):
    membership_id: int
    club_id: int
    user_id: int
    status: str
    joined_at: datetime


class MembershipUpdateRequest(BaseModel):
    status: Optional[str] = Field(None, pattern="^(requested|active|removed)$")
    role: Optional[str] = Field(None, pattern="^(Member|Lead)$")


class MembershipMemberResponse(BaseModel):
    membership_id: int
    club_id: int
    user_id: int
    full_name: str
    email: str
    status: str
    role: str
    joined_at: datetime


class MembershipListResponse(BaseModel):
    items: List[MembershipMemberResponse]
    total: int
    page: int
    page_size: int
