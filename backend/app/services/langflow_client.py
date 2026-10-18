import json
import logging
import re
from typing import Optional, Dict, Any, List
import httpx

from backend.app.config import settings
from backend.app.agents.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentFinding,
    AgentSourceCitation,
)

logger = logging.getLogger("legal_ai.langflow")


class LangflowError(Exception):
    """Base exception for all Langflow client errors."""
    pass


class LangflowConfigurationError(LangflowError):
    """Raised when Langflow is enabled but required configuration is missing."""
    pass


class LangflowUnavailableError(LangflowError):
    """Raised when the Langflow server cannot be reached (offline, connection error, DNS failure)."""
    pass


class LangflowTimeoutError(LangflowError):
    """Raised when a request to Langflow exceeds the configured timeout threshold."""
    pass


class LangflowResponseError(LangflowError):
    """Raised when Langflow returns an HTTP error code or malformed response payload."""
    pass


class LangflowClientService:
    """
    Client service for invoking Langflow-orchestrated agent flows.
    Communicates server-to-server with the Langflow API, passing user query,
    tenant-isolated context, and receiving grounded legal intelligence responses.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        flow_id: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        lexiq_internal_api_key: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.LANGFLOW_BASE_URL).rstrip("/")
        self.flow_id = (flow_id or settings.LANGFLOW_FLOW_ID).strip()
        self.api_key = (api_key or settings.LANGFLOW_API_KEY).strip()
        self.timeout_seconds = timeout_seconds or settings.LANGFLOW_TIMEOUT_SECONDS
        self.lexiq_internal_api_key = lexiq_internal_api_key or settings.LEXIQ_INTERNAL_API_KEY

    def is_configured(self) -> bool:
        """Check whether minimum required Langflow parameters are configured."""
        return bool(self.base_url and self.flow_id)

    def _build_headers(self) -> Dict[str, str]:
        """Construct secure HTTP headers for server-to-server calls to Langflow."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def _build_payload(self, request: AgentQueryRequest) -> Dict[str, Any]:
        """
        Build the Langflow execution payload with user query, contract constraints,
        and tenant parameters for backend tool authentication.
        """
        tweaks: Dict[str, Any] = {
            "LEXIQContext": {
                "contract_id": request.contract_id or "",
                "contract_ids": request.contract_ids or [],
                "user_id": request.user_id or "",
                "conversation_id": request.conversation_id or "",
                "internal_api_key": self.lexiq_internal_api_key,
            }
        }

        # Provide a structured legal query envelope
        prompt_envelope = (
            f"LEGAL QUERY: {request.question}\n"
            f"TARGET CONTRACT ID: {request.contract_id or 'None specified'}\n"
            f"PERMITTED CONTRACT IDS: {', '.join(request.contract_ids) if request.contract_ids else 'All authorized'}\n"
            "REQUIREMENTS: Synthesize an evidence-grounded answer citing exact sections/pages. "
            "Return structured analysis including findings, source citations, and confidence level."
        )

        return {
            "input_value": prompt_envelope,
            "input_type": "chat",
            "output_type": "chat",
            "tweaks": tweaks,
        }

    def run_flow(self, request: AgentQueryRequest) -> AgentQueryResponse:
        """
        Execute the legal analysis flow in Langflow and transform the output
        into a standardized LEXIQ AgentQueryResponse.
        """
        if not self.is_configured():
            raise LangflowConfigurationError(
                "Langflow client is not fully configured. Both LANGFLOW_BASE_URL and LANGFLOW_FLOW_ID must be set."
            )

        url = f"{self.base_url}/api/v1/run/{self.flow_id}"
        headers = self._build_headers()
        payload = self._build_payload(request)

        logger.info(
            f"Invoking Langflow flow [url={url}, flow_id={self.flow_id}, "
            f"contract_id={request.contract_id}, user_id={request.user_id}]"
        )

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            logger.error(f"Langflow request timed out after {self.timeout_seconds}s: {exc}")
            raise LangflowTimeoutError(f"Langflow flow execution timed out after {self.timeout_seconds} seconds.") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            logger.error(f"Failed to connect to Langflow at {self.base_url}: {exc}")
            raise LangflowUnavailableError(f"Unable to connect to Langflow at {self.base_url}. Service may be offline.") from exc
        except Exception as exc:
            logger.error(f"Unexpected error communicating with Langflow: {exc}")
            raise LangflowUnavailableError(f"Langflow connection error: {str(exc)}") from exc

        if response.status_code >= 400:
            logger.error(f"Langflow API error [status={response.status_code}]: {response.text}")
            raise LangflowResponseError(
                f"Langflow API returned error {response.status_code}: {response.text[:300]}"
            )

        try:
            raw_data = response.json()
        except Exception as exc:
            logger.error(f"Failed to decode Langflow JSON response: {exc}")
            raise LangflowResponseError("Langflow returned non-JSON response.") from exc

        return self.parse_langflow_response(raw_data, request)

    def parse_langflow_response(
        self,
        raw_data: Dict[str, Any],
        request: AgentQueryRequest
    ) -> AgentQueryResponse:
        """
        Extract text, findings, and citations from standard Langflow execution response.
        Langflow returns nested output structures under outputs[0].outputs[0].results.message.
        """
        extracted_text = ""
        extracted_tools_used: List[str] = []

        try:
            # Langflow 1.x response hierarchy
            outputs = raw_data.get("outputs", [])
            if outputs and isinstance(outputs, list):
                first_output = outputs[0]
                inner_outputs = first_output.get("outputs", [])
                if inner_outputs and isinstance(inner_outputs, list):
                    res = inner_outputs[0].get("results", {})
                    # Look for message text
                    if "message" in res:
                        msg = res["message"]
                        if isinstance(msg, dict):
                            extracted_text = msg.get("text") or msg.get("data", {}).get("text", "")
                        elif isinstance(msg, str):
                            extracted_text = msg
                    elif "text" in res:
                        extracted_text = res["text"]

            # Fallback direct checks
            if not extracted_text:
                if "result" in raw_data and isinstance(raw_data["result"], str):
                    extracted_text = raw_data["result"]
                elif "message" in raw_data and isinstance(raw_data["message"], str):
                    extracted_text = raw_data["message"]
                elif "text" in raw_data and isinstance(raw_data["text"], str):
                    extracted_text = raw_data["text"]

        except Exception as exc:
            logger.warning(f"Error parsing Langflow response hierarchy: {exc}")

        if not extracted_text:
            logger.warning(f"Could not locate text message in Langflow response: {raw_data}")
            extracted_text = str(raw_data)

        # Attempt to parse structured JSON from the model's output
        parsed_json = self._extract_json_object(extracted_text)
        if parsed_json and isinstance(parsed_json, dict) and "answer" in parsed_json:
            return self._build_response_from_dict(parsed_json, request)

        # Otherwise parse markdown/text response gracefully
        return self._build_response_from_text(extracted_text, request, extracted_tools_used)

    def _extract_json_object(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract a JSON object from text or markdown code fences."""
        cleaned = text.strip()
        # Check for ```json ... ``` fences
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        if cleaned.startswith("{") and cleaned.endswith("}"):
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

        return None

    def _build_response_from_dict(
        self,
        data: Dict[str, Any],
        request: AgentQueryRequest
    ) -> AgentQueryResponse:
        """Build validated AgentQueryResponse from structured dictionary."""
        answer = data.get("answer", "")
        summary = data.get("summary") or answer[:200]
        confidence = str(data.get("confidence", "MEDIUM")).upper()
        if confidence not in ("HIGH", "MEDIUM", "LOW"):
            confidence = "MEDIUM"

        findings: List[AgentFinding] = []
        for f in data.get("findings", []):
            if isinstance(f, dict) and "fact" in f:
                findings.append(
                    AgentFinding(
                        category=f.get("category", "clause"),
                        fact=f["fact"],
                        contract_id=f.get("contract_id") or request.contract_id,
                        contract_name=f.get("contract_name"),
                        page_number=f.get("page_number"),
                        source_reference=f.get("source_reference"),
                    )
                )

        sources: List[AgentSourceCitation] = []
        for s in data.get("sources", []):
            if isinstance(s, dict):
                sources.append(
                    AgentSourceCitation(
                        contract_id=s.get("contract_id") or request.contract_id,
                        contract_name=s.get("contract_name"),
                        document_id=s.get("document_id"),
                        chunk_id=s.get("chunk_id"),
                        page_number=s.get("page_number"),
                        section=s.get("section"),
                        source_location=s.get("source_location"),
                        snippet=s.get("snippet"),
                        relevance_score=s.get("relevance_score"),
                    )
                )

        tools_used = data.get("tools_used", ["langflow_orchestrator"])
        limitations = data.get("limitations", [])

        return AgentQueryResponse(
            answer=answer,
            summary=summary,
            findings=findings,
            sources=sources,
            tools_used=tools_used,
            confidence=confidence,
            limitations=limitations,
        )

    def _build_response_from_text(
        self,
        text: str,
        request: AgentQueryRequest,
        tools_used: List[str]
    ) -> AgentQueryResponse:
        """Parse unstructured or semi-structured text response into AgentQueryResponse."""
        first_paragraph = text.split("\n\n")[0].replace("\n", " ").strip()
        summary = first_paragraph[:250] if len(first_paragraph) > 250 else first_paragraph

        # Detect confidence level keywords
        confidence = "MEDIUM"
        if re.search(r"\b(high confidence|sufficient evidence|verified across)\b", text, re.IGNORECASE):
            confidence = "HIGH"
        elif re.search(r"\b(low confidence|insufficient evidence|unclear|missing|partial)\b", text, re.IGNORECASE):
            confidence = "LOW"

        # Extract citation references (e.g. Page 3, Section 5.1)
        sources: List[AgentSourceCitation] = []
        page_matches = re.finditer(r"(?:Page|pg\.?)\s*(\d+)", text, re.IGNORECASE)
        for m in page_matches:
            try:
                pg = int(m.group(1))
                sources.append(
                    AgentSourceCitation(
                        contract_id=request.contract_id,
                        page_number=pg,
                        source_location=f"Page {pg}",
                    )
                )
            except ValueError:
                pass

        return AgentQueryResponse(
            answer=text,
            summary=summary or "Legal agent analysis completed via Langflow orchestration layer.",
            findings=[],
            sources=sources[:5],
            tools_used=tools_used or ["langflow_orchestrator"],
            confidence=confidence,
            limitations=[
                "Generated via Langflow orchestration layer. Please review verified source citations in the contract."
            ],
        )


def get_langflow_client() -> LangflowClientService:
    """Dependency provider returning singleton/configured LangflowClientService."""
    return LangflowClientService()
