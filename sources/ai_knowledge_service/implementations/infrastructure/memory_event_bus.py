"""
Memory Event Bus - In-memory event bus implementation.

This implementation provides:
- Synchronous event publishing
- Multiple handlers per event type
- Wildcard subscription (all events)
- Thread-safe operations
"""

import threading
import uuid
from typing import Callable, Dict, List, Set, Type, TypeVar

from ai_knowledge_service.abstractions.infrastructure.event_bus import (
    DomainEvent,
    EventHandler,
    IEventBus,
)


TEvent = TypeVar("TEvent", bound=DomainEvent)


class MemoryEventBus(IEventBus):
    """
    In-memory event bus implementation.

    Events are published synchronously to all registered handlers.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], Dict[str, EventHandler]] = {}
        self._global_handlers: Dict[str, EventHandler] = {}
        self._lock = threading.RLock()

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        handlers_to_call: List[EventHandler] = []

        with self._lock:
            event_type = type(event)
            if event_type in self._handlers:
                handlers_to_call.extend(self._handlers[event_type].values())

            handlers_to_call.extend(self._global_handlers.values())

        for handler in handlers_to_call:
            try:
                handler(event)
            except Exception:
                pass

    def subscribe(
        self,
        event_type: Type[TEvent],
        handler: Callable[[TEvent], None],
    ) -> str:
        """Subscribe to an event type."""
        subscription_id = str(uuid.uuid4())

        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = {}
            self._handlers[event_type][subscription_id] = handler

        return subscription_id

    def subscribe_all(
        self,
        handler: EventHandler,
    ) -> str:
        """Subscribe to all events."""
        subscription_id = str(uuid.uuid4())

        with self._lock:
            self._global_handlers[subscription_id] = handler

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        with self._lock:
            if subscription_id in self._global_handlers:
                del self._global_handlers[subscription_id]
                return True

            for handlers in self._handlers.values():
                if subscription_id in handlers:
                    del handlers[subscription_id]
                    return True

        return False

    def get_handlers(
        self,
        event_type: Type[DomainEvent],
    ) -> List[EventHandler]:
        """Get all handlers for an event type."""
        with self._lock:
            handlers: List[EventHandler] = []
            if event_type in self._handlers:
                handlers.extend(self._handlers[event_type].values())
            handlers.extend(self._global_handlers.values())
            return handlers

    def clear(self) -> None:
        """Clear all subscriptions."""
        with self._lock:
            self._handlers.clear()
            self._global_handlers.clear()
