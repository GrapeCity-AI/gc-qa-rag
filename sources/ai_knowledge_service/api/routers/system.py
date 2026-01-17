"""
System Router - Health check and system status endpoints.
"""

from datetime import datetime

from fastapi import APIRouter, Depends

from ai_knowledge_service.api.schemas.common import (
    ApiResponse,
    CountStats,
    HealthStatus,
    SystemConfigResponse,
)
from ai_knowledge_service.api.dependencies import (
    TaskQueueDep,
    KbStoreDep,
)
from ai_knowledge_service.abstractions.models.tasks import TaskStatus


router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthStatus])
async def health_check() -> ApiResponse[HealthStatus]:
    """
    Health check endpoint.

    Returns the current service status and version information.
    """
    health = HealthStatus(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(),
        components={
            "api": "healthy",
            "task_queue": "healthy",
            "event_bus": "healthy",
        },
    )
    return ApiResponse.success(health)


@router.get("/stats", response_model=ApiResponse[CountStats])
async def get_stats(
    kb_store: KbStoreDep,
    task_queue: TaskQueueDep,
) -> ApiResponse[CountStats]:
    """
    Get system statistics for dashboard.

    Returns counts of knowledge bases, versions, and task statuses.
    """
    # Get knowledge base counts
    knowledge_bases = kb_store.list_knowledge_bases()
    kb_count = len(knowledge_bases)

    # Count versions
    version_count = sum(
        len(kb_store.list_versions(kb.id)) for kb in knowledge_bases
    )

    # Get task counts
    all_tasks = task_queue.list_tasks()
    pending = sum(1 for t in all_tasks if task_queue.get_status(t.id) == TaskStatus.PENDING)
    running = sum(1 for t in all_tasks if task_queue.get_status(t.id) == TaskStatus.RUNNING)
    completed = sum(1 for t in all_tasks if task_queue.get_status(t.id) == TaskStatus.COMPLETED)
    failed = sum(1 for t in all_tasks if task_queue.get_status(t.id) == TaskStatus.FAILED)

    stats = CountStats(
        knowledge_bases=kb_count,
        versions=version_count,
        pending_tasks=pending,
        running_tasks=running,
        completed_tasks=completed,
        failed_tasks=failed,
    )
    return ApiResponse.success(stats)


@router.get("/config", response_model=ApiResponse[SystemConfigResponse])
async def get_config() -> ApiResponse[SystemConfigResponse]:
    """
    Get system configuration.

    Returns sanitized configuration values (no secrets/credentials).
    """
    # In a real implementation, this would read from actual config
    # For now, return default/placeholder values
    config = SystemConfigResponse(
        llm_provider="dashscope",
        llm_model="qwen-max",
        storage_type="local",
        vector_db_type="qdrant",
        max_concurrent_tasks=4,
        default_chunk_size=512,
        default_chunk_overlap=50,
        features={
            "incremental_indexing": True,
            "blue_green_deployment": True,
            "sitemap_connector": True,
            "filesystem_connector": True,
            "forum_api_connector": False,
        },
    )
    return ApiResponse.success(config)
