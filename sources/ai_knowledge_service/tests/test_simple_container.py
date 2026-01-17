"""
Tests for SimpleContainer - Dependency Injection Container.
"""

import pytest
from typing import Protocol

from ai_knowledge_service.abstractions.infrastructure.container import Lifetime
from ai_knowledge_service.implementations.infrastructure.simple_container import (
    SimpleContainer,
    ServiceScope,
)


# Test interfaces and implementations
class IDatabase(Protocol):
    def query(self, sql: str) -> str:
        ...


class ILogger(Protocol):
    def log(self, message: str) -> None:
        ...


class IService(Protocol):
    def process(self) -> str:
        ...


class MockDatabase:
    def __init__(self):
        self.instance_id = id(self)

    def query(self, sql: str) -> str:
        return f"Result: {sql}"


class MockLogger:
    def __init__(self):
        self.messages = []
        self.instance_id = id(self)

    def log(self, message: str) -> None:
        self.messages.append(message)


class MockService:
    def __init__(self, database: IDatabase, logger: ILogger):
        self.database = database
        self.logger = logger
        self.instance_id = id(self)

    def process(self) -> str:
        result = self.database.query("SELECT 1")
        self.logger.log(f"Processed: {result}")
        return result


class DisposableService:
    def __init__(self):
        self.disposed = False

    def dispose(self):
        self.disposed = True


class CloseableService:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


# Circular dependency test classes - must be at module level for proper type resolution
class CircularB:
    """Second class in circular dependency chain."""

    def __init__(self, a: "CircularA"):
        self.a = a


class CircularA:
    """First class in circular dependency chain - depends on CircularB which depends on CircularA."""

    def __init__(self, b: CircularB):
        self.b = b


class TestSimpleContainerRegistration:
    """Tests for service registration."""

    def test_register_implementation(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase)

        assert container.is_registered(IDatabase)

    def test_register_duplicate_raises_error(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase)

        with pytest.raises(ValueError, match="already registered"):
            container.register(IDatabase, MockDatabase)

    def test_register_instance(self):
        container = SimpleContainer()
        instance = MockDatabase()
        container.register_instance(IDatabase, instance)

        assert container.is_registered(IDatabase)
        assert container.resolve(IDatabase) is instance

    def test_register_factory(self):
        container = SimpleContainer()

        def factory():
            return MockDatabase()

        container.register_factory(IDatabase, factory)

        assert container.is_registered(IDatabase)

    def test_unregister_service(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase)

        assert container.unregister(IDatabase)
        assert not container.is_registered(IDatabase)

    def test_unregister_nonexistent_returns_false(self):
        container = SimpleContainer()

        assert not container.unregister(IDatabase)

    def test_clear_registrations(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase)
        container.register(ILogger, MockLogger)

        container.clear()

        assert not container.is_registered(IDatabase)
        assert not container.is_registered(ILogger)

    def test_registered_services(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase)
        container.register(ILogger, MockLogger)

        services = container.registered_services

        assert IDatabase in services
        assert ILogger in services
        assert len(services) == 2


class TestSimpleContainerResolution:
    """Tests for service resolution."""

    def test_resolve_transient(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase, Lifetime.TRANSIENT)

        db1 = container.resolve(IDatabase)
        db2 = container.resolve(IDatabase)

        assert db1.instance_id != db2.instance_id

    def test_resolve_singleton(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase, Lifetime.SINGLETON)

        db1 = container.resolve(IDatabase)
        db2 = container.resolve(IDatabase)

        assert db1.instance_id == db2.instance_id

    def test_resolve_unregistered_raises_error(self):
        container = SimpleContainer()

        with pytest.raises(KeyError, match="not registered"):
            container.resolve(IDatabase)

    def test_try_resolve_returns_none_for_unregistered(self):
        container = SimpleContainer()

        result = container.try_resolve(IDatabase)

        assert result is None

    def test_try_resolve_returns_instance_for_registered(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase)

        result = container.try_resolve(IDatabase)

        assert isinstance(result, MockDatabase)


