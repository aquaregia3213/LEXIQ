from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.graph import get_graph_service, GraphService

router = APIRouter(tags=["Knowledge Graph"])


@router.get("/api/contracts/{contract_id}/graph", status_code=status.HTTP_200_OK)
def get_contract_graph_endpoint(
    contract_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Retrieve Knowledge Graph subgraph (nodes and relationship edges) for a contract."""
    subgraph = graph_service.get_contract_graph(contract_id)
    if not subgraph.get("nodes"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph data for contract '{contract_id}' not found. Please trigger sync first."
        )
    return subgraph


@router.post("/api/contracts/{contract_id}/sync-graph", status_code=status.HTTP_200_OK)
def sync_contract_to_graph_endpoint(
    contract_id: str,
    db: Session = Depends(get_db),
    graph_service: GraphService = Depends(get_graph_service)
):
    """Sync contract relational entities, clauses, obligations, and risks into Knowledge Graph."""
    try:
        subgraph = graph_service.sync_contract_to_graph(db=db, contract_id=contract_id)
        return subgraph
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )


@router.get("/api/graph/contracts-by-company", status_code=status.HTTP_200_OK)
def query_contracts_by_company_endpoint(
    company_name: str = Query(..., description="Name of company to query"),
    graph_service: GraphService = Depends(get_graph_service)
):
    """Graph Query 1: Find contracts involving a company."""
    if not company_name or not company_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name parameter cannot be empty."
        )
    return graph_service.query_contracts_by_company(company_name)


@router.get("/api/graph/contracts-by-jurisdiction", status_code=status.HTTP_200_OK)
def query_contracts_by_jurisdiction_endpoint(
    jurisdiction_name: str = Query(..., description="Name of jurisdiction to query"),
    graph_service: GraphService = Depends(get_graph_service)
):
    """Graph Query 4: Find contracts governed by a jurisdiction."""
    if not jurisdiction_name or not jurisdiction_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jurisdiction parameter cannot be empty."
        )
    return graph_service.query_contracts_by_jurisdiction(jurisdiction_name)
