"""
Tests for HtmlParser.
"""

import pytest
from unittest.mock import MagicMock

from ai_knowledge_service.abstractions.pipelines.steps import ProcessingContext
from ai_knowledge_service.abstractions.models.raw_file import RawFile, LifecycleStatus
from ai_knowledge_service.abstractions.models.knowledge_base import FileVersion, IndexStatus
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
from ai_knowledge_service.abstractions.models.tasks import TaskType
from ai_knowledge_service.implementations.steps.parsers import HtmlParser


def create_test_raw_file(html_content: str, metadata: dict = None) -> RawFile:
    """Create a test RawFile."""
    return RawFile(
        id="test-file",
        knowledge_base_id="test-kb",
        source_type="sitemap",
        source_uri="https://example.com/docs/getting-started",
        original_name="getting-started.html",
        content_hash="abc123",
        storage_path="/tmp/test.html",
        mime_type="text/html",
        size_bytes=len(html_content.encode()),
        metadata=metadata or {},
        lifecycle_status=LifecycleStatus.ACTIVE,
    )


def create_test_context(html_content: str, metadata: dict = None) -> ProcessingContext:
    """Create a test processing context."""
    raw_file = create_test_raw_file(html_content, metadata)

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
    context.raw_content = html_content.encode("utf-8")
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
def parser():
    """Create an HtmlParser instance."""
    return HtmlParser()


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page Title</title>
    </head>
    <body>
        <nav class="nav__breadcrumb-items">
            Home / Docs / Getting Started
        </nav>
        <h1 id="site_main_content-doc-content_title">Getting Started Guide</h1>
        <div class="main__doc">
            <p>This is the main content of the document.</p>
            <p>It contains multiple paragraphs.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def processing_context(sample_html):
    """Create a ProcessingContext with HTML content."""
    return create_test_context(
        sample_html,
        metadata={
            "url": "https://example.com/docs/getting-started",
            "product": "TestProduct",
            "content_html": sample_html,
        }
    )


@pytest.fixture
def observability_context():
    """Create an ObservabilityContext."""
    return create_obs_context()


class TestHtmlParser:
    """Tests for HtmlParser."""

    def test_step_type(self, parser):
        """Test step type identifier."""
        assert parser.step_type == "html_parser"

    def test_supported_mime_types(self, parser):
        """Test supported MIME types."""
        assert "text/html" in parser.supported_mime_types
        assert "application/xhtml+xml" in parser.supported_mime_types

    def test_configure(self, parser):
        """Test configuration."""
        config = {"extract_title": False}
        parser.configure(config)
        assert parser._config == config

    def test_process_extracts_main_content(
        self, parser, processing_context, observability_context
    ):
        """Test that process extracts main content correctly."""
        result = parser.process(processing_context, observability_context)

        assert result.parsed_document is not None
        assert "This is the main content" in result.parsed_document.content
        assert "multiple paragraphs" in result.parsed_document.content

    def test_process_extracts_title(
        self, parser, processing_context, observability_context
    ):
        """Test that process extracts title correctly."""
        result = parser.process(processing_context, observability_context)

        assert result.parsed_document is not None
        assert result.parsed_document.title == "Getting Started Guide"

    def test_process_extracts_category(
        self, parser, processing_context, observability_context
    ):
        """Test that process extracts category from breadcrumb."""
        result = parser.process(processing_context, observability_context)

        assert result.parsed_document is not None
        # Category should be the breadcrumb path minus the last item
        category = result.parsed_document.metadata.get("category", "")
        assert "Home" in category or "Docs" in category

    def test_process_preserves_metadata(
        self, parser, processing_context, observability_context
    ):
        """Test that process preserves URL and product metadata."""
        result = parser.process(processing_context, observability_context)

        assert result.parsed_document is not None
        assert result.parsed_document.metadata["url"] == "https://example.com/docs/getting-started"
        assert result.parsed_document.metadata["product"] == "TestProduct"

    def test_process_skips_when_should_skip(
        self, parser, processing_context, observability_context
    ):
        """Test that process respects should_skip flag."""
        processing_context.mark_skip("Skip reason")
        result = parser.process(processing_context, observability_context)
        assert result.should_skip is True
        assert result.parsed_document is None

    def test_process_handles_missing_main_content(
        self, parser, observability_context
    ):
        """Test handling when main content selector doesn't match."""
        html = "<html><body><div>No main__doc class</div></body></html>"
        context = create_test_context(html, {"content_html": html})

        result = parser.process(context, observability_context)

        # Should fall back to full page text
        assert result.parsed_document is not None
        assert "No main__doc class" in result.parsed_document.content

    def test_process_with_custom_selectors(
        self, parser, observability_context
    ):
        """Test with custom content selectors."""
        html = '<html><body><div class="custom-content">Custom content here</div></body></html>'
        context = create_test_context(html, {"content_html": html})

        parser.configure({
            "content_selectors": [{"class": "custom-content"}],
        })

        result = parser.process(context, observability_context)

        assert result.parsed_document is not None
        assert "Custom content here" in result.parsed_document.content

    def test_process_handles_empty_html(
        self, parser, observability_context
    ):
        """Test handling of empty HTML content."""
        context = create_test_context("", {})
        context.raw_content = b""

        result = parser.process(context, observability_context)

        # Should add error and skip
        assert result.should_skip is True
        assert len(result.errors) > 0
