"""
Health Check interfaces - Defines health checking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Protocol, runtime_checkable


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"  # Component is fully operational
    DEGRADED = "degraded"  # Component is operational but with issues
    UNHEALTHY = "unhealthy"  # Component is not operational

    @property
    def is_operational(self) -> bool:
        """Check if the status indicates operational state."""
        return self in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    component: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0

    @classmethod
    def healthy(
        cls,
        component: str,
        message: str = "OK",
        **details: Any,
    ) -> "HealthCheckResult":
        """Create a healthy result."""
        return cls(
            component=component,
            status=HealthStatus.HEALTHY,
            message=message,
            details=details,
        )

    @classmethod
    def degraded(
        cls,
        component: str,
        message: str,
        **details: Any,
    ) -> "HealthCheckResult":
        """Create a degraded result."""
        return cls(
            component=component,
            status=HealthStatus.DEGRADED,
            message=message,
            details=details,
        )

    @classmethod
    def unhealthy(
        cls,
        component: str,
        message: str,
        **details: Any,
    ) -> "HealthCheckResult":
        """Create an unhealthy result."""
        return cls(
            component=component,
            status=HealthStatus.UNHEALTHY,
            message=message,
            details=details,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
            "duration_ms": self.duration_ms,
        }


@runtime_checkable
class IHealthCheck(Protocol):
    """
    Health Check - Interface for checking component health.

    Each component that needs health monitoring should implement this.
    """

    @property
    def component_name(self) -> str:
        """Get the component name."""
        ...

    def check(self) -> HealthCheckResult:
        """
        Perform the health check.

        Returns:
            HealthCheckResult: The health check result.
        """
        ...

    @property
    def is_critical(self) -> bool:
        """
        Check if this component is critical.

        Critical components failing will make the overall status UNHEALTHY.
        Non-critical components failing will make it DEGRADED.
        """
        ...


@runtime_checkable
class IHealthChecker(Protocol):
    """
    Health Checker - Manages and runs health checks.
    """

    def register(self, check: IHealthCheck) -> None:
        """
        Register a health check.

        Args:
            check: The health check to register.
        """
        ...

    def unregister(self, component_name: str) -> bool:
        """
        Unregister a health check.

        Args:
            component_name: Name of the component to unregister.

        Returns:
            bool: True if a check was unregistered.
        """
        ...

    def check(self, component_name: str) -> HealthCheckResult:
        """
        Run a specific health check.

        Args:
            component_name: Name of the component to check.

        Returns:
            HealthCheckResult: The health check result.

        Raises:
            KeyError: If no check is registered for the component.
        """
        ...

    def check_all(self) -> List[HealthCheckResult]:
        """
        Run all registered health checks.

        Returns:
            List[HealthCheckResult]: All health check results.
        """
        ...

    def get_overall_status(self) -> HealthStatus:
        """
        Get the overall health status.

        The overall status is:
        - UNHEALTHY if any critical component is unhealthy
        - DEGRADED if any component is degraded or non-critical unhealthy
        - HEALTHY if all components are healthy

        Returns:
            HealthStatus: Overall health status.
        """
        ...

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all health checks.

        Returns:
            Dict[str, Any]: Summary including overall status and all results.
        """
        ...

    @property
    def registered_checks(self) -> List[str]:
        """Get names of all registered health checks."""
        ...
