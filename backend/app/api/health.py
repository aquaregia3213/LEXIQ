from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.database import check_db_connection

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def get_health_status():
    """Health check endpoint returning system status and component diagnostic info."""
    db_info = check_db_connection()
    return {
        "status": "ok",
        "service": "Legal AI Contract Intelligence API",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_info
    }
