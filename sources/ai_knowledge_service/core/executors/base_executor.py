"""
Base Executor - Abstract base class for task executors.

Provides common functionality for all executors including:
- ObservabilityContext creation
- Unified error handling
- Logging integration
"""

import logging
import threading
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Generic, List, Optional, Set, TypeVar

from ai_knowledge_service.abstractions.execution.executor import ITaskExecutor
from ai_knowledge_service.abstractions.models.tasks import (
    ProcessingError,
    TaskBase,
    TaskResultBase,
    TaskStatus,
    TaskType,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext


TTask = TypeVar("TTask", bound=TaskBase)
TResult = TypeVar("TResult", bound=TaskResultBase)


class BaseExecutor(ABC, Generic[TTask, TResult]):
    """
    Base Executor - Abstract base class providing common executor functionality.

    Provides:
    - ObservabilityContext creation for tracing and metrics
    - Unified error handling with skip-and-continue support
    - Thread-safe cancellation tracking
    - Logging integration
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the executor.

        Args:
            logger: Optional logger instance. If not provided, creates one
                   using the class name.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._running_tasks: Set[str] = set()
        self._cancelled_tasks: Set[str] = set()
        self._lock = threading.RLock()

    @property
    @abstractmethod
    def task_type(self) -> TaskType:
        """Get the task type this executor handles."""
        ...

    @abstractmethod
    def validate(self, task: TTask) -> List[str]:
        """
        Validate task parameters before execution.

        Args:
            task: The task to validate.

        Returns:
            List of validation error messages. Empty list means valid.
        """
        ...

    @abstractmethod
    def _execute_impl(
        self,
        task: TTask,
        obs_context: ObservabilityContext,
    ) -> TResult:
        """
        Execute the task (implementation).

        This method should be implemented by subclasses to perform
        the actual task execution logic.

        Args:
            task: The task to execute.
            obs_context: Observability context for tracing/metrics.

        Returns:
            The execution result.
        """
        ...

    def execute(self, task: TTask) -> TResult:
        """
        Execute the task with error handling and observability.

        This method:
        - Creates an observability context
        - Handles errors with skip-and-continue strategy
        - Tracks running tasks for cancellation support
        - Logs execution progress

        Args:
            task: The task to execute.

        Returns:
            The execution result.
        """
        # Mark task as running
        with self._lock:
            self._running_tasks.add(task.id)

        # Create observability context
        obs_context = self._create_observability_context(task)

        self._logger.info(
            f"Starting {self.task_type.value} task {task.id}",
            extra=obs_context.to_log_context(),
        )

        started_at = datetime.now()

        try:
            # Check for cancellation before starting
            if self._is_cancelled(task.id):
                return self._create_cancelled_result(task, started_at)

            # Validate task
            validation_errors = self.validate(task)
            if validation_errors:
                return self._create_validation_error_result(
                    task, validation_errors, started_at
                )

            # Execute the task
            result = self._execute_impl(task, obs_context)

            self._logger.info(
                f"Completed {self.task_type.value} task {task.id}: "
                f"{result.succeeded_count}/{result.total_items} succeeded",
                extra=obs_context.to_log_context(),
            )

            return result

        except Exception as e:
            self._logger.error(
                f"Fatal error in {self.task_type.value} task {task.id}: {e}",
                extra=obs_context.to_log_context(),
                exc_info=True,
            )
            return self._create_fatal_error_result(task, e, started_at)

        finally:
            # Mark task as no longer running
            with self._lock:
                self._running_tasks.discard(task.id)
                self._cancelled_tasks.discard(task.id)

    def cancel(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: The ID of the task to cancel.

        Returns:
            True if the task was running and marked for cancellation.
        """
        with self._lock:
            if task_id in self._running_tasks:
                self._cancelled_tasks.add(task_id)
                self._logger.info(f"Marked task {task_id} for cancellation")
                return True
            return False

    def _is_cancelled(self, task_id: str) -> bool:
        """Check if a task has been cancelled."""
        with self._lock:
            return task_id in self._cancelled_tasks

    def _create_observability_context(self, task: TTask) -> ObservabilityContext:
        """
        Create an observability context for the task.

        Args:
            task: The task being executed.

        Returns:
            ObservabilityContext for tracing and metrics.
        """
        return ObservabilityContext.create(
            task_id=task.id,
            task_type=task.task_type,
            knowledge_base_id=task.knowledge_base_id,
            knowledge_base_version_id=task.knowledge_base_version_id,
        )

    def _create_processing_error(
        self,
        item_id: str,
        item_name: str,
        step: str,
        error: Exception,
        recoverable: bool = True,
    ) -> ProcessingError:
        """
        Create a processing error record.

        Args:
            item_id: ID of the failed item.
            item_name: Human-readable name.
            step: Processing step where error occurred.
            error: The exception that occurred.
            recoverable: Whether the error can be retried.

        Returns:
            ProcessingError record.
        """
        return ProcessingError(
            item_id=item_id,
            item_name=item_name,
            step=step,
            error_type=type(error).__name__,
            error_message=str(error),
            stacktrace=traceback.format_exc(),
            recoverable=recoverable,
        )

    @abstractmethod
    def _create_cancelled_result(
        self,
        task: TTask,
        started_at: datetime,
    ) -> TResult:
        """Create a result for a cancelled task."""
        ...

    @abstractmethod
    def _create_validation_error_result(
        self,
        task: TTask,
        errors: List[str],
        started_at: datetime,
    ) -> TResult:
        """Create a result for a task with validation errors."""
        ...

    @abstractmethod
    def _create_fatal_error_result(
        self,
        task: TTask,
        error: Exception,
        started_at: datetime,
    ) -> TResult:
        """Create a result for a task that failed with a fatal error."""
        ...
