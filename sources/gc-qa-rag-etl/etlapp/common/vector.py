from typing import List, Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, SparseVectorParams
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
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


class VectorDatabase(ABC):
    """Abstract base class for vector database implementations."""
    
    @abstractmethod
    def ensure_collection_exists(self, collection_name: str) -> None:
        """Ensure a collection exists, create it if it doesn't."""
        pass
    
    @abstractmethod
    def insert_to_collection(
        self, collection_name: str, points: List[Dict[str, Any]]
    ) -> None:
        """Insert or update points in a collection."""
        pass
    
    @abstractmethod
    def update_collection_aliases(self, collection_name: str, alias_name: str) -> None:
        """Update collection aliases."""
        pass
    
    @abstractmethod
    def get_collections_info(self) -> List[Dict[str, Any]]:
        """Get information about all collections."""
        pass
    
    @abstractmethod
    def get_collection_aliases(self) -> List[Dict[str, Any]]:
        """Get information about all collection aliases."""
        pass


class QdrantVectorDatabase(VectorDatabase):
    """Qdrant vector database implementation."""
    
    def __init__(self, url: str, vector_config: Optional[VectorConfig] = None):
        self.client = QdrantClient(url=url)
        self.vector_config = vector_config or VectorConfig()
    
    def ensure_collection_exists(self, collection_name: str) -> None:
        """Ensure a collection exists, create it if it doesn't."""
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
        """Insert or update points in a collection."""
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
        """Update collection aliases by removing old alias and creating new one."""
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

    def get_collections_info(self) -> List[Dict[str, Any]]:
        """Get information about all collections including basic stats."""
        try:
            collections = self.client.get_collections()
            collections_info = []
            
            for collection in collections.collections:
                try:
                    collection_info = self.client.get_collection(collection.name)
                    collections_info.append({
                        "name": collection.name,
                        "vectors_count": collection_info.vectors_count or 0,
                        "points_count": collection_info.points_count or 0,
                        "status": collection_info.status.value if collection_info.status else "unknown",
                    })
                except Exception as e:
                    logger.warning(f"Failed to get details for collection {collection.name}: {str(e)}")
                    collections_info.append({
                        "name": collection.name,
                        "vectors_count": 0,
                        "points_count": 0,
                        "status": "unknown",
                    })
            
            logger.info(f"Retrieved information for {len(collections_info)} collections")
            return collections_info
        except Exception as e:
            logger.error(f"Failed to get collections info: {str(e)}")
            raise

    def get_collection_aliases(self) -> List[Dict[str, Any]]:
        """Get information about all collection aliases."""
        try:
            aliases_response = self.client.get_aliases()
            aliases_info = []
            
            for alias_description in aliases_response.aliases:
                aliases_info.append({
                    "alias_name": alias_description.alias_name,
                    "collection_name": alias_description.collection_name
                })
            
            logger.info(f"Retrieved {len(aliases_info)} aliases")
            return aliases_info
        except Exception as e:
            logger.error(f"Failed to get collection aliases: {str(e)}")
            raise


