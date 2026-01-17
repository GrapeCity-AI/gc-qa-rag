"""
Qdrant Index Storage - Vector storage using Qdrant.

Implements IIndexStorage for storing and managing vector indexes in Qdrant.
Supports collection management, alias management (blue-green deployment),
and batch writing.
"""

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    Distance,
    PointStruct,
    SparseVector,
    VectorParams,
    SparseVectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from ai_knowledge_service.abstractions.models.index import (
    IndexRecord,
    IndexSchema,
    VectorConfig,
)
from ai_knowledge_service.abstractions.storage.index_storage import (
    CollectionInfo,
    IIndexStorage,
    WriteResult,
)


@dataclass
class QdrantConfig:
    """Configuration for Qdrant connection."""

    url: str
    api_key: Optional[str] = None
    timeout: float = 60.0


class QdrantIndexStorage(IIndexStorage):
    """
    Qdrant Index Storage - Stores vector indexes in Qdrant.

    Features:
    - Collection management (create, delete, info)
    - Alias management for blue-green deployments
    - Batch writing with configurable batch size
    - Support for dense and sparse vectors
    """

    def __init__(
        self,
        config: QdrantConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Qdrant storage.

        Args:
            config: Qdrant connection configuration.
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._config = config

        # Initialize client
        self._client = QdrantClient(
            url=config.url,
            api_key=config.api_key,
            timeout=config.timeout,
        )

        self._logger.info(f"Connected to Qdrant at {config.url}")

    def create_collection(
        self,
        name: str,
        schema: IndexSchema,
        knowledge_base_version_id: str,
    ) -> None:
        """Create a new index collection."""
        if self.collection_exists(name):
            raise ValueError(f"Collection already exists: {name}")

        if schema.vector_config is None:
            raise ValueError("Vector config is required for vector index")

        try:
            # Build vector configuration
            vector_config = schema.vector_config
            vectors_config = {}
            sparse_vectors_config = {}

            # Standard QA vectors
            vectors_config["question_dense"] = VectorParams(
                size=vector_config.dimensions,
                distance=self._get_distance(vector_config.distance_metric),
            )
            vectors_config["answer_dense"] = VectorParams(
                size=vector_config.dimensions,
                distance=self._get_distance(vector_config.distance_metric),
            )

            # Sparse vectors if enabled
            if vector_config.sparse_enabled:
                sparse_vectors_config["question_sparse"] = SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )
                sparse_vectors_config["answer_sparse"] = SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )

            # Create collection
            self._client.create_collection(
                collection_name=name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config if sparse_vectors_config else None,
            )

            self._logger.info(f"Created collection: {name}")

        except Exception as e:
            self._logger.error(f"Failed to create collection {name}: {e}")
            raise

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        try:
            return self._client.collection_exists(name)
        except Exception:
            return False

    def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        """Get information about a collection."""
        if not self.collection_exists(name):
            return None

        try:
            info = self._client.get_collection(name)

            # Build schema from collection info
            schema = IndexSchema(
                index_type="vector",
                vector_config=VectorConfig(
                    dimensions=1024,  # Default
                    distance_metric="cosine",
                    sparse_enabled=True,
                ),
            )

            return CollectionInfo(
                name=name,
                schema=schema,
                records_count=info.points_count or 0,
                size_bytes=0,  # Qdrant doesn't expose this directly
                metadata={
                    "status": info.status.value if info.status else "unknown",
                    "vectors_count": info.vectors_count or 0,
                },
            )

        except Exception as e:
            self._logger.warning(f"Failed to get collection info for {name}: {e}")
            return None

    def list_collections(
        self,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """List collection names."""
        try:
            collections = self._client.get_collections()
            names = [c.name for c in collections.collections]

            if prefix:
                names = [n for n in names if n.startswith(prefix)]

            return sorted(names)

        except Exception as e:
            self._logger.error(f"Failed to list collections: {e}")
            return []

    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            if not self.collection_exists(name):
                return False

            self._client.delete_collection(name)
            self._logger.info(f"Deleted collection: {name}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to delete collection {name}: {e}")
            return False

    def write(
        self,
        collection: str,
        records: List[IndexRecord],
        batch_size: int = 100,
    ) -> WriteResult:
        """Write index records to a collection."""
        if not records:
            return WriteResult(success=True, records_written=0)

        if not self.collection_exists(collection):
            return WriteResult.failure(f"Collection does not exist: {collection}")

        start_time = time.time()
        records_written = 0
        records_failed = 0

        try:
            # Process in batches
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                points = []

                for record in batch:
                    try:
                        point = self._record_to_point(record)
                        points.append(point)
                    except Exception as e:
                        self._logger.warning(f"Failed to convert record {record.id}: {e}")
                        records_failed += 1

                if points:
                    self._client.upsert(
                        collection_name=collection,
                        wait=True,
                        points=points,
                    )
                    records_written += len(points)

            duration = time.time() - start_time

            self._logger.info(
                f"Wrote {records_written} records to {collection} in {duration:.2f}s"
            )

            return WriteResult(
                success=records_failed == 0,
                records_written=records_written,
                records_failed=records_failed,
                duration_seconds=duration,
            )

        except Exception as e:
            self._logger.error(f"Failed to write to collection {collection}: {e}")
            return WriteResult.failure(str(e))

    def delete_by_file_version(
        self,
        collection: str,
        file_version_id: str,
    ) -> int:
        """Delete all records for a file version."""
        try:
            # Use scroll to find matching points
            result = self._client.scroll(
                collection_name=collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="file_version_id",
                            match=MatchValue(value=file_version_id),
                        )
                    ]
                ),
                limit=10000,
                with_payload=False,
                with_vectors=False,
            )

            point_ids = [point.id for point in result[0]]

            if point_ids:
                self._client.delete(
                    collection_name=collection,
                    points_selector=models.PointIdsList(
                        points=point_ids,
                    ),
                )

            self._logger.debug(
                f"Deleted {len(point_ids)} records for file version {file_version_id}"
            )
            return len(point_ids)

        except Exception as e:
            self._logger.error(f"Failed to delete by file version: {e}")
            return 0

    def delete_by_ids(
        self,
        collection: str,
        record_ids: List[str],
    ) -> int:
        """Delete records by IDs."""
        if not record_ids:
            return 0

        try:
            self._client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(
                    points=record_ids,
                ),
            )

            self._logger.debug(f"Deleted {len(record_ids)} records by ID")
            return len(record_ids)

        except Exception as e:
            self._logger.error(f"Failed to delete by IDs: {e}")
            return 0

    def get_record_count(self, collection: str) -> int:
        """Get the number of records in a collection."""
        info = self.get_collection_info(collection)
        return info.records_count if info else 0

    def get_file_version_ids(self, collection: str) -> List[str]:
        """Get all unique file version IDs in a collection."""
        try:
            # Scroll through all points to collect unique file_version_ids
            unique_ids = set()
            offset = None

            while True:
                result = self._client.scroll(
                    collection_name=collection,
                    scroll_filter=None,
                    limit=1000,
                    offset=offset,
                    with_payload=["file_version_id"],
                    with_vectors=False,
                )

                points, next_offset = result

                for point in points:
                    if point.payload and "file_version_id" in point.payload:
                        unique_ids.add(point.payload["file_version_id"])

                if next_offset is None:
                    break
                offset = next_offset

            return list(unique_ids)

        except Exception as e:
            self._logger.error(f"Failed to get file version IDs: {e}")
            return []

    # Alias management

    def update_alias(
        self,
        alias: str,
        collection: str,
    ) -> None:
        """Create or update an alias to point to a collection."""
        try:
            self._client.update_collection_aliases(
                change_aliases_operations=[
                    models.DeleteAliasOperation(
                        delete_alias=models.DeleteAlias(alias_name=alias)
                    ),
                    models.CreateAliasOperation(
                        create_alias=models.CreateAlias(
                            collection_name=collection,
                            alias_name=alias,
                        )
                    ),
                ]
            )

            self._logger.info(f"Updated alias {alias} -> {collection}")

        except Exception as e:
            self._logger.error(f"Failed to update alias {alias}: {e}")
            raise

    def delete_alias(self, alias: str) -> bool:
        """Delete an alias."""
        try:
            self._client.update_collection_aliases(
                change_aliases_operations=[
                    models.DeleteAliasOperation(
                        delete_alias=models.DeleteAlias(alias_name=alias)
                    ),
                ]
            )

            self._logger.info(f"Deleted alias: {alias}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to delete alias {alias}: {e}")
            return False

    def get_alias_target(self, alias: str) -> Optional[str]:
        """Get the collection name for an alias."""
        aliases = self.list_aliases()
        return aliases.get(alias)

    def list_aliases(self) -> Dict[str, str]:
        """List all aliases and their targets."""
        try:
            aliases_response = self._client.get_aliases()
            return {
                alias.alias_name: alias.collection_name
                for alias in aliases_response.aliases
            }

        except Exception as e:
            self._logger.error(f"Failed to list aliases: {e}")
            return {}

    def switch_alias(
        self,
        alias: str,
        old_collection: str,
        new_collection: str,
    ) -> bool:
        """Atomically switch an alias from one collection to another."""
        current_target = self.get_alias_target(alias)

        if current_target != old_collection:
            raise ValueError(
                f"Alias {alias} points to {current_target}, not {old_collection}"
            )

        try:
            self._client.update_collection_aliases(
                change_aliases_operations=[
                    models.DeleteAliasOperation(
                        delete_alias=models.DeleteAlias(alias_name=alias)
                    ),
                    models.CreateAliasOperation(
                        create_alias=models.CreateAlias(
                            collection_name=new_collection,
                            alias_name=alias,
                        )
                    ),
                ]
            )

            self._logger.info(
                f"Switched alias {alias}: {old_collection} -> {new_collection}"
            )
            return True

        except Exception as e:
            self._logger.error(f"Failed to switch alias {alias}: {e}")
            return False

    def _get_distance(self, metric: str) -> Distance:
        """Convert distance metric string to Qdrant Distance enum."""
        metric_map = {
            "cosine": Distance.COSINE,
            "euclidean": Distance.EUCLID,
            "dot": Distance.DOT,
        }
        return metric_map.get(metric, Distance.COSINE)

    def _record_to_point(self, record: IndexRecord) -> PointStruct:
        """Convert an IndexRecord to a Qdrant PointStruct."""
        # Extract vectors from content
        vectors = {}

        if "question_dense" in record.content:
            vectors["question_dense"] = record.content["question_dense"]
        if "answer_dense" in record.content:
            vectors["answer_dense"] = record.content["answer_dense"]
        if "dense_vector" in record.content:
            vectors["question_dense"] = record.content["dense_vector"]

        # Extract and add sparse vectors to the same vector dict
        if "question_sparse" in record.content:
            sparse_data = record.content["question_sparse"]
            vectors["question_sparse"] = self._transform_sparse(sparse_data)

        if "answer_sparse" in record.content:
            sparse_data = record.content["answer_sparse"]
            vectors["answer_sparse"] = self._transform_sparse(sparse_data)

        # Build payload
        payload = {
            "file_version_id": record.file_version_id,
            "index_type": record.index_type,
            "created_at": record.created_at.isoformat(),
            **record.payload,
        }

        return PointStruct(
            id=record.id,
            vector=vectors if vectors else None,
            payload=payload,
        )

    def _transform_sparse(
        self,
        sparse_data: Any,
    ) -> SparseVector:
        """
        Transform sparse embedding data to Qdrant SparseVector.

        Handles the original format: [{"index": int, "value": float}, ...]
        Converts to Qdrant's {"indices": [...], "values": [...]} format.
        """
        if isinstance(sparse_data, list):
            # Original format: [{"index": int, "value": float}, ...]
            indices = [item["index"] for item in sparse_data if isinstance(item, dict)]
            values = [item["value"] for item in sparse_data if isinstance(item, dict)]
            return SparseVector(indices=indices, values=values)
        elif isinstance(sparse_data, dict):
            # Already in {"indices": [...], "values": [...]} format
            if "indices" in sparse_data and "values" in sparse_data:
                return SparseVector(
                    indices=sparse_data["indices"],
                    values=sparse_data["values"],
                )
            # Or dict format {index: value, ...}
            else:
                return SparseVector(
                    indices=list(sparse_data.keys()),
                    values=list(sparse_data.values()),
                )
        else:
            self._logger.warning(f"Unknown sparse data format: {type(sparse_data)}")
            return SparseVector(indices=[], values=[])
