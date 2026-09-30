from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.agents.schemas import AgentQueryRequest, AgentQueryResponse
from backend.app.agents.orchestrator import AgentOrchestrator, get_agent_orchestrator

router = APIRouter(prefix="/agent", tags=["Agentic AI"])


@router.post(
    "/query",
    response_model=AgentQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Agentic AI Contract Intelligence Assistant",
    description=(
        "Autonomous legal agent that analyzes intent, selects appropriate tools, gathers grounded evidence, "
        "and produces structured responses with verified source citations, findings, and disclaimers."
    ),
    responses={
        200: {"description": "Agent analysis with answer, findings, sources, and confidence."},
        400: {"description": "Empty question or invalid parameters."},
        500: {"description": "Internal agent execution error."}
    }
)
def query_agent(
    request: AgentQueryRequest,
    db: Session = Depends(get_db),
    orchestrator: AgentOrchestrator = Depends(get_agent_orchestrator)
):
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question parameter cannot be empty."
        )

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
