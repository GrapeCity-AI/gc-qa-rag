"""
Error Handler Middleware - Global error handling for the API.

Provides consistent error responses and logging for all exceptions.
"""

import logging
import traceback
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ai_knowledge_service.api.schemas.common import ApiError, ApiResponse


logger = logging.getLogger(__name__)


def add_error_handlers(app: FastAPI) -> None:
    """Add global error handlers to the FastAPI application."""

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append(
                ApiError(
                    code="validation_error",
                    message=error["msg"],
                    field=field,
                    details={"type": error["type"]},
                )
            )

        response = ApiResponse[None](data=None, errors=errors)
        return JSONResponse(
            status_code=422,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request,
        exc: ValueError,
    ) -> JSONResponse:
        """Handle value errors."""
        error = ApiError(
            code="invalid_value",
            message=str(exc),
        )
        response = ApiResponse[None](data=None, errors=[error])
        return JSONResponse(
            status_code=400,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(KeyError)
    async def key_error_handler(
        request: Request,
        exc: KeyError,
    ) -> JSONResponse:
        """Handle key errors (usually missing resources)."""
        error = ApiError(
            code="not_found",
            message=f"Resource not found: {str(exc)}",
        )
        response = ApiResponse[None](data=None, errors=[error])
        return JSONResponse(
            status_code=404,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(
        request: Request,
        exc: PermissionError,
    ) -> JSONResponse:
        """Handle permission errors."""
        error = ApiError(
            code="forbidden",
            message=str(exc) or "Permission denied",
        )
        response = ApiResponse[None](data=None, errors=[error])
        return JSONResponse(
            status_code=403,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle all other exceptions."""
        # Log the full error
        logger.exception(f"Unhandled exception: {exc}")

        # In development, include the traceback
        # In production, you'd want to hide this
        details = {
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }

        error = ApiError(
            code="internal_error",
            message="An internal error occurred",
            details=details,
        )
        response = ApiResponse[None](data=None, errors=[error])
        return JSONResponse(
            status_code=500,
            content=response.model_dump(mode="json"),
        )


class RequestLoggingMiddleware:
    """Middleware for logging requests and responses."""

    def __init__(self, app: Callable):
        self.app = app
        self.logger = logging.getLogger(__name__)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Log request
        method = scope.get("method", "")
        path = scope.get("path", "")
        self.logger.info(f"Request: {method} {path}")

        # Track response status
        status_code = None

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status")
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            self.logger.info(f"Response: {method} {path} -> {status_code}")
