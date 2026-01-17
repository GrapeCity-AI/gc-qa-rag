"""
Publishing interfaces - Defines how indexes are published to target environments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ai_knowledge_service.abstractions.pipelines.source import (
    ConnectionResult,
)


@dataclass
class EnvironmentCapabilities:
    """Capabilities of a target environment."""

    supported_index_types: List[str] = field(default_factory=list)
    supports_alias: bool = True
    supports_incremental: bool = True
    max_batch_size: int = 1000
    max_vector_dimensions: int = 4096
    metadata: Dict[str, Any] = field(default_factory=dict)

    def supports_index_type(self, index_type: str) -> bool:
        """Check if an index type is supported."""
        return index_type in self.supported_index_types


@dataclass
class ExportOptions:
    """Options for exporting indexes."""

    include_payloads: bool = True
    include_vectors: bool = True
    batch_size: int = 1000
    compression: Optional[str] = None  # "gzip", "zstd", etc.
    format: str = "jsonl"  # "jsonl", "parquet", etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool
    output_path: str = ""
    records_exported: int = 0
    bytes_written: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def failure(cls, error: str) -> "ExportResult":
        """Create a failed export result."""
        return cls(success=False, error_message=error)


@dataclass
class ImportOptions:
    """Options for importing indexes."""

    batch_size: int = 1000
    overwrite_existing: bool = False
    validate_schema: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportResult:
    """Result of an import operation."""

    success: bool
    target_collection: str = ""
    records_imported: int = 0
    records_skipped: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def failure(cls, error: str) -> "ImportResult":
        """Create a failed import result."""
        return cls(success=False, error_message=error)


@runtime_checkable
class ITargetEnvironment(Protocol):
    """
    Target Environment - Represents a deployment target for indexes.

    Target environments can be:
    - Production vector databases
    - Staging environments
    - Other isolated deployments
    """

    @property
    def environment_id(self) -> str:
        """Get the environment identifier."""
        ...

    @property
    def environment_name(self) -> str:
        """Get the human-readable environment name."""
        ...

    def validate_connection(self) -> ConnectionResult:
        """
        Validate connection to the target environment.

        Returns:
            ConnectionResult: Connection test result.
        """
        ...

    def get_capabilities(self) -> EnvironmentCapabilities:
        """
        Get the capabilities of this environment.

        Returns:
            EnvironmentCapabilities: Environment capabilities.
        """
        ...

    def list_collections(self) -> List[str]:
        """
        List existing collections in the environment.

        Returns:
            List[str]: Collection names.
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

    def get_alias(self, alias: str) -> Optional[str]:
        """
        Get the collection name for an alias.

        Args:
            alias: Alias name.

        Returns:
            Optional[str]: Collection name, or None if alias doesn't exist.
        """
        ...


@runtime_checkable
class IIndexExporter(Protocol):
    """
    Index Exporter - Exports indexes from local storage.

    Used to extract index data for transfer to target environments.
    """

    def export(
        self,
        collection: str,
        output_path: str,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Export a collection to a file.

        Args:
            collection: Source collection name.
            output_path: Path to write exported data.
            options: Export options.

        Returns:
            ExportResult: Export operation result.
        """
        ...

    def export_partial(
        self,
        collection: str,
        file_version_ids: List[str],
        output_path: str,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Export specific records from a collection.

        Args:
            collection: Source collection name.
            file_version_ids: IDs of file versions to export.
            output_path: Path to write exported data.
            options: Export options.

        Returns:
            ExportResult: Export operation result.
        """
        ...

    def get_export_size_estimate(
        self,
        collection: str,
        file_version_ids: Optional[List[str]] = None,
    ) -> int:
        """
        Estimate the size of an export in bytes.

        Args:
            collection: Source collection name.
            file_version_ids: Optional specific file versions.

        Returns:
            int: Estimated size in bytes.
        """
        ...


@runtime_checkable
class IIndexImporter(Protocol):
    """
    Index Importer - Imports indexes to a target environment.

    Used to load exported index data into target environments.
    """

    def import_index(
        self,
        source_path: str,
        target_collection: str,
        target_environment: ITargetEnvironment,
        options: Optional[ImportOptions] = None,
    ) -> ImportResult:
        """
        Import index data to a target collection.

        Args:
            source_path: Path to exported data.
            target_collection: Target collection name.
            target_environment: Target environment.
            options: Import options.

        Returns:
            ImportResult: Import operation result.
        """
        ...

    def validate_import_file(self, source_path: str) -> List[str]:
        """
        Validate an import file.

        Args:
            source_path: Path to the import file.

        Returns:
            List[str]: List of validation errors. Empty if valid.
        """
        ...


@runtime_checkable
class IRawFileExporter(Protocol):
    """
    Raw File Exporter - Exports raw files for publishing.

    Used when target environments need access to original documents.
    """

    def export(
        self,
        file_ids: List[str],
        output_path: str,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Export raw files to a directory.

        Args:
            file_ids: IDs of files to export.
            output_path: Directory to write files.
            options: Export options.

        Returns:
            ExportResult: Export operation result.
        """
        ...

    def export_for_version(
        self,
        knowledge_base_version_id: str,
        output_path: str,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Export all raw files for a knowledge base version.

        Args:
            knowledge_base_version_id: Version ID.
            output_path: Directory to write files.
            options: Export options.

        Returns:
            ExportResult: Export operation result.
        """
        ...


@runtime_checkable
class IAliasManager(Protocol):
    """
    Alias Manager - Manages collection aliases.

    Used for blue-green deployments and version switching.
    """

    def create_alias(
        self,
        alias: str,
        collection: str,
        environment: ITargetEnvironment,
    ) -> bool:
        """
        Create or update an alias.

        Args:
            alias: Alias name.
            collection: Target collection name.
            environment: Target environment.

        Returns:
            bool: True if successful.
        """
        ...

    def delete_alias(
        self,
        alias: str,
        environment: ITargetEnvironment,
    ) -> bool:
        """
        Delete an alias.

        Args:
            alias: Alias name.
            environment: Target environment.

        Returns:
            bool: True if successful.
        """
        ...

    def switch_alias(
        self,
        alias: str,
        old_collection: str,
        new_collection: str,
        environment: ITargetEnvironment,
    ) -> bool:
        """
        Atomically switch an alias from one collection to another.

        Args:
            alias: Alias name.
            old_collection: Current collection (for verification).
            new_collection: New target collection.
            environment: Target environment.

        Returns:
            bool: True if successful.
        """
        ...
