"""
HTML Parser - Content parser for HTML documents.

Extracts main content from HTML pages using configurable selectors.
Designed for documentation sites crawled via SitemapConnector.
"""

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


class HtmlParser(IContentParser):
    """
    HTML Parser - Extracts main content from HTML documents.

    Features:
    - Configurable content selectors (class, id)
    - Title extraction
    - Category extraction from breadcrumb
    - HTML to text conversion with proper whitespace handling
    """

    DEFAULT_CONTENT_SELECTORS = [
        {"class": "main__doc"},
        {"class": "doc-content"},
        {"class": "content"},
        {"id": "content"},
        {"tag": "main"},
        {"tag": "article"},
    ]

    DEFAULT_TITLE_SELECTORS = [
        {"id": "site_main_content-doc-content_title"},
        {"tag": "h1"},
        {"class": "title"},
    ]

    DEFAULT_BREADCRUMB_SELECTORS = [
        {"class": "nav__breadcrumb-items"},
        {"class": "breadcrumb"},
    ]

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
        return "html_parser"

    @property
    def supported_mime_types(self) -> List[str]:
        """Get list of supported MIME types."""
        return ["text/html", "application/xhtml+xml"]

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the parser.

        Config options:
        - content_selectors: List[dict] - Selectors for main content
        - title_selectors: List[dict] - Selectors for title
        - breadcrumb_selectors: List[dict] - Selectors for breadcrumb/category
        - extract_title: bool - Extract title (default: True)
        - extract_category: bool - Extract category (default: True)
        """
        self._config = config
        self._logger.debug(f"Configured with: {config}")

    def process(
        self,
        context: ProcessingContext,
        observability: ObservabilityContext,
    ) -> ProcessingContext:
        """
        Parse HTML content into a structured document.

        Args:
            context: Processing context with raw_file.
            observability: Observability context for metrics/tracing.

        Returns:
            Updated context with parsed_document set.
        """
        if context.should_skip:
            return context

        raw_file = context.raw_file

        self._logger.debug(
            f"Parsing HTML: {raw_file.original_name} ({raw_file.mime_type})"
        )

        try:
            # Get HTML content
            html_content = self._get_html_content(context)
            if not html_content:
                raise ValueError("No HTML content available")

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract main content
            main_content = self._extract_main_content(soup)
            if not main_content:
                self._logger.warning(
                    f"No main content found for {raw_file.original_name}"
                )
                main_content = soup.get_text(separator="\n", strip=True)

            # Extract title
            title = self._extract_title(soup, raw_file.original_name)

            # Extract category
            category = self._extract_category(soup)

            # Get URL from metadata if available
            url = raw_file.metadata.get("url", "")

            # Create parsed document
            context.parsed_document = ParsedDocument(
                title=title,
                content=main_content,
                sections=[],
                metadata={
                    "original_mime_type": raw_file.mime_type,
                    "original_name": raw_file.original_name,
                    "content_length": len(main_content),
                    "url": url,
                    "category": category,
                    "product": raw_file.metadata.get("product", ""),
                },
            )

            self._logger.debug(
                f"Parsed HTML: {title}, category={category}, {len(main_content)} chars"
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

    def _get_html_content(self, context: ProcessingContext) -> str:
        """Get HTML content from context."""
        # First check if HTML is in raw_file metadata (from SitemapConnector)
        html_content = context.raw_file.metadata.get("content_html", "")
        if html_content:
            return html_content

        # Otherwise decode from raw_content
        if context.raw_content:
            try:
                return context.raw_content.decode("utf-8")
            except UnicodeDecodeError:
                return context.raw_content.decode("latin-1")

        return ""

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML."""
        selectors = self._config.get(
            "content_selectors", self.DEFAULT_CONTENT_SELECTORS
        )

        for selector in selectors:
            element = self._find_element(soup, selector)
            if element:
                return self._element_to_text(element)

        return ""

    def _extract_title(self, soup: BeautifulSoup, fallback: str) -> str:
        """Extract title from HTML."""
        if not self._config.get("extract_title", True):
            return fallback

        selectors = self._config.get("title_selectors", self.DEFAULT_TITLE_SELECTORS)

        for selector in selectors:
            element = self._find_element(soup, selector)
            if element:
                return element.get_text(strip=True)

        # Try <title> tag
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        return fallback

    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract category from breadcrumb."""
        if not self._config.get("extract_category", True):
            return ""

        selectors = self._config.get(
            "breadcrumb_selectors", self.DEFAULT_BREADCRUMB_SELECTORS
        )

        for selector in selectors:
            element = self._find_element(soup, selector)
            if element:
                text = element.get_text(separator="/", strip=True)
                # Clean up consecutive slashes/newlines
                text = self._replace_consecutive_newlines(text).strip("/")
                # Remove last part (current page) if present
                if "/" in text:
                    text = text.rsplit("/", 1)[0]
                return text

        return ""

    def _find_element(self, soup: BeautifulSoup, selector: Dict[str, str]):
        """Find element using selector dict."""
        if "id" in selector:
            return soup.find(id=selector["id"])
        if "class" in selector:
            return soup.find(class_=selector["class"])
        if "tag" in selector:
            return soup.find(selector["tag"])
        return None

    def _element_to_text(self, element) -> str:
        """Convert HTML element to clean text."""
        # Get text with proper spacing
        text = element.get_text(separator="\n", strip=True)
        # Normalize whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    @staticmethod
    def _replace_consecutive_newlines(s: str) -> str:
        """Replace consecutive newlines with a single forward slash."""
        return re.sub(r"\n+", "/", s)
