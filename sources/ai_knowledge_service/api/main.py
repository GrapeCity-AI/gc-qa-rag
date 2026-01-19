"""
FastAPI Application - Main entry point for the management API.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_knowledge_service.abstractions.execution.executor import (
    IIndexingExecutor,
    IIngestionExecutor,
    IPublishingExecutor,
)
from ai_knowledge_service.abstractions.execution.queue import ITaskQueue
from ai_knowledge_service.abstractions.infrastructure.event_bus import IEventBus
from ai_knowledge_service.abstractions.infrastructure.version_manager import IVersionManager
from ai_knowledge_service.abstractions.models.tasks import TaskType
from ai_knowledge_service.api.config import get_settings
from ai_knowledge_service.api.di_setup import setup_container
from ai_knowledge_service.api.event_handlers import TaskCompletionHandler
from ai_knowledge_service.api.middleware import add_error_handlers
from ai_knowledge_service.api.routers import (
    connectors_router,
    environments_router,
    knowledge_bases_router,
    system_router,
    tasks_router,
    versions_router,
)
from ai_knowledge_service.api.websocket import TaskUpdateManager
from ai_knowledge_service.core.scheduler.thread_scheduler import ThreadScheduler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# API version prefix
API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # === Startup ===
    logger.info("Starting AI Knowledge Service...")

    # Load settings
    settings = get_settings()
    logger.info(f"Loaded settings: debug={settings.debug}, log_level={settings.log_level}")

    # Setup DI container
    container = setup_container(settings)
    app.state.container = container
    logger.info("DI container initialized")

    # Get core services from container
    event_bus = container.resolve(IEventBus)
    task_queue = container.resolve(ITaskQueue)
    version_manager = container.resolve(IVersionManager)

    # Create and start scheduler
    scheduler = ThreadScheduler(
        task_queue=task_queue,
        event_bus=event_bus,
        poll_interval=settings.scheduler.poll_interval,
    )

    # Register executors
    scheduler.register_executor(
        TaskType.INGESTION,
        container.resolve(IIngestionExecutor),
    )
    scheduler.register_executor(
        TaskType.INDEXING,
        container.resolve(IIndexingExecutor),
    )
    scheduler.register_executor(
        TaskType.PUBLISHING,
        container.resolve(IPublishingExecutor),
    )

    # Start scheduler
    scheduler.start(worker_count=settings.scheduler.max_workers)
    app.state.scheduler = scheduler
    logger.info(
        f"Scheduler started with {settings.scheduler.max_workers} workers"
    )

    # Start event handler for version status updates
    completion_handler = TaskCompletionHandler(event_bus, version_manager)
    completion_handler.start()
    app.state.completion_handler = completion_handler
    logger.info("TaskCompletionHandler started")

    # Initialize WebSocket manager with event bus
    task_update_manager = TaskUpdateManager(event_bus)
    task_update_manager.start()
    app.state.task_update_manager = task_update_manager
    logger.info("TaskUpdateManager started")

    logger.info("AI Knowledge Service started successfully")

    yield

    # === Shutdown ===
    logger.info("Shutting down AI Knowledge Service...")

    # Stop in reverse order
    task_update_manager.stop()
    logger.info("TaskUpdateManager stopped")

    completion_handler.stop()
    logger.info("TaskCompletionHandler stopped")

    scheduler.stop(graceful=True, timeout=30.0)
    logger.info("Scheduler stopped")

    logger.info("AI Knowledge Service shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Knowledge Service API",
        description="Management API for AI Knowledge Service ETL system",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=f"{API_V1_PREFIX}/docs",
        redoc_url=f"{API_V1_PREFIX}/redoc",
        openapi_url=f"{API_V1_PREFIX}/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add error handlers
    add_error_handlers(app)

    # Include routers
    app.include_router(
        system_router,
        prefix=API_V1_PREFIX,
        tags=["System"],
    )
    app.include_router(
        knowledge_bases_router,
        prefix=f"{API_V1_PREFIX}/knowledge-bases",
        tags=["Knowledge Bases"],
    )
    app.include_router(
        versions_router,
        prefix=API_V1_PREFIX,
        tags=["Versions"],
    )
    app.include_router(
        tasks_router,
        prefix=f"{API_V1_PREFIX}/tasks",
        tags=["Tasks"],
    )
    app.include_router(
        connectors_router,
        prefix=f"{API_V1_PREFIX}/connectors",
        tags=["Connectors"],
    )
    app.include_router(
        environments_router,
        prefix=f"{API_V1_PREFIX}/environments",
        tags=["Environments"],
    )

    return app


# Application instance for uvicorn
app = create_app()
