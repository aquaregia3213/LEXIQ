from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.schemas.ecourts import ECourtsSearchRequest
from backend.app.services.ecourts import get_ecourts_service


class ECourtsCaseLookupTool(BaseTool):
    """
    Tool for querying official Indian eCourts portal coordinates and case status.
    Respects portal CAPTCHA and boundaries; separates official court facts from assumptions.
    """
    name = "lookup_court_case"
    description = (
        "Retrieve case status or verified portal search coordinates from official Indian eCourts services "
        "(services.ecourts.gov.in) using a 16-character CNR number or case type, number, and year."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "cnr_number": {
                "type": "string",
                "description": "16-character Indian Court Case Record (CNR) number, e.g. MHAU010012342023."
            },
            "case_type": {
                "type": "string",
                "description": "Case type code, e.g. COMM.S., ARB.P., CS, WP."
            },
            "case_number": {
                "type": "string",
                "description": "Case registration number."
            },
            "year": {
                "type": "integer",
                "description": "Filing or registration year (e.g. 2023)."
            }
        }
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            cnr = kwargs.get("cnr_number")
            case_type = kwargs.get("case_type")
            case_number = kwargs.get("case_number")
            year = kwargs.get("year")

            search_req = ECourtsSearchRequest(
                cnr_number=cnr,
                case_type=case_type,
                case_number=case_number,
                year=year
            )

            ecourts_service = get_ecourts_service()
            lookup_res = ecourts_service.search_case(search_req)

            summary = (
                f"eCourts Lookup Status: {lookup_res.integration_status.value}. "
                f"{lookup_res.message} Official Portal URL: {lookup_res.portal_search_url}"
            )
            if lookup_res.case_data:
                summary += (
                    f" | Case: {lookup_res.case_data.case_type} {lookup_res.case_data.case_number}/{lookup_res.case_data.filing_year}"
                    f" | Status: {lookup_res.case_data.status} | Court: {lookup_res.case_data.court_name}"
                    f" | Next Date: {lookup_res.case_data.next_hearing_date or 'Not specified'}"
                )

            evidence = []
            if lookup_res.case_data:
                evidence.append({
                    "source_location": lookup_res.portal_search_url,
                    "court_name": lookup_res.case_data.court_name,
                    "cnr": lookup_res.case_data.cnr_number,
                    "status": lookup_res.case_data.status,
                    "stage": lookup_res.case_data.stage_of_case,
                    "snippet": f"Petitioner: {lookup_res.case_data.petitioner} vs. Respondent: {lookup_res.case_data.respondent}",
                    "retrieved_at": lookup_res.case_data.retrieved_at,
                })

            return ToolResult(
                success=lookup_res.success,
                data=lookup_res.model_dump(),
                evidence=evidence,
                summary_for_agent=summary,
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                data=None,
                error=str(exc),
                summary_for_agent=f"Failed to lookup court case: {str(exc)}"
            )
