"""
Tests for FullAnswerEnricher.
"""

import pytest
from unittest.mock import MagicMock, Mock

from ai_knowledge_service.abstractions.pipelines.steps import (
    ParsedDocument,
    ProcessingContext,
    Chunk,
)
from ai_knowledge_service.abstractions.models.raw_file import RawFile, LifecycleStatus
from ai_knowledge_service.abstractions.models.knowledge_base import FileVersion, IndexStatus
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
from ai_knowledge_service.abstractions.models.tasks import TaskType
from ai_knowledge_service.implementations.steps.enrichers import FullAnswerEnricher


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


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock()
    client.chat.return_value = "这是一个详细的答案，包含更多上下文信息..."
    return client


@pytest.fixture
def enricher(mock_llm_client):
    """Create a FullAnswerEnricher instance."""
    return FullAnswerEnricher(mock_llm_client)


@pytest.fixture
def processing_context():
    """Create a ProcessingContext with QA enrichment data."""
    context = create_test_context("This is the full document content for reference.")

    # Set chunks
    context.chunks = [
        Chunk(
            id="chunk-1",
            content="First chunk content",
            index=0,
            metadata={"sentence_count": 3},
        ),
    ]

    # Set QA enrichment
    context.set_enrichment("qa", {
        "chunk_qa": [
            {
                "chunk_id": "chunk-1",
                "summary": "Test summary",
                "qa_pairs": [
                    {"question": "What is this?", "answer": "Short answer"},
                    {"question": "How does it work?", "answer": "Brief explanation"},
                ],
            },
        ],
        "total_qa_pairs": 2,
    })

    return context


@pytest.fixture
def observability_context():
    """Create an ObservabilityContext."""
    return create_obs_context()


class TestFullAnswerEnricher:
    """Tests for FullAnswerEnricher."""

    def test_step_type(self, enricher):
        """Test step type identifier."""
        assert enricher.step_type == "full_answer_enricher"

    def test_enrichment_type(self, enricher):
        """Test enrichment type."""
        assert enricher.enrichment_type == "full_answer"

    def test_requires_chunks(self, enricher):
        """Test requires_chunks property."""
        assert enricher.requires_chunks is False

    def test_configure(self, enricher):
        """Test configuration."""
        config = {"max_content_length": 4000}
        enricher.configure(config)
        assert enricher._config == config

    def test_process_generates_full_answers(
        self, enricher, processing_context, observability_context, mock_llm_client
    ):
        """Test that process generates full answers for each QA pair."""
        result = enricher.process(processing_context, observability_context)

        # Check LLM was called for each QA pair
        assert mock_llm_client.chat.call_count == 2

        # Check enrichment was set
        full_answer_data = result.get_enrichment("full_answer")
        assert full_answer_data is not None
        assert full_answer_data["total_count"] == 2
        assert full_answer_data["success_count"] == 2

        answers = full_answer_data["answers"]
        assert len(answers) == 2
        assert answers[0]["question"] == "What is this?"
        assert answers[0]["full_answer"] == "这是一个详细的答案，包含更多上下文信息..."

    def test_process_skips_when_should_skip(
        self, enricher, processing_context, observability_context
    ):
        """Test that process respects should_skip flag."""
        processing_context.mark_skip("Skip reason")
        result = enricher.process(processing_context, observability_context)
        assert result.should_skip is True

    def test_process_without_qa_enrichment(
        self, enricher, observability_context
    ):
        """Test handling when no QA enrichment exists."""
        # Create a fresh context without QA enrichment
        context = create_test_context("This is the full document content for reference.")
        # Don't set any QA enrichment

        result = enricher.process(context, observability_context)

        # Should not generate any full answers
        assert result.get_enrichment("full_answer") is None

    def test_process_without_parsed_document(
        self, enricher, processing_context, observability_context
    ):
        """Test handling when no parsed document exists."""
        processing_context.parsed_document = None

        result = enricher.process(processing_context, observability_context)

        # Should add error
        assert len(result.errors) > 0
        assert "MissingInput" in result.errors[0].error_type

    def test_process_truncates_long_content(
        self, enricher, processing_context, observability_context, mock_llm_client
    ):
        """Test that long content is truncated."""
        enricher.configure({"max_content_length": 50})
        processing_context.parsed_document = ParsedDocument(
            title="Test",
            content="A" * 1000,  # Very long content
        )

        enricher.process(processing_context, observability_context)

        # Check that truncated content was passed to LLM
        call_args = mock_llm_client.chat.call_args[0][0]
        assert "...(内容已截断)" in call_args

    def test_process_handles_llm_error(
        self, enricher, processing_context, observability_context, mock_llm_client
    ):
        """Test handling of LLM errors."""
        mock_llm_client.chat.side_effect = [
            Exception("LLM error"),
            "Success answer",
        ]

        result = enricher.process(processing_context, observability_context)

        full_answer_data = result.get_enrichment("full_answer")
        assert full_answer_data["total_count"] == 2
        assert full_answer_data["success_count"] == 1

        # First answer should have error
        assert full_answer_data["answers"][0]["full_answer"] == ""
        assert "error" in full_answer_data["answers"][0]

    def test_process_with_empty_qa_pairs(
        self, enricher, processing_context, observability_context
    ):
        """Test handling of empty QA pairs."""
        processing_context.set_enrichment("qa", {
            "chunk_qa": [
                {
                    "chunk_id": "chunk-1",
                    "summary": "Summary",
                    "qa_pairs": [],
                },
            ],
            "total_qa_pairs": 0,
        })

        result = enricher.process(processing_context, observability_context)

        full_answer_data = result.get_enrichment("full_answer")
        assert full_answer_data["total_count"] == 0
