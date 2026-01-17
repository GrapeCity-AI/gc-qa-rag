"""
Integration Tests for Generic Pipeline.

Tests the end-to-end flow from ingestion through indexing.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

import pytest

from ai_knowledge_service.abstractions.models.tasks import (
    IngestionTask,
    IndexingTask,
    PublishingTask,
    TaskStatus,
    StepConfig,
)
from ai_knowledge_service.abstractions.models.raw_file import RawFile, LifecycleStatus
from ai_knowledge_service.abstractions.models.knowledge_base import FileVersion, IndexStatus
from ai_knowledge_service.abstractions.pipelines.source import SourceConfig
from ai_knowledge_service.abstractions.models.index import IndexSchema, VectorConfig

from ai_knowledge_service.implementations.connectors.filesystem_connector import (
    FilesystemConnector,
)
from ai_knowledge_service.implementations.steps.parsers.markitdown_parser import (
    MarkItDownParser,
)
from ai_knowledge_service.implementations.steps.chunkers.sentence_chunker import (
    SentenceChunker,
)
from ai_knowledge_service.implementations.steps.enrichers.qa_enricher import (
    QAEnricher,
)
from ai_knowledge_service.implementations.steps.embedders.dashscope_embedder import (
    DashScopeEmbedder,
    DashScopeConfig,
)
from ai_knowledge_service.implementations.steps.index_builders.vector_index_builder import (
    VectorIndexBuilder,
)

from ai_knowledge_service.core.executors.ingestion_executor import IngestionExecutor
from ai_knowledge_service.core.executors.indexing_executor import IndexingExecutor
from ai_knowledge_service.core.executors.publishing_executor import PublishingExecutor


class TestGenericPipelineIntegration:
    """Integration tests for the generic pipeline."""

    def test_filesystem_connector_fetch(self):
        """Test filesystem connector can fetch files."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "test1.txt").write_text("这是第一个测试文件。内容很简单。", encoding="utf-8")
            Path(tmpdir, "test2.txt").write_text("这是第二个测试文件。内容也很简单。", encoding="utf-8")

            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
            )
            connector.configure(config)

            records = list(connector.fetch())

            assert len(records) == 2
            assert all(r.content_str for r in records)

    def test_parser_chunker_integration(self):
        """Test parser and chunker work together."""
        from ai_knowledge_service.abstractions.pipelines.steps import ProcessingContext
        from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
        from ai_knowledge_service.abstractions.models.tasks import TaskType

        parser = MarkItDownParser()
        parser.configure({})

        chunker = SentenceChunker()
        chunker.configure({"group_size": 2})

        # Create context with raw file
        raw_file = RawFile(
            id="test-file",
            knowledge_base_id="test-kb",
            source_type="test",
            source_uri="test://file",
            original_name="test.txt",
            content_hash="abc123",
            storage_path="/tmp/test.txt",
            mime_type="text/plain",
            size_bytes=100,
            lifecycle_status=LifecycleStatus.ACTIVE,
        )

        file_version = FileVersion(
            id="test-version",
            raw_file_id="test-file",
            knowledge_base_version_id="test-kb-version",
            content_hash="abc123",
            index_status=IndexStatus.PENDING,
        )

        context = ProcessingContext(
            raw_file=raw_file,
            file_version=file_version,
        )

        obs = ObservabilityContext.create(
            task_id="test-task",
            task_type=TaskType.INDEXING,
            knowledge_base_id="test-kb",
            knowledge_base_version_id="test-kb-version",
        )

        # Create temp file for parser and load content
        test_content = "第一句话。第二句话。第三句话。第四句话。"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(test_content)
            temp_path = f.name

        try:
            # Update context with actual file path and content
            context.raw_file.storage_path = temp_path
            context.raw_content = test_content.encode("utf-8")

            # Run parser
            context = parser.process(context, obs)
            assert context.parsed_document is not None

            # Run chunker
            context = chunker.process(context, obs)
            assert context.chunks is not None
            assert len(context.chunks) == 2  # 4 sentences / group_size 2

        finally:
            Path(temp_path).unlink()

    def test_ingestion_executor_validation(self):
        """Test ingestion executor validation."""
        raw_storage = Mock()
        connectors = {"filesystem": FilesystemConnector()}

        executor = IngestionExecutor(raw_storage, connectors)

        # Valid task
        valid_task = IngestionTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            source_config={
                "connector_type": "filesystem",
                "connection_params": {"path": "/data"},
            },
        )
        errors = executor.validate(valid_task)
        assert len(errors) == 0

        # Invalid task - missing connector type
        invalid_task = IngestionTask(
            id="task-2",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            source_config={},
        )
        errors = executor.validate(invalid_task)
        assert len(errors) > 0

    def test_indexing_executor_validation(self):
        """Test indexing executor validation."""
        raw_storage = Mock()
        index_storage = Mock()

        parser = MarkItDownParser()
        chunker = SentenceChunker()

        steps = {
            "markitdown_parser": parser,
            "sentence_chunker": chunker,
        }

        executor = IndexingExecutor(raw_storage, index_storage, steps)

        # Valid task
        valid_task = IndexingTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            pipeline_config=[
                StepConfig(step_type="markitdown_parser"),
                StepConfig(step_type="sentence_chunker"),
            ],
        )
        errors = executor.validate(valid_task)
        assert len(errors) == 0

        # Invalid task - unknown step
        invalid_task = IndexingTask(
            id="task-2",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            pipeline_config=[
                StepConfig(step_type="unknown_step"),
            ],
        )
        errors = executor.validate(invalid_task)
        assert len(errors) > 0

    def test_publishing_executor_validation(self):
        """Test publishing executor validation."""
        index_storage = Mock()
        executor = PublishingExecutor(index_storage)

        # Valid task
        valid_task = PublishingTask(
            id="task-1",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            target_environment_id="local",
            alias_name="test-alias",
        )
        errors = executor.validate(valid_task)
        assert len(errors) == 0

        # Invalid task - missing alias
        invalid_task = PublishingTask(
            id="task-2",
            knowledge_base_id="kb-1",
            knowledge_base_version_id="v-1",
            target_environment_id="local",
            alias_name=None,
        )
        errors = executor.validate(invalid_task)
        assert len(errors) > 0

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_publishing_executor_execute(self, mock_qdrant_class):
        """Test publishing executor execution."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = True
        mock_client.get_aliases.return_value = Mock(aliases=[])

        mock_info = Mock()
        mock_info.points_count = 100
        mock_info.vectors_count = 200
        mock_info.status = Mock(value="green")
        mock_client.get_collection.return_value = mock_info

        mock_qdrant_class.return_value = mock_client

        from ai_knowledge_service.implementations.storage.qdrant_index_storage import (
            QdrantIndexStorage,
            QdrantConfig,
        )

        config = QdrantConfig(url="http://localhost:6333")
        index_storage = QdrantIndexStorage(config)

        executor = PublishingExecutor(index_storage)

        task = PublishingTask(
            id="task-12345678",
            knowledge_base_id="kb-12345678",
            knowledge_base_version_id="v-12345678",
            target_environment_id="local",
            alias_name="test-alias",
        )

        result = executor.execute(task)

        assert result.status == TaskStatus.COMPLETED
        mock_client.update_collection_aliases.assert_called_once()

    def test_steps_skip_propagation(self):
        """Test that skip status propagates through steps."""
        from ai_knowledge_service.abstractions.pipelines.steps import ProcessingContext
        from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
        from ai_knowledge_service.abstractions.models.tasks import TaskType

        parser = MarkItDownParser()
        parser.configure({})

        chunker = SentenceChunker()
        chunker.configure({})

        raw_file = RawFile(
            id="test-file",
            knowledge_base_id="test-kb",
            source_type="test",
            source_uri="test://file",
            original_name="test.txt",
            content_hash="abc123",
            storage_path="/nonexistent/path.txt",  # Will cause error
            mime_type="text/plain",
            size_bytes=100,
            lifecycle_status=LifecycleStatus.ACTIVE,
        )

        file_version = FileVersion(
            id="test-version",
            raw_file_id="test-file",
            knowledge_base_version_id="test-kb-version",
            content_hash="abc123",
            index_status=IndexStatus.PENDING,
        )

        context = ProcessingContext(
            raw_file=raw_file,
            file_version=file_version,
        )

        obs = ObservabilityContext.create(
            task_id="test-task",
            task_type=TaskType.INDEXING,
            knowledge_base_id="test-kb",
            knowledge_base_version_id="test-kb-version",
        )

        # Parser should mark skip due to file not found
        context = parser.process(context, obs)
        assert context.should_skip

        # Chunker should respect the skip
        context = chunker.process(context, obs)
        assert context.should_skip

    def test_vector_index_builder(self):
        """Test vector index builder creates records."""
        from ai_knowledge_service.abstractions.pipelines.steps import (
            ProcessingContext,
            Chunk,
            Embedding,
            ParsedDocument,
        )
        from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
        from ai_knowledge_service.abstractions.models.tasks import TaskType

        builder = VectorIndexBuilder()
        builder.configure({})

        raw_file = RawFile(
            id="test-file",
            knowledge_base_id="test-kb",
            source_type="test",
            source_uri="test://file",
            original_name="test.txt",
            content_hash="abc123",
            storage_path="/tmp/test.txt",
            mime_type="text/plain",
            size_bytes=100,
            lifecycle_status=LifecycleStatus.ACTIVE,
        )

        file_version = FileVersion(
            id="test-version",
            raw_file_id="test-file",
            knowledge_base_version_id="test-kb-version",
            content_hash="abc123",
            index_status=IndexStatus.PENDING,
        )

        context = ProcessingContext(
            raw_file=raw_file,
            file_version=file_version,
        )

        context.parsed_document = ParsedDocument(
            title="Test Doc",
            content="Test content",
        )

        context.chunks = [
            Chunk(id="chunk-1", index=0, content="Test chunk"),
        ]

        # Add QA enrichment
        context.set_enrichment("qa", {
            "chunk_qa": [{
                "chunk_id": "chunk-1",
                "summary": "Test summary",
                "qa_pairs": [{"question": "Q?", "answer": "A"}],
            }],
        })

        # Add embeddings
        context.embeddings = [
            Embedding(
                id="emb-1",
                chunk_id="chunk-1",
                vector=[0.1] * 1024,
                sparse_vector={1: 0.5},
                metadata={"type": "question", "index": 0},
            ),
            Embedding(
                id="emb-2",
                chunk_id="chunk-1",
                vector=[0.2] * 1024,
                sparse_vector={2: 0.3},
                metadata={"type": "answer", "index": 0},
            ),
        ]

        obs = ObservabilityContext.create(
            task_id="test-task",
            task_type=TaskType.INDEXING,
            knowledge_base_id="test-kb",
            knowledge_base_version_id="test-kb-version",
        )

        context = builder.process(context, obs)

        assert context.index_records is not None
        assert len(context.index_records) > 0
        # Each QA pair should generate one record, index_type is "vector"
        assert any(r.index_type == "vector" for r in context.index_records)


class TestConnectorIntegration:
    """Integration tests for connectors."""

    def test_filesystem_connector_with_extensions(self):
        """Test filesystem connector with extension filtering."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text("text", encoding="utf-8")
            Path(tmpdir, "test.md").write_text("markdown", encoding="utf-8")
            Path(tmpdir, "test.py").write_text("python", encoding="utf-8")

            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
                fetch_options={"extensions": [".txt", ".md"]},
            )
            connector.configure(config)

            records = list(connector.fetch())

            assert len(records) == 2
            names = {r.metadata["original_name"] for r in records}
            assert names == {"test.txt", "test.md"}

    def test_filesystem_connector_recursive(self):
        """Test filesystem connector recursive mode."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()

            Path(tmpdir, "root.txt").write_text("root", encoding="utf-8")
            Path(subdir, "nested.txt").write_text("nested", encoding="utf-8")

            # Test recursive=True
            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir, "recursive": True},
            )
            connector.configure(config)

            records = list(connector.fetch())
            assert len(records) == 2

            # Test recursive=False
            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir, "recursive": False},
            )
            connector.configure(config)

            records = list(connector.fetch())
            assert len(records) == 1
            assert records[0].metadata["original_name"] == "root.txt"
