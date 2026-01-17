"""
MarkItDown Parser - Content parser using the MarkItDown library.

Parses various document formats (PDF, DOCX, PPTX, etc.) into Markdown text.
"""

import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from markitdown import MarkItDown

from ai_knowledge_service.abstractions.pipelines.steps import (
    IContentParser,
    ParsedDocument,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext


# Supported MIME types and their file extensions
SUPPORTED_MIME_TYPES = {
    # Documents
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    # Text formats
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/html": ".html",
    "text/csv": ".csv",
    # Other
    "application/json": ".json",
    "application/xml": ".xml",
    "text/xml": ".xml",
}


class MarkItDownParser(IContentParser):
    """
    MarkItDown Parser - Parses documents using the MarkItDown library.

    Supports multiple document formats including PDF, DOCX, PPTX, HTML,
    and various text formats. Converts them to Markdown for unified processing.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the parser.

        Args:
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._config: Dict[str, Any] = {}
        self._markitdown = MarkItDown()

    @property
    def step_type(self) -> str:
        """Get the step type identifier."""
        return "markitdown_parser"

    @property
    def supported_mime_types(self) -> List[str]:
        """Get list of supported MIME types."""
        return list(SUPPORTED_MIME_TYPES.keys())

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the parser.

        Config options:
        - extract_title: bool - Extract title from document (default: True)
        - max_content_length: int - Max content length (default: None)
        """
        self._config = config
        self._logger.debug(f"Configured with: {config}")

    def process(
        self,
        context: ProcessingContext,
        observability: ObservabilityContext,
    ) -> ProcessingContext:
        """
        Parse the raw file content into a structured document.

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
            f"Parsing file: {raw_file.original_name} ({raw_file.mime_type})"
        )

        try:
            # Check if MIME type is supported
            if raw_file.mime_type not in SUPPORTED_MIME_TYPES:
                # Try to parse anyway - MarkItDown might support it
                self._logger.warning(
                    f"Unknown MIME type: {raw_file.mime_type}, attempting parse"
                )

            # Get content from context (loaded by executor)
            if context.raw_content is None:
                raise ValueError("Raw content not loaded in context")
            content_bytes = context.raw_content

            # Parse content using MarkItDown
            parsed_content = self._parse_content(
                content_bytes,
                raw_file.mime_type,
                raw_file.original_name,
            )

            # Extract title
            title = self._extract_title(parsed_content, raw_file.original_name)

            # Apply max content length if configured
            max_length = self._config.get("max_content_length")
            if max_length and len(parsed_content) > max_length:
                parsed_content = parsed_content[:max_length]
                self._logger.debug(f"Truncated content to {max_length} chars")

            # Create parsed document
            context.parsed_document = ParsedDocument(
                title=title,
                content=parsed_content,
                sections=[],
                metadata={
                    "original_mime_type": raw_file.mime_type,
                    "original_name": raw_file.original_name,
                    "content_length": len(parsed_content),
                },
            )

            self._logger.debug(
                f"Parsed document: {title}, {len(parsed_content)} chars"
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

    def _read_content(self, storage_path: str) -> bytes:
        """Read content from storage path."""
        with open(storage_path, "rb") as f:
            return f.read()

    def _parse_content(
        self,
        content: bytes,
        mime_type: str,
        filename: str,
    ) -> str:
        """
        Parse content using MarkItDown.

        Args:
            content: Raw file content.
            mime_type: MIME type of the content.
            filename: Original filename.

        Returns:
            Parsed markdown text.
        """
        # Get appropriate extension
        extension = SUPPORTED_MIME_TYPES.get(mime_type, "")
        if not extension:
            # Try to extract from filename
            extension = Path(filename).suffix or ".txt"

        # Write to temp file (MarkItDown requires file path)
        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Parse with MarkItDown
            result = self._markitdown.convert(tmp_path)
            return result.text_content or ""
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

    def _extract_title(self, content: str, fallback: str) -> str:
        """
        Extract title from parsed content.

        Args:
            content: Parsed markdown content.
            fallback: Fallback title (e.g., filename).

        Returns:
            Extracted title or fallback.
        """
        if not self._config.get("extract_title", True):
            return fallback

        # Try to find a heading at the start
        lines = content.strip().split("\n")
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            if line.startswith("## "):
                return line[3:].strip()

        # Use filename without extension as fallback
        if fallback:
            return Path(fallback).stem

        return "Untitled"
