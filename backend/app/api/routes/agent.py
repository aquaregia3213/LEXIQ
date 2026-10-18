import logging
import secrets
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.api.dependencies import get_db
from backend.app.agents.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
)
from backend.app.agents.orchestrator import AgentOrchestrator, get_agent_orchestrator
from backend.app.services.langflow_client import (
    LangflowClientService,
    get_langflow_client,
    LangflowUnavailableError,
    LangflowTimeoutError,
    LangflowResponseError,
    LangflowConfigurationError,
)
from backend.app.models.models import Contract

logger = logging.getLogger("legal_ai.agent")
router = APIRouter(prefix="/agent", tags=["Agentic AI"])


def verify_internal_api_key(
    x_lexiq_api_key: Optional[str] = Header(None, alias="x-lexiq-api-key"),
    authorization: Optional[str] = Header(None, alias="authorization"),
) -> None:
    """
    Authenticate server-to-server calls from external orchestrators (e.g. Langflow).
    Accepts either 'x-lexiq-api-key' header or 'Authorization: Bearer <key>'.
    """
    provided_key = None
    if x_lexiq_api_key:
        provided_key = x_lexiq_api_key
    elif authorization and authorization.lower().startswith("bearer "):
        provided_key = authorization[7:].strip()

    expected_key = settings.LEXIQ_INTERNAL_API_KEY
    if not provided_key or not expected_key or not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid internal API key for tool execution.",
        )


@router.post(
    "/query",
    response_model=AgentQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Agentic AI Contract Intelligence Assistant",
    description=(
        "Autonomous legal agent that analyzes intent, selects appropriate tools, gathers grounded evidence, "
        "and produces structured responses with verified source citations, findings, and disclaimers. "
        "Supports Langflow workflow orchestration with seamless native fallback."
    ),
    responses={
        200: {"description": "Agent analysis with answer, findings, sources, and confidence."},
        400: {"description": "Empty question or invalid parameters."},
        502: {"description": "External Langflow orchestrator unavailable."},
        504: {"description": "External Langflow orchestrator timed out."},
        500: {"description": "Internal agent execution error."}
    }
)
def query_agent(
    request: AgentQueryRequest,
    db: Session = Depends(get_db),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
    langflow_client: LangflowClientService = Depends(get_langflow_client),
):
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question parameter cannot be empty."
        )

    orchestration_layer = (settings.AGENT_ORCHESTRATOR or "native").lower().strip()

    # If configured for Langflow orchestration
    if orchestration_layer == "langflow":
        try:
            return langflow_client.run_flow(request=request)
        except (LangflowUnavailableError, LangflowTimeoutError, LangflowResponseError, LangflowConfigurationError) as exc:
            logger.warning(
                f"Langflow orchestration error: {exc}. "
                f"Fallback to native: {settings.LANGFLOW_FALLBACK_TO_NATIVE}"
            )
            if settings.LANGFLOW_FALLBACK_TO_NATIVE:
                logger.info("Failing over to native AgentOrchestrator for grounded contract execution.")
                return orchestrator.run(db=db, request=request)
            
            if isinstance(exc, LangflowTimeoutError):
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=f"Langflow agent orchestration timed out: {str(exc)}"
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Langflow agent orchestrator error: {str(exc)}"
            )

    # Default / Native Agent Orchestration
    try:
        response = orchestrator.run(db=db, request=request)
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(exc)}"
        )


@router.post(
    "/tools/execute",
    response_model=ToolExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute registered agent tool (Authenticated server-to-server)",
    description=(
        "Enables Langflow or external agent workflow engines to call approved legal retrieval and "
        "analysis tools while strictly preserving FastAPI authorization, database access controls, "
        "and multi-tenant boundaries."
    ),
    dependencies=[Depends(verify_internal_api_key)],
    responses={
        200: {"description": "Tool execution successful."},
        400: {"description": "Unknown tool or missing required arguments."},
        401: {"description": "Unauthorized internal API key."},
        403: {"description": "Forbidden: cross-tenant contract access violation."},
        404: {"description": "Referenced contract not found."},
        500: {"description": "Tool execution runtime error."}
    }
)
def execute_agent_tool(
    request: ToolExecutionRequest,
    db: Session = Depends(get_db),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator),
):
    # 1. Whitelist validation
    tool = orchestrator.tools.get(request.tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{request.tool_name}' is not authorized or does not exist."
        )

    # 2. Multi-tenant contract isolation check
    target_contract_id = request.contract_id or request.arguments.get("contract_id")
    if target_contract_id:
        contract = db.query(Contract).filter(Contract.id == target_contract_id).first()
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contract '{target_contract_id}' not found."
            )
        # Check tenant boundaries if user_id is provided
        if request.user_id and contract.uploaded_by:
            if contract.uploaded_by != request.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-tenant access prohibited: User does not own the requested contract."
                )

    # 3. Arguments schema validation
    try:
        tool.validate_args(request.arguments)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid arguments for tool '{request.tool_name}': {str(ve)}"
        )

    # 4. Tool Execution
    try:
        result = tool.execute(db=db, **request.arguments)
        return ToolExecutionResponse(
            success=result.success,
            tool_name=request.tool_name,
            data=result.data,
            evidence=result.evidence or [],
            summary_for_agent=result.summary_for_agent,
            error=result.error,
        )
    except Exception as exc:
        logger.error(f"Execution error in tool '{request.tool_name}': {exc}", exc_info=True)
        return ToolExecutionResponse(
            success=False,
            tool_name=request.tool_name,
            data=None,
            evidence=[],
            summary_for_agent=f"Execution error: {str(exc)}",
            error=str(exc),
        )


@router.get(
    "/tools",
    status_code=status.HTTP_200_OK,
    summary="List available agent tools",
    description="Retrieve the inventory of authorized legal analysis tools with their parameter schemas.",
    responses={
        200: {"description": "List of available agent tools and schemas."}
    }
)
def list_agent_tools(
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
) -> List[Dict[str, Any]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters_schema
        }
        for tool in orchestrator.tools.values()
    ]
