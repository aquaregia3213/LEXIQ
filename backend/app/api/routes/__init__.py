from backend.app.api.routes.contracts import router as contracts_router
from backend.app.api.routes.search import router as search_router
from backend.app.api.routes.rag import router as rag_router
from backend.app.api.routes.clauses import router as clauses_router
from backend.app.api.routes.entities import router as entities_router
from backend.app.api.routes.obligations import router as obligations_router
from backend.app.api.routes.risks import router as risks_router
from backend.app.api.routes.graph import router as graph_router
from backend.app.api.routes.health import router as health_router

__all__ = [
    "contracts_router",
    "search_router",
    "rag_router",
    "clauses_router",
    "entities_router",
    "obligations_router",
    "risks_router",
    "graph_router",
    "health_router"
]
