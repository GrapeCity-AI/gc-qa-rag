"""
Version schemas - Pydantic models for version operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ai_knowledge_service.abstractions.models.knowledge_base import VersionStatus, IndexStatus


class VersionCreate(BaseModel):
    """Request model for creating a version."""

    version_tag: str = Field(..., min_length=1, max_length=100, description="Version tag (e.g., v1.0, 20260117)")
    parent_version_id: str | None = Field(default=None, description="Parent version ID for incremental builds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "version_tag": "v1.0.0",
                    "metadata": {"release_notes": "Initial release"}
                }
            ]
        }
    }


class VersionResponse(BaseModel):
    """Response model for version."""

    id: str = Field(..., description="Version ID")
    knowledge_base_id: str = Field(..., description="Parent knowledge base ID")
    version_tag: str = Field(..., description="Version tag")
    status: str = Field(..., description="Version status")
    parent_version_id: str | None = Field(default=None, description="Parent version ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    published_at: datetime | None = Field(default=None, description="Publication timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Computed fields
    file_count: int = Field(default=0, description="Number of files in this version")
    indexed_count: int = Field(default=0, description="Number of indexed files")
    pending_count: int = Field(default=0, description="Number of files pending indexing")
    failed_count: int = Field(default=0, description="Number of files that failed indexing")

    model_config = {
        "from_attributes": True
    }


class VersionSummary(BaseModel):
    """Summary view of version for lists."""

    id: str = Field(..., description="Version ID")
    version_tag: str = Field(..., description="Version tag")
    status: str = Field(..., description="Version status")
    file_count: int = Field(default=0, description="Number of files")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True
    }


class VersionBuildRequest(BaseModel):
    """Request model for triggering a build."""

    build_type: str = Field(default="full", description="Build type: full or incremental")
    pipeline_config: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Pipeline step configuration"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "build_type": "full",
                    "pipeline_config": [
                        {"step_type": "html_parser"},
                        {"step_type": "sentence_chunker", "config": {"max_chunk_size": 512}},
                        {"step_type": "dashscope_embedder"}
                    ]
                }
            ]
        }
    }


class VersionPublishRequest(BaseModel):
    """Request model for publishing a version."""

    target_environment_id: str = Field(..., description="Target environment ID")
    alias_name: str | None = Field(default=None, description="Alias name for the published version")
    publish_strategy: str = Field(default="blue_green", description="Publishing strategy: replace or blue_green")
    include_raw_files: bool = Field(default=False, description="Include raw files in publication")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "target_environment_id": "production",
                    "alias_name": "latest",
                    "publish_strategy": "blue_green"
                }
            ]
        }
    }


class FileVersionResponse(BaseModel):
    """Response model for file version."""

    id: str = Field(..., description="File version ID")
    raw_file_id: str = Field(..., description="Raw file ID")
    knowledge_base_version_id: str = Field(..., description="Parent version ID")
    content_hash: str = Field(..., description="Content hash for change detection")
    index_status: str = Field(..., description="Index status")
    indexed_at: datetime | None = Field(default=None, description="Indexing timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    # Raw file info (joined)
    source_type: str | None = Field(default=None, description="Source type")
    source_uri: str | None = Field(default=None, description="Source URI")
    original_name: str | None = Field(default=None, description="Original file name")
    mime_type: str | None = Field(default=None, description="MIME type")
    size_bytes: int | None = Field(default=None, description="File size in bytes")

    model_config = {
        "from_attributes": True
    }
