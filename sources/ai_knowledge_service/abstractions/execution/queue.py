"""
Task Queue interface - Defines how tasks are queued and managed.
"""

from datetime import timedelta
from typing import List, Optional, Protocol, runtime_checkable

from ai_knowledge_service.abstractions.models.tasks import (
    TaskBase,
    TaskResultBase,
    TaskType,
    TaskStatus,
)


@runtime_checkable
class ITaskQueue(Protocol):
    """
    Task Queue - Interface for task queuing and management.

    The task queue is responsible for:
    - Enqueueing tasks with priority and delay support
    - Dequeueing tasks for processing
    - Managing task lifecycle (complete, fail, cancel)
    - Storing task results
    - Automatic retry handling
    """

    def enqueue(
        self,
        task: TaskBase,
        delay: Optional[timedelta] = None,
    ) -> str:
        """
        Enqueue a task for processing.

        Tasks are processed in priority order (higher priority first).
        If delay is specified, the task won't be available until after the delay.

        Args:
            task: The task to enqueue.
            delay: Optional delay before the task becomes available.

        Returns:
            str: The task ID.
        """
        ...

    def dequeue(self, task_type: TaskType) -> Optional[TaskBase]:
        """
        Dequeue a task for processing.

        Retrieves the highest priority pending task of the specified type.
        The task is marked as RUNNING and won't be returned again until
        completed or failed.

        Args:
            task_type: The type of task to dequeue.

        Returns:
            Optional[TaskBase]: The task, or None if no tasks are available.
        """
        ...

    def complete(
        self,
        task_id: str,
        result: TaskResultBase,
    ) -> None:
        """
        Mark a task as completed and store its result.

        Args:
            task_id: The ID of the task.
            result: The task execution result.
        """
        ...

    def fail(
        self,
        task_id: str,
        error: str,
        result: Optional[TaskResultBase] = None,
    ) -> None:
        """
        Mark a task as failed.

        If the task's retry_count < max_retries, it will be automatically
        re-enqueued with incremented retry_count.

        Args:
            task_id: The ID of the task.
            error: Error message describing the failure.
            result: Optional partial result from the failed execution.
        """
        ...

    def get_task(self, task_id: str) -> Optional[TaskBase]:
        """
        Get a task by ID.

        Args:
            task_id: The ID of the task.

        Returns:
            Optional[TaskBase]: The task, or None if not found.
        """
        ...

    def get_result(self, task_id: str) -> Optional[TaskResultBase]:
        """
        Get the result of a completed task.

        Args:
            task_id: The ID of the task.

        Returns:
            Optional[TaskResultBase]: The result, or None if not available.
        """
        ...

    def list_tasks(
        self,
        task_type: Optional[TaskType] = None,
        status: Optional[TaskStatus] = None,
        knowledge_base_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TaskBase]:
        """
        List tasks with optional filters.

        Args:
            task_type: Filter by task type.
            status: Filter by task status.
            knowledge_base_id: Filter by knowledge base.
            limit: Maximum number of tasks to return.
            offset: Number of tasks to skip.

        Returns:
            List[TaskBase]: List of tasks matching the filters.
        """
        ...

    def cancel(self, task_id: str) -> bool:
        """
        Cancel a pending task.

        Only tasks in PENDING status can be cancelled.

        Args:
            task_id: The ID of the task to cancel.

        Returns:
            bool: True if the task was cancelled, False otherwise.
        """
        ...

    def get_pending_count(self, task_type: Optional[TaskType] = None) -> int:
        """
        Get the number of pending tasks.

        Args:
            task_type: Optional filter by task type.

        Returns:
            int: Number of pending tasks.
        """
        ...

    def get_running_count(self, task_type: Optional[TaskType] = None) -> int:
        """
        Get the number of running tasks.

        Args:
            task_type: Optional filter by task type.

        Returns:
            int: Number of running tasks.
        """
        ...

    def clear_completed(
        self,
        older_than: Optional[timedelta] = None,
    ) -> int:
        """
        Clear completed tasks and their results.

        Args:
            older_than: Only clear tasks older than this duration.

        Returns:
            int: Number of tasks cleared.
        """
        ...
