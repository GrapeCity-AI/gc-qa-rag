"""
Tests for storage implementations:
- FilesystemContentStore
- SqliteMetadataStore
- CompositeRawFileStorage
"""

import pytest
from datetime import datetime
from pathlib import Path

from ai_knowledge_service.abstractions.models.raw_file import RawFile, LifecycleStatus
from ai_knowledge_service.abstractions.storage.raw_file_storage import QueryCriteria
from ai_knowledge_service.abstractions.pipelines.source import SourceRecord
from ai_knowledge_service.implementations.storage.filesystem_content_store import (
    FilesystemContentStore,
)
from ai_knowledge_service.implementations.storage.sqlite_metadata_store import (
    SqliteMetadataStore,
)
from ai_knowledge_service.implementations.storage.composite_raw_file_storage import (
    CompositeRawFileStorage,
)


# ============ FilesystemContentStore Tests ============


class TestFilesystemContentStoreWrite:
    """Tests for content writing."""

    def test_write_returns_storage_path(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)

        path = store.write(
            file_id="file-001",
            content=b"Hello, World!",
            knowledge_base_id="kb-1",
        )

        assert path is not None
        assert "kb-1" in path
        assert "file-001" in path

    def test_write_creates_file(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)

        path = store.write(
            file_id="file-001",
            content=b"Hello, World!",
            knowledge_base_id="kb-1",
        )

        full_path = temp_storage_path / path
        assert full_path.exists()

    def test_write_preserves_content(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)
        content = b"Test content \x00\x01\x02"

        path = store.write(
            file_id="file-001",
            content=content,
            knowledge_base_id="kb-1",
        )

        full_path = temp_storage_path / path
        with open(full_path, "rb") as f:
            assert f.read() == content


class TestFilesystemContentStoreRead:
    """Tests for content reading."""

    def test_read_returns_content(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)
        content = b"Test content"

        path = store.write("file-001", content, "kb-1")

        result = store.read(path)

        assert result == content

    def test_read_nonexistent_raises_error(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)

        with pytest.raises(FileNotFoundError):
            store.read("nonexistent/path")


class TestFilesystemContentStoreDelete:
    """Tests for content deletion."""

    def test_delete_removes_file(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)

        path = store.write("file-001", b"content", "kb-1")

        result = store.delete(path)

        assert result is True
        assert not store.exists(path)

    def test_delete_nonexistent_returns_false(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)

        result = store.delete("nonexistent/path")

        assert result is False


class TestFilesystemContentStoreExists:
    """Tests for existence checking."""

    def test_exists_returns_true_for_existing(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)

        path = store.write("file-001", b"content", "kb-1")

        assert store.exists(path) is True

    def test_exists_returns_false_for_nonexistent(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)

        assert store.exists("nonexistent/path") is False


class TestFilesystemContentStoreGetSize:
    """Tests for size retrieval."""

    def test_get_size_returns_correct_size(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)
        content = b"12345678901234567890"  # 20 bytes

        path = store.write("file-001", content, "kb-1")

        assert store.get_size(path) == 20

    def test_get_size_nonexistent_raises_error(self, temp_storage_path):
        store = FilesystemContentStore(temp_storage_path)

        with pytest.raises(FileNotFoundError):
            store.get_size("nonexistent/path")


class TestFilesystemContentStoreComputeHash:
    """Tests for hash computation."""

    def test_compute_hash_returns_consistent_hash(self, temp_storage_path):
        content = b"Test content"

        hash1 = FilesystemContentStore.compute_hash(content)
        hash2 = FilesystemContentStore.compute_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters


# ============ SqliteMetadataStore Tests ============


