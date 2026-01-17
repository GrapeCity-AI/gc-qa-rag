"""
Noop Metrics - No-operation metrics collector.

This implementation does nothing with metrics, useful for:
- Development/testing when no metrics backend is needed
- Disabling metrics without changing application code
"""

import time
from typing import Dict, Optional

from ai_knowledge_service.abstractions.observability.metrics import (
    IMetricsCollector,
    ITimer,
)


class NoopTimer(ITimer):
    """No-operation timer."""

    def __init__(self):
        self._start_time: Optional[float] = None
        self._elapsed: float = 0.0

    def __enter__(self) -> "NoopTimer":
        """Start the timer."""
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        """Stop the timer."""
        self.stop()

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self._start_time is not None and self._elapsed == 0.0:
            return time.perf_counter() - self._start_time
        return self._elapsed

    def stop(self) -> float:
        """Manually stop the timer."""
        if self._start_time is not None and self._elapsed == 0.0:
            self._elapsed = time.perf_counter() - self._start_time
        return self._elapsed


class NoopMetricsCollector(IMetricsCollector):
    """
    No-operation metrics collector.

    All metric operations are no-ops.
    """

    def counter(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter (no-op)."""
        pass

    def gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge value (no-op)."""
        pass

    def histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a histogram value (no-op)."""
        pass

    def timer(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> ITimer:
        """Create a timer (returns noop timer)."""
        return NoopTimer()

    def record_duration(
        self,
        name: str,
        duration_seconds: float,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a duration value (no-op)."""
        pass

    def flush(self) -> None:
        """Flush any buffered metrics (no-op)."""
        pass
