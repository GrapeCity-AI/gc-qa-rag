"""
Tests for MemoryTaskQueue - In-memory task queue implementation.
"""

import pytest
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ai_knowledge_service.abstractions.models.tasks import (
    TaskType,
    TaskStatus,
    IngestionTask,
    IngestionTaskResult,
)
from ai_knowledge_service.implementations.infrastructure.memory_queue import (
    MemoryTaskQueue,
)


def create_test_task(
    task_id: str = "task-1",
    knowledge_base_id: str = "kb-1",
    version_id: str = "v-1",
    priority: int = 0,
    source_config: dict = None,
) -> IngestionTask:
    """Create a test ingestion task."""
    return IngestionTask(
        id=task_id,
        knowledge_base_id=knowledge_base_id,
        knowledge_base_version_id=version_id,
        priority=priority,
        source_config=source_config or {"type": "test"},
    )


def create_test_result(
    task_id: str = "task-1",
    status: TaskStatus = TaskStatus.COMPLETED,
) -> IngestionTaskResult:
    """Create a test ingestion task result."""
    return IngestionTaskResult(
        task_id=task_id,
        status=status,
        total_items=10,
        succeeded_count=10,
        failed_count=0,
        skipped_count=0,
    )


class TestMemoryTaskQueueEnqueue:
    """Tests for task enqueueing."""

    def test_enqueue_returns_task_id(self):
        queue = MemoryTaskQueue()
        task = create_test_task()

        task_id = queue.enqueue(task)

        assert task_id == task.id

    def test_enqueue_sets_pending_status(self):
        queue = MemoryTaskQueue()
        task = create_test_task()

        queue.enqueue(task)

        assert queue.get_task_status(task.id) == TaskStatus.PENDING

    def test_enqueue_with_delay(self):
        queue = MemoryTaskQueue()
        task = create_test_task()

        queue.enqueue(task, delay=timedelta(hours=1))

        # Task should be pending but not dequeue-able
        assert queue.get_task_status(task.id) == TaskStatus.PENDING
        assert queue.dequeue(TaskType.INGESTION) is None

    def test_get_task_after_enqueue(self):
        queue = MemoryTaskQueue()
        task = create_test_task()

        queue.enqueue(task)

        retrieved = queue.get_task(task.id)

        assert retrieved is not None
        assert retrieved.id == task.id