def create_raw_file(
    file_id: str = "file-001",
    knowledge_base_id: str = "kb-1",
    content_hash: str = "abc123",
) -> RawFile:
    """Create a test RawFile."""
    return RawFile(
        id=file_id,
        knowledge_base_id=knowledge_base_id,
        source_type="test",
        source_uri=f"test://{file_id}",
        original_name=f"{file_id}.txt",
        content_hash=content_hash,
        storage_path=f"{knowledge_base_id}/{file_id[:2]}/{file_id}",
        mime_type="text/plain",
        size_bytes=100,
        metadata={},
        lifecycle_status=LifecycleStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestSqliteMetadataStoreSave:
    """Tests for metadata saving."""

    def test_save_and_get(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)
        raw_file = create_raw_file()

        store.save(raw_file)

        retrieved = store.get(raw_file.id)

        assert retrieved is not None
        assert retrieved.id == raw_file.id
        assert retrieved.knowledge_base_id == raw_file.knowledge_base_id

    def test_save_updates_existing(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)
        raw_file = create_raw_file()

        store.save(raw_file)

        raw_file.original_name = "updated.txt"
        store.save(raw_file)

        retrieved = store.get(raw_file.id)

        assert retrieved.original_name == "updated.txt"


class TestSqliteMetadataStoreQuery:
    """Tests for metadata querying."""

    def test_query_by_knowledge_base(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)

        store.save(create_raw_file("f1", "kb-1"))
        store.save(create_raw_file("f2", "kb-1"))
        store.save(create_raw_file("f3", "kb-2"))

        criteria = QueryCriteria(knowledge_base_id="kb-1")
        results = store.query(criteria)

        assert len(results) == 2

    def test_query_by_status(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)

        active_file = create_raw_file("f1")
        deleted_file = create_raw_file("f2")
        deleted_file.lifecycle_status = LifecycleStatus.DELETED

        store.save(active_file)
        store.save(deleted_file)

        criteria = QueryCriteria(
            knowledge_base_id="kb-1",
            lifecycle_status=LifecycleStatus.ACTIVE,
        )
        results = store.query(criteria)

        assert len(results) == 1
        assert results[0].id == "f1"

    def test_query_with_limit_and_offset(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)

        for i in range(10):
            store.save(create_raw_file(f"f{i:02d}"))

        criteria = QueryCriteria(knowledge_base_id="kb-1", limit=3, offset=2)
        results = store.query(criteria)

        assert len(results) == 3


class TestSqliteMetadataStoreCount:
    """Tests for counting."""

    def test_count_all_in_knowledge_base(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)

        for i in range(5):
            store.save(create_raw_file(f"f{i}"))

        criteria = QueryCriteria(knowledge_base_id="kb-1")
        count = store.count(criteria)

        assert count == 5

    def test_count_by_status(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)

        for i in range(3):
            store.save(create_raw_file(f"active-{i}"))

        for i in range(2):
            deleted = create_raw_file(f"deleted-{i}")
            deleted.lifecycle_status = LifecycleStatus.DELETED
            store.save(deleted)

        criteria = QueryCriteria(
            knowledge_base_id="kb-1",
            lifecycle_status=LifecycleStatus.ACTIVE,
        )
        count = store.count(criteria)

        assert count == 3


class TestSqliteMetadataStoreExistsByHash:
    """Tests for hash existence checking."""

    def test_exists_by_hash_returns_id(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)
        raw_file = create_raw_file(content_hash="unique-hash-123")

        store.save(raw_file)

        result = store.exists_by_hash("kb-1", "unique-hash-123")

        assert result == raw_file.id

    def test_exists_by_hash_returns_none(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)

        result = store.exists_by_hash("kb-1", "nonexistent-hash")

        assert result is None

    def test_exists_by_hash_ignores_deleted(self, temp_db_path):
        store = SqliteMetadataStore(temp_db_path)
        raw_file = create_raw_file(content_hash="deleted-hash")
        raw_file.lifecycle_status = LifecycleStatus.DELETED

        store.save(raw_file)

        result = store.exists_by_hash("kb-1", "deleted-hash")

        assert result is None


# ============ CompositeRawFileStorage Tests ============


class TestCompositeRawFileStorageSave:
    """Tests for composite storage saving."""

    def test_save_stores_content_and_metadata(self, temp_dir):
        content_store = FilesystemContentStore(temp_dir / "content")
        metadata_store = SqliteMetadataStore(temp_dir / "metadata.db")
        storage = CompositeRawFileStorage(metadata_store, content_store)

        record = SourceRecord(
            source_uri="test://doc1",
            content=b"Test content",
            content_type="text/plain",
            metadata={"source_type": "test"},
        )

        raw_file = storage.save(record, "kb-1")

        assert raw_file is not None
        assert raw_file.id is not None
        assert content_store.exists(raw_file.storage_path)
        assert metadata_store.get(raw_file.id) is not None

    def test_save_deduplicates_by_hash(self, temp_dir):
        content_store = FilesystemContentStore(temp_dir / "content")
        metadata_store = SqliteMetadataStore(temp_dir / "metadata.db")
        storage = CompositeRawFileStorage(metadata_store, content_store)

        record = SourceRecord(
            source_uri="test://doc1",
            content=b"Same content",
            content_type="text/plain",
            metadata={"source_type": "test"},
        )

        file1 = storage.save(record, "kb-1")
        file2 = storage.save(record, "kb-1")

        assert file1.id == file2.id


class TestCompositeRawFileStorageGetContent:
    """Tests for content retrieval."""

    def test_get_content(self, temp_dir):
        content_store = FilesystemContentStore(temp_dir / "content")
        metadata_store = SqliteMetadataStore(temp_dir / "metadata.db")
        storage = CompositeRawFileStorage(metadata_store, content_store)

        content = b"Test content for retrieval"
        record = SourceRecord(
            source_uri="test://doc1",
            content=content,
            content_type="text/plain",
            metadata={"source_type": "test"},
        )

        raw_file = storage.save(record, "kb-1")

        retrieved_content = storage.get_content(raw_file.id)

        assert retrieved_content == content

    def test_get_content_nonexistent_raises_error(self, temp_dir):
        content_store = FilesystemContentStore(temp_dir / "content")
        metadata_store = SqliteMetadataStore(temp_dir / "metadata.db")
        storage = CompositeRawFileStorage(metadata_store, content_store)

        with pytest.raises(FileNotFoundError):
            storage.get_content("nonexistent-id")


class TestCompositeRawFileStorageList:
    """Tests for listing files."""

    def test_list_files(self, temp_dir):
        content_store = FilesystemContentStore(temp_dir / "content")
        metadata_store = SqliteMetadataStore(temp_dir / "metadata.db")
        storage = CompositeRawFileStorage(metadata_store, content_store)

        for i in range(5):
            record = SourceRecord(
                source_uri=f"test://doc{i}",
                content=f"Content {i}".encode(),
                content_type="text/plain",
                metadata={"source_type": "test"},
            )
            storage.save(record, "kb-1")

        files = list(storage.list("kb-1"))

        assert len(files) == 5


class TestCompositeRawFileStorageUpdateStatus:
    """Tests for status updates."""

    def test_update_status(self, temp_dir):
        content_store = FilesystemContentStore(temp_dir / "content")
        metadata_store = SqliteMetadataStore(temp_dir / "metadata.db")
        storage = CompositeRawFileStorage(metadata_store, content_store)

        record = SourceRecord(
            source_uri="test://doc1",
            content=b"Content",
            content_type="text/plain",
            metadata={"source_type": "test"},
        )
        raw_file = storage.save(record, "kb-1")

        storage.update_status(raw_file.id, LifecycleStatus.ARCHIVED)

        updated = storage.get(raw_file.id)

        assert updated.lifecycle_status == LifecycleStatus.ARCHIVED


class TestCompositeRawFileStorageDelete:
    """Tests for logical deletion."""

    def test_delete_marks_as_deleted(self, temp_dir):
        content_store = FilesystemContentStore(temp_dir / "content")
        metadata_store = SqliteMetadataStore(temp_dir / "metadata.db")
        storage = CompositeRawFileStorage(metadata_store, content_store)

        record = SourceRecord(
            source_uri="test://doc1",
            content=b"Content",
            content_type="text/plain",
            metadata={"source_type": "test"},
        )
        raw_file = storage.save(record, "kb-1")

        result = storage.delete(raw_file.id)

        assert result is True

        deleted = storage.get(raw_file.id)
        assert deleted.lifecycle_status == LifecycleStatus.DELETED

    def test_delete_nonexistent_returns_false(self, temp_dir):
        content_store = FilesystemContentStore(temp_dir / "content")
        metadata_store = SqliteMetadataStore(temp_dir / "metadata.db")
        storage = CompositeRawFileStorage(metadata_store, content_store)

        result = storage.delete("nonexistent-id")

        assert result is False
