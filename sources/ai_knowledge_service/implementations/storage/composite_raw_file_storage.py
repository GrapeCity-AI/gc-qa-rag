"""
Composite Raw File Storage - Combines metadata and content storage.

This implementation provides a unified interface for raw file storage
by combining a metadata store and a content store.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Iterator, List, Optional

from ai_knowledge_service.abstractions.models.raw_file import (
    RawFile,
    LifecycleStatus,
)
from ai_knowledge_service.abstractions.pipelines.source import SourceRecord
from ai_knowledge_service.abstractions.storage.raw_file_storage import (
    IRawFileStorage,
    IRawFileMetadataStore,
    IRawFileContentStore,
    QueryCriteria,
)


class CompositeRawFileStorage(IRawFileStorage):
    """
    Composite storage combining metadata and content stores.

    This is the main implementation of IRawFileStorage that coordinates
    between a metadata store (e.g., SQLite) and a content store (e.g., filesystem).
    """

    def __init__(
        self,
        metadata_store: IRawFileMetadataStore,
        content_store: IRawFileContentStore,
    ):
        self._metadata = metadata_store
        self._content = content_store

    def save(
        self,
        record: SourceRecord,
        knowledge_base_id: str,
    ) -> RawFile:
        """Save a source record as a raw file."""
        content_bytes = record.content_bytes
        content_hash = self._compute_hash(content_bytes)

        existing_id = self._metadata.exists_by_hash(knowledge_base_id, content_hash)
        if existing_id:
            existing = self._metadata.get(existing_id)
            if existing:
                return existing

        file_id = str(uuid.uuid4())

        storage_path = self._content.write(
            file_id=file_id,
            content=content_bytes,
            knowledge_base_id=knowledge_base_id,
        )

        original_name = self._extract_original_name(record)

        raw_file = RawFile(
            id=file_id,
            knowledge_base_id=knowledge_base_id,
            source_type=record.metadata.get("source_type", "unknown"),
            source_uri=record.source_uri,
            original_name=original_name,
            content_hash=content_hash,
            storage_path=storage_path,
            mime_type=record.content_type,
            size_bytes=len(content_bytes),
            metadata=record.metadata,
            lifecycle_status=LifecycleStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self._metadata.save(raw_file)

        return raw_file

    def get(self, file_id: str) -> Optional[RawFile]:
        """Get a raw file by ID."""
        return self._metadata.get(file_id)

    def get_content(self, file_id: str) -> bytes:
        """Get the content of a raw file."""
        raw_file = self._metadata.get(file_id)
        if raw_file is None:
            raise FileNotFoundError(f"File not found: {file_id}")

        return self._content.read(raw_file.storage_path)

    def list(
        self,
        knowledge_base_id: str,
        status: Optional[LifecycleStatus] = None,
        since: Optional[datetime] = None,
    ) -> Iterator[RawFile]:
        """List raw files for a knowledge base."""
        criteria = QueryCriteria(
            knowledge_base_id=knowledge_base_id,
            lifecycle_status=status,
            created_after=since,
            limit=1000,
            offset=0,
        )

        while True:
            results = self._metadata.query(criteria)
            if not results:
                break

            for raw_file in results:
                yield raw_file

            if len(results) < criteria.limit:
                break

            criteria.offset += criteria.limit

    def query(self, criteria: QueryCriteria) -> List[RawFile]:
        """Query raw files with complex criteria."""
        return self._metadata.query(criteria)

    def update_status(
        self,
        file_id: str,
        status: LifecycleStatus,
    ) -> None:
        """Update the lifecycle status of a file."""
        raw_file = self._metadata.get(file_id)
        if raw_file is None:
            raise FileNotFoundError(f"File not found: {file_id}")

        raw_file.lifecycle_status = status
        raw_file.updated_at = datetime.now()
        self._metadata.update(raw_file)

    def exists_by_hash(
        self,
        knowledge_base_id: str,
        content_hash: str,
    ) -> Optional[str]:
        """Check if a file with the given hash exists."""
        return self._metadata.exists_by_hash(knowledge_base_id, content_hash)

    def count(
        self,
        knowledge_base_id: str,
        status: Optional[LifecycleStatus] = None,
    ) -> int:
        """Count raw files."""
        criteria = QueryCriteria(
            knowledge_base_id=knowledge_base_id,
            lifecycle_status=status,
        )
        return self._metadata.count(criteria)

    def delete(self, file_id: str) -> bool:
        """Logically delete a file."""
        try:
            self.update_status(file_id, LifecycleStatus.DELETED)
            return True
        except FileNotFoundError:
            return False

    def _compute_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()

    def _extract_original_name(self, record: SourceRecord) -> str:
        """Extract original file name from source record."""
        if "original_name" in record.metadata:
            return record.metadata["original_name"]

        if "title" in record.metadata:
            return record.metadata["title"]

        uri = record.source_uri
        if "/" in uri:
            name = uri.rsplit("/", 1)[-1]
            if "?" in name:
                name = name.split("?")[0]
            return name or "unnamed"

        return "unnamed"
