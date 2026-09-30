from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.database import check_db_connection

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="System health diagnostic check",
    description="Returns API service health status, runtime environment, version, and database connectivity diagnostic information."
)
def get_health_status():
    db_info = check_db_connection()
    return {
        "status": "ok",
        "service": "Legal AI Contract Intelligence API",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_info
    }
