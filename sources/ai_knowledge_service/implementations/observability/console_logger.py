"""
Console Logger - Simple console-based logging implementation.

This implementation provides:
- Colored console output
- Structured logging with context
- Log level filtering
- Trace context support
"""

import json
import sys
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from ai_knowledge_service.abstractions.observability.logging import (
    ILogger,
    ILoggerFactory,
    LogLevel,
)


COLORS = {
    LogLevel.DEBUG: "\033[36m",     # Cyan
    LogLevel.INFO: "\033[32m",      # Green
    LogLevel.WARNING: "\033[33m",   # Yellow
    LogLevel.ERROR: "\033[31m",     # Red
    LogLevel.CRITICAL: "\033[35m",  # Magenta
}
RESET = "\033[0m"
BOLD = "\033[1m"


class ConsoleLogger(ILogger):
    """
    Console Logger implementation.

    Outputs log messages to the console with optional color coding.
    """

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        use_colors: bool = True,
        use_json: bool = False,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
    ):
        self._name = name
        self._level = level
        self._use_colors = use_colors and sys.stdout.isatty()
        self._use_json = use_json
        self._context = context or {}
        self._trace_id = trace_id
        self._span_id = span_id
        self._lock = threading.Lock()

    def log(
        self,
        level: LogLevel,
        message: str,
        **context: Any,
    ) -> None:
        """Log a message at the specified level."""
        if level < self._level:
            return

        merged_context = {**self._context, **context}

        if self._use_json:
            self._log_json(level, message, merged_context)
        else:
            self._log_text(level, message, merged_context)

    def debug(self, message: str, **context: Any) -> None:
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, **context)

    def info(self, message: str, **context: Any) -> None:
        """Log an info message."""
        self.log(LogLevel.INFO, message, **context)

    def warning(self, message: str, **context: Any) -> None:
        """Log a warning message."""
        self.log(LogLevel.WARNING, message, **context)

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        **context: Any,
    ) -> None:
        """Log an error message."""
        if error is not None:
            context["error_type"] = type(error).__name__
            context["error_message"] = str(error)
        self.log(LogLevel.ERROR, message, **context)

    def critical(
        self,
        message: str,
        error: Optional[Exception] = None,
        **context: Any,
    ) -> None:
        """Log a critical message."""
        if error is not None:
            context["error_type"] = type(error).__name__
            context["error_message"] = str(error)
        self.log(LogLevel.CRITICAL, message, **context)

    def with_context(self, **context: Any) -> "ConsoleLogger":
        """Create a child logger with additional context."""
        merged_context = {**self._context, **context}
        return ConsoleLogger(
            name=self._name,
            level=self._level,
            use_colors=self._use_colors,
            use_json=self._use_json,
            context=merged_context,
            trace_id=self._trace_id,
            span_id=self._span_id,
        )

    def with_trace(self, trace_id: str, span_id: str) -> "ConsoleLogger":
        """Create a child logger with trace context."""
        return ConsoleLogger(
            name=self._name,
            level=self._level,
            use_colors=self._use_colors,
            use_json=self._use_json,
            context=self._context,
            trace_id=trace_id,
            span_id=span_id,
        )

    def _log_json(
        self,
        level: LogLevel,
        message: str,
        context: Dict[str, Any],
    ) -> None:
        """Output log as JSON."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value.upper(),
            "logger": self._name,
            "message": message,
        }

        if self._trace_id:
            record["trace_id"] = self._trace_id
        if self._span_id:
            record["span_id"] = self._span_id

        if context:
            record["context"] = self._serialize_context(context)

        with self._lock:
            print(json.dumps(record, ensure_ascii=False), flush=True)

    def _log_text(
        self,
        level: LogLevel,
        message: str,
        context: Dict[str, Any],
    ) -> None:
        """Output log as text."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level_str = level.value.upper().ljust(8)

        if self._use_colors:
            color = COLORS.get(level, "")
            level_str = f"{color}{BOLD}{level_str}{RESET}"

        parts = [f"{timestamp} {level_str} [{self._name}]"]

        if self._trace_id:
            parts.append(f"[{self._trace_id[:8]}]")

        parts.append(message)

        if context:
            ctx_str = " ".join(f"{k}={self._format_value(v)}" for k, v in context.items())
            parts.append(f"| {ctx_str}")

        line = " ".join(parts)

        with self._lock:
            print(line, flush=True)

    def _format_value(self, value: Any) -> str:
        """Format a context value for display."""
        if isinstance(value, str):
            if " " in value or "=" in value:
                return f'"{value}"'
            return value
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _serialize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize context for JSON output."""
        result = {}
        for key, value in context.items():
            try:
                json.dumps(value)
                result[key] = value
            except (TypeError, ValueError):
                result[key] = str(value)
        return result


class ConsoleLoggerFactory(ILoggerFactory):
    """
    Console Logger Factory implementation.

    Creates named console loggers with shared configuration.
    """

    def __init__(
        self,
        level: LogLevel = LogLevel.INFO,
        use_colors: bool = True,
        use_json: bool = False,
    ):
        self._level = level
        self._use_colors = use_colors
        self._use_json = use_json
        self._loggers: Dict[str, ConsoleLogger] = {}
        self._lock = threading.Lock()

    def get_logger(self, name: str) -> ILogger:
        """Get a logger by name."""
        with self._lock:
            if name not in self._loggers:
                self._loggers[name] = ConsoleLogger(
                    name=name,
                    level=self._level,
                    use_colors=self._use_colors,
                    use_json=self._use_json,
                )
            return self._loggers[name]

    def set_level(self, level: LogLevel) -> None:
        """Set the minimum log level."""
        with self._lock:
            self._level = level
            for logger in self._loggers.values():
                logger._level = level

    def get_level(self) -> LogLevel:
        """Get the current minimum log level."""
        return self._level
