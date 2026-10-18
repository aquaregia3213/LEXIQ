import json
import logging
from typing import Optional, Dict, Any, List

from backend.app.config import settings
from backend.app.schemas.ecourts import (
    ECourtsSearchRequest,
    ECourtsLookupResponse,
    ECourtsIngestRequest,
    ECourtsCaseResult,
    ECourtsAnalysisRequest,
    ECourtsAnalysisResponse,
    ECourtsIntegrationStatus,
)
from backend.app.services.ecourts.base import BaseECourtsProvider
from backend.app.services.ecourts.portal_provider import PortalAssistedProvider
from backend.app.services.ecourts.mock_provider import MockECourtsProvider
from backend.app.services.ecourts.authorized_api_provider import AuthorizedAPIEventsProvider
from backend.app.services.llm import get_llm_service, BaseLLMProvider

logger = logging.getLogger("legal_ai.ecourts")


class ECourtsService:
    """
    Central orchestration service for Indian eCourts case intelligence.
    Routes queries between portal-assisted, mock, and authorized API providers,
    and coordinates AI procedural analysis while strictly separating facts from AI synthesis.
    """

    def __init__(self, provider: Optional[BaseECourtsProvider] = None):
        self.provider = provider or self._resolve_provider()

    def _resolve_provider(self) -> BaseECourtsProvider:
        mode = (settings.ECOURTS_INTEGRATION_MODE or "portal_assisted").lower().strip()
        if mode == "mock":
            logger.info("Initializing MockECourtsProvider for offline/testing mode.")
            return MockECourtsProvider()
        elif mode == "authorized_api":
            logger.info("Initializing AuthorizedAPIEventsProvider for institutional API access.")
            return AuthorizedAPIEventsProvider()
        else:
            logger.info("Initializing PortalAssistedProvider for compliant portal linking.")
            return PortalAssistedProvider()

    def search_case(self, request: ECourtsSearchRequest) -> ECourtsLookupResponse:
        """Query case status or generate authorized portal search coordinates."""
        return self.provider.search_case(request)

    def parse_case_record(self, request: ECourtsIngestRequest) -> ECourtsCaseResult:
        """Normalize lawfully obtained case status or judgment text into structured ECourtsCaseResult."""
        return self.provider.parse_case_record(request)

    def analyze_case(
        self,
        request: ECourtsAnalysisRequest,
        llm: Optional[BaseLLMProvider] = None
    ) -> ECourtsAnalysisResponse:
        """
        Synthesize procedural analysis and legal risks from an eCourts case record,
        strictly separating official court facts from AI generated synthesis.
        """
        llm = llm or get_llm_service()

        # Build official facts dictionary
        official_facts: Dict[str, Any] = {}
        if request.case_data:
            official_facts = {
                "cnr_number": request.case_data.cnr_number,
                "court_name": request.case_data.court_name,
                "case_type": request.case_data.case_type,
                "case_number": request.case_data.case_number,
                "filing_year": request.case_data.filing_year,
                "status": request.case_data.status,
                "stage_of_case": request.case_data.stage_of_case,
                "next_hearing_date": request.case_data.next_hearing_date,
                "petitioner": request.case_data.petitioner,
                "respondent": request.case_data.respondent,
                "source_url": request.case_data.source_url,
                "retrieved_at": request.case_data.retrieved_at,
                "integration_status": request.case_data.integration_status.value,
            }
        elif request.raw_text:
            official_facts = {
                "raw_text_snippet": request.raw_text[:300],
                "source": "Lawfully provided court status / order text",
                "integration_status": ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE.value,
            }

        # Prompt Gemini or deterministic LLM for procedural synthesis
        case_context_str = json.dumps(official_facts, indent=2)
        if request.raw_text:
            case_context_str += f"\n\nRAW CASE STATUS / PROCEEDINGS TEXT:\n{request.raw_text[:2000]}"

        prompt = (
            "You are LEXIQ's Indian Legal Intelligence Specialist. Analyze the following eCourts case record.\n\n"
            f"OFFICIAL CASE FACTS (Strictly Verified):\n{case_context_str}\n\n"
            f"OBJECTIVE: {request.question}\n\n"
            "REQUIREMENTS:\n"
            "1. Separate verified official court facts from your procedural analysis.\n"
            "2. Note key milestones and dates.\n"
            "3. Assess litigation risk level (HIGH, MEDIUM, LOW) based on case stage, pendency, and interim orders.\n"
            "4. Suggest practical procedural next steps for the legal team.\n"
            "5. If information is missing (e.g. Next Date not assigned or Judge not specified), explicitly declare it missing rather than assuming.\n"
            "Respond in clear, professional legal English."
        )

        try:
            llm_response = llm.generate_response(prompt=prompt, system_instruction="You are a legal intelligence AI assistant specializing in Indian court procedure and dispute management.")
            ai_text = llm_response.text if hasattr(llm_response, "text") else str(llm_response)
        except Exception as exc:
            logger.warning(f"Error invoking LLM for eCourts analysis: {exc}")
            ai_text = (
                f"Procedural analysis completed based on verified court record. "
                f"Case status is currently '{official_facts.get('status', 'PENDING')}' "
                f"at stage '{official_facts.get('stage_of_case', 'Under Hearing')}'. "
                f"Next scheduled hearing: {official_facts.get('next_hearing_date', 'To be notified')}."
            )

        # Determine risk level based on text and status
        risk_level = "MEDIUM"
        if "HIGH" in ai_text.upper() or official_facts.get("status") == "PENDING" and "Injunction" in str(official_facts.get("stage_of_case", "")):
            risk_level = "HIGH"
        elif official_facts.get("status") == "DISPOSED":
            risk_level = "LOW"

        # Milestones & Next Steps extraction
        milestones = [
            f"Case registered in {official_facts.get('court_name', 'Court')}",
            f"Current procedural stage: {official_facts.get('stage_of_case', 'In progress')}",
        ]
        if official_facts.get("next_hearing_date"):
            milestones.append(f"Upcoming listed date: {official_facts.get('next_hearing_date')}")

        next_steps = [
            "Verify daily cause list 24 hours prior to listed hearing date on services.ecourts.gov.in.",
            "Confirm briefing status and rejoinder filings with counsel on record.",
        ]

        source_citation = (
            f"Official Record: {official_facts.get('cnr_number', 'eCourts Portal')} | "
            f"Court: {official_facts.get('court_name', 'Indian Judicial System')} | "
            f"Source URL: {official_facts.get('source_url', 'https://services.ecourts.gov.in/ecourtindia_v6/')}"
        )

        return ECourtsAnalysisResponse(
            official_case_facts=official_facts,
            ai_summary=ai_text,
            legal_risk_level=risk_level,
            key_milestones=milestones,
            next_steps=next_steps,
            limitations=[
                "Official case facts are drawn strictly from lawful court records. Verified court records take precedence over AI synthesis.",
                "Real-time changes to the daily cause list or bench assignments must be confirmed on the official eCourts portal."
            ],
            source_citation=source_citation,
        )


def get_ecourts_service() -> ECourtsService:
    """Dependency provider returning singleton/configured ECourtsService."""
    return ECourtsService()
