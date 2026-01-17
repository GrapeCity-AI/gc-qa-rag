"""
Publishing Executor - Executes publishing tasks.

Manages alias updates for blue-green deployment of indexes.
"""

import logging
from datetime import datetime
from typing import List, Optional

from ai_knowledge_service.abstractions.execution.executor import IPublishingExecutor
from ai_knowledge_service.abstractions.models.tasks import (
    ProcessingError,
    PublishingTask,
    PublishingTaskResult,
    PublishStrategy,
    TaskStatus,
    TaskType,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
from ai_knowledge_service.abstractions.storage.index_storage import IIndexStorage
from ai_knowledge_service.core.executors.base_executor import BaseExecutor


class PublishingExecutor(BaseExecutor[PublishingTask, PublishingTaskResult], IPublishingExecutor):
    """
    Publishing Executor - Manages index publishing and alias updates.

    Responsibilities:
    - Update/switch collection aliases for blue-green deployment
    - Track previous collection for rollback support
    - Simple local-to-local publishing (no remote transfer)
    """

    def __init__(
        self,
        index_storage: IIndexStorage,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the publishing executor.

        Args:
            index_storage: Storage for managing indexes and aliases.
            logger: Optional logger instance.
        """
        super().__init__(logger)
        self._index_storage = index_storage

    @property
    def task_type(self) -> TaskType:
        """Get the task type this executor handles."""
        return TaskType.PUBLISHING

    def validate(self, task: PublishingTask) -> List[str]:
        """Validate publishing task parameters."""
        errors = []

        if not task.target_environment_id:
            errors.append("target_environment_id is required")

        # For now, we require an alias name
        if not task.alias_name:
            errors.append("alias_name is required")

        return errors

    def _execute_impl(
        self,
        task: PublishingTask,
        obs_context: ObservabilityContext,
    ) -> PublishingTaskResult:
        """Execute the publishing task."""
        started_at = datetime.now()
        errors: List[ProcessingError] = []
        alias_applied: Optional[str] = None
        target_collection = ""
        previous_collection: Optional[str] = None
        index_records_published = 0
        raw_files_published = 0

        try:
            # Determine target collection name
            target_collection = self._get_target_collection_name(task)

            # Check if target collection exists
            if not self._index_storage.collection_exists(target_collection):
                raise ValueError(f"Target collection does not exist: {target_collection}")

            # Get current alias target (for rollback support)
            if task.alias_name:
                previous_collection = self._index_storage.get_alias_target(task.alias_name)

            # Apply publishing strategy
            if task.publish_strategy == PublishStrategy.BLUE_GREEN:
                self._apply_blue_green(task, target_collection, previous_collection)
            else:
                self._apply_replace(task, target_collection)

            alias_applied = task.alias_name

            # Get record count from target collection
            collection_info = self._index_storage.get_collection_info(target_collection)
            if collection_info:
                index_records_published = collection_info.records_count

            self._logger.info(
                f"Published collection {target_collection} with alias {alias_applied}"
            )

        except Exception as e:
            self._logger.error(f"Publishing failed: {e}")
            errors.append(
                self._create_processing_error(
                    item_id=task.id,
                    item_name="publish",
                    step="publish",
                    error=e,
                    recoverable=True,
                )
            )

        # Determine status
        if self._is_cancelled(task.id):
            status = TaskStatus.CANCELLED
        elif errors:
            status = TaskStatus.FAILED
        else:
            status = TaskStatus.COMPLETED

        return PublishingTaskResult(
            task_id=task.id,
            status=status,
            total_items=1,
            succeeded_count=1 if status == TaskStatus.COMPLETED else 0,
            failed_count=1 if status == TaskStatus.FAILED else 0,
            skipped_count=0,
            errors=errors,
            started_at=started_at,
            completed_at=datetime.now(),
            target_collection=target_collection,
            alias_applied=alias_applied,
            previous_collection=previous_collection,
            index_records_published=index_records_published,
            raw_files_published=raw_files_published,
        )

    def _get_target_collection_name(self, task: PublishingTask) -> str:
        """Get the target collection name for publishing."""
        # Format: kb_{kb_id}_{version_id}
        kb_id = task.knowledge_base_id[:8]
        version_id = task.knowledge_base_version_id[:8]
        return f"kb_{kb_id}_{version_id}"

    def _apply_blue_green(
        self,
        task: PublishingTask,
        target_collection: str,
        previous_collection: Optional[str],
    ) -> None:
        """Apply blue-green deployment strategy."""
        if not task.alias_name:
            raise ValueError("alias_name required for blue-green deployment")

        if previous_collection and previous_collection != target_collection:
            # Switch from old to new collection
            self._index_storage.switch_alias(
                alias=task.alias_name,
                old_collection=previous_collection,
                new_collection=target_collection,
            )
        else:
            # Create or update alias
            self._index_storage.update_alias(
                alias=task.alias_name,
                collection=target_collection,
            )

        self._logger.info(
            f"Blue-green: {previous_collection} -> {target_collection}"
        )

    def _apply_replace(
        self,
        task: PublishingTask,
        target_collection: str,
    ) -> None:
        """Apply replace strategy (simple alias update)."""
        if task.alias_name:
            self._index_storage.update_alias(
                alias=task.alias_name,
                collection=target_collection,
            )

        self._logger.info(f"Replace: alias -> {target_collection}")

    def _create_cancelled_result(
        self,
        task: PublishingTask,
        started_at: datetime,
    ) -> PublishingTaskResult:
        """Create a result for a cancelled task."""
        return PublishingTaskResult(
            task_id=task.id,
            status=TaskStatus.CANCELLED,
            total_items=0,
            succeeded_count=0,
            failed_count=0,
            skipped_count=0,
            errors=[],
            started_at=started_at,
            completed_at=datetime.now(),
            target_collection="",
            alias_applied=None,
            previous_collection=None,
            index_records_published=0,
            raw_files_published=0,
        )

    def _create_validation_error_result(
        self,
        task: PublishingTask,
        errors: List[str],
        started_at: datetime,
    ) -> PublishingTaskResult:
        """Create a result for validation errors."""
        return PublishingTaskResult(
            task_id=task.id,
            status=TaskStatus.FAILED,
            total_items=0,
            succeeded_count=0,
            failed_count=1,
            skipped_count=0,
            errors=[
                ProcessingError(
                    item_id=task.id,
                    item_name="validation",
                    step="validate",
                    error_type="ValidationError",
                    error_message="; ".join(errors),
                    recoverable=False,
                )
            ],
            started_at=started_at,
            completed_at=datetime.now(),
            target_collection="",
            alias_applied=None,
            previous_collection=None,
            index_records_published=0,
            raw_files_published=0,
        )

    def _create_fatal_error_result(
        self,
        task: PublishingTask,
        error: Exception,
        started_at: datetime,
    ) -> PublishingTaskResult:
        """Create a result for a fatal error."""
        return PublishingTaskResult(
            task_id=task.id,
            status=TaskStatus.FAILED,
            total_items=0,
            succeeded_count=0,
            failed_count=1,
            skipped_count=0,
            errors=[
                self._create_processing_error(
                    item_id=task.id,
                    item_name="execution",
                    step="execute",
                    error=error,
                    recoverable=False,
                )
            ],
            started_at=started_at,
            completed_at=datetime.now(),
            target_collection="",
            alias_applied=None,
            previous_collection=None,
            index_records_published=0,
            raw_files_published=0,
        )
