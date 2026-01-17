"""
Tests for SqliteVersionManager - Version management implementation.
"""

import pytest
from datetime import datetime

from ai_knowledge_service.abstractions.models.knowledge_base import (
    VersionStatus,
    IndexStatus,
)
from ai_knowledge_service.implementations.infrastructure.sqlite_version_manager import (
    SqliteVersionManager,
)


# ============ Knowledge Base Tests ============


class TestKnowledgeBaseCreate:
    """Tests for knowledge base creation."""

    def test_create_knowledge_base(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        kb = manager.create_knowledge_base(
            id="kb-001",
            name="Test KB",
            description="A test knowledge base",
        )

        assert kb is not None
        assert kb.id == "kb-001"
        assert kb.name == "Test KB"
        assert kb.description == "A test knowledge base"
        assert kb.created_at is not None

    def test_create_duplicate_raises_error(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "First KB")

        with pytest.raises(ValueError, match="already exists"):
            manager.create_knowledge_base("kb-001", "Second KB")


class TestKnowledgeBaseGet:
    """Tests for knowledge base retrieval."""

    def test_get_knowledge_base(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB", "Description")

        kb = manager.get_knowledge_base("kb-001")

        assert kb is not None
        assert kb.id == "kb-001"
        assert kb.name == "Test KB"

    def test_get_nonexistent_returns_none(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        kb = manager.get_knowledge_base("nonexistent")

        assert kb is None


class TestKnowledgeBaseList:
    """Tests for knowledge base listing."""

    def test_list_knowledge_bases(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "First KB")
        manager.create_knowledge_base("kb-002", "Second KB")
        manager.create_knowledge_base("kb-003", "Third KB")

        kbs = manager.list_knowledge_bases()

        assert len(kbs) == 3

    def test_list_empty(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        kbs = manager.list_knowledge_bases()

        assert len(kbs) == 0


class TestKnowledgeBaseDelete:
    """Tests for knowledge base deletion."""

    def test_delete_knowledge_base(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")

        result = manager.delete_knowledge_base("kb-001")

        assert result is True
        assert manager.get_knowledge_base("kb-001") is None

    def test_delete_nonexistent_returns_false(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        result = manager.delete_knowledge_base("nonexistent")

        assert result is False

    def test_delete_cascades_to_versions(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")

        manager.delete_knowledge_base("kb-001")

        assert manager.get_version(version.id) is None


# ============ Version Tests ============


class TestVersionCreate:
    """Tests for version creation."""

    def test_create_version(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")

        version = manager.create_version("kb-001", "v1.0")

        assert version is not None
        assert version.knowledge_base_id == "kb-001"
        assert version.version_tag == "v1.0"
        assert version.status == VersionStatus.DRAFT

    def test_create_version_nonexistent_kb_raises_error(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        with pytest.raises(ValueError, match="not found"):
            manager.create_version("nonexistent", "v1.0")

    def test_create_duplicate_version_raises_error(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        manager.create_version("kb-001", "v1.0")

        with pytest.raises(ValueError, match="already exists"):
            manager.create_version("kb-001", "v1.0")

    def test_create_version_with_parent(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        v1 = manager.create_version("kb-001", "v1.0")
        v2 = manager.create_version("kb-001", "v2.0", parent_version_id=v1.id)

        assert v2.parent_version_id == v1.id


class TestVersionGet:
    """Tests for version retrieval."""

    def test_get_version(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        created = manager.create_version("kb-001", "v1.0")

        version = manager.get_version(created.id)

        assert version is not None
        assert version.id == created.id

    def test_get_version_by_tag(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        manager.create_version("kb-001", "v1.0")

        version = manager.get_version_by_tag("kb-001", "v1.0")

        assert version is not None
        assert version.version_tag == "v1.0"

    def test_get_latest_version(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        manager.create_version("kb-001", "v1.0")
        manager.create_version("kb-001", "v2.0")
        manager.create_version("kb-001", "v3.0")

        latest = manager.get_latest_version("kb-001")

        assert latest is not None
        assert latest.version_tag == "v3.0"

    def test_get_latest_version_by_status(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        v1 = manager.create_version("kb-001", "v1.0")
        manager.update_version_status(v1.id, VersionStatus.PUBLISHED)
        manager.create_version("kb-001", "v2.0")  # Draft

        latest_published = manager.get_latest_version(
            "kb-001", status=VersionStatus.PUBLISHED
        )

        assert latest_published is not None
        assert latest_published.version_tag == "v1.0"


class TestVersionList:
    """Tests for version listing."""

    def test_list_versions(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        manager.create_version("kb-001", "v1.0")
        manager.create_version("kb-001", "v2.0")
        manager.create_version("kb-001", "v3.0")

        versions = manager.list_versions("kb-001")

        assert len(versions) == 3

    def test_list_versions_by_status(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        v1 = manager.create_version("kb-001", "v1.0")
        manager.update_version_status(v1.id, VersionStatus.PUBLISHED)
        manager.create_version("kb-001", "v2.0")

        drafts = manager.list_versions("kb-001", status=VersionStatus.DRAFT)
        published = manager.list_versions("kb-001", status=VersionStatus.PUBLISHED)

        assert len(drafts) == 1
        assert len(published) == 1


class TestVersionUpdateStatus:
    """Tests for version status updates."""

    def test_update_version_status(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")

        manager.update_version_status(version.id, VersionStatus.BUILDING)

        updated = manager.get_version(version.id)

        assert updated.status == VersionStatus.BUILDING

    def test_update_to_published_sets_published_at(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")

        manager.update_version_status(version.id, VersionStatus.PUBLISHED)

        updated = manager.get_version(version.id)

        assert updated.published_at is not None

    def test_update_nonexistent_raises_error(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        with pytest.raises(ValueError, match="not found"):
            manager.update_version_status("nonexistent", VersionStatus.BUILDING)


class TestVersionDelete:
    """Tests for version deletion."""

    def test_delete_version(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")

        result = manager.delete_version(version.id)

        assert result is True
        assert manager.get_version(version.id) is None


# ============ File Version Tests ============


class TestFileVersionCreate:
    """Tests for file version creation."""

    def test_create_file_version(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")

        file_version = manager.create_file_version(
            raw_file_id="file-001",
            knowledge_base_version_id=version.id,
            content_hash="abc123def456",
        )

        assert file_version is not None
        assert file_version.raw_file_id == "file-001"
        assert file_version.index_status == IndexStatus.PENDING


class TestFileVersionGet:
    """Tests for file version retrieval."""

    def test_get_file_version(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")
        fv = manager.create_file_version("file-001", version.id, "hash123")

        retrieved = manager.get_file_version(fv.id)

        assert retrieved is not None
        assert retrieved.id == fv.id

    def test_get_file_version_by_raw_file(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")
        manager.create_file_version("file-001", version.id, "hash123")

        retrieved = manager.get_file_version_by_raw_file("file-001", version.id)

        assert retrieved is not None
        assert retrieved.raw_file_id == "file-001"


class TestFileVersionList:
    """Tests for file version listing."""

    def test_get_file_versions(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")

        for i in range(5):
            manager.create_file_version(f"file-{i:03d}", version.id, f"hash-{i}")

        file_versions = manager.get_file_versions(version.id)

        assert len(file_versions) == 5

    def test_get_file_versions_by_status(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")

        fv1 = manager.create_file_version("file-001", version.id, "hash1")
        manager.create_file_version("file-002", version.id, "hash2")

        manager.update_file_index_status(fv1.id, IndexStatus.INDEXED)

        pending = manager.get_file_versions(version.id, index_status=IndexStatus.PENDING)
        indexed = manager.get_file_versions(version.id, index_status=IndexStatus.INDEXED)

        assert len(pending) == 1
        assert len(indexed) == 1


class TestFileVersionUpdateStatus:
    """Tests for file version status updates."""

    def test_update_file_index_status(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")
        fv = manager.create_file_version("file-001", version.id, "hash123")

        manager.update_file_index_status(fv.id, IndexStatus.INDEXED)

        updated = manager.get_file_version(fv.id)

        assert updated.index_status == IndexStatus.INDEXED
        assert updated.indexed_at is not None


class TestFileVersionCount:
    """Tests for file version counting."""

    def test_count_file_versions(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        version = manager.create_version("kb-001", "v1.0")

        for i in range(5):
            manager.create_file_version(f"file-{i:03d}", version.id, f"hash-{i}")

        count = manager.count_file_versions(version.id)

        assert count == 5


class TestFileVersionChangedFiles:
    """Tests for changed file detection."""

    def test_get_changed_files_new_files(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        v1 = manager.create_version("kb-001", "v1.0")
        v2 = manager.create_version("kb-001", "v2.0", parent_version_id=v1.id)

        # Add files to v1
        manager.create_file_version("file-001", v1.id, "hash1")
        manager.create_file_version("file-002", v1.id, "hash2")

        # Add same files + new file to v2
        manager.create_file_version("file-001", v2.id, "hash1")
        manager.create_file_version("file-002", v2.id, "hash2")
        manager.create_file_version("file-003", v2.id, "hash3")  # New

        changed = manager.get_changed_files(v2.id, v1.id)

        assert len(changed) == 1
        assert changed[0].raw_file_id == "file-003"

    def test_get_changed_files_modified_files(self, temp_db_path):
        manager = SqliteVersionManager(temp_db_path)

        manager.create_knowledge_base("kb-001", "Test KB")
        v1 = manager.create_version("kb-001", "v1.0")
        v2 = manager.create_version("kb-001", "v2.0", parent_version_id=v1.id)

        # Add files to v1
        manager.create_file_version("file-001", v1.id, "hash1-v1")
        manager.create_file_version("file-002", v1.id, "hash2")

        # Add files to v2 with one modified
        manager.create_file_version("file-001", v2.id, "hash1-v2")  # Modified
        manager.create_file_version("file-002", v2.id, "hash2")

        changed = manager.get_changed_files(v2.id, v1.id)

        assert len(changed) == 1
        assert changed[0].raw_file_id == "file-001"
        assert changed[0].content_hash == "hash1-v2"
