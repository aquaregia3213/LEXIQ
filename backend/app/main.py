import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse

# Legacy routers for 100% backward-compatibility with existing unit tests
from backend.app.api.health import router as legacy_health_router
from backend.app.api.contracts import router as legacy_contracts_router
from backend.app.api.search import router as legacy_search_router
from backend.app.api.rag import router as legacy_rag_router
from backend.app.api.entities import router as legacy_entities_router
from backend.app.api.clauses import router as legacy_clauses_router
from backend.app.api.graph import router as legacy_graph_router
from backend.app.api.risks import router as legacy_risks_router

# v1 REST API Router
from backend.app.api.v1 import v1_router
from backend.app.config import settings
from backend.app.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("legal_ai")

# Initialize database tables
init_db()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Execute startup diagnostics, validate configuration, and log structured operational parameters."""
    from backend.app.database import check_db_connection
    from ingestion.pipeline.ingestor import ensure_upload_dir

    logger.info("=" * 60)
    logger.info("Starting LEXIQ Legal Contract Intelligence API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Active AI Provider: {settings.active_ai_provider}")
    logger.info(f"LLM Model: {settings.GEMINI_MODEL if settings.active_ai_provider == 'gemini' else 'deterministic'}")
    logger.info(f"Embedding Model: {settings.GEMINI_EMBEDDING_MODEL if settings.active_ai_provider == 'gemini' else 'deterministic'}")
    logger.info(f"Embedding Dimension: {settings.embedding_dimension}")
    logger.info(f"Agent Orchestrator: {settings.AGENT_ORCHESTRATOR}")
    logger.info(f"Gemini API Key: {settings.mask_credential(settings.GEMINI_API_KEY)}")

    # Database connectivity check
    db_status = check_db_connection()
    logger.info(f"Database Connection: {db_status.get('status')} (Dialect: {db_status.get('dialect')})")

    if settings.ENVIRONMENT == "production":
        if "sqlite" in settings.normalized_database_url.lower():
            logger.critical("PRODUCTION WARNING: SQLite is active in production environment. A managed PostgreSQL database with pgvector is strongly recommended.")
        if settings.active_ai_provider == "gemini" and not settings.GEMINI_API_KEY:
            logger.error("PRODUCTION CONFIGURATION ERROR: GEMINI_API_KEY is missing while AI_PROVIDER=gemini.")

    # Storage check
    upload_path = ensure_upload_dir()
    logger.info(f"Persistent Upload Directory: {upload_path}")
    logger.info(f"Configured Allowed CORS Origins: {settings.cors_origins_list}")
    logger.info("=" * 60)

    yield


# Initialize FastAPI application with comprehensive OpenAPI metadata
app = FastAPI(
    title="Legal AI Contract Intelligence Platform API",
    description="""
Enterprise AI-powered Legal Tech platform REST API for contract intelligence.

