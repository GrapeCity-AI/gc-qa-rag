"""
Raw File models - Models for raw file storage and lifecycle management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class LifecycleStatus(Enum):
    """Raw file lifecycle status."""

    ACTIVE = "active"  # Active and available
    ARCHIVED = "archived"  # Archived but recoverable
    DELETED = "deleted"  # Logically deleted, physically retained


@dataclass
class RawFile:
    """
    Raw File - Record of an ingested file.

    Raw files are immutable once created. The content is stored separately
    from the metadata to support different storage backends.
    """

    id: str
    knowledge_base_id: str
    source_type: str  # "sitemap", "forum_api", "file_upload", etc.
    source_uri: str  # Original source identifier
    original_name: str
    content_hash: str  # Content fingerprint for deduplication
    storage_path: str  # Physical storage path
    mime_type: str
    size_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    lifecycle_status: LifecycleStatus = LifecycleStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Raw file ID cannot be empty")
        if not self.knowledge_base_id:
            raise ValueError("Knowledge base ID cannot be empty")
        if not self.source_type:
            raise ValueError("Source type cannot be empty")
        if not self.source_uri:
            raise ValueError("Source URI cannot be empty")
        if not self.content_hash:
            raise ValueError("Content hash cannot be empty")
        if not self.storage_path:
            raise ValueError("Storage path cannot be empty")
        if self.size_bytes < 0:
            raise ValueError("Size bytes cannot be negative")

    @property
    def is_active(self) -> bool:
        """Check if this file is active."""
        return self.lifecycle_status == LifecycleStatus.ACTIVE

    @property
    def is_deleted(self) -> bool:
        """Check if this file is deleted."""
        return self.lifecycle_status == LifecycleStatus.DELETED

    @property
    def file_extension(self) -> Optional[str]:
        """Extract file extension from original name."""
        if "." in self.original_name:
            return self.original_name.rsplit(".", 1)[-1].lower()
        return None

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key with optional default."""
        return self.metadata.get(key, default)
