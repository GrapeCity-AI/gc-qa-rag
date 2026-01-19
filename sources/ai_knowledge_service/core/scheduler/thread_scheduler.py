"""
Thread Scheduler - Thread pool-based task scheduler.

Manages a pool of worker threads that process tasks from the queue.
Supports start/stop/pause/resume operations.
"""

import logging
import threading
import time
from typing import Dict, List, Optional

from ai_knowledge_service.abstractions.execution.queue import ITaskQueue
from ai_knowledge_service.abstractions.execution.scheduler import (
    ITaskScheduler,
    SchedulerStatus,
)
from ai_knowledge_service.abstractions.execution.executor import ITaskExecutor
from ai_knowledge_service.abstractions.infrastructure.event_bus import (
    BuildTaskCompletedEvent,
    IEventBus,
    VersionPublishedEvent,
)
from ai_knowledge_service.abstractions.models.tasks import TaskType, TaskStatus


class ThreadScheduler(ITaskScheduler):
    """
    Thread Scheduler - Manages worker threads for task execution.

    This scheduler:
    - Manages a pool of worker threads
    - Distributes tasks to executors based on task type
    - Supports graceful shutdown with timeout
    - Supports pause/resume operations
    """

    def __init__(
        self,
        task_queue: ITaskQueue,
        event_bus: Optional[IEventBus] = None,
        logger: Optional[logging.Logger] = None,
        poll_interval: float = 0.5,
    ):
        """
        Initialize the scheduler.

        Args:
            task_queue: Task queue to pull tasks from.
            event_bus: Optional event bus for publishing task completion events.
            logger: Optional logger instance.
            poll_interval: Interval in seconds between queue polls.
        """
        self._task_queue = task_queue
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._poll_interval = poll_interval

        self._executors: Dict[TaskType, ITaskExecutor] = {}
        self._workers: List[threading.Thread] = []
        self._task_types: Optional[List[TaskType]] = None

        self._running = False
        self._paused = False
        self._shutdown_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially

        self._lock = threading.RLock()
        self._active_tasks = 0

    def register_executor(
        self,
        task_type: TaskType,
        executor: ITaskExecutor,
    ) -> None:
        """Register a task executor for a specific task type."""
        with self._lock:
            if task_type in self._executors:
                raise ValueError(
                    f"Executor already registered for task type: {task_type.value}"
                )
            self._executors[task_type] = executor
            self._logger.info(f"Registered executor for {task_type.value}")

    def unregister_executor(self, task_type: TaskType) -> bool:
        """Unregister a task executor."""
        with self._lock:
            if task_type in self._executors:
                del self._executors[task_type]
                self._logger.info(f"Unregistered executor for {task_type.value}")
                return True
            return False

    def get_executor(self, task_type: TaskType) -> Optional[ITaskExecutor]:
        """Get the registered executor for a task type."""
        with self._lock:
            return self._executors.get(task_type)

    def start(
        self,
        worker_count: int = 1,
        task_types: Optional[List[TaskType]] = None,
    ) -> None:
        """Start the scheduler with the specified number of workers."""
        with self._lock:
            if self._running:
                raise RuntimeError("Scheduler is already running")

            if not self._executors:
                raise ValueError("No executors registered")

            # Determine which task types to process
            self._task_types = task_types
            if task_types:
                # Validate all requested types have executors
                for task_type in task_types:
                    if task_type not in self._executors:
                        raise ValueError(
                            f"No executor registered for task type: {task_type.value}"
                        )

            self._running = True
            self._paused = False
            self._shutdown_event.clear()
            self._pause_event.set()

            # Start worker threads
            for i in range(worker_count):
                worker = threading.Thread(
                    target=self._worker_loop,
                    name=f"TaskWorker-{i}",
                    daemon=True,
                )
                self._workers.append(worker)
                worker.start()

            self._logger.info(
                f"Scheduler started with {worker_count} workers, "
                f"processing task types: {[t.value for t in (task_types or list(self._executors.keys()))]}"
            )

    def stop(self, graceful: bool = True, timeout: float = 30.0) -> None:
        """Stop the scheduler."""
        with self._lock:
            if not self._running:
                return

            self._logger.info(
                f"Stopping scheduler (graceful={graceful}, timeout={timeout}s)"
            )

            # Signal shutdown
            self._shutdown_event.set()
            self._pause_event.set()  # Unpause to allow workers to exit
            self._running = False

        if graceful:
            # Wait for workers to finish
            deadline = time.time() + timeout
            for worker in self._workers:
                remaining = max(0, deadline - time.time())
                worker.join(timeout=remaining)
                if worker.is_alive():
                    self._logger.warning(f"Worker {worker.name} did not stop in time")

        with self._lock:
            self._workers.clear()
            self._paused = False

        self._logger.info("Scheduler stopped")

    def get_status(self) -> SchedulerStatus:
        """Get the current scheduler status."""
        with self._lock:
            pending_tasks = {}
            for task_type in self._executors.keys():
                count = self._task_queue.get_pending_count(task_type)
                pending_tasks[task_type] = count

            return SchedulerStatus(
                is_running=self._running,
                worker_count=len(self._workers),
                active_tasks=self._active_tasks,
                pending_tasks=pending_tasks,
            )

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        with self._lock:
            return self._running

    def wait_for_completion(
        self,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait for all pending and running tasks to complete."""
        deadline = time.time() + timeout if timeout else None

        while True:
            status = self.get_status()
            if status.is_idle:
                return True

            if deadline and time.time() >= deadline:
                return False

            time.sleep(self._poll_interval)

    def pause(self) -> None:
        """Pause the scheduler."""
        with self._lock:
            if self._paused:
                return

            self._paused = True
            self._pause_event.clear()
            self._logger.info("Scheduler paused")

    def resume(self) -> None:
        """Resume a paused scheduler."""
        with self._lock:
            if not self._paused:
                return

            self._paused = False
            self._pause_event.set()
            self._logger.info("Scheduler resumed")

    @property
    def is_paused(self) -> bool:
        """Check if the scheduler is paused."""
        with self._lock:
            return self._paused

    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        thread_name = threading.current_thread().name
        self._logger.debug(f"{thread_name}: Starting")

        while not self._shutdown_event.is_set():
            # Wait if paused
            self._pause_event.wait()

            if self._shutdown_event.is_set():
                break

            # Try to get a task
            task = self._try_get_task()

            if task is None:
                # No task available, wait before polling again
                self._shutdown_event.wait(self._poll_interval)
                continue

            # Process the task
            with self._lock:
                self._active_tasks += 1

            try:
                self._process_task(task)
            finally:
                with self._lock:
                    self._active_tasks -= 1

        self._logger.debug(f"{thread_name}: Stopped")

    def _try_get_task(self):
        """Try to get a task from the queue."""
        with self._lock:
            task_types = self._task_types or list(self._executors.keys())

        for task_type in task_types:
            task = self._task_queue.dequeue(task_type)
            if task is not None:
                return task

        return None

    def _process_task(self, task) -> None:
        """Process a single task."""
        task_type = task.task_type
        thread_name = threading.current_thread().name

        self._logger.info(
            f"{thread_name}: Processing {task_type.value} task {task.id}"
        )

        executor = self._executors.get(task_type)
        if executor is None:
            self._logger.error(
                f"{thread_name}: No executor for {task_type.value}"
            )
            self._task_queue.fail(task.id, f"No executor for {task_type.value}")
            return

        try:
            result = executor.execute(task)

            if result.status == TaskStatus.COMPLETED:
                self._task_queue.complete(task.id, result)
                self._publish_completion_event(task, result)
            else:
                self._task_queue.fail(
                    task.id,
                    f"Task failed with {result.failed_count} errors",
                    result,
                )

            self._logger.info(
                f"{thread_name}: Finished {task_type.value} task {task.id}: "
                f"status={result.status.value}, "
                f"succeeded={result.succeeded_count}/{result.total_items}"
            )

        except Exception as e:
            self._logger.exception(
                f"{thread_name}: Error processing task {task.id}: {e}"
            )
            self._task_queue.fail(task.id, str(e))

    def _publish_completion_event(self, task, result) -> None:
        """Publish task completion event to the event bus."""
        if self._event_bus is None:
            return

        try:
            task_type = task.task_type

            if task_type == TaskType.INDEXING:
                # Publish BuildTaskCompletedEvent for indexing tasks
                event = BuildTaskCompletedEvent(
                    task_id=task.id,
                    knowledge_base_id=task.knowledge_base_id,
                    knowledge_base_version_id=task.knowledge_base_version_id,
                    success=result.status == TaskStatus.COMPLETED,
                    records_indexed=getattr(result, "index_records_count", 0),
                    errors_count=result.failed_count,
                )
                self._event_bus.publish(event)
                self._logger.debug(
                    f"Published BuildTaskCompletedEvent for task {task.id}"
                )

            elif task_type == TaskType.PUBLISHING:
                # Publish VersionPublishedEvent for publishing tasks
                if result.status == TaskStatus.COMPLETED:
                    event = VersionPublishedEvent(
                        knowledge_base_id=task.knowledge_base_id,
                        knowledge_base_version_id=task.knowledge_base_version_id,
                        target_environment_id=task.target_environment_id,
                        target_collection=getattr(result, "target_collection", ""),
                        alias_applied=getattr(result, "alias_applied", "") or "",
                    )
                    self._event_bus.publish(event)
                    self._logger.debug(
                        f"Published VersionPublishedEvent for version {task.knowledge_base_version_id}"
                    )

        except Exception as e:
            self._logger.warning(f"Failed to publish completion event: {e}")
