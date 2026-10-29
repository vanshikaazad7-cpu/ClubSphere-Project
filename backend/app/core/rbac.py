from typing import List, Callable, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import bearer_scheme, decode_token
from app.models.models import User, Club, RoleNameEnum


def normalize_role(role_name: str) -> str:
    """Normalize role string to canonical enum value."""
    cleaned = role_name.strip().lower().replace(" ", "").replace("_", "")
    mapping = {
        "student": RoleNameEnum.STUDENT.value,
        "clubmanager": RoleNameEnum.CLUB_MANAGER.value,
        "manager": RoleNameEnum.CLUB_MANAGER.value,
        "faculty": RoleNameEnum.FACULTY.value,
        "hod": RoleNameEnum.HOD.value,
        "admin": RoleNameEnum.ADMINISTRATOR.value,
        "administrator": RoleNameEnum.ADMINISTRATOR.value,
    }
    return mapping.get(cleaned, role_name)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the currently authenticated user from Bearer JWT."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for API access. Access token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject format in token",
        )

    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists",
        )

    if not user.IsActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or disabled",
        )

    token_version = payload.get("token_version")
    if token_version is not None and token_version != user.TokenVersion:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or invalidated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure current user is active."""
    if not current_user.IsActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


def require_roles(*allowed_roles: str) -> Callable:
    """FastAPI dependency factory enforcing server-side Role-Based Access Control."""
    canonical_allowed = {normalize_role(r) for r in allowed_roles}

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_role_str = current_user.role.RoleName if current_user.role else ""
        canonical_user_role = normalize_role(user_role_str)

        # Administrator has global override on protected routes unless explicitly restricted
        if canonical_user_role == RoleNameEnum.ADMINISTRATOR.value or canonical_user_role in canonical_allowed:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted. Required role: {', '.join(allowed_roles)}. Current role: {user_role_str}",
        )

    return role_checker


def check_club_ownership(club_id: int, user: User, db: Session) -> Club:
    """Verify that user is the manager of the specified club or an administrator."""
    club = db.query(Club).filter(Club.ClubId == club_id).first()
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club with ID {club_id} not found",
        )

    user_role = normalize_role(user.role.RoleName if user.role else "")
    if user_role == RoleNameEnum.ADMINISTRATOR.value:
        return club

    if club.ManagerUserId != user.UserId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have management authority over this club",
        )

    return club
