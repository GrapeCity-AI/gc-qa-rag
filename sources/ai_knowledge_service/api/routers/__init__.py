"""
API Routers - Endpoint definitions for the management API.
"""

from ai_knowledge_service.api.routers.connectors import router as connectors_router
from ai_knowledge_service.api.routers.environments import router as environments_router
from ai_knowledge_service.api.routers.knowledge_bases import router as knowledge_bases_router
from ai_knowledge_service.api.routers.system import router as system_router
from ai_knowledge_service.api.routers.tasks import router as tasks_router
from ai_knowledge_service.api.routers.versions import router as versions_router

__all__ = [
    "system_router",
    "knowledge_bases_router",
    "versions_router",
    "tasks_router",
    "connectors_router",
    "environments_router",
]
