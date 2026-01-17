"""
Tests for DashScope Embedder.
"""

from http import HTTPStatus
from unittest.mock import Mock, MagicMock, patch

import pytest

from ai_knowledge_service.abstractions.pipelines.steps import (
    Chunk,
    ParsedDocument,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.models.raw_file import RawFile, LifecycleStatus
from ai_knowledge_service.abstractions.models.knowledge_base import FileVersion, IndexStatus
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
from ai_knowledge_service.abstractions.models.tasks import TaskType
from ai_knowledge_service.implementations.steps.embedders.dashscope_embedder import (
    DashScopeEmbedder,
    DashScopeConfig,
    EmbeddingError,
)


def create_test_context(chunks: list = None) -> ProcessingContext:
    """Create a test processing context."""
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
        title="Test Document",
        content="Test content",
    )

    context.chunks = chunks

    return context


def create_obs_context() -> ObservabilityContext:
    """Create a test observability context."""
    return ObservabilityContext.create(
        task_id="test-task",
        task_type=TaskType.INDEXING,
        knowledge_base_id="test-kb",
        knowledge_base_version_id="test-kb-version",
    )


class TestDashScopeEmbedder:
    """Tests for DashScopeEmbedder."""

    def test_step_type(self):
        """Test embedder step type."""
        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)
        assert embedder.step_type == "dashscope_embedder"

    def test_dimensions(self):
        """Test embedding dimensions."""
        config = DashScopeConfig(api_key="test-key", dimensions=768)
        embedder = DashScopeEmbedder(config)
        assert embedder.dimensions == 768

    def test_supports_sparse(self):
        """Test sparse embedding support."""
        config = DashScopeConfig(api_key="test-key", output_type="dense&sparse")
        embedder = DashScopeEmbedder(config)
        assert embedder.supports_sparse is True

        config2 = DashScopeConfig(api_key="test-key", output_type="dense")
        embedder2 = DashScopeEmbedder(config2)
        assert embedder2.supports_sparse is False

    def test_model_name(self):
        """Test model name property."""
        config = DashScopeConfig(api_key="test-key", model_name="custom-model")
        embedder = DashScopeEmbedder(config)
        assert embedder.model_name == "custom-model"

    def test_configure(self):
        """Test configuration."""
        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)

        embedder.configure({
            "embed_questions": True,
            "embed_answers": False,
            "embed_chunks": True,
        })

        assert embedder._config["embed_questions"] is True
        assert embedder._config["embed_answers"] is False
        assert embedder._config["embed_chunks"] is True

    def test_process_no_chunks(self):
        """Test processing without chunks marks skip."""
        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)
        embedder.configure({})

        context = create_test_context(chunks=None)
        obs = create_obs_context()

        result = embedder.process(context, obs)

        assert result.should_skip
        assert len(result.errors) > 0

    def test_process_empty_chunks(self):
        """Test processing with empty chunks marks skip."""
        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)
        embedder.configure({})

        context = create_test_context(chunks=[])
        obs = create_obs_context()

        result = embedder.process(context, obs)

        assert result.should_skip

    def test_skip_already_skipped_context(self):
        """Test that already skipped context is returned unchanged."""
        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)
        embedder.configure({})

        chunks = [
            Chunk(id="chunk-1", index=0, content="Test content"),
        ]
        context = create_test_context(chunks=chunks)
        context.mark_skip("previous error")
        obs = create_obs_context()

        result = embedder.process(context, obs)

        assert result.should_skip
        assert result.skip_reason == "previous error"

    @patch("ai_knowledge_service.implementations.steps.embedders.dashscope_embedder.TextEmbedding")
    def test_process_with_qa_enrichment(self, mock_text_embedding):
        """Test processing with QA enrichment data."""
        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.output = {
            "embeddings": [
                {
                    "text_index": 0,
                    "embedding": [0.1] * 1024,
                    "sparse_embedding": {"indices": [1, 2], "values": [0.5, 0.3]},
                },
            ]
        }
        mock_text_embedding.call.return_value = mock_response

        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)
        embedder.configure({"embed_questions": True, "embed_answers": False})

        chunks = [
            Chunk(id="chunk-1", index=0, content="Test content"),
        ]
        context = create_test_context(chunks=chunks)
        context.set_enrichment("qa", {
            "chunk_qa": [{
                "chunk_id": "chunk-1",
                "summary": "Test summary",
                "qa_pairs": [{"question": "Q1?", "answer": "A1"}],
            }],
        })
        obs = create_obs_context()

        result = embedder.process(context, obs)

        assert not result.should_skip
        assert result.embeddings is not None
        assert len(result.embeddings) == 1
        mock_text_embedding.call.assert_called_once()

    @patch("ai_knowledge_service.implementations.steps.embedders.dashscope_embedder.TextEmbedding")
    def test_process_batch(self, mock_text_embedding):
        """Test batch processing of embeddings."""
        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.OK
        mock_response.output = {
            "embeddings": [
                {"text_index": 0, "embedding": [0.1] * 1024},
                {"text_index": 1, "embedding": [0.2] * 1024},
            ]
        }
        mock_text_embedding.call.return_value = mock_response

        config = DashScopeConfig(api_key="test-key", batch_size=10)
        embedder = DashScopeEmbedder(config)
        embedder.configure({"embed_questions": True, "embed_answers": True})

        chunks = [
            Chunk(id="chunk-1", index=0, content="Test content 1"),
        ]
        context = create_test_context(chunks=chunks)
        context.set_enrichment("qa", {
            "chunk_qa": [{
                "chunk_id": "chunk-1",
                "summary": "Test summary",
                "qa_pairs": [{"question": "Q1?", "answer": "A1"}],
            }],
        })
        obs = create_obs_context()

        result = embedder.process(context, obs)

        assert not result.should_skip
        assert len(result.embeddings) == 2

    @patch("ai_knowledge_service.implementations.steps.embedders.dashscope_embedder.TextEmbedding")
    def test_api_error_handling(self, mock_text_embedding):
        """Test handling of API errors."""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        mock_response.message = "API Error"
        mock_text_embedding.call.return_value = mock_response

        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)
        embedder.configure({})

        chunks = [
            Chunk(id="chunk-1", index=0, content="Test content"),
        ]
        context = create_test_context(chunks=chunks)
        context.set_enrichment("qa", {
            "chunk_qa": [{
                "chunk_id": "chunk-1",
                "summary": "Test",
                "qa_pairs": [{"question": "Q?", "answer": "A"}],
            }],
        })
        obs = create_obs_context()

        result = embedder.process(context, obs)

        assert result.should_skip
        assert len(result.errors) > 0

    def test_batched_generator(self):
        """Test the batch generator function."""
        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)

        items = [1, 2, 3, 4, 5]
        batches = list(embedder._batched(items, 2))

        assert len(batches) == 3
        assert batches[0] == [1, 2]
        assert batches[1] == [3, 4]
        assert batches[2] == [5]

    def test_convert_sparse_vector(self):
        """Test sparse vector conversion."""
        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)

        sparse_data = {"indices": [1, 5, 10], "values": [0.5, 0.3, 0.2]}
        result = embedder._convert_sparse_vector(sparse_data)

        assert result[1] == 0.5
        assert result[5] == 0.3
        assert result[10] == 0.2

    @patch("ai_knowledge_service.implementations.steps.embedders.dashscope_embedder.TextEmbedding")
    def test_no_texts_to_embed(self, mock_text_embedding):
        """Test behavior when no texts to embed."""
        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)
        embedder.configure({"embed_questions": True, "embed_answers": True})

        chunks = [
            Chunk(id="chunk-1", index=0, content="Test content"),
        ]
        context = create_test_context(chunks=chunks)
        # No QA enrichment data
        obs = create_obs_context()

        result = embedder.process(context, obs)

        assert not result.should_skip
        assert result.embeddings == []
        mock_text_embedding.call.assert_not_called()

    def test_create_embeddings_empty_texts(self):
        """Test that empty texts raise error."""
        config = DashScopeConfig(api_key="test-key")
        embedder = DashScopeEmbedder(config)

        with pytest.raises(EmbeddingError, match="No texts"):
            embedder._create_embeddings([])
