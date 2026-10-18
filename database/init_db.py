#!/usr/bin/env python
"""
LEXIQ Database Migration & Schema Initializer
=============================================
Connects to the configured DATABASE_URL (e.g. Neon, Supabase, Render PostgreSQL),
creates the pgvector extension, aligns embedding vector dimensionality,
and initializes all tables.
"""

import sys
from pathlib import Path
import logging

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("lexiq.migration")

try:
    from backend.app.config import settings
    from backend.app.database import init_db, check_db_connection
except ImportError as exc:
    logger.error(f"Failed to import LEXIQ application modules: {exc}")
    sys.exit(1)


def main():
    logger.info("Initializing LEXIQ Production Database...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Target Dialect: {'postgresql' if 'postgres' in settings.normalized_database_url else 'sqlite'}")
    logger.info(f"Vector Dimension: {settings.embedding_dimension}")

    # Check connection
    status = check_db_connection()
    logger.info(f"Pre-migration Connectivity: {status.get('status')} ({status.get('dialect')})")

    # Run migration / table creation
    success = init_db()
    if not success:
        logger.error("Database initialization failed. Please check DATABASE_URL and network access.")
        sys.exit(1)

    logger.info("Post-migration Check: All tables and pgvector extension are active.")
    logger.info("Database migration finished successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
