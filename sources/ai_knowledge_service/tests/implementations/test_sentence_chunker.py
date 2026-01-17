"""
Tests for Sentence Chunker.
"""

from unittest.mock import Mock

import pytest

from ai_knowledge_service.abstractions.pipelines.steps import (
    ParsedDocument,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.models.raw_file import RawFile, LifecycleStatus
from ai_knowledge_service.abstractions.models.knowledge_base import FileVersion, IndexStatus
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
from ai_knowledge_service.abstractions.models.tasks import TaskType
from ai_knowledge_service.implementations.steps.chunkers.sentence_chunker import (
    SentenceChunker,
)


def create_test_context(content: str) -> ProcessingContext:
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

    return context


def create_obs_context() -> ObservabilityContext:
    """Create a test observability context."""
    return ObservabilityContext.create(
        task_id="test-task",
        task_type=TaskType.INDEXING,
        knowledge_base_id="test-kb",
        knowledge_base_version_id="test-kb-version",
    )


class TestSentenceChunker:
    """Tests for SentenceChunker."""

    def test_step_type(self):
        """Test chunker step type."""
        chunker = SentenceChunker()
        assert chunker.step_type == "sentence_chunker"

    def test_default_configuration(self):
        """Test default configuration values."""
        chunker = SentenceChunker()
        assert chunker.max_chunk_size == 2000
        assert chunker.overlap_size == 0

    def test_configure(self):
        """Test custom configuration."""
        chunker = SentenceChunker()

        chunker.configure({
            "group_size": 5,
            "min_group_size": 2,
            "max_chunk_size": 1000,
        })

        assert chunker.max_chunk_size == 1000

    def test_process_empty_content(self):
        """Test processing empty content marks skip."""
        chunker = SentenceChunker()
        chunker.configure({})

        context = create_test_context("")
        obs = create_obs_context()

        result = chunker.process(context, obs)

        assert result.should_skip
        assert len(result.errors) > 0

    def test_process_no_document(self):
        """Test processing without parsed document marks skip."""
        chunker = SentenceChunker()
        chunker.configure({})

        context = create_test_context("content")
        context.parsed_document = None
        obs = create_obs_context()

        result = chunker.process(context, obs)

        assert result.should_skip

    def test_process_chinese_sentences(self):
        """Test chunking Chinese text with period delimiter."""
        chunker = SentenceChunker()
        chunker.configure({"group_size": 2})

        content = "第一句话。第二句话。第三句话。第四句话。"
        context = create_test_context(content)
        obs = create_obs_context()

        result = chunker.process(context, obs)

        assert not result.should_skip
        assert result.chunks is not None
        assert len(result.chunks) == 2  # 4 sentences / group_size 2

    def test_process_newline_fallback(self):
        """Test chunking with newline fallback when no periods."""
        chunker = SentenceChunker()
        chunker.configure({"group_size": 2})

        content = "Line 1\nLine 2\nLine 3\nLine 4"
        context = create_test_context(content)
        obs = create_obs_context()

        result = chunker.process(context, obs)

        assert not result.should_skip
        assert result.chunks is not None
        assert len(result.chunks) == 2

    def test_chunk_ids_are_unique(self):
        """Test that chunk IDs are unique."""
        chunker = SentenceChunker()
        chunker.configure({"group_size": 2})

        content = "句子一。句子二。句子三。句子四。"
        context = create_test_context(content)
        obs = create_obs_context()

        result = chunker.process(context, obs)

        ids = [chunk.id for chunk in result.chunks]
        assert len(ids) == len(set(ids))  # All unique

    def test_chunk_indices(self):
        """Test that chunk indices are sequential."""
        chunker = SentenceChunker()
        chunker.configure({"group_size": 2})

        content = "一。二。三。四。"
        context = create_test_context(content)
        obs = create_obs_context()

        result = chunker.process(context, obs)

        indices = [chunk.index for chunk in result.chunks]
        assert indices == [0, 1]

    def test_small_last_group_merged(self):
        """Test that small last groups are merged with previous."""
        chunker = SentenceChunker()
        chunker.configure({
            "group_size": 3,
            "min_group_size": 2,
        })

        # 4 sentences: groups of 3+1, but 1 is too small, so merge
        content = "一。二。三。四。"
        context = create_test_context(content)
        obs = create_obs_context()

        result = chunker.process(context, obs)

        # Should result in one chunk (3+1 merged)
        assert len(result.chunks) == 1

    def test_skip_already_skipped_context(self):
        """Test that already skipped context is returned unchanged."""
        chunker = SentenceChunker()
        chunker.configure({})

        context = create_test_context("content")
        context.mark_skip("previous error")
        obs = create_obs_context()

        result = chunker.process(context, obs)

        assert result.should_skip
        assert result.skip_reason == "previous error"

    def test_large_chunk_split(self):
        """Test that chunks exceeding max size are split."""
        chunker = SentenceChunker()
        chunker.configure({
            "group_size": 100,  # Large to get one group
            "max_chunk_size": 50,  # Small to force split
        })

        # Create content longer than max_chunk_size
        content = "这是一个很长的句子" * 10 + "。"  # About 91 chars
        context = create_test_context(content)
        obs = create_obs_context()

        result = chunker.process(context, obs)

        assert not result.should_skip
        assert result.chunks is not None
        # Content should be split into multiple chunks
        assert len(result.chunks) >= 2
