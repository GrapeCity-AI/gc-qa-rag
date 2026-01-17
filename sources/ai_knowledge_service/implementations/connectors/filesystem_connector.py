"""
Filesystem Connector - Connector for local filesystem data sources.

Supports recursive directory traversal, file filtering, and incremental
mode based on file modification times.
"""

import logging
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Set

from ai_knowledge_service.abstractions.pipelines.source import (
    ConnectionResult,
    ISourceConnector,
    SourceConfig,
    SourceRecord,
)


# Common file extensions that might not have MIME types registered
EXTENSION_MIME_MAP = {
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".json": "application/json",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
    ".rst": "text/x-rst",
    ".tex": "application/x-tex",
    ".csv": "text/csv",
    ".tsv": "text/tab-separated-values",
}


class FilesystemConnector(ISourceConnector):
    """
    Filesystem Connector - Connects to local filesystem for data ingestion.

    Supports:
    - Recursive directory traversal
    - File extension filtering
    - Incremental mode (files modified since timestamp)
    - MIME type detection
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the connector.

        Args:
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._config: Optional[SourceConfig] = None
        self._root_path: Optional[Path] = None
        self._extensions: Set[str] = set()
        self._recursive: bool = True
        self._exclude_patterns: List[str] = []

    @property
    def source_type(self) -> str:
        """Get the source type identifier."""
        return "filesystem"

    def configure(self, config: SourceConfig) -> None:
        """
        Configure the connector.

        Expected connection_params:
        - path: str - Root path to scan
        - recursive: bool - Whether to scan recursively (default: True)

        Expected fetch_options:
        - extensions: List[str] - Allowed file extensions (e.g., [".txt", ".md"])
        - exclude_patterns: List[str] - Glob patterns to exclude
        """
        if config.connector_type != self.source_type:
            raise ValueError(
                f"Invalid connector type: {config.connector_type}, "
                f"expected: {self.source_type}"
            )

        path = config.get_connection_param("path")
        if not path:
            raise ValueError("Connection parameter 'path' is required")

        self._root_path = Path(path)
        self._recursive = config.get_connection_param("recursive", True)

        # Parse extensions
        extensions = config.get_fetch_option("extensions", [])
        self._extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in extensions
        }

        # Parse exclude patterns
        self._exclude_patterns = config.get_fetch_option("exclude_patterns", [])

        self._config = config

        self._logger.info(
            f"Configured filesystem connector: path={self._root_path}, "
            f"recursive={self._recursive}, extensions={self._extensions}"
        )

    def validate_connection(self) -> ConnectionResult:
        """Validate that the filesystem path is accessible."""
        if self._root_path is None:
            return ConnectionResult.error("Connector not configured")

        if not self._root_path.exists():
            return ConnectionResult.error(
                f"Path does not exist: {self._root_path}",
                path=str(self._root_path),
            )

        if not self._root_path.is_dir():
            return ConnectionResult.error(
                f"Path is not a directory: {self._root_path}",
                path=str(self._root_path),
            )

        if not os.access(self._root_path, os.R_OK):
            return ConnectionResult.error(
                f"Path is not readable: {self._root_path}",
                path=str(self._root_path),
            )

        return ConnectionResult.success(f"Connected to {self._root_path}")

    def fetch(self) -> Iterator[SourceRecord]:
        """Fetch all records from the filesystem."""
        if self._root_path is None:
            raise ConnectionError("Connector not configured")

        validation = self.validate_connection()
        if not validation.is_connected:
            raise ConnectionError(validation.message)

        self._logger.info(f"Starting full fetch from {self._root_path}")

        yield from self._scan_directory(self._root_path, since=None)

    def fetch_incremental(
        self,
        since: datetime,
    ) -> Iterator[SourceRecord]:
        """Fetch files modified since the given timestamp."""
        if self._root_path is None:
            raise ConnectionError("Connector not configured")

        validation = self.validate_connection()
        if not validation.is_connected:
            raise ConnectionError(validation.message)

        self._logger.info(
            f"Starting incremental fetch from {self._root_path} since {since}"
        )

        yield from self._scan_directory(self._root_path, since=since)

    @property
    def supports_incremental(self) -> bool:
        """Check if this connector supports incremental fetching."""
        return True

    def get_record_count(self) -> Optional[int]:
        """Get the total number of files (if countable without full scan)."""
        if self._root_path is None:
            return None

        # For small directories, we can count; for large ones, return None
        try:
            count = 0
            for _ in self._scan_directory(self._root_path, since=None):
                count += 1
                if count > 10000:
                    return None  # Too many files, don't count
            return count
        except Exception:
            return None

    def _scan_directory(
        self,
        directory: Path,
        since: Optional[datetime],
    ) -> Iterator[SourceRecord]:
        """
        Scan a directory for files.

        Args:
            directory: Directory to scan.
            since: Only yield files modified after this time (optional).

        Yields:
            SourceRecord for each matching file.
        """
        try:
            entries = list(directory.iterdir())
        except PermissionError:
            self._logger.warning(f"Permission denied: {directory}")
            return
        except OSError as e:
            self._logger.warning(f"Error scanning directory {directory}: {e}")
            return

        for entry in entries:
            try:
                # Skip excluded patterns
                if self._is_excluded(entry):
                    continue

                if entry.is_file():
                    record = self._process_file(entry, since)
                    if record is not None:
                        yield record

                elif entry.is_dir() and self._recursive:
                    yield from self._scan_directory(entry, since)

            except PermissionError:
                self._logger.warning(f"Permission denied: {entry}")
            except OSError as e:
                self._logger.warning(f"Error processing {entry}: {e}")

    def _process_file(
        self,
        file_path: Path,
        since: Optional[datetime],
    ) -> Optional[SourceRecord]:
        """
        Process a single file.

        Args:
            file_path: Path to the file.
            since: Only process files modified after this time (optional).

        Returns:
            SourceRecord if the file matches criteria, None otherwise.
        """
        # Check extension filter
        if self._extensions and file_path.suffix.lower() not in self._extensions:
            return None

        # Get file stats
        try:
            stat = file_path.stat()
        except OSError as e:
            self._logger.warning(f"Cannot stat file {file_path}: {e}")
            return None

        # Check modification time for incremental
        mtime = datetime.fromtimestamp(stat.st_mtime)
        if since is not None and mtime <= since:
            return None

        # Read content
        try:
            content = file_path.read_bytes()
        except OSError as e:
            self._logger.warning(f"Cannot read file {file_path}: {e}")
            return None

        # Determine MIME type
        mime_type = self._get_mime_type(file_path)

        # Create source URI (relative to root)
        source_uri = str(file_path.relative_to(self._root_path))

        return SourceRecord(
            source_uri=source_uri,
            content=content,
            content_type=mime_type,
            metadata={
                "source_type": self.source_type,
                "original_name": file_path.name,
                "file_path": str(file_path.absolute()),
                "size_bytes": stat.st_size,
                "modified_at": mtime.isoformat(),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            },
            fetched_at=datetime.now(),
        )

    def _is_excluded(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        name = path.name

        # Common exclusions
        if name.startswith("."):
            return True
        if name in ("__pycache__", "node_modules", ".git", ".svn"):
            return True

        # Check custom exclude patterns
        for pattern in self._exclude_patterns:
            if path.match(pattern):
                return True

        return False

    def _get_mime_type(self, file_path: Path) -> str:
        """Get the MIME type for a file."""
        # Check extension map first
        suffix = file_path.suffix.lower()
        if suffix in EXTENSION_MIME_MAP:
            return EXTENSION_MIME_MAP[suffix]

        # Use mimetypes module
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            return mime_type

        # Fallback
        return "application/octet-stream"