class TestConstructorInjection:
    """Tests for constructor injection."""

    def test_inject_dependencies(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase)
        container.register(ILogger, MockLogger)
        container.register(IService, MockService)

        service = container.resolve(IService)

        assert isinstance(service.database, MockDatabase)
        assert isinstance(service.logger, MockLogger)

    def test_factory_with_container_parameter(self):
        from ai_knowledge_service.abstractions.infrastructure.container import (
            IServiceContainer,
        )

        container = SimpleContainer()
        container.register(IDatabase, MockDatabase)

        def logger_factory(c: IServiceContainer):
            # Can use container to resolve dependencies
            return MockLogger()

        container.register_factory(ILogger, logger_factory)

        logger = container.resolve(ILogger)

        assert isinstance(logger, MockLogger)


class TestServiceScope:
    """Tests for scoped services."""

    def test_scoped_service_same_within_scope(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase, Lifetime.SCOPED)

        with container.create_scope() as scope:
            db1 = scope.resolve(IDatabase)
            db2 = scope.resolve(IDatabase)

            assert db1.instance_id == db2.instance_id

    def test_scoped_service_different_between_scopes(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase, Lifetime.SCOPED)

        with container.create_scope() as scope1:
            db1 = scope1.resolve(IDatabase)

        with container.create_scope() as scope2:
            db2 = scope2.resolve(IDatabase)

        assert db1.instance_id != db2.instance_id

    def test_resolve_scoped_without_scope_raises_error(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase, Lifetime.SCOPED)

        with pytest.raises(RuntimeError, match="without a scope"):
            container.resolve(IDatabase)

    def test_scope_disposes_disposable_services(self):
        container = SimpleContainer()
        container.register(DisposableService, DisposableService, Lifetime.SCOPED)

        with container.create_scope() as scope:
            service = scope.resolve(DisposableService)
            assert not service.disposed

        assert service.disposed

    def test_scope_closes_closeable_services(self):
        container = SimpleContainer()
        container.register(CloseableService, CloseableService, Lifetime.SCOPED)

        with container.create_scope() as scope:
            service = scope.resolve(CloseableService)
            assert not service.closed

        assert service.closed

    def test_resolve_from_disposed_scope_raises_error(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase, Lifetime.SCOPED)

        scope = container.create_scope()
        scope.__enter__()
        scope.__exit__(None, None, None)

        with pytest.raises(RuntimeError, match="disposed scope"):
            scope.resolve(IDatabase)

    def test_singleton_in_scope_returns_same_instance(self):
        container = SimpleContainer()
        container.register(IDatabase, MockDatabase, Lifetime.SINGLETON)

        global_db = container.resolve(IDatabase)

        with container.create_scope() as scope:
            scoped_db = scope.resolve(IDatabase)

            assert global_db.instance_id == scoped_db.instance_id


class TestCircularDependency:
    """Tests for circular dependency detection."""

    def test_circular_dependency_detection(self):
        # Define classes at module level to allow proper type resolution
        # We simulate circular dependency by having A depend on B and B depend on A

        container = SimpleContainer()

        # Register services that will create a cycle when resolved
        # Using a simpler approach: create classes that explicitly reference each other
        class ServiceX:
            pass

        class ServiceY:
            def __init__(self, x: ServiceX):
                self.x = x

        class ServiceZ:
            def __init__(self, y: ServiceY):
                self.y = y

        container.register(ServiceX, ServiceX)
        container.register(ServiceY, ServiceY)
        container.register(ServiceZ, ServiceZ)

        # This should work - no cycle
        z = container.resolve(ServiceZ)
        assert isinstance(z, ServiceZ)
        assert isinstance(z.y, ServiceY)

    def test_self_referencing_raises_error(self):
        """Test that mutually dependent services raise circular dependency error."""
        container = SimpleContainer()

        # Use the module-level CircularA and CircularB classes
        # CircularA depends on CircularB, and CircularB depends on CircularA
        container.register(CircularA, CircularA)
        container.register(CircularB, CircularB)

        with pytest.raises(RuntimeError, match="Circular dependency"):
            container.resolve(CircularA)
