from typing import Dict, Optional, List
from datetime import datetime, timezone

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


class MockECourtsProvider(BaseECourtsProvider):
    """
    Deterministic Mock Provider for testing and local development.
    Supplies realistic Indian High Court and District Court case records without network calls.
    """

    MOCK_CASES: Dict[str, Dict] = {
        "MHAU010012342023": {
            "cnr_number": "MHAU010012342023",
            "case_type": "Commercial Suit (COMM.S.)",
            "case_number": "1234",
            "filing_year": 2023,
            "filing_date": "14/03/2023",
            "registration_date": "18/03/2023",
            "court_name": "Commercial Division, High Court of Judicature at Bombay",
            "jurisdiction": "Original Civil Jurisdiction",
            "status": "PENDING",
            "stage_of_case": "Arguments on Interim Injunction (Order 39 Rule 1 & 2 CPC)",
            "next_hearing_date": "12/11/2026",
            "purpose_of_hearing": "Hearing on Notice of Motion",
            "petitioner": "Apex Cloud Technologies Pvt. Ltd.",
            "petitioner_advocate": "Adv. Rajesh K. Sharma (Enrolment: MAH/1245/2008)",
            "respondent": "Bharat Infra Solutions Ltd. & Ors.",
            "respondent_advocate": "Adv. Meenakshi S. Sundaram",
            "history": [
                {
                    "hearing_date": "18/03/2023",
                    "business_recorded": "Admit. Notice issued to respondents returnable in 4 weeks.",
                    "next_date": "20/04/2023",
                    "purpose": "First Appearance"
                },
                {
                    "hearing_date": "20/04/2023",
                    "business_recorded": "Written Statement filed by Respondent 1. Adjourned for rejoinder.",
                    "next_date": "15/06/2023",
                    "purpose": "Pleadings Completion"
                },
                {
                    "hearing_date": "15/09/2024",
                    "business_recorded": "Part heard on Notice of Motion. Injunction continued till next date.",
                    "next_date": "12/11/2026",
                    "purpose": "Arguments"
                }
            ],
            "orders": [
                {
                    "order_date": "18/03/2023",
                    "order_number": "1",
                    "judge_name": "Hon'ble Justice V. K. Deshmukh",
                    "order_link": "https://services.ecourts.gov.in/ecourtindia_v6/order_view?cino=MHAU010012342023&order=1",
                    "summary": "Notice issued; status quo ordered regarding disputed intellectual property."
                }
            ]
        },
        "DLHC010056782022": {
            "cnr_number": "DLHC010056782022",
            "case_type": "Arbitration Petition (O.M.P. (COMM))",
            "case_number": "5678",
            "filing_year": 2022,
            "filing_date": "05/08/2022",
            "registration_date": "10/08/2022",
            "court_name": "High Court of Delhi at New Delhi",
            "jurisdiction": "Commercial Appellate Division",
            "status": "DISPOSED",
            "stage_of_case": "Judgment Pronounced",
            "next_hearing_date": None,
            "purpose_of_hearing": "Disposed",
            "petitioner": "Global Telecom Infrastructure Ltd.",
            "petitioner_advocate": "Adv. Siddharth Malhotra",
            "respondent": "National Highways Logistics Authority",
            "respondent_advocate": "Senior Standing Counsel",
            "history": [
                {
                    "hearing_date": "10/08/2022",
                    "business_recorded": "Petition under Section 34 of Arbitration Act admitted.",
                    "next_date": "14/11/2022",
                    "purpose": "Admission"
                },
                {
                    "hearing_date": "22/05/2023",
                    "business_recorded": "Arguments concluded. Judgment reserved.",
                    "next_date": "15/07/2023",
                    "purpose": "Judgment"
                }
            ],
            "orders": [
                {
                    "order_date": "15/07/2023",
                    "order_number": "Final",
                    "judge_name": "Hon'ble Justice Ananya Roy",
                    "order_link": "https://services.ecourts.gov.in/ecourtindia_v6/order_view?cino=DLHC010056782022&order=final",
                    "summary": "Arbitral award upheld with minor modification on post-award interest rates."
                }
            ]
        }
    }

    def build_portal_url(self, request: ECourtsSearchRequest) -> str:
        cnr = request.cnr_number or "MHAU010012342023"
        return f"https://services.ecourts.gov.in/ecourtindia_v6/?cino={cnr}"

    def search_case(self, request: ECourtsSearchRequest) -> ECourtsLookupResponse:
        cnr = (request.cnr_number or "").upper()
        raw_case = self.MOCK_CASES.get(cnr)

        if not raw_case and request.case_number:
            for case in self.MOCK_CASES.values():
                if case["case_number"] == request.case_number:
                    raw_case = case
                    break

        if not raw_case:
            # Default to first mock case for test robustness
            raw_case = self.MOCK_CASES["MHAU010012342023"]

        history_records = [HearingRecord(**h) for h in raw_case.get("history", [])]
        order_records = [OrderRecord(**o) for o in raw_case.get("orders", [])]

        case_result = ECourtsCaseResult(
            cnr_number=raw_case["cnr_number"],
            case_type=raw_case["case_type"],
            case_number=raw_case["case_number"],
            filing_year=raw_case["filing_year"],
            filing_date=raw_case["filing_date"],
            registration_date=raw_case["registration_date"],
            court_name=raw_case["court_name"],
            jurisdiction=raw_case.get("jurisdiction"),
            status=raw_case["status"],
            stage_of_case=raw_case.get("stage_of_case"),
            next_hearing_date=raw_case.get("next_hearing_date"),
            purpose_of_hearing=raw_case.get("purpose_of_hearing"),
            petitioner=raw_case.get("petitioner"),
            petitioner_advocate=raw_case.get("petitioner_advocate"),
            respondent=raw_case.get("respondent"),
            respondent_advocate=raw_case.get("respondent_advocate"),
            history=history_records,
            orders=order_records,
            portal_search_url=self.build_portal_url(request),
            source_url="https://services.ecourts.gov.in/ecourtindia_v6/",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            integration_status=ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE,
            is_verified_automated=False,
            disclaimer="Mock demonstration data replicating official Indian eCourts record schema."
        )

        return ECourtsLookupResponse(
            success=True,
            integration_status=ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE,
            portal_search_url=self.build_portal_url(request),
            message="Mock case record retrieved successfully (Test/Demonstration Mode).",
            case_data=case_result,
            suggested_actions=[
                "Review procedural history and next hearing dates.",
                "Execute AI procedural risk analysis.",
            ],
        )

    def parse_case_record(self, request: ECourtsIngestRequest) -> ECourtsCaseResult:
        # Re-use first mock case schema with injected raw text snippet
        base = self.MOCK_CASES["MHAU010012342023"]
        return ECourtsCaseResult(
            cnr_number=request.cnr_number or base["cnr_number"],
            case_type=base["case_type"],
            case_number=base["case_number"],
            filing_year=base["filing_year"],
            filing_date=base["filing_date"],
            court_name=base["court_name"],
            status=base["status"],
            petitioner=base["petitioner"],
            respondent=base["respondent"],
            history=[HearingRecord(**h) for h in base["history"]],
            orders=[OrderRecord(**o) for o in base["orders"]],
            portal_search_url="https://services.ecourts.gov.in/ecourtindia_v6/",
            source_url=request.source_url or "https://services.ecourts.gov.in/ecourtindia_v6/",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            integration_status=ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE,
            is_verified_automated=False,
            disclaimer="Normalized from ingested case response."
        )
