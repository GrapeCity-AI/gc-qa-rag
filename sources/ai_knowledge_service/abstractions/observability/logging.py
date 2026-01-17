"""
Logging interfaces - Defines structured logging.
"""

from enum import Enum
from typing import Any, Optional, Protocol, runtime_checkable


class LogLevel(Enum):
    """Log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    def __ge__(self, other: "LogLevel") -> bool:
        """Compare log levels."""
        order = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        return order.index(self) >= order.index(other)

    def __gt__(self, other: "LogLevel") -> bool:
        """Compare log levels."""
        order = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        return order.index(self) > order.index(other)

    def __le__(self, other: "LogLevel") -> bool:
        """Compare log levels."""
        return not self.__gt__(other)

    def __lt__(self, other: "LogLevel") -> bool:
        """Compare log levels."""
        return not self.__ge__(other)


@runtime_checkable
class ILogger(Protocol):
    """
    Logger - Interface for structured logging.

    Supports contextual logging where additional context can be
    attached to all subsequent log messages.
    """

    def log(
        self,
        level: LogLevel,
        message: str,
        **context: Any,
    ) -> None:
        """
        Log a message at the specified level.

        Args:
            level: Log level.
            message: Log message.
            **context: Additional context fields.
        """
        ...

    def debug(self, message: str, **context: Any) -> None:
        """
        Log a debug message.

        Args:
            message: Log message.
            **context: Additional context fields.
        """
        ...

    def info(self, message: str, **context: Any) -> None:
        """
        Log an info message.

        Args:
            message: Log message.
            **context: Additional context fields.
        """
        ...

    def warning(self, message: str, **context: Any) -> None:
        """
        Log a warning message.

        Args:
            message: Log message.
            **context: Additional context fields.
        """
        ...

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        **context: Any,
    ) -> None:
        """
        Log an error message.

        Args:
            message: Log message.
            error: Optional exception to include.
            **context: Additional context fields.
        """
        ...

    def critical(
        self,
        message: str,
        error: Optional[Exception] = None,
        **context: Any,
    ) -> None:
        """
        Log a critical message.

        Args:
            message: Log message.
            error: Optional exception to include.
            **context: Additional context fields.
        """
        ...

    def with_context(self, **context: Any) -> "ILogger":
        """
        Create a child logger with additional context.

        The returned logger will include the specified context
        in all log messages.

        Args:
            **context: Context fields to add.

        Returns:
            ILogger: A new logger with the added context.
        """
        ...

    def with_trace(self, trace_id: str, span_id: str) -> "ILogger":
        """
        Create a child logger with trace context.

        Args:
            trace_id: Trace ID.
            span_id: Span ID.

        Returns:
            ILogger: A new logger with trace context.
        """
        ...


@runtime_checkable
class ILoggerFactory(Protocol):
    """
    Logger Factory - Creates named loggers.
    """

    def get_logger(self, name: str) -> ILogger:
        """
        Get a logger by name.

        Args:
            name: Logger name (typically module or class name).

        Returns:
            ILogger: The logger instance.
        """
        ...

    def set_level(self, level: LogLevel) -> None:
        """
        Set the minimum log level.

        Args:
            level: Minimum level to log.
        """
        ...

    def get_level(self) -> LogLevel:
        """
        Get the current minimum log level.

        Returns:
            LogLevel: Current minimum level.
        """
        ...
