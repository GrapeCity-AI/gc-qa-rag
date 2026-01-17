"""
Task Updates WebSocket Manager - Real-time task status updates via WebSocket.

This manager subscribes to the event bus and broadcasts task updates to
connected WebSocket clients.
"""

import asyncio
import json
import threading
from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import WebSocket

from ai_knowledge_service.abstractions.infrastructure.event_bus import (
    DomainEvent,
    IEventBus,
)


class TaskUpdateManager:
    """
    Manages WebSocket connections for real-time task updates.

    Subscribes to task-related domain events and broadcasts updates
    to clients connected to the corresponding task's WebSocket.
    """

    def __init__(self, event_bus: IEventBus):
        self._event_bus = event_bus
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = threading.Lock()
        self._subscription_id: str | None = None
        self._running = False

    def start(self) -> None:
        """Start listening to task events."""
        if self._running:
            return

        self._running = True
        self._subscription_id = self._event_bus.subscribe_all(self._handle_event)

    def stop(self) -> None:
        """Stop listening to task events."""
        if not self._running:
            return

        self._running = False
        if self._subscription_id:
            self._event_bus.unsubscribe(self._subscription_id)
            self._subscription_id = None

        # Close all connections
        with self._lock:
            for task_id, connections in self._connections.items():
                for ws in connections:
                    try:
                        asyncio.create_task(ws.close())
                    except Exception:
                        pass
            self._connections.clear()

    def connect(self, task_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket connection for a task."""
        with self._lock:
            self._connections[task_id].add(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection."""
        with self._lock:
            if task_id in self._connections:
                self._connections[task_id].discard(websocket)
                if not self._connections[task_id]:
                    del self._connections[task_id]

    def _handle_event(self, event: DomainEvent) -> None:
        """Handle incoming domain events."""
        # Extract task_id from event payload if available
        task_id = None
        if hasattr(event, "task_id"):
            task_id = event.task_id
        elif hasattr(event, "payload") and isinstance(event.payload, dict):
            task_id = event.payload.get("task_id")

        if not task_id:
            return

        # Check if there are any connections for this task
        with self._lock:
            if task_id not in self._connections:
                return
            connections = list(self._connections[task_id])

        if not connections:
            return

        # Prepare update message
        message = self._create_update_message(event)

        # Broadcast to all connections
        for ws in connections:
            try:
                # Use asyncio to send in the main event loop
                asyncio.create_task(self._send_message(ws, message))
            except Exception:
                # Connection might be closed
                self.disconnect(task_id, ws)

    async def _send_message(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """Send a message to a WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    def _create_update_message(self, event: DomainEvent) -> dict[str, Any]:
        """Create an update message from a domain event."""
        message = {
            "event_type": event.event_type,
            "timestamp": datetime.now().isoformat(),
        }

        # Add task-specific fields based on event type
        if hasattr(event, "task_id"):
            message["task_id"] = event.task_id

        if hasattr(event, "status"):
            message["status"] = event.status

        if hasattr(event, "progress"):
            message["progress"] = event.progress

        if hasattr(event, "message"):
            message["message"] = event.message

        if hasattr(event, "current_step"):
            message["current_step"] = event.current_step

        if hasattr(event, "items_processed"):
            message["items_processed"] = event.items_processed

        if hasattr(event, "total_items"):
            message["total_items"] = event.total_items

        # Include any payload data
        if hasattr(event, "payload") and isinstance(event.payload, dict):
            for key, value in event.payload.items():
                if key not in message:
                    message[key] = value

        return message

    async def broadcast_to_task(self, task_id: str, message: dict[str, Any]) -> None:
        """Manually broadcast a message to all connections for a task."""
        with self._lock:
            if task_id not in self._connections:
                return
            connections = list(self._connections[task_id])

        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(task_id, ws)

    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        with self._lock:
            return sum(len(conns) for conns in self._connections.values())

    @property
    def task_count(self) -> int:
        """Get number of tasks with active connections."""
        with self._lock:
            return len(self._connections)
