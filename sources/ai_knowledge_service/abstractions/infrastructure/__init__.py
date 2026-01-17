"""
Infrastructure module - Core infrastructure interfaces.
"""

from ai_knowledge_service.abstractions.infrastructure.version_manager import (
    IVersionManager,
)

from ai_knowledge_service.abstractions.infrastructure.event_bus import (
    IEventBus,
    DomainEvent,
    FileIngestedEvent,
    BuildTaskCompletedEvent,
    VersionPublishedEvent,
)

from ai_knowledge_service.abstractions.infrastructure.container import (
    IServiceContainer,
    IServiceScope,
    Lifetime,
)

__all__ = [
    # Version Manager
    "IVersionManager",
    # Event Bus
    "IEventBus",
    "DomainEvent",
    "FileIngestedEvent",
    "BuildTaskCompletedEvent",
    "VersionPublishedEvent",
    # Container
    "IServiceContainer",
    "IServiceScope",
    "Lifetime",
]
