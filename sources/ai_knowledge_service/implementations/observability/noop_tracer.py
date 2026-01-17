"""
Noop Tracer - No-operation distributed tracer.

This implementation does nothing with traces, useful for:
- Development/testing when no tracing backend is needed
- Disabling tracing without changing application code
"""

import uuid
from typing import Any, Dict, Optional

from ai_knowledge_service.abstractions.observability.tracing import (
    ISpan,
    ITracer,
)


class NoopSpan(ISpan):
    """No-operation span."""

    def __init__(
        self,
        name: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ):
        self._name = name
        self._trace_id = trace_id or str(uuid.uuid4()).replace("-", "")
        self._span_id = span_id or str(uuid.uuid4()).replace("-", "")[:16]
        self._parent_span_id = parent_span_id

    @property
    def trace_id(self) -> str:
        """Get the trace ID."""
        return self._trace_id

    @property
    def span_id(self) -> str:
        """Get the span ID."""
        return self._span_id

    @property
    def parent_span_id(self) -> Optional[str]:
        """Get the parent span ID, if any."""
        return self._parent_span_id

    def set_tag(self, key: str, value: str) -> None:
        """Set a tag on the span (no-op)."""
        pass

    def set_tags(self, tags: Dict[str, str]) -> None:
        """Set multiple tags on the span (no-op)."""
        pass

    def log(self, message: str, **kwargs: Any) -> None:
        """Log an event on the span (no-op)."""
        pass

    def set_error(self, error: Exception) -> None:
        """Mark the span as errored (no-op)."""
        pass

    def set_status(self, status: str, message: str = "") -> None:
        """Set the span status (no-op)."""
        pass

    def finish(self) -> None:
        """Finish the span (no-op)."""
        pass

    def __enter__(self) -> "NoopSpan":
        """Start the span as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Finish the span."""
        pass


class NoopTracer(ITracer):
    """
    No-operation tracer.

    All tracing operations are no-ops but return valid span objects
    that can be used without null checks.
    """

    def __init__(self):
        self._current_span: Optional[NoopSpan] = None

    def start_span(
        self,
        name: str,
        parent: Optional[ISpan] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> ISpan:
        """Start a new span."""
        parent_trace_id = parent.trace_id if parent else None
        parent_span_id = parent.span_id if parent else None

        span = NoopSpan(
            name=name,
            trace_id=parent_trace_id,
            parent_span_id=parent_span_id,
        )
        self._current_span = span
        return span

    def get_current_span(self) -> Optional[ISpan]:
        """Get the current active span."""
        return self._current_span

    def inject_context(self, carrier: Dict[str, str]) -> None:
        """Inject trace context into a carrier (no-op)."""
        if self._current_span:
            carrier["traceparent"] = (
                f"00-{self._current_span.trace_id}-{self._current_span.span_id}-01"
            )

    def extract_context(
        self,
        carrier: Dict[str, str],
    ) -> Optional[ISpan]:
        """Extract trace context from a carrier."""
        traceparent = carrier.get("traceparent")
        if not traceparent:
            return None

        parts = traceparent.split("-")
        if len(parts) < 3:
            return None

        return NoopSpan(
            name="extracted",
            trace_id=parts[1],
            span_id=parts[2],
        )

    def with_span(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> ISpan:
        """Create a span as a context manager."""
        return self.start_span(name, parent=self._current_span, tags=tags)
