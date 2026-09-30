from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db, get_graph_service, GraphService
from backend.app.models.models import Contract
from backend.app.api.schemas.graph import GraphResponseV1

router = APIRouter(tags=["Knowledge Graph"])


@router.get(
    "/contracts/{contract_id}/graph",
    response_model=GraphResponseV1,
    status_code=status.HTTP_200_OK,
    summary="Get contract knowledge graph subgraph",
    description="Retrieve Knowledge Graph subgraph for a contract containing nodes and directed relationships formatted for UI graph visualizers.",
    responses={
        200: {"description": "Graph subgraph with nodes and relationships."},
        404: {"description": "Contract or graph data not found."}
    }
)
def get_contract_graph(
    contract_id: str,
    db: Session = Depends(get_db),
    graph_service: GraphService = Depends(get_graph_service)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id '{contract_id}' not found."
        )

    subgraph = graph_service.get_contract_graph(contract_id)
    if not subgraph.get("nodes"):
        # Auto-sync if not yet populated
        try:
            subgraph = graph_service.sync_contract_to_graph(db=db, contract_id=contract_id)
        except Exception:
            pass

    nodes = subgraph.get("nodes", [])
    edges = subgraph.get("edges", [])

    if not nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph data for contract '{contract_id}' not found. Please trigger sync first."
        )

    return GraphResponseV1(
        contract_id=contract_id,
        node_count=len(nodes),
        relationship_count=len(edges),
        nodes=nodes,
        relationships=edges,
        edges=edges
    )


@router.post(
    "/contracts/{contract_id}/sync-graph",
    response_model=GraphResponseV1,
    status_code=status.HTTP_200_OK,
    summary="Synchronize contract relational data to Knowledge Graph",
    description="Extract contract relational records (entities, clauses, obligations, risks) and sync into Knowledge Graph nodes and edges.",
    responses={
        200: {"description": "Synchronized Knowledge Graph subgraph."},
        404: {"description": "Contract not found."}
    }
)
def sync_contract_to_graph(
    contract_id: str,
    db: Session = Depends(get_db),
    graph_service: GraphService = Depends(get_graph_service)
):
    try:
        subgraph = graph_service.sync_contract_to_graph(db=db, contract_id=contract_id)
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])

        return GraphResponseV1(
            contract_id=contract_id,
            node_count=len(nodes),
            relationship_count=len(edges),
            nodes=nodes,
            relationships=edges,
            edges=edges
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )


@router.get(
    "/graph/contracts-by-company",
    status_code=status.HTTP_200_OK,
    summary="Find contracts involving a company",
    description="Multi-hop Knowledge Graph query: find contracts where a company is a signatory or contracting party.",
    responses={
        200: {"description": "List of matching contract nodes."},
        400: {"description": "Company name parameter cannot be empty."}
    }
)
def query_contracts_by_company(
    company_name: str = Query(..., description="Name or canonical name of company to query"),
    graph_service: GraphService = Depends(get_graph_service)
):
    if not company_name or not company_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name parameter cannot be empty."
        )
    return graph_service.query_contracts_by_company(company_name.strip())


@router.get(
    "/graph/contracts-by-jurisdiction",
    status_code=status.HTTP_200_OK,
    summary="Find contracts governed by a jurisdiction",
    description="Multi-hop Knowledge Graph query: find contracts governed by the laws or courts of a specified jurisdiction.",
    responses={
        200: {"description": "List of matching contract nodes."},
        400: {"description": "Jurisdiction parameter cannot be empty."}
    }
)
def query_contracts_by_jurisdiction(
    jurisdiction_name: str = Query(..., description="Name or state of governing jurisdiction to query"),
    graph_service: GraphService = Depends(get_graph_service)
):
    if not jurisdiction_name or not jurisdiction_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jurisdiction parameter cannot be empty."
        )
    return graph_service.query_contracts_by_jurisdiction(jurisdiction_name.strip())
