"""
Task models - Models for task execution and results.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskType(Enum):
    """Task types."""

    INGESTION = "ingestion"
    INDEXING = "indexing"
    PUBLISHING = "publishing"


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"  # Waiting in queue
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed (partial success counts as failed)
    CANCELLED = "cancelled"  # Cancelled by user


class BuildType(Enum):
    """Index build type."""

    FULL = "full"  # Full rebuild
    INCREMENTAL = "incremental"  # Incremental update


class PublishStrategy(Enum):
    """Publishing strategy."""

    REPLACE = "replace"  # Replace existing
    BLUE_GREEN = "blue_green"  # Blue-green deployment


@dataclass
class ProcessingError:
    """
    Processing Error - Record of an error during processing.

    Used for skip-and-continue error handling.
    """

    item_id: str  # ID of the failed item
    item_name: str  # Human-readable name
    step: str  # Processing step where error occurred
    error_type: str  # Error type/category
    error_message: str  # Error message
    stacktrace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    recoverable: bool = True  # Whether the error can be retried

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "step": self.step,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stacktrace": self.stacktrace,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
        }


@dataclass
class StepConfig:
    """Configuration for a processing step."""

    step_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def __post_init__(self):
        if not self.step_type:
            raise ValueError("Step type cannot be empty")

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self.config.get(key, default)


@dataclass
class StepStats:
    """Statistics for a processing step execution."""

    step_type: str
    input_count: int
    output_count: int
    duration_seconds: float
    errors_count: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.input_count == 0:
            return 1.0
        return (self.input_count - self.errors_count) / self.input_count


@dataclass
class TaskBase(ABC):
    """
    Task Base - Abstract base class for all tasks.

    All tasks are job-mode and driven by the task queue.
    """

    id: str
    task_type: TaskType
    knowledge_base_id: str
    knowledge_base_version_id: str

    # Scheduling
    priority: int = 0  # Higher priority = processed first
    retry_count: int = 0
    max_retries: int = 3

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Task ID cannot be empty")
        if not self.knowledge_base_id:
            raise ValueError("Knowledge base ID cannot be empty")
        if not self.knowledge_base_version_id:
            raise ValueError("Knowledge base version ID cannot be empty")

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries


@dataclass
class TaskResultBase(ABC):
    """
    Task Result Base - Abstract base class for all task results.
    """

    task_id: str
    task_type: TaskType
    status: TaskStatus

    # Statistics
    total_items: int
    succeeded_count: int
    failed_count: int
    skipped_count: int

    # Errors (skip-and-continue mode)
    errors: List[ProcessingError] = field(default_factory=list)

    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime = field(default_factory=datetime.now)

    @property
    def duration_seconds(self) -> float:
        """Calculate task duration in seconds."""
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_items == 0:
            return 1.0
        return self.succeeded_count / self.total_items

    @property
    def has_errors(self) -> bool:
        """Check if task has any errors."""
        return len(self.errors) > 0

    def add_error(self, error: ProcessingError) -> None:
        """Add an error to the result."""
        self.errors.append(error)


# ============ Ingestion Task ============


@dataclass
class IngestionTask(TaskBase):
    """
    Ingestion Task - Task for ingesting data from a source.
    """

    task_type: TaskType = field(default=TaskType.INGESTION, init=False)

    # Source configuration (will be replaced with SourceConfig reference)
    source_config: Dict[str, Any] = field(default_factory=dict)

    # Ingestion options
    incremental: bool = False
    since: Optional[datetime] = None  # For incremental ingestion

    # Validation
    validators: List[str] = field(default_factory=list)
    dedup_strategy: str = "version"  # "skip", "replace", "version"

    def __post_init__(self):
        super().__post_init__()
        if self.incremental and self.since is None:
            raise ValueError(
                "Incremental ingestion requires 'since' timestamp"
            )


@dataclass
class IngestionTaskResult(TaskResultBase):
    """
    Ingestion Task Result - Result of an ingestion task.
    """

    task_type: TaskType = field(default=TaskType.INGESTION, init=False)

    # Ingestion output
    ingested_file_ids: List[str] = field(default_factory=list)

    # Detailed statistics
    new_files_count: int = 0
    updated_files_count: int = 0
    unchanged_files_count: int = 0


# ============ Indexing Task ============


@dataclass
class IndexingTask(TaskBase):
    """
    Indexing Task - Task for building indexes from raw files.
    """

    task_type: TaskType = field(default=TaskType.INDEXING, init=False)

    # Build scope
    build_type: BuildType = BuildType.FULL
    file_version_ids: List[str] = field(default_factory=list)  # Empty = all files

    # Pipeline configuration
    pipeline_config: List[StepConfig] = field(default_factory=list)

    @property
    def is_full_build(self) -> bool:
        """Check if this is a full build."""
        return self.build_type == BuildType.FULL or len(self.file_version_ids) == 0

    @property
    def is_incremental_build(self) -> bool:
        """Check if this is an incremental build."""
        return self.build_type == BuildType.INCREMENTAL and len(self.file_version_ids) > 0


@dataclass
class IndexingTaskResult(TaskResultBase):
    """
    Indexing Task Result - Result of an indexing task.
    """

    task_type: TaskType = field(default=TaskType.INDEXING, init=False)

    # Indexing output
    index_records_count: int = 0
    collections_affected: List[str] = field(default_factory=list)

    # Per-step statistics
    step_stats: Dict[str, StepStats] = field(default_factory=dict)

    def add_step_stats(self, stats: StepStats) -> None:
        """Add statistics for a processing step."""
        self.step_stats[stats.step_type] = stats

    def get_step_stats(self, step_type: str) -> Optional[StepStats]:
        """Get statistics for a specific step."""
        return self.step_stats.get(step_type)


# ============ Publishing Task ============


@dataclass
class PublishingTask(TaskBase):
    """
    Publishing Task - Task for publishing indexes to a target environment.
    """

    task_type: TaskType = field(default=TaskType.PUBLISHING, init=False)

    # Target
    target_environment_id: str = ""

    # Publishing options
    include_raw_files: bool = False
    alias_name: Optional[str] = None
    publish_strategy: PublishStrategy = PublishStrategy.BLUE_GREEN

    def __post_init__(self):
        super().__post_init__()
        if not self.target_environment_id:
            raise ValueError("Target environment ID cannot be empty")


@dataclass
class PublishingTaskResult(TaskResultBase):
    """
    Publishing Task Result - Result of a publishing task.
    """

    task_type: TaskType = field(default=TaskType.PUBLISHING, init=False)

    # Publishing output
    target_collection: str = ""
    alias_applied: Optional[str] = None
    previous_collection: Optional[str] = None  # For rollback

    # Statistics
    index_records_published: int = 0
    raw_files_published: int = 0
