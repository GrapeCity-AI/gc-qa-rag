"""
FastAPI Application - Main entry point for the management API.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_knowledge_service.api.routers import (
    connectors_router,
    environments_router,
    knowledge_bases_router,
    system_router,
    tasks_router,
    versions_router,
)
from ai_knowledge_service.api.middleware import add_error_handlers
from ai_knowledge_service.api.websocket import TaskUpdateManager
from ai_knowledge_service.api.dependencies import get_container, get_event_bus


# API version prefix
API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    container = get_container()
    event_bus = get_event_bus()

    # Initialize WebSocket manager with event bus
    task_manager = TaskUpdateManager(event_bus)
    app.state.task_update_manager = task_manager
    task_manager.start()

    yield

    # Shutdown
    task_manager.stop()


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
