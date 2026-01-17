"""
Tests for ConsoleLogger and ConsoleLoggerFactory.
"""

import json
import pytest
from io import StringIO
from unittest.mock import patch

from ai_knowledge_service.abstractions.observability.logging import LogLevel
from ai_knowledge_service.implementations.observability.console_logger import (
    ConsoleLogger,
    ConsoleLoggerFactory,
)


class TestConsoleLoggerBasic:
    
    """Basic logging tests."""

    def test_logger_name(self):
        logger = ConsoleLogger(name="test.logger")

        # Logger should store its name
        assert logger._name == "test.logger"

    def test_log_level_filtering(self):
        logger = ConsoleLogger(name="test", level=LogLevel.WARNING)

        with patch("builtins.print") as mock_print:
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")

        # Only warning and error should be printed
        assert mock_print.call_count == 2

    def test_debug_level_logs_all(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG)

        with patch("builtins.print") as mock_print:
            logger.debug("debug")
            logger.info("info")
            logger.warning("warning")
            logger.error("error")
            logger.critical("critical")

        assert mock_print.call_count == 5


class TestConsoleLoggerMethods:
    """Tests for individual logging methods."""

    def test_debug_method(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_colors=False)

        with patch("builtins.print") as mock_print:
            logger.debug("debug message")

        args = mock_print.call_args[0][0]
        assert "DEBUG" in args
        assert "debug message" in args

    def test_info_method(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_colors=False)

        with patch("builtins.print") as mock_print:
            logger.info("info message")

        args = mock_print.call_args[0][0]
        assert "INFO" in args
        assert "info message" in args

    def test_warning_method(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_colors=False)

        with patch("builtins.print") as mock_print:
            logger.warning("warning message")

        args = mock_print.call_args[0][0]
        assert "WARNING" in args
        assert "warning message" in args

    def test_error_method(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_colors=False)

        with patch("builtins.print") as mock_print:
            logger.error("error message")

        args = mock_print.call_args[0][0]
        assert "ERROR" in args
        assert "error message" in args

    def test_critical_method(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_colors=False)

        with patch("builtins.print") as mock_print:
            logger.critical("critical message")

        args = mock_print.call_args[0][0]
        assert "CRITICAL" in args
        assert "critical message" in args

    def test_error_with_exception(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_colors=False)

        with patch("builtins.print") as mock_print:
            try:
                raise ValueError("test error")
            except ValueError as e:
                logger.error("error occurred", error=e)

        args = mock_print.call_args[0][0]
        assert "error occurred" in args
        assert "ValueError" in args
        assert "test error" in args


class TestConsoleLoggerContext:
    """Tests for context handling."""

    def test_log_with_context(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_colors=False)

        with patch("builtins.print") as mock_print:
            logger.info("message", user_id=123, action="login")

        args = mock_print.call_args[0][0]
        assert "user_id=123" in args
        assert "action=login" in args

    def test_with_context_creates_child_logger(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_colors=False)

        child = logger.with_context(request_id="abc123")

        with patch("builtins.print") as mock_print:
            child.info("message")

        args = mock_print.call_args[0][0]
        assert "request_id=abc123" in args

    def test_child_logger_inherits_parent_context(self):
        logger = ConsoleLogger(
            name="test",
            level=LogLevel.DEBUG,
            use_colors=False,
            context={"service": "api"},
        )

        child = logger.with_context(request_id="abc123")

        with patch("builtins.print") as mock_print:
            child.info("message")

        args = mock_print.call_args[0][0]
        assert "service=api" in args
        assert "request_id=abc123" in args


class TestConsoleLoggerTrace:
    """Tests for trace context."""

    def test_with_trace(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_colors=False)

        traced = logger.with_trace(trace_id="trace123", span_id="span456")

        with patch("builtins.print") as mock_print:
            traced.info("message")

        args = mock_print.call_args[0][0]
        assert "trace123" in args

    def test_trace_context_in_json_mode(self):
        logger = ConsoleLogger(
            name="test",
            level=LogLevel.DEBUG,
            use_json=True,
            trace_id="trace123",
            span_id="span456",
        )

        with patch("builtins.print") as mock_print:
            logger.info("message")

        output = mock_print.call_args[0][0]
        data = json.loads(output)

        assert data["trace_id"] == "trace123"
        assert data["span_id"] == "span456"


class TestConsoleLoggerJsonOutput:
    """Tests for JSON output mode."""

    def test_json_output_format(self):
        logger = ConsoleLogger(
            name="test.logger",
            level=LogLevel.DEBUG,
            use_json=True,
        )

        with patch("builtins.print") as mock_print:
            logger.info("test message", user_id=123)

        output = mock_print.call_args[0][0]
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "test message"
        assert "timestamp" in data
        assert data["context"]["user_id"] == 123

    def test_json_serialization_of_complex_types(self):
        logger = ConsoleLogger(name="test", level=LogLevel.DEBUG, use_json=True)

        with patch("builtins.print") as mock_print:
            logger.info("message", data={"nested": {"key": "value"}})

        output = mock_print.call_args[0][0]
        data = json.loads(output)

        assert data["context"]["data"]["nested"]["key"] == "value"


class TestConsoleLoggerFactory:
    """Tests for ConsoleLoggerFactory."""

    def test_get_logger_returns_logger(self):
        factory = ConsoleLoggerFactory()

        logger = factory.get_logger("test.module")

        assert logger is not None

    def test_get_logger_returns_same_instance(self):
        factory = ConsoleLoggerFactory()

        logger1 = factory.get_logger("test.module")
        logger2 = factory.get_logger("test.module")

        assert logger1 is logger2

    def test_get_logger_different_names_different_instances(self):
        factory = ConsoleLoggerFactory()

        logger1 = factory.get_logger("module1")
        logger2 = factory.get_logger("module2")

        assert logger1 is not logger2

    def test_factory_default_level(self):
        factory = ConsoleLoggerFactory(level=LogLevel.WARNING)

        logger = factory.get_logger("test")

        # Should not log INFO
        with patch("builtins.print") as mock_print:
            logger.info("info message")
            logger.warning("warning message")

        assert mock_print.call_count == 1

    def test_set_level_affects_existing_loggers(self):
        factory = ConsoleLoggerFactory(level=LogLevel.INFO)
        logger = factory.get_logger("test")

        factory.set_level(LogLevel.ERROR)

        with patch("builtins.print") as mock_print:
            logger.info("info")
            logger.warning("warning")
            logger.error("error")

        assert mock_print.call_count == 1

    def test_get_level(self):
        factory = ConsoleLoggerFactory(level=LogLevel.WARNING)

        assert factory.get_level() == LogLevel.WARNING

    def test_factory_with_json_output(self):
        factory = ConsoleLoggerFactory(use_json=True)

        logger = factory.get_logger("test")

        with patch("builtins.print") as mock_print:
            logger.info("message")

        output = mock_print.call_args[0][0]
        data = json.loads(output)

        assert "message" in data
