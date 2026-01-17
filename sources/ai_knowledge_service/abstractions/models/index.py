"""
Index models - Models for index records and schema definitions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class FieldType(Enum):
    """Index field types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    TEXT = "text"  # Full-text searchable
    KEYWORD = "keyword"  # Exact match
    VECTOR = "vector"  # Dense vector
    SPARSE_VECTOR = "sparse_vector"  # Sparse vector


@dataclass
class FieldDefinition:
    """Definition of a field in an index schema."""

    name: str
    field_type: FieldType
    required: bool = False
    indexed: bool = True
    stored: bool = True
    description: str = ""

    def __post_init__(self):
        if not self.name:
            raise ValueError("Field name cannot be empty")


@dataclass
class VectorConfig:
    """Configuration for vector fields in an index."""

    dimensions: int
    distance_metric: str = "cosine"  # "cosine", "euclidean", "dot"
    sparse_enabled: bool = False
    quantization: Optional[str] = None  # "scalar", "binary", etc.

    def __post_init__(self):
        if self.dimensions <= 0:
            raise ValueError("Dimensions must be positive")
        if self.distance_metric not in ("cosine", "euclidean", "dot"):
            raise ValueError(
                f"Invalid distance metric: {self.distance_metric}"
            )


@dataclass
class IndexSchema:
    """Schema definition for an index collection."""

    index_type: str  # "vector", "structured", "fulltext"
    fields: List[FieldDefinition] = field(default_factory=list)
    vector_config: Optional[VectorConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.index_type:
            raise ValueError("Index type cannot be empty")
        if self.index_type == "vector" and self.vector_config is None:
            raise ValueError("Vector index requires vector_config")

    def get_field(self, name: str) -> Optional[FieldDefinition]:
        """Get field definition by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    @property
    def field_names(self) -> List[str]:
        """Get list of all field names."""
        return [f.name for f in self.fields]


@dataclass
class IndexRecord:
    """
    Index Record - A single record to be written to an index.

    This is the unit of data that gets stored in the index storage.
    """

    id: str
    file_version_id: str  # Traceability to file version
    index_type: str  # "vector", "structured", "fulltext"
    content: Dict[str, Any] = field(default_factory=dict)  # Index content (vectors, text)
    payload: Dict[str, Any] = field(default_factory=dict)  # Additional data (Q&A, metadata)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Index record ID cannot be empty")
        if not self.file_version_id:
            raise ValueError("File version ID cannot be empty")
        if not self.index_type:
            raise ValueError("Index type cannot be empty")

    def get_content(self, key: str, default: Any = None) -> Any:
        """Get content value by key."""
        return self.content.get(key, default)

    def get_payload(self, key: str, default: Any = None) -> Any:
        """Get payload value by key."""
        return self.payload.get(key, default)

    def set_content(self, key: str, value: Any) -> None:
        """Set content value."""
        self.content[key] = value

    def set_payload(self, key: str, value: Any) -> None:
        """Set payload value."""
        self.payload[key] = value
