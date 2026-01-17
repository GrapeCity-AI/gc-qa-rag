"""
SQLite Metadata Store - SQLite-based metadata storage.

This implementation stores file metadata in a SQLite database.
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

from ai_knowledge_service.abstractions.models.raw_file import (
    RawFile,
    LifecycleStatus,
)
from ai_knowledge_service.abstractions.storage.raw_file_storage import (
    IRawFileMetadataStore,
    QueryCriteria,
)


class SqliteMetadataStore(IRawFileMetadataStore):
    """
    SQLite-based metadata storage.

    Thread-safe implementation using connection pooling.
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
                CREATE TABLE IF NOT EXISTS raw_files (
                    id TEXT PRIMARY KEY,
                    knowledge_base_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_uri TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    lifecycle_status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_files_kb_id
                ON raw_files(knowledge_base_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_files_hash
                ON raw_files(knowledge_base_id, content_hash)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_files_status
                ON raw_files(knowledge_base_id, lifecycle_status)
            """)

    def save(self, raw_file: RawFile) -> None:
        """Save a raw file metadata record."""
        with self._cursor() as cursor:
            cursor.execute("""
                INSERT OR REPLACE INTO raw_files
                (id, knowledge_base_id, source_type, source_uri, original_name,
                 content_hash, storage_path, mime_type, size_bytes, metadata,
                 lifecycle_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                raw_file.id,
                raw_file.knowledge_base_id,
                raw_file.source_type,
                raw_file.source_uri,
                raw_file.original_name,
                raw_file.content_hash,
                raw_file.storage_path,
                raw_file.mime_type,
                raw_file.size_bytes,
                json.dumps(raw_file.metadata),
                raw_file.lifecycle_status.value,
                raw_file.created_at.isoformat(),
                raw_file.updated_at.isoformat(),
            ))

    def get(self, file_id: str) -> Optional[RawFile]:
        """Get a raw file by ID."""
        with self._cursor() as cursor:
            cursor.execute(
                "SELECT * FROM raw_files WHERE id = ?",
                (file_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_raw_file(row)

    def query(self, criteria: QueryCriteria) -> List[RawFile]:
        """Query raw files."""
        conditions = []
        params = []

        if criteria.knowledge_base_id:
            conditions.append("knowledge_base_id = ?")
            params.append(criteria.knowledge_base_id)

        if criteria.source_type:
            conditions.append("source_type = ?")
            params.append(criteria.source_type)

        if criteria.lifecycle_status:
            conditions.append("lifecycle_status = ?")
            params.append(criteria.lifecycle_status.value)

        if criteria.content_hash:
            conditions.append("content_hash = ?")
            params.append(criteria.content_hash)

        if criteria.created_after:
            conditions.append("created_at > ?")
            params.append(criteria.created_after.isoformat())

        if criteria.created_before:
            conditions.append("created_at < ?")
            params.append(criteria.created_before.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        order_direction = "DESC" if criteria.order_desc else "ASC"
        order_clause = f"ORDER BY {criteria.order_by} {order_direction}"

        query = f"""
            SELECT * FROM raw_files
            WHERE {where_clause}
            {order_clause}
            LIMIT ? OFFSET ?
        """
        params.extend([criteria.limit, criteria.offset])

        with self._cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_raw_file(row) for row in rows]

    def update(self, raw_file: RawFile) -> None:
        """Update a raw file record."""
        raw_file.updated_at = datetime.now()
        self.save(raw_file)

    def count(self, criteria: QueryCriteria) -> int:
        """Count raw files matching criteria."""
        conditions = []
        params = []

        if criteria.knowledge_base_id:
            conditions.append("knowledge_base_id = ?")
            params.append(criteria.knowledge_base_id)

        if criteria.lifecycle_status:
            conditions.append("lifecycle_status = ?")
            params.append(criteria.lifecycle_status.value)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"SELECT COUNT(*) FROM raw_files WHERE {where_clause}"

        with self._cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def exists_by_hash(
        self,
        knowledge_base_id: str,
        content_hash: str,
    ) -> Optional[str]:
        """Check if a file with the given hash exists."""
        with self._cursor() as cursor:
            cursor.execute("""
                SELECT id FROM raw_files
                WHERE knowledge_base_id = ? AND content_hash = ?
                AND lifecycle_status != 'deleted'
                LIMIT 1
            """, (knowledge_base_id, content_hash))

            row = cursor.fetchone()
            return row[0] if row else None

    def _row_to_raw_file(self, row: sqlite3.Row) -> RawFile:
        """Convert a database row to a RawFile object."""
        return RawFile(
            id=row["id"],
            knowledge_base_id=row["knowledge_base_id"],
            source_type=row["source_type"],
            source_uri=row["source_uri"],
            original_name=row["original_name"],
            content_hash=row["content_hash"],
            storage_path=row["storage_path"],
            mime_type=row["mime_type"],
            size_bytes=row["size_bytes"],
            metadata=json.loads(row["metadata"]),
            lifecycle_status=LifecycleStatus(row["lifecycle_status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
