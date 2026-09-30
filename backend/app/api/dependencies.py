from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.search import get_search_service, SearchService
from backend.app.services.rag import get_rag_pipeline, RAGPipeline
from backend.app.services.clause_classifier import get_clause_classifier, ClauseClassifier
from backend.app.services.extractor import get_entity_extractor, EntityExtractor
from backend.app.services.obligation_extractor import get_obligation_extractor, ObligationExtractor
from backend.app.services.risk_analyzer import get_risk_analyzer, RiskAnalyzer
from backend.app.services.graph import get_graph_service, GraphService
from backend.app.agents.orchestrator import get_agent_orchestrator, AgentOrchestrator

__all__ = [
    "get_db",
    "get_search_service",
    "get_rag_pipeline",
    "get_clause_classifier",
    "get_entity_extractor",
    "get_obligation_extractor",
    "get_risk_analyzer",
    "get_graph_service",
    "get_agent_orchestrator",
    "SearchService",
    "RAGPipeline",
    "ClauseClassifier",
    "EntityExtractor",
    "ObligationExtractor",
    "RiskAnalyzer",
    "GraphService",
    "AgentOrchestrator"
]
