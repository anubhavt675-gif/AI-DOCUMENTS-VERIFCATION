"""
Health check router.
"""
from fastapi import APIRouter

from app.config import get_settings
from app.schemas.document import HealthResponse

settings = get_settings()
router = APIRouter(tags=["Health"])


@router.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Service health check",
)
def health_check():
    return HealthResponse(
        status="ok",
        service="document-integrity-api",
        version=settings.app_version,
    )
