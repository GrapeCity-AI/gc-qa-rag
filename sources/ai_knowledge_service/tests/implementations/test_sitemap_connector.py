"""
Tests for SitemapConnector.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

from ai_knowledge_service.abstractions.pipelines.source import SourceConfig
from ai_knowledge_service.implementations.connectors import SitemapConnector


@pytest.fixture
def connector():
    """Create a SitemapConnector instance."""
    return SitemapConnector()


@pytest.fixture
def source_config():
    """Create a SourceConfig for testing."""
    return SourceConfig(
        connector_type="sitemap",
        connection_params={
            "sitemap_url": "https://example.com/sitemap.xml",
            "product_name": "TestProduct",
        },
        fetch_options={
            "request_delay": 0,  # No delay for tests
            "max_retries": 1,
        },
    )


@pytest.fixture
def sample_sitemap_xml():
    """Sample sitemap XML content."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/docs/page1</loc>
        </url>
        <url>
            <loc>https://example.com/docs/page2</loc>
        </url>
        <url>
            <loc>https://example.com/docs/page3</loc>
        </url>
    </urlset>
    """


class TestSitemapConnector:
    """Tests for SitemapConnector."""

    def test_source_type(self, connector):
        """Test source type identifier."""
        assert connector.source_type == "sitemap"

    def test_supports_incremental(self, connector):
        """Test that incremental is not supported."""
        assert connector.supports_incremental is False

    def test_configure(self, connector, source_config):
        """Test configuration."""
        connector.configure(source_config)

        assert connector._sitemap_url == "https://example.com/sitemap.xml"
        assert connector._product_name == "TestProduct"

    def test_configure_requires_sitemap_url(self, connector):
        """Test that configuration requires sitemap_url."""
        config = SourceConfig(
            connector_type="sitemap",
            connection_params={},
            fetch_options={},
        )

        with pytest.raises(ValueError, match="sitemap_url"):
            connector.configure(config)

    def test_configure_validates_connector_type(self, connector):
        """Test that configuration validates connector type."""
        config = SourceConfig(
            connector_type="wrong_type",
            connection_params={"sitemap_url": "https://example.com"},
            fetch_options={},
        )

        with pytest.raises(ValueError, match="Invalid connector type"):
            connector.configure(config)

    @patch("requests.Session")
    def test_validate_connection_success(
        self, mock_session_class, connector, source_config, sample_sitemap_xml
    ):
        """Test successful connection validation."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.content = sample_sitemap_xml.encode("utf-8")
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        connector.configure(source_config)
        result = connector.validate_connection()

        assert result.is_connected is True
        assert "3 URLs" in result.message
        assert len(connector._urls) == 3

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
        assert "Connection failed" in result.message

    @patch("requests.Session")
    def test_fetch_yields_records(
        self, mock_session_class, connector, source_config, sample_sitemap_xml
    ):
        """Test that fetch yields SourceRecords."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # First call returns sitemap, subsequent calls return page content
        def mock_get(url, **kwargs):
            response = MagicMock()
            response.raise_for_status = MagicMock()
            if "sitemap.xml" in url:
                response.content = sample_sitemap_xml.encode("utf-8")
            else:
                response.text = "<html><body>Page content</body></html>"
                response.apparent_encoding = "utf-8"
            return response

        mock_session.get.side_effect = mock_get

        connector.configure(source_config)
        records = list(connector.fetch())

        assert len(records) == 3
        for record in records:
            assert record.content_type == "text/html"
            assert record.metadata["product"] == "TestProduct"
            assert record.metadata["source_type"] == "sitemap"

    @patch("requests.Session")
    def test_fetch_handles_page_error(
        self, mock_session_class, connector, source_config, sample_sitemap_xml
    ):
        """Test that fetch handles individual page errors gracefully."""
        import requests

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        call_count = [0]

        def mock_get(url, **kwargs):
            call_count[0] += 1
            response = MagicMock()
            response.raise_for_status = MagicMock()

            if "sitemap.xml" in url:
                response.content = sample_sitemap_xml.encode("utf-8")
            elif "page2" in url:
                # Fail on page2
                raise requests.RequestException("Page error")
            else:
                response.text = "<html><body>Content</body></html>"
                response.apparent_encoding = "utf-8"

            return response

        mock_session.get.side_effect = mock_get

        connector.configure(source_config)
        records = list(connector.fetch())

        # Should still get 2 records (page1 and page3)
        assert len(records) == 2

    def test_get_record_count_after_validation(
        self, connector, source_config, sample_sitemap_xml
    ):
        """Test get_record_count after validation."""
        with patch("requests.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            mock_response = MagicMock()
            mock_response.content = sample_sitemap_xml.encode("utf-8")
            mock_response.raise_for_status = MagicMock()
            mock_session.get.return_value = mock_response

            connector.configure(source_config)
            connector.validate_connection()

            assert connector.get_record_count() == 3

    def test_find_common_prefix(self, connector):
        """Test common prefix finding."""
        urls = [
            "https://example.com/docs/page1",
            "https://example.com/docs/page2",
            "https://example.com/docs/guide/intro",
        ]

        prefix = connector._find_common_prefix(urls)
        assert prefix == "https://example.com/docs/"

    def test_find_common_prefix_empty(self, connector):
        """Test common prefix with empty list."""
        assert connector._find_common_prefix([]) == ""
