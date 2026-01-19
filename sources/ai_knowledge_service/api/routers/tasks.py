"""
Tasks Router - Task management endpoints.
"""

import uuid
from datetime import datetime
from copy import deepcopy

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, Request

from ai_knowledge_service.api.schemas.common import (
    ApiResponse,
    PaginatedResponse,
    PaginationMeta,
)
from ai_knowledge_service.api.schemas.task import (
    ProcessingErrorResponse,
    StepStatsResponse,
    TaskCancelRequest,
    TaskResponse,
    TaskResultResponse,
    TaskRetryRequest,
    TaskSummary,
)
from ai_knowledge_service.api.dependencies import VersionManagerDep, TaskQueueDep
from ai_knowledge_service.abstractions.models.tasks import TaskStatus, TaskType


router = APIRouter()


@router.get("", response_model=PaginatedResponse[TaskSummary])
async def list_tasks(
    task_queue: TaskQueueDep,
    version_manager: VersionManagerDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status"),
    task_type: str | None = Query(None, description="Filter by task type"),
) -> PaginatedResponse[TaskSummary]:
    """
    List all tasks with pagination and filters.
    """
    all_tasks = task_queue.list_tasks()

    # Apply filters
    if status:
        try:
            status_enum = TaskStatus(status)
            all_tasks = [t for t in all_tasks if task_queue.get_task_status(t.id) == status_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if task_type:
        try:
            type_enum = TaskType(task_type)
            all_tasks = [t for t in all_tasks if t.task_type == type_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid task type: {task_type}")

    # Sort by created_at descending
    all_tasks.sort(key=lambda x: x.created_at, reverse=True)

    # Paginate
    total_items = len(all_tasks)
    total_pages = (total_items + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = all_tasks[start_idx:end_idx]

    summaries = []
    for task in page_items:
        kb = version_manager.get_knowledge_base(task.knowledge_base_id)
        version = version_manager.get_version(task.knowledge_base_version_id)
        task_status = task_queue.get_task_status(task.id)

        summaries.append(
            TaskSummary(
                id=task.id,
                task_type=task.task_type.value,
                status=task_status.value if task_status else TaskStatus.PENDING.value,
                knowledge_base_name=kb.name if kb else None,
                version_tag=version.version_tag if version else None,
                created_at=task.created_at,
                completed_at=task.completed_at,
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


@router.get("/{task_id}", response_model=ApiResponse[TaskResponse])
async def get_task(
    task_id: str,
    task_queue: TaskQueueDep,
    version_manager: VersionManagerDep,
) -> ApiResponse[TaskResponse]:
    """
    Get a task by ID.
    """
    task = task_queue.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    kb = version_manager.get_knowledge_base(task.knowledge_base_id)
    version = version_manager.get_version(task.knowledge_base_version_id)
    task_status = task_queue.get_task_status(task_id)

    duration = None
    if task.started_at and task.completed_at:
        duration = (task.completed_at - task.started_at).total_seconds()

    return ApiResponse.success(
        TaskResponse(
            id=task.id,
            task_type=task.task_type.value,
            knowledge_base_id=task.knowledge_base_id,
            knowledge_base_version_id=task.knowledge_base_version_id,
            status=task_status.value if task_status else TaskStatus.PENDING.value,
            priority=task.priority,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            metadata=task.metadata,
            knowledge_base_name=kb.name if kb else None,
            version_tag=version.version_tag if version else None,
            duration_seconds=duration,
        )
    )


@router.get("/{task_id}/result", response_model=ApiResponse[TaskResultResponse])
async def get_task_result(
    task_id: str,
    task_queue: TaskQueueDep,
) -> ApiResponse[TaskResultResponse]:
    """
    Get the result of a completed task.
    """
    task = task_queue.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    result = task_queue.get_result(task_id)
    if result is None:
        task_status = task_queue.get_task_status(task_id)
        if task_status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            raise HTTPException(status_code=400, detail="Task has not completed yet")
        raise HTTPException(status_code=404, detail="Task result not found")

    # Convert errors
    errors = [
        ProcessingErrorResponse(
            item_id=e.item_id,
            item_name=e.item_name,
            step=e.step,
            error_type=e.error_type,
            error_message=e.error_message,
            stacktrace=e.stacktrace,
            timestamp=e.timestamp,
            recoverable=e.recoverable,
        )
        for e in result.errors
    ]

    # Convert step stats if present
    step_stats = {}
    if hasattr(result, "step_stats") and result.step_stats:
        for step_type, stats in result.step_stats.items():
            step_stats[step_type] = StepStatsResponse(
                step_type=stats.step_type,
                input_count=stats.input_count,
                output_count=stats.output_count,
                duration_seconds=stats.duration_seconds,
                errors_count=stats.errors_count,
                success_rate=stats.success_rate,
            )

    response = TaskResultResponse(
        task_id=result.task_id,
        task_type=result.task_type.value,
        status=result.status.value,
        total_items=result.total_items,
        succeeded_count=result.succeeded_count,
        failed_count=result.failed_count,
        skipped_count=result.skipped_count,
        errors=errors,
        started_at=result.started_at,
        completed_at=result.completed_at,
        duration_seconds=result.duration_seconds,
        success_rate=result.success_rate,
        step_stats=step_stats,
    )

    # Add type-specific fields
    if hasattr(result, "index_records_count"):
        response.index_records_count = result.index_records_count
    if hasattr(result, "new_files_count"):
        response.new_files_count = result.new_files_count
    if hasattr(result, "updated_files_count"):
        response.updated_files_count = result.updated_files_count
    if hasattr(result, "unchanged_files_count"):
        response.unchanged_files_count = result.unchanged_files_count
    if hasattr(result, "target_collection"):
        response.target_collection = result.target_collection
    if hasattr(result, "alias_applied"):
        response.alias_applied = result.alias_applied

    return ApiResponse.success(response)


@router.post("/{task_id}/cancel", response_model=ApiResponse[TaskResponse])
async def cancel_task(
    task_id: str,
    task_queue: TaskQueueDep,
    version_manager: VersionManagerDep,
    data: TaskCancelRequest | None = None,
) -> ApiResponse[TaskResponse]:
    """
    Cancel a pending or running task.
    """
    task = task_queue.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    task_status = task_queue.get_task_status(task_id)
    if task_status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task in status: {task_status.value if task_status else 'unknown'}"
        )

    success = task_queue.cancel(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel task")

    kb = version_manager.get_knowledge_base(task.knowledge_base_id)
    version = version_manager.get_version(task.knowledge_base_version_id)

    return ApiResponse.success(
        TaskResponse(
            id=task.id,
            task_type=task.task_type.value,
            knowledge_base_id=task.knowledge_base_id,
            knowledge_base_version_id=task.knowledge_base_version_id,
            status=TaskStatus.CANCELLED.value,
            priority=task.priority,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            metadata=task.metadata,
            knowledge_base_name=kb.name if kb else None,
            version_tag=version.version_tag if version else None,
        )
    )


@router.post("/{task_id}/retry", response_model=ApiResponse[TaskResponse])
async def retry_task(
    task_id: str,
    task_queue: TaskQueueDep,
    version_manager: VersionManagerDep,
    data: TaskRetryRequest | None = None,
) -> ApiResponse[TaskResponse]:
    """
    Retry a failed or cancelled task. Creates a new task with the same configuration.
    """
    original_task = task_queue.get_task(task_id)
    if original_task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    task_status = task_queue.get_task_status(task_id)
    if task_status not in (TaskStatus.FAILED, TaskStatus.CANCELLED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry task in status: {task_status.value if task_status else 'unknown'}. Only FAILED or CANCELLED tasks can be retried."
        )

    # Check if max retries exceeded (unless reset_retry_count is True)
    reset_retry = data.reset_retry_count if data else True
    if not reset_retry and original_task.retry_count >= original_task.max_retries:
        raise HTTPException(
            status_code=400,
            detail=f"Task has exceeded maximum retries ({original_task.max_retries})"
        )

    # Create a new task with same configuration
    new_task = deepcopy(original_task)
    new_task.id = str(uuid.uuid4())
    new_task.created_at = datetime.now()
    new_task.started_at = None
    new_task.completed_at = None

    if reset_retry:
        new_task.retry_count = 0
    else:
        new_task.retry_count = original_task.retry_count + 1

    if data and data.priority is not None:
        new_task.priority = data.priority

    # Add reference to original task in metadata
    new_task.metadata = new_task.metadata.copy() if new_task.metadata else {}
    new_task.metadata["retried_from"] = task_id

    task_queue.enqueue(new_task)

    kb = version_manager.get_knowledge_base(new_task.knowledge_base_id)
    version = version_manager.get_version(new_task.knowledge_base_version_id)

    return ApiResponse.success(
        TaskResponse(
            id=new_task.id,
            task_type=new_task.task_type.value,
            knowledge_base_id=new_task.knowledge_base_id,
            knowledge_base_version_id=new_task.knowledge_base_version_id,
            status=TaskStatus.PENDING.value,
            priority=new_task.priority,
            retry_count=new_task.retry_count,
            max_retries=new_task.max_retries,
            created_at=new_task.created_at,
            started_at=new_task.started_at,
            completed_at=new_task.completed_at,
            metadata=new_task.metadata,
            knowledge_base_name=kb.name if kb else None,
            version_tag=version.version_tag if version else None,
        )
    )


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(
    websocket: WebSocket,
    task_id: str,
    request: Request,
) -> None:
    """
    WebSocket endpoint for real-time task updates.
    """
    await websocket.accept()

    # Get the task update manager from app state
    if not hasattr(request.app.state, "task_update_manager"):
        await websocket.close(code=1011, reason="Task update manager not initialized")
        return

    manager = request.app.state.task_update_manager

    try:
        # Register this connection for task updates
        manager.connect(task_id, websocket)

        # Keep connection alive
        while True:
            try:
                # Wait for messages (mainly for ping/pong)
                data = await websocket.receive_text()
                # Echo back for ping
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
    finally:
        manager.disconnect(task_id, websocket)
