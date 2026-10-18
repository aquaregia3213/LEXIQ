"""
LEXIQ Legal Tool Caller - Langflow Custom Component
===================================================
Self-contained custom component for Langflow 1.x workspaces.
Calls the authenticated LEXIQ FastAPI tool execution endpoint over HTTP.
Zero local module imports required.
"""

import json
from typing import Optional, Dict, Any
import httpx

try:
    from langflow.custom import Component
    from langflow.io import StrInput, SecretStrInput, DropdownInput, Output
    from langflow.schema import Data
except ImportError:
    # Fallback mock classes for environments without Langflow package installed
    class Component:
        pass
    def StrInput(**kwargs): return kwargs
    def SecretStrInput(**kwargs): return kwargs
    def DropdownInput(**kwargs): return kwargs
    def Output(**kwargs): return kwargs
    class Data(dict):
        def __init__(self, data=None):
            super().__init__(data or {})


class LEXIQToolCaller(Component):
    display_name = "LEXIQ Legal Tool Caller"
    description = (
        "Calls authenticated LEXIQ backend legal analysis and retrieval tools over HTTP. "
        "Strictly enforces FastAPI authorization and multi-tenant contract isolation."
    )
    icon = "Scale"
    documentation = "https://github.com/aquaregia3213/LEXIQ"

    inputs = [
        StrInput(
            name="lexiq_api_url",
            display_name="LEXIQ API Base URL",
            value="http://localhost:8000",
            info="Base URL of the running LEXIQ FastAPI backend.",
            required=True
        ),
        SecretStrInput(
            name="internal_api_key",
            display_name="LEXIQ Internal API Key",
            value="lexiq_internal_secret_token",
            info="Must match settings.LEXIQ_INTERNAL_API_KEY on the backend.",
            required=True
        ),
        DropdownInput(
            name="tool_name",
            display_name="Tool to Execute",
            options=[
                "search_contract",
                "get_clauses",
                "get_obligations",
                "get_risks",
                "analyze_risk",
                "compare_contracts",
                "get_contract",
                "retrieve_source",
                "lookup_court_case"
            ],
            value="search_contract",
            info="The authorized legal tool to execute."
        ),
        StrInput(
            name="contract_id",
            display_name="Target Contract ID",
            info="UUID of the contract to inspect (optional if tool is cross-contract).",
        ),
        StrInput(
            name="query_or_args",
            display_name="Query or JSON Arguments",
            info="Text search query or a raw JSON string of arguments for the tool.",
            required=True
        ),
        StrInput(
            name="user_id",
            display_name="User UUID (Tenant Isolation)",
            info="Optional authenticated user UUID to ensure tenant data isolation.",
        ),
    ]

    outputs = [
        Output(name="summary_for_agent", display_name="Summary for Agent", method="execute_tool"),
        Output(name="evidence", display_name="Evidence Data", method="get_evidence_data"),
    ]

    def _prepare_payload(self) -> Dict[str, Any]:
        """Construct the tool execution payload."""
        tool_name = getattr(self, "tool_name", "search_contract")
        query_or_args = getattr(self, "query_or_args", "")
        contract_id = getattr(self, "contract_id", None) or None
        user_id = getattr(self, "user_id", None) or None

        # Build arguments dictionary
        arguments: Dict[str, Any] = {}
        if query_or_args:
            try:
                # If valid JSON, load as kwargs
                parsed = json.loads(query_or_args)
                if isinstance(parsed, dict):
                    arguments = parsed
                else:
                    arguments = {"query": str(query_or_args)}
            except (json.JSONDecodeError, ValueError):
                arguments = {"query": str(query_or_args)}

        if contract_id and "contract_id" not in arguments:
            arguments["contract_id"] = contract_id

        return {
            "tool_name": tool_name,
            "arguments": arguments,
            "contract_id": contract_id,
            "user_id": user_id,
        }

    def _call_backend_api(self) -> Dict[str, Any]:
        """Perform authenticated HTTP POST to LEXIQ FastAPI backend."""
        base_url = (getattr(self, "lexiq_api_url", "http://localhost:8000") or "http://localhost:8000").rstrip("/")
        api_key = getattr(self, "internal_api_key", "lexiq_internal_secret_token")
        endpoint = f"{base_url}/api/v1/agent/tools/execute"

        payload = self._prepare_payload()
        headers = {
            "Content-Type": "application/json",
            "x-lexiq-api-key": api_key,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def execute_tool(self) -> str:
        """Return the formatted summary string for agent reasoning."""
        try:
            result = self._call_backend_api()
            return result.get("summary_for_agent", "Tool executed successfully.")
        except Exception as exc:
            return f"Error executing tool: {str(exc)}"

    def get_evidence_data(self) -> Any:
        """Return evidence objects as Data for downstream Langflow nodes."""
        try:
            result = self._call_backend_api()
            return Data(data={"evidence": result.get("evidence", []), "raw": result.get("data")})
        except Exception as exc:
            return Data(data={"error": str(exc), "evidence": []})
