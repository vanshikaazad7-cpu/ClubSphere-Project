from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2, max_length=150)
    program_id: Optional[int] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    role: str
    user_id: int
    full_name: str
    email: str


class UserBrief(BaseModel):
    user_id: int
    email: str
    full_name: str
    role: str
    program_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user_id: int
    email: str
    full_name: str
    role: str
    program_id: Optional[int] = None
    program_name: Optional[str] = None
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
