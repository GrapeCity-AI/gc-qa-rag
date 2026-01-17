"""
Filesystem Content Store - File system-based content storage.

This implementation stores file content on the local filesystem
with a structured directory layout.
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

from ai_knowledge_service.abstractions.storage.raw_file_storage import (
    IRawFileContentStore,
)


class FilesystemContentStore(IRawFileContentStore):
    """
    Filesystem-based content storage.

    Files are stored in a directory structure:
    base_path/
      {knowledge_base_id}/
        {file_id_prefix}/
          {file_id}
    """

    def __init__(self, base_path: str | Path):
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        file_id: str,
        content: bytes,
        knowledge_base_id: str,
    ) -> str:
        """Write file content."""
        storage_path = self._build_path(knowledge_base_id, file_id)
        full_path = self._base_path / storage_path

        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(content)

        return storage_path

    def read(self, storage_path: str) -> bytes:
        """Read file content."""
        full_path = self._base_path / storage_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")

        with open(full_path, "rb") as f:
            return f.read()

    def delete(self, storage_path: str) -> bool:
        """Delete file content."""
        full_path = self._base_path / storage_path

        if not full_path.exists():
            return False

        try:
            full_path.unlink()
            return True
        except OSError:
            return False

    def exists(self, storage_path: str) -> bool:
        """Check if a file exists."""
        full_path = self._base_path / storage_path
        return full_path.exists()

    def get_size(self, storage_path: str) -> int:
        """Get the size of a file."""
        full_path = self._base_path / storage_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")

        return full_path.stat().st_size

    def _build_path(self, knowledge_base_id: str, file_id: str) -> str:
        """Build storage path for a file."""
        prefix = file_id[:2] if len(file_id) >= 2 else "00"
        return f"{knowledge_base_id}/{prefix}/{file_id}"

    @staticmethod
    def compute_hash(content: bytes) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()
