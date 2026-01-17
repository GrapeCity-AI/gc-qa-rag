"""
SQLite Version Manager - SQLite-based version management.

This implementation stores knowledge base, version, and file version
data in a SQLite database.
"""

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

from ai_knowledge_service.abstractions.infrastructure.version_manager import (
    IVersionManager,
)
from ai_knowledge_service.abstractions.models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseVersion,
    VersionStatus,
    FileVersion,
    IndexStatus,
)


class SqliteVersionManager(IVersionManager):
    """
    SQLite-based version manager.

    Thread-safe implementation using thread-local connections.
    """

    def __init__(self, db_path: str | Path):
        self._db_path = str(db_path)
        self._local = threading.local()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "connection"):
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._local.connection = conn
        return self._local.connection

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Get a cursor with automatic commit/rollback."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base_versions (
                    id TEXT PRIMARY KEY,
                    knowledge_base_id TEXT NOT NULL,
                    version_tag TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    parent_version_id TEXT,
                    created_at TEXT NOT NULL,
                    published_at TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id),
                    UNIQUE (knowledge_base_id, version_tag)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kb_versions_kb_id
                ON knowledge_base_versions(knowledge_base_id)
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_versions (
                    id TEXT PRIMARY KEY,
                    raw_file_id TEXT NOT NULL,
                    knowledge_base_version_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    index_status TEXT NOT NULL DEFAULT 'pending',
                    indexed_at TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY (knowledge_base_version_id)
                        REFERENCES knowledge_base_versions(id),
                    UNIQUE (raw_file_id, knowledge_base_version_id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_versions_kb_version
                ON file_versions(knowledge_base_version_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_versions_raw_file
                ON file_versions(raw_file_id)
            """)

    # ============ Knowledge Base Management ============

    def create_knowledge_base(
        self,
        id: str,
        name: str,
        description: str = "",
    ) -> KnowledgeBase:
        """Create a new knowledge base."""
        now = datetime.now()
        kb = KnowledgeBase(
            id=id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )

        with self._cursor() as cursor:
            cursor.execute(
                "SELECT id FROM knowledge_bases WHERE id = ?",
                (id,)
            )
            if cursor.fetchone():
                raise ValueError(f"Knowledge base already exists: {id}")

            cursor.execute("""
                INSERT INTO knowledge_bases
                (id, name, description, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                kb.id,
                kb.name,
                kb.description,
                kb.created_at.isoformat(),
                kb.updated_at.isoformat(),
                json.dumps(kb.metadata),
            ))

        return kb

    def get_knowledge_base(self, id: str) -> Optional[KnowledgeBase]:
        """Get a knowledge base by ID."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM knowledge_bases WHERE id = ?",
                (id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_kb(row)

    def list_knowledge_bases(self) -> List[KnowledgeBase]:
        """List all knowledge bases."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM knowledge_bases ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            return [self._row_to_kb(row) for row in rows]

    def delete_knowledge_base(self, id: str) -> bool:
        """Delete a knowledge base."""
        with self._cursor() as cursor:
            cursor.execute("""
                DELETE FROM file_versions
                WHERE knowledge_base_version_id IN (
                    SELECT id FROM knowledge_base_versions
                    WHERE knowledge_base_id = ?
                )
            """, (id,))

            cursor.execute(
                "DELETE FROM knowledge_base_versions WHERE knowledge_base_id = ?",
                (id,)
            )

            cursor.execute(
                "DELETE FROM knowledge_bases WHERE id = ?",
                (id,)
            )

            return cursor.rowcount > 0

    # ============ Knowledge Base Version Management ============

    def create_version(
        self,
        knowledge_base_id: str,
        version_tag: str,
        parent_version_id: Optional[str] = None,
    ) -> KnowledgeBaseVersion:
        """Create a new version for a knowledge base."""
        kb = self.get_knowledge_base(knowledge_base_id)
        if kb is None:
            raise ValueError(f"Knowledge base not found: {knowledge_base_id}")

        existing = self.get_version_by_tag(knowledge_base_id, version_tag)
        if existing:
            raise ValueError(
                f"Version already exists: {knowledge_base_id}/{version_tag}"
            )

        version = KnowledgeBaseVersion(
            id=str(uuid.uuid4()),
            knowledge_base_id=knowledge_base_id,
            version_tag=version_tag,
            status=VersionStatus.DRAFT,
            parent_version_id=parent_version_id,
            created_at=datetime.now(),
        )

        with self._cursor() as cursor:
            cursor.execute("""
                INSERT INTO knowledge_base_versions
                (id, knowledge_base_id, version_tag, status, parent_version_id,
                 created_at, published_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version.id,
                version.knowledge_base_id,
                version.version_tag,
                version.status.value,
                version.parent_version_id,
                version.created_at.isoformat(),
                None,
                json.dumps(version.metadata),
            ))

        return version

    def get_version(self, version_id: str) -> Optional[KnowledgeBaseVersion]:
        """Get a version by ID."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM knowledge_base_versions WHERE id = ?",
                (version_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_version(row)

    def get_version_by_tag(
        self,
        knowledge_base_id: str,
        version_tag: str,
    ) -> Optional[KnowledgeBaseVersion]:
        """Get a version by knowledge base ID and tag."""
        with self._cursor() as cursor:
            cursor.execute("""
                SELECT * FROM knowledge_base_versions
                WHERE knowledge_base_id = ? AND version_tag = ?
            """, (knowledge_base_id, version_tag))
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_version(row)

    def get_latest_version(
        self,
        knowledge_base_id: str,
        status: Optional[VersionStatus] = None,
    ) -> Optional[KnowledgeBaseVersion]:
        """Get the latest version for a knowledge base."""
        with self._cursor() as cursor:
            if status:
                cursor.execute("""
                    SELECT * FROM knowledge_base_versions
                    WHERE knowledge_base_id = ? AND status = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (knowledge_base_id, status.value))
            else:
                cursor.execute("""
                    SELECT * FROM knowledge_base_versions
                    WHERE knowledge_base_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (knowledge_base_id,))

            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_version(row)

    def list_versions(
        self,
        knowledge_base_id: str,
        status: Optional[VersionStatus] = None,
    ) -> List[KnowledgeBaseVersion]:
        """List versions for a knowledge base."""
        with self._cursor() as cursor:
            if status:
                cursor.execute("""
                    SELECT * FROM knowledge_base_versions
                    WHERE knowledge_base_id = ? AND status = ?
                    ORDER BY created_at DESC
                """, (knowledge_base_id, status.value))
            else:
                cursor.execute("""
                    SELECT * FROM knowledge_base_versions
                    WHERE knowledge_base_id = ?
                    ORDER BY created_at DESC
                """, (knowledge_base_id,))

            rows = cursor.fetchall()
            return [self._row_to_version(row) for row in rows]

    def update_version_status(
        self,
        version_id: str,
        status: VersionStatus,
    ) -> None:
        """Update the status of a version."""
        with self._cursor() as cursor:
            published_at = None
            if status == VersionStatus.PUBLISHED:
                published_at = datetime.now().isoformat()

            cursor.execute("""
                UPDATE knowledge_base_versions
                SET status = ?, published_at = COALESCE(?, published_at)
                WHERE id = ?
            """, (status.value, published_at, version_id))

            if cursor.rowcount == 0:
                raise ValueError(f"Version not found: {version_id}")

    def delete_version(self, version_id: str) -> bool:
        """Delete a version."""
        with self._cursor() as cursor:
            cursor.execute(
                "DELETE FROM file_versions WHERE knowledge_base_version_id = ?",
                (version_id,)
            )

            cursor.execute(
                "DELETE FROM knowledge_base_versions WHERE id = ?",
                (version_id,)
            )

            return cursor.rowcount > 0

    # ============ File Version Management ============

    def create_file_version(
        self,
        raw_file_id: str,
        knowledge_base_version_id: str,
        content_hash: str,
    ) -> FileVersion:
        """Create a file version."""
        file_version = FileVersion(
            id=str(uuid.uuid4()),
            raw_file_id=raw_file_id,
            knowledge_base_version_id=knowledge_base_version_id,
            content_hash=content_hash,
            index_status=IndexStatus.PENDING,
            created_at=datetime.now(),
        )

        with self._cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO file_versions
                (id, raw_file_id, knowledge_base_version_id, content_hash,
                 index_status, indexed_at, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_version.id,
                file_version.raw_file_id,
                file_version.knowledge_base_version_id,
                file_version.content_hash,
                file_version.index_status.value,
                None,
                file_version.created_at.isoformat(),
                json.dumps(file_version.metadata),
            ))

        return file_version

    def get_file_version(self, file_version_id: str) -> Optional[FileVersion]:
        """Get a file version by ID."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM file_versions WHERE id = ?",
                (file_version_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_file_version(row)

    def get_file_versions(
        self,
        knowledge_base_version_id: str,
        index_status: Optional[IndexStatus] = None,
    ) -> List[FileVersion]:
        """Get all file versions for a knowledge base version."""
        with self._cursor() as cursor:
            if index_status:
                cursor.execute("""
                    SELECT * FROM file_versions
                    WHERE knowledge_base_version_id = ? AND index_status = ?
                    ORDER BY created_at
                """, (knowledge_base_version_id, index_status.value))
            else:
                cursor.execute("""
                    SELECT * FROM file_versions
                    WHERE knowledge_base_version_id = ?
                    ORDER BY created_at
                """, (knowledge_base_version_id,))

            rows = cursor.fetchall()
            return [self._row_to_file_version(row) for row in rows]

    def get_file_version_by_raw_file(
        self,
        raw_file_id: str,
        knowledge_base_version_id: str,
    ) -> Optional[FileVersion]:
        """Get a file version for a specific raw file and KB version."""
        with self._cursor() as cursor:
            cursor.execute("""
                SELECT * FROM file_versions
                WHERE raw_file_id = ? AND knowledge_base_version_id = ?
            """, (raw_file_id, knowledge_base_version_id))
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_file_version(row)

    def get_changed_files(
        self,
        knowledge_base_version_id: str,
        base_version_id: str,
    ) -> List[FileVersion]:
        """Get file versions that have changed relative to a base version."""
        with self._cursor() as cursor:
            cursor.execute("""
                SELECT fv.*
                FROM file_versions fv
                WHERE fv.knowledge_base_version_id = ?
                AND (
                    -- New files (not in base version)
                    NOT EXISTS (
                        SELECT 1 FROM file_versions base
                        WHERE base.knowledge_base_version_id = ?
                        AND base.raw_file_id = fv.raw_file_id
                    )
                    OR
                    -- Modified files (different content hash)
                    EXISTS (
                        SELECT 1 FROM file_versions base
                        WHERE base.knowledge_base_version_id = ?
                        AND base.raw_file_id = fv.raw_file_id
                        AND base.content_hash != fv.content_hash
                    )
                )
            """, (knowledge_base_version_id, base_version_id, base_version_id))

            rows = cursor.fetchall()
            return [self._row_to_file_version(row) for row in rows]

    def update_file_index_status(
        self,
        file_version_id: str,
        status: IndexStatus,
    ) -> None:
        """Update the index status of a file version."""
        with self._cursor() as cursor:
            indexed_at = None
            if status == IndexStatus.INDEXED:
                indexed_at = datetime.now().isoformat()

            cursor.execute("""
                UPDATE file_versions
                SET index_status = ?, indexed_at = COALESCE(?, indexed_at)
                WHERE id = ?
            """, (status.value, indexed_at, file_version_id))

    def count_file_versions(
        self,
        knowledge_base_version_id: str,
        index_status: Optional[IndexStatus] = None,
    ) -> int:
        """Count file versions."""
        with self._cursor() as cursor:
            if index_status:
                cursor.execute("""
                    SELECT COUNT(*) FROM file_versions
                    WHERE knowledge_base_version_id = ? AND index_status = ?
                """, (knowledge_base_version_id, index_status.value))
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM file_versions
                    WHERE knowledge_base_version_id = ?
                """, (knowledge_base_version_id,))

            return cursor.fetchone()[0]

    # ============ Helper Methods ============

    def _row_to_kb(self, row: sqlite3.Row) -> KnowledgeBase:
        """Convert a database row to a KnowledgeBase object."""
        return KnowledgeBase(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            metadata=json.loads(row["metadata"]),
        )

    def _row_to_version(self, row: sqlite3.Row) -> KnowledgeBaseVersion:
        """Convert a database row to a KnowledgeBaseVersion object."""
        published_at = None
        if row["published_at"]:
            published_at = datetime.fromisoformat(row["published_at"])

        return KnowledgeBaseVersion(
            id=row["id"],
            knowledge_base_id=row["knowledge_base_id"],
            version_tag=row["version_tag"],
            status=VersionStatus(row["status"]),
            parent_version_id=row["parent_version_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            published_at=published_at,
            metadata=json.loads(row["metadata"]),
        )

    def _row_to_file_version(self, row: sqlite3.Row) -> FileVersion:
        """Convert a database row to a FileVersion object."""
        indexed_at = None
        if row["indexed_at"]:
            indexed_at = datetime.fromisoformat(row["indexed_at"])

        return FileVersion(
            id=row["id"],
            raw_file_id=row["raw_file_id"],
            knowledge_base_version_id=row["knowledge_base_version_id"],
            content_hash=row["content_hash"],
            index_status=IndexStatus(row["index_status"]),
            indexed_at=indexed_at,
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=json.loads(row["metadata"]),
        )
