"""
Index Storage interfaces - Defines storage for indexes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ai_knowledge_service.abstractions.models.index import (
    IndexRecord,
    IndexSchema,
)


@dataclass
class WriteResult:
    """Result of a write operation."""

    success: bool
    records_written: int = 0
    records_failed: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None

    @property
    def total_records(self) -> int:
        """Get total records attempted."""
        return self.records_written + self.records_failed

    @classmethod
    def failure(cls, error: str) -> "WriteResult":
        """Create a failed write result."""
        return cls(success=False, error_message=error)


@dataclass
class CollectionInfo:
    """Information about an index collection."""

    name: str
    schema: IndexSchema
    records_count: int = 0
    size_bytes: int = 0
    knowledge_base_version_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        """Check if the collection is empty."""
        return self.records_count == 0


@runtime_checkable
class IIndexStorage(Protocol):
    """
    Index Storage - Interface for storing and managing indexes.

    Typically backed by a vector database (Qdrant, Milvus, Pinecone)
    or search engine (Elasticsearch, OpenSearch).
    """

    def create_collection(
        self,
        name: str,
        schema: IndexSchema,
        knowledge_base_version_id: str,
    ) -> None:
        """
        Create a new index collection.

        Args:
            name: Collection name.
            schema: Index schema.
            knowledge_base_version_id: Associated version ID.

        Raises:
            ValueError: If collection already exists.
        """
        ...

    def collection_exists(self, name: str) -> bool:
        """
        Check if a collection exists.

        Args:
            name: Collection name.

        Returns:
            bool: True if the collection exists.
        """
        ...

    def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        """
        Get information about a collection.

        Args:
            name: Collection name.

        Returns:
            Optional[CollectionInfo]: Collection info, or None if not found.
        """
        ...

    def list_collections(
        self,
        prefix: Optional[str] = None,
    ) -> List[str]:
        """
        List collection names.

        Args:
            prefix: Optional prefix filter.

        Returns:
            List[str]: Collection names.
        """
        ...

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.

        Args:
            name: Collection name.

        Returns:
            bool: True if the collection was deleted.
        """
        ...

    def write(
        self,
        collection: str,
        records: List[IndexRecord],
        batch_size: int = 100,
    ) -> WriteResult:
        """
        Write index records to a collection.

        Args:
            collection: Collection name.
            records: Records to write.
            batch_size: Number of records per batch.

        Returns:
            WriteResult: Write operation result.
        """
        ...

    def delete_by_file_version(
        self,
        collection: str,
        file_version_id: str,
    ) -> int:
        """
        Delete all records for a file version.

        Used for incremental updates - delete old records before inserting new ones.

        Args:
            collection: Collection name.
            file_version_id: File version ID.

        Returns:
            int: Number of records deleted.
        """
        ...

    def delete_by_ids(
        self,
        collection: str,
        record_ids: List[str],
    ) -> int:
        """
        Delete records by IDs.

        Args:
            collection: Collection name.
            record_ids: IDs of records to delete.

        Returns:
            int: Number of records deleted.
        """
        ...

    def get_record_count(self, collection: str) -> int:
        """
        Get the number of records in a collection.

        Args:
            collection: Collection name.

        Returns:
            int: Number of records.
        """
        ...

    def get_file_version_ids(self, collection: str) -> List[str]:
        """
        Get all unique file version IDs in a collection.

        Args:
            collection: Collection name.

        Returns:
            List[str]: Unique file version IDs.
        """
        ...

    # Alias management

    def update_alias(
        self,
        alias: str,
        collection: str,
    ) -> None:
        """
        Create or update an alias to point to a collection.

        Args:
            alias: Alias name.
            collection: Target collection name.
        """
        ...

    def delete_alias(self, alias: str) -> bool:
        """
        Delete an alias.

        Args:
            alias: Alias name.

        Returns:
            bool: True if the alias was deleted.
        """
        ...

    def get_alias_target(self, alias: str) -> Optional[str]:
        """
        Get the collection name for an alias.

        Args:
            alias: Alias name.

        Returns:
            Optional[str]: Collection name, or None if alias doesn't exist.
        """
        ...

    def list_aliases(self) -> Dict[str, str]:
        """
        List all aliases and their targets.

        Returns:
            Dict[str, str]: Mapping of alias name to collection name.
        """
        ...

    def switch_alias(
        self,
        alias: str,
        old_collection: str,
        new_collection: str,
    ) -> bool:
        """
        Atomically switch an alias from one collection to another.

        Args:
            alias: Alias name.
            old_collection: Current collection (for verification).
            new_collection: New target collection.

        Returns:
            bool: True if the switch was successful.

        Raises:
            ValueError: If the alias doesn't point to old_collection.
        """
        ...
