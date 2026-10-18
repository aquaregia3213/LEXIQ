import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from backend.app.config import settings
from backend.app.database import check_db_connection

logger = logging.getLogger("legal_ai.health")
router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="System liveness check",
    description="Returns API service health status, runtime environment, version, and database connectivity diagnostic information."
)
def get_health_status():
    db_info = check_db_connection()
    return {
        "status": "ok",
        "service": "Legal AI Contract Intelligence API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_info,
        "ai_provider": {
            "provider": settings.active_ai_provider,
            "llm_model": settings.GEMINI_MODEL if settings.active_ai_provider == "gemini" else "deterministic",
            "embedding_model": settings.GEMINI_EMBEDDING_MODEL if settings.active_ai_provider == "gemini" else "deterministic",
            "embedding_dimension": settings.embedding_dimension,
            "is_configured": bool(settings.GEMINI_API_KEY) if settings.active_ai_provider == "gemini" else True
        }
    }


@router.get(
    "/health/ready",
    summary="System readiness diagnostic check",
    description="Checks whether the application is ready to accept production traffic (database connection verified)."
)
def get_readiness_status(response: Response):
    db_info = check_db_connection()
    is_db_connected = db_info.get("status") == "connected"

    # In production, database must be connected for readiness
    if not is_db_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "reason": "Database connection is unavailable.",
            "database": db_info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    return {
        "status": "ready",
        "database": db_info,
        "ai_provider_configured": bool(settings.GEMINI_API_KEY) if settings.active_ai_provider == "gemini" else True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get(
    "/health/config",
    summary="Sanitized configuration diagnostic",
    description="Inspect active runtime configuration settings with all secrets strictly masked."
)
def get_sanitized_config():
    return settings.get_sanitized_config_summary()
