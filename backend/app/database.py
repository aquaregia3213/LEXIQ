import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Base class for ORM models
Base = declarative_base()

# Configure SQLAlchemy engine (lazy setup with fallback)
def create_app_engine(database_url: str = None):
    url = database_url or settings.normalized_database_url
    if not url:
        return None
    try:
        if url.startswith("postgresql"):
            try:
                return create_engine(
                    url,
                    pool_pre_ping=True,
                    connect_args={"connect_timeout": 5}
                )
            except Exception as inner_err:
                # If default driver (psycopg 3) is missing, attempt fallback to psycopg2
                if "psycopg" in str(inner_err).lower() and "postgresql://" in url:
                    fallback_url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
                    return create_engine(
                        fallback_url,
                        pool_pre_ping=True,
                        connect_args={"connect_timeout": 5}
                    )
                raise inner_err
        else:
            return create_engine(
                url,
                connect_args={"check_same_thread": False} if "sqlite" in url else {}
            )
    except Exception as e:
        logger.warning(f"Failed to initialize database engine: {e}")
        return None


engine = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None


def init_db(target_engine=None):
    """Initialize database tables and create pgvector extension if connected to PostgreSQL."""
    global engine, SessionLocal
    db_engine = target_engine or engine
    if not db_engine:
        logger.warning("Cannot initialize DB tables: Engine is None")
        return False
    
    try:
        # Import models so Base.metadata collects all table definitions
        import backend.app.models.models  # noqa: F401
        
        # If PostgreSQL, enable pgvector extension and verify vector dimensionality
        if db_engine.dialect.name == "postgresql":
            with db_engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                
                # Check if chunks table already exists with mismatched vector dimension
                target_dim = settings.embedding_dimension
                check_dim_sql = text("""
                    SELECT atttypmod
                    FROM pg_attribute
                    JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
                    JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid
                    WHERE pg_class.relname = 'chunks'
                      AND pg_attribute.attname = 'embedding'
                      AND pg_namespace.nspname = 'public';
                """)
                existing_dim = conn.execute(check_dim_sql).scalar()
                if existing_dim is not None and existing_dim > 0 and existing_dim != target_dim:
                    logger.info(
                        f"PostgreSQL pgvector: migrating 'chunks.embedding' dimension from {existing_dim} to {target_dim}."
                    )
                    conn.execute(text(f"ALTER TABLE chunks ALTER COLUMN embedding TYPE vector({target_dim}) USING NULL;"))
                
                conn.commit()
                logger.info("Successfully checked pgvector extension and schema in PostgreSQL.")
        
        Base.metadata.create_all(bind=db_engine)
        logger.info("All database tables created successfully.")
        return True
    except Exception as err:
        logger.error(f"Primary database connection/initialization failed: {err}")
        # In production, NEVER silently fall back to an ephemeral SQLite database
        if settings.ENVIRONMENT == "production":
            logger.critical("PRODUCTION ERROR: PostgreSQL database is required. Refusing silent fallback to SQLite.")
            raise RuntimeError(f"Production database connection failed: {err}") from err

        # Fall back to local SQLite only in development or test environments
        if db_engine.dialect.name == "postgresql" and target_engine is None:
            try:
                logger.info("Development environment: falling back to local SQLite database ('legal_ai.db')...")
                fallback_url = "sqlite:///legal_ai.db"
                engine = create_app_engine(fallback_url)
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                Base.metadata.create_all(bind=engine)
                logger.info("Local SQLite database initialized and tables ready.")
                return True
            except Exception as fb_err:
                logger.error(f"Fallback database initialization also failed: {fb_err}")
        return False


def check_db_connection(target_engine=None) -> dict:
    """Check connectivity to database. Returns connection status dict."""
    db_engine = target_engine or engine
    if not db_engine:
        return {"status": "error", "message": "Database engine not initialized"}
    
    try:
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return {
                "status": "connected",
                "dialect": db_engine.dialect.name,
                "database": getattr(db_engine.url, "database", "default")
            }
    except Exception as err:
        logger.warning(f"Database connection test failed: {err}")
        return {
            "status": "disconnected",
            "message": "Database instance unreachable. Local app running in standalone/offline mode."
        }


def get_db():
    """Dependency for obtaining database session in API routes."""
    if not SessionLocal:
        raise RuntimeError("Database session factory is uninitialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    print("==================================================")
    print("LEXIQ Database Schema & Migration Runner")
    print(f"Target Database Dialect: {'postgresql' if 'postgres' in settings.normalized_database_url else 'sqlite'}")
    print(f"Vector Dimension: {settings.embedding_dimension}")
    print("==================================================")
    success = init_db()
    if success:
        print("[SUCCESS] Database schema initialized and ready for production.")
        sys.exit(0)
    else:
        print("[ERROR] Database initialization failed.")
        sys.exit(1)
