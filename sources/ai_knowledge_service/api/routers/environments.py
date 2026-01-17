"""
Environments Router - Environment management endpoints.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from ai_knowledge_service.api.schemas.common import (
    ApiResponse,
    PaginatedResponse,
    PaginationMeta,
)
from ai_knowledge_service.api.schemas.environment import (
    EnvironmentCreate,
    EnvironmentResponse,
    EnvironmentSummary,
    EnvironmentTestRequest,
    EnvironmentTestResult,
    EnvironmentUpdate,
)
from ai_knowledge_service.api.dependencies import EnvStoreDep


router = APIRouter()


@dataclass
class Environment:
    """Environment model for in-memory storage."""
    id: str
    name: str
    environment_type: str
    description: str = ""
    config: dict = field(default_factory=dict)
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@router.get("", response_model=PaginatedResponse[EnvironmentSummary])
async def list_environments(
    env_store: EnvStoreDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    environment_type: str | None = Query(None, description="Filter by environment type"),
) -> PaginatedResponse[EnvironmentSummary]:
    """
    List all environments with pagination.
    """
    environments = env_store.list_environments()

    # Apply filter
    if environment_type:
        environments = [e for e in environments if e.environment_type == environment_type]

    # Sort by created_at descending
    environments.sort(key=lambda x: x.created_at, reverse=True)

    # Paginate
    total_items = len(environments)
    total_pages = (total_items + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = environments[start_idx:end_idx]

    summaries = [
        EnvironmentSummary(
            id=env.id,
            name=env.name,
            environment_type=env.environment_type,
            is_default=env.is_default,
            created_at=env.created_at,
        )
        for env in page_items
    ]

    return PaginatedResponse(
        data=summaries,
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.post("", response_model=ApiResponse[EnvironmentResponse], status_code=201)
async def create_environment(
    env_store: EnvStoreDep,
    data: EnvironmentCreate,
) -> ApiResponse[EnvironmentResponse]:
    """
    Create a new environment.
    """
    # Validate environment type
    valid_types = ["development", "staging", "production"]
    if data.environment_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid environment type: {data.environment_type}. Must be one of: {valid_types}"
        )

    # If this is the default, clear other defaults
    if data.is_default:
        env_store.clear_default()

    now = datetime.now()
    env = Environment(
        id=str(uuid.uuid4()),
        name=data.name,
        environment_type=data.environment_type,
        description=data.description,
        config=data.config,
        is_default=data.is_default,
        created_at=now,
        updated_at=now,
    )
    env_store.save_environment(env)

    return ApiResponse.success(
        EnvironmentResponse(
            id=env.id,
            name=env.name,
            environment_type=env.environment_type,
            description=env.description,
            config=env.config,
            is_default=env.is_default,
            created_at=env.created_at,
            updated_at=env.updated_at,
        )
    )


@router.get("/{env_id}", response_model=ApiResponse[EnvironmentResponse])
async def get_environment(
    env_id: str,
    env_store: EnvStoreDep,
) -> ApiResponse[EnvironmentResponse]:
    """
    Get an environment by ID.
    """
    env = env_store.get_environment(env_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Environment not found: {env_id}")

    return ApiResponse.success(
        EnvironmentResponse(
            id=env.id,
            name=env.name,
            environment_type=env.environment_type,
            description=env.description,
            config=env.config,
            is_default=env.is_default,
            created_at=env.created_at,
            updated_at=env.updated_at,
        )
    )


@router.put("/{env_id}", response_model=ApiResponse[EnvironmentResponse])
async def update_environment(
    env_id: str,
    env_store: EnvStoreDep,
    data: EnvironmentUpdate,
) -> ApiResponse[EnvironmentResponse]:
    """
    Update an environment.
    """
    env = env_store.get_environment(env_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Environment not found: {env_id}")

    # Update fields if provided
    if data.name is not None:
        env.name = data.name
    if data.description is not None:
        env.description = data.description
    if data.config is not None:
        env.config = data.config
    if data.is_default is not None:
        if data.is_default and not env.is_default:
            # Setting as default - clear other defaults first
            env_store.clear_default()
        env.is_default = data.is_default

    env.updated_at = datetime.now()
    env_store.save_environment(env)

    return ApiResponse.success(
        EnvironmentResponse(
            id=env.id,
            name=env.name,
            environment_type=env.environment_type,
            description=env.description,
            config=env.config,
            is_default=env.is_default,
            created_at=env.created_at,
            updated_at=env.updated_at,
        )
    )


@router.delete("/{env_id}", response_model=ApiResponse[None])
async def delete_environment(
    env_id: str,
    env_store: EnvStoreDep,
) -> ApiResponse[None]:
    """
    Delete an environment.
    """
    env = env_store.get_environment(env_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Environment not found: {env_id}")

    if env.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the default environment. Set another environment as default first."
        )

    env_store.delete_environment(env_id)

    return ApiResponse.success(None)


@router.post("/{env_id}/test", response_model=ApiResponse[EnvironmentTestResult])
async def test_environment(
    env_id: str,
    env_store: EnvStoreDep,
    data: EnvironmentTestRequest | None = None,
) -> ApiResponse[EnvironmentTestResult]:
    """
    Test connection to an environment.
    """
    env = env_store.get_environment(env_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Environment not found: {env_id}")

    # In a real implementation, this would actually test the connection
    # For now, return a mock success result
    timeout = data.timeout_seconds if data else 10

    # Simulate connection test based on environment type
    if env.environment_type == "production":
        # Simulate a slightly longer latency for production
        latency = 45.5
    else:
        latency = 12.3

    result = EnvironmentTestResult(
        success=True,
        message=f"Successfully connected to {env.name}",
        latency_ms=latency,
        details={
            "environment_type": env.environment_type,
            "timeout_used": timeout,
            "config_keys": list(env.config.keys()) if env.config else [],
        },
    )

    return ApiResponse.success(result)
