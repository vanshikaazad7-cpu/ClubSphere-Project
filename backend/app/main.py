from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List
from fastapi import FastAPI, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, Base, get_db, check_db_health
from app.models.models import Role, RoleNameEnum
from app.api.v1.router import api_v1_router
from app.core.academic_seed import seed_academic_data


def seed_baseline_data():
    """Ensure baseline roles and academic data (branches + programs) exist for local development and testing."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        # Seed Roles
        for role_name in [
            RoleNameEnum.STUDENT.value,
            RoleNameEnum.CLUB_MANAGER.value,
            RoleNameEnum.FACULTY.value,
            RoleNameEnum.HOD.value,
            RoleNameEnum.ADMINISTRATOR.value,
        ]:
            existing_role = db.query(Role).filter(Role.RoleName == role_name).first()
            if not existing_role:
                db.add(Role(RoleName=role_name))

        db.commit()

        # Seed academic data (branches + programs) from JSON if empty
        summary = seed_academic_data(db)
        if summary.get("seeded"):
            print(
                f"Academic seed: {summary['branches']} branches, {summary['programs']} programs loaded."
            )
    except Exception as e:
        db.rollback()
        print(f"Baseline seed warning: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables and baseline seed data exist when running in dev/test SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        seed_baseline_data()
    yield
    # Shutdown logic if needed


def create_application() -> FastAPI:
    app = FastAPI(
        title="ClubSphere API",
        version="1.0.0",
        description="University Club & Activity Lifecycle Management System — Backend REST APIs",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS Middleware
    origins = settings.CORS_ORIGINS
    if isinstance(origins, str):
        origins_list = [o.strip() for o in origins.split(",")]
    else:
        origins_list = origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root health smoke check
    @app.get("/health", tags=["Health"])
    def root_health_check(db: Session = Depends(get_db)):
        is_db_healthy = check_db_health(db)
        timestamp = datetime.now(timezone.utc).isoformat()
        if not is_db_healthy:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "degraded",
                    "app": settings.APP_NAME,
                    "database": "disconnected",
                    "timestamp": timestamp,
                },
            )
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
            "database": "connected",
            "timestamp": timestamp,
        }

    # Mount versioned API routes
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
