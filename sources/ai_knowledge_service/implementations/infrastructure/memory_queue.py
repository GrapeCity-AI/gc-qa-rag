"""
Memory Queue - In-memory task queue implementation.

This implementation provides:
- Priority-based task ordering
- Delayed task scheduling
- Automatic retry handling
- Task state management
- Thread-safe operations

Note: This is for development/testing only. For production, use Redis-based queue.
"""

import threading
import heapq
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ai_knowledge_service.abstractions.execution.queue import ITaskQueue
from ai_knowledge_service.abstractions.models.tasks import (
    TaskBase,
    TaskResultBase,
    TaskType,
    TaskStatus,
)


@dataclass(order=True)
class PriorityItem:
    """Wrapper for priority queue ordering."""

    priority: int
    available_at: datetime
    task: TaskBase = field(compare=False)


class MemoryTaskQueue(ITaskQueue):
    """
    In-memory task queue implementation.

    Tasks are stored in memory with priority-based ordering.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        self._pending: List[PriorityItem] = []  # Min-heap
        self._tasks: Dict[str, TaskBase] = {}  # All tasks by ID
        self._results: Dict[str, TaskResultBase] = {}  # Results by task ID
        self._status: Dict[str, TaskStatus] = {}  # Task status
        self._lock = threading.RLock()

    def enqueue(
        self,
        task: TaskBase,
        delay: Optional[timedelta] = None,
    ) -> str:
        """Enqueue a task for processing."""
        with self._lock:
            task_id = task.id
            available_at = datetime.now()
            if delay:
                available_at = available_at + delay

            # Use negative priority for max-heap behavior (higher priority first)
            item = PriorityItem(
                priority=-task.priority,
                available_at=available_at,
                task=task,
            )

            heapq.heappush(self._pending, item)
            self._tasks[task_id] = task
            self._status[task_id] = TaskStatus.PENDING

            return task_id

    def dequeue(self, task_type: TaskType) -> Optional[TaskBase]:
        """Dequeue a task for processing."""
        with self._lock:
            now = datetime.now()
            candidates: List[PriorityItem] = []
            selected: Optional[PriorityItem] = None

            while self._pending:
                item = heapq.heappop(self._pending)

                if item.available_at > now:
                    candidates.append(item)
                    continue

                if self._status.get(item.task.id) != TaskStatus.PENDING:
                    continue

                if item.task.task_type != task_type:
                    candidates.append(item)
                    continue

                selected = item
                break

            for item in candidates:
                heapq.heappush(self._pending, item)

            if selected is None:
                return None

            task = selected.task
            task.started_at = now
            self._status[task.id] = TaskStatus.RUNNING

            return task

    def complete(
        self,
        task_id: str,
        result: TaskResultBase,
    ) -> None:
        """Mark a task as completed and store its result."""
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Task not found: {task_id}")

            task = self._tasks[task_id]
            task.completed_at = datetime.now()

            self._status[task_id] = TaskStatus.COMPLETED
            self._results[task_id] = result

    def fail(
        self,
        task_id: str,
        error: str,
        result: Optional[TaskResultBase] = None,
    ) -> None:
        """Mark a task as failed."""
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Task not found: {task_id}")

            task = self._tasks[task_id]

            if task.can_retry:
                task.retry_count += 1
                task.started_at = None

                retry_delay = timedelta(seconds=2 ** task.retry_count)
                available_at = datetime.now() + retry_delay

                item = PriorityItem(
                    priority=-task.priority,
                    available_at=available_at,
                    task=task,
                )
                heapq.heappush(self._pending, item)
                self._status[task_id] = TaskStatus.PENDING
            else:
                task.completed_at = datetime.now()
                self._status[task_id] = TaskStatus.FAILED

                if result:
                    self._results[task_id] = result

    def get_task(self, task_id: str) -> Optional[TaskBase]:
        """Get a task by ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def get_result(self, task_id: str) -> Optional[TaskResultBase]:
        """Get the result of a completed task."""
        with self._lock:
            return self._results.get(task_id)

    def list_tasks(
        self,
        task_type: Optional[TaskType] = None,
        status: Optional[TaskStatus] = None,
        knowledge_base_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TaskBase]:
        """List tasks with optional filters."""
        with self._lock:
            tasks = list(self._tasks.values())

            if task_type is not None:
                tasks = [t for t in tasks if t.task_type == task_type]

            if status is not None:
                tasks = [t for t in tasks if self._status.get(t.id) == status]

            if knowledge_base_id is not None:
                tasks = [t for t in tasks if t.knowledge_base_id == knowledge_base_id]

            tasks.sort(key=lambda t: t.created_at, reverse=True)

            return tasks[offset : offset + limit]

    def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        with self._lock:
            if task_id not in self._tasks:
                return False

            if self._status.get(task_id) != TaskStatus.PENDING:
                return False

            self._status[task_id] = TaskStatus.CANCELLED
            return True

    def get_pending_count(self, task_type: Optional[TaskType] = None) -> int:
        """Get the number of pending tasks."""
        with self._lock:
            count = 0
            for task_id, status in self._status.items():
                if status != TaskStatus.PENDING:
                    continue
                if task_type is not None:
                    task = self._tasks.get(task_id)
                    if task and task.task_type != task_type:
                        continue
                count += 1
            return count

    def get_running_count(self, task_type: Optional[TaskType] = None) -> int:
        """Get the number of running tasks."""
        with self._lock:
            count = 0
            for task_id, status in self._status.items():
                if status != TaskStatus.RUNNING:
                    continue
                if task_type is not None:
                    task = self._tasks.get(task_id)
                    if task and task.task_type != task_type:
                        continue
                count += 1
            return count

    def clear_completed(
        self,
        older_than: Optional[timedelta] = None,
    ) -> int:
        """Clear completed tasks and their results."""
        with self._lock:
            now = datetime.now()
            to_remove: List[str] = []

            for task_id, status in self._status.items():
                if status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    continue

                task = self._tasks.get(task_id)
                if task is None:
                    continue

                if older_than is not None:
                    completed_at = task.completed_at or task.created_at
                    if now - completed_at < older_than:
                        continue

                to_remove.append(task_id)

            for task_id in to_remove:
                del self._tasks[task_id]
                del self._status[task_id]
                self._results.pop(task_id, None)

            return len(to_remove)

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task."""
        with self._lock:
            return self._status.get(task_id)
