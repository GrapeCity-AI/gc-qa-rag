"""
Qdrant-compatible data models for API compatibility
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import time


class QdrantResponse(BaseModel):
    """Standard Qdrant API response wrapper"""
    result: Any = Field(..., description="Response result data")
    status: str = Field(default="ok", description="Response status")
    time: float = Field(default_factory=lambda: round(time.time() - time.time(), 6), description="Response time in seconds")

    @classmethod
    def success(cls, result: Any, response_time: float = 0.001) -> "QdrantResponse":
        """Create a successful response"""
        return cls(result=result, status="ok", time=response_time)


class Distance(str, Enum):
    """Distance metrics"""
    COSINE = "Cosine"
    EUCLIDEAN = "Euclid"
    DOT = "Dot"


class VectorParams(BaseModel):
    """Vector configuration parameters"""
    size: int = Field(..., description="Vector dimension")
    distance: Distance = Field(default=Distance.COSINE, description="Distance metric")


class CollectionInfo(BaseModel):
    """Collection information"""
    status: str = Field(default="green")
    optimizer_status: str = Field(default="ok")
    vectors_count: int = Field(default=0)
    indexed_vectors_count: int = Field(default=0)
    points_count: int = Field(default=0)
    segments_count: int = Field(default=1)
    config: Dict[str, Any] = Field(default_factory=dict)


class PointStruct(BaseModel):
    """Point structure for upsert operations - supports both single and multi-vector formats"""
    id: Union[int, str]
    vector: Union[Dict[str, Any], List[float]] = Field(
        ...,
        description="Vector data - named vector dictionary (dense/sparse) or single vector list"
    )
    payload: Optional[Dict[str, Any]] = None

    @field_validator('vector', mode='before')
    @classmethod
    def validate_vector(cls, v):
        """Custom validator for vector field to handle both dense and sparse vector formats"""
        if isinstance(v, dict):
            # Multi-vector format - validate that all values are valid vector formats
            for key, value in v.items():
                if isinstance(value, list):
                    # Dense vector - list of numbers
                    if not all(isinstance(x, (int, float)) for x in value):
                        raise ValueError(f"Dense vector '{key}' must be a list of numbers")
                elif isinstance(value, dict):
                    # Sparse vector - check for indices/values format or other sparse formats
                    if 'indices' in value and 'values' in value:
                        # Standard sparse format
                        if not isinstance(value['indices'], list) or not isinstance(value['values'], list):
                            raise ValueError(f"Sparse vector '{key}' indices and values must be lists")
                        if len(value['indices']) != len(value['values']):
                            raise ValueError(f"Sparse vector '{key}' indices and values must have same length")
                        if not all(isinstance(x, int) for x in value['indices']):
                            raise ValueError(f"Sparse vector '{key}' indices must be integers")
                        if not all(isinstance(x, (int, float)) for x in value['values']):
                            raise ValueError(f"Sparse vector '{key}' values must be numbers")
                    else:
                        # Other sparse formats - accept as-is for now
                        pass
                else:
                    raise ValueError(f"Vector '{key}' must be a list of numbers (dense) or a dict (sparse)")
            return v
        elif isinstance(v, list):
            # Single vector format - validate that all items are floats
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("Vector must be a list of numbers")
            return v
        else:
            raise ValueError("Vector must be either a list of numbers or a dictionary of named vectors")


class SearchRequest(BaseModel):
    """Search request model"""
    vector: List[float]
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filter: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    score_threshold: Optional[float] = None
    with_payload: Union[bool, List[str]] = Field(default=True)
    with_vector: bool = Field(default=False)


class ScrollRequest(BaseModel):
    """Scroll request model"""
    offset: Optional[Union[int, str]] = None
    limit: int = Field(default=10, ge=1, le=100)
    filter: Optional[Dict[str, Any]] = None
    with_payload: Union[bool, List[str]] = Field(default=True)
    with_vector: bool = Field(default=False)


class ScoredPoint(BaseModel):
    """Scored point in search results"""
    id: Union[int, str]
    version: int = Field(default=0)
    score: float
    payload: Optional[Dict[str, Any]] = None
    vector: Optional[List[float]] = None


class SearchResult(BaseModel):
    """Search result response"""
    result: List[ScoredPoint]
    status: str = Field(default="ok")
    time: float = Field(default=0.0)


class UpsertRequest(BaseModel):
    """Upsert request model"""
    points: List[PointStruct]


class UpsertResult(BaseModel):
    """Upsert operation result"""
    operation_id: int = Field(default=0)
    status: str = Field(default="acknowledged")


class DeleteRequest(BaseModel):
    """Delete request model"""
    points: List[Union[int, str]]


class DeleteResult(BaseModel):
    """Delete operation result"""
    operation_id: int = Field(default=0)
    status: str = Field(default="acknowledged")


class CreateCollectionRequest(BaseModel):
    """Create collection request - supports both single and multi-vector formats"""
    vectors: Union[VectorParams, Dict[str, VectorParams]] = Field(
        ...,
        description="Vector configuration - single vector or named vector configurations"
    )


class CollectionOperationResult(BaseModel):
    """Collection operation result"""
    result: bool = Field(default=True)
    status: str = Field(default="ok")
    time: float = Field(default=0.0)


class HealthInfo(BaseModel):
    """Health information"""
    status: str = Field(default="ok")
    version: str = Field(default="1.0.0")


# Hybrid search specific models
class HybridSearchRequest(BaseModel):
    """Hybrid search request combining dense and sparse vectors"""
    query_vector: List[float] = Field(..., description="Dense query vector (computed by AI service)")
    query_text: str = Field(..., description="Text query for sparse/BM25 search")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filter: Optional[Dict[str, Any]] = None
    fusion_weights: Optional[Dict[str, float]] = Field(
        default={"dense": 0.7, "sparse": 0.3},
        description="Weights for fusion of dense and sparse results"
    )
    with_payload: Union[bool, List[str]] = Field(default=True)
    with_vector: bool = Field(default=False)