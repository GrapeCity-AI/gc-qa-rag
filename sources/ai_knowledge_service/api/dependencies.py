"""
Dependencies - FastAPI dependency injection bridge.

This module bridges FastAPI's Depends mechanism with the existing SimpleContainer DI.
Services are resolved from the container stored in app.state.
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


T = TypeVar("T")


def get_container_from_request(request: Request) -> SimpleContainer:
    """Get the DI container from the request's app state."""
    return request.app.state.container


def get_service_from_request(
    service_type: Type[T],
) -> Callable[[Request], T]:
    """
    Create a FastAPI dependency that resolves a service from the app container.

    Usage:
        @router.get("/items")
        def get_items(
            task_queue: Annotated[ITaskQueue, Depends(get_service_from_request(ITaskQueue))]
        ):
            ...
    """
    def _get_service(request: Request) -> T:
        container = get_container_from_request(request)
        return container.resolve(service_type)

    return _get_service


# Request-based dependencies for common services
def get_event_bus_from_request(request: Request) -> IEventBus:
    """Get the event bus instance from request."""
    container = get_container_from_request(request)
    return container.resolve(IEventBus)


def get_task_queue_from_request(request: Request) -> ITaskQueue:
    """Get the task queue instance from request."""
    container = get_container_from_request(request)
    return container.resolve(ITaskQueue)


def get_version_manager_from_request(request: Request) -> IVersionManager:
    """Get the version manager instance from request."""
    container = get_container_from_request(request)
    return container.resolve(IVersionManager)


# Type aliases for cleaner dependency injection (request-based)
ContainerDep = Annotated[SimpleContainer, Depends(get_container_from_request)]
EventBusDep = Annotated[IEventBus, Depends(get_event_bus_from_request)]
TaskQueueDep = Annotated[ITaskQueue, Depends(get_task_queue_from_request)]
VersionManagerDep = Annotated[IVersionManager, Depends(get_version_manager_from_request)]


# Request-scoped dependencies
def get_request_scope(request: Request) -> IServiceScope:
    """
    Get or create a request-scoped service scope.

    This scope is created once per request and stored in request.state.
    """
    if not hasattr(request.state, "service_scope"):
        container = get_container_from_request(request)
        request.state.service_scope = container.create_scope()
    return request.state.service_scope


RequestScopeDep = Annotated[IServiceScope, Depends(get_request_scope)]


# =============================================================================
# Legacy global container support (for backwards compatibility and testing)
# =============================================================================

_container: SimpleContainer | None = None


def get_container() -> SimpleContainer:
    """
    Get the global DI container.

    NOTE: Prefer using get_container_from_request for request handlers.
    This function is kept for backwards compatibility and testing.
    """
    global _container
    if _container is None:
        # Create a minimal container for backwards compatibility
        from ai_knowledge_service.implementations.infrastructure.memory_event_bus import MemoryEventBus
        from ai_knowledge_service.implementations.infrastructure.memory_queue import MemoryTaskQueue

        _container = SimpleContainer()
        _container.register(IEventBus, MemoryEventBus, lifetime=Lifetime.SINGLETON)
        _container.register(ITaskQueue, MemoryTaskQueue, lifetime=Lifetime.SINGLETON)

    return _container


def set_container(container: SimpleContainer) -> None:
    """Set the global DI container (for testing)."""
    global _container
    _container = container


def get_event_bus() -> IEventBus:
    """Get the event bus instance from global container."""
    return get_container().resolve(IEventBus)


def get_task_queue() -> ITaskQueue:
    """Get the task queue instance from global container."""
    return get_container().resolve(ITaskQueue)


def get_version_manager() -> IVersionManager | None:
    """Get the version manager instance from global container (if registered)."""
    return get_container().try_resolve(IVersionManager)


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


# =============================================================================
# In-memory stores (for development - will be replaced by actual storage)
# =============================================================================

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
