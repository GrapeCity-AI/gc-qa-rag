"""
Indexing Executor - Executes indexing tasks.

Coordinates the processing pipeline: parsing, chunking, enrichment,
embedding, index building, and storage.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_knowledge_service.abstractions.execution.executor import IIndexingExecutor
from ai_knowledge_service.abstractions.models.index import IndexSchema, VectorConfig
from ai_knowledge_service.abstractions.models.knowledge_base import (
    FileVersion,
    IndexStatus,
)
from ai_knowledge_service.abstractions.models.tasks import (
    IndexingTask,
    IndexingTaskResult,
    ProcessingError,
    StepConfig,
    StepStats,
    TaskStatus,
    TaskType,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
from ai_knowledge_service.abstractions.pipelines.steps import (
    IProcessingStep,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.storage.index_storage import IIndexStorage
from ai_knowledge_service.abstractions.storage.raw_file_storage import IRawFileStorage
from ai_knowledge_service.core.executors.base_executor import BaseExecutor


class IndexingExecutor(BaseExecutor[IndexingTask, IndexingTaskResult], IIndexingExecutor):
    """
    Indexing Executor - Runs the indexing pipeline.

    Responsibilities:
    - Load files to process (full or incremental)
    - Run processing steps in sequence
    - Build and write index records
    - Track per-step statistics
    - Handle errors with skip-and-continue
    """

    def __init__(
        self,
        raw_file_storage: IRawFileStorage,
        index_storage: IIndexStorage,
        processing_steps: Dict[str, IProcessingStep],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the indexing executor.

        Args:
            raw_file_storage: Storage for reading raw files.
            index_storage: Storage for writing indexes.
            processing_steps: Map of step type to step instance.
            logger: Optional logger instance.
        """
        super().__init__(logger)
        self._raw_storage = raw_file_storage
        self._index_storage = index_storage
        self._steps = processing_steps

    @property
    def task_type(self) -> TaskType:
        """Get the task type this executor handles."""
        return TaskType.INDEXING

    def validate(self, task: IndexingTask) -> List[str]:
        """Validate indexing task parameters."""
        errors = []

        # Check pipeline configuration
        if not task.pipeline_config:
            errors.append("pipeline_config is required")
            return errors

        # Validate all steps are available
        for step_config in task.pipeline_config:
            if step_config.step_type not in self._steps:
                errors.append(f"Unknown step type: {step_config.step_type}")

        return errors

    def _execute_impl(
        self,
        task: IndexingTask,
        obs_context: ObservabilityContext,
    ) -> IndexingTaskResult:
        """Execute the indexing task."""
        started_at = datetime.now()
        step_stats: Dict[str, StepStats] = {}
        errors: List[ProcessingError] = []
        total_items = 0
        succeeded_count = 0
        failed_count = 0
        skipped_count = 0
        index_records_count = 0
        collections_affected: List[str] = []

        try:
            # Get or create collection
            collection_name = self._get_collection_name(task)

            # Ensure collection exists
            if not self._index_storage.collection_exists(collection_name):
                self._create_collection(collection_name, task)

            collections_affected.append(collection_name)

            # Get files to process
            file_versions = self._get_files_to_process(task)
            total_items = len(file_versions)

            self._logger.info(
                f"Processing {total_items} files for indexing"
            )

            # Configure processing steps
            enabled_steps = self._configure_steps(task.pipeline_config)

            # Process each file
            for file_version in file_versions:
                if self._is_cancelled(task.id):
                    self._logger.info(f"Task {task.id} cancelled")
                    break

                try:
                    # Load raw file
                    raw_file = self._raw_storage.get(file_version.raw_file_id)
                    if raw_file is None:
                        raise ValueError(f"Raw file not found: {file_version.raw_file_id}")

                    # Load content
                    raw_content = self._raw_storage.get_content(file_version.raw_file_id)

                    # Create processing context
                    context = ProcessingContext(
                        raw_file=raw_file,
                        file_version=file_version,
                        raw_content=raw_content,
                    )

                    # Run processing pipeline
                    context = self._run_pipeline(
                        context,
                        enabled_steps,
                        obs_context,
                        step_stats,
                    )

                    # Collect errors from context
                    errors.extend(context.errors)

                    if context.should_skip:
                        skipped_count += 1
                        self._logger.debug(
                            f"Skipped file {raw_file.original_name}: {context.skip_reason}"
                        )
                        continue

                    # Write index records
                    if context.index_records:
                        write_result = self._index_storage.write(
                            collection_name,
                            context.index_records,
                        )

                        if write_result.success:
                            index_records_count += write_result.records_written
                            succeeded_count += 1
                        else:
                            failed_count += 1
                            errors.append(
                                ProcessingError(
                                    item_id=file_version.id,
                                    item_name=raw_file.original_name,
                                    step="write",
                                    error_type="WriteError",
                                    error_message=write_result.error_message or "Unknown write error",
                                )
                            )
                    else:
                        # No records generated (but no error)
                        skipped_count += 1

                except Exception as e:
                    failed_count += 1
                    errors.append(
                        self._create_processing_error(
                            item_id=file_version.id,
                            item_name=file_version.raw_file_id,
                            step="process",
                            error=e,
                            recoverable=True,
                        )
                    )
                    self._logger.warning(
                        f"Failed to process file {file_version.id}: {e}"
                    )

        except Exception as e:
            self._logger.error(f"Fatal error during indexing: {e}")
            errors.append(
                self._create_processing_error(
                    item_id=task.id,
                    item_name="indexing_task",
                    step="execute",
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

        return IndexingTaskResult(
            task_id=task.id,
            status=status,
            total_items=total_items,
            succeeded_count=succeeded_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            errors=errors,
            started_at=started_at,
            completed_at=datetime.now(),
            index_records_count=index_records_count,
            collections_affected=collections_affected,
            step_stats=step_stats,
        )

    def _get_collection_name(self, task: IndexingTask) -> str:
        """Generate collection name for the task."""
        # Format: kb_{kb_id}_{version_id}
        kb_id = task.knowledge_base_id[:8]
        version_id = task.knowledge_base_version_id[:8]
        return f"kb_{kb_id}_{version_id}"

    def _create_collection(self, name: str, task: IndexingTask) -> None:
        """Create index collection."""
        # Default schema for QA vector index
        schema = IndexSchema(
            index_type="vector",
            vector_config=VectorConfig(
                dimensions=1024,
                distance_metric="cosine",
                sparse_enabled=True,
            ),
        )

        self._index_storage.create_collection(
            name=name,
            schema=schema,
            knowledge_base_version_id=task.knowledge_base_version_id,
        )

    def _get_files_to_process(self, task: IndexingTask) -> List[FileVersion]:
        """Get list of files to process based on task configuration."""
        # For now, we'll create FileVersion objects from specified IDs
        # In a full implementation, this would query a FileVersion store

        file_versions = []

        if task.file_version_ids:
            # Process specific files
            for fv_id in task.file_version_ids:
                # Create a placeholder FileVersion
                # In production, this would be loaded from storage
                file_versions.append(
                    FileVersion(
                        id=fv_id,
                        raw_file_id=fv_id,  # Assuming same ID for simplicity
                        knowledge_base_version_id=task.knowledge_base_version_id,
                        content_hash="",  # Would be populated from storage
                        index_status=IndexStatus.PENDING,
                    )
                )
        else:
            # Full build - list all files for the knowledge base
            for raw_file in self._raw_storage.list(task.knowledge_base_id):
                file_versions.append(
                    FileVersion(
                        id=str(uuid.uuid4()),
                        raw_file_id=raw_file.id,
                        knowledge_base_version_id=task.knowledge_base_version_id,
                        content_hash=raw_file.content_hash,
                        index_status=IndexStatus.PENDING,
                    )
                )

        return file_versions

    def _configure_steps(
        self,
        pipeline_config: List[StepConfig],
    ) -> List[IProcessingStep]:
        """Configure and return enabled processing steps."""
        enabled_steps = []

        for step_config in pipeline_config:
            if not step_config.enabled:
                continue

            step = self._steps.get(step_config.step_type)
            if step is None:
                self._logger.warning(f"Step not found: {step_config.step_type}")
                continue

            step.configure(step_config.config)
            enabled_steps.append(step)

        return enabled_steps

    def _run_pipeline(
        self,
        context: ProcessingContext,
        steps: List[IProcessingStep],
        obs_context: ObservabilityContext,
        step_stats: Dict[str, StepStats],
    ) -> ProcessingContext:
        """Run the processing pipeline on a context."""
        for step in steps:
            if context.should_skip:
                break

            step_type = step.step_type
            step_start = time.time()
            input_count = self._get_input_count(context, step_type)

            try:
                context = step.process(context, obs_context)

            except Exception as e:
                context.add_error(
                    step=step_type,
                    error_type=type(e).__name__,
                    message=str(e),
                    recoverable=True,
                )
                self._logger.warning(f"Step {step_type} failed: {e}")

            # Update step stats
            step_duration = time.time() - step_start
            output_count = self._get_output_count(context, step_type)
            errors_count = len([e for e in context.errors if e.step == step_type])

            if step_type not in step_stats:
                step_stats[step_type] = StepStats(
                    step_type=step_type,
                    input_count=0,
                    output_count=0,
                    duration_seconds=0.0,
                    errors_count=0,
                )

            stats = step_stats[step_type]
            step_stats[step_type] = StepStats(
                step_type=step_type,
                input_count=stats.input_count + input_count,
                output_count=stats.output_count + output_count,
                duration_seconds=stats.duration_seconds + step_duration,
                errors_count=stats.errors_count + errors_count,
            )

        return context

    def _get_input_count(self, context: ProcessingContext, step_type: str) -> int:
        """Get input count for a step."""
        if "parser" in step_type:
            return 1  # One raw file
        elif "chunker" in step_type:
            return 1  # One document
        elif "enricher" in step_type:
            return len(context.chunks or [])
        elif "embedder" in step_type:
            return len(context.chunks or [])
        elif "index_builder" in step_type:
            return len(context.embeddings or [])
        return 1

    def _get_output_count(self, context: ProcessingContext, step_type: str) -> int:
        """Get output count for a step."""
        if "parser" in step_type:
            return 1 if context.parsed_document else 0
        elif "chunker" in step_type:
            return len(context.chunks or [])
        elif "enricher" in step_type:
            qa = context.get_enrichment("qa", {})
            return qa.get("total_qa_pairs", 0)
        elif "embedder" in step_type:
            return len(context.embeddings or [])
        elif "index_builder" in step_type:
            return len(context.index_records or [])
        return 0

    def _create_cancelled_result(
        self,
        task: IndexingTask,
        started_at: datetime,
    ) -> IndexingTaskResult:
        """Create a result for a cancelled task."""
        return IndexingTaskResult(
            task_id=task.id,
            status=TaskStatus.CANCELLED,
            total_items=0,
            succeeded_count=0,
            failed_count=0,
            skipped_count=0,
            errors=[],
            started_at=started_at,
            completed_at=datetime.now(),
            index_records_count=0,
            collections_affected=[],
            step_stats={},
        )

    def _create_validation_error_result(
        self,
        task: IndexingTask,
        errors: List[str],
        started_at: datetime,
    ) -> IndexingTaskResult:
        """Create a result for validation errors."""
        return IndexingTaskResult(
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
            index_records_count=0,
            collections_affected=[],
            step_stats={},
        )

    def _create_fatal_error_result(
        self,
        task: IndexingTask,
        error: Exception,
        started_at: datetime,
    ) -> IndexingTaskResult:
        """Create a result for a fatal error."""
        return IndexingTaskResult(
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
            index_records_count=0,
            collections_affected=[],
            step_stats={},
        )
