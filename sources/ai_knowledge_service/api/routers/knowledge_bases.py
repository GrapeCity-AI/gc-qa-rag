"""
Knowledge Bases Router - CRUD operations for knowledge bases.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from ai_knowledge_service.api.schemas.common import (
    ApiResponse,
    ApiError,
    PaginatedResponse,
    PaginationMeta,
)
from ai_knowledge_service.api.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseSummary,
    KnowledgeBaseUpdate,
)
from ai_knowledge_service.api.dependencies import KbStoreDep
from ai_knowledge_service.abstractions.models.knowledge_base import KnowledgeBase


router = APIRouter()


@router.get("", response_model=PaginatedResponse[KnowledgeBaseSummary])
async def list_knowledge_bases(
    kb_store: KbStoreDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by name"),
) -> PaginatedResponse[KnowledgeBaseSummary]:
    """
    List all knowledge bases with pagination.
    """
    all_kbs = kb_store.list_knowledge_bases()

    # Apply search filter
    if search:
        search_lower = search.lower()
        all_kbs = [kb for kb in all_kbs if search_lower in kb.name.lower()]

    # Sort by created_at descending
    all_kbs.sort(key=lambda x: x.created_at, reverse=True)

    # Paginate
    total_items = len(all_kbs)
    total_pages = (total_items + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = all_kbs[start_idx:end_idx]

    # Convert to summaries with version counts
    summaries = []
    for kb in page_items:
        versions = kb_store.list_versions(kb.id)
        latest = max(versions, key=lambda v: v.created_at, default=None) if versions else None
        summaries.append(
            KnowledgeBaseSummary(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                version_count=len(versions),
                latest_version=latest.version_tag if latest else None,
                created_at=kb.created_at,
                updated_at=kb.updated_at,
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


@router.post("", response_model=ApiResponse[KnowledgeBaseResponse], status_code=201)
async def create_knowledge_base(
    kb_store: KbStoreDep,
    data: KnowledgeBaseCreate,
) -> ApiResponse[KnowledgeBaseResponse]:
    """
    Create a new knowledge base.
    """
    kb = KnowledgeBase(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        metadata=data.metadata,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb_store.save_knowledge_base(kb)

    return ApiResponse.success(
        KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            metadata=kb.metadata,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            version_count=0,
            latest_version=None,
        )
    )


@router.get("/{kb_id}", response_model=ApiResponse[KnowledgeBaseResponse])
async def get_knowledge_base(
    kb_id: str,
    kb_store: KbStoreDep,
) -> ApiResponse[KnowledgeBaseResponse]:
    """
    Get a knowledge base by ID.
    """
    kb = kb_store.get_knowledge_base(kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"Knowledge base not found: {kb_id}")

    versions = kb_store.list_versions(kb_id)
    latest = max(versions, key=lambda v: v.created_at, default=None) if versions else None

    return ApiResponse.success(
        KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            metadata=kb.metadata,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            version_count=len(versions),
            latest_version=latest.version_tag if latest else None,
        )
    )


@router.put("/{kb_id}", response_model=ApiResponse[KnowledgeBaseResponse])
async def update_knowledge_base(
    kb_id: str,
    kb_store: KbStoreDep,
    data: KnowledgeBaseUpdate,
) -> ApiResponse[KnowledgeBaseResponse]:
    """
    Update a knowledge base.
    """
    kb = kb_store.get_knowledge_base(kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"Knowledge base not found: {kb_id}")

    # Update fields
    if data.name is not None:
        kb.name = data.name
    if data.description is not None:
        kb.description = data.description
    if data.metadata is not None:
        kb.metadata = data.metadata
    kb.updated_at = datetime.now()

    kb_store.save_knowledge_base(kb)

    versions = kb_store.list_versions(kb_id)
    latest = max(versions, key=lambda v: v.created_at, default=None) if versions else None

    return ApiResponse.success(
        KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            metadata=kb.metadata,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            version_count=len(versions),
            latest_version=latest.version_tag if latest else None,
        )
    )


@router.delete("/{kb_id}", response_model=ApiResponse[None])
async def delete_knowledge_base(
    kb_id: str,
    kb_store: KbStoreDep,
) -> ApiResponse[None]:
    """
    Delete a knowledge base and all its versions.
    """
    if not kb_store.delete_knowledge_base(kb_id):
        raise HTTPException(status_code=404, detail=f"Knowledge base not found: {kb_id}")

    return ApiResponse.success(None, meta={"deleted": kb_id})
