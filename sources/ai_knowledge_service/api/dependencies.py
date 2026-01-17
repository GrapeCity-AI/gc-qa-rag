"""
Dependencies - FastAPI dependency injection bridge.

This module bridges FastAPI's Depends mechanism with the existing SimpleContainer DI.
"""

from contextlib import asynccontextmanager
from typing import Annotated, Any, Callable, Type, TypeVar

from fastapi import Depends, Request

from ai_knowledge_service.abstractions.infrastructure.container import (
    IServiceContainer,
    IServiceScope,
    Lifetime,
)
from ai_knowledge_service.abstractions.infrastructure.event_bus import IEventBus
from ai_knowledge_service.abstractions.execution.queue import ITaskQueue
from ai_knowledge_service.abstractions.infrastructure.version_manager import IVersionManager
from ai_knowledge_service.implementations.infrastructure.simple_container import SimpleContainer
from ai_knowledge_service.implementations.infrastructure.memory_event_bus import MemoryEventBus
from ai_knowledge_service.implementations.infrastructure.memory_queue import MemoryTaskQueue


T = TypeVar("T")


# Global container instance
_container: SimpleContainer | None = None


def get_container() -> SimpleContainer:
    """Get the global DI container."""
    global _container
    if _container is None:
        _container = create_default_container()
    return _container


def set_container(container: SimpleContainer) -> None:
    """Set the global DI container (for testing)."""
    global _container
    _container = container


def create_default_container() -> SimpleContainer:
    """Create and configure the default DI container."""
    container = SimpleContainer()

    # Register infrastructure services
    container.register(IEventBus, MemoryEventBus, lifetime=Lifetime.SINGLETON)
    container.register(ITaskQueue, MemoryTaskQueue, lifetime=Lifetime.SINGLETON)

    return container


def get_service(service_type: Type[T]) -> Callable[[], T]:
    """
    Create a FastAPI dependency that resolves a service from the container.

    Usage:
        @router.get("/items")
        def get_items(task_queue: Annotated[ITaskQueue, Depends(get_service(ITaskQueue))]):
            ...
    """
    def _get_service() -> T:
        container = get_container()
        return container.resolve(service_type)

    return _get_service


# Pre-built dependencies for common services
def get_event_bus() -> IEventBus:
    """Get the event bus instance."""
    return get_container().resolve(IEventBus)


def get_task_queue() -> ITaskQueue:
    """Get the task queue instance."""
    return get_container().resolve(ITaskQueue)


def get_version_manager() -> IVersionManager | None:
    """Get the version manager instance (if registered)."""
    return get_container().try_resolve(IVersionManager)


# Type aliases for cleaner dependency injection
EventBusDep = Annotated[IEventBus, Depends(get_event_bus)]
TaskQueueDep = Annotated[ITaskQueue, Depends(get_task_queue)]


# Request-scoped dependencies
def get_request_scope(request: Request) -> IServiceScope:
    """
    Get or create a request-scoped service scope.

    This scope is created once per request and stored in request.state.
    """
    if not hasattr(request.state, "service_scope"):
        container = get_container()
        request.state.service_scope = container.create_scope()
    return request.state.service_scope


RequestScopeDep = Annotated[IServiceScope, Depends(get_request_scope)]


# Cleanup middleware helper
@asynccontextmanager
async def lifespan_scope():
    """Context manager for managing scope lifecycle."""
    container = get_container()
    scope = container.create_scope()
    try:
        yield scope
    finally:
        scope.__exit__(None, None, None)


# In-memory stores for development (will be replaced by actual storage)
class InMemoryKnowledgeBaseStore:
    """In-memory store for knowledge bases (development only)."""

    def __init__(self):
        self._knowledge_bases: dict[str, Any] = {}
        self._versions: dict[str, Any] = {}
        self._file_versions: dict[str, Any] = {}

    def get_knowledge_base(self, kb_id: str) -> Any | None:
        return self._knowledge_bases.get(kb_id)

    def list_knowledge_bases(self) -> list[Any]:
        return list(self._knowledge_bases.values())

    def save_knowledge_base(self, kb: Any) -> None:
        self._knowledge_bases[kb.id] = kb

    def delete_knowledge_base(self, kb_id: str) -> bool:
        if kb_id in self._knowledge_bases:
            del self._knowledge_bases[kb_id]
            # Also delete related versions
            version_ids_to_delete = [
                v_id for v_id, v in self._versions.items()
                if v.knowledge_base_id == kb_id
            ]
            for v_id in version_ids_to_delete:
                del self._versions[v_id]
            return True
        return False

    def get_version(self, version_id: str) -> Any | None:
        return self._versions.get(version_id)

    def list_versions(self, kb_id: str) -> list[Any]:
        return [v for v in self._versions.values() if v.knowledge_base_id == kb_id]

    def save_version(self, version: Any) -> None:
        self._versions[version.id] = version

    def delete_version(self, version_id: str) -> bool:
        if version_id in self._versions:
            del self._versions[version_id]
            return True
        return False

    def get_file_versions(self, version_id: str) -> list[Any]:
        return [fv for fv in self._file_versions.values() if fv.knowledge_base_version_id == version_id]

    def save_file_version(self, file_version: Any) -> None:
        self._file_versions[file_version.id] = file_version

    def delete_file_version(self, file_version_id: str) -> bool:
        if file_version_id in self._file_versions:
            del self._file_versions[file_version_id]
            return True
        return False


# Global store instance (for development)
_kb_store: InMemoryKnowledgeBaseStore | None = None


def get_kb_store() -> InMemoryKnowledgeBaseStore:
    """Get the in-memory knowledge base store."""
    global _kb_store
    if _kb_store is None:
        _kb_store = InMemoryKnowledgeBaseStore()
    return _kb_store


KbStoreDep = Annotated[InMemoryKnowledgeBaseStore, Depends(get_kb_store)]


class InMemoryEnvironmentStore:
    """In-memory store for environments (development only)."""

    def __init__(self):
        self._environments: dict[str, Any] = {}

    def get_environment(self, env_id: str) -> Any | None:
        return self._environments.get(env_id)

    def list_environments(self) -> list[Any]:
        return list(self._environments.values())

    def save_environment(self, env: Any) -> None:
        self._environments[env.id] = env

    def delete_environment(self, env_id: str) -> bool:
        if env_id in self._environments:
            del self._environments[env_id]
            return True
        return False

    def get_default_environment(self) -> Any | None:
        for env in self._environments.values():
            if env.is_default:
                return env
        return None

    def clear_default(self) -> None:
        """Clear the default flag from all environments."""
        for env in self._environments.values():
            env.is_default = False


# Global environment store instance (for development)
_env_store: InMemoryEnvironmentStore | None = None


def get_env_store() -> InMemoryEnvironmentStore:
    """Get the in-memory environment store."""
    global _env_store
    if _env_store is None:
        _env_store = InMemoryEnvironmentStore()
    return _env_store


EnvStoreDep = Annotated[InMemoryEnvironmentStore, Depends(get_env_store)]
