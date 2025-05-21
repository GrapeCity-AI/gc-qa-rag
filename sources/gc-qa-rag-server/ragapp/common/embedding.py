from http import HTTPStatus
from typing import Generator, List, Optional, Dict, Any
from dashscope import TextEmbedding
from ragapp.common.config import app_config

# Default configuration
DEFAULT_BATCH_SIZE = 6
DEFAULT_DIMENSION = 1024
DEFAULT_OUTPUT_TYPE = "dense&sparse"


class EmbeddingError(Exception):
    """Custom exception for embedding-related errors."""

    pass


def batched(
    inputs: List[Any], batch_size: int = DEFAULT_BATCH_SIZE
) -> Generator[List[Any], None, None]:
    """Split a list into batches of specified size.

    Args:
        inputs: List of items to batch
        batch_size: Size of each batch

    Yields:
        List of items in the current batch
    """
    for i in range(0, len(inputs), batch_size):
        yield inputs[i : i + batch_size]


def create_embedding(
    texts: List[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
    dimension: int = DEFAULT_DIMENSION,
    output_type: str = DEFAULT_OUTPUT_TYPE,
) -> Dict[str, Any]:
    """Create embeddings for a list of texts.

    Args:
        texts: List of texts to embed
        batch_size: Number of texts to process in each batch
        dimension: Dimension of the embedding vectors
        output_type: Type of embedding output

    Returns:
        Dictionary containing the embeddings and usage information

    Raises:
        EmbeddingError: If the embedding process fails
    """
    if not texts:
        raise EmbeddingError("No texts provided for embedding")

    result: Optional[Dict[str, Any]] = None
    batch_counter = 0

    for batch in batched(texts, batch_size):
        resp = TextEmbedding.call(
            api_key=app_config.embedding.api_key,
            model=TextEmbedding.Models.text_embedding_v3,
            input=batch,
            dimension=dimension,
            output_type=output_type,
        )

        if resp.status_code != HTTPStatus.OK:
            raise EmbeddingError(f"Embedding failed: {resp.error}")

        if result is None:
            result = resp
        else:
            for emb in resp.output["embeddings"]:
                emb["text_index"] += batch_counter
                result.output["embeddings"].append(emb)
            result.usage["total_tokens"] += resp.usage["total_tokens"]

        batch_counter += len(batch)

    if result is None:
        raise EmbeddingError("No embeddings were generated")

    return result
