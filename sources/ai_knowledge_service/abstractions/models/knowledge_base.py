"""
Knowledge Base models - Core domain models for knowledge base and versioning.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class VersionStatus(Enum):
    """Knowledge base version status."""

    DRAFT = "draft"  # Draft, editable
    BUILDING = "building"  # Build in progress
    READY = "ready"  # Build complete, ready for publishing
    PUBLISHED = "published"  # Published to production
    ARCHIVED = "archived"  # Archived


class IndexStatus(Enum):
    """File version index status."""

    PENDING = "pending"  # Pending indexing
    INDEXED = "indexed"  # Indexed successfully
    FAILED = "failed"  # Index failed


@dataclass
class KnowledgeBase:
    """
    Knowledge Base - Top-level organizational unit.

    A knowledge base represents a collection of documents and their
    associated indexes for a specific domain or product.
    """

    id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Knowledge base ID cannot be empty")
        if not self.name:
            raise ValueError("Knowledge base name cannot be empty")


@dataclass
class KnowledgeBaseVersion:
    """
    Knowledge Base Version - A snapshot of the knowledge base at a point in time.

    Versions support incremental builds by tracking parent versions.
    """

    id: str
    knowledge_base_id: str
    version_tag: str  # e.g., "v1.0", "20260117"
    status: VersionStatus = VersionStatus.DRAFT
    parent_version_id: Optional[str] = None  # For incremental builds
    created_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Version ID cannot be empty")
        if not self.knowledge_base_id:
            raise ValueError("Knowledge base ID cannot be empty")
        if not self.version_tag:
            raise ValueError("Version tag cannot be empty")

    @property
    def is_editable(self) -> bool:
        """Check if this version can be edited."""
        return self.status == VersionStatus.DRAFT

    @property
    def is_publishable(self) -> bool:
        """Check if this version can be published."""
        return self.status == VersionStatus.READY

    @property
    def has_parent(self) -> bool:
        """Check if this version has a parent (for incremental builds)."""
        return self.parent_version_id is not None


@dataclass
class FileVersion:
    """
    File Version - Tracks a specific version of a file within a knowledge base version.

    Each file can have multiple versions across different knowledge base versions.
    The content_hash is used to detect changes for incremental indexing.
    """

    id: str
    raw_file_id: str
    knowledge_base_version_id: str
    content_hash: str  # Content fingerprint for change detection
    index_status: IndexStatus = IndexStatus.PENDING
    indexed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raise ValueError("File version ID cannot be empty")
        if not self.raw_file_id:
            raise ValueError("Raw file ID cannot be empty")
        if not self.knowledge_base_version_id:
            raise ValueError("Knowledge base version ID cannot be empty")
        if not self.content_hash:
            raise ValueError("Content hash cannot be empty")

    @property
    def is_indexed(self) -> bool:
        """Check if this file version has been indexed."""
        return self.index_status == IndexStatus.INDEXED

    @property
    def needs_indexing(self) -> bool:
        """Check if this file version needs indexing."""
        return self.index_status == IndexStatus.PENDING
