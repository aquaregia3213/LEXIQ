from fastapi import APIRouter

from backend.app.api.routes.contracts import router as contracts_router
from backend.app.api.routes.search import router as search_router
from backend.app.api.routes.rag import router as rag_router
from backend.app.api.routes.clauses import router as clauses_router
from backend.app.api.routes.entities import router as entities_router
from backend.app.api.routes.obligations import router as obligations_router
from backend.app.api.routes.risks import router as risks_router
from backend.app.api.routes.graph import router as graph_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.agent import router as agent_router

v1_router = APIRouter(prefix="/api/v1")

# Register all v1 modular sub-routers
v1_router.include_router(health_router)
v1_router.include_router(contracts_router)
v1_router.include_router(search_router)
v1_router.include_router(rag_router)
v1_router.include_router(clauses_router)
v1_router.include_router(entities_router)
v1_router.include_router(obligations_router)
v1_router.include_router(risks_router)
v1_router.include_router(graph_router)
v1_router.include_router(agent_router)
