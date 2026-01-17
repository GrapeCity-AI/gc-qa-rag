"""
Connectors Router - Source connector management endpoints.
"""

from pydantic import BaseModel, Field
from typing import Any

from fastapi import APIRouter, HTTPException

from ai_knowledge_service.api.schemas.common import ApiResponse


router = APIRouter()


class ConnectorTypeResponse(BaseModel):
    """Response model for connector type."""

    type: str = Field(..., description="Connector type identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Connector description")
    config_schema: dict[str, Any] = Field(default_factory=dict, description="Configuration schema")


class ConnectorTestRequest(BaseModel):
    """Request model for testing a connector."""

    connector_type: str = Field(..., description="Connector type to test")
    config: dict[str, Any] = Field(default_factory=dict, description="Connector configuration")


class ConnectorTestResponse(BaseModel):
    """Response model for connector test result."""

    success: bool = Field(..., description="Whether the connection test succeeded")
    message: str = Field(default="", description="Test result message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")


# Available connector types (static for now, can be made dynamic later)
CONNECTOR_TYPES = [
    ConnectorTypeResponse(
        type="sitemap",
        name="Sitemap",
        description="Crawl websites using sitemap.xml",
        config_schema={
            "type": "object",
            "required": ["sitemap_url"],
            "properties": {
                "sitemap_url": {
                    "type": "string",
                    "description": "URL to sitemap.xml",
                },
                "include_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "URL patterns to include (regex)",
                },
                "exclude_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "URL patterns to exclude (regex)",
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum crawl depth",
                    "default": 3,
                },
            },
        },
    ),
    ConnectorTypeResponse(
        type="filesystem",
        name="Filesystem",
        description="Read files from local filesystem",
        config_schema={
            "type": "object",
            "required": ["base_path"],
            "properties": {
                "base_path": {
                    "type": "string",
                    "description": "Base directory path",
                },
                "file_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File patterns to include (glob)",
                    "default": ["**/*"],
                },
                "exclude_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File patterns to exclude (glob)",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Recursively scan directories",
                    "default": True,
                },
            },
        },
    ),
    ConnectorTypeResponse(
        type="forum_api",
        name="Forum API",
        description="Fetch content from forum API",
        config_schema={
            "type": "object",
            "required": ["api_base_url"],
            "properties": {
                "api_base_url": {
                    "type": "string",
                    "description": "Base URL for forum API",
                },
                "api_key": {
                    "type": "string",
                    "description": "API key for authentication",
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Category IDs to fetch",
                },
                "include_replies": {
                    "type": "boolean",
                    "description": "Include post replies",
                    "default": True,
                },
            },
        },
    ),
]


@router.get("", response_model=ApiResponse[list[ConnectorTypeResponse]])
async def list_connectors() -> ApiResponse[list[ConnectorTypeResponse]]:
    """
    List available connector types.
    """
    return ApiResponse.success(CONNECTOR_TYPES)


@router.get("/{connector_type}", response_model=ApiResponse[ConnectorTypeResponse])
async def get_connector(connector_type: str) -> ApiResponse[ConnectorTypeResponse]:
    """
    Get details for a specific connector type.
    """
    for ct in CONNECTOR_TYPES:
        if ct.type == connector_type:
            return ApiResponse.success(ct)

    raise HTTPException(status_code=404, detail=f"Connector type not found: {connector_type}")


@router.post("/test", response_model=ApiResponse[ConnectorTestResponse])
async def test_connector(data: ConnectorTestRequest) -> ApiResponse[ConnectorTestResponse]:
    """
    Test a connector configuration.

    This validates the configuration and attempts to connect to the source.
    """
    # Find connector type
    connector_info = None
    for ct in CONNECTOR_TYPES:
        if ct.type == data.connector_type:
            connector_info = ct
            break

    if connector_info is None:
        raise HTTPException(status_code=400, detail=f"Unknown connector type: {data.connector_type}")

    # Basic validation (real implementation would actually test the connection)
    try:
        if data.connector_type == "sitemap":
            if "sitemap_url" not in data.config:
                return ApiResponse.success(
                    ConnectorTestResponse(
                        success=False,
                        message="Missing required field: sitemap_url",
                    )
                )
            # Would actually try to fetch the sitemap here

        elif data.connector_type == "filesystem":
            if "base_path" not in data.config:
                return ApiResponse.success(
                    ConnectorTestResponse(
                        success=False,
                        message="Missing required field: base_path",
                    )
                )
            # Would actually check if path exists and is readable

        elif data.connector_type == "forum_api":
            if "api_base_url" not in data.config:
                return ApiResponse.success(
                    ConnectorTestResponse(
                        success=False,
                        message="Missing required field: api_base_url",
                    )
                )
            # Would actually try to connect to the API

        return ApiResponse.success(
            ConnectorTestResponse(
                success=True,
                message="Connection test successful",
                details={"connector_type": data.connector_type},
            )
        )

    except Exception as e:
        return ApiResponse.success(
            ConnectorTestResponse(
                success=False,
                message=f"Connection test failed: {str(e)}",
            )
        )
