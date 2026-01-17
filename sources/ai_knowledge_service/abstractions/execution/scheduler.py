"""
Task Scheduler interface - Defines how tasks are scheduled and workers managed.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Protocol, runtime_checkable

from ai_knowledge_service.abstractions.models.tasks import TaskType
from ai_knowledge_service.abstractions.execution.executor import ITaskExecutor


@dataclass
class SchedulerStatus:
    """Status information for the task scheduler."""

    is_running: bool
    worker_count: int
    active_tasks: int
    pending_tasks: Dict[TaskType, int] = field(default_factory=dict)

    @property
    def total_pending(self) -> int:
        """Get total number of pending tasks across all types."""
        return sum(self.pending_tasks.values())

    @property
    def is_idle(self) -> bool:
        """Check if the scheduler is idle (no active or pending tasks)."""
        return self.active_tasks == 0 and self.total_pending == 0


@runtime_checkable
class ITaskScheduler(Protocol):
    """
    Task Scheduler - Interface for managing task execution workers.

    The scheduler is responsible for:
    - Registering task executors for each task type
    - Managing worker threads/processes
    - Coordinating task distribution
    - Providing status information
    """

    def register_executor(
        self,
        task_type: TaskType,
        executor: ITaskExecutor,
    ) -> None:
        """
        Register a task executor for a specific task type.

        Each task type can only have one registered executor.

        Args:
            task_type: The type of task the executor handles.
            executor: The executor instance.

        Raises:
            ValueError: If an executor is already registered for the task type.
        """
        ...

    def unregister_executor(self, task_type: TaskType) -> bool:
        """
        Unregister a task executor.

        Args:
            task_type: The type of task to unregister.

        Returns:
            bool: True if an executor was unregistered.
        """
        ...

    def get_executor(self, task_type: TaskType) -> Optional[ITaskExecutor]:
        """
        Get the registered executor for a task type.

        Args:
            task_type: The type of task.

        Returns:
            Optional[ITaskExecutor]: The executor, or None if not registered.
        """
        ...

    def start(
        self,
        worker_count: int = 1,
        task_types: Optional[list[TaskType]] = None,
    ) -> None:
        """
        Start the scheduler with the specified number of workers.

        Args:
            worker_count: Number of worker threads/processes to start.
            task_types: Optional list of task types to process.
                       If None, all registered types are processed.

        Raises:
            RuntimeError: If the scheduler is already running.
            ValueError: If no executors are registered.
        """
        ...

    def stop(self, graceful: bool = True, timeout: float = 30.0) -> None:
        """
        Stop the scheduler.

        Args:
            graceful: If True, wait for current tasks to complete.
                     If False, stop immediately.
            timeout: Maximum time to wait for graceful shutdown (seconds).
        """
        ...

    def get_status(self) -> SchedulerStatus:
        """
        Get the current scheduler status.

        Returns:
            SchedulerStatus: Current status information.
        """
        ...

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        ...

    def wait_for_completion(
        self,
        timeout: Optional[float] = None,
    ) -> bool:
        """
        Wait for all pending and running tasks to complete.

        Args:
            timeout: Maximum time to wait (seconds). None for no timeout.

        Returns:
            bool: True if all tasks completed, False if timeout reached.
        """
        ...

    def pause(self) -> None:
        """
        Pause the scheduler.

        Workers will finish current tasks but won't pick up new ones.
        """
        ...

    def resume(self) -> None:
        """
        Resume a paused scheduler.
        """
        ...

    @property
    def is_paused(self) -> bool:
        """Check if the scheduler is paused."""
        ...
