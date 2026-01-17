"""
Pytest configuration and shared fixtures for AI Knowledge Service tests.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Create a temporary database path."""
    return temp_dir / "test.db"


@pytest.fixture
def temp_storage_path(temp_dir: Path) -> Path:
    """Create a temporary storage path."""
    storage_path = temp_dir / "storage"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path
