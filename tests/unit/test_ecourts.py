import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import app
from backend.app.config import settings
from backend.app.schemas.ecourts import (
    ECourtsSearchRequest,
    ECourtsIngestRequest,
    ECourtsCaseResult,
    ECourtsAnalysisRequest,
    ECourtsIntegrationStatus,
)
from backend.app.services.ecourts.portal_provider import PortalAssistedProvider
from backend.app.services.ecourts.mock_provider import MockECourtsProvider
from backend.app.services.ecourts.authorized_api_provider import AuthorizedAPIEventsProvider
from backend.app.services.ecourts.service import ECourtsService

client = TestClient(app)


# =====================================================================
# 1. Validation & Schema Tests
# =====================================================================

def test_cnr_validation_valid():
    """Valid 16-character CNR string is normalized and accepted."""
    req = ECourtsSearchRequest(cnr_number="mhau01-001234-2023")
    assert req.cnr_number == "MHAU010012342023"
    assert len(req.cnr_number) == 16


def test_cnr_validation_invalid_length():
    """CNR strings that are not 16 characters must fail validation."""
    with pytest.raises(ValidationError):
        ECourtsSearchRequest(cnr_number="SHORT123")


# =====================================================================
# 2. PortalAssistedProvider Tests
# =====================================================================

def test_portal_provider_generates_deep_link():
    """Portal provider creates official coordinates on services.ecourts.gov.in."""
    provider = PortalAssistedProvider()
    req = ECourtsSearchRequest(cnr_number="MHAU010012342023", case_type="COMM.S", case_number="123", year=2023)
    res = provider.search_case(req)

    assert res.success is True
    assert res.integration_status == ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE
    assert "https://services.ecourts.gov.in/ecourtindia_v6/" in res.portal_search_url
    assert "cino=MHAU010012342023" in res.portal_search_url
    assert "CAPTCHA" in res.message


def test_portal_provider_ingest_record_normalization():
    """Portal provider correctly parses lawful court text response into typed fields."""
    raw_court_text = """
    In the Court of Hon'ble Commercial Division, High Court of Bombay
    Case Type: Commercial Suit 456 of 2023
    CNR Number: MHAU010045672023
    Filing Date: 12/04/2023
    Registration Date: 15/04/2023
    Petitioner: TechCorp India Pvt. Ltd. Advocate: Adv. K. R. Rao
    Versus
    Respondent: Cloud Services Ltd. Advocate: Adv. P. V. Sen
    Status: PENDING
    Next Hearing Date: 25/11/2026
    Purpose of Hearing: Arguments on Notice of Motion
    
    Case History:
    15/04/2023 Summons issued to respondent 20/05/2023
    20/05/2023 Written statement filed 10/08/2023
    """
    provider = PortalAssistedProvider()
    ingest_req = ECourtsIngestRequest(raw_text=raw_court_text)
    record = provider.parse_case_record(ingest_req)

    assert record.cnr_number == "MHAU010045672023"
    assert record.status == "PENDING"
    assert record.filing_year == 2023
    assert record.filing_date == "12/04/2023"
    assert record.next_hearing_date == "25/11/2026"
    assert "TechCorp India" in record.petitioner
    assert "Cloud Services" in record.respondent
    assert len(record.history) >= 2


# =====================================================================
# 3. Mock Provider Tests
# =====================================================================

def test_mock_provider_returns_case():
    """Mock provider returns deterministic Indian court case details."""
    provider = MockECourtsProvider()
    req = ECourtsSearchRequest(cnr_number="MHAU010012342023")
    res = provider.search_case(req)

    assert res.success is True
    assert res.case_data is not None
    assert res.case_data.cnr_number == "MHAU010012342023"
    assert "High Court of Judicature at Bombay" in res.case_data.court_name
    assert res.case_data.status == "PENDING"
    assert len(res.case_data.history) == 3


# =====================================================================
# 4. Authorized API Provider Tests
# =====================================================================

def test_authorized_api_unconfigured_marks_pending():
    """Unconfigured enterprise API explicitly reports pending institutional approval."""
    provider = AuthorizedAPIEventsProvider(api_url="", client_id="")
    req = ECourtsSearchRequest(cnr_number="MHAU010012342023")
    res = provider.search_case(req)

    assert res.success is False
    assert res.integration_status == ECourtsIntegrationStatus.AUTHORIZED_API_CONFIGURED
    assert "institutional clearance" in res.message


