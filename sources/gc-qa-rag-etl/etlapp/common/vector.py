from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, SparseVectorParams
import logging

logger = logging.getLogger(__name__)


class VectorConfig:
    """Configuration for vector collection parameters."""

    def __init__(
        self,
        dense_vector_size: int = 1024,
        dense_distance: Distance = Distance.COSINE,
        sparse_modifier: models.Modifier = models.Modifier.IDF,
    ):
        self.dense_vector_size = dense_vector_size
        self.dense_distance = dense_distance
        self.sparse_modifier = sparse_modifier


class VectorClient:
    """Client for interacting with Qdrant vector database.

    This class provides methods to manage vector collections and perform operations
    like creating collections, inserting points, and managing aliases.

    Args:
        url (str): URL of the Qdrant server
        vector_config (Optional[VectorConfig]): Configuration for vector parameters
    """

    def __init__(self, url: str, vector_config: Optional[VectorConfig] = None):
        """Initialize the VectorClient with Qdrant server URL and optional configuration."""
        self.client = QdrantClient(url=url)
        self.vector_config = vector_config or VectorConfig()

    def ensure_collection_exists(self, collection_name: str) -> None:
        """Ensure a collection exists, create it if it doesn't.

        Args:
            collection_name (str): Name of the collection to check/create

        Raises:
            ValueError: If collection_name is empty
            Exception: If collection creation fails
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")

        if self.client.collection_exists(collection_name):
            logger.info(f"Collection {collection_name} already exists")
            return

        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "question_dense": VectorParams(
                        size=self.vector_config.dense_vector_size,
                        distance=self.vector_config.dense_distance,
                    ),
                    "answer_dense": VectorParams(
                        size=self.vector_config.dense_vector_size,
                        distance=self.vector_config.dense_distance,
                    ),
                },
                sparse_vectors_config={
                    "question_sparse": SparseVectorParams(
                        modifier=self.vector_config.sparse_modifier
                    ),
                    "answer_sparse": SparseVectorParams(
                        modifier=self.vector_config.sparse_modifier
                    ),
                },
            )
            logger.info(f"Created collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {str(e)}")
            raise

    def insert_to_collection(
        self, collection_name: str, points: List[Dict[str, Any]]
    ) -> None:
        """Insert or update points in a collection.

        Args:
            collection_name (str): Name of the collection
            points (List[Dict[str, Any]]): List of points to insert/update

        Raises:
            ValueError: If collection_name is empty or points list is empty
            Exception: If insertion fails
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
        if not points:
            raise ValueError("Points list cannot be empty")

        try:
            operation_info = self.client.upsert(
                collection_name=collection_name,
                wait=True,
                points=points,
            )
            logger.info(f"Successfully inserted {len(points)} points: {operation_info}")
        except Exception as e:
            logger.error(
                f"Failed to insert points to collection {collection_name}: {str(e)}"
            )
            raise

    def update_collection_aliases(self, collection_name: str, alias_name: str) -> None:
        """Update collection aliases by removing old alias and creating new one.

        Args:
            collection_name (str): Name of the collection
            alias_name (str): Name of the alias to create

        Raises:
            ValueError: If collection_name or alias_name is empty
            Exception: If alias update fails
        """
        if not collection_name or not alias_name:
            raise ValueError("Collection name and alias name cannot be empty")

        try:
            self.client.update_collection_aliases(
                change_aliases_operations=[
                    models.DeleteAliasOperation(
                        delete_alias=models.DeleteAlias(alias_name=alias_name)
                    ),
                    models.CreateAliasOperation(
                        create_alias=models.CreateAlias(
                            collection_name=collection_name,
                            alias_name=alias_name,
                        )
                    ),
                ]
            )
            logger.info(
                f"Successfully updated alias {alias_name} for collection {collection_name}"
            )
        except Exception as e:
            logger.error(
                f"Failed to update alias {alias_name} for collection {collection_name}: {str(e)}"
            )
            raise
