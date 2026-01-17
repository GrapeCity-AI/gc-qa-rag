"""
Tracing interfaces - Defines distributed tracing.
"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


class SpanNames:
    """Predefined span names for consistency."""

    # Task execution
    TASK_EXECUTE = "task.execute"
    TASK_VALIDATE = "task.validate"

    # Ingestion
    INGESTION_CONNECT = "ingestion.connect"
    INGESTION_FETCH = "ingestion.fetch"
    INGESTION_VALIDATE = "ingestion.validate"
    INGESTION_EXTRACT_METADATA = "ingestion.extract_metadata"
    INGESTION_SAVE = "ingestion.save"
    INGESTION_DEDUP_CHECK = "ingestion.dedup_check"

    # Indexing
    INDEXING_LOAD_FILE = "indexing.load_file"
    INDEXING_PARSE = "indexing.parse"
    INDEXING_CHUNK = "indexing.chunk"
    INDEXING_ENRICH = "indexing.enrich"
    INDEXING_EMBED = "indexing.embed"
    INDEXING_BUILD_INDEX = "indexing.build_index"
    INDEXING_WRITE = "indexing.write"

    # Publishing
    PUBLISHING_EXPORT = "publishing.export"
    PUBLISHING_TRANSFER = "publishing.transfer"
    PUBLISHING_IMPORT = "publishing.import"
    PUBLISHING_SWITCH_ALIAS = "publishing.switch_alias"
    PUBLISHING_VALIDATE = "publishing.validate"

    # Storage
    STORAGE_READ = "storage.read"
    STORAGE_WRITE = "storage.write"
    STORAGE_DELETE = "storage.delete"
    STORAGE_QUERY = "storage.query"

    # External calls
    EXTERNAL_LLM_CALL = "external.llm.call"
    EXTERNAL_EMBEDDING_CALL = "external.embedding.call"
    EXTERNAL_HTTP_REQUEST = "external.http.request"


@runtime_checkable
class ISpan(Protocol):
    """
    Span - A unit of work in a distributed trace.

    Spans can be nested to represent parent-child relationships.
    """

    @property
    def trace_id(self) -> str:
        """Get the trace ID."""
        ...

    @property
    def span_id(self) -> str:
        """Get the span ID."""
        ...

    @property
    def parent_span_id(self) -> Optional[str]:
        """Get the parent span ID, if any."""
        ...

    def set_tag(self, key: str, value: str) -> None:
        """
        Set a tag on the span.

        Args:
            key: Tag key.
            value: Tag value.
        """
        ...

    def set_tags(self, tags: Dict[str, str]) -> None:
        """
        Set multiple tags on the span.

        Args:
            tags: Dictionary of tags.
        """
        ...

    def log(self, message: str, **kwargs: Any) -> None:
        """
        Log an event on the span.

        Args:
            message: Log message.
            **kwargs: Additional log fields.
        """
        ...

    def set_error(self, error: Exception) -> None:
        """
        Mark the span as errored.

        Args:
            error: The exception that occurred.
        """
        ...

    def set_status(self, status: str, message: str = "") -> None:
        """
        Set the span status.

        Args:
            status: Status code ("ok", "error").
            message: Optional status message.
        """
        ...

    def finish(self) -> None:
        """Finish the span."""
        ...

    def __enter__(self) -> "ISpan":
        """Start the span as a context manager."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Finish the span, recording any exception."""
        ...


@runtime_checkable
class ITracer(Protocol):
    """
    Tracer - Interface for distributed tracing.

    The tracer creates and manages spans for tracking operations
    across service boundaries.
    """

    def start_span(
        self,
        name: str,
        parent: Optional[ISpan] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> ISpan:
        """
        Start a new span.

        Args:
            name: Span name.
            parent: Optional parent span.
            tags: Optional initial tags.

        Returns:
            ISpan: The new span.
        """
        ...

    def get_current_span(self) -> Optional[ISpan]:
        """
        Get the current active span.

        Returns:
            Optional[ISpan]: The current span, or None if no active span.
        """
        ...

    def inject_context(self, carrier: Dict[str, str]) -> None:
        """
        Inject trace context into a carrier for propagation.

        Args:
            carrier: Dictionary to inject context into.
        """
        ...

    def extract_context(
        self,
        carrier: Dict[str, str],
    ) -> Optional[ISpan]:
        """
        Extract trace context from a carrier.

        Args:
            carrier: Dictionary containing trace context.

        Returns:
            Optional[ISpan]: A span representing the extracted context.
        """
        ...

    def with_span(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> ISpan:
        """
        Create a span as a context manager, automatically parented to current span.

        Usage:
            with tracer.with_span("operation") as span:
                span.set_tag("key", "value")
                do_something()

        Args:
            name: Span name.
            tags: Optional initial tags.

        Returns:
            ISpan: The new span.
        """
        ...
