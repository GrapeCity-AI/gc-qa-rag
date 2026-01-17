"""
Observability module - Interfaces for metrics, tracing, logging, and health checks.
"""

from ai_knowledge_service.abstractions.observability.metrics import (
    IMetricsCollector,
    ITimer,
    MetricNames,
)

from ai_knowledge_service.abstractions.observability.tracing import (
    ITracer,
    ISpan,
    SpanNames,
)

from ai_knowledge_service.abstractions.observability.logging import (
    ILogger,
    ILoggerFactory,
    LogLevel,
)

from ai_knowledge_service.abstractions.observability.health import (
    IHealthCheck,
    IHealthChecker,
    HealthStatus,
    HealthCheckResult,
)

from ai_knowledge_service.abstractions.observability.context import (
    ObservabilityContext,
)

__all__ = [
    # Metrics
    "IMetricsCollector",
    "ITimer",
    "MetricNames",
    # Tracing
    "ITracer",
    "ISpan",
    "SpanNames",
    # Logging
    "ILogger",
    "ILoggerFactory",
    "LogLevel",
    # Health
    "IHealthCheck",
    "IHealthChecker",
    "HealthStatus",
    "HealthCheckResult",
    # Context
    "ObservabilityContext",
]
