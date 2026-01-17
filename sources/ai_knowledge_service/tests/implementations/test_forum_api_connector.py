"""
Tests for ForumApiConnector.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock

from ai_knowledge_service.abstractions.pipelines.source import SourceConfig
from ai_knowledge_service.implementations.connectors import ForumApiConnector
from ai_knowledge_service.implementations.connectors.forum_api_connector import (
    ForumProductType,
    ForumSectionType,
)


@pytest.fixture
def connector():
    """Create a ForumApiConnector instance."""
    return ForumApiConnector()


@pytest.fixture
def source_config():
    """Create a SourceConfig for testing."""
    return SourceConfig(
        connector_type="forum_api",
        connection_params={
            "base_url_page": "https://api.forum.example.com/threads",
            "base_url_thread": "https://api.forum.example.com/thread",
            "token": "test-token",
            "product": "Forguncy",
            "section": "QA",
        },
        fetch_options={
            "request_delay": 0,  # No delay for tests
            "max_retries": 1,
            "page_size": 10,
        },
    )


@pytest.fixture
def sample_threads_response():
    """Sample API response for thread listing."""
    return {
        "tidList": [
            {
                "tid": "12345",
                "title": "How to solve this problem?",
                "postDate": 1609459200,
            },
            {
                "tid": "12346",
                "title": "Another question",
                "postDate": 1609459300,
            },
        ],
        "nextLink": None,  # No more pages
    }


@pytest.fixture
def sample_thread_content():
    """Sample API response for thread content."""
    return {
        "tid": "12345",
        "title": "How to solve this problem?",
        "postDate": 1609459200,
        "content": {
            "title": "How to solve this problem?",
            "url": "https://forum.example.com/thread/12345",
            "forumName": "Technical Support",
            "threadTag": "Question",
            "product": "Forguncy",
            "authorContent": "<p>I have a problem.</p>",
            "replies": [
                {"author": "Expert", "content": "<p>Try this...</p>"},
            ],
        },
    }


class TestForumApiConnector:
    """Tests for ForumApiConnector."""

    def test_source_type(self, connector):
        """Test source type identifier."""
        assert connector.source_type == "forum_api"

    def test_supports_incremental(self, connector):
        """Test that incremental is not supported."""
        assert connector.supports_incremental is False

    def test_configure(self, connector, source_config):
        """Test configuration."""
        connector.configure(source_config)

        assert connector._base_url_page == "https://api.forum.example.com/threads"
        assert connector._base_url_thread == "https://api.forum.example.com/thread"
        assert connector._product == "Forguncy"
        assert connector._section == "QA"

    def test_configure_requires_base_urls(self, connector):
        """Test that configuration requires base_url_page and base_url_thread."""
        config = SourceConfig(
            connector_type="forum_api",
            connection_params={
                "token": "test-token",
                "product": "Forguncy",
                "section": "QA",
            },
            fetch_options={},
        )

        with pytest.raises(ValueError, match="base_url_page.*base_url_thread.*token"):
            connector.configure(config)

    def test_configure_requires_product_and_section(self, connector):
        """Test that configuration requires product and section."""
        config = SourceConfig(
            connector_type="forum_api",
            connection_params={
                "base_url_page": "https://api.example.com/threads",
                "base_url_thread": "https://api.example.com/thread",
                "token": "test-token",
            },
            fetch_options={},
        )

        with pytest.raises(ValueError, match="product.*section"):
            connector.configure(config)

    def test_configure_validates_connector_type(self, connector):
        """Test that configuration validates connector type."""
        config = SourceConfig(
            connector_type="wrong_type",
            connection_params={
                "base_url_page": "https://api.example.com/threads",
                "base_url_thread": "https://api.example.com/thread",
                "token": "test-token",
                "product": "Forguncy",
                "section": "QA",
            },
            fetch_options={},
        )

        with pytest.raises(ValueError, match="Invalid connector type"):
            connector.configure(config)

    @patch("requests.Session")
    def test_validate_connection_success(
        self, mock_session_class, connector, source_config, sample_threads_response
    ):
        """Test successful connection validation."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.json.return_value = sample_threads_response
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        connector.configure(source_config)
        result = connector.validate_connection()

        assert result.is_connected is True
        assert "Forguncy" in result.message or "QA" in result.message

    @patch("requests.Session")
    def test_validate_connection_failure(
        self, mock_session_class, connector, source_config
    ):
        """Test connection validation failure."""
        import requests

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = requests.RequestException("Connection failed")

        connector.configure(source_config)
        result = connector.validate_connection()

        assert result.is_connected is False
        assert "Connection failed" in result.message or "error" in result.message.lower()

    @patch("requests.Session")
    def test_fetch_yields_records(
        self,
        mock_session_class,
        connector,
        source_config,
        sample_threads_response,
        sample_thread_content,
    ):
        """Test that fetch yields SourceRecords."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.raise_for_status = MagicMock()

            if "thread" in url and "tid=" in url:
                # Thread content endpoint
                response.json.return_value = sample_thread_content
            else:
                # Thread listing endpoint
                response.json.return_value = sample_threads_response

            return response

        mock_session.get.side_effect = mock_get

        connector.configure(source_config)
        records = list(connector.fetch())

        # Should yield records for each thread
        assert len(records) >= 1
        for record in records:
            assert record.content_type == "application/json"
            assert record.metadata["product"] == "Forguncy"
            assert record.metadata["section"] == "QA"
            assert record.metadata["source_type"] == "forum_api"

    @patch("requests.Session")
    def test_fetch_handles_api_error(
        self,
        mock_session_class,
        connector,
        source_config,
        sample_threads_response,
    ):
        """Test that fetch handles API errors gracefully."""
        import requests

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        def mock_get(url, **kwargs):
            response = MagicMock()
            response.raise_for_status = MagicMock()

            if "thread" in url and "tid=" in url:
                # Fail on content fetch
                raise requests.RequestException("API error")
            else:
                # Thread listing endpoint
                response.json.return_value = sample_threads_response
                return response

        mock_session.get.side_effect = mock_get

        connector.configure(source_config)
        records = list(connector.fetch())

        # Should continue despite errors
        assert isinstance(records, list)

    def test_get_record_count_before_validation(self, connector, source_config):
        """Test get_record_count before validation returns None or 0."""
        connector.configure(source_config)
        count = connector.get_record_count()
        assert count is None or count == 0

    @patch("requests.Session")
    def test_get_record_count_after_validation(
        self, mock_session_class, connector, source_config, sample_threads_response
    ):
        """Test get_record_count after validation returns None (unknown without full scan)."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.json.return_value = sample_threads_response
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        connector.configure(source_config)
        connector.validate_connection()

        # Forum API connector doesn't know total count without full scan
        count = connector.get_record_count()
        assert count is None


class TestForumProductType:
    """Tests for ForumProductType enum."""

    def test_forguncy_value(self):
        """Test Forguncy enum value."""
        assert ForumProductType.FORGUNCY.value == "Forguncy"

    def test_wyn_value(self):
        """Test Wyn enum value."""
        assert ForumProductType.WYN.value == "Wyn"

    def test_spreadjs_gcexcel_value(self):
        """Test SpreadJSGcExcel enum value."""
        assert ForumProductType.SPREADJS_GCEXCEL.value == "SpreadJSGcExcel"


class TestForumSectionType:
    """Tests for ForumSectionType enum."""

    def test_qa_value(self):
        """Test QA enum value."""
        assert ForumSectionType.QA.value == "QA"

    def test_tutorial_value(self):
        """Test Tutorial enum value."""
        assert ForumSectionType.TUTORIAL.value == "Tutorial"
