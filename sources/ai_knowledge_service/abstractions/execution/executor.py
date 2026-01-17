"""
Task Executor interfaces - Defines how tasks are executed.
"""

from typing import Generic, List, Protocol, TypeVar, runtime_checkable

from ai_knowledge_service.abstractions.models.tasks import (
    TaskBase,
    TaskResultBase,
    TaskType,
    IngestionTask,
    IngestionTaskResult,
    IndexingTask,
    IndexingTaskResult,
    PublishingTask,
    PublishingTaskResult,
)

TTask = TypeVar("TTask", bound=TaskBase)
TResult = TypeVar("TResult", bound=TaskResultBase)


@runtime_checkable
class ITaskExecutor(Protocol, Generic[TTask, TResult]):
    """
    Task Executor - Generic interface for executing tasks.

    Executors are responsible for:
    - Validating task parameters
    - Executing the task logic
    - Handling errors with skip-and-continue strategy
    - Returning complete results
    """

    @property
    def task_type(self) -> TaskType:
        """
        Get the task type this executor handles.

        Returns:
            TaskType: The type of task this executor can process.
        """
        ...

    def validate(self, task: TTask) -> List[str]:
        """
        Validate task parameters before execution.

        Args:
            task: The task to validate.

        Returns:
            List[str]: List of validation errors. Empty list means valid.
        """
        ...

    def execute(self, task: TTask) -> TResult:
        """
        Execute the task.

        This method:
        - Is called synchronously by the task scheduler worker
        - Handles errors internally with skip-and-continue
        - Returns complete results including any errors

        Args:
            task: The task to execute.

        Returns:
            TResult: The execution result.
        """
        ...

    def cancel(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: The ID of the task to cancel.

        Returns:
            bool: True if cancellation was successful.
        """
        ...


@runtime_checkable
class IIngestionExecutor(
    ITaskExecutor[IngestionTask, IngestionTaskResult],
    Protocol
):
    """
    Ingestion Executor - Executes ingestion tasks.

    Responsible for:
    - Connecting to data sources
    - Fetching and validating content
    - Storing raw files
    - Tracking ingestion statistics
    """

    pass


@runtime_checkable
class IIndexingExecutor(
    ITaskExecutor[IndexingTask, IndexingTaskResult],
    Protocol
):
    """
    Indexing Executor - Executes indexing tasks.

    Responsible for:
    - Running the indexing pipeline
    - Managing processing steps
    - Building and writing indexes
    - Tracking per-step statistics
    """

    pass


@runtime_checkable
class IPublishingExecutor(
    ITaskExecutor[PublishingTask, PublishingTaskResult],
    Protocol
):
    """
    Publishing Executor - Executes publishing tasks.

    Responsible for:
    - Exporting indexes from local storage
    - Transferring to target environments
    - Managing aliases and rollback
    - Optionally publishing raw files
    """

    pass
