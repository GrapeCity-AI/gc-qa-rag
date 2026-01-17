"""
Raw File Storage interfaces - Defines storage for raw files.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Protocol, runtime_checkable

from ai_knowledge_service.abstractions.models.raw_file import (
    RawFile,
    LifecycleStatus,
)
from ai_knowledge_service.abstractions.pipelines.source import SourceRecord


@dataclass
class QueryCriteria:
    """Criteria for querying raw files."""

    knowledge_base_id: Optional[str] = None
    source_type: Optional[str] = None
    lifecycle_status: Optional[LifecycleStatus] = None
    content_hash: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)

    # Pagination
    limit: int = 100
    offset: int = 0

    # Sorting
    order_by: str = "created_at"
    order_desc: bool = True


@runtime_checkable
class IRawFileStorage(Protocol):
    """
    Raw File Storage - Composite interface for raw file storage.

    Combines metadata storage and content storage into a single interface.
    This is the primary interface for interacting with raw files.
    """

    def save(
        self,
        record: SourceRecord,
        knowledge_base_id: str,
    ) -> RawFile:
        """
        Save a source record as a raw file.

        This method:
        1. Computes content hash
        2. Checks for duplicates (by hash)
        3. Stores content
        4. Creates metadata record

        Args:
            record: The source record to save.
            knowledge_base_id: The knowledge base ID.

        Returns:
            RawFile: The created raw file record.
        """
        ...

    def get(self, file_id: str) -> Optional[RawFile]:
        """
        Get a raw file by ID.

        Args:
            file_id: The file ID.

        Returns:
            Optional[RawFile]: The raw file, or None if not found.
        """
        ...

    def get_content(self, file_id: str) -> bytes:
        """
        Get the content of a raw file.

        Args:
            file_id: The file ID.

        Returns:
            bytes: The file content.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        ...

    def list(
        self,
        knowledge_base_id: str,
        status: Optional[LifecycleStatus] = None,
        since: Optional[datetime] = None,
    ) -> Iterator[RawFile]:
        """
        List raw files for a knowledge base.

        Args:
            knowledge_base_id: The knowledge base ID.
            status: Optional status filter.
            since: Optional filter for files created after this time.

        Yields:
            RawFile: Matching raw files.
        """
        ...

    def query(self, criteria: QueryCriteria) -> List[RawFile]:
        """
        Query raw files with complex criteria.

        Args:
            criteria: The query criteria.

        Returns:
            List[RawFile]: Matching raw files.
        """
        ...

    def update_status(
        self,
        file_id: str,
        status: LifecycleStatus,
    ) -> None:
        """
        Update the lifecycle status of a file.

        Args:
            file_id: The file ID.
            status: The new status.
        """
        ...

    def exists_by_hash(
        self,
        knowledge_base_id: str,
        content_hash: str,
    ) -> Optional[str]:
        """
        Check if a file with the given hash exists.

        Args:
            knowledge_base_id: The knowledge base ID.
            content_hash: The content hash.

        Returns:
            Optional[str]: The file ID if exists, None otherwise.
        """
        ...

    def count(
        self,
        knowledge_base_id: str,
        status: Optional[LifecycleStatus] = None,
    ) -> int:
        """
        Count raw files.

        Args:
            knowledge_base_id: The knowledge base ID.
            status: Optional status filter.

        Returns:
            int: Number of matching files.
        """
        ...

    def delete(self, file_id: str) -> bool:
        """
        Logically delete a file (set status to DELETED).

        Args:
            file_id: The file ID.

        Returns:
            bool: True if the file was deleted.
        """
        ...


@runtime_checkable
class IRawFileMetadataStore(Protocol):
    """
    Raw File Metadata Store - Interface for file metadata storage.

    Typically backed by a database (SQLite, MySQL, PostgreSQL).
    """

    def save(self, raw_file: RawFile) -> None:
        """
        Save a raw file metadata record.

        Args:
            raw_file: The raw file to save.
        """
        ...

    def get(self, file_id: str) -> Optional[RawFile]:
        """
        Get a raw file by ID.

        Args:
            file_id: The file ID.

        Returns:
            Optional[RawFile]: The raw file, or None if not found.
        """
        ...

    def query(self, criteria: QueryCriteria) -> List[RawFile]:
        """
        Query raw files.

        Args:
            criteria: The query criteria.

        Returns:
            List[RawFile]: Matching raw files.
        """
        ...

    def update(self, raw_file: RawFile) -> None:
        """
        Update a raw file record.

        Args:
            raw_file: The raw file with updated fields.
        """
        ...

    def count(self, criteria: QueryCriteria) -> int:
        """
        Count raw files matching criteria.

        Args:
            criteria: The query criteria.

        Returns:
            int: Number of matching files.
        """
        ...

    def exists_by_hash(
        self,
        knowledge_base_id: str,
        content_hash: str,
    ) -> Optional[str]:
        """
        Check if a file with the given hash exists.

        Args:
            knowledge_base_id: The knowledge base ID.
            content_hash: The content hash.

        Returns:
            Optional[str]: The file ID if exists, None otherwise.
        """
        ...


@runtime_checkable
class IRawFileContentStore(Protocol):
    """
    Raw File Content Store - Interface for file content storage.

    Typically backed by a file system or object storage (S3, MinIO).
    """

    def write(
        self,
        file_id: str,
        content: bytes,
        knowledge_base_id: str,
    ) -> str:
        """
        Write file content.

        Args:
            file_id: The file ID.
            content: The file content.
            knowledge_base_id: The knowledge base ID (for path organization).

        Returns:
            str: The storage path.
        """
        ...

    def read(self, storage_path: str) -> bytes:
        """
        Read file content.

        Args:
            storage_path: The storage path.

        Returns:
            bytes: The file content.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        ...

    def delete(self, storage_path: str) -> bool:
        """
        Delete file content.

        Args:
            storage_path: The storage path.

        Returns:
            bool: True if the file was deleted.
        """
        ...

    def exists(self, storage_path: str) -> bool:
        """
        Check if a file exists.

        Args:
            storage_path: The storage path.

        Returns:
            bool: True if the file exists.
        """
        ...

    def get_size(self, storage_path: str) -> int:
        """
        Get the size of a file.

        Args:
            storage_path: The storage path.

        Returns:
            int: File size in bytes.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        ...
