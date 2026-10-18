import os
import pytest
from dotenv import load_dotenv

load_dotenv()
from backend.app.config import settings
from backend.app.services.gemini_service import GeminiLLMProvider, GeminiEmbeddingProvider

GEMINI_API_KEY = (os.environ.get("GEMINI_API_KEY") or settings.GEMINI_API_KEY or "").strip()



@pytest.mark.skipif(
    not GEMINI_API_KEY,
    reason="Live Gemini smoke tests require GEMINI_API_KEY to be set in environment."
)
class TestGeminiLiveSmoke:
    """
    Live integration smoke tests for Google Gemini.
    Only run when a valid GEMINI_API_KEY is available in the environment.
    Run via: GEMINI_API_KEY=your_key python -m pytest tests/smoke/test_gemini_smoke.py
    """

    def test_live_gemini_llm_generation(self):
        """Smoke test verifying live model connection to Google Gemini."""
        provider = GeminiLLMProvider(api_key=GEMINI_API_KEY)
        response = provider.generate("In 10 words or less, what is a legal contract?")
        assert response
        assert len(response) > 5

    def test_live_gemini_grounded_qa(self):
        """Smoke test verifying live grounded question answering with citations."""
        provider = GeminiLLMProvider(api_key=GEMINI_API_KEY)
        evidence = [
            {
                "chunk_id": "live-chk-1",
                "contract_id": "test-c1",
                "contract_name": "Sample SaaS Agreement",
                "section": "Confidentiality",
                "page_start": 2,
                "page_end": 2,
                "text": "The confidentiality obligations set forth herein shall survive for a period of three (3) years."
            }
        ]
        result = provider.generate_grounded_answer(
            question="How long does confidentiality survive?",
            evidence_chunks=evidence
        )
        assert result["has_sufficient_evidence"] is True
        assert "three" in result["answer"].lower() or "3" in result["answer"]
        assert len(result["sources"]) == 1
        assert "DISCLAIMER:" in result["answer"]

    def test_live_gemini_embeddings(self):
        """Smoke test verifying live Gemini text-embedding-004 output."""
        provider = GeminiEmbeddingProvider(api_key=GEMINI_API_KEY)
        assert provider.dimension == 768
        vec = provider.embed_text("Intellectual property rights clause")
        assert len(vec) == 768
        assert any(v != 0.0 for v in vec)
