"""
Tests for ForumQAParser and ForumTutorialParser.
"""

import json
import pytest
from unittest.mock import MagicMock

from ai_knowledge_service.abstractions.pipelines.steps import ProcessingContext
from ai_knowledge_service.abstractions.models.raw_file import RawFile, LifecycleStatus
from ai_knowledge_service.abstractions.models.knowledge_base import FileVersion, IndexStatus
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
from ai_knowledge_service.abstractions.models.tasks import TaskType
from ai_knowledge_service.implementations.steps.parsers import (
    ForumQAParser,
    ForumTutorialParser,
)


def create_test_raw_file(
    thread_data: dict, source_uri: str, metadata: dict = None
) -> RawFile:
    """Create a test RawFile."""
    content_bytes = json.dumps(thread_data).encode("utf-8")
    return RawFile(
        id="test-file",
        knowledge_base_id="test-kb",
        source_type="forum_api",
        source_uri=source_uri,
        original_name=f"{source_uri}.json",
        content_hash="abc123",
        storage_path="/tmp/thread.json",
        mime_type="application/json",
        size_bytes=len(content_bytes),
        metadata=metadata or {},
        lifecycle_status=LifecycleStatus.ACTIVE,
    )


def create_test_context(thread_data: dict, source_uri: str, metadata: dict = None) -> ProcessingContext:
    """Create a test processing context."""
    content_bytes = json.dumps(thread_data).encode("utf-8")
    raw_file = create_test_raw_file(thread_data, source_uri, metadata)

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
    context.raw_content = content_bytes
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
def sample_thread_data():
    """Sample forum thread data."""
    return {
        "tid": "12345",
        "title": "How to solve this problem?",
        "postDate": 1609459200,
        "product": "Forguncy",
        "content": {
            "title": "How to solve this problem?",
            "url": "https://forum.example.com/thread/12345",
            "forumName": "Technical Support",
            "threadTag": "Question",
            "product": "Forguncy",
            "authorContent": "<p>I have a problem with my application.</p><p>How can I fix it?</p>",
            "replies": [
                {
                    "author": "Expert User",
                    "content": "<p>You can try this solution...</p>",
                },
                {
                    "author": "Support Team",
                    "content": "<p>Here is the official guide...</p>",
                },
            ],
        },
    }


@pytest.fixture
def processing_context(sample_thread_data):
    """Create a ProcessingContext with thread data."""
    return create_test_context(
        sample_thread_data,
        "Forguncy_QA_12345",
        metadata={
            "thread_data": sample_thread_data,
            "product": "Forguncy",
            "section": "QA",
        }
    )


@pytest.fixture
def observability_context():
    """Create an ObservabilityContext."""
    return create_obs_context()


class TestForumQAParser:
    """Tests for ForumQAParser."""

    @pytest.fixture
    def parser(self):
        """Create a ForumQAParser instance."""
        return ForumQAParser()

    def test_step_type(self, parser):
        """Test step type identifier."""
        assert parser.step_type == "forum_qa_parser"

    def test_supported_mime_types(self, parser):
        """Test supported MIME types."""
        assert "application/json" in parser.supported_mime_types

    def test_configure(self, parser):
        """Test configuration."""
        config = {"include_replies": False}
        parser.configure(config)
        assert parser._config == config

    def test_process_extracts_title(
        self, parser, processing_context, observability_context
    ):
        """Test that process extracts title correctly."""
        result = parser.process(processing_context, observability_context)

        assert result.parsed_document is not None
        assert result.parsed_document.title == "How to solve this problem?"

    def test_process_extracts_question_content(
        self, parser, processing_context, observability_context
    ):
        """Test that process extracts question content."""
        result = parser.process(processing_context, observability_context)

        assert result.parsed_document is not None
        content = result.parsed_document.content
        assert "问题：" in content
        assert "I have a problem with my application" in content

    def test_process_includes_replies(
        self, parser, processing_context, observability_context
    ):
        """Test that process includes replies."""
        result = parser.process(processing_context, observability_context)

        content = result.parsed_document.content
        assert "回复" in content
        assert "You can try this solution" in content
        assert "official guide" in content

    def test_process_respects_include_replies_config(
        self, parser, processing_context, observability_context
    ):
        """Test that include_replies config is respected."""
        parser.configure({"include_replies": False})
        result = parser.process(processing_context, observability_context)

        content = result.parsed_document.content
        assert "回复" not in content

    def test_process_respects_max_replies_config(
        self, parser, processing_context, observability_context
    ):
        """Test that max_replies config is respected."""
        parser.configure({"max_replies": 1})
        result = parser.process(processing_context, observability_context)

        content = result.parsed_document.content
        assert "You can try this solution" in content
        assert "official guide" not in content

    def test_process_extracts_metadata(
        self, parser, processing_context, observability_context
    ):
        """Test that process extracts metadata correctly."""
        result = parser.process(processing_context, observability_context)

        metadata = result.parsed_document.metadata
        assert metadata["url"] == "https://forum.example.com/thread/12345"
        assert metadata["product"] == "Forguncy"
        assert metadata["category"] == "Technical Support-Question"
        assert metadata["thread_id"] == "12345"
        assert metadata["source_type"] == "forum_qa"

    def test_process_strips_html(
        self, parser, processing_context, observability_context
    ):
        """Test that HTML is stripped from content."""
        result = parser.process(processing_context, observability_context)

        content = result.parsed_document.content
        assert "<p>" not in content
        assert "</p>" not in content

    def test_process_skips_when_should_skip(
        self, parser, processing_context, observability_context
    ):
        """Test that process respects should_skip flag."""
        processing_context.mark_skip("Skip reason")
        result = parser.process(processing_context, observability_context)
        assert result.should_skip is True

    def test_process_handles_missing_content(
        self, parser, observability_context
    ):
        """Test handling when thread content is missing."""
        context = create_test_context(
            {"tid": "123"},
            "test.json",
            metadata={"thread_data": {"tid": "123"}}
        )

        result = parser.process(context, observability_context)

        assert result.should_skip is True
        assert len(result.errors) > 0


