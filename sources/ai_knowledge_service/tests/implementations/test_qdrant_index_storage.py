"""
Tests for Qdrant Index Storage.
"""

from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

import pytest

from ai_knowledge_service.abstractions.models.index import (
    IndexRecord,
    IndexSchema,
    VectorConfig,
)
from ai_knowledge_service.implementations.storage.qdrant_index_storage import (
    QdrantIndexStorage,
    QdrantConfig,
)


class TestQdrantIndexStorage:
    """Tests for QdrantIndexStorage."""

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_init(self, mock_qdrant_class):
        """Test storage initialization."""
        mock_client = Mock()
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333", api_key="test-key")
        storage = QdrantIndexStorage(config)

        mock_qdrant_class.assert_called_once_with(
            url="http://localhost:6333",
            api_key="test-key",
            timeout=60.0,
        )

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_collection_exists(self, mock_qdrant_class):
        """Test checking if collection exists."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = True
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.collection_exists("test-collection")

        assert result is True
        mock_client.collection_exists.assert_called_once_with("test-collection")

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_collection_exists_not_found(self, mock_qdrant_class):
        """Test collection_exists when not found."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = False
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.collection_exists("test-collection")

        assert result is False

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_create_collection(self, mock_qdrant_class):
        """Test creating a collection."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = False
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        schema = IndexSchema(
            index_type="vector",
            vector_config=VectorConfig(
                dimensions=1024,
                distance_metric="cosine",
                sparse_enabled=True,
            ),
        )

        storage.create_collection("test-collection", schema, "test-version")

        mock_client.create_collection.assert_called_once()
        call_kwargs = mock_client.create_collection.call_args
        assert call_kwargs[1]["collection_name"] == "test-collection"

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_create_collection_already_exists(self, mock_qdrant_class):
        """Test creating collection that already exists raises error."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = True
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        schema = IndexSchema(
            index_type="vector",
            vector_config=VectorConfig(dimensions=1024),
        )

        with pytest.raises(ValueError, match="already exists"):
            storage.create_collection("test-collection", schema, "test-version")

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_create_collection_no_vector_config(self, mock_qdrant_class):
        """Test creating collection without vector config raises error."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = False
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        # IndexSchema validates that vector index requires vector_config in __post_init__
        with pytest.raises(ValueError, match="vector_config"):
            schema = IndexSchema(index_type="vector", vector_config=None)

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_delete_collection(self, mock_qdrant_class):
        """Test deleting a collection."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = True
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.delete_collection("test-collection")

        assert result is True
        mock_client.delete_collection.assert_called_once_with("test-collection")

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_delete_collection_not_exists(self, mock_qdrant_class):
        """Test deleting non-existent collection returns False."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = False
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.delete_collection("test-collection")

        assert result is False
        mock_client.delete_collection.assert_not_called()

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_list_collections(self, mock_qdrant_class):
        """Test listing collections."""
        mock_client = Mock()

        # Create proper mock collection objects with name attribute
        collection1 = Mock()
        collection1.name = "test-1"
        collection2 = Mock()
        collection2.name = "test-2"
        collection3 = Mock()
        collection3.name = "other"

        mock_collections = Mock()
        mock_collections.collections = [collection1, collection2, collection3]
        mock_client.get_collections.return_value = mock_collections
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        # Test without prefix
        result = storage.list_collections()
        assert sorted(result) == ["other", "test-1", "test-2"]

        # Test with prefix
        result = storage.list_collections(prefix="test")
        assert sorted(result) == ["test-1", "test-2"]

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_write_records(self, mock_qdrant_class):
        """Test writing records to a collection."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = True
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        records = [
            IndexRecord(
                id="record-1",
                file_version_id="file-v1",
                index_type="qa_vector",
                content={
                    "question_dense": [0.1] * 1024,
                    "answer_dense": [0.2] * 1024,
                },
                payload={"text": "test"},
            ),
        ]

        result = storage.write("test-collection", records)

        assert result.success is True
        assert result.records_written == 1
        mock_client.upsert.assert_called_once()

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_write_empty_records(self, mock_qdrant_class):
        """Test writing empty records."""
        mock_client = Mock()
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.write("test-collection", [])

        assert result.success is True
        assert result.records_written == 0
        mock_client.upsert.assert_not_called()

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_write_nonexistent_collection(self, mock_qdrant_class):
        """Test writing to non-existent collection fails."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = False
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        records = [
            IndexRecord(
                id="record-1",
                file_version_id="file-v1",
                index_type="qa_vector",
                content={},
                payload={},
            ),
        ]

        result = storage.write("test-collection", records)

        assert result.success is False
        assert "does not exist" in result.error_message

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_update_alias(self, mock_qdrant_class):
        """Test updating an alias."""
        mock_client = Mock()
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        storage.update_alias("test-alias", "test-collection")

        mock_client.update_collection_aliases.assert_called_once()

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_delete_alias(self, mock_qdrant_class):
        """Test deleting an alias."""
        mock_client = Mock()
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.delete_alias("test-alias")

        assert result is True
        mock_client.update_collection_aliases.assert_called_once()

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_get_alias_target(self, mock_qdrant_class):
        """Test getting alias target."""
        mock_client = Mock()
        mock_aliases = Mock()
        mock_aliases.aliases = [
            Mock(alias_name="test-alias", collection_name="test-collection"),
        ]
        mock_client.get_aliases.return_value = mock_aliases
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.get_alias_target("test-alias")

        assert result == "test-collection"

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_get_alias_target_not_found(self, mock_qdrant_class):
        """Test getting alias target when not found."""
        mock_client = Mock()
        mock_aliases = Mock()
        mock_aliases.aliases = []
        mock_client.get_aliases.return_value = mock_aliases
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.get_alias_target("nonexistent")

        assert result is None

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_list_aliases(self, mock_qdrant_class):
        """Test listing aliases."""
        mock_client = Mock()
        mock_aliases = Mock()
        mock_aliases.aliases = [
            Mock(alias_name="alias-1", collection_name="collection-1"),
            Mock(alias_name="alias-2", collection_name="collection-2"),
        ]
        mock_client.get_aliases.return_value = mock_aliases
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.list_aliases()

        assert result == {
            "alias-1": "collection-1",
            "alias-2": "collection-2",
        }

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_switch_alias(self, mock_qdrant_class):
        """Test switching an alias."""
        mock_client = Mock()
        mock_aliases = Mock()
        mock_aliases.aliases = [
            Mock(alias_name="test-alias", collection_name="old-collection"),
        ]
        mock_client.get_aliases.return_value = mock_aliases
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.switch_alias("test-alias", "old-collection", "new-collection")

        assert result is True
        mock_client.update_collection_aliases.assert_called_once()

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_switch_alias_wrong_source(self, mock_qdrant_class):
        """Test switching alias with wrong source collection."""
        mock_client = Mock()
        mock_aliases = Mock()
        mock_aliases.aliases = [
            Mock(alias_name="test-alias", collection_name="different-collection"),
        ]
        mock_client.get_aliases.return_value = mock_aliases
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        with pytest.raises(ValueError, match="points to"):
            storage.switch_alias("test-alias", "old-collection", "new-collection")

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_get_collection_info(self, mock_qdrant_class):
        """Test getting collection info."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = True
        mock_info = Mock()
        mock_info.points_count = 100
        mock_info.vectors_count = 200
        mock_info.status = Mock(value="green")
        mock_client.get_collection.return_value = mock_info
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.get_collection_info("test-collection")

        assert result is not None
        assert result.name == "test-collection"
        assert result.records_count == 100
        assert result.metadata["vectors_count"] == 200

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_get_collection_info_not_exists(self, mock_qdrant_class):
        """Test getting info for non-existent collection."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = False
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.get_collection_info("nonexistent")

        assert result is None

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_get_record_count(self, mock_qdrant_class):
        """Test getting record count."""
        mock_client = Mock()
        mock_client.collection_exists.return_value = True
        mock_info = Mock()
        mock_info.points_count = 42
        mock_info.vectors_count = 84
        mock_info.status = Mock(value="green")
        mock_client.get_collection.return_value = mock_info
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.get_record_count("test-collection")

        assert result == 42

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_delete_by_ids(self, mock_qdrant_class):
        """Test deleting records by IDs."""
        mock_client = Mock()
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.delete_by_ids("test-collection", ["id-1", "id-2"])

        assert result == 2
        mock_client.delete.assert_called_once()

    @patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient")
    def test_delete_by_ids_empty(self, mock_qdrant_class):
        """Test deleting with empty ID list."""
        mock_client = Mock()
        mock_qdrant_class.return_value = mock_client

        config = QdrantConfig(url="http://localhost:6333")
        storage = QdrantIndexStorage(config)

        result = storage.delete_by_ids("test-collection", [])

        assert result == 0
        mock_client.delete.assert_not_called()

    def test_get_distance(self):
        """Test distance metric conversion."""
        with patch("ai_knowledge_service.implementations.storage.qdrant_index_storage.QdrantClient"):
            config = QdrantConfig(url="http://localhost:6333")
            storage = QdrantIndexStorage(config)

            from qdrant_client.models import Distance

            assert storage._get_distance("cosine") == Distance.COSINE
            assert storage._get_distance("euclidean") == Distance.EUCLID
            assert storage._get_distance("dot") == Distance.DOT
            assert storage._get_distance("unknown") == Distance.COSINE  # Default
