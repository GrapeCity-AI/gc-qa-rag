"""
Versions Router - Version management endpoints.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from ai_knowledge_service.api.schemas.common import (
    ApiResponse,
    PaginatedResponse,
    PaginationMeta,
)
from ai_knowledge_service.api.schemas.version import (
    FileVersionResponse,
    VersionBuildRequest,
    VersionCreate,
    VersionPublishRequest,
    VersionResponse,
    VersionSummary,
)
from ai_knowledge_service.api.schemas.task import TaskResponse
from ai_knowledge_service.api.dependencies import KbStoreDep, TaskQueueDep
from ai_knowledge_service.abstractions.models.knowledge_base import (
    KnowledgeBaseVersion,
    VersionStatus,
    IndexStatus,
)
from ai_knowledge_service.abstractions.models.tasks import (
    IndexingTask,
    PublishingTask,
    BuildType,
    PublishStrategy,
    TaskStatus,
    StepConfig,
)


router = APIRouter()


@router.get("/knowledge-bases/{kb_id}/versions", response_model=PaginatedResponse[VersionSummary])
async def list_versions(
    kb_id: str,
    kb_store: KbStoreDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[VersionSummary]:
    """
    List all versions for a knowledge base.
    """
    kb = kb_store.get_knowledge_base(kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"Knowledge base not found: {kb_id}")

    versions = kb_store.list_versions(kb_id)
    versions.sort(key=lambda x: x.created_at, reverse=True)

    # Paginate
    total_items = len(versions)
    total_pages = (total_items + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = versions[start_idx:end_idx]

    summaries = []
    for v in page_items:
        file_versions = kb_store.get_file_versions(v.id)
        summaries.append(
            VersionSummary(
                id=v.id,
                version_tag=v.version_tag,
                status=v.status.value,
                file_count=len(file_versions),
                created_at=v.created_at,
            )
        )

    return PaginatedResponse(
        data=summaries,
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


@router.post("/knowledge-bases/{kb_id}/versions", response_model=ApiResponse[VersionResponse], status_code=201)
async def create_version(
    kb_id: str,
    kb_store: KbStoreDep,
    data: VersionCreate,
) -> ApiResponse[VersionResponse]:
    """
    Create a new version for a knowledge base.
    """
    kb = kb_store.get_knowledge_base(kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"Knowledge base not found: {kb_id}")

    # Validate parent version if provided
    if data.parent_version_id:
        parent = kb_store.get_version(data.parent_version_id)
        if parent is None:
            raise HTTPException(status_code=400, detail=f"Parent version not found: {data.parent_version_id}")
        if parent.knowledge_base_id != kb_id:
            raise HTTPException(status_code=400, detail="Parent version belongs to a different knowledge base")

    version = KnowledgeBaseVersion(
        id=str(uuid.uuid4()),
        knowledge_base_id=kb_id,
        version_tag=data.version_tag,
        status=VersionStatus.DRAFT,
        parent_version_id=data.parent_version_id,
        created_at=datetime.now(),
        metadata=data.metadata,
    )
    kb_store.save_version(version)

    return ApiResponse.success(
        VersionResponse(
            id=version.id,
            knowledge_base_id=version.knowledge_base_id,
            version_tag=version.version_tag,
            status=version.status.value,
            parent_version_id=version.parent_version_id,
            created_at=version.created_at,
            published_at=version.published_at,
            metadata=version.metadata,
            file_count=0,
            indexed_count=0,
            pending_count=0,
            failed_count=0,
        )
    )


@router.get("/versions/{version_id}", response_model=ApiResponse[VersionResponse])
async def get_version(
    version_id: str,
    kb_store: KbStoreDep,
) -> ApiResponse[VersionResponse]:
    """
    Get a version by ID.
    """
    version = kb_store.get_version(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail=f"Version not found: {version_id}")

    file_versions = kb_store.get_file_versions(version_id)
    indexed = sum(1 for fv in file_versions if fv.index_status == IndexStatus.INDEXED)
    pending = sum(1 for fv in file_versions if fv.index_status == IndexStatus.PENDING)
    failed = sum(1 for fv in file_versions if fv.index_status == IndexStatus.FAILED)

    return ApiResponse.success(
        VersionResponse(
            id=version.id,
            knowledge_base_id=version.knowledge_base_id,
            version_tag=version.version_tag,
            status=version.status.value,
            parent_version_id=version.parent_version_id,
            created_at=version.created_at,
            published_at=version.published_at,
            metadata=version.metadata,
            file_count=len(file_versions),
            indexed_count=indexed,
            pending_count=pending,
            failed_count=failed,
        )
    )


@router.post("/versions/{version_id}/build", response_model=ApiResponse[TaskResponse])
async def trigger_build(
    version_id: str,
    kb_store: KbStoreDep,
    task_queue: TaskQueueDep,
    data: VersionBuildRequest,
) -> ApiResponse[TaskResponse]:
    """
    Trigger a build for a version.
    """
    version = kb_store.get_version(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail=f"Version not found: {version_id}")

    if version.status not in (VersionStatus.DRAFT, VersionStatus.READY):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot build version in status: {version.status.value}"
        )

    # Update version status
    version.status = VersionStatus.BUILDING
    kb_store.save_version(version)

    # Get KB for response
    kb = kb_store.get_knowledge_base(version.knowledge_base_id)

    # Create indexing task
    build_type = BuildType.FULL if data.build_type == "full" else BuildType.INCREMENTAL
    pipeline_config = [StepConfig(**step) for step in data.pipeline_config]

    task = IndexingTask(
        id=str(uuid.uuid4()),
        knowledge_base_id=version.knowledge_base_id,
        knowledge_base_version_id=version_id,
        build_type=build_type,
        pipeline_config=pipeline_config,
        created_at=datetime.now(),
    )

    task_queue.enqueue(task)

    return ApiResponse.success(
        TaskResponse(
            id=task.id,
            task_type=task.task_type.value,
            knowledge_base_id=task.knowledge_base_id,
            knowledge_base_version_id=task.knowledge_base_version_id,
            status=TaskStatus.PENDING.value,
            priority=task.priority,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            metadata=task.metadata,
            knowledge_base_name=kb.name if kb else None,
            version_tag=version.version_tag,
        )
    )


@router.post("/versions/{version_id}/publish", response_model=ApiResponse[TaskResponse])
async def trigger_publish(
    version_id: str,
    kb_store: KbStoreDep,
    task_queue: TaskQueueDep,
    data: VersionPublishRequest,
) -> ApiResponse[TaskResponse]:
    """
    Trigger publishing for a version.
    """
    version = kb_store.get_version(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail=f"Version not found: {version_id}")

    if version.status != VersionStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish version in status: {version.status.value}. Must be 'ready'."
        )

    # Get KB for response
    kb = kb_store.get_knowledge_base(version.knowledge_base_id)

    # Create publishing task
    strategy = PublishStrategy.BLUE_GREEN if data.publish_strategy == "blue_green" else PublishStrategy.REPLACE

    task = PublishingTask(
        id=str(uuid.uuid4()),
        knowledge_base_id=version.knowledge_base_id,
        knowledge_base_version_id=version_id,
        target_environment_id=data.target_environment_id,
        alias_name=data.alias_name,
        publish_strategy=strategy,
        include_raw_files=data.include_raw_files,
        created_at=datetime.now(),
    )

    task_queue.enqueue(task)

    return ApiResponse.success(
        TaskResponse(
            id=task.id,
            task_type=task.task_type.value,
            knowledge_base_id=task.knowledge_base_id,
            knowledge_base_version_id=task.knowledge_base_version_id,
            status=TaskStatus.PENDING.value,
            priority=task.priority,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            metadata=task.metadata,
            knowledge_base_name=kb.name if kb else None,
            version_tag=version.version_tag,
        )
    )


@router.get("/versions/{version_id}/files", response_model=PaginatedResponse[FileVersionResponse])
async def list_version_files(
    version_id: str,
    kb_store: KbStoreDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    status: str | None = Query(None, description="Filter by index status"),
) -> PaginatedResponse[FileVersionResponse]:
    """
    List files in a version.
    """
    version = kb_store.get_version(version_id)
    if version is None:
        raise HTTPException(status_code=404, detail=f"Version not found: {version_id}")

    file_versions = kb_store.get_file_versions(version_id)

    # Apply status filter
    if status:
        try:
            status_enum = IndexStatus(status)
            file_versions = [fv for fv in file_versions if fv.index_status == status_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    # Paginate
    total_items = len(file_versions)
    total_pages = (total_items + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = file_versions[start_idx:end_idx]

    responses = [
        FileVersionResponse(
            id=fv.id,
            raw_file_id=fv.raw_file_id,
            knowledge_base_version_id=fv.knowledge_base_version_id,
            content_hash=fv.content_hash,
            index_status=fv.index_status.value,
            indexed_at=fv.indexed_at,
            created_at=fv.created_at,
            source_type=fv.metadata.get("source_type"),
            source_uri=fv.metadata.get("source_uri"),
            original_name=fv.metadata.get("original_name"),
            mime_type=fv.metadata.get("mime_type"),
            size_bytes=fv.metadata.get("size_bytes"),
        )
        for fv in page_items
    ]

    return PaginatedResponse(
        data=responses,
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )
