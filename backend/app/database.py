import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Base class for ORM models
Base = declarative_base()

# Configure SQLAlchemy engine (lazy setup with fallback)
def create_app_engine(database_url: str = None):
    url = database_url or settings.DATABASE_URL
    try:
        if url.startswith("postgresql"):
            return create_engine(
                url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3}
            )
        else:
            return create_engine(
                url,
                connect_args={"check_same_thread": False} if "sqlite" in url else {}
            )
    except Exception as e:
        logger.warning(f"Failed to initialize database engine for {url}: {e}")
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
        
        # If PostgreSQL, enable pgvector extension
        if db_engine.dialect.name == "postgresql":
            with db_engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                logger.info("Successfully enabled pgvector extension in PostgreSQL.")
        
        Base.metadata.create_all(bind=db_engine)
        logger.info("All database tables created successfully.")
        return True
    except Exception as err:
        logger.warning(f"Primary database connection failed: {err}")
        # Fall back to local SQLite if PostgreSQL is unreachable in local environment
        if db_engine.dialect.name == "postgresql" and target_engine is None:
            try:
                logger.info("Falling back to local SQLite database ('legal_ai.db')...")
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
