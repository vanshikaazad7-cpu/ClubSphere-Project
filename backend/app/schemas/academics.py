"""Pydantic schemas for academic structure (branches + programs).

Used to serve the cascading dropdowns in the UI.
"""
from typing import List, Optional
from pydantic import BaseModel


class ProgramInBranchResponse(BaseModel):
    program_id: int
    program_key: str
    name: str
    full_name: str
    collaboration_partner: Optional[str] = None
    sort_order: int

    class Config:
        from_attributes = True


class BranchResponse(BaseModel):
    branch_id: int
    branch_key: str
    name: str
    degree_level: str
    sort_order: int
    programs: List[ProgramInBranchResponse] = []

    class Config:
        from_attributes = True


class BranchListResponse(BaseModel):
    items: List[BranchResponse]
    total: int
