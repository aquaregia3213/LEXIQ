from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
import re


class ECourtsIntegrationStatus(str, Enum):
    """Statuses denoting integration verification level for eCourts."""
    OFFICIAL_PORTAL_LINK_AVAILABLE = "Official portal link available"
    MANUAL_LOOKUP_REQUIRED = "Manual lookup required"
    AUTHORIZED_API_CONFIGURED = "Authorized API configured"
    AUTOMATED_LOOKUP_VERIFIED = "Automated lookup verified"


class HearingRecord(BaseModel):
    """Individual recorded hearing in court case history."""
    hearing_date: Optional[str] = None
    business_recorded: Optional[str] = None
    next_date: Optional[str] = None
    purpose: Optional[str] = None


class OrderRecord(BaseModel):
    """Specific interim order or final judgment entry."""
    order_date: Optional[str] = None
    order_number: Optional[str] = None
    judge_name: Optional[str] = None
    order_link: Optional[str] = None
    summary: Optional[str] = None


class ECourtsSearchRequest(BaseModel):
    """Search parameters for querying case status via portal deep link or provider."""
    cnr_number: Optional[str] = Field(None, description="16-character alphanumeric Case Number Record (CNR).")
    state: Optional[str] = Field(None, description="State code or name (e.g., 'Maharashtra', 'Delhi').")
    district: Optional[str] = Field(None, description="District court jurisdiction.")
    court_complex: Optional[str] = Field(None, description="Name or code of Court Complex.")
    case_type: Optional[str] = Field(None, description="Type of case (e.g., 'CS', 'ARB.P.', 'CRL.M.C.', 'WP').")
    case_number: Optional[str] = Field(None, description="Registration case number.")
    year: Optional[int] = Field(None, ge=1950, le=2100, description="Filing/registration year.")
    party_name: Optional[str] = Field(None, description="Petitioner or Respondent party name.")

    @field_validator("cnr_number")
    @classmethod
    def validate_cnr(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = re.sub(r"[^A-Za-z0-9]", "", v).upper()
        if len(cleaned) != 16:
            raise ValueError(
                f"Invalid CNR format: '{v}'. Official Indian eCourts CNR must be exactly 16 alphanumeric characters "
                "(e.g., MHAU010012342023)."
            )
        return cleaned


class ECourtsIngestRequest(BaseModel):
    """Payload for submitting lawfully obtained case-status response or judgment text."""
    raw_text: str = Field(..., min_length=10, description="Lawfully extracted or downloaded court status text.")
    source_url: Optional[str] = Field(
        "https://services.ecourts.gov.in/ecourtindia_v6/",
        description="Official source URL where record was retrieved."
    )
    cnr_number: Optional[str] = None
    case_title: Optional[str] = None
    document_type: Optional[str] = Field("case_status", description="Type: case_status, daily_order, final_judgment, cause_list")


class ECourtsCaseResult(BaseModel):
    """Normalized representation of an Indian Court Case Record."""
    cnr_number: Optional[str] = None
    case_type: Optional[str] = None
    case_number: Optional[str] = None
    filing_year: Optional[int] = None
    filing_date: Optional[str] = None
    registration_date: Optional[str] = None
    court_name: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: str = Field("PENDING", description="Case status (e.g., PENDING, DISPOSED, TRANSFERRED).")
    stage_of_case: Optional[str] = None
    next_hearing_date: Optional[str] = None
    purpose_of_hearing: Optional[str] = None
    petitioner: Optional[str] = None
    petitioner_advocate: Optional[str] = None
    respondent: Optional[str] = None
    respondent_advocate: Optional[str] = None
    history: List[HearingRecord] = Field(default_factory=list)
    orders: List[OrderRecord] = Field(default_factory=list)
    portal_search_url: str = Field("https://services.ecourts.gov.in/ecourtindia_v6/")
    source_url: str = Field("https://services.ecourts.gov.in/ecourtindia_v6/")
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    integration_status: ECourtsIntegrationStatus = ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE
    is_verified_automated: bool = False
    disclaimer: str = (
        "Case information is subject to official court verification. Official record hosted at services.ecourts.gov.in."
    )


class ECourtsLookupResponse(BaseModel):
    """API response for an eCourts lookup request."""
    success: bool
    integration_status: ECourtsIntegrationStatus
    portal_search_url: str
    message: str
    case_data: Optional[ECourtsCaseResult] = None
    suggested_actions: List[str] = Field(default_factory=list)


class ECourtsAnalysisRequest(BaseModel):
    """Payload for analyzing an eCourts case status or judgment with Gemini / Langflow."""
    case_data: Optional[ECourtsCaseResult] = None
    raw_text: Optional[str] = None
    question: Optional[str] = Field("Summarize the procedural posture, risks, and next hearing requirements.", description="Analysis objective.")


class ECourtsAnalysisResponse(BaseModel):
    """Evidence-grounded analysis of court proceedings separating facts from AI summary."""
    official_case_facts: Dict[str, Any] = Field(..., description="Unmodified court-recorded facts.")
    ai_summary: str = Field(..., description="Synthesized procedural and legal analysis.")
    legal_risk_level: str = Field("MEDIUM", description="Assessed legal risk: HIGH, MEDIUM, or LOW.")
    key_milestones: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    source_citation: str = Field(..., description="Exact official portal reference and citation.")
