import json
from unittest.mock import patch, MagicMock
import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.config import settings
from backend.app.database import Base
from backend.app.api.dependencies import get_db
from backend.app.models.models import Contract, Document, Chunk, Clause, User
from backend.app.agents.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    ToolExecutionRequest,
)
from backend.app.services.langflow_client import (
    LangflowClientService,
    LangflowUnavailableError,
    LangflowTimeoutError,
    LangflowResponseError,
    LangflowConfigurationError,
)

# Test in-memory DB setup
@pytest.fixture
def langflow_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    # Create test users and contracts
    user_a = User(id="user-111", email="alice@firm.com")
    user_b = User(id="user-222", email="bob@firm.com")
    session.add_all([user_a, user_b])
    session.flush()

    contract_a = Contract(
        id="contract-aaa",
        name="Master Service Agreement - Alice",
        contract_type="MSA",
        status="COMPLETED",
        uploaded_by="user-111"
    )
    contract_b = Contract(
        id="contract-bbb",
        name="Vendor Agreement - Bob",
        contract_type="Vendor",
        status="COMPLETED",
        uploaded_by="user-222"
    )
    session.add_all([contract_a, contract_b])
    session.flush()

    doc_a = Document(
        contract_id=contract_a.id,
        file_name="msa_alice.pdf",
        file_type="PDF",
        processing_status="COMPLETED"
    )
    session.add(doc_a)
    session.flush()

    chunk_a = Chunk(
        contract_id=contract_a.id,
        document_id=doc_a.id,
        chunk_index=0,
        text="Section 14: Termination. Either party may terminate with 30 days notice.",
        page_start=1,
        page_end=1,
    )
    session.add(chunk_a)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_client(langflow_db):
    def override_get_db():
        try:
            yield langflow_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# =====================================================================
# Unit Tests for LangflowClientService
# =====================================================================

def test_langflow_client_unconfigured_raises():
    """Verify that calling run_flow without base_url or flow_id raises LangflowConfigurationError."""
    client = LangflowClientService(base_url="", flow_id="")
    req = AgentQueryRequest(question="What are the indemnification terms?")
    with pytest.raises(LangflowConfigurationError):
        client.run_flow(req)


