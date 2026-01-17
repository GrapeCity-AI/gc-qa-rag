"""
Environment schemas - Pydantic models for environment operations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EnvironmentCreate(BaseModel):
    """Request model for creating an environment."""

    name: str = Field(..., min_length=1, max_length=100, description="Environment name")
    environment_type: str = Field(
        ...,
        description="Environment type: development, staging, or production"
    )
    description: str = Field(default="", max_length=500, description="Environment description")
    config: dict[str, Any] = Field(default_factory=dict, description="Environment configuration")
    is_default: bool = Field(default=False, description="Whether this is the default environment")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Production",
                    "environment_type": "production",
                    "description": "Production Qdrant cluster",
                    "config": {
                        "qdrant_url": "https://qdrant.example.com",
                        "collection_prefix": "prod_"
                    },
                    "is_default": True
                }
            ]
        }
    }


class EnvironmentUpdate(BaseModel):
    """Request model for updating an environment."""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="Environment name")
    description: str | None = Field(default=None, max_length=500, description="Environment description")
    config: dict[str, Any] | None = Field(default=None, description="Environment configuration")
    is_default: bool | None = Field(default=None, description="Whether this is the default environment")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Production v2",
                    "config": {"qdrant_url": "https://qdrant-v2.example.com"}
                }
            ]
        }
    }


class EnvironmentResponse(BaseModel):
    """Response model for environment."""

    id: str = Field(..., description="Environment ID")
    name: str = Field(..., description="Environment name")
    environment_type: str = Field(..., description="Environment type")
    description: str = Field(default="", description="Environment description")
    config: dict[str, Any] = Field(default_factory=dict, description="Environment configuration")
    is_default: bool = Field(default=False, description="Whether this is the default environment")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True
    }


class EnvironmentSummary(BaseModel):
    """Summary view of environment for lists."""

    id: str = Field(..., description="Environment ID")
    name: str = Field(..., description="Environment name")
    environment_type: str = Field(..., description="Environment type")
    is_default: bool = Field(default=False, description="Whether this is the default environment")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True
    }


class EnvironmentTestRequest(BaseModel):
    """Request model for testing environment connection."""

    timeout_seconds: int = Field(default=10, ge=1, le=60, description="Connection timeout in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"timeout_seconds": 10}
            ]
        }
    }


class EnvironmentTestResult(BaseModel):
    """Response model for environment connection test."""

    success: bool = Field(..., description="Whether the connection test succeeded")
    message: str = Field(..., description="Test result message")
    latency_ms: float | None = Field(default=None, description="Connection latency in milliseconds")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional test details")
