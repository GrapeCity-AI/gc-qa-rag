"""
API Schemas - Pydantic models for API request/response validation.
"""

from ai_knowledge_service.api.schemas.common import ApiError, ApiResponse, PaginatedResponse
from ai_knowledge_service.api.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from ai_knowledge_service.api.schemas.task import (
    TaskResponse,
    TaskResultResponse,
)
from ai_knowledge_service.api.schemas.version import (
    VersionBuildRequest,
    VersionCreate,
    VersionPublishRequest,
    VersionResponse,
)

__all__ = [
    # Common
    "ApiResponse",
    "ApiError",
    "PaginatedResponse",
    # Knowledge Base
    "KnowledgeBaseCreate",
    "KnowledgeBaseUpdate",
    "KnowledgeBaseResponse",
    # Version
    "VersionCreate",
    "VersionResponse",
    "VersionBuildRequest",
    "VersionPublishRequest",
    # Task
    "TaskResponse",
    "TaskResultResponse",
]
