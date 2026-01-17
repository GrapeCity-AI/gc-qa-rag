"""
Vector Index Builder - Builds index records from embeddings and enrichments.

Assembles the final index records that will be written to vector storage.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from ai_knowledge_service.abstractions.models.index import IndexRecord
from ai_knowledge_service.abstractions.pipelines.steps import (
    IIndexBuilder,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext


class VectorIndexBuilder(IIndexBuilder):
    """
    Vector Index Builder - Builds index records for vector storage.

    Combines:
    - Embeddings (dense and sparse vectors)
    - QA data (questions and answers)
    - Document metadata

    Into IndexRecord objects ready for storage.
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

            # Build index records
            index_records: List[IndexRecord] = []

            for embedding in context.embeddings:
                chunk_id = embedding.chunk_id
                emb_type = embedding.metadata.get("type", "unknown")

                # Get related data
                chunk = chunk_map.get(chunk_id)
                chunk_qa = chunk_qa_map.get(chunk_id, {})

                # Build record content (vectors)
                content: Dict[str, Any] = {}

                # Add dense vector based on embedding type
                if emb_type == "question":
                    content["question_dense"] = embedding.vector
                elif emb_type == "answer":
                    content["answer_dense"] = embedding.vector
                else:
                    content["dense_vector"] = embedding.vector

                # Add sparse vector if available
                if embedding.sparse_vector:
                    if emb_type == "question":
                        content["question_sparse"] = embedding.sparse_vector
                    elif emb_type == "answer":
                        content["answer_sparse"] = embedding.sparse_vector
                    else:
                        content["sparse_vector"] = embedding.sparse_vector

                # Build payload (searchable/filterable data)
                payload: Dict[str, Any] = {
                    "chunk_id": chunk_id,
                    "embedding_type": emb_type,
                }

                # Add text content
                if emb_type == "question":
                    payload["question"] = embedding.metadata.get("text", "")
                    payload["answer"] = embedding.metadata.get("answer", "")
                elif emb_type == "answer":
                    payload["answer"] = embedding.metadata.get("text", "")
                    payload["question"] = embedding.metadata.get("question", "")

                # Add chunk content if configured
                if include_chunk_content and chunk:
                    payload["chunk_content"] = chunk.content[:1000]  # Limit size

                # Add summary if available
                summary = chunk_qa.get("summary", "")
                if summary:
                    payload["summary"] = summary

                # Add document metadata if configured
                if include_metadata:
                    payload["document_title"] = ""
                    if context.parsed_document:
                        payload["document_title"] = context.parsed_document.title
                    payload["file_name"] = context.raw_file.original_name
                    payload["source_uri"] = context.raw_file.source_uri

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

            self._logger.debug(
                f"Built {len(index_records)} index records from "
                f"{len(context.embeddings)} embeddings"
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
