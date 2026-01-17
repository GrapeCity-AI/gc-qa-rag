"""
Common schemas - Shared response models for the API.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiError(BaseModel):
    """API error detail."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: str | None = Field(default=None, description="Field that caused the error")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    data: T | None = Field(default=None, description="Response data")
    meta: dict[str, Any] | None = Field(default=None, description="Response metadata")
    errors: list[ApiError] = Field(default_factory=list, description="List of errors")

    @classmethod
    def success(cls, data: T, meta: dict[str, Any] | None = None) -> "ApiResponse[T]":
        """Create a successful response."""
        return cls(data=data, meta=meta, errors=[])

    @classmethod
    def error(cls, errors: list[ApiError]) -> "ApiResponse[T]":
        """Create an error response."""
        return cls(data=None, errors=errors)


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""

    data: list[T] = Field(default_factory=list, description="Page of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    errors: list[ApiError] = Field(default_factory=list, description="List of errors")


class HealthStatus(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current timestamp")
    components: dict[str, str] = Field(default_factory=dict, description="Component health status")


class CountStats(BaseModel):
    """Count statistics for dashboard."""

    knowledge_bases: int = Field(default=0, description="Total knowledge bases")
    versions: int = Field(default=0, description="Total versions")
    pending_tasks: int = Field(default=0, description="Pending tasks")
    running_tasks: int = Field(default=0, description="Running tasks")
    completed_tasks: int = Field(default=0, description="Completed tasks (last 24h)")
    failed_tasks: int = Field(default=0, description="Failed tasks (last 24h)")
