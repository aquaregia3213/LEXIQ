import pytest
from unittest.mock import MagicMock, patch

from backend.app.services.gemini_service import (
    GeminiLLMProvider,
    GeminiEmbeddingProvider,
    GeminiProviderError,
    sanitize_sensitive_details,
    LEGAL_DISCLAIMER_TEXT
)
from backend.app.services.llm import INSUFFICIENT_EVIDENCE_RESPONSE


def test_sanitize_sensitive_details():
    """Verify API keys and sensitive tokens are completely redacted."""
    raw = "Failed with key=AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6 and Bearer secret_token_xyz"
    sanitized = sanitize_sensitive_details(raw)
    assert "AIzaSy" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "secret_token_xyz" not in sanitized
    assert "Bearer [REDACTED]" in sanitized


def test_gemini_llm_missing_api_key_raises_error():
    """Verify GeminiLLMProvider raises GeminiProviderError when API key is missing."""
    provider = GeminiLLMProvider(api_key="", client=None)
    with pytest.raises(GeminiProviderError) as exc_info:
        provider.generate("Test prompt")
    assert "GEMINI_API_KEY" in str(exc_info.value)
    assert exc_info.value.status_code == 503


def test_gemini_embedding_missing_api_key_raises_error():
    """Verify GeminiEmbeddingProvider raises GeminiProviderError when API key is missing."""
    provider = GeminiEmbeddingProvider(api_key="", client=None)
    with pytest.raises(GeminiProviderError) as exc_info:
        provider.embed_text("Test snippet")
    assert "GEMINI_API_KEY" in str(exc_info.value)
    assert exc_info.value.status_code == 503


def test_gemini_llm_generate_with_mock_client():
    """Verify text generation using a mocked Gemini client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is a verified legal summary."
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiLLMProvider(api_key="mock_key", client=mock_client)
    res = provider.generate("Summarize the clause.")

    assert res == "This is a verified legal summary."
    mock_client.models.generate_content.assert_called_once()


def test_gemini_grounded_answer_empty_evidence():
    """Verify empty evidence immediately returns insufficient evidence response."""
    provider = GeminiLLMProvider(api_key="mock_key", client=MagicMock())
    result = provider.generate_grounded_answer(
        question="What is the notice period?",
        evidence_chunks=[]
    )
    assert result["has_sufficient_evidence"] is False
    assert result["answer"] == INSUFFICIENT_EVIDENCE_RESPONSE
    assert result["sources"] == []


def test_gemini_grounded_answer_with_mock_client():
    """Verify grounded QA preserves sources, page numbers, citations, and disclaimers."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        "According to the Master Services Agreement [Contract: MSA Acme, Section: Termination, Page: 4], "
        "either party may terminate for convenience upon thirty (30) days written notice."
    )
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiLLMProvider(api_key="mock_key", client=mock_client)

    sample_chunks = [
        {
            "chunk_id": "chunk-101",
            "contract_id": "c-1",
            "contract_name": "MSA Acme",
            "file_name": "msa_acme.pdf",
            "page_start": 4,
            "page_end": 4,
            "section": "Termination",
            "text": "Either party may terminate for convenience upon thirty (30) days written notice."
        }
    ]

    result = provider.generate_grounded_answer(
        question="What is the termination notice period?",
        evidence_chunks=sample_chunks
    )

    assert result["has_sufficient_evidence"] is True
    assert "thirty (30) days" in result["answer"]
    assert "DISCLAIMER:" in result["answer"]
    assert len(result["sources"]) == 1
    assert result["sources"][0]["page_start"] == 4
    assert result["sources"][0]["section"] == "Termination"
    assert result["sources"][0]["contract_name"] == "MSA Acme"


def test_gemini_grounded_answer_detected_insufficient_evidence():
    """Verify that when Gemini states evidence is insufficient, has_sufficient_evidence is False."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "The available documents do not provide sufficient evidence to answer this question."
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiLLMProvider(api_key="mock_key", client=mock_client)
    sample_chunks = [
        {
            "chunk_id": "chk-1",
            "contract_name": "Test Contract",
            "page_start": 1,
            "page_end": 1,
            "section": "General",
            "text": "Irrelevant boilerplate text."
        }
    ]

    result = provider.generate_grounded_answer(
        question="What is the penalty for late payment?",
        evidence_chunks=sample_chunks
    )

    assert result["has_sufficient_evidence"] is False
    assert result["sources"] == []


def test_gemini_empty_response_raises_error():
    """Verify GeminiProviderError is raised if Gemini returns an empty completion."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = ""
    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiLLMProvider(api_key="mock_key", client=mock_client)
    with pytest.raises(GeminiProviderError) as exc_info:
        provider.generate("Test prompt")
    assert "empty" in str(exc_info.value).lower()


def test_gemini_retry_on_transient_error():
    """Verify provider retries on transient errors (e.g. 429 / resource exhausted)."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Success after retry."

    # First call raises 429 error, second call succeeds
    mock_client.models.generate_content.side_effect = [
        Exception("ResourceExhausted: 429 Quota exceeded, retry later"),
        mock_response
    ]

    provider = GeminiLLMProvider(api_key="mock_key", client=mock_client)
    with patch("time.sleep", return_value=None):
        res = provider.generate("Test prompt")

    assert res == "Success after retry."
    assert mock_client.models.generate_content.call_count == 2


def test_gemini_embedding_provider_single_and_empty():
    """Verify GeminiEmbeddingProvider dimension, single text embedding, and empty handling."""
    mock_client = MagicMock()
    mock_emb = MagicMock()
    mock_emb.values = [0.123] * 768
    mock_res = MagicMock()
    mock_res.embeddings = [mock_emb]
    mock_client.models.embed_content.return_value = mock_res

    provider = GeminiEmbeddingProvider(api_key="mock_key", dim=768, client=mock_client)
    assert provider.dimension == 768

    # Empty text should return zeros without API call
    zero_vec = provider.embed_text("")
    assert len(zero_vec) == 768
    assert all(v == 0.0 for v in zero_vec)
    mock_client.models.embed_content.assert_not_called()

    # Substantive text should invoke API
    vec = provider.embed_text("Confidentiality agreement clause")
    assert len(vec) == 768
    assert vec[0] == 0.123
    mock_client.models.embed_content.assert_called_once()


def test_gemini_embedding_batch():
    """Verify GeminiEmbeddingProvider batch text embedding."""
    mock_client = MagicMock()
    mock_emb1 = MagicMock(values=[0.1] * 768)
    mock_emb2 = MagicMock(values=[0.2] * 768)
    mock_res = MagicMock(embeddings=[mock_emb1, mock_emb2])
    mock_client.models.embed_content.return_value = mock_res

    provider = GeminiEmbeddingProvider(api_key="mock_key", dim=768, client=mock_client)
    batch_vecs = provider.embed_batch(["text one", "text two"])

    assert len(batch_vecs) == 2
    assert len(batch_vecs[0]) == 768
    assert len(batch_vecs[1]) == 768
    assert batch_vecs[0][0] == 0.1
    assert batch_vecs[1][0] == 0.2


def test_gemini_error_sanitization_on_failure():
    """Verify that permanent errors redact API keys from exceptions."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception(
        "Invalid call for key=AIzaSyDUMMY1234567890ABCDEFGHIJKLM123: Model not found"
    )

    provider = GeminiLLMProvider(api_key="mock_key", client=mock_client)
    with pytest.raises(GeminiProviderError) as exc_info:
        provider.generate("Test prompt")

    err_str = str(exc_info.value)
    assert "AIzaSy" not in err_str
    assert "[REDACTED_API_KEY]" in err_str
