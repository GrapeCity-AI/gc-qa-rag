"""
AI Knowledge Service - Abstraction Layer

This package defines the abstract interfaces for the AI Knowledge Service.
All interfaces are defined using Python's Protocol for structural subtyping.
"""

from ai_knowledge_service.abstractions.models import (
    # Knowledge Base
    KnowledgeBase,
    KnowledgeBaseVersion,
    VersionStatus,
    FileVersion,
    IndexStatus,
    # Raw File
    RawFile,
    LifecycleStatus,
    # Index
    IndexRecord,
    IndexSchema,
    VectorConfig,
    FieldDefinition,
    FieldType,
    # Tasks
    TaskType,
    TaskStatus,
    TaskBase,
    TaskResultBase,
    ProcessingError,
    IngestionTask,
    IngestionTaskResult,
    IndexingTask,
    IndexingTaskResult,
    BuildType,
    StepConfig,
    StepStats,
    PublishingTask,
    PublishingTaskResult,
    PublishStrategy,
)

from ai_knowledge_service.abstractions.execution import (
    ITaskExecutor,
    IIngestionExecutor,
    IIndexingExecutor,
    IPublishingExecutor,
    ITaskQueue,
    ITaskScheduler,
    SchedulerStatus,
)

from ai_knowledge_service.abstractions.pipelines import (
    # Source
    ISourceConnector,
    SourceConfig,
    SourceRecord,
    ConnectionResult,
    ConnectionStatus,
    # Steps
    IProcessingStep,
    IContentParser,
    IChunker,
    IEnricher,
    IEmbedder,
    IIndexBuilder,
    ProcessingContext,
    ParsedDocument,
    Chunk,
    Embedding,
    # Publishing
    ITargetEnvironment,
    IIndexExporter,
    IIndexImporter,
    IRawFileExporter,
    EnvironmentCapabilities,
    ExportOptions,
    ExportResult,
    ImportOptions,
    ImportResult,
)

from ai_knowledge_service.abstractions.storage import (
    # Raw File Storage
    IRawFileStorage,
    IRawFileMetadataStore,
    IRawFileContentStore,
    QueryCriteria,
    # Index Storage
    IIndexStorage,
    WriteResult,
    CollectionInfo,
)

from ai_knowledge_service.abstractions.observability import (
    # Metrics
    IMetricsCollector,
    ITimer,
    MetricNames,
    # Tracing
    ITracer,
    ISpan,
    SpanNames,
    # Logging
    ILogger,
    ILoggerFactory,
    LogLevel,
    # Health
    IHealthCheck,
    IHealthChecker,
    HealthStatus,
    HealthCheckResult,
    # Context
    ObservabilityContext,
)

from ai_knowledge_service.abstractions.infrastructure import (
    # Version Manager
    IVersionManager,
    # Event Bus
    IEventBus,
    DomainEvent,
    FileIngestedEvent,
    BuildTaskCompletedEvent,
    VersionPublishedEvent,
    # Container
    IServiceContainer,
    IServiceScope,
    Lifetime,
)

from ai_knowledge_service.abstractions.config import (
    KnowledgeBaseConfig,
    IngestionConfig,
    IndexingConfig,
    PublishingConfig,
    ObservabilityConfig,
)

__all__ = [
    # Models - Knowledge Base
    "KnowledgeBase",
    "KnowledgeBaseVersion",
    "VersionStatus",
    "FileVersion",
    "IndexStatus",
    # Models - Raw File
    "RawFile",
    "LifecycleStatus",
    # Models - Index
    "IndexRecord",
    "IndexSchema",
    "VectorConfig",
    "FieldDefinition",
    "FieldType",
    # Models - Tasks
    "TaskType",
    "TaskStatus",
    "TaskBase",
    "TaskResultBase",
    "ProcessingError",
    "IngestionTask",
    "IngestionTaskResult",
    "IndexingTask",
    "IndexingTaskResult",
    "BuildType",
    "StepConfig",
    "StepStats",
    "PublishingTask",
    "PublishingTaskResult",
    "PublishStrategy",
    # Execution
    "ITaskExecutor",
    "IIngestionExecutor",
    "IIndexingExecutor",
    "IPublishingExecutor",
    "ITaskQueue",
    "ITaskScheduler",
    "SchedulerStatus",
    # Pipelines - Source
    "ISourceConnector",
    "SourceConfig",
    "SourceRecord",
    "ConnectionResult",
    "ConnectionStatus",
    # Pipelines - Steps
    "IProcessingStep",
    "IContentParser",
    "IChunker",
    "IEnricher",
    "IEmbedder",
    "IIndexBuilder",
    "ProcessingContext",
    "ParsedDocument",
    "Chunk",
    "Embedding",
    # Pipelines - Publishing
    "ITargetEnvironment",
    "IIndexExporter",
    "IIndexImporter",
    "IRawFileExporter",
    "EnvironmentCapabilities",
    "ExportOptions",
    "ExportResult",
    "ImportOptions",
    "ImportResult",
    # Storage
    "IRawFileStorage",
    "IRawFileMetadataStore",
    "IRawFileContentStore",
    "QueryCriteria",
    "IIndexStorage",
    "WriteResult",
    "CollectionInfo",
    # Observability
    "IMetricsCollector",
    "ITimer",
    "MetricNames",
    "ITracer",
    "ISpan",
    "SpanNames",
    "ILogger",
    "ILoggerFactory",
    "LogLevel",
    "IHealthCheck",
    "IHealthChecker",
    "HealthStatus",
    "HealthCheckResult",
    "ObservabilityContext",
    # Infrastructure
    "IVersionManager",
    "IEventBus",
    "DomainEvent",
    "FileIngestedEvent",
    "BuildTaskCompletedEvent",
    "VersionPublishedEvent",
    "IServiceContainer",
    "IServiceScope",
    "Lifetime",
    # Config
    "KnowledgeBaseConfig",
    "IngestionConfig",
    "IndexingConfig",
    "PublishingConfig",
    "ObservabilityConfig",
]
