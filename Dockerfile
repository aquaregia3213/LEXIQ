# =========================================================================
# LEXIQ Backend Production Dockerfile
# Optimized multi-stage build for FastAPI, pgvector, and Google Gemini
# =========================================================================

FROM python:3.11-slim as base

# Set environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    ENVIRONMENT=production

# Install system dependencies (build essentials, libpq for psycopg2, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifest
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY database/ ./database/
COPY ingestion/ ./ingestion/
COPY flows/ ./flows/

# Create persistent uploads directory
RUN mkdir -p uploads/contracts

# Non-root security user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose service port
EXPOSE 8000

# Health check probe against readiness endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Production entrypoint with Gunicorn and Uvicorn workers
CMD ["sh", "-c", "python database/init_db.py && gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.app.main:app -b 0.0.0.0:${PORT} --access-logfile - --error-logfile -"]
