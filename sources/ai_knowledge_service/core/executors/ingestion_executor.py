"""
Ingestion Executor - Executes ingestion tasks.

Coordinates between source connectors and raw file storage to ingest
data from external sources.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from ai_knowledge_service.abstractions.execution.executor import IIngestionExecutor
from ai_knowledge_service.abstractions.models.tasks import (
    IngestionTask,
    IngestionTaskResult,
    ProcessingError,
    TaskStatus,
    TaskType,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
from ai_knowledge_service.abstractions.pipelines.source import (
    ISourceConnector,
    SourceConfig,
)
from ai_knowledge_service.abstractions.storage.raw_file_storage import IRawFileStorage
from ai_knowledge_service.core.executors.base_executor import BaseExecutor


class IngestionExecutor(BaseExecutor[IngestionTask, IngestionTaskResult], IIngestionExecutor):
    """
    Ingestion Executor - Coordinates data ingestion from sources.

    Responsibilities:
    - Connect to data sources using appropriate connectors
    - Fetch and validate content
    - Store raw files with deduplication
    - Track ingestion statistics
    """

    def __init__(
        self,
        raw_file_storage: IRawFileStorage,
        connectors: Dict[str, ISourceConnector],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the ingestion executor.

        Args:
            raw_file_storage: Storage for raw files.
            connectors: Mapping of connector type to connector instance.
            logger: Optional logger instance.
        """
        super().__init__(logger)
        self._storage = raw_file_storage
        self._connectors = connectors

    @property
    def task_type(self) -> TaskType:
        """Get the task type this executor handles."""
        return TaskType.INGESTION

    def validate(self, task: IngestionTask) -> List[str]:
        """Validate ingestion task parameters."""
        errors = []

        if not task.source_config:
            errors.append("source_config is required")
            return errors

        connector_type = task.source_config.get("connector_type")
        if not connector_type:
            errors.append("source_config.connector_type is required")
        elif connector_type not in self._connectors:
            errors.append(f"Unknown connector type: {connector_type}")

        if task.incremental and task.since is None:
            errors.append("'since' timestamp is required for incremental ingestion")

        return errors

    def _execute_impl(
        self,
        task: IngestionTask,
        obs_context: ObservabilityContext,
    ) -> IngestionTaskResult:
        """Execute the ingestion task."""
        started_at = datetime.now()

        # Get connector
        connector_type = task.source_config.get("connector_type")
        connector = self._connectors[connector_type]

        # Configure connector
        source_config = SourceConfig(
            connector_type=connector_type,
            connection_params=task.source_config.get("connection_params", {}),
            fetch_options=task.source_config.get("fetch_options", {}),
        )
        connector.configure(source_config)

        # Validate connection
        connection_result = connector.validate_connection()
        if not connection_result.is_connected:
            return self._create_connection_error_result(
                task, connection_result.message, started_at
            )

        # Fetch and store records
        total_items = 0
        succeeded_count = 0
        failed_count = 0
        skipped_count = 0
        new_files_count = 0
        updated_files_count = 0
        unchanged_files_count = 0
        errors: List[ProcessingError] = []
        ingested_file_ids: List[str] = []

        try:
            # Get records iterator
            if task.incremental and task.since:
                records = connector.fetch_incremental(task.since)
            else:
                records = connector.fetch()

            # Process each record
            for record in records:
                if self._is_cancelled(task.id):
                    self._logger.info(f"Task {task.id} cancelled")
                    break

                total_items += 1

                try:
                    # Check for duplicates
                    existing_id = self._storage.exists_by_hash(
                        task.knowledge_base_id,
                        record.content_bytes.hex()[:64],  # Use first 64 chars as partial hash
                    )

                    if existing_id and task.dedup_strategy == "skip":
                        unchanged_files_count += 1
                        skipped_count += 1
                        continue

                    # Store the record
                    raw_file = self._storage.save(record, task.knowledge_base_id)
                    ingested_file_ids.append(raw_file.id)

                    if existing_id:
                        updated_files_count += 1
                    else:
                        new_files_count += 1

                    succeeded_count += 1

                    self._logger.debug(
                        f"Ingested file: {record.source_uri} -> {raw_file.id}"
                    )

                except Exception as e:
                    failed_count += 1
                    errors.append(
                        self._create_processing_error(
                            item_id=record.source_uri,
                            item_name=record.metadata.get("original_name", record.source_uri),
                            step="ingestion",
                            error=e,
                            recoverable=True,
                        )
                    )
                    self._logger.warning(
                        f"Failed to ingest {record.source_uri}: {e}"
                    )

        except Exception as e:
            # Fatal error during fetch
            self._logger.error(f"Fatal error during ingestion: {e}")
            errors.append(
                self._create_processing_error(
                    item_id=task.id,
                    item_name="fetch_operation",
                    step="fetch",
                    error=e,
                    recoverable=False,
                )
            )

        # Determine status
        if self._is_cancelled(task.id):
            status = TaskStatus.CANCELLED
        elif failed_count > 0 and succeeded_count == 0:
            status = TaskStatus.FAILED
        else:
            status = TaskStatus.COMPLETED

        return IngestionTaskResult(
            task_id=task.id,
            status=status,
            total_items=total_items,
            succeeded_count=succeeded_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            errors=errors,
            started_at=started_at,
            completed_at=datetime.now(),
            ingested_file_ids=ingested_file_ids,
            new_files_count=new_files_count,
            updated_files_count=updated_files_count,
            unchanged_files_count=unchanged_files_count,
        )

    def _create_connection_error_result(
        self,
        task: IngestionTask,
        error_message: str,
        started_at: datetime,
    ) -> IngestionTaskResult:
        """Create a result for a connection error."""
        return IngestionTaskResult(
            task_id=task.id,
            status=TaskStatus.FAILED,
            total_items=0,
            succeeded_count=0,
            failed_count=1,
            skipped_count=0,
            errors=[
                ProcessingError(
                    item_id=task.id,
                    item_name="connection",
                    step="connect",
                    error_type="ConnectionError",
                    error_message=error_message,
                    recoverable=True,
                )
            ],
            started_at=started_at,
            completed_at=datetime.now(),
            ingested_file_ids=[],
            new_files_count=0,
            updated_files_count=0,
            unchanged_files_count=0,
        )

    def _create_cancelled_result(
        self,
        task: IngestionTask,
        started_at: datetime,
    ) -> IngestionTaskResult:
        """Create a result for a cancelled task."""
        return IngestionTaskResult(
            task_id=task.id,
            status=TaskStatus.CANCELLED,
            total_items=0,
            succeeded_count=0,
            failed_count=0,
            skipped_count=0,
            errors=[],
            started_at=started_at,
            completed_at=datetime.now(),
            ingested_file_ids=[],
            new_files_count=0,
            updated_files_count=0,
            unchanged_files_count=0,
        )

    def _create_validation_error_result(
        self,
        task: IngestionTask,
        errors: List[str],
        started_at: datetime,
    ) -> IngestionTaskResult:
        """Create a result for validation errors."""
        return IngestionTaskResult(
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
            ingested_file_ids=[],
            new_files_count=0,
            updated_files_count=0,
            unchanged_files_count=0,
        )

    def _create_fatal_error_result(
        self,
        task: IngestionTask,
        error: Exception,
        started_at: datetime,
    ) -> IngestionTaskResult:
        """Create a result for a fatal error."""
        return IngestionTaskResult(
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
            ingested_file_ids=[],
            new_files_count=0,
            updated_files_count=0,
            unchanged_files_count=0,
        )
