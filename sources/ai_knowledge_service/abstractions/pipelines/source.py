"""
Source Connector interface - Defines how to connect to and fetch from data sources.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterator, Optional, Protocol, runtime_checkable


class ConnectionStatus(Enum):
    """Connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ConnectionResult:
    """Result of a connection attempt."""

    status: ConnectionStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_connected(self) -> bool:
        """Check if connection is successful."""
        return self.status == ConnectionStatus.CONNECTED

    @classmethod
    def success(cls, message: str = "Connected") -> "ConnectionResult":
        """Create a successful connection result."""
        return cls(status=ConnectionStatus.CONNECTED, message=message)

    @classmethod
    def error(cls, message: str, **details) -> "ConnectionResult":
        """Create an error connection result."""
        return cls(
            status=ConnectionStatus.ERROR,
            message=message,
            details=details,
        )


@dataclass
class SourceConfig:
    """Configuration for a data source connector."""

    connector_type: str  # "sitemap", "forum_api", "filesystem", etc.
    connection_params: Dict[str, Any] = field(default_factory=dict)
    fetch_options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.connector_type:
            raise ValueError("Connector type cannot be empty")

    def get_connection_param(self, key: str, default: Any = None) -> Any:
        """Get a connection parameter."""
        return self.connection_params.get(key, default)

    def get_fetch_option(self, key: str, default: Any = None) -> Any:
        """Get a fetch option."""
        return self.fetch_options.get(key, default)


@dataclass
class SourceRecord:
    """
    A record fetched from a data source.

    This is the raw data before it's stored as a RawFile.
    """

    source_uri: str  # Unique identifier for this record in the source
    content: bytes | str  # Raw content
    content_type: str  # MIME type
    metadata: Dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.source_uri:
            raise ValueError("Source URI cannot be empty")
        if self.content is None:
            raise ValueError("Content cannot be None")

    @property
    def content_bytes(self) -> bytes:
        """Get content as bytes."""
        if isinstance(self.content, bytes):
            return self.content
        return self.content.encode("utf-8")

    @property
    def content_str(self) -> str:
        """Get content as string."""
        if isinstance(self.content, str):
            return self.content
        return self.content.decode("utf-8")

    @property
    def size_bytes(self) -> int:
        """Get content size in bytes."""
        return len(self.content_bytes)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)


@runtime_checkable
class ISourceConnector(Protocol):
    """
    Source Connector - Interface for connecting to and fetching from data sources.

    Implementations should be stateless where possible.
    Configuration is passed via configure() method.
    """

    @property
    def source_type(self) -> str:
        """
        Get the source type identifier.

        Returns:
            str: A unique identifier for this connector type.
        """
        ...

    def configure(self, config: SourceConfig) -> None:
        """
        Configure the connector.

        Args:
            config: The source configuration.

        Raises:
            ValueError: If configuration is invalid.
        """
        ...

    def validate_connection(self) -> ConnectionResult:
        """
        Validate that the source is accessible.

        Returns:
            ConnectionResult: The connection test result.
        """
        ...

    def fetch(self) -> Iterator[SourceRecord]:
        """
        Fetch all records from the source.

        Yields:
            SourceRecord: Records from the source.

        Raises:
            ConnectionError: If unable to connect to the source.
        """
        ...

    def fetch_incremental(
        self,
        since: datetime,
    ) -> Iterator[SourceRecord]:
        """
        Fetch records modified since the given timestamp.

        Not all sources support incremental fetching. If not supported,
        this should fall back to full fetch.

        Args:
            since: Only fetch records modified after this time.

        Yields:
            SourceRecord: Records modified since the given time.
        """
        ...

    @property
    def supports_incremental(self) -> bool:
        """
        Check if this connector supports incremental fetching.

        Returns:
            bool: True if incremental fetch is supported.
        """
        ...

    def get_record_count(self) -> Optional[int]:
        """
        Get the total number of records available (if known).

        Returns:
            Optional[int]: Record count, or None if unknown.
        """
        ...
