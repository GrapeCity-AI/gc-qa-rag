"""
DashScope Embedder - Generates embeddings using DashScope API.

Supports both dense and sparse vector generation with batch processing.
"""

import logging
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Dict, Generator, List, Optional

from dashscope import TextEmbedding

from ai_knowledge_service.abstractions.pipelines.steps import (
    Embedding,
    IEmbedder,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext


@dataclass
class DashScopeConfig:
    """Configuration for DashScope embedder."""

    api_key: str
    model_name: str = "text-embedding-v4"
    dimensions: int = 1024
    batch_size: int = 10
    output_type: str = "dense&sparse"


class EmbeddingError(Exception):
    """Custom exception for embedding-related errors."""
    pass


class DashScopeEmbedder(IEmbedder):
    """
    DashScope Embedder - Generates vector embeddings using DashScope API.

    Supports:
    - Dense vector embeddings
    - Sparse vector embeddings (BM25-style)
    - Batch processing for efficiency
    - Configurable dimensions
    """

    def __init__(
        self,
        config: DashScopeConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the embedder.

        Args:
            config: DashScope configuration.
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._api_key = config.api_key
        self._model_name = config.model_name
        self._dimensions = config.dimensions
        self._batch_size = config.batch_size
        self._output_type = config.output_type
        self._config: Dict[str, Any] = {}

    @property
    def step_type(self) -> str:
        """Get the step type identifier."""
        return "dashscope_embedder"

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions

    @property
    def supports_sparse(self) -> bool:
        """Check if sparse embeddings are supported."""
        return "sparse" in self._output_type

    @property
    def model_name(self) -> str:
        """Get the embedding model name."""
        return self._model_name

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the embedder.

        Config options:
        - embed_questions: bool - Embed QA questions (default: True)
        - embed_answers: bool - Embed QA answers (default: True)
        - embed_chunks: bool - Embed original chunks (default: False)
        """
        self._config = config
        self._logger.debug(f"Configured with: {config}")

    def process(
        self,
        context: ProcessingContext,
        observability: ObservabilityContext,
    ) -> ProcessingContext:
        """
        Generate embeddings for chunks and/or QA pairs.

        Args:
            context: Processing context with chunks and enrichments.
            observability: Observability context for metrics/tracing.

        Returns:
            Updated context with embeddings.
        """
        if context.should_skip:
            return context

        if context.chunks is None or len(context.chunks) == 0:
            context.add_error(
                step=self.step_type,
                error_type="MissingInput",
                message="No chunks available for embedding",
                recoverable=True,
            )
            context.mark_skip("No chunks")
            return context

        try:
            embeddings: List[Embedding] = []

            # Get configuration options
            embed_questions = self._config.get("embed_questions", True)
            embed_answers = self._config.get("embed_answers", True)
            embed_chunks = self._config.get("embed_chunks", False)

            # Build embedding prefix from category and title
            # Format: [Category/Title] - matches original implementation
            prefix = self._build_embedding_prefix(context)

            # Get QA enrichment data
            qa_data = context.get_enrichment("qa", {})
            chunk_qa_list = qa_data.get("chunk_qa", []) if isinstance(qa_data, dict) else []

            # Build a map of chunk_id to QA data
            chunk_qa_map = {}
            for cqa in chunk_qa_list:
                if isinstance(cqa, dict) and "chunk_id" in cqa:
                    chunk_qa_map[cqa["chunk_id"]] = cqa
                else:
                    self._logger.warning(f"Invalid chunk_qa item: {type(cqa)}")

            # Collect texts to embed
            texts_to_embed: List[Dict[str, Any]] = []

            for chunk in context.chunks:
                chunk_id = chunk.id

                # Get QA data for this chunk
                chunk_qa = chunk_qa_map.get(chunk_id, {})
                if not isinstance(chunk_qa, dict):
                    self._logger.warning(f"chunk_qa is not a dict: {type(chunk_qa)}")
                    chunk_qa = {}

                qa_pairs = chunk_qa.get("qa_pairs", [])
                if not isinstance(qa_pairs, list):
                    self._logger.warning(f"qa_pairs is not a list: {type(qa_pairs)}")
                    qa_pairs = []

                # Add chunk content embedding if configured
                if embed_chunks:
                    texts_to_embed.append({
                        "text": prefix + chunk.content,
                        "chunk_id": chunk_id,
                        "type": "chunk",
                        "index": 0,
                    })

                # Add QA embeddings with prefix
                for i, qa in enumerate(qa_pairs):
                    if not isinstance(qa, dict):
                        self._logger.warning(f"qa item is not a dict: {type(qa)}")
                        continue
                    if embed_questions and qa.get("question"):
                        texts_to_embed.append({
                            "text": prefix + qa["question"],
                            "chunk_id": chunk_id,
                            "type": "question",
                            "index": i,
                            "answer": qa.get("answer", ""),
                        })
                    if embed_answers and qa.get("answer"):
                        texts_to_embed.append({
                            "text": prefix + qa["answer"],
                            "chunk_id": chunk_id,
                            "type": "answer",
                            "index": i,
                            "question": qa.get("question", ""),
                        })

            if not texts_to_embed:
                self._logger.warning("No texts to embed")
                context.embeddings = []
                return context

            # Generate embeddings in batches
            all_texts = [t["text"] for t in texts_to_embed]
            embedding_results = self._create_embeddings(all_texts)

            # Map results back to embeddings
            for i, result in enumerate(embedding_results):
                text_info = texts_to_embed[i]

                sparse_vector = None
                if "sparse_embedding" in result:
                    sparse_vector = self._convert_sparse_vector(
                        result["sparse_embedding"]
                    )

                embedding = Embedding(
                    id=str(uuid.uuid4()),
                    chunk_id=text_info["chunk_id"],
                    vector=result["embedding"],
                    sparse_vector=sparse_vector,
                    metadata={
                        "type": text_info["type"],
                        "index": text_info["index"],
                        "text": text_info["text"][:200],  # Truncate for metadata
                        "question": text_info.get("question", ""),
                        "answer": text_info.get("answer", ""),
                    },
                )
                embeddings.append(embedding)

            context.embeddings = embeddings

            self._logger.debug(
                f"Generated {len(embeddings)} embeddings for {len(context.chunks)} chunks"
            )

        except Exception as e:
            context.add_error(
                step=self.step_type,
                error_type=type(e).__name__,
                message=f"Failed to generate embeddings: {e}",
                recoverable=True,
            )
            context.mark_skip(f"Embedding error: {e}")
            self._logger.error(f"Embedding error: {e}")

        return context

    def _create_embeddings(
        self,
        texts: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Create embeddings for a list of texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding results.
        """
        if not texts:
            raise EmbeddingError("No texts provided for embedding")

        all_embeddings: List[Dict[str, Any]] = []

        for batch in self._batched(texts, self._batch_size):
            resp = TextEmbedding.call(
                api_key=self._api_key,
                model=self._model_name,
                input=batch,
                dimension=self._dimensions,
                output_type=self._output_type,
            )

            if resp.status_code != HTTPStatus.OK:
                raise EmbeddingError(f"Embedding failed: {resp.message}")

            # Sort by text_index to maintain order
            embeddings = sorted(
                resp.output["embeddings"],
                key=lambda x: x["text_index"],
            )

            for emb in embeddings:
                all_embeddings.append(emb)

        return all_embeddings

    def _batched(
        self,
        inputs: List[Any],
        batch_size: int,
    ) -> Generator[List[Any], None, None]:
        """Split a list into batches of specified size."""
        for i in range(0, len(inputs), batch_size):
            yield inputs[i:i + batch_size]

    def _convert_sparse_vector(
        self,
        sparse_data: Any,
    ) -> List[Dict[str, Any]]:
        """
        Convert DashScope sparse embedding to list format.

        Keeps the original format: [{"index": int, "value": float}, ...]
        This matches the original implementation and preserves order.
        """
        if isinstance(sparse_data, dict):
            # Handle {"indices": [...], "values": [...]} format
            indices = sparse_data.get("indices", [])
            values = sparse_data.get("values", [])
            return [
                {"index": int(idx), "value": float(val)}
                for idx, val in zip(indices, values)
            ]
        elif isinstance(sparse_data, list):
            # Handle list of items
            result = []
            for item in sparse_data:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    result.append({"index": int(item[0]), "value": float(item[1])})
                elif isinstance(item, dict):
                    idx = item.get("index", item.get("token_id", 0))
                    val = item.get("value", item.get("weight", 0.0))
                    result.append({"index": int(idx), "value": float(val)})
            return result
        else:
            self._logger.warning(f"Unknown sparse data format: {type(sparse_data)}")
            return []

    def _build_embedding_prefix(self, context: ProcessingContext) -> str:
        """
        Build embedding prefix from category and title.

        Format: [Category/Title]
        This matches the original implementation to ensure
        consistent vector semantics.
        """
        category = ""
        title = ""

        # Try to get from raw_file metadata
        if context.raw_file and context.raw_file.metadata:
            category = context.raw_file.metadata.get("category", "")
            # Title might be in metadata or parsed_document
            title = context.raw_file.metadata.get("title", "")

        # Fallback to parsed_document for title
        if not title and context.parsed_document:
            title = context.parsed_document.title or ""

        # Build prefix only if we have both category and title
        if category and title:
            return f"[{category}/{title}]"
        elif category:
            return f"[{category}]"
        elif title:
            return f"[{title}]"
        else:
            return ""
