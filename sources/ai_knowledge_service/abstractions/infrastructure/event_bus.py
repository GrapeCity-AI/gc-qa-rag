"""
Event Bus interface - Defines event-driven communication.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Protocol, Type, TypeVar, runtime_checkable
import uuid


@dataclass
class DomainEvent:
    """
    Domain Event - Base class for all domain events.

    Events are used for loose coupling between components.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_type:
            self.event_type = self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }


@dataclass
class FileIngestedEvent(DomainEvent):
    """
    Event fired when a file is ingested.
    """

    event_type: str = field(default="FileIngestedEvent", init=False)

    # Payload fields
    file_id: str = ""
    knowledge_base_id: str = ""
    source_type: str = ""
    source_uri: str = ""
    content_hash: str = ""
    is_new: bool = True  # True if new, False if update

    def __post_init__(self):
        super().__post_init__()
        self.payload = {
            "file_id": self.file_id,
            "knowledge_base_id": self.knowledge_base_id,
            "source_type": self.source_type,
            "source_uri": self.source_uri,
            "content_hash": self.content_hash,
            "is_new": self.is_new,
        }


@dataclass
class BuildTaskCompletedEvent(DomainEvent):
    """
    Event fired when a build task completes.
    """

    event_type: str = field(default="BuildTaskCompletedEvent", init=False)

    # Payload fields
    task_id: str = ""
    knowledge_base_id: str = ""
    knowledge_base_version_id: str = ""
    success: bool = True
    records_indexed: int = 0
    errors_count: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.payload = {
            "task_id": self.task_id,
            "knowledge_base_id": self.knowledge_base_id,
            "knowledge_base_version_id": self.knowledge_base_version_id,
            "success": self.success,
            "records_indexed": self.records_indexed,
            "errors_count": self.errors_count,
        }


@dataclass
class VersionPublishedEvent(DomainEvent):
    """
    Event fired when a version is published.
    """

    event_type: str = field(default="VersionPublishedEvent", init=False)

    # Payload fields
    knowledge_base_id: str = ""
    knowledge_base_version_id: str = ""
    target_environment_id: str = ""
    target_collection: str = ""
    alias_applied: str = ""

    def __post_init__(self):
        super().__post_init__()
        self.payload = {
            "knowledge_base_id": self.knowledge_base_id,
            "knowledge_base_version_id": self.knowledge_base_version_id,
            "target_environment_id": self.target_environment_id,
            "target_collection": self.target_collection,
            "alias_applied": self.alias_applied,
        }


# Type variable for event types
TEvent = TypeVar("TEvent", bound=DomainEvent)

# Event handler type
EventHandler = Callable[[DomainEvent], None]


@runtime_checkable
class IEventBus(Protocol):
    """
    Event Bus - Interface for publishing and subscribing to events.

    Provides loose coupling between components through events.
    """

    def publish(self, event: DomainEvent) -> None:
        """
        Publish an event.

        All registered handlers for this event type will be called.

        Args:
            event: The event to publish.
        """
        ...

    def subscribe(
        self,
        event_type: Type[TEvent],
        handler: Callable[[TEvent], None],
    ) -> str:
        """
        Subscribe to an event type.

        Args:
            event_type: The type of event to subscribe to.
            handler: The handler function to call.

        Returns:
            str: Subscription ID (for unsubscribing).
        """
        ...

    def subscribe_all(
        self,
        handler: EventHandler,
    ) -> str:
        """
        Subscribe to all events.

        Args:
            handler: The handler function to call.

        Returns:
            str: Subscription ID.
        """
        ...

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscription_id: The subscription ID returned from subscribe.

        Returns:
            bool: True if the subscription was removed.
        """
        ...

    def get_handlers(
        self,
        event_type: Type[DomainEvent],
    ) -> List[EventHandler]:
        """
        Get all handlers for an event type.

        Args:
            event_type: The event type.

        Returns:
            List[EventHandler]: Registered handlers.
        """
        ...

    def clear(self) -> None:
        """
        Clear all subscriptions.
        """
        ...
