"""
Vector Index Builder - Builds index records from embeddings and enrichments.

Assembles the final index records that will be written to vector storage.
Each QA pair produces one IndexRecord with 4 vectors:
- question_dense
- answer_dense
- question_sparse
- answer_sparse
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ai_knowledge_service.abstractions.models.index import IndexRecord
from ai_knowledge_service.abstractions.pipelines.steps import (
    Embedding,
    IIndexBuilder,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext


class VectorIndexBuilder(IIndexBuilder):
    """
    Vector Index Builder - Builds index records for vector storage.

    Combines:
    - Question embeddings (dense and sparse vectors)
    - Answer embeddings (dense and sparse vectors)
    - QA data (questions and answers)
    - Document metadata

    Into IndexRecord objects ready for storage, with each QA pair
    producing one record containing all 4 vectors.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the index builder.

        Args:
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._config: Dict[str, Any] = {}

    @property
    def step_type(self) -> str:
        """Get the step type identifier."""
        return "vector_index_builder"

    @property
    def index_type(self) -> str:
        """Get the type of index built."""
        return "vector"

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the index builder.

        Config options:
        - include_metadata: bool - Include document metadata (default: True)
        - include_chunk_content: bool - Include chunk text (default: True)
        """
        self._config = config
        self._logger.debug(f"Configured with: {config}")

    def process(
        self,
        context: ProcessingContext,
        observability: ObservabilityContext,
    ) -> ProcessingContext:
        """
        Build index records from processed data.

        Each QA pair produces one IndexRecord with 4 vectors:
        - question_dense, answer_dense (dense embeddings)
        - question_sparse, answer_sparse (sparse embeddings)

        Args:
            context: Processing context with embeddings and enrichments.
            observability: Observability context for metrics/tracing.

        Returns:
            Updated context with index_records.
        """
        if context.should_skip:
            return context

        if context.embeddings is None or len(context.embeddings) == 0:
            context.add_error(
                step=self.step_type,
                error_type="MissingInput",
                message="No embeddings available for index building",
                recoverable=True,
            )
            context.mark_skip("No embeddings")
            return context

        try:
            # Get configuration options
            include_metadata = self._config.get("include_metadata", True)
            include_chunk_content = self._config.get("include_chunk_content", True)

            # Build a map of chunk_id to chunk data
            chunk_map = {}
            if context.chunks:
                chunk_map = {chunk.id: chunk for chunk in context.chunks}

            # Get QA enrichment data
            qa_data = context.get_enrichment("qa", {})
            chunk_qa_list = qa_data.get("chunk_qa", [])
            chunk_qa_map = {
                cqa["chunk_id"]: cqa
                for cqa in chunk_qa_list
            }

            # Get full answer enrichment data
            full_answer_data = context.get_enrichment("full_answer", {})
            full_answers = full_answer_data.get("answers", []) if full_answer_data else []
            # Build map: (chunk_id, qa_index) -> full_answer
            full_answer_map = {}
            for fa in full_answers:
                key = (fa.get("chunk_id", ""), fa.get("qa_index", 0))
                full_answer_map[key] = fa.get("full_answer", "")

            # Group embeddings by (chunk_id, qa_index) to combine Q and A
            embedding_groups = self._group_embeddings(context.embeddings)

            # Build index records
            index_records: List[IndexRecord] = []

            for (chunk_id, qa_index), emb_pair in embedding_groups.items():
                question_emb = emb_pair.get("question")
                answer_emb = emb_pair.get("answer")

                # Skip if we don't have both question and answer embeddings
                if not question_emb or not answer_emb:
                    self._logger.warning(
                        f"Incomplete embedding pair for chunk {chunk_id}, qa {qa_index}: "
                        f"question={question_emb is not None}, answer={answer_emb is not None}"
                    )
                    continue

                # Get related data
                chunk = chunk_map.get(chunk_id)
                chunk_qa = chunk_qa_map.get(chunk_id, {})

                # Build record content with all 4 vectors
                content: Dict[str, Any] = {
                    "question_dense": question_emb.vector,
                    "answer_dense": answer_emb.vector,
                }

                # Add sparse vectors if available
                if question_emb.sparse_vector:
                    content["question_sparse"] = question_emb.sparse_vector
                if answer_emb.sparse_vector:
                    content["answer_sparse"] = answer_emb.sparse_vector

                # Build payload (searchable/filterable data)
                # Includes all fields from original implementation plus new fields
                question_text = question_emb.metadata.get("text", "")
                answer_text = answer_emb.metadata.get("text", "")

                # Get metadata from raw_file
                raw_metadata = context.raw_file.metadata or {}
                product = raw_metadata.get("product", "")
                category = raw_metadata.get("category", "")
                title = raw_metadata.get("title", "")

                # Fallback title to parsed_document.title
                if not title and context.parsed_document:
                    title = context.parsed_document.title or ""

                # Build file_index from raw_file (remove extension, use original name)
                file_name = context.raw_file.original_name or ""
                file_index = file_name.rsplit(".", 1)[0] if "." in file_name else file_name

                # Get group_index from chunk metadata
                group_index = 0
                if chunk:
                    group_index = chunk.metadata.get("group_index", chunk.index)

                # Build URL in original format: /api/raw_file/{product}/{filename}
                url = raw_metadata.get("url", "")
                if not url and product and file_name:
                    # Remove hash suffix if present (format: xxx_xxxxxxxx -> xxx)
                    original_filename = file_index
                    if "_" in original_filename:
                        parts = original_filename.split("_")
                        # Check if last part looks like a hash (8+ chars, alphanumeric)
                        if len(parts[-1]) >= 8 and parts[-1].isalnum():
                            original_filename = "_".join(parts[:-1])
                    url = f"/api/raw_file/{product}/{original_filename}"

                payload: Dict[str, Any] = {
                    # Original implementation fields (required)
                    "file_index": file_index,
                    "group_index": group_index,
                    "question_index": qa_index,
                    "product": product,
                    "url": url,
                    "title": title,
                    "category": category,
                    "summary": chunk_qa.get("summary", ""),
                    "question": question_text,
                    "answer": answer_text,
                    "full_answer": full_answer_map.get((chunk_id, qa_index), ""),

                    # New implementation additional fields
                    "chunk_id": chunk_id,
                    "qa_index": qa_index,  # Same as question_index, kept for compatibility
                    "document_title": context.parsed_document.title if context.parsed_document else "",
                    "file_name": file_name,
                    "source_uri": context.raw_file.source_uri or "",
                }

                # Add chunk content if configured
                if include_chunk_content and chunk:
                    payload["chunk_content"] = chunk.content[:1000]  # Limit size

                # Create index record
                record = IndexRecord(
                    id=str(uuid.uuid4()),
                    file_version_id=context.file_version.id,
                    index_type=self.index_type,
                    content=content,
                    payload=payload,
                )

                index_records.append(record)

            context.index_records = index_records

            self._logger.info(
                f"Built {len(index_records)} index records from "
                f"{len(context.embeddings)} embeddings ({len(embedding_groups)} QA pairs)"
            )

        except Exception as e:
            context.add_error(
                step=self.step_type,
                error_type=type(e).__name__,
                message=f"Failed to build index records: {e}",
                recoverable=True,
            )
            context.mark_skip(f"Index build error: {e}")
            self._logger.error(f"Index build error: {e}")

        return context

    def _group_embeddings(
        self,
        embeddings: List[Embedding],
    ) -> Dict[Tuple[str, int], Dict[str, Embedding]]:
        """
        Group embeddings by (chunk_id, qa_index) to pair question and answer.

        Args:
            embeddings: List of embeddings to group.

        Returns:
            Dict mapping (chunk_id, qa_index) to {"question": Embedding, "answer": Embedding}
        """
        groups: Dict[Tuple[str, int], Dict[str, Embedding]] = {}

        for emb in embeddings:
            chunk_id = emb.chunk_id
            emb_type = emb.metadata.get("type", "unknown")
            qa_index = emb.metadata.get("index", 0)

            key = (chunk_id, qa_index)

            if key not in groups:
                groups[key] = {}

            if emb_type in ("question", "answer"):
                groups[key][emb_type] = emb

        return groups
