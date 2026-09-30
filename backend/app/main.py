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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("legal_ai")

# Initialize database tables
init_db()

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
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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
    """Convenience root health endpoint."""
    from backend.app.database import check_db_connection
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "service": "Legal AI Contract Intelligence API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": check_db_connection()
    }


@app.get("/", include_in_schema=False)
def root():
    """Root route redirecting to interactive Swagger API documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
