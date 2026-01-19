"""
Version Manager interface - Manages knowledge base and file versions.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ai_knowledge_service.abstractions.models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseVersion,
    VersionStatus,
    FileVersion,
    IndexStatus,
)


@runtime_checkable
class IVersionManager(Protocol):
    """
    Version Manager - Interface for managing versions.

    Handles both knowledge base versions and file versions.
    Supports incremental builds through version lineage tracking.
    """

    # ============ Knowledge Base Management ============

    def create_knowledge_base(
        self,
        id: str,
        name: str,
        description: str = "",
    ) -> KnowledgeBase:
        """
        Create a new knowledge base.

        Args:
            id: Knowledge base ID.
            name: Knowledge base name.
            description: Optional description.

        Returns:
            KnowledgeBase: The created knowledge base.

        Raises:
            ValueError: If a knowledge base with the ID already exists.
        """
        ...

    def get_knowledge_base(self, id: str) -> Optional[KnowledgeBase]:
        """
        Get a knowledge base by ID.

        Args:
            id: Knowledge base ID.

        Returns:
            Optional[KnowledgeBase]: The knowledge base, or None if not found.
        """
        ...

    def list_knowledge_bases(self) -> List[KnowledgeBase]:
        """
        List all knowledge bases.

        Returns:
            List[KnowledgeBase]: All knowledge bases.
        """
        ...

    def delete_knowledge_base(self, id: str) -> bool:
        """
        Delete a knowledge base.

        This also deletes all versions and file versions.

        Args:
            id: Knowledge base ID.

        Returns:
            bool: True if the knowledge base was deleted.
        """
        ...

    def update_knowledge_base(self, kb: KnowledgeBase) -> None:
        """
        Update a knowledge base.

        Args:
            kb: The knowledge base with updated fields.

        Raises:
            ValueError: If the knowledge base doesn't exist.
        """
        ...

    # ============ Knowledge Base Version Management ============

    def create_version(
        self,
        knowledge_base_id: str,
        version_tag: str,
        parent_version_id: Optional[str] = None,
    ) -> KnowledgeBaseVersion:
        """
        Create a new version for a knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID.
            version_tag: Version tag (e.g., "v1.0", "20260117").
            parent_version_id: Optional parent version for incremental builds.

        Returns:
            KnowledgeBaseVersion: The created version.

        Raises:
            ValueError: If the knowledge base doesn't exist.
            ValueError: If a version with the tag already exists.
        """
        ...

    def get_version(self, version_id: str) -> Optional[KnowledgeBaseVersion]:
        """
        Get a version by ID.

        Args:
            version_id: Version ID.

        Returns:
            Optional[KnowledgeBaseVersion]: The version, or None if not found.
        """
        ...

    def get_version_by_tag(
        self,
        knowledge_base_id: str,
        version_tag: str,
    ) -> Optional[KnowledgeBaseVersion]:
        """
        Get a version by knowledge base ID and tag.

        Args:
            knowledge_base_id: Knowledge base ID.
            version_tag: Version tag.

        Returns:
            Optional[KnowledgeBaseVersion]: The version, or None if not found.
        """
        ...

    def get_latest_version(
        self,
        knowledge_base_id: str,
        status: Optional[VersionStatus] = None,
    ) -> Optional[KnowledgeBaseVersion]:
        """
        Get the latest version for a knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID.
            status: Optional status filter.

        Returns:
            Optional[KnowledgeBaseVersion]: The latest version, or None.
        """
        ...

    def list_versions(
        self,
        knowledge_base_id: str,
        status: Optional[VersionStatus] = None,
    ) -> List[KnowledgeBaseVersion]:
        """
        List versions for a knowledge base.

        Args:
            knowledge_base_id: Knowledge base ID.
            status: Optional status filter.

        Returns:
            List[KnowledgeBaseVersion]: Matching versions.
        """
        ...

    def update_version_status(
        self,
        version_id: str,
        status: VersionStatus,
    ) -> None:
        """
        Update the status of a version.

        Args:
            version_id: Version ID.
            status: New status.

        Raises:
            ValueError: If the version doesn't exist.
        """
        ...

    def update_version(self, version: KnowledgeBaseVersion) -> None:
        """
        Update a version.

        Args:
            version: The version with updated fields.

        Raises:
            ValueError: If the version doesn't exist.
        """
        ...

    def delete_version(self, version_id: str) -> bool:
        """
        Delete a version.

        This also deletes all file versions for this version.

        Args:
            version_id: Version ID.

        Returns:
            bool: True if the version was deleted.
        """
        ...

    # ============ File Version Management ============

    def create_file_version(
        self,
        raw_file_id: str,
        knowledge_base_version_id: str,
        content_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileVersion:
        """
        Create a file version.

        Args:
            raw_file_id: Raw file ID.
            knowledge_base_version_id: Knowledge base version ID.
            content_hash: Content hash for change detection.
            metadata: Optional metadata (source_type, source_uri, original_name, etc.).

        Returns:
            FileVersion: The created file version.
        """
        ...

    def get_file_version(self, file_version_id: str) -> Optional[FileVersion]:
        """
        Get a file version by ID.

        Args:
            file_version_id: File version ID.

        Returns:
            Optional[FileVersion]: The file version, or None if not found.
        """
        ...

    def get_file_versions(
        self,
        knowledge_base_version_id: str,
        index_status: Optional[IndexStatus] = None,
    ) -> List[FileVersion]:
        """
        Get all file versions for a knowledge base version.

        Args:
            knowledge_base_version_id: Knowledge base version ID.
            index_status: Optional status filter.

        Returns:
            List[FileVersion]: Matching file versions.
        """
        ...

    def get_file_version_by_raw_file(
        self,
        raw_file_id: str,
        knowledge_base_version_id: str,
    ) -> Optional[FileVersion]:
        """
        Get a file version for a specific raw file and KB version.

        Args:
            raw_file_id: Raw file ID.
            knowledge_base_version_id: Knowledge base version ID.

        Returns:
            Optional[FileVersion]: The file version, or None if not found.
        """
        ...

    def get_changed_files(
        self,
        knowledge_base_version_id: str,
        base_version_id: str,
    ) -> List[FileVersion]:
        """
        Get file versions that have changed relative to a base version.

        Used for incremental builds. Returns files that:
        - Are new (not in base version)
        - Have different content_hash (modified)

        Args:
            knowledge_base_version_id: Current version ID.
            base_version_id: Base version to compare against.

        Returns:
            List[FileVersion]: Changed file versions.
        """
        ...

    def update_file_index_status(
        self,
        file_version_id: str,
        status: IndexStatus,
    ) -> None:
        """
        Update the index status of a file version.

        Args:
            file_version_id: File version ID.
            status: New index status.
        """
        ...

    def count_file_versions(
        self,
        knowledge_base_version_id: str,
        index_status: Optional[IndexStatus] = None,
    ) -> int:
        """
        Count file versions.

        Args:
            knowledge_base_version_id: Knowledge base version ID.
            index_status: Optional status filter.

        Returns:
            int: Number of matching file versions.
        """
        ...
