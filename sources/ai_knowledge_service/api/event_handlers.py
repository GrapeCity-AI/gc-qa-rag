"""
Event Handlers - Domain event handlers for task completion.

These handlers listen for task completion events and update version statuses.
"""

import logging
from typing import Optional

from ai_knowledge_service.abstractions.infrastructure.event_bus import (
    BuildTaskCompletedEvent,
    IEventBus,
    VersionPublishedEvent,
)
from ai_knowledge_service.abstractions.infrastructure.version_manager import IVersionManager
from ai_knowledge_service.abstractions.models.knowledge_base import VersionStatus


logger = logging.getLogger(__name__)


class TaskCompletionHandler:
    """
    Handles task completion events and updates version status.

    Subscribes to:
    - BuildTaskCompletedEvent: Updates version status to READY or FAILED
    - VersionPublishedEvent: Updates version status to PUBLISHED
    """

    def __init__(
        self,
        event_bus: IEventBus,
        version_manager: IVersionManager,
    ):
        """
        Initialize the handler.

        Args:
            event_bus: Event bus to subscribe to.
            version_manager: Version manager for status updates.
        """
        self._event_bus = event_bus
        self._version_manager = version_manager
        self._subscription_ids: list[str] = []
        self._running = False

    def start(self) -> None:
        """Start listening to task completion events."""
        if self._running:
            return

        self._running = True

        # Subscribe to build task completion events
        sub_id = self._event_bus.subscribe(
            BuildTaskCompletedEvent,
            self._handle_build_completed,
        )
        self._subscription_ids.append(sub_id)

        # Subscribe to version published events
        sub_id = self._event_bus.subscribe(
            VersionPublishedEvent,
            self._handle_published,
        )
        self._subscription_ids.append(sub_id)

        logger.info("TaskCompletionHandler started")

    def stop(self) -> None:
        """Stop listening to task completion events."""
        if not self._running:
            return

        self._running = False

        for sub_id in self._subscription_ids:
            try:
                self._event_bus.unsubscribe(sub_id)
            except Exception as e:
                logger.warning(f"Failed to unsubscribe {sub_id}: {e}")

        self._subscription_ids.clear()
        logger.info("TaskCompletionHandler stopped")

    def _handle_build_completed(self, event: BuildTaskCompletedEvent) -> None:
        """Handle build task completion event."""
        try:
            version_id = event.knowledge_base_version_id

            if event.success:
                status = VersionStatus.READY
                logger.info(
                    f"Build completed successfully for version {version_id}, "
                    f"indexed {event.records_indexed} records"
                )
            else:
                status = VersionStatus.FAILED
                logger.warning(
                    f"Build failed for version {version_id} "
                    f"with {event.errors_count} errors"
                )

            self._version_manager.update_version_status(version_id, status)
            logger.debug(f"Updated version {version_id} status to {status.value}")

        except Exception as e:
            logger.error(f"Failed to handle build completed event: {e}")

    def _handle_published(self, event: VersionPublishedEvent) -> None:
        """Handle version published event."""
        try:
            version_id = event.knowledge_base_version_id

            self._version_manager.update_version_status(
                version_id,
                VersionStatus.PUBLISHED,
            )

            logger.info(
                f"Version {version_id} published to {event.target_environment_id}, "
                f"collection={event.target_collection}, alias={event.alias_applied}"
            )

        except Exception as e:
            logger.error(f"Failed to handle published event: {e}")

    @property
    def is_running(self) -> bool:
        """Check if the handler is running."""
        return self._running