class TestMemoryTaskQueueDequeue:
    """Tests for task dequeueing."""

    def test_dequeue_returns_task(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        queue.enqueue(task)

        dequeued = queue.dequeue(TaskType.INGESTION)

        assert dequeued is not None
        assert dequeued.id == task.id

    def test_dequeue_sets_running_status(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        queue.enqueue(task)

        queue.dequeue(TaskType.INGESTION)

        assert queue.get_task_status(task.id) == TaskStatus.RUNNING

    def test_dequeue_sets_started_at(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        queue.enqueue(task)

        dequeued = queue.dequeue(TaskType.INGESTION)

        assert dequeued.started_at is not None

    def test_dequeue_empty_queue_returns_none(self):
        queue = MemoryTaskQueue()

        result = queue.dequeue(TaskType.INGESTION)

        assert result is None

    def test_dequeue_wrong_type_returns_none(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        queue.enqueue(task)

        result = queue.dequeue(TaskType.INDEXING)

        assert result is None

    def test_dequeue_respects_priority(self):
        queue = MemoryTaskQueue()

        low_priority = create_test_task(task_id="low", priority=1)
        high_priority = create_test_task(task_id="high", priority=10)

        queue.enqueue(low_priority)
        queue.enqueue(high_priority)

        first = queue.dequeue(TaskType.INGESTION)
        second = queue.dequeue(TaskType.INGESTION)

        assert first.id == "high"
        assert second.id == "low"


class TestMemoryTaskQueueComplete:
    """Tests for task completion."""

    def test_complete_sets_completed_status(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        queue.enqueue(task)
        queue.dequeue(TaskType.INGESTION)

        result = create_test_result(task.id)
        queue.complete(task.id, result)

        assert queue.get_task_status(task.id) == TaskStatus.COMPLETED

    def test_complete_stores_result(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        queue.enqueue(task)
        queue.dequeue(TaskType.INGESTION)

        result = create_test_result(task.id)
        queue.complete(task.id, result)

        stored_result = queue.get_result(task.id)

        assert stored_result is not None
        assert stored_result.task_id == task.id

    def test_complete_nonexistent_task_raises_error(self):
        queue = MemoryTaskQueue()

        with pytest.raises(KeyError):
            queue.complete("nonexistent", create_test_result("nonexistent"))


class TestMemoryTaskQueueFail:
    """Tests for task failure."""

    def test_fail_with_retries_requeues_task(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        task.max_retries = 3
        queue.enqueue(task)
        queue.dequeue(TaskType.INGESTION)

        queue.fail(task.id, "Test error")

        assert queue.get_task_status(task.id) == TaskStatus.PENDING
        assert task.retry_count == 1

    def test_fail_exhausted_retries_sets_failed_status(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        task.max_retries = 0
        queue.enqueue(task)
        queue.dequeue(TaskType.INGESTION)

        queue.fail(task.id, "Test error")

        assert queue.get_task_status(task.id) == TaskStatus.FAILED

    def test_fail_nonexistent_task_raises_error(self):
        queue = MemoryTaskQueue()

        with pytest.raises(KeyError):
            queue.fail("nonexistent", "Test error")


class TestMemoryTaskQueueCancel:
    """Tests for task cancellation."""

    def test_cancel_pending_task(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        queue.enqueue(task)

        result = queue.cancel(task.id)

        assert result is True
        assert queue.get_task_status(task.id) == TaskStatus.CANCELLED

    def test_cancel_running_task_fails(self):
        queue = MemoryTaskQueue()
        task = create_test_task()
        queue.enqueue(task)
        queue.dequeue(TaskType.INGESTION)

        result = queue.cancel(task.id)

        assert result is False
        assert queue.get_task_status(task.id) == TaskStatus.RUNNING

    def test_cancel_nonexistent_task_returns_false(self):
        queue = MemoryTaskQueue()

        result = queue.cancel("nonexistent")

        assert result is False


class TestMemoryTaskQueueListTasks:
    """Tests for task listing."""

    def test_list_all_tasks(self):
        queue = MemoryTaskQueue()

        for i in range(5):
            queue.enqueue(create_test_task(task_id=f"task-{i}"))

        tasks = queue.list_tasks()

        assert len(tasks) == 5

    def test_list_tasks_by_type(self):
        queue = MemoryTaskQueue()

        for i in range(3):
            queue.enqueue(create_test_task(task_id=f"task-{i}"))

        tasks = queue.list_tasks(task_type=TaskType.INGESTION)

        assert len(tasks) == 3

    def test_list_tasks_by_status(self):
        queue = MemoryTaskQueue()

        for i in range(3):
            task = create_test_task(task_id=f"task-{i}")
            queue.enqueue(task)

        queue.dequeue(TaskType.INGESTION)

        pending_tasks = queue.list_tasks(status=TaskStatus.PENDING)
        running_tasks = queue.list_tasks(status=TaskStatus.RUNNING)

        assert len(pending_tasks) == 2
        assert len(running_tasks) == 1

    def test_list_tasks_by_knowledge_base(self):
        queue = MemoryTaskQueue()

        queue.enqueue(create_test_task(task_id="t1", knowledge_base_id="kb-1"))
        queue.enqueue(create_test_task(task_id="t2", knowledge_base_id="kb-1"))
        queue.enqueue(create_test_task(task_id="t3", knowledge_base_id="kb-2"))

        tasks = queue.list_tasks(knowledge_base_id="kb-1")

        assert len(tasks) == 2

    def test_list_tasks_with_limit_and_offset(self):
        queue = MemoryTaskQueue()

        for i in range(10):
            queue.enqueue(create_test_task(task_id=f"task-{i}"))

        tasks = queue.list_tasks(limit=3, offset=2)

        assert len(tasks) == 3


class TestMemoryTaskQueueCounts:
    """Tests for task counting."""

    def test_get_pending_count(self):
        queue = MemoryTaskQueue()

        for i in range(5):
            queue.enqueue(create_test_task(task_id=f"task-{i}"))

        queue.dequeue(TaskType.INGESTION)

        assert queue.get_pending_count() == 4

    def test_get_pending_count_by_type(self):
        queue = MemoryTaskQueue()

        for i in range(3):
            queue.enqueue(create_test_task(task_id=f"task-{i}"))

        count = queue.get_pending_count(TaskType.INGESTION)

        assert count == 3

    def test_get_running_count(self):
        queue = MemoryTaskQueue()

        for i in range(3):
            task = create_test_task(task_id=f"task-{i}")
            queue.enqueue(task)
            queue.dequeue(TaskType.INGESTION)

        assert queue.get_running_count() == 3


class TestMemoryTaskQueueClearCompleted:
    """Tests for clearing completed tasks."""

    def test_clear_completed_tasks(self):
        queue = MemoryTaskQueue()

        task = create_test_task()
        queue.enqueue(task)
        queue.dequeue(TaskType.INGESTION)
        queue.complete(task.id, create_test_result(task.id))

        count = queue.clear_completed()

        assert count == 1
        assert queue.get_task(task.id) is None

    def test_clear_completed_with_age_filter(self):
        queue = MemoryTaskQueue()

        task = create_test_task()
        queue.enqueue(task)
        queue.dequeue(TaskType.INGESTION)
        queue.complete(task.id, create_test_result(task.id))

        # Task completed just now, so filtering by 1 hour should not remove it
        count = queue.clear_completed(older_than=timedelta(hours=1))

        assert count == 0
        assert queue.get_task(task.id) is not None

    def test_clear_keeps_pending_tasks(self):
        queue = MemoryTaskQueue()

        pending_task = create_test_task(task_id="pending")
        completed_task = create_test_task(task_id="completed")

        queue.enqueue(pending_task)
        queue.enqueue(completed_task)
        queue.dequeue(TaskType.INGESTION)
        queue.complete(completed_task.id, create_test_result(completed_task.id))

        queue.clear_completed()

        assert queue.get_task("pending") is not None
        assert queue.get_task("completed") is None
