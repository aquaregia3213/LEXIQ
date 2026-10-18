import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "legal_ai_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/legal_ai_db"

    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # AI Provider Settings
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_EMBEDDING_DIMENSION: int = 768

    DEFAULT_EMBEDDING_DIMENSION: int = 1536
    GEMINI_TIMEOUT_SECONDS: float = 30.0
    GEMINI_MAX_RETRIES: int = 3

    # Legacy / Secondary Provider Settings
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: str = ""
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_API_KEY: str = ""

    # Agent Orchestration & Langflow Configuration
    # Options: 'native' (built-in ReAct orchestrator) or 'langflow' (Langflow orchestration layer)
    AGENT_ORCHESTRATOR: str = "native"
    LANGFLOW_BASE_URL: str = "http://localhost:7860"
    LANGFLOW_FLOW_ID: str = ""
    LANGFLOW_API_KEY: str = ""
    LANGFLOW_TIMEOUT_SECONDS: float = 30.0
    LANGFLOW_FALLBACK_TO_NATIVE: bool = True
    LEXIQ_INTERNAL_API_KEY: str = "lexiq_internal_secret_token"

    # eCourts Integration Configuration
    # Options: 'portal_assisted' (official portal link & lawful intake), 'mock' (test data), 'authorized_api' (institutional API Setu/NIC)
    ECOURTS_INTEGRATION_MODE: str = "portal_assisted"
    ECOURTS_PORTAL_URL: str = "https://services.ecourts.gov.in/ecourtindia_v6/"
    ECOURTS_API_URL: str = ""
    ECOURTS_CLIENT_ID: str = ""
    ECOURTS_CLIENT_SECRET: str = ""
    ECOURTS_TIMEOUT_SECONDS: float = 15.0

    # Storage & Upload Directory Configuration
    UPLOAD_DIR: str = "uploads/contracts"

    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"

    @property
    def normalized_database_url(self) -> str:
        """Return DATABASE_URL normalized for SQLAlchemy 2.0 (replaces legacy 'postgres://' with 'postgresql://')."""
        url = self.DATABASE_URL or ""
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    @property
    def active_ai_provider(self) -> str:
        """Return canonical active AI provider name ('gemini' or 'deterministic')."""
        provider = (self.AI_PROVIDER or self.LLM_PROVIDER or "gemini").lower().strip()
        return provider

    @property
    def embedding_dimension(self) -> int:
        """Return vector embedding dimension matching the active embedding provider."""
        provider = (self.AI_PROVIDER or self.EMBEDDING_PROVIDER or "gemini").lower().strip()
        if provider == "gemini":
            return self.GEMINI_EMBEDDING_DIMENSION
        return self.DEFAULT_EMBEDDING_DIMENSION

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins parsed as a list of strings without trailing slashes."""
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def mask_credential(self, val: str) -> str:
        """Safely mask a credential or secret string for logging (never printing raw secret)."""
        if not val:
            return "(not configured)"
        if len(val) <= 8:
            return "********"
        return f"{val[:4]}...{val[-4:]}"

    def get_sanitized_config_summary(self) -> dict:
        """Return non-sensitive configuration dictionary for startup verification and health checks."""
        return {
            "environment": self.ENVIRONMENT,
            "database_dialect": "postgresql" if "postgres" in self.normalized_database_url else "sqlite",
            "ai_provider": self.active_ai_provider,
            "gemini_api_key_configured": bool(self.GEMINI_API_KEY),
            "gemini_model": self.GEMINI_MODEL,
            "gemini_embedding_model": self.GEMINI_EMBEDDING_MODEL,
            "embedding_dimension": self.embedding_dimension,
            "agent_orchestrator": self.AGENT_ORCHESTRATOR,
            "langflow_configured": bool(self.LANGFLOW_BASE_URL and self.LANGFLOW_FLOW_ID),
            "upload_dir": self.UPLOAD_DIR,
            "cors_origins": self.cors_origins_list,
        }

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )



settings = Settings()
