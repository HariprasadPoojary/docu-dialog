"""Version 1 API router."""

from fastapi import APIRouter

from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router
from app.api.v1.projects import router as projects_router

router = APIRouter()
router.include_router(health_router)
router.include_router(projects_router)
router.include_router(documents_router)
