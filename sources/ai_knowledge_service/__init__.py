"""
AI Knowledge Service

A modular, extensible knowledge service framework for building
RAG (Retrieval-Augmented Generation) systems.

This package provides:
- Abstract interfaces for all components (abstractions module)
- Core pipeline orchestration (core module - future)
- Concrete implementations (implementations module - future)

The abstractions module defines all interfaces using Python's Protocol
for structural subtyping, enabling clean dependency injection and
easy testing.
"""

__version__ = "0.1.0"

# Re-export key types from abstractions for convenience
from ai_knowledge_service.abstractions import (
    # Models
    KnowledgeBase,
    KnowledgeBaseVersion,
    VersionStatus,
    FileVersion,
    IndexStatus,
    RawFile,
    LifecycleStatus,
    IndexRecord,
    TaskType,
    TaskStatus,
    BuildType,
    PublishStrategy,
    # Execution
    ITaskExecutor,
    ITaskQueue,
    ITaskScheduler,
    # Pipelines
    ISourceConnector,
    IProcessingStep,
    IContentParser,
    IChunker,
    IEnricher,
    IEmbedder,
    # Storage
    IRawFileStorage,
    IIndexStorage,
    # Observability
    IMetricsCollector,
    ITracer,
    ILogger,
    IHealthChecker,
    ObservabilityContext,
    # Infrastructure
    IVersionManager,
    IEventBus,
    IServiceContainer,
    Lifetime,
)

__all__ = [
    # Version
    "__version__",
    # Models
    "KnowledgeBase",
    "KnowledgeBaseVersion",
    "VersionStatus",
    "FileVersion",
    "IndexStatus",
    "RawFile",
    "LifecycleStatus",
    "IndexRecord",
    "TaskType",
    "TaskStatus",
    "BuildType",
    "PublishStrategy",
    # Execution
    "ITaskExecutor",
    "ITaskQueue",
    "ITaskScheduler",
    # Pipelines
    "ISourceConnector",
    "IProcessingStep",
    "IContentParser",
    "IChunker",
    "IEnricher",
    "IEmbedder",
    # Storage
    "IRawFileStorage",
    "IIndexStorage",
    # Observability
    "IMetricsCollector",
    "ITracer",
    "ILogger",
    "IHealthChecker",
    "ObservabilityContext",
    # Infrastructure
    "IVersionManager",
    "IEventBus",
    "IServiceContainer",
    "Lifetime",
]
