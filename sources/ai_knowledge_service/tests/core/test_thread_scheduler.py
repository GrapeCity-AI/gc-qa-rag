"""
Tests for Thread Scheduler.
"""

import threading
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock

import pytest

from ai_knowledge_service.abstractions.models.tasks import (
    TaskBase,
    TaskResultBase,
    TaskStatus,
    TaskType,
)
from ai_knowledge_service.implementations.infrastructure.memory_queue import MemoryTaskQueue
from ai_knowledge_service.core.scheduler.thread_scheduler import ThreadScheduler


class MockTask(TaskBase):
    """Mock task for testing."""

    def __init__(self, task_id: str, task_type: TaskType = TaskType.INGESTION):
        super().__init__(
            id=task_id,
            task_type=task_type,
            knowledge_base_id="test-kb",
            knowledge_base_version_id="test-version",
        )


class MockResult(TaskResultBase):
    """Mock result for testing."""

    def __init__(self, task_id: str, status: TaskStatus = TaskStatus.COMPLETED):
        super().__init__(
            task_id=task_id,
            task_type=TaskType.INGESTION,
            status=status,
            total_items=1,
            succeeded_count=1 if status == TaskStatus.COMPLETED else 0,
            failed_count=1 if status == TaskStatus.FAILED else 0,
            skipped_count=0,
        )


class TestThreadScheduler:
    """Tests for ThreadScheduler."""

    def test_register_executor(self):
        """Test registering an executor."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue)

        executor = Mock()
        executor.task_type = TaskType.INGESTION

        scheduler.register_executor(TaskType.INGESTION, executor)

        assert scheduler.get_executor(TaskType.INGESTION) == executor

    def test_register_executor_duplicate_raises(self):
        """Test that registering duplicate executor raises error."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue)

        executor = Mock()
        scheduler.register_executor(TaskType.INGESTION, executor)

        with pytest.raises(ValueError, match="already registered"):
            scheduler.register_executor(TaskType.INGESTION, executor)

    def test_unregister_executor(self):
        """Test unregistering an executor."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue)

        executor = Mock()
        scheduler.register_executor(TaskType.INGESTION, executor)

        result = scheduler.unregister_executor(TaskType.INGESTION)

        assert result is True
        assert scheduler.get_executor(TaskType.INGESTION) is None

    def test_unregister_nonexistent_executor(self):
        """Test unregistering a non-existent executor returns False."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue)

        result = scheduler.unregister_executor(TaskType.INGESTION)

        assert result is False

    def test_start_without_executors_raises(self):
        """Test starting without executors raises error."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue)

        with pytest.raises(ValueError, match="No executors registered"):
            scheduler.start()

    def test_start_already_running_raises(self):
        """Test starting an already running scheduler raises error."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue)

        executor = Mock()
        executor.task_type = TaskType.INGESTION
        scheduler.register_executor(TaskType.INGESTION, executor)

        scheduler.start()
        try:
            with pytest.raises(RuntimeError, match="already running"):
                scheduler.start()
        finally:
            scheduler.stop(graceful=False)

    def test_stop_scheduler(self):
        """Test stopping the scheduler."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue)

        executor = Mock()
        executor.task_type = TaskType.INGESTION
        scheduler.register_executor(TaskType.INGESTION, executor)

        scheduler.start(worker_count=1)
        assert scheduler.is_running

        scheduler.stop(graceful=True, timeout=5.0)
        assert not scheduler.is_running

    def test_get_status(self):
        """Test getting scheduler status."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue)

        executor = Mock()
        scheduler.register_executor(TaskType.INGESTION, executor)

        scheduler.start(worker_count=2)
        try:
            status = scheduler.get_status()

            assert status.is_running
            assert status.worker_count == 2
            assert status.active_tasks == 0
        finally:
            scheduler.stop(graceful=False)

    def test_pause_resume(self):
        """Test pausing and resuming the scheduler."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue)

        executor = Mock()
        scheduler.register_executor(TaskType.INGESTION, executor)

        scheduler.start()
        try:
            assert not scheduler.is_paused

            scheduler.pause()
            assert scheduler.is_paused

            scheduler.resume()
            assert not scheduler.is_paused
        finally:
            scheduler.stop(graceful=False)

    def test_process_task(self):
        """Test that scheduler processes tasks."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue, poll_interval=0.1)

        # Create mock executor
        executor = Mock()
        executor.task_type = TaskType.INGESTION
        executor.execute = Mock(
            return_value=MockResult("task-1", TaskStatus.COMPLETED)
        )
        scheduler.register_executor(TaskType.INGESTION, executor)

        # Enqueue task
        task = MockTask("task-1", TaskType.INGESTION)
        queue.enqueue(task)

        # Start scheduler and wait for task to be processed
        scheduler.start(worker_count=1)
        try:
            # Wait for task to complete
            time.sleep(0.5)

            # Check executor was called
            executor.execute.assert_called_once()

            # Check task is completed in queue
            assert queue.get_task_status("task-1") == TaskStatus.COMPLETED

        finally:
            scheduler.stop(graceful=False)

    def test_wait_for_completion(self):
        """Test waiting for task completion."""
        queue = MemoryTaskQueue()
        scheduler = ThreadScheduler(queue, poll_interval=0.1)

        executor = Mock()
        executor.task_type = TaskType.INGESTION
        executor.execute = Mock(
            return_value=MockResult("task-1", TaskStatus.COMPLETED)
        )
        scheduler.register_executor(TaskType.INGESTION, executor)

        task = MockTask("task-1", TaskType.INGESTION)
        queue.enqueue(task)

        scheduler.start(worker_count=1)
        try:
            completed = scheduler.wait_for_completion(timeout=5.0)
            assert completed
        finally:
            scheduler.stop(graceful=False)
