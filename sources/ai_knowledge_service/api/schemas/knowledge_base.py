"""
Knowledge Base schemas - Pydantic models for knowledge base operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """Request model for creating a knowledge base."""

    name: str = Field(..., min_length=1, max_length=255, description="Knowledge base name")
    description: str = Field(default="", max_length=2000, description="Knowledge base description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Product Documentation",
                    "description": "Documentation for our main product",
                    "metadata": {"category": "docs", "language": "en"}
                }
            ]
        }
    }


class KnowledgeBaseUpdate(BaseModel):
    """Request model for updating a knowledge base."""

    name: str | None = Field(default=None, min_length=1, max_length=255, description="Knowledge base name")
    description: str | None = Field(default=None, max_length=2000, description="Knowledge base description")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class KnowledgeBaseResponse(BaseModel):
    """Response model for knowledge base."""

    id: str = Field(..., description="Knowledge base ID")
    name: str = Field(..., description="Knowledge base name")
    description: str = Field(default="", description="Knowledge base description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Computed fields for list view
    version_count: int = Field(default=0, description="Number of versions")
    latest_version: str | None = Field(default=None, description="Latest version tag")

    model_config = {
        "from_attributes": True
    }


class KnowledgeBaseSummary(BaseModel):
    """Summary view of knowledge base for lists."""

    id: str = Field(..., description="Knowledge base ID")
    name: str = Field(..., description="Knowledge base name")
    description: str = Field(default="", description="Knowledge base description")
    version_count: int = Field(default=0, description="Number of versions")
    latest_version: str | None = Field(default=None, description="Latest version tag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True
    }
