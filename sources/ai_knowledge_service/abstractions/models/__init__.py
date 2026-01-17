"""
Models module - Domain models for AI Knowledge Service.
"""

from ai_knowledge_service.abstractions.models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseVersion,
    VersionStatus,
    FileVersion,
    IndexStatus,
)

from ai_knowledge_service.abstractions.models.raw_file import (
    RawFile,
    LifecycleStatus,
)

from ai_knowledge_service.abstractions.models.index import (
    IndexRecord,
    IndexSchema,
    VectorConfig,
    FieldDefinition,
    FieldType,
)

from ai_knowledge_service.abstractions.models.tasks import (
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

__all__ = [
    # Knowledge Base
    "KnowledgeBase",
    "KnowledgeBaseVersion",
    "VersionStatus",
    "FileVersion",
    "IndexStatus",
    # Raw File
    "RawFile",
    "LifecycleStatus",
    # Index
    "IndexRecord",
    "IndexSchema",
    "VectorConfig",
    "FieldDefinition",
    "FieldType",
    # Tasks
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
]
