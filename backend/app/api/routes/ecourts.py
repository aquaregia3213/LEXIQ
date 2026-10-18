import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

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
from backend.app.services.ecourts import ECourtsService, get_ecourts_service

logger = logging.getLogger("legal_ai.ecourts.api")
router = APIRouter(prefix="/ecourts", tags=["eCourts Intelligence"])


@router.post(
    "/lookup",
    response_model=ECourtsLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Lookup Indian eCourts case status / portal coordinates",
    description=(
        "Validates CNR number or case parameters and provides official portal coordinates for "
        "https://services.ecourts.gov.in/ecourtindia_v6/. Avoids CAPTCHA bypass or unauthorized scraping."
    ),
    responses={
        200: {"description": "Portal coordinates or verified case record."},
        400: {"description": "Invalid CNR format or empty search criteria."}
    }
)
def lookup_ecourts_case(
    request: ECourtsSearchRequest,
    service: ECourtsService = Depends(get_ecourts_service)
) -> ECourtsLookupResponse:
    try:
        return service.search_case(request)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.error(f"Error during eCourts lookup: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"eCourts lookup service error: {str(exc)}"
        )


@router.post(
    "/ingest",
    response_model=ECourtsCaseResult,
    status_code=status.HTTP_200_OK,
    summary="Ingest and normalize lawfully obtained court record / order text",
    description=(
        "Normalizes raw court status text or judgment obtained from the official eCourts portal "
        "into a structured, typed legal case record with hearing history and party details."
    ),
    responses={
        200: {"description": "Normalized court case record."},
        400: {"description": "Empty or invalid court record text."}
    }
)
def ingest_court_record(
    request: ECourtsIngestRequest,
    service: ECourtsService = Depends(get_ecourts_service)
) -> ECourtsCaseResult:
    if not request.raw_text or not request.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Raw court record text cannot be empty."
        )

    try:
        return service.parse_case_record(request)
    except Exception as exc:
        logger.error(f"Error ingesting court record: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Court record normalization failed: {str(exc)}"
        )


@router.post(
    "/analyze",
    response_model=ECourtsAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="AI procedural and legal risk analysis of eCourts record",
    description=(
        "Analyzes an eCourts case status or judgment using Gemini / Langflow. Strictly separates "
        "verified court facts from AI synthesized risk assessment, milestones, and next steps."
    ),
    responses={
        200: {"description": "Procedural risk analysis separating facts from AI summary."},
        400: {"description": "Missing case data or raw text."}
    }
)
def analyze_court_case(
    request: ECourtsAnalysisRequest,
    service: ECourtsService = Depends(get_ecourts_service)
) -> ECourtsAnalysisResponse:
    if not request.case_data and (not request.raw_text or not request.raw_text.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either case_data or raw_text must be provided for AI procedural analysis."
        )

    try:
        return service.analyze_case(request)
    except Exception as exc:
        logger.error(f"Error during AI court case analysis: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI court analysis error: {str(exc)}"
        )


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="eCourts integration operational status",
    description="Check current integration capability, active provider, and official portal URLs."
)
def get_integration_status() -> Dict[str, Any]:
    mode = (settings.ECOURTS_INTEGRATION_MODE or "portal_assisted").lower().strip()
    status_label = ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE
    if mode == "authorized_api":
        status_label = ECourtsIntegrationStatus.AUTHORIZED_API_CONFIGURED if settings.ECOURTS_API_URL else ECourtsIntegrationStatus.MANUAL_LOOKUP_REQUIRED
    elif mode == "mock":
        status_label = ECourtsIntegrationStatus.OFFICIAL_PORTAL_LINK_AVAILABLE

    return {
        "integration_mode": mode,
        "status_label": status_label.value,
        "official_portal_url": settings.ECOURTS_PORTAL_URL,
        "captcha_protection_active": True,
        "automated_scraping_permitted": False,
        "authorized_api_configured": bool(settings.ECOURTS_API_URL and settings.ECOURTS_CLIENT_ID),
        "notes": (
            "services.ecourts.gov.in requires visual CAPTCHA verification for public queries. "
            "Automated scraping is prohibited. Institutional REST APIs require MeitY API Setu / High Court approval."
        )
    }