class MilvusVectorDatabase(VectorDatabase):
    """Milvus vector database implementation."""
    
    def __init__(self, host: str, port: int = 19530, username: Optional[str] = None, 
                 password: Optional[str] = None, vector_config: Optional[VectorConfig] = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.vector_config = vector_config or VectorConfig()
        self._connect()
    
    def _connect(self):
        """Connect to Milvus server."""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password
            )
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            raise
    
    def _create_collection_schema(self, collection_name: str) -> CollectionSchema:
        """Create collection schema for Milvus."""
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
            FieldSchema(name="question_dense", dtype=DataType.FLOAT_VECTOR, dim=self.vector_config.dense_vector_size),
            FieldSchema(name="answer_dense", dtype=DataType.FLOAT_VECTOR, dim=self.vector_config.dense_vector_size),
            FieldSchema(name="question_sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="answer_sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
        ]
        
        return CollectionSchema(fields, description=f"Collection {collection_name}")
    
    def ensure_collection_exists(self, collection_name: str) -> None:
        """Ensure a collection exists, create it if it doesn't."""
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
        
        try:
            if utility.has_collection(collection_name):
                logger.info(f"Collection {collection_name} already exists")
                return
            
            schema = self._create_collection_schema(collection_name)
            Collection(collection_name, schema)
            logger.info(f"Created collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {str(e)}")
            raise
    
    def insert_to_collection(
        self, collection_name: str, points: List[Dict[str, Any]]
    ) -> None:
        """Insert or update points in a collection."""
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
        if not points:
            raise ValueError("Points list cannot be empty")
        
        try:
            collection = Collection(collection_name)
            
            # Convert points to Milvus format
            ids = []
            question_dense_vectors = []
            answer_dense_vectors = []
            question_sparse_vectors = []
            answer_sparse_vectors = []
            
            for point in points:
                ids.append(str(point.get("id", "")))
                question_dense_vectors.append(point.get("vector", {}).get("question_dense", []))
                answer_dense_vectors.append(point.get("vector", {}).get("answer_dense", []))
                question_sparse_vectors.append(point.get("vector", {}).get("question_sparse", {}))
                answer_sparse_vectors.append(point.get("vector", {}).get("answer_sparse", {}))
            
            data = [
                ids,
                question_dense_vectors,
                answer_dense_vectors,
                question_sparse_vectors,
                answer_sparse_vectors
            ]
            
            collection.insert(data)
            collection.flush()
            logger.info(f"Successfully inserted {len(points)} points")
        except Exception as e:
            logger.error(
                f"Failed to insert points to collection {collection_name}: {str(e)}"
            )
            raise
    
    def update_collection_aliases(self, collection_name: str, alias_name: str) -> None:
        """Update collection aliases."""
        if not collection_name or not alias_name:
            raise ValueError("Collection name and alias name cannot be empty")
        
        try:
            # Milvus uses aliases differently - drop existing and create new
            if utility.has_collection(alias_name):
                utility.drop_alias(alias_name)
            
            utility.create_alias(collection_name, alias_name)
            logger.info(
                f"Successfully updated alias {alias_name} for collection {collection_name}"
            )
        except Exception as e:
            logger.error(
                f"Failed to update alias {alias_name} for collection {collection_name}: {str(e)}"
            )
            raise
    
    def get_collections_info(self) -> List[Dict[str, Any]]:
        """Get information about all collections including basic stats."""
        try:
            collection_names = utility.list_collections()
            collections_info = []
            
            for name in collection_names:
                try:
                    collection = Collection(name)
                    stats = collection.describe()
                    collections_info.append({
                        "name": name,
                        "vectors_count": collection.num_entities,
                        "points_count": collection.num_entities,
                        "status": "ready",
                    })
                except Exception as e:
                    logger.warning(f"Failed to get details for collection {name}: {str(e)}")
                    collections_info.append({
                        "name": name,
                        "vectors_count": 0,
                        "points_count": 0,
                        "status": "unknown",
                    })
            
            logger.info(f"Retrieved information for {len(collections_info)} collections")
            return collections_info
        except Exception as e:
            logger.error(f"Failed to get collections info: {str(e)}")
            raise
    
    def get_collection_aliases(self) -> List[Dict[str, Any]]:
        """Get information about all collection aliases."""
        # Note: Milvus doesn't have a direct way to list all aliases
        # This is a simplified implementation
        try:
            logger.info("Retrieved 0 aliases (Milvus alias listing not fully supported)")
            return []
        except Exception as e:
            logger.error(f"Failed to get collection aliases: {str(e)}")
            raise


class VectorDatabaseFactory:
    """Factory class for creating vector database instances."""
    
    @staticmethod
    def create_vector_database(db_type: str, host: str, port: Optional[int] = None,
                             username: Optional[str] = None, password: Optional[str] = None,
                             vector_config: Optional[VectorConfig] = None) -> VectorDatabase:
        """Create a vector database instance based on the specified type."""
        if db_type == "qdrant":
            return QdrantVectorDatabase(url=host, vector_config=vector_config)
        elif db_type == "milvus":
            return MilvusVectorDatabase(
                host=host.replace("http://", "").replace("https://", ""),
                port=port or 19530,
                username=username,
                password=password,
                vector_config=vector_config
            )
        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")


class VectorClient:
    """Client for interacting with vector databases using strategy pattern.

    This class provides a unified interface for different vector database implementations.
    """

    def __init__(self, db_type: str, host: str, port: Optional[int] = None,
                 username: Optional[str] = None, password: Optional[str] = None,
                 vector_config: Optional[VectorConfig] = None):
        """Initialize the VectorClient with the specified database type and configuration."""
        self.vector_db = VectorDatabaseFactory.create_vector_database(
            db_type=db_type,
            host=host,
            port=port,
            username=username,
            password=password,
            vector_config=vector_config
        )

    def ensure_collection_exists(self, collection_name: str) -> None:
        """Ensure a collection exists, create it if it doesn't."""
        return self.vector_db.ensure_collection_exists(collection_name)

    def insert_to_collection(
        self, collection_name: str, points: List[Dict[str, Any]]
    ) -> None:
        """Insert or update points in a collection."""
        return self.vector_db.insert_to_collection(collection_name, points)

    def update_collection_aliases(self, collection_name: str, alias_name: str) -> None:
        """Update collection aliases."""
        return self.vector_db.update_collection_aliases(collection_name, alias_name)

    def get_collections_info(self) -> List[Dict[str, Any]]:
        """Get information about all collections including basic stats."""
        return self.vector_db.get_collections_info()

    def get_collection_aliases(self) -> List[Dict[str, Any]]:
        """Get information about all collection aliases."""
        return self.vector_db.get_collection_aliases()


def create_vector_client_from_config() -> VectorClient:
    """Create a VectorClient instance from application configuration."""
    from etlapp.common.config import app_config
    
    return VectorClient(
        db_type=app_config.vector_db.type,
        host=app_config.vector_db.host,
        port=app_config.vector_db.port,
        username=app_config.vector_db.username,
        password=app_config.vector_db.password
    )


def create_vector_client_from_url(url: str, db_type: str = "qdrant") -> VectorClient:
    """Create a VectorClient instance from URL (for backward compatibility)."""
    return VectorClient(
        db_type=db_type,
        host=url
    )