def test_langflow_client_success_json_parsing():
    """Verify successful parsing of Langflow response with embedded JSON answer."""
    client = LangflowClientService(
        base_url="http://mock-langflow:7860",
        flow_id="mock-flow-uuid",
        api_key="mock-key"
    )

    mock_llm_json = {
        "answer": "The agreement permits termination upon 30 days written notice.",
        "summary": "Termination requires 30 days notice.",
        "findings": [{"category": "clause", "fact": "30 days notice required", "page_number": 4}],
        "sources": [{"section": "Section 14.1", "page_number": 4, "snippet": "Notice of 30 days"}],
        "confidence": "HIGH",
        "limitations": ["Applies only to convenience termination."]
    }

    mock_langflow_response = {
        "outputs": [
            {
                "outputs": [
                    {
                        "results": {
                            "message": {
                                "text": f"```json\n{json.dumps(mock_llm_json)}\n```"
                            }
                        }
                    }
                ]
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_langflow_response

    with patch("httpx.Client.post", return_value=mock_resp):
        req = AgentQueryRequest(question="Termination rules?", contract_id="contract-123")
        res = client.run_flow(req)

        assert isinstance(res, AgentQueryResponse)
        assert "30 days written notice" in res.answer
        assert res.confidence == "HIGH"
        assert len(res.findings) == 1
        assert res.findings[0].page_number == 4
        assert len(res.sources) == 1
        assert res.sources[0].section == "Section 14.1"


def test_langflow_client_success_markdown_parsing():
    """Verify fallback parsing when Langflow returns natural language text."""
    client = LangflowClientService(
        base_url="http://mock-langflow:7860",
        flow_id="mock-flow-uuid"
    )

    raw_text = (
        "Based on Section 9 and Page 5 of the contract, the limitation of liability is capped at $500,000. "
        "There is high confidence evidence supporting this conclusion."
    )
    mock_langflow_response = {
        "outputs": [
            {
                "outputs": [
                    {
                        "results": {
                            "message": {"text": raw_text}
                        }
                    }
                ]
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_langflow_response

    with patch("httpx.Client.post", return_value=mock_resp):
        req = AgentQueryRequest(question="What is the liability cap?")
        res = client.run_flow(req)

        assert isinstance(res, AgentQueryResponse)
        assert "$500,000" in res.answer
        assert res.confidence == "HIGH"
        assert any(src.page_number == 5 for src in res.sources)


def test_langflow_client_timeout():
    """Verify that httpx.TimeoutException maps to LangflowTimeoutError."""
    client = LangflowClientService(
        base_url="http://mock-langflow:7860",
        flow_id="mock-flow-uuid"
    )

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timed out")):
        req = AgentQueryRequest(question="Summary?")
        with pytest.raises(LangflowTimeoutError):
            client.run_flow(req)


def test_langflow_client_unavailable():
    """Verify that network/connection errors map to LangflowUnavailableError."""
    client = LangflowClientService(
        base_url="http://mock-langflow:7860",
        flow_id="mock-flow-uuid"
    )

    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")):
        req = AgentQueryRequest(question="Summary?")
        with pytest.raises(LangflowUnavailableError):
            client.run_flow(req)


def test_langflow_client_http_500():
    """Verify that HTTP 500 error from Langflow maps to LangflowResponseError."""
    client = LangflowClientService(
        base_url="http://mock-langflow:7860",
        flow_id="mock-flow-uuid"
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Flow Engine Error"

    with patch("httpx.Client.post", return_value=mock_resp):
        req = AgentQueryRequest(question="Summary?")
        with pytest.raises(LangflowResponseError):
            client.run_flow(req)


# =====================================================================
# Integration Tests for Tool Execution Endpoint
# =====================================================================

def test_tool_execute_unauthorized_missing_key(test_client):
    """Calling /api/v1/agent/tools/execute without credentials must return 401."""
    payload = {
        "tool_name": "search_contract",
        "arguments": {"query": "termination"}
    }
    response = test_client.post("/api/v1/agent/tools/execute", json=payload)
    assert response.status_code == 401
    assert "Unauthorized" in response.json()["detail"]


def test_tool_execute_unauthorized_invalid_key(test_client):
    """Calling /api/v1/agent/tools/execute with bad key must return 401."""
    payload = {
        "tool_name": "search_contract",
        "arguments": {"query": "termination"}
    }
    headers = {"x-lexiq-api-key": "wrong_invalid_secret_key"}
    response = test_client.post("/api/v1/agent/tools/execute", json=payload, headers=headers)
    assert response.status_code == 401


def test_tool_execute_authorized_success(test_client):
    """Calling with valid x-lexiq-api-key returns 200 and tool summary."""
    payload = {
        "tool_name": "get_contract",
        "arguments": {"contract_id": "contract-aaa"},
        "contract_id": "contract-aaa"
    }
    headers = {"x-lexiq-api-key": settings.LEXIQ_INTERNAL_API_KEY}
    response = test_client.post("/api/v1/agent/tools/execute", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tool_name"] == "get_contract"
    assert "Master Service Agreement - Alice" in data["summary_for_agent"]


def test_tool_execute_bearer_token_authorized(test_client):
    """Authorization: Bearer <key> must also be accepted."""
    payload = {
        "tool_name": "get_contract",
        "arguments": {"contract_id": "contract-aaa"},
    }
    headers = {"Authorization": f"Bearer {settings.LEXIQ_INTERNAL_API_KEY}"}
    response = test_client.post("/api/v1/agent/tools/execute", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_tool_execute_unknown_tool(test_client):
    """Executing an unauthorized or non-existent tool must return 400."""
    payload = {
        "tool_name": "unauthorized_arbitrary_shell_command",
        "arguments": {}
    }
    headers = {"x-lexiq-api-key": settings.LEXIQ_INTERNAL_API_KEY}
    response = test_client.post("/api/v1/agent/tools/execute", json=payload, headers=headers)
    assert response.status_code == 400
    assert "not authorized" in response.json()["detail"]


def test_tool_execute_missing_required_arguments(test_client):
    """Missing required tool arguments must fail schema validation with 400."""
    payload = {
        "tool_name": "search_contract",
        "arguments": {}  # search_contract requires 'query'
    }
    headers = {"x-lexiq-api-key": settings.LEXIQ_INTERNAL_API_KEY}
    response = test_client.post("/api/v1/agent/tools/execute", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Missing required parameter" in response.json()["detail"]


def test_tool_execute_tenant_isolation_forbidden(test_client):
    """User B trying to run a tool against User A's contract must return 403 Forbidden."""
    payload = {
        "tool_name": "get_contract",
        "contract_id": "contract-aaa",  # owned by user-111 (Alice)
        "user_id": "user-222",          # requesting user is Bob
        "arguments": {"contract_id": "contract-aaa"}
    }
    headers = {"x-lexiq-api-key": settings.LEXIQ_INTERNAL_API_KEY}
    response = test_client.post("/api/v1/agent/tools/execute", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Cross-tenant access prohibited" in response.json()["detail"]


def test_tool_execute_tenant_isolation_allowed(test_client):
    """User A accessing User A's contract succeeds."""
    payload = {
        "tool_name": "get_contract",
        "contract_id": "contract-aaa",
        "user_id": "user-111",
        "arguments": {"contract_id": "contract-aaa"}
    }
    headers = {"x-lexiq-api-key": settings.LEXIQ_INTERNAL_API_KEY}
    response = test_client.post("/api/v1/agent/tools/execute", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True


# =====================================================================
# End-to-end Orchestration Fallback & Routing Tests
# =====================================================================

def test_query_agent_langflow_success(test_client):
    """When AGENT_ORCHESTRATOR=langflow, route delegates to Langflow service."""
    mock_response = AgentQueryResponse(
        answer="Langflow synthesized response with verified citations.",
        summary="Synthesized via Langflow.",
        findings=[],
        sources=[],
        tools_used=["langflow_orchestrator", "search_contract"],
        confidence="HIGH",
        limitations=[]
    )

    with patch.object(settings, "AGENT_ORCHESTRATOR", "langflow"):
        with patch("backend.app.services.langflow_client.LangflowClientService.run_flow", return_value=mock_response):
            payload = {"question": "What is the warranty period?", "contract_id": "contract-aaa"}
            response = test_client.post("/api/v1/agent/query", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert "Langflow synthesized response" in data["answer"]
            assert "langflow_orchestrator" in data["tools_used"]


def test_query_agent_langflow_fallback_to_native(test_client):
    """When Langflow is unavailable and fallback is True, seamlessly fallback to native orchestrator."""
    with patch.object(settings, "AGENT_ORCHESTRATOR", "langflow"):
        with patch.object(settings, "LANGFLOW_FALLBACK_TO_NATIVE", True):
            with patch(
                "backend.app.services.langflow_client.LangflowClientService.run_flow",
                side_effect=LangflowUnavailableError("Connection refused")
            ):
                payload = {"question": "What are the termination terms?", "contract_id": "contract-aaa"}
                response = test_client.post("/api/v1/agent/query", json=payload)
                # Should not crash; falls back to native AgentOrchestrator
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert "confidence" in data


def test_query_agent_langflow_no_fallback_raises_502(test_client):
    """When Langflow is unavailable and fallback is False, raises HTTP 502 Bad Gateway."""
    with patch.object(settings, "AGENT_ORCHESTRATOR", "langflow"):
        with patch.object(settings, "LANGFLOW_FALLBACK_TO_NATIVE", False):
            with patch(
                "backend.app.services.langflow_client.LangflowClientService.run_flow",
                side_effect=LangflowUnavailableError("Langflow service offline")
            ):
                payload = {"question": "What are the termination terms?", "contract_id": "contract-aaa"}
                response = test_client.post("/api/v1/agent/query", json=payload)
                assert response.status_code == 502
                assert "Langflow agent orchestrator error" in response.json()["detail"]
