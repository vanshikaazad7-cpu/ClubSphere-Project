from datetime import datetime, timezone
import time
import threading
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.rbac import get_current_active_user, normalize_role
from app.models.models import User, Role, Program, RoleNameEnum
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory thread-safe rate limiter for failed login attempts
_login_failures: Dict[str, List[float]] = {}
_failures_lock = threading.Lock()


def _check_rate_limit(key: str):
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    max_attempts = settings.RATE_LIMIT_LOGIN_ATTEMPTS
    with _failures_lock:
        timestamps = _login_failures.get(key, [])
        # Keep only timestamps within window
        valid_timestamps = [t for t in timestamps if now - t < window]
        _login_failures[key] = valid_timestamps
        if len(valid_timestamps) >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again after {int(window - (now - valid_timestamps[0]))} seconds.",
            )


def _record_login_failure(key: str):
    now = time.time()
    with _failures_lock:
        if key not in _login_failures:
            _login_failures[key] = []
        _login_failures[key].append(now)


def _clear_login_failures(key: str):
    with _failures_lock:
        _login_failures.pop(key, None)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new student user. Other roles are assigned by an Administrator."""
    existing_user = db.query(User).filter(User.Email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address is already registered",
        )

    # Resolve default Student role
    student_role = db.query(Role).filter(Role.RoleName == RoleNameEnum.STUDENT.value).first()
    if not student_role:
        # Seed student role if not yet present
        student_role = Role(RoleName=RoleNameEnum.STUDENT.value)
        db.add(student_role)
        db.flush()

    if payload.program_id:
        prog = db.query(Program).filter(Program.ProgramId == payload.program_id).first()
        if not prog:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Program with ID {payload.program_id} does not exist",
            )

    new_user = User(
        Email=payload.email.lower(),
        PasswordHash=get_password_hash(payload.password),
        FullName=payload.full_name,
        RoleId=student_role.RoleId,
        ProgramId=payload.program_id,
        IsActive=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        user_id=new_user.UserId,
        email=new_user.Email,
        full_name=new_user.FullName,
        role=new_user.role.RoleName,
        program_id=new_user.ProgramId,
        program_name=new_user.program.FullName if new_user.program else None,
        branch_id=new_user.program.BranchId if new_user.program else None,
        branch_name=new_user.program.branch.Name if new_user.program else None,
        is_active=new_user.IsActive,
        created_at=new_user.CreatedAt,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate with email and password to receive JWT access and refresh tokens."""
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{payload.email.lower()}"

    _check_rate_limit(rate_key)

    user = db.query(User).filter(User.Email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.PasswordHash):
        _record_login_failure(rate_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.IsActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or disabled. Contact administrator.",
        )

    # Clear previous failures on successful authentication
    _clear_login_failures(rate_key)

    role_name = user.role.RoleName if user.role else RoleNameEnum.STUDENT.value
    access_token = create_access_token(
        subject=user.UserId,
        role=role_name,
        token_version=user.TokenVersion,
    )
    refresh_token = create_refresh_token(
        subject=user.UserId,
        role=role_name,
        token_version=user.TokenVersion,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=900,
        role=role_name,
        user_id=user.UserId,
        full_name=user.FullName,
        email=user.Email,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(
    payload: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token and rotated refresh token."""
    decoded = decode_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided token is not a valid refresh token",
        )

    user_id = int(decoded["sub"])
    user = db.query(User).filter(User.UserId == user_id).first()
    if not user or not user.IsActive:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active or exists",
        )

    token_ver = decoded.get("token_version")
    if token_ver is not None and token_ver != user.TokenVersion:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or invalidated. Please log in again.",
        )

    role_name = user.role.RoleName if user.role else RoleNameEnum.STUDENT.value
    new_access_token = create_access_token(
        subject=user.UserId,
        role=role_name,
        token_version=user.TokenVersion,
    )
    new_refresh_token = create_refresh_token(
        subject=user.UserId,
        role=role_name,
        token_version=user.TokenVersion,
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=900,
        role=role_name,
        user_id=user.UserId,
        full_name=user.FullName,
        email=user.Email,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke all active sessions and refresh tokens for current user by incrementing TokenVersion."""
    current_user.TokenVersion += 1
    db.commit()
    return {"message": "Successfully logged out. All active sessions have been revoked."}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Get the currently authenticated user's profile details."""
    return UserResponse(
        user_id=current_user.UserId,
        email=current_user.Email,
        full_name=current_user.FullName,
        role=current_user.role.RoleName if current_user.role else RoleNameEnum.STUDENT.value,
        program_id=current_user.ProgramId,
        program_name=current_user.program.FullName if current_user.program else None,
        branch_id=current_user.program.BranchId if current_user.program else None,
        branch_name=current_user.program.branch.Name if current_user.program else None,
        is_active=current_user.IsActive,
        created_at=current_user.CreatedAt,
    )
