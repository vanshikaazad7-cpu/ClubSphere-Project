from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.clubs import router as clubs_router
from app.api.v1.events import router as events_router
from app.api.v1.proposals import router as proposals_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.admin import router as admin_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.health import router as health_router
from app.api.v1.academics import router as academics_router
from app.api.v1.meta import router as meta_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(clubs_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(proposals_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(uploads_router)
api_v1_router.include_router(academics_router)
api_v1_router.include_router(meta_router)
