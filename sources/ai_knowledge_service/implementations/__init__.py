"""
AI Knowledge Service - Implementations

Concrete implementations of the abstraction layer interfaces.
"""

__version__ = "0.1.0"

# Infrastructure
from ai_knowledge_service.implementations.infrastructure import (
    SimpleContainer,
    ServiceScope,
    MemoryEventBus,
    MemoryTaskQueue,
    SqliteVersionManager,
)

# Observability
from ai_knowledge_service.implementations.observability import (
    ConsoleLogger,
    ConsoleLoggerFactory,
    NoopMetricsCollector,
    NoopTimer,
    NoopTracer,
    NoopSpan,
)

# Storage
from ai_knowledge_service.implementations.storage import (
    FilesystemContentStore,
    SqliteMetadataStore,
    CompositeRawFileStorage,
)

__all__ = [
    # Infrastructure
    "SimpleContainer",
    "ServiceScope",
    "MemoryEventBus",
    "MemoryTaskQueue",
    "SqliteVersionManager",
    # Observability
    "ConsoleLogger",
    "ConsoleLoggerFactory",
    "NoopMetricsCollector",
    "NoopTimer",
    "NoopTracer",
    "NoopSpan",
    # Storage
    "FilesystemContentStore",
    "SqliteMetadataStore",
    "CompositeRawFileStorage",
]
