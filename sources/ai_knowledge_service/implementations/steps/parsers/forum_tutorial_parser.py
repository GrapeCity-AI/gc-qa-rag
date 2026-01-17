"""
Forum Tutorial Parser - Parser for forum tutorial thread data.

Parses forum tutorial threads from ForumApiConnector,
extracting the tutorial content for chunking and QA generation.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from ai_knowledge_service.abstractions.pipelines.steps import (
    IContentParser,
    ParsedDocument,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext


class ForumTutorialParser(IContentParser):
    """
    Forum Tutorial Parser - Parses forum tutorial thread data.

    Unlike ForumQAParser which focuses on Q&A threads,
    this parser treats the thread as a tutorial article:
    - Author content is the main article body
    - Title and forum name are prepended for context
    - Output is suitable for chunking and QA generation
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the parser.

        Args:
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._config: Dict[str, Any] = {}

    @property
    def step_type(self) -> str:
        """Get the step type identifier."""
        return "forum_tutorial_parser"

    @property
    def supported_mime_types(self) -> List[str]:
        """Get list of supported MIME types."""
        return ["application/json"]

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the parser.

        Config options:
        - include_title_header: bool - Prepend forum name and title (default: True)
        - strip_html: bool - Strip HTML tags from content (default: True)
        """
        self._config = config
        self._logger.debug(f"Configured with: {config}")

    def process(
        self,
        context: ProcessingContext,
        observability: ObservabilityContext,
    ) -> ProcessingContext:
        """
        Parse forum tutorial thread into a structured document.

        Args:
            context: Processing context with raw_file.
            observability: Observability context for metrics/tracing.

        Returns:
            Updated context with parsed_document set.
        """
        if context.should_skip:
            return context

        raw_file = context.raw_file

        self._logger.debug(f"Parsing forum tutorial: {raw_file.original_name}")

        try:
            # Get thread data
            thread_data = self._get_thread_data(context)
            if not thread_data:
                raise ValueError("No thread data available")

            # Extract content
            content_data = thread_data.get("content", {})
            if not content_data:
                raise ValueError("No content in thread data")

            # Get author content (main tutorial body)
            author_content = content_data.get("authorContent", "")

            # Clean HTML if configured
            if self._config.get("strip_html", True):
                author_content = self._strip_html(author_content)

            if not author_content:
                raise ValueError("Empty author content")

            # Build full content with header
            title = content_data.get("title", thread_data.get("title", ""))
            forum_name = content_data.get("forumName", "")
            full_content = self._build_full_content(
                author_content, title, forum_name
            )

            # Extract metadata
            product = thread_data.get("product", content_data.get("product", ""))
            category = self._build_category(content_data)
            url = content_data.get("url", "")
            post_date = thread_data.get("postDate", "")

            # Create parsed document
            context.parsed_document = ParsedDocument(
                title=title,
                content=full_content,
                sections=[],
                metadata={
                    "original_mime_type": raw_file.mime_type,
                    "original_name": raw_file.original_name,
                    "content_length": len(full_content),
                    "url": url,
                    "category": category,
                    "product": product,
                    "post_date": post_date,
                    "thread_id": thread_data.get("tid", ""),
                    "forum_name": forum_name,
                    "source_type": "forum_tutorial",
                },
            )

            self._logger.debug(
                f"Parsed forum tutorial: {title}, {len(full_content)} chars"
            )

        except Exception as e:
            context.add_error(
                step=self.step_type,
                error_type=type(e).__name__,
                message=f"Failed to parse {raw_file.original_name}: {e}",
                recoverable=True,
            )
            context.mark_skip(f"Parse error: {e}")
            self._logger.warning(f"Parse error for {raw_file.original_name}: {e}")

        return context

    def _get_thread_data(self, context: ProcessingContext) -> Dict[str, Any]:
        """Get thread data from context."""
        # First check metadata
        thread_data = context.raw_file.metadata.get("thread_data")
        if thread_data:
            return thread_data

        # Otherwise parse from raw_content
        if context.raw_content:
            try:
                return json.loads(context.raw_content.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                self._logger.warning(f"Failed to parse thread JSON: {e}")

        return {}

    def _build_full_content(
        self,
        author_content: str,
        title: str,
        forum_name: str,
    ) -> str:
        """Build full content with optional header."""
        if not self._config.get("include_title_header", True):
            return author_content

        # Prepend forum name and title for context
        header_parts = []
        if forum_name:
            header_parts.append(f"论坛名称：{forum_name}")
        if title:
            header_parts.append(f"标题：{title}")

        if header_parts:
            header = " ".join(header_parts)
            return f"{header}\n\n{author_content}"

        return author_content

    def _build_category(self, content_data: Dict[str, Any]) -> str:
        """Build category string from forum metadata."""
        forum_name = content_data.get("forumName", "")
        thread_tag = content_data.get("threadTag", "")

        if forum_name and thread_tag:
            return f"{forum_name}-{thread_tag}"
        return forum_name or thread_tag or ""

    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content."""
        if not html_content:
            return ""

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            # Normalize whitespace
            text = re.sub(r"\n\s*\n", "\n\n", text)
            return text.strip()
        except Exception:
            # Fallback: simple regex strip
            return re.sub(r"<[^>]+>", "", html_content).strip()
