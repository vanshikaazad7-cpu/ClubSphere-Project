from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from app.core.database import get_db, check_db_health
from app.core.config import settings

router = APIRouter(tags=["Health & Smoke Verification"])


@router.get("/health")
def health_check(response: Response, db: Session = Depends(get_db)):
    """Health and readiness probe for container orchestrators and smoke verification."""
    is_db_healthy = check_db_health(db)
    timestamp = datetime.now(timezone.utc).isoformat()

    if not is_db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "degraded",
            "app": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
            "database": "disconnected",
            "timestamp": timestamp,
        }

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "connected",
        "timestamp": timestamp,
    }
