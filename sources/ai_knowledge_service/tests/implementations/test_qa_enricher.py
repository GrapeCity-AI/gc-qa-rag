"""
Tests for QA Enricher.
"""

from unittest.mock import Mock, MagicMock

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
from ai_knowledge_service.implementations.steps.enrichers.qa_enricher import (
    QAEnricher,
    QAPair,
    ChunkQA,
)


def create_test_context(content: str, chunks: list = None) -> ProcessingContext:
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
        size_bytes=len(content.encode()),
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
        content=content,
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


class TestQAEnricher:
    """Tests for QAEnricher."""

    def test_step_type(self):
        """Test enricher step type."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)
        assert enricher.step_type == "qa_enricher"

    def test_enrichment_type(self):
        """Test enrichment type."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)
        assert enricher.enrichment_type == "qa"

    def test_requires_chunks(self):
        """Test requires_chunks property."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)
        assert enricher.requires_chunks is True

    def test_configure(self):
        """Test custom configuration."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)

        enricher.configure({
            "min_qa_count": 5,
            "multi_chunk_threshold": 3,
        })

        assert enricher._config["min_qa_count"] == 5
        assert enricher._config["multi_chunk_threshold"] == 3

    def test_process_no_chunks(self):
        """Test processing without chunks marks skip."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)
        enricher.configure({})

        context = create_test_context("content", chunks=None)
        obs = create_obs_context()

        result = enricher.process(context, obs)

        assert result.should_skip
        assert len(result.errors) > 0

    def test_process_empty_chunks(self):
        """Test processing with empty chunks marks skip."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)
        enricher.configure({})

        context = create_test_context("content", chunks=[])
        obs = create_obs_context()

        result = enricher.process(context, obs)

        assert result.should_skip

    def test_skip_already_skipped_context(self):
        """Test that already skipped context is returned unchanged."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)
        enricher.configure({})

        chunks = [
            Chunk(id="chunk-1", index=0, content="Test content"),
        ]
        context = create_test_context("content", chunks=chunks)
        context.mark_skip("previous error")
        obs = create_obs_context()

        result = enricher.process(context, obs)

        assert result.should_skip
        assert result.skip_reason == "previous error"

    def test_single_group_strategy(self):
        """Test single group QA generation."""
        llm_client = Mock()
        llm_client.chat.return_value = '{"Summary":"Test summary","PossibleQA":[{"Question":"Q1?","Answer":"A1"}]}'

        enricher = QAEnricher(llm_client)
        enricher.configure({"multi_chunk_threshold": 3})  # High threshold to force single group

        chunks = [
            Chunk(id="chunk-1", index=0, content="Test content"),
        ]
        context = create_test_context("Test full content", chunks=chunks)
        obs = create_obs_context()

        result = enricher.process(context, obs)

        assert not result.should_skip
        qa_data = result.get_enrichment("qa")
        assert qa_data is not None
        assert qa_data["total_qa_pairs"] == 1
        llm_client.chat.assert_called_once()

    def test_multi_group_strategy(self):
        """Test multi group QA generation with context."""
        llm_client = Mock()
        llm_client.chat_with_messages.return_value = '{"Summary":"Test summary","PossibleQA":[{"Question":"Q1?","Answer":"A1"}]}'

        enricher = QAEnricher(llm_client)
        enricher.configure({"multi_chunk_threshold": 2})

        chunks = [
            Chunk(id="chunk-1", index=0, content="Test content 1"),
            Chunk(id="chunk-2", index=1, content="Test content 2"),
        ]
        context = create_test_context("Test full content", chunks=chunks)
        obs = create_obs_context()

        result = enricher.process(context, obs)

        assert not result.should_skip
        qa_data = result.get_enrichment("qa")
        assert qa_data is not None
        assert len(qa_data["chunk_qa"]) == 2
        # Should use chat_with_messages for multi-group
        assert llm_client.chat_with_messages.call_count == 2

    def test_extract_qa_json(self):
        """Test QA extraction from JSON response."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)

        response = '{"Summary":"Test","PossibleQA":[{"Question":"Q?","Answer":"A"}]}'
        result = enricher._extract_qa_object(response)

        assert result["Summary"] == "Test"
        assert len(result["PossibleQA"]) == 1

    def test_extract_qa_markdown_code_block(self):
        """Test QA extraction from markdown code block."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)

        response = '''```json
{"Summary":"Test","PossibleQA":[{"Question":"Q?","Answer":"A"}]}
```'''
        result = enricher._extract_qa_object(response)

        assert result["Summary"] == "Test"
        assert len(result["PossibleQA"]) == 1

    def test_extract_qa_invalid_json(self):
        """Test QA extraction handles invalid JSON gracefully."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)

        response = "This is not valid JSON at all"
        result = enricher._extract_qa_object(response)

        assert result["Summary"] == ""
        assert result["PossibleQA"] == []

    def test_llm_error_handling(self):
        """Test that LLM errors are handled gracefully."""
        llm_client = Mock()
        llm_client.chat.side_effect = Exception("LLM API error")

        enricher = QAEnricher(llm_client)
        enricher.configure({"multi_chunk_threshold": 10})

        chunks = [
            Chunk(id="chunk-1", index=0, content="Test content"),
        ]
        context = create_test_context("Test full content", chunks=chunks)
        obs = create_obs_context()

        result = enricher.process(context, obs)

        # Should not skip on QA failure - it's not fatal
        # But should have an empty QA result
        qa_data = result.get_enrichment("qa")
        assert qa_data is not None
        assert qa_data["chunk_qa"][0]["qa_pairs"] == []

    def test_chunk_qa_to_dict(self):
        """Test ChunkQA to dict conversion."""
        llm_client = Mock()
        enricher = QAEnricher(llm_client)

        chunk_qa = ChunkQA(
            chunk_id="test-chunk",
            summary="Test summary",
            qa_pairs=[
                QAPair(question="Q1?", answer="A1"),
                QAPair(question="Q2?", answer="A2"),
            ],
        )

        result = enricher._chunk_qa_to_dict(chunk_qa)

        assert result["chunk_id"] == "test-chunk"
        assert result["summary"] == "Test summary"
        assert len(result["qa_pairs"]) == 2
        assert result["qa_pairs"][0]["question"] == "Q1?"
        assert result["qa_pairs"][0]["answer"] == "A1"
