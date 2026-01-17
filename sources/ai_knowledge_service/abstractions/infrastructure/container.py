"""
Service Container interface - Defines dependency injection.
"""

from enum import Enum
from typing import Any, Callable, Protocol, Type, TypeVar, runtime_checkable


class Lifetime(Enum):
    """Service lifetime options."""

    TRANSIENT = "transient"  # New instance every resolve
    SCOPED = "scoped"  # One instance per scope
    SINGLETON = "singleton"  # One instance globally


T = TypeVar("T")


@runtime_checkable
class IServiceScope(Protocol):
    """
    Service Scope - A scoped container for resolving services.

    Services with SCOPED lifetime are created once per scope.
    """

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a service within this scope.

        Args:
            interface: The interface/type to resolve.

        Returns:
            T: The service instance.

        Raises:
            KeyError: If the service is not registered.
        """
        ...

    def __enter__(self) -> "IServiceScope":
        """Enter the scope context."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the scope context, disposing scoped services."""
        ...


@runtime_checkable
class IServiceContainer(Protocol):
    """
    Service Container - Interface for dependency injection.

    Supports registration of services with different lifetimes
    and resolution of dependencies.
    """

    def register(
        self,
        interface: Type[T],
        implementation: Type[T] | Callable[..., T],
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> None:
        """
        Register a service.

        Args:
            interface: The interface/base type.
            implementation: The implementation class or factory function.
            lifetime: Service lifetime.

        Raises:
            ValueError: If interface is already registered.
        """
        ...

    def register_instance(
        self,
        interface: Type[T],
        instance: T,
    ) -> None:
        """
        Register a specific instance (singleton).

        Args:
            interface: The interface/base type.
            instance: The instance to use.
        """
        ...

    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[["IServiceContainer"], T],
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> None:
        """
        Register a factory function.

        The factory receives the container for resolving dependencies.

        Args:
            interface: The interface/base type.
            factory: Factory function that creates the service.
            lifetime: Service lifetime.
        """
        ...

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a service.

        Args:
            interface: The interface/type to resolve.

        Returns:
            T: The service instance.

        Raises:
            KeyError: If the service is not registered.
        """
        ...

    def try_resolve(self, interface: Type[T]) -> T | None:
        """
        Try to resolve a service.

        Args:
            interface: The interface/type to resolve.

        Returns:
            T | None: The service instance, or None if not registered.
        """
        ...

    def is_registered(self, interface: Type[Any]) -> bool:
        """
        Check if a service is registered.

        Args:
            interface: The interface/type to check.

        Returns:
            bool: True if registered.
        """
        ...

    def create_scope(self) -> IServiceScope:
        """
        Create a new scope.

        Returns:
            IServiceScope: A new service scope.
        """
        ...

    def unregister(self, interface: Type[Any]) -> bool:
        """
        Unregister a service.

        Args:
            interface: The interface to unregister.

        Returns:
            bool: True if the service was unregistered.
        """
        ...

    def clear(self) -> None:
        """
        Clear all registrations.
        """
        ...

    @property
    def registered_services(self) -> list[Type[Any]]:
        """Get list of all registered interfaces."""
        ...
