"""
Tests for Executors.
"""

from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

import pytest

from ai_knowledge_service.abstractions.models.tasks import (
    IngestionTask,
    IndexingTask,
    PublishingTask,
    TaskStatus,
    TaskType,
    StepConfig,
    PublishStrategy,
)
from ai_knowledge_service.abstractions.pipelines.source import SourceRecord
from ai_knowledge_service.core.executors.ingestion_executor import IngestionExecutor
from ai_knowledge_service.core.executors.indexing_executor import IndexingExecutor
from ai_knowledge_service.core.executors.publishing_executor import PublishingExecutor


class TestIngestionExecutor:
    """Tests for IngestionExecutor."""

    def test_validate_missing_source_config(self):
        """Test validation fails without source_config."""
        raw_storage = Mock()
        connectors = {"filesystem": Mock()}

        executor = IngestionExecutor(raw_storage, connectors)

        task = IngestionTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            source_config={},
        )

        errors = executor.validate(task)
        assert len(errors) > 0
        # Could be missing connector_type or source_config validation
        assert any("connector" in e.lower() or "source" in e.lower() for e in errors)

    def test_validate_unknown_connector(self):
        """Test validation fails with unknown connector."""
        raw_storage = Mock()
        connectors = {"filesystem": Mock()}

        executor = IngestionExecutor(raw_storage, connectors)

        task = IngestionTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            source_config={"connector_type": "unknown"},
        )

        errors = executor.validate(task)
        assert len(errors) > 0
        assert "unknown" in errors[0].lower()

    def test_validate_valid_config(self):
        """Test validation passes with valid config."""
        raw_storage = Mock()
        connectors = {"filesystem": Mock()}

        executor = IngestionExecutor(raw_storage, connectors)

        task = IngestionTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            source_config={
                "connector_type": "filesystem",
                "connection_params": {"path": "/data"},
            },
        )

        errors = executor.validate(task)
        assert len(errors) == 0

    def test_task_type(self):
        """Test executor has correct task type."""
        executor = IngestionExecutor(Mock(), {})
        assert executor.task_type == TaskType.INGESTION


class TestIndexingExecutor:
    """Tests for IndexingExecutor."""

    def test_validate_missing_pipeline_config(self):
        """Test validation fails without pipeline_config."""
        raw_storage = Mock()
        index_storage = Mock()
        steps = {}

        executor = IndexingExecutor(raw_storage, index_storage, steps)

        task = IndexingTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            pipeline_config=[],
        )

        errors = executor.validate(task)
        assert len(errors) > 0

    def test_validate_unknown_step(self):
        """Test validation fails with unknown step type."""
        raw_storage = Mock()
        index_storage = Mock()
        steps = {"markitdown_parser": Mock()}

        executor = IndexingExecutor(raw_storage, index_storage, steps)

        task = IndexingTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            pipeline_config=[
                StepConfig(step_type="unknown_step"),
            ],
        )

        errors = executor.validate(task)
        assert len(errors) > 0
        assert "unknown_step" in errors[0].lower()

    def test_validate_valid_config(self):
        """Test validation passes with valid config."""
        raw_storage = Mock()
        index_storage = Mock()
        steps = {
            "markitdown_parser": Mock(),
            "sentence_chunker": Mock(),
        }

        executor = IndexingExecutor(raw_storage, index_storage, steps)

        task = IndexingTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            pipeline_config=[
                StepConfig(step_type="markitdown_parser"),
                StepConfig(step_type="sentence_chunker"),
            ],
        )

        errors = executor.validate(task)
        assert len(errors) == 0

    def test_task_type(self):
        """Test executor has correct task type."""
        executor = IndexingExecutor(Mock(), Mock(), {})
        assert executor.task_type == TaskType.INDEXING


class TestPublishingExecutor:
    """Tests for PublishingExecutor."""

    def test_validate_missing_target_environment(self):
        """Test validation fails without target_environment_id."""
        # PublishingTask validates target_environment_id in __post_init__
        # so we expect ValueError when creating with empty target_environment_id
        with pytest.raises(ValueError, match="Target environment ID"):
            PublishingTask(
                id="task-1",
                knowledge_base_id="kb-1",
                knowledge_base_version_id="v-1",
                target_environment_id="",
            )

    def test_validate_missing_alias(self):
        """Test validation fails without alias_name."""
        index_storage = Mock()
        executor = PublishingExecutor(index_storage)

        task = PublishingTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            target_environment_id="local",
            alias_name=None,
        )

        errors = executor.validate(task)
        assert len(errors) > 0
        assert "alias_name" in errors[0]

    def test_validate_valid_config(self):
        """Test validation passes with valid config."""
        index_storage = Mock()
        executor = PublishingExecutor(index_storage)

        task = PublishingTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            target_environment_id="local",
            alias_name="kb-1-latest",
        )

        errors = executor.validate(task)
        assert len(errors) == 0

    def test_task_type(self):
        """Test executor has correct task type."""
        executor = PublishingExecutor(Mock())
        assert executor.task_type == TaskType.PUBLISHING

    def test_execute_updates_alias(self):
        """Test that execute updates the alias."""
        index_storage = Mock()
        index_storage.collection_exists.return_value = True
        index_storage.get_alias_target.return_value = None
        index_storage.get_collection_info.return_value = Mock(records_count=100)

        executor = PublishingExecutor(index_storage)

        task = PublishingTask(
            id="task-1",
            knowledge_base_id="kb-12345678",
            knowledge_base_version_id="v-12345678",
            target_environment_id="local",
            alias_name="test-alias",
        )

        result = executor.execute(task)

        assert result.status == TaskStatus.COMPLETED
        index_storage.update_alias.assert_called_once()
