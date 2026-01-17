"""
Metrics interfaces - Defines metrics collection.
"""

from typing import Dict, Optional, Protocol, runtime_checkable


class MetricNames:
    """Predefined metric names for consistency."""

    # Task metrics
    TASK_ENQUEUED = "task.enqueued"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_DURATION = "task.duration_seconds"
    TASK_RETRY = "task.retry"

    # Ingestion metrics
    INGESTION_FILES_TOTAL = "ingestion.files.total"
    INGESTION_FILES_NEW = "ingestion.files.new"
    INGESTION_FILES_UPDATED = "ingestion.files.updated"
    INGESTION_FILES_SKIPPED = "ingestion.files.skipped"
    INGESTION_BYTES_TOTAL = "ingestion.bytes.total"
    INGESTION_DURATION = "ingestion.duration_seconds"

    # Indexing metrics
    INDEXING_RECORDS_TOTAL = "indexing.records.total"
    INDEXING_RECORDS_FAILED = "indexing.records.failed"
    INDEXING_STEP_DURATION = "indexing.step.duration_seconds"
    INDEXING_STEP_ERRORS = "indexing.step.errors"
    INDEXING_STEP_INPUT = "indexing.step.input_count"
    INDEXING_STEP_OUTPUT = "indexing.step.output_count"

    # Publishing metrics
    PUBLISHING_RECORDS_TOTAL = "publishing.records.total"
    PUBLISHING_DURATION = "publishing.duration_seconds"
    PUBLISHING_FILES_TOTAL = "publishing.files.total"

    # Storage metrics
    STORAGE_RAW_FILES_COUNT = "storage.raw_files.count"
    STORAGE_RAW_FILES_BYTES = "storage.raw_files.bytes"
    STORAGE_INDEX_RECORDS_COUNT = "storage.index_records.count"
    STORAGE_COLLECTIONS_COUNT = "storage.collections.count"

    # Queue metrics
    QUEUE_PENDING_COUNT = "queue.pending.count"
    QUEUE_RUNNING_COUNT = "queue.running.count"
    QUEUE_ENQUEUE_DURATION = "queue.enqueue.duration_seconds"
    QUEUE_DEQUEUE_DURATION = "queue.dequeue.duration_seconds"


@runtime_checkable
class ITimer(Protocol):
    """
    Timer - Context manager for measuring duration.
    """

    def __enter__(self) -> "ITimer":
        """Start the timer."""
        ...

    def __exit__(self, *args) -> None:
        """Stop the timer and record the duration."""
        ...

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        ...

    def stop(self) -> float:
        """
        Manually stop the timer.

        Returns:
            float: Elapsed time in seconds.
        """
        ...


@runtime_checkable
class IMetricsCollector(Protocol):
    """
    Metrics Collector - Interface for collecting metrics.

    Supports:
    - Counters: Monotonically increasing values
    - Gauges: Values that can go up and down
    - Histograms: Distribution of values
    - Timers: Duration measurements
    """

    def counter(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter.

        Args:
            name: Metric name.
            value: Value to add (default 1).
            tags: Optional tags/labels.
        """
        ...

    def gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Set a gauge value.

        Args:
            name: Metric name.
            value: Current value.
            tags: Optional tags/labels.
        """
        ...

    def histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a histogram value.

        Args:
            name: Metric name.
            value: Observed value.
            tags: Optional tags/labels.
        """
        ...

    def timer(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> ITimer:
        """
        Create a timer for measuring duration.

        Usage:
            with metrics.timer("operation.duration") as t:
                do_something()
            # Duration is automatically recorded

        Args:
            name: Metric name.
            tags: Optional tags/labels.

        Returns:
            ITimer: A timer context manager.
        """
        ...

    def record_duration(
        self,
        name: str,
        duration_seconds: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a duration value directly.

        Args:
            name: Metric name.
            duration_seconds: Duration in seconds.
            tags: Optional tags/labels.
        """
        ...

    def flush(self) -> None:
        """
        Flush any buffered metrics.

        Some implementations buffer metrics for efficiency.
        Call this to ensure all metrics are sent.
        """
        ...
