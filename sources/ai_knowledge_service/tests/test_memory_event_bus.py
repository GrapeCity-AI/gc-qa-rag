"""
Tests for MemoryEventBus - In-memory event bus implementation.
"""

import pytest
import threading
from dataclasses import dataclass
from typing import List

from ai_knowledge_service.abstractions.infrastructure.event_bus import DomainEvent
from ai_knowledge_service.implementations.infrastructure.memory_event_bus import (
    MemoryEventBus,
)


# Test events (prefixed with Sample to avoid pytest collection)
@dataclass
class SampleEvent(DomainEvent):
    message: str = ""


@dataclass
class AnotherSampleEvent(DomainEvent):
    value: int = 0


class TestMemoryEventBusSubscription:
    """Tests for event subscription."""

    def test_subscribe_returns_subscription_id(self):
        bus = MemoryEventBus()

        subscription_id = bus.subscribe(SampleEvent, lambda e: None)

        assert subscription_id is not None
        assert len(subscription_id) > 0

    def test_subscribe_multiple_handlers(self):
        bus = MemoryEventBus()
        received1 = []
        received2 = []

        bus.subscribe(SampleEvent, lambda e: received1.append(e))
        bus.subscribe(SampleEvent, lambda e: received2.append(e))

        event = SampleEvent(message="hello")
        bus.publish(event)

        assert len(received1) == 1
        assert len(received2) == 1

    def test_subscribe_all_receives_all_events(self):
        bus = MemoryEventBus()
        received: List[DomainEvent] = []

        bus.subscribe_all(lambda e: received.append(e))

        event1 = SampleEvent(message="hello")
        event2 = AnotherSampleEvent(value=42)

        bus.publish(event1)
        bus.publish(event2)

        assert len(received) == 2

    def test_unsubscribe_removes_handler(self):
        bus = MemoryEventBus()
        received = []

        sub_id = bus.subscribe(SampleEvent, lambda e: received.append(e))

        bus.publish(SampleEvent(message="first"))

        assert len(received) == 1

        bus.unsubscribe(sub_id)

        bus.publish(SampleEvent(message="second"))

        assert len(received) == 1  # Should not receive second event

    def test_unsubscribe_nonexistent_returns_false(self):
        bus = MemoryEventBus()

        result = bus.unsubscribe("nonexistent-id")

        assert result is False

    def test_unsubscribe_global_handler(self):
        bus = MemoryEventBus()
        received = []

        sub_id = bus.subscribe_all(lambda e: received.append(e))

        bus.publish(SampleEvent(message="first"))

        assert len(received) == 1

        result = bus.unsubscribe(sub_id)

        assert result is True

        bus.publish(SampleEvent(message="second"))

        assert len(received) == 1


class TestMemoryEventBusPublish:
    """Tests for event publishing."""

    def test_publish_to_specific_handler(self):
        bus = MemoryEventBus()
        received_test = []
        received_another = []

        bus.subscribe(SampleEvent, lambda e: received_test.append(e))
        bus.subscribe(AnotherSampleEvent, lambda e: received_another.append(e))

        bus.publish(SampleEvent(message="hello"))

        assert len(received_test) == 1
        assert len(received_another) == 0

    def test_publish_handler_exception_does_not_stop_others(self):
        bus = MemoryEventBus()
        received = []

        def failing_handler(e):
            raise ValueError("Handler error")

        bus.subscribe(SampleEvent, failing_handler)
        bus.subscribe(SampleEvent, lambda e: received.append(e))

        bus.publish(SampleEvent(message="hello"))  # Should not raise

        assert len(received) == 1

    def test_publish_with_no_handlers(self):
        bus = MemoryEventBus()

        bus.publish(SampleEvent(message="hello"))  # Should not raise


class TestMemoryEventBusGetHandlers:
    """Tests for getting handlers."""

    def test_get_handlers_for_event_type(self):
        bus = MemoryEventBus()

        bus.subscribe(SampleEvent, lambda e: None)
        bus.subscribe(SampleEvent, lambda e: None)

        handlers = bus.get_handlers(SampleEvent)

        assert len(handlers) == 2

    def test_get_handlers_includes_global_handlers(self):
        bus = MemoryEventBus()

        bus.subscribe(SampleEvent, lambda e: None)
        bus.subscribe_all(lambda e: None)

        handlers = bus.get_handlers(SampleEvent)

        assert len(handlers) == 2

    def test_get_handlers_for_unsubscribed_type(self):
        bus = MemoryEventBus()

        handlers = bus.get_handlers(SampleEvent)

        assert len(handlers) == 0


class TestMemoryEventBusClear:
    """Tests for clearing subscriptions."""

    def test_clear_removes_all_subscriptions(self):
        bus = MemoryEventBus()
        received = []

        bus.subscribe(SampleEvent, lambda e: received.append(e))
        bus.subscribe_all(lambda e: received.append(e))

        bus.clear()

        bus.publish(SampleEvent(message="hello"))

        assert len(received) == 0

    def test_get_handlers_after_clear(self):
        bus = MemoryEventBus()

        bus.subscribe(SampleEvent, lambda e: None)
        bus.subscribe_all(lambda e: None)

        bus.clear()

        handlers = bus.get_handlers(SampleEvent)

        assert len(handlers) == 0


class TestMemoryEventBusThreadSafety:
    """Tests for thread safety (basic checks)."""

    def test_concurrent_subscribe_and_publish(self):
        bus = MemoryEventBus()
        received = []
        lock = threading.Lock()

        def handler(e):
            with lock:
                received.append(e)

        def subscriber():
            for i in range(10):
                bus.subscribe(SampleEvent, handler)

        def publisher():
            for i in range(10):
                bus.publish(SampleEvent(message=f"msg-{i}"))

        threads = [
            threading.Thread(target=subscriber),
            threading.Thread(target=publisher),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should not crash and receive some events
        assert len(received) > 0
