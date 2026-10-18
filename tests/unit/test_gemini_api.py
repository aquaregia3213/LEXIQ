import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings


def test_health_reports_ai_provider_status():
    """Verify health endpoint accurately reports AI provider status."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "ai_provider" in data
    assert "provider" in data["ai_provider"]
    assert "llm_model" in data["ai_provider"]
    assert "embedding_dimension" in data["ai_provider"]


def test_rag_query_with_gemini_missing_api_key_returns_clear_error():
    """Verify that when AI_PROVIDER is gemini and GEMINI_API_KEY is empty, a clear error is returned without silent fallback."""
    client = TestClient(app)
    
    # Temporarily force AI_PROVIDER to gemini with empty key
    original_provider = settings.AI_PROVIDER
    original_key = settings.GEMINI_API_KEY
    try:
        settings.AI_PROVIDER = "gemini"
        settings.GEMINI_API_KEY = ""

        response = client.post(
            "/api/v1/rag/query",
            json={"question": "What is the liability cap limit in the agreement?"}
        )
        assert response.status_code in [502, 503]
        error_payload = response.json()
        assert "error" in error_payload or "detail" in error_payload
        err_msg = str(error_payload).lower()
        assert "gemini" in err_msg or "api key" in err_msg
    finally:
        settings.AI_PROVIDER = original_provider
        settings.GEMINI_API_KEY = original_key
