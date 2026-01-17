"""
Observability Context - Carries observability information through the pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from ai_knowledge_service.abstractions.models.tasks import TaskType


@dataclass
class ObservabilityContext:
    """
    Observability Context - Carries observability information through processing.

    This context is passed through the processing pipeline to enable
    consistent metrics, tracing, and logging across all steps.
    """

    # Tracing
    trace_id: str
    span_id: str

    # Business context
    task_id: str
    task_type: TaskType
    knowledge_base_id: str
    knowledge_base_version_id: str

    # Optional extra context
    extra: Dict[str, str] = field(default_factory=dict)

    # Optional references to observability components
    # These are set by the executor and used by steps
    _metrics: Optional["IMetricsCollector"] = field(default=None, repr=False)
    _tracer: Optional["ITracer"] = field(default=None, repr=False)
    _logger: Optional["ILogger"] = field(default=None, repr=False)

    def to_tags(self) -> Dict[str, str]:
        """
        Convert to a dictionary of tags for metrics/tracing.

        Returns:
            Dict[str, str]: Tags dictionary.
        """
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "kb_id": self.knowledge_base_id,
            "kb_version_id": self.knowledge_base_version_id,
            **self.extra,
        }

    def to_log_context(self) -> Dict[str, str]:
        """
        Convert to a dictionary for logging context.

        Returns:
            Dict[str, str]: Log context dictionary.
        """
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "knowledge_base_id": self.knowledge_base_id,
            "knowledge_base_version_id": self.knowledge_base_version_id,
            **self.extra,
        }

    def with_span(self, span_id: str) -> "ObservabilityContext":
        """
        Create a new context with an updated span ID.

        Args:
            span_id: New span ID.

        Returns:
            ObservabilityContext: New context with updated span ID.
        """
        return ObservabilityContext(
            trace_id=self.trace_id,
            span_id=span_id,
            task_id=self.task_id,
            task_type=self.task_type,
            knowledge_base_id=self.knowledge_base_id,
            knowledge_base_version_id=self.knowledge_base_version_id,
            extra=self.extra.copy(),
            _metrics=self._metrics,
            _tracer=self._tracer,
            _logger=self._logger,
        )

    def with_extra(self, **extra: str) -> "ObservabilityContext":
        """
        Create a new context with additional extra fields.

        Args:
            **extra: Extra fields to add.

        Returns:
            ObservabilityContext: New context with added fields.
        """
        new_extra = {**self.extra, **extra}
        return ObservabilityContext(
            trace_id=self.trace_id,
            span_id=self.span_id,
            task_id=self.task_id,
            task_type=self.task_type,
            knowledge_base_id=self.knowledge_base_id,
            knowledge_base_version_id=self.knowledge_base_version_id,
            extra=new_extra,
            _metrics=self._metrics,
            _tracer=self._tracer,
            _logger=self._logger,
        )

    @classmethod
    def create(
        cls,
        task_id: str,
        task_type: TaskType,
        knowledge_base_id: str,
        knowledge_base_version_id: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
    ) -> "ObservabilityContext":
        """
        Create a new observability context.

        If trace_id or span_id are not provided, they will be generated.

        Args:
            task_id: Task ID.
            task_type: Task type.
            knowledge_base_id: Knowledge base ID.
            knowledge_base_version_id: Knowledge base version ID.
            trace_id: Optional trace ID.
            span_id: Optional span ID.

        Returns:
            ObservabilityContext: New context.
        """
        import uuid

        return cls(
            trace_id=trace_id or str(uuid.uuid4()),
            span_id=span_id or str(uuid.uuid4()),
            task_id=task_id,
            task_type=task_type,
            knowledge_base_id=knowledge_base_id,
            knowledge_base_version_id=knowledge_base_version_id,
        )


# Type hints for the optional components (avoiding circular imports)
# These are imported at runtime by implementations
IMetricsCollector = "ai_knowledge_service.abstractions.observability.metrics.IMetricsCollector"
ITracer = "ai_knowledge_service.abstractions.observability.tracing.ITracer"
ILogger = "ai_knowledge_service.abstractions.observability.logging.ILogger"
