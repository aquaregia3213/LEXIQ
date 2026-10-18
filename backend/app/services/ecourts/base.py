from abc import ABC, abstractmethod
from typing import Optional
from backend.app.schemas.ecourts import (
    ECourtsSearchRequest,
    ECourtsLookupResponse,
    ECourtsIngestRequest,
    ECourtsCaseResult,
)


class BaseECourtsProvider(ABC):
    """Abstract base provider for Indian eCourts case intelligence."""

    @abstractmethod
    def search_case(self, request: ECourtsSearchRequest) -> ECourtsLookupResponse:
        """Query case status or generate authorized portal search coordinates."""
        pass

    @abstractmethod
    def parse_case_record(self, request: ECourtsIngestRequest) -> ECourtsCaseResult:
        """Parse lawfully obtained court status text or judgment into structured record."""
        pass

    @abstractmethod
    def build_portal_url(self, request: ECourtsSearchRequest) -> str:
        """Construct official search URL on services.ecourts.gov.in."""
        pass
