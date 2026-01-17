"""
Sentence Chunker - Splits documents into sentence-based chunks.

Groups sentences together for processing, using Chinese period (。) as
the primary delimiter, with fallback to newlines.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from ai_knowledge_service.abstractions.pipelines.steps import (
    Chunk,
    IChunker,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext


class SentenceChunker(IChunker):
    """
    Sentence Chunker - Groups sentences into chunks.

    Splits text by sentence delimiters and groups them together.
    Supports Chinese period (。) and English period (.) as delimiters,
    with fallback to newlines for non-sentence-delimited text.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the chunker.

        Args:
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._group_size: int = 10
        self._min_group_size: int = 5
        self._sentence_delimiter: str = "。"
        self._max_chunk_size: int = 2000
        self._overlap_size: int = 0

    @property
    def step_type(self) -> str:
        """Get the step type identifier."""
        return "sentence_chunker"

    @property
    def max_chunk_size(self) -> int:
        """Get maximum chunk size."""
        return self._max_chunk_size

    @property
    def overlap_size(self) -> int:
        """Get chunk overlap size."""
        return self._overlap_size

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the chunker.

        Config options:
        - group_size: int - Max sentences per group (default: 10)
        - min_group_size: int - Min sentences for a new group (default: 5)
        - sentence_delimiter: str - Primary delimiter (default: "。")
        - max_chunk_size: int - Max characters per chunk (default: 2000)
        - overlap_size: int - Overlap between chunks (default: 0)
        """
        self._group_size = config.get("group_size", 10)
        self._min_group_size = config.get("min_group_size", 5)
        self._sentence_delimiter = config.get("sentence_delimiter", "。")
        self._max_chunk_size = config.get("max_chunk_size", 2000)
        self._overlap_size = config.get("overlap_size", 0)

        self._logger.debug(
            f"Configured with group_size={self._group_size}, "
            f"min_group_size={self._min_group_size}, "
            f"delimiter='{self._sentence_delimiter}'"
        )

    def process(
        self,
        context: ProcessingContext,
        observability: ObservabilityContext,
    ) -> ProcessingContext:
        """
        Split the parsed document into chunks.

        Args:
            context: Processing context with parsed_document.
            observability: Observability context for metrics/tracing.

        Returns:
            Updated context with chunks set.
        """
        if context.should_skip:
            return context

        if context.parsed_document is None:
            context.add_error(
                step=self.step_type,
                error_type="MissingInput",
                message="No parsed document available for chunking",
                recoverable=False,
            )
            context.mark_skip("No parsed document")
            return context

        try:
            # Get full text content
            text = context.parsed_document.full_text

            if not text.strip():
                context.add_error(
                    step=self.step_type,
                    error_type="EmptyContent",
                    message="Document has no content to chunk",
                    recoverable=True,
                )
                context.mark_skip("Empty content")
                return context

            # Split into sentence groups
            sentence_groups = self._split_text_into_sentence_groups(text)

            # Convert groups to chunks
            chunks: List[Chunk] = []
            for i, group in enumerate(sentence_groups):
                chunk_content = self._sentence_delimiter.join(group)

                # Apply max chunk size
                if len(chunk_content) > self._max_chunk_size:
                    # Split large chunks
                    sub_chunks = self._split_large_chunk(chunk_content, i * 100)
                    chunks.extend(sub_chunks)
                else:
                    chunk_id = str(uuid.uuid4())
                    chunks.append(
                        Chunk(
                            id=chunk_id,
                            content=chunk_content,
                            index=i,
                            metadata={
                                "sentence_count": len(group),
                                "group_index": i,
                            },
                        )
                    )

            context.chunks = chunks

            self._logger.debug(
                f"Created {len(chunks)} chunks from document"
            )

        except Exception as e:
            context.add_error(
                step=self.step_type,
                error_type=type(e).__name__,
                message=f"Failed to chunk document: {e}",
                recoverable=True,
            )
            context.mark_skip(f"Chunk error: {e}")
            self._logger.warning(f"Chunking error: {e}")

        return context

    def _split_text_into_sentence_groups(
        self,
        text: str,
    ) -> List[List[str]]:
        """
        Split text into groups of sentences.

        Args:
            text: Input text to split.

        Returns:
            List of sentence groups.
        """
        if not text:
            return []

        # Try primary delimiter first
        if self._sentence_delimiter in text:
            sentences = text.split(self._sentence_delimiter)
        else:
            # Fall back to newlines
            sentences = text.split("\n")

        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        # Group sentences
        groups: List[List[str]] = []
        current_group: List[str] = []

        for sentence in sentences:
            current_group.append(sentence)

            if len(current_group) >= self._group_size:
                groups.append(current_group)
                current_group = []

        # Handle remaining sentences
        if current_group:
            if len(current_group) < self._min_group_size and groups:
                # Merge with last group if too small
                groups[-1].extend(current_group)
            else:
                groups.append(current_group)

        return groups

    def _split_large_chunk(
        self,
        content: str,
        base_index: int,
    ) -> List[Chunk]:
        """
        Split a large chunk into smaller pieces.

        Args:
            content: Content to split.
            base_index: Base index for chunk numbering.

        Returns:
            List of smaller chunks.
        """
        chunks: List[Chunk] = []
        remaining = content
        sub_index = 0

        while remaining:
            # Take up to max_chunk_size characters
            chunk_content = remaining[:self._max_chunk_size]

            # Try to break at a sentence boundary
            if len(remaining) > self._max_chunk_size:
                # Look for the last sentence delimiter
                last_delimiter = chunk_content.rfind(self._sentence_delimiter)
                if last_delimiter > 0:
                    chunk_content = chunk_content[:last_delimiter + 1]
                else:
                    # Look for last newline
                    last_newline = chunk_content.rfind("\n")
                    if last_newline > 0:
                        chunk_content = chunk_content[:last_newline]

            chunk_id = str(uuid.uuid4())
            chunks.append(
                Chunk(
                    id=chunk_id,
                    content=chunk_content.strip(),
                    index=base_index + sub_index,
                    metadata={
                        "is_split": True,
                        "split_index": sub_index,
                    },
                )
            )

            remaining = remaining[len(chunk_content):].strip()
            sub_index += 1

        return chunks
