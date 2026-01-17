"""
Tests for Filesystem Connector.
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ai_knowledge_service.abstractions.pipelines.source import (
    ConnectionStatus,
    SourceConfig,
)
from ai_knowledge_service.implementations.connectors.filesystem_connector import (
    FilesystemConnector,
)


class TestFilesystemConnector:
    """Tests for FilesystemConnector."""

    def test_source_type(self):
        """Test connector source type."""
        connector = FilesystemConnector()
        assert connector.source_type == "filesystem"

    def test_configure_valid(self):
        """Test configuring with valid config."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
                fetch_options={"extensions": [".txt", ".md"]},
            )

            connector.configure(config)
            # Should not raise

    def test_configure_missing_path(self):
        """Test configuring without path raises error."""
        connector = FilesystemConnector()

        config = SourceConfig(
            connector_type="filesystem",
            connection_params={},
        )

        with pytest.raises(ValueError, match="path"):
            connector.configure(config)

    def test_configure_wrong_connector_type(self):
        """Test configuring with wrong connector type raises error."""
        connector = FilesystemConnector()

        config = SourceConfig(
            connector_type="sitemap",
            connection_params={"path": "/data"},
        )

        with pytest.raises(ValueError, match="Invalid connector type"):
            connector.configure(config)

    def test_validate_connection_not_configured(self):
        """Test validation without configuration."""
        connector = FilesystemConnector()

        result = connector.validate_connection()

        assert result.status == ConnectionStatus.ERROR
        assert "not configured" in result.message.lower()

    def test_validate_connection_path_exists(self):
        """Test validation with existing path."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
            )
            connector.configure(config)

            result = connector.validate_connection()

            assert result.is_connected
            assert result.status == ConnectionStatus.CONNECTED

    def test_validate_connection_path_not_exists(self):
        """Test validation with non-existent path."""
        connector = FilesystemConnector()

        config = SourceConfig(
            connector_type="filesystem",
            connection_params={"path": "/non/existent/path"},
        )
        connector.configure(config)

        result = connector.validate_connection()

        assert not result.is_connected
        assert result.status == ConnectionStatus.ERROR

    def test_fetch_empty_directory(self):
        """Test fetching from empty directory."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
            )
            connector.configure(config)

            records = list(connector.fetch())

            assert len(records) == 0

    def test_fetch_with_files(self):
        """Test fetching files."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "test1.txt").write_text("content 1")
            Path(tmpdir, "test2.txt").write_text("content 2")

            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
            )
            connector.configure(config)

            records = list(connector.fetch())

            assert len(records) == 2
            names = {r.metadata["original_name"] for r in records}
            assert names == {"test1.txt", "test2.txt"}

    def test_fetch_with_extension_filter(self):
        """Test fetching with extension filter."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "test.txt").write_text("content")
            Path(tmpdir, "test.md").write_text("markdown")
            Path(tmpdir, "test.py").write_text("python")

            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
                fetch_options={"extensions": [".txt", ".md"]},
            )
            connector.configure(config)

            records = list(connector.fetch())

            assert len(records) == 2
            names = {r.metadata["original_name"] for r in records}
            assert names == {"test.txt", "test.md"}

    def test_fetch_recursive(self):
        """Test recursive directory scanning."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(tmpdir, "test1.txt").write_text("content 1")
            Path(subdir, "test2.txt").write_text("content 2")

            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir, "recursive": True},
            )
            connector.configure(config)

            records = list(connector.fetch())

            assert len(records) == 2

    def test_fetch_non_recursive(self):
        """Test non-recursive directory scanning."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            subdir = Path(tmpdir, "subdir")
            subdir.mkdir()
            Path(tmpdir, "test1.txt").write_text("content 1")
            Path(subdir, "test2.txt").write_text("content 2")

            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir, "recursive": False},
            )
            connector.configure(config)

            records = list(connector.fetch())

            assert len(records) == 1
            assert records[0].metadata["original_name"] == "test1.txt"

    def test_fetch_incremental(self):
        """Test incremental fetching by modification time."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir, "test.txt")
            test_file.write_text("content")

            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
            )
            connector.configure(config)

            # Fetch with old timestamp should return file
            old_time = datetime.now() - timedelta(days=1)
            records = list(connector.fetch_incremental(old_time))
            assert len(records) == 1

            # Fetch with future timestamp should return nothing
            future_time = datetime.now() + timedelta(days=1)
            records = list(connector.fetch_incremental(future_time))
            assert len(records) == 0

    def test_supports_incremental(self):
        """Test incremental support flag."""
        connector = FilesystemConnector()
        assert connector.supports_incremental is True

    def test_source_record_content(self):
        """Test that source records contain correct content."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text("hello world")

            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
            )
            connector.configure(config)

            records = list(connector.fetch())

            assert len(records) == 1
            assert records[0].content_str == "hello world"
            assert records[0].content_type == "text/plain"

    def test_hidden_files_excluded(self):
        """Test that hidden files are excluded."""
        connector = FilesystemConnector()

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "visible.txt").write_text("visible")
            Path(tmpdir, ".hidden.txt").write_text("hidden")

            config = SourceConfig(
                connector_type="filesystem",
                connection_params={"path": tmpdir},
            )
            connector.configure(config)

            records = list(connector.fetch())

            assert len(records) == 1
            assert records[0].metadata["original_name"] == "visible.txt"