# =====================================================================
# 5. Service & AI Procedural Analysis Tests
# =====================================================================

def test_ecourts_service_ai_analysis_separates_facts():
    """AI procedural analysis separates verified official facts from generated legal analysis."""
    service = ECourtsService(provider=MockECourtsProvider())
    mock_case_resp = service.search_case(ECourtsSearchRequest(cnr_number="MHAU010012342023"))
    case_data = mock_case_resp.case_data

    analysis_req = ECourtsAnalysisRequest(
        case_data=case_data,
        question="What is the current posture and when is the next hearing?"
    )

    analysis_resp = service.analyze_case(analysis_req)

    # Official facts must be isolated and unmodified
    assert analysis_resp.official_case_facts["cnr_number"] == "MHAU010012342023"
    assert analysis_resp.official_case_facts["status"] == "PENDING"
    assert "Bombay" in analysis_resp.official_case_facts["court_name"]

    # AI procedural summary must be present
    assert len(analysis_resp.ai_summary) > 20
    assert analysis_resp.legal_risk_level in ("HIGH", "MEDIUM", "LOW")
    assert len(analysis_resp.key_milestones) >= 2
    assert len(analysis_resp.next_steps) >= 1
    assert "services.ecourts.gov.in" in analysis_resp.source_citation


# =====================================================================
# 6. REST API Endpoints Tests
# =====================================================================

def test_api_lookup_endpoint_valid():
    """POST /api/v1/ecourts/lookup returns 200 and portal coordinates."""
    payload = {"cnr_number": "MHAU010012342023"}
    resp = client.post("/api/v1/ecourts/lookup", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "https://services.ecourts.gov.in" in data["portal_search_url"]


def test_api_lookup_endpoint_invalid_cnr():
    """POST /api/v1/ecourts/lookup with malformed CNR returns validation error (400/422)."""
    payload = {"cnr_number": "INVALID_CNR"}
    resp = client.post("/api/v1/ecourts/lookup", json=payload)
    assert resp.status_code in (400, 422)
    assert "Invalid CNR format" in resp.text


def test_api_ingest_endpoint_valid():
    """POST /api/v1/ecourts/ingest normalizes raw text and returns typed result."""
    payload = {
        "raw_text": "In the High Court of Delhi Case No: WP 1234 of 2024 Status: PENDING Next Hearing Date: 18/12/2026",
        "source_url": "https://services.ecourts.gov.in/ecourtindia_v6/"
    }
    resp = client.post("/api/v1/ecourts/ingest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["next_hearing_date"] == "18/12/2026"


def test_api_analyze_endpoint_valid():
    """POST /api/v1/ecourts/analyze performs procedural analysis."""
    payload = {
        "raw_text": "High Court of Bombay Commercial Suit 500/2023 Status: PENDING Injunction Granted Next Date: 10/11/2026",
        "question": "What is the injunction status?"
    }
    resp = client.post("/api/v1/ecourts/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "official_case_facts" in data
    assert "ai_summary" in data
    assert data["legal_risk_level"] in ("HIGH", "MEDIUM", "LOW")


def test_api_status_endpoint():
    """GET /api/v1/ecourts/status reports operational flags and CAPTCHA status."""
    resp = client.get("/api/v1/ecourts/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["captcha_protection_active"] is True
    assert data["automated_scraping_permitted"] is False
    assert "official_portal_url" in data


# =====================================================================
# 7. Agent / Langflow Tool Execution Test
# =====================================================================

def test_agent_tool_lookup_court_case():
    """lookup_court_case tool can be executed via authenticated /tools/execute."""
    payload = {
        "tool_name": "lookup_court_case",
        "arguments": {
            "cnr_number": "MHAU010012342023"
        }
    }
    headers = {"x-lexiq-api-key": settings.LEXIQ_INTERNAL_API_KEY}
    resp = client.post("/api/v1/agent/tools/execute", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["tool_name"] == "lookup_court_case"
    assert "services.ecourts.gov.in" in data["summary_for_agent"]
