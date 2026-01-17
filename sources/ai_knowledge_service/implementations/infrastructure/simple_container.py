"""
Simple Container - A lightweight dependency injection container.

This implementation provides:
- Service registration with different lifetimes (transient, scoped, singleton)
- Constructor injection via type hints
- Factory function registration
- Instance registration
- Scoped service resolution
"""

import inspect
import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, get_type_hints

from ai_knowledge_service.abstractions.infrastructure.container import (
    IServiceContainer,
    IServiceScope,
    Lifetime,
)


T = TypeVar("T")


@dataclass
class ServiceRegistration:
    """Internal registration record."""

    interface: Type[Any]
    implementation: Optional[Type[Any]] = None
    factory: Optional[Callable[..., Any]] = None
    instance: Optional[Any] = None
    lifetime: Lifetime = Lifetime.TRANSIENT


class ServiceScope(IServiceScope):
    """
    Service Scope implementation.

    Manages scoped service instances within a scope context.
    """

    def __init__(self, container: "SimpleContainer"):
        self._container = container
        self._scoped_instances: Dict[Type[Any], Any] = {}
        self._disposed = False

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service within this scope."""
        if self._disposed:
            raise RuntimeError("Cannot resolve from a disposed scope")

        registration = self._container._get_registration(interface)
        if registration is None:
            raise KeyError(f"Service not registered: {interface.__name__}")

        if registration.lifetime == Lifetime.SCOPED:
            if interface in self._scoped_instances:
                return self._scoped_instances[interface]

            instance = self._container._create_instance(registration, self)
            self._scoped_instances[interface] = instance
            return instance

        return self._container._resolve_with_scope(registration, self)

    def __enter__(self) -> "ServiceScope":
        """Enter the scope context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the scope context, disposing scoped services."""
        self._disposed = True
        for instance in self._scoped_instances.values():
            if hasattr(instance, "dispose"):
                try:
                    instance.dispose()
                except Exception:
                    pass
            elif hasattr(instance, "close"):
                try:
                    instance.close()
                except Exception:
                    pass
        self._scoped_instances.clear()


class SimpleContainer(IServiceContainer):
    """
    Simple dependency injection container.

    Thread-safe implementation supporting:
    - Transient: New instance every resolve
    - Scoped: One instance per scope
    - Singleton: One instance globally
    """

    def __init__(self):
        self._registrations: Dict[Type[Any], ServiceRegistration] = {}
        self._singletons: Dict[Type[Any], Any] = {}
        self._lock = threading.RLock()
        self._resolving: Set[Type[Any]] = set()

    def register(
        self,
        interface: Type[T],
        implementation: Type[T] | Callable[..., T],
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> None:
        """Register a service."""
        with self._lock:
            if interface in self._registrations:
                raise ValueError(f"Service already registered: {interface.__name__}")

            if callable(implementation) and not inspect.isclass(implementation):
                self._registrations[interface] = ServiceRegistration(
                    interface=interface,
                    factory=implementation,
                    lifetime=lifetime,
                )
            else:
                self._registrations[interface] = ServiceRegistration(
                    interface=interface,
                    implementation=implementation,
                    lifetime=lifetime,
                )

    def register_instance(
        self,
        interface: Type[T],
        instance: T,
    ) -> None:
        """Register a specific instance (singleton)."""
        with self._lock:
            self._registrations[interface] = ServiceRegistration(
                interface=interface,
                instance=instance,
                lifetime=Lifetime.SINGLETON,
            )
            self._singletons[interface] = instance

    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[["IServiceContainer"], T],
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> None:
        """Register a factory function."""
        with self._lock:
            if interface in self._registrations:
                raise ValueError(f"Service already registered: {interface.__name__}")

            self._registrations[interface] = ServiceRegistration(
                interface=interface,
                factory=factory,
                lifetime=lifetime,
            )

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service."""
        registration = self._get_registration(interface)
        if registration is None:
            raise KeyError(f"Service not registered: {interface.__name__}")

        return self._resolve_with_scope(registration, None)

    def try_resolve(self, interface: Type[T]) -> T | None:
        """Try to resolve a service."""
        try:
            return self.resolve(interface)
        except KeyError:
            return None

    def is_registered(self, interface: Type[Any]) -> bool:
        """Check if a service is registered."""
        with self._lock:
            return interface in self._registrations

    def create_scope(self) -> IServiceScope:
        """Create a new scope."""
        return ServiceScope(self)

    def unregister(self, interface: Type[Any]) -> bool:
        """Unregister a service."""
        with self._lock:
            if interface in self._registrations:
                del self._registrations[interface]
                self._singletons.pop(interface, None)
                return True
            return False

    def clear(self) -> None:
        """Clear all registrations."""
        with self._lock:
            self._registrations.clear()
            self._singletons.clear()

    @property
    def registered_services(self) -> List[Type[Any]]:
        """Get list of all registered interfaces."""
        with self._lock:
            return list(self._registrations.keys())

    def _get_registration(self, interface: Type[Any]) -> Optional[ServiceRegistration]:
        """Get registration for an interface."""
        with self._lock:
            return self._registrations.get(interface)

    def _resolve_with_scope(
        self,
        registration: ServiceRegistration,
        scope: Optional[ServiceScope],
    ) -> Any:
        """Resolve a service with optional scope context."""
        interface = registration.interface

        if registration.lifetime == Lifetime.SINGLETON:
            with self._lock:
                if interface in self._singletons:
                    return self._singletons[interface]

                instance = self._create_instance(registration, scope)
                self._singletons[interface] = instance
                return instance

        if registration.lifetime == Lifetime.SCOPED:
            if scope is None:
                raise RuntimeError(
                    f"Cannot resolve scoped service {interface.__name__} without a scope"
                )
            return scope.resolve(interface)

        return self._create_instance(registration, scope)

    def _create_instance(
        self,
        registration: ServiceRegistration,
        scope: Optional[ServiceScope],
    ) -> Any:
        """Create an instance of the registered service."""
        interface = registration.interface

        if interface in self._resolving:
            raise RuntimeError(f"Circular dependency detected: {interface.__name__}")

        self._resolving.add(interface)
        try:
            if registration.instance is not None:
                return registration.instance

            if registration.factory is not None:
                sig = inspect.signature(registration.factory)
                params = sig.parameters

                if len(params) == 1:
                    first_param = list(params.values())[0]
                    if first_param.annotation in (IServiceContainer, "IServiceContainer"):
                        return registration.factory(self)

                return self._call_with_injection(registration.factory, scope)

            if registration.implementation is not None:
                return self._call_with_injection(registration.implementation, scope)

            raise RuntimeError(f"No implementation for {interface.__name__}")

        finally:
            self._resolving.discard(interface)

    def _call_with_injection(
        self,
        callable_obj: Callable[..., Any],
        scope: Optional[ServiceScope],
    ) -> Any:
        """Call a callable with constructor injection."""
        try:
            # For classes, get type hints from __init__ method
            if inspect.isclass(callable_obj):
                hints = get_type_hints(callable_obj.__init__)
            else:
                hints = get_type_hints(callable_obj)
        except Exception:
            hints = {}

        sig = inspect.signature(callable_obj)
        kwargs: Dict[str, Any] = {}

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            if param.default != inspect.Parameter.empty:
                continue

            param_type = hints.get(name, param.annotation)
            if param_type == inspect.Parameter.empty:
                continue

            if self.is_registered(param_type):
                reg = self._get_registration(param_type)
                if reg is not None:
                    kwargs[name] = self._resolve_with_scope(reg, scope)

        return callable_obj(**kwargs)