class TestForumTutorialParser:
    """Tests for ForumTutorialParser."""

    @pytest.fixture
    def parser(self):
        """Create a ForumTutorialParser instance."""
        return ForumTutorialParser()

    @pytest.fixture
    def tutorial_thread_data(self):
        """Sample tutorial thread data."""
        return {
            "tid": "67890",
            "title": "Complete Guide to Feature X",
            "postDate": 1609459200,
            "product": "Wyn",
            "content": {
                "title": "Complete Guide to Feature X",
                "url": "https://forum.example.com/thread/67890",
                "forumName": "Tutorials",
                "threadTag": "Guide",
                "product": "Wyn",
                "authorContent": "<h2>Introduction</h2><p>This tutorial explains Feature X.</p><h2>Step 1</h2><p>First, do this...</p>",
            },
        }

    @pytest.fixture
    def tutorial_context(self, tutorial_thread_data):
        """Create a ProcessingContext with tutorial thread data."""
        return create_test_context(
            tutorial_thread_data,
            "Wyn_Tutorial_67890",
            metadata={
                "thread_data": tutorial_thread_data,
                "product": "Wyn",
                "section": "Tutorial",
            }
        )

    def test_step_type(self, parser):
        """Test step type identifier."""
        assert parser.step_type == "forum_tutorial_parser"

    def test_process_extracts_title(
        self, parser, tutorial_context, observability_context
    ):
        """Test that process extracts title correctly."""
        result = parser.process(tutorial_context, observability_context)

        assert result.parsed_document is not None
        assert result.parsed_document.title == "Complete Guide to Feature X"

    def test_process_extracts_tutorial_content(
        self, parser, tutorial_context, observability_context
    ):
        """Test that process extracts tutorial content."""
        result = parser.process(tutorial_context, observability_context)

        content = result.parsed_document.content
        assert "Introduction" in content
        assert "This tutorial explains Feature X" in content
        assert "Step 1" in content

    def test_process_includes_header(
        self, parser, tutorial_context, observability_context
    ):
        """Test that process includes forum name and title header."""
        result = parser.process(tutorial_context, observability_context)

        content = result.parsed_document.content
        assert "论坛名称：Tutorials" in content
        assert "标题：Complete Guide to Feature X" in content

    def test_process_respects_header_config(
        self, parser, tutorial_context, observability_context
    ):
        """Test that include_title_header config is respected."""
        parser.configure({"include_title_header": False})
        result = parser.process(tutorial_context, observability_context)

        content = result.parsed_document.content
        assert "论坛名称" not in content

    def test_process_extracts_metadata(
        self, parser, tutorial_context, observability_context
    ):
        """Test that process extracts metadata correctly."""
        result = parser.process(tutorial_context, observability_context)

        metadata = result.parsed_document.metadata
        assert metadata["url"] == "https://forum.example.com/thread/67890"
        assert metadata["product"] == "Wyn"
        assert metadata["category"] == "Tutorials-Guide"
        assert metadata["forum_name"] == "Tutorials"
        assert metadata["source_type"] == "forum_tutorial"

    def test_process_strips_html(
        self, parser, tutorial_context, observability_context
    ):
        """Test that HTML is stripped from content."""
        result = parser.process(tutorial_context, observability_context)

        content = result.parsed_document.content
        assert "<h2>" not in content
        assert "<p>" not in content
