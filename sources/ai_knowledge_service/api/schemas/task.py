"""
Task schemas - Pydantic models for task operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProcessingErrorResponse(BaseModel):
    """Response model for processing error."""

    item_id: str = Field(..., description="ID of the failed item")
    item_name: str = Field(..., description="Human-readable name")
    step: str = Field(..., description="Processing step where error occurred")
    error_type: str = Field(..., description="Error type/category")
    error_message: str = Field(..., description="Error message")
    stacktrace: str | None = Field(default=None, description="Stack trace")
    timestamp: datetime = Field(..., description="Error timestamp")
    recoverable: bool = Field(default=True, description="Whether the error can be retried")


class StepStatsResponse(BaseModel):
    """Response model for step statistics."""

    step_type: str = Field(..., description="Step type")
    input_count: int = Field(..., description="Input count")
    output_count: int = Field(..., description="Output count")
    duration_seconds: float = Field(..., description="Duration in seconds")
    errors_count: int = Field(default=0, description="Number of errors")
    success_rate: float = Field(..., description="Success rate (0-1)")


class TaskResponse(BaseModel):
    """Response model for task."""

    id: str = Field(..., description="Task ID")
    task_type: str = Field(..., description="Task type: ingestion, indexing, or publishing")
    knowledge_base_id: str = Field(..., description="Knowledge base ID")
    knowledge_base_version_id: str = Field(..., description="Knowledge base version ID")

    # Status
    status: str = Field(..., description="Task status")
    priority: int = Field(default=0, description="Task priority")
    retry_count: int = Field(default=0, description="Current retry count")
    max_retries: int = Field(default=3, description="Maximum retries")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Computed fields
    knowledge_base_name: str | None = Field(default=None, description="Knowledge base name")
    version_tag: str | None = Field(default=None, description="Version tag")
    duration_seconds: float | None = Field(default=None, description="Duration in seconds")

    model_config = {
        "from_attributes": True
    }


class TaskResultResponse(BaseModel):
    """Response model for task result."""

    task_id: str = Field(..., description="Task ID")
    task_type: str = Field(..., description="Task type")
    status: str = Field(..., description="Result status")

    # Statistics
    total_items: int = Field(default=0, description="Total items processed")
    succeeded_count: int = Field(default=0, description="Successful items")
    failed_count: int = Field(default=0, description="Failed items")
    skipped_count: int = Field(default=0, description="Skipped items")

    # Errors
    errors: list[ProcessingErrorResponse] = Field(default_factory=list, description="Processing errors")

    # Timestamps
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: datetime = Field(..., description="Completion timestamp")

    # Computed
    duration_seconds: float = Field(..., description="Duration in seconds")
    success_rate: float = Field(..., description="Success rate (0-1)")

    # Type-specific fields (for indexing tasks)
    step_stats: dict[str, StepStatsResponse] = Field(default_factory=dict, description="Per-step statistics")
    index_records_count: int = Field(default=0, description="Index records created")

    # Type-specific fields (for ingestion tasks)
    new_files_count: int = Field(default=0, description="New files ingested")
    updated_files_count: int = Field(default=0, description="Updated files")
    unchanged_files_count: int = Field(default=0, description="Unchanged files")

    # Type-specific fields (for publishing tasks)
    target_collection: str | None = Field(default=None, description="Target collection name")
    alias_applied: str | None = Field(default=None, description="Alias applied")

    model_config = {
        "from_attributes": True
    }


class TaskSummary(BaseModel):
    """Summary view of task for lists."""

    id: str = Field(..., description="Task ID")
    task_type: str = Field(..., description="Task type")
    status: str = Field(..., description="Task status")
    knowledge_base_name: str | None = Field(default=None, description="Knowledge base name")
    version_tag: str | None = Field(default=None, description="Version tag")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")

    model_config = {
        "from_attributes": True
    }


class TaskCancelRequest(BaseModel):
    """Request model for cancelling a task."""

    reason: str | None = Field(default=None, description="Cancellation reason")


class TaskRetryRequest(BaseModel):
    """Request model for retrying a task."""

    reset_retry_count: bool = Field(default=True, description="Whether to reset the retry count")
    priority: int | None = Field(default=None, description="New priority for the retried task")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reset_retry_count": True,
                    "priority": 1
                }
            ]
        }
    }


class TaskProgressUpdate(BaseModel):
    """WebSocket message for task progress updates."""

    task_id: str = Field(..., description="Task ID")
    event_type: str = Field(..., description="Event type: started, progress, completed, failed")
    status: str = Field(..., description="Current task status")
    progress: float | None = Field(default=None, description="Progress percentage (0-100)")
    message: str | None = Field(default=None, description="Progress message")
    current_step: str | None = Field(default=None, description="Current processing step")
    items_processed: int | None = Field(default=None, description="Items processed so far")
    total_items: int | None = Field(default=None, description="Total items to process")
    timestamp: datetime = Field(default_factory=datetime.now, description="Update timestamp")
