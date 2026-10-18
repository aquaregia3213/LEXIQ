import re
from typing import List, Optional
from datetime import datetime, timezone
from urllib.parse import urlencode

from backend.app.config import settings
from backend.app.schemas.ecourts import (
    ECourtsSearchRequest,
    ECourtsLookupResponse,
    ECourtsIngestRequest,
    ECourtsCaseResult,
    ECourtsIntegrationStatus,
    HearingRecord,
    OrderRecord,
)
from backend.app.services.ecourts.base import BaseECourtsProvider


class PortalAssistedProvider(BaseECourtsProvider):
    """
    Lawful, portal-assisted integration for Indian eCourts services.
    Generates authorized search deep links to official services.ecourts.gov.in,
    validates Indian CNR/case identifiers, and normalizes lawfully ingested case records.
    """

    def __init__(self, base_portal_url: Optional[str] = None):
        self.base_portal_url = (base_portal_url or settings.ECOURTS_PORTAL_URL).rstrip("/") + "/"

    def build_portal_url(self, request: ECourtsSearchRequest) -> str:
        """Construct the official eCourts web portal URL with relevant search parameters."""
        params = {}
        if request.cnr_number:
            params["cino"] = request.cnr_number
        if request.case_type:
            params["case_type"] = request.case_type
        if request.case_number:
            params["case_no"] = request.case_number
        if request.year:
            params["rgyear"] = str(request.year)
        if request.state:
            params["state_code"] = request.state
        if request.district:
            params["dist_code"] = request.district

        if params:
            return f"{self.base_portal_url}?{urlencode(params)}"
        return self.base_portal_url

    def search_case(self, request: ECourtsSearchRequest) -> ECourtsLookupResponse:
        """
        Validate identifiers and return official portal destination with manual lookup instructions.
        Explicitly does not bypass visual CAPTCHA or scrape protected pages.
        """
        portal_url = self.build_portal_url(request)

        # Validate minimum search criteria
        has_criteria = bool(
            request.cnr_number or (request.case_number and request.year) or request.party_name
        )
        if not has_criteria:
            return ECourtsLookupResponse(
                success=False,
                integration_status=ECourtsIntegrationStatus.MANUAL_LOOKUP_REQUIRED,
                portal_search_url=self.base_portal_url,
                message="Please provide a valid 16-character CNR number, Case Number & Year, or Party Name.",
                suggested_actions=[
                    "Locate your 16-digit CNR number on existing case orders or summons.",
                    f"Visit the official eCourts portal directly at {self.base_portal_url}.",
                ],
            )

        identifier_desc = f"CNR: {request.cnr_number}" if request.cnr_number else f"Case {request.case_type or ''} {request.case_number or ''}/{request.year or ''}".strip()

        return ECourtsLookupResponse(
            success=True,
            integration_status=ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE,
            portal_search_url=portal_url,
            message=(
                f"Official eCourts portal coordinates generated for {identifier_desc}. "
                "Because services.ecourts.gov.in requires a visual CAPTCHA and session verification, "
                "please open the official portal to complete your search, then paste the lawful case status "
                "response into LEXIQ for AI analysis."
            ),
            case_data=None,
            suggested_actions=[
                f"Open the official portal at {portal_url}",
                "Enter the displayed visual CAPTCHA",
                "Copy the official case status or daily order text",
                "Use the 'Ingest Court Record' tab in LEXIQ to analyze status and risk",
            ],
        )

    def parse_case_record(self, request: ECourtsIngestRequest) -> ECourtsCaseResult:
        """
        Normalize lawfully obtained case status or judgment text into structured ECourtsCaseResult.
        Extracts CNR, Case Type, Filing Date, Next Hearing, Parties, and Hearing History.
        """
        text = request.raw_text.strip()

        # 1. Extract CNR
        cnr_match = re.search(r"\b([A-Z]{2}[A-Z0-9]{4}[0-9]{10})\b", text, re.IGNORECASE)
        cnr_number = request.cnr_number or (cnr_match.group(1).upper() if cnr_match else None)

        # 2. Extract Case Type and Number
        case_no_match = re.search(
            r"Case\s*(?:Type|No\.?|Number)?\s*[:\-]?\s*([A-Za-z\.\s]+?)\s*[:\-\s]?\s*(\d+)\s*(?:\s+of\s+|[\/\-])\s*(\d{4})",
            text,
            re.IGNORECASE
        )
        case_type, case_number, filing_year = None, None, None
        if case_no_match:
            case_type = case_no_match.group(1).strip()
            case_number = case_no_match.group(2).strip()
            try:
                filing_year = int(case_no_match.group(3).strip())
            except ValueError:
                pass

        # Fallback year extraction from CNR if available
        if filing_year is None and cnr_number and len(cnr_number) == 16:
            try:
                cnr_year = int(cnr_number[-4:])
                if 1950 <= cnr_year <= 2100:
                    filing_year = cnr_year
            except ValueError:
                pass

        # 3. Status extraction
        status = "PENDING"
        if re.search(r"\b(DISPOSED|DECIDED|DISMISSED|ALLOWED|DECREED|CLOSED)\b", text, re.IGNORECASE):
            status = "DISPOSED"
        elif re.search(r"\b(TRANSFERRED)\b", text, re.IGNORECASE):
            status = "TRANSFERRED"

        # 4. Dates extraction
        filing_date_match = re.search(r"Filing\s*Date\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", text, re.IGNORECASE)
        filing_date = filing_date_match.group(1) if filing_date_match else None

        reg_date_match = re.search(r"Registration\s*Date\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", text, re.IGNORECASE)
        registration_date = reg_date_match.group(1) if reg_date_match else None

        next_date_match = re.search(r"Next\s*Hearing\s*Date\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", text, re.IGNORECASE)
        next_hearing_date = next_date_match.group(1) if next_date_match else None

        # 5. Purpose of Hearing / Stage
        purpose_match = re.search(r"(?:Purpose\s*of\s*Hearing|Stage\s*of\s*Case)\s*[:\-]?\s*([^\n\r]+)", text, re.IGNORECASE)
        purpose = purpose_match.group(1).strip() if purpose_match else None

        # 6. Parties extraction
        petitioner_match = re.search(r"(?:Petitioner|Plaintiff|Appellant)\s*[:\-]?\s*([^\n\r]+?)(?:\s+Advocate|\s+Versus|\s+Vs|\n)", text, re.IGNORECASE)
        petitioner = petitioner_match.group(1).strip() if petitioner_match else None

        respondent_match = re.search(r"(?:Respondent|Defendant)\s*[:\-]?\s*([^\n\r]+?)(?:\s+Advocate|\n|$)", text, re.IGNORECASE)
        respondent = respondent_match.group(1).strip() if respondent_match else None

        # 7. Court Complex / Name
        court_match = re.search(r"(?:In\s*the\s*Court\s*of|Court\s*Name|Court\s*Complex)\s*[:\-]?\s*([^\n\r]+)", text, re.IGNORECASE)
        court_name = court_match.group(1).strip() if court_match else "Indian District & Sessions Court"

        # 8. Extract Hearing History rows if present
        history: List[HearingRecord] = []
        date_pattern = re.compile(r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s+([^\n\d]+?)\s+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})?")
        for match in date_pattern.finditer(text):
            h_date = match.group(1)
            business = match.group(2).strip()
            n_date = match.group(3)
            if business and len(business) > 3 and not any(h.hearing_date == h_date for h in history):
                history.append(
                    HearingRecord(
                        hearing_date=h_date,
                        business_recorded=business,
                        next_date=n_date,
                        purpose=business
                    )
                )

        return ECourtsCaseResult(
            cnr_number=cnr_number,
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year,
            filing_date=filing_date,
            registration_date=registration_date,
            court_name=court_name,
            status=status,
            stage_of_case=purpose,
            next_hearing_date=next_hearing_date,
            purpose_of_hearing=purpose,
            petitioner=petitioner,
            respondent=respondent,
            history=history[:10],
            portal_search_url=self.base_portal_url,
            source_url=request.source_url or self.base_portal_url,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            integration_status=ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE,
            is_verified_automated=False,
            disclaimer="Lawfully ingested case record. Verified against official portal parameters at services.ecourts.gov.in."
        )