### Key Capabilities
* **Contracts**: PDF/DOCX ingestion, lifecycle tracking, metadata retrieval, document chunk inspection.
* **Semantic Search**: Dense vector similarity search with contract, section, and metadata filtering.
* **Grounded RAG QA**: Hallucination-resistant question answering with page-level source citations and evidence checks.
* **Clause Extraction**: Identification and taxonomy classification across 12 standard legal clause categories.
* **Entity Extraction**: Canonical entity extraction (companies, persons, dates, amounts, jurisdictions).
* **Obligations**: Contractual commitments, responsible parties, and temporal deadlines.
* **Risk Analysis**: AI-assisted risk detection (liability, indemnification, renewal, termination, IP) with safety disclaimers.
* **Knowledge Graph**: Subgraph generation and multi-hop traversal queries for company and jurisdiction relations.
* **Agentic AI**: Autonomous ReAct and Langflow multi-step contract investigation with verifiable source citations.
* **eCourts**: Indian case status coordinates, CNR validation, and procedural risk analysis.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS middleware with environment-driven origins
cors_origins = settings.cors_origins_list
logger.info(f"Configuring CORS with allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


def _status_code_to_error_code(status_code: int) -> str:
    """Map HTTP status codes to standardized error code strings."""
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    return code_map.get(status_code, "ERROR")


# Custom Exception Handler: HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standardize HTTP error responses ensuring both 'detail' (for backward compatibility)
    and structured 'error' (code, message) are returned.
    """
    error_code = _status_code_to_error_code(exc.status_code)
    message = str(exc.detail) if isinstance(exc.detail, str) else str(exc.detail)

    if isinstance(exc.detail, dict) and "error" in exc.detail:
        error_payload = exc.detail["error"]
        detail_msg = error_payload.get("message", str(exc.detail))
    else:
        error_payload = {
            "code": error_code,
            "message": message
        }
        detail_msg = message

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": detail_msg,
            "error": error_payload
        }
    )


# Custom Exception Handler: RequestValidationError (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Clean validation error formatting without leaking stack traces."""
    clean_errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        clean_errors.append({
            "field": loc,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error")
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed.",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "One or more request parameters are invalid.",
                "details": clean_errors
            }
        }
    )


# Custom Exception Handler: Unhandled Exceptions (500)
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch unhandled errors, log details internally, and return safe 500 response."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please contact system support."
            }
        }
    )


# Custom Exception Handler: GeminiProviderError
from backend.app.services.gemini_service import GeminiProviderError

@app.exception_handler(GeminiProviderError)
async def gemini_provider_exception_handler(request: Request, exc: GeminiProviderError):
    """Transparently return Gemini AI provider errors without fake silent answers."""
    logger.error(f"Gemini provider error on {request.method} {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error": {
                "code": "AI_PROVIDER_ERROR",
                "message": exc.message,
                "provider": "google-gemini",
                "model": settings.GEMINI_MODEL
            }
        }
    )


# Mount v1 REST API Router
app.include_router(v1_router)

# Mount Legacy routes for 100% backward-compatibility with existing unit tests
app.include_router(legacy_health_router)
app.include_router(legacy_contracts_router)
app.include_router(legacy_search_router)
app.include_router(legacy_rag_router)
app.include_router(legacy_entities_router)
app.include_router(legacy_clauses_router)
app.include_router(legacy_graph_router)
app.include_router(legacy_risks_router)


@app.get("/health", tags=["Health"], summary="Root health endpoint")
def root_health():
    """Convenience root health endpoint with AI provider status."""
    from backend.app.database import check_db_connection
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "service": "Legal AI Contract Intelligence API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": check_db_connection(),
        "ai_provider": {
            "provider": settings.active_ai_provider,
            "llm_model": settings.GEMINI_MODEL if settings.active_ai_provider == "gemini" else "deterministic",
            "embedding_model": settings.GEMINI_EMBEDDING_MODEL if settings.active_ai_provider == "gemini" else "deterministic",
            "embedding_dimension": settings.embedding_dimension,
            "is_configured": bool(settings.GEMINI_API_KEY) if settings.active_ai_provider == "gemini" else True
        }
    }


@app.get("/health/ready", tags=["Health"], summary="Root readiness endpoint")
def root_health_ready():
    """Convenience root readiness endpoint verifying database connectivity."""
    from backend.app.database import check_db_connection
    from datetime import datetime, timezone
    db_info = check_db_connection()
    is_ready = db_info.get("status") == "connected"
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "not_ready",
            "database": db_info,
            "ai_provider_configured": bool(settings.GEMINI_API_KEY) if settings.active_ai_provider == "gemini" else True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


@app.get("/health/config", tags=["Health"], summary="Safe configuration summary")
def root_health_config():
    """Returns safe, non-sensitive operational configuration flags."""
    return settings.get_sanitized_config_summary()


@app.get("/", include_in_schema=False)
def root():
    """Root route redirecting to interactive Swagger API documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", settings.PORT))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = settings.ENVIRONMENT != "production"
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=reload
    )
