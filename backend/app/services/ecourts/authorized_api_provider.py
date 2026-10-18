import logging
import httpx
from typing import Optional
from datetime import datetime, timezone

from backend.app.config import settings
from backend.app.schemas.ecourts import (
    ECourtsSearchRequest,
    ECourtsLookupResponse,
    ECourtsIngestRequest,
    ECourtsCaseResult,
    ECourtsIntegrationStatus,
)
from backend.app.services.ecourts.base import BaseECourtsProvider

logger = logging.getLogger("legal_ai.ecourts.api")


class AuthorizedAPIEventsProvider(BaseECourtsProvider):
    """
    Enterprise adapter for official Government Open API / API Setu / NIC eCourts endpoints.
    Requires institutional authorization, client credentials, and High Court CPC approval.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.api_url = (api_url or settings.ECOURTS_API_URL).strip()
        self.client_id = (client_id or settings.ECOURTS_CLIENT_ID).strip()
        self.client_secret = (client_secret or settings.ECOURTS_CLIENT_SECRET).strip()
        self.timeout_seconds = timeout_seconds or settings.ECOURTS_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        """Check whether institutional credentials and API URL are provided."""
        return bool(self.api_url and self.client_id and self.client_secret)

    def build_portal_url(self, request: ECourtsSearchRequest) -> str:
        cnr = request.cnr_number or ""
        return f"{settings.ECOURTS_PORTAL_URL}?cino={cnr}"

    def search_case(self, request: ECourtsSearchRequest) -> ECourtsLookupResponse:
        """
        Execute automated query against authorized NIC / API Setu endpoint if credentials exist,
        otherwise clearly report that official approval/credentials are pending.
        """
        if not self.is_configured():
            logger.info("Authorized eCourts API credentials not configured; institutional grant required.")
            return ECourtsLookupResponse(
                success=False,
                integration_status=ECourtsIntegrationStatus.AUTHORIZED_API_CONFIGURED,
                portal_search_url=self.build_portal_url(request),
                message=(
                    "Official automated eCourts API integration requires institutional clearance "
                    "(eCommittee / High Court Central Project Coordinator approval) and API Setu credentials. "
                    "Automated retrieval is marked pending. Please use Portal-Assisted mode or input lawfully obtained case records."
                ),
                suggested_actions=[
                    "Contact the respective High Court Central Project Coordinator (CPC) for institutional API access.",
                    "Register for MeitY API Setu institutional litigant credentials.",
                    "In the interim, use the Official Portal link to complete case lookup with visual CAPTCHA.",
                ],
            )

        # Authorized API invocation
        headers = {
            "Content-Type": "application/json",
            "X-Client-Id": self.client_id,
            "Authorization": f"Bearer {self.client_secret}",
        }
        payload = {"cnr": request.cnr_number, "case_number": request.case_number, "year": request.year}

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.post(f"{self.api_url}/v1/case/status", json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    case_data = ECourtsCaseResult(
                        cnr_number=data.get("cnr"),
                        case_type=data.get("case_type"),
                        case_number=data.get("case_number"),
                        filing_year=data.get("year"),
                        court_name=data.get("court_name"),
                        status=data.get("status", "PENDING"),
                        petitioner=data.get("petitioner"),
                        respondent=data.get("respondent"),
                        portal_search_url=self.build_portal_url(request),
                        source_url=self.api_url,
                        retrieved_at=datetime.now(timezone.utc).isoformat(),
                        integration_status=ECourtsIntegrationStatus.AUTOMATED_LOOKUP_VERIFIED,
                        is_verified_automated=True,
                        disclaimer="Retrieved via authorized NIC / API Setu institutional interface."
                    )
                    return ECourtsLookupResponse(
                        success=True,
                        integration_status=ECourtsIntegrationStatus.AUTOMATED_LOOKUP_VERIFIED,
                        portal_search_url=self.build_portal_url(request),
                        message="Automated lookup verified via authorized institutional API.",
                        case_data=case_data,
                    )
                else:
                    return ECourtsLookupResponse(
                        success=False,
                        integration_status=ECourtsIntegrationStatus.AUTHORIZED_API_CONFIGURED,
                        portal_search_url=self.build_portal_url(request),
                        message=f"Authorized upstream API returned HTTP {resp.status_code}: {resp.text[:200]}",
                    )
        except Exception as exc:
            logger.error(f"Error querying authorized eCourts API: {exc}")
            return ECourtsLookupResponse(
                success=False,
                integration_status=ECourtsIntegrationStatus.AUTHORIZED_API_CONFIGURED,
                portal_search_url=self.build_portal_url(request),
                message=f"Failed to communicate with authorized eCourts API: {str(exc)}",
            )

    def parse_case_record(self, request: ECourtsIngestRequest) -> ECourtsCaseResult:
        # Fallback to standard parsing
        return ECourtsCaseResult(
            cnr_number=request.cnr_number,
            status="PENDING",
            portal_search_url=self.build_portal_url(ECourtsSearchRequest(cnr_number=request.cnr_number)),
            source_url=request.source_url or self.api_url,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            integration_status=ECourtsIntegrationStatus.AUTHORIZED_API_CONFIGURED,
            is_verified_automated=False,
            disclaimer="Parsed via authorized provider intake interface."
        )
