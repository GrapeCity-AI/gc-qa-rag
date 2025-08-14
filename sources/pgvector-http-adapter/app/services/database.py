"""
Database service for PostgreSQL + pgvector operations
"""

import asyncio
import asyncpg
import json
import numpy as np
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from contextlib import asynccontextmanager

from app.core.config import settings
from app.utils.payload import parse_payload

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for PostgreSQL operations"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    async def initialize(self):
        """Initialize database connection pool"""
        if self._initialized:
            return

        try:
            self.pool = await asyncpg.create_pool(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=settings.postgres_database,
                min_size=settings.postgres_min_connections,
                max_size=settings.postgres_max_connections,
                command_timeout=60
            )

            # Ensure pgvector extension is loaded
            async with self.pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

                # Load plpgsql_bm25 functions
                await self._load_bm25_functions(conn)

            self._initialized = True
            logger.info("Database connection pool initialized")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def _load_bm25_functions(self, conn):
        """Load plpgsql_bm25 functions from SQL file"""
        try:
            # Get the path to the SQL file - go up to /app directory
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sql_file_path = os.path.join(app_dir, 'scripts', 'plpgsql_bm25.sql')

            if os.path.exists(sql_file_path):
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                await conn.execute(sql_content)
                logger.info("plpgsql_bm25 functions loaded successfully")
            else:
                logger.warning(f"plpgsql_bm25.sql not found at {sql_file_path}, using fallback FTS")

        except Exception as e:
            logger.warning(f"Failed to load plpgsql_bm25 functions: {e}, using fallback FTS")

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self._initialized:
            await self.initialize()

        async with self.pool.acquire() as conn:
            yield conn

    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """Create a collection (table) for storing vectors"""
        try:
            # Normalize collection name to lowercase for PostgreSQL compatibility
            normalized_name = collection_name.lower()

            async with self.get_connection() as conn:
                # Create table with vector column
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {normalized_name} (
                        id TEXT PRIMARY KEY,
                        question_dense VECTOR({vector_size}),
                        answer_dense VECTOR({vector_size}),
                        question_sparse JSONB,
                        answer_sparse JSONB,
                        payload JSONB DEFAULT '{{}}',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                                # Create vector indexes for both dense vectors (compatible with original Qdrant)
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {normalized_name}_question_dense_idx
                    ON {normalized_name} USING hnsw (question_dense vector_cosine_ops);
                """)

                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {normalized_name}_answer_dense_idx
                    ON {normalized_name} USING hnsw (answer_dense vector_cosine_ops);
                """)

                # Create JSONB indexes for sparse vectors and payload
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {normalized_name}_question_sparse_idx
                    ON {normalized_name} USING gin (question_sparse);
                """)

                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {normalized_name}_answer_sparse_idx
                    ON {normalized_name} USING gin (answer_sparse);
                """)

                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {normalized_name}_payload_idx
                    ON {normalized_name} USING gin (payload);
                """)

                logger.info(f"Collection {collection_name} created successfully as {normalized_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        try:
            # Resolve alias to actual collection name
            normalized_name = await self.resolve_collection_name(collection_name)

            async with self.get_connection() as conn:
                result = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = $1
                    );
                """, normalized_name)
                return bool(result)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False

    async def list_collections(self) -> List[str]:
        """List all vector collections (tables with vector columns)"""
        try:
            async with self.get_connection() as conn:
                # Only return tables that have vector columns
                query = """
                    SELECT DISTINCT t.table_name
                    FROM information_schema.tables t
                    INNER JOIN information_schema.columns c
                        ON t.table_name = c.table_name
                        AND t.table_schema = c.table_schema
                    WHERE t.table_schema = 'public'
                    AND t.table_type = 'BASE TABLE'
                    AND c.data_type = 'USER-DEFINED'
                    AND c.udt_name = 'vector'
                    AND t.table_name NOT LIKE '%_bm25i_%'
                    ORDER BY t.table_name;
                """
                rows = await conn.fetch(query)
                return [row["table_name"] for row in rows]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information"""
        try:
            # Resolve alias to actual collection name
            normalized_name = await self.resolve_collection_name(collection_name)

            async with self.get_connection() as conn:
                # Get point count
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {normalized_name}")

                return {
                    "status": "green",
                    "optimizer_status": "ok",
                    "vectors_count": count,
                    "indexed_vectors_count": count,
                    "points_count": count,
                    "segments_count": 1,
                    "config": {
                        "params": {
                            "vectors": {
                                "size": settings.default_vector_dimension,
                                "distance": "Cosine"
                            }
                        },
                        "hnsw_config": {
                            "m": 16,
                            "ef_construct": 100,
                            "full_scan_threshold": 10000
                        },
                        "optimizer_config": {
                            "deleted_threshold": 0.2,
                            "vacuum_min_vector_number": 1000,
                            "default_segment_number": 0,
                            "max_segment_size": None,
                            "memmap_threshold": None,
                            "indexing_threshold": 20000,
                            "flush_interval_sec": 5,
                            "max_optimization_threads": 1
                        }
                    },
                    "payload_schema": {}
                }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "status": "red",
                "optimizer_status": "error",
                "vectors_count": 0,
                "indexed_vectors_count": 0,
                "points_count": 0,
                "segments_count": 0,
                "config": {}
            }

    async def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]) -> bool:
        """Insert or update points in collection with 4-way vectors (Qdrant-compatible)"""
        try:
            # Resolve alias to actual collection name
            normalized_name = await self.resolve_collection_name(collection_name)

            async with self.get_connection() as conn:
                async with conn.transaction():
                    for point in points:
                        # Extract 4-way vectors from original Qdrant format
                        vectors = point.get("vector", {})

                        # Handle both new 4-way format and legacy single vector format
                        if isinstance(vectors, dict):
                            # New 4-way vector format (Qdrant-compatible)
                            question_dense = vectors.get("question_dense", [])
                            answer_dense = vectors.get("answer_dense", [])
                            question_sparse = vectors.get("question_sparse", {})
                            answer_sparse = vectors.get("answer_sparse", {})
                        elif isinstance(vectors, list):
                            # Legacy single vector format - replicate to all channels
                            question_dense = vectors
                            answer_dense = vectors
                            question_sparse = {}
                            answer_sparse = {}
                        else:
                            logger.warning(f"Invalid vector format for point {point.get('id')}")
                            continue

                        # Convert dense vectors to PostgreSQL format
                        question_dense_str = "[" + ",".join(map(str, question_dense)) + "]" if question_dense else None
                        answer_dense_str = "[" + ",".join(map(str, answer_dense)) + "]" if answer_dense else None

                        await conn.execute(f"""
                            INSERT INTO {normalized_name} (
                                id, question_dense, answer_dense, question_sparse, answer_sparse, payload
                            )
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (id) DO UPDATE SET
                                question_dense = EXCLUDED.question_dense,
                                answer_dense = EXCLUDED.answer_dense,
                                question_sparse = EXCLUDED.question_sparse,
                                answer_sparse = EXCLUDED.answer_sparse,
                                payload = EXCLUDED.payload;
                        """,
                        str(point["id"]),
                        question_dense_str,
                        answer_dense_str,
                        json.dumps(question_sparse),
                        json.dumps(answer_sparse),
                        json.dumps(point.get("payload", {}))
                        )

                logger.info(f"Upserted {len(points)} points with 4-way vectors to {normalized_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to upsert points to {collection_name}: {e}")
            return False

    async def delete_points(self, collection_name: str, point_ids: List[str]) -> bool:
        """Delete points from collection"""
        try:
            # Normalize collection name to lowercase for PostgreSQL compatibility
            normalized_name = collection_name.lower()

            async with self.get_connection() as conn:
                await conn.execute(
                    f"DELETE FROM {normalized_name} WHERE id = ANY($1)",
                    point_ids
                )
                logger.info(f"Deleted {len(point_ids)} points from {normalized_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete points from {collection_name}: {e}")
            return False

    async def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        offset: int = 0,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors using 4-way dense vector search (question_dense + answer_dense)"""
        try:
            # Resolve alias to actual collection name
            normalized_name = await self.resolve_collection_name(collection_name)

            async with self.get_connection() as conn:
                vector_str = "[" + ",".join(map(str, query_vector)) + "]"

                                # Query both question_dense and answer_dense vectors with improved scoring
                question_dense_query = f"""
                    SELECT id, payload, 'question_dense' as vector_type,
                           CASE
                               WHEN (question_dense <=> '{vector_str}') <= 0.001 THEN 1.0
                               WHEN (question_dense <=> '{vector_str}') <= 0.3 THEN 0.9 - 2.0 * (question_dense <=> '{vector_str}')
                               WHEN (question_dense <=> '{vector_str}') <= 0.7 THEN 0.6 - 0.5 * (question_dense <=> '{vector_str}')
                               ELSE GREATEST(0.05, 0.3 - 0.2 * (question_dense <=> '{vector_str}'))
                           END as score
                    FROM {normalized_name}
                    WHERE question_dense IS NOT NULL
                    ORDER BY question_dense <=> '{vector_str}' ASC
                """

                answer_dense_query = f"""
                    SELECT id, payload, 'answer_dense' as vector_type,
                           CASE
                               WHEN (answer_dense <=> '{vector_str}') <= 0.001 THEN 1.0
                               WHEN (answer_dense <=> '{vector_str}') <= 0.3 THEN 0.9 - 2.0 * (answer_dense <=> '{vector_str}')
                               WHEN (answer_dense <=> '{vector_str}') <= 0.7 THEN 0.6 - 0.5 * (answer_dense <=> '{vector_str}')
                               ELSE GREATEST(0.05, 0.3 - 0.2 * (answer_dense <=> '{vector_str}'))
                           END as score
                    FROM {normalized_name}
                    WHERE answer_dense IS NOT NULL
                    ORDER BY answer_dense <=> '{vector_str}' ASC
                """

                params = []
                param_count = 1

                                # Add score threshold conditions for new scoring system
                if score_threshold is not None:
                    question_dense_query = question_dense_query.replace("WHERE question_dense IS NOT NULL",
                        f"WHERE question_dense IS NOT NULL AND (CASE WHEN (question_dense <=> '{vector_str}') <= 0.001 THEN 1.0 WHEN (question_dense <=> '{vector_str}') <= 0.3 THEN 0.9 - 2.0 * (question_dense <=> '{vector_str}') WHEN (question_dense <=> '{vector_str}') <= 0.7 THEN 0.6 - 0.5 * (question_dense <=> '{vector_str}') ELSE GREATEST(0.05, 0.3 - 0.2 * (question_dense <=> '{vector_str}')) END) >= {score_threshold}")
                    answer_dense_query = answer_dense_query.replace("WHERE answer_dense IS NOT NULL",
                        f"WHERE answer_dense IS NOT NULL AND (CASE WHEN (answer_dense <=> '{vector_str}') <= 0.001 THEN 1.0 WHEN (answer_dense <=> '{vector_str}') <= 0.3 THEN 0.9 - 2.0 * (answer_dense <=> '{vector_str}') WHEN (answer_dense <=> '{vector_str}') <= 0.7 THEN 0.6 - 0.5 * (answer_dense <=> '{vector_str}') ELSE GREATEST(0.05, 0.3 - 0.2 * (answer_dense <=> '{vector_str}')) END) >= {score_threshold}")

                # Add filter conditions
                if filter_conditions:
                    for key, value in filter_conditions.items():
                        filter_condition = f"payload->>'{key}' = '{str(value)}'"
                        question_dense_query = question_dense_query.replace("WHERE question_dense IS NOT NULL", f"WHERE question_dense IS NOT NULL AND {filter_condition}")
                        answer_dense_query = answer_dense_query.replace("WHERE answer_dense IS NOT NULL", f"WHERE answer_dense IS NOT NULL AND {filter_condition}")

                # Combine both queries with UNION ALL, maintaining individual ordering
                combined_query = f"""
                    (
                        {question_dense_query}
                        LIMIT {limit}
                    )
                    UNION ALL
                    (
                        {answer_dense_query}
                        LIMIT {limit}
                    )
                    ORDER BY score DESC
                    LIMIT {limit * 2} OFFSET {offset}
                """

                rows = await conn.fetch(combined_query)

                results = []
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "score": float(row["score"]),
                        "payload": row["payload"] if row["payload"] else {},
                        "vector_type": row["vector_type"]  # Track which vector type matched
                    })

                logger.debug(f"Dense vector search returned {len(results)} results from {normalized_name}")
                return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def bm25_search(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """BM25 text search using 4-way sparse search (question_sparse + answer_sparse) with FTS fallback"""
        try:
            # Resolve alias to actual collection name
            normalized_name = await self.resolve_collection_name(collection_name)

            async with self.get_connection() as conn:
                # Search both question and answer text from payload using PostgreSQL FTS
                question_fts_query = f"""
                    SELECT id, payload, 'question_text' as text_type,
                           ts_rank(to_tsvector('english', payload->>'question'), plainto_tsquery('english', $1)) as score
                    FROM {normalized_name}
                    WHERE payload->>'question' IS NOT NULL
                      AND to_tsvector('english', payload->>'question') @@ plainto_tsquery('english', $1)
                """

                answer_fts_query = f"""
                    SELECT id, payload, 'answer_text' as text_type,
                           ts_rank(to_tsvector('english', payload->>'answer'), plainto_tsquery('english', $1)) as score
                    FROM {normalized_name}
                    WHERE payload->>'answer' IS NOT NULL
                      AND to_tsvector('english', payload->>'answer') @@ plainto_tsquery('english', $1)
                """

                # Combine both queries with UNION ALL and order by score
                combined_fts_query = f"""
                    ({question_fts_query})
                    UNION ALL
                    ({answer_fts_query})
                    ORDER BY score DESC
                    LIMIT {limit * 2} OFFSET {offset}
                """

                rows = await conn.fetch(combined_fts_query, query_text, query_text)

                results = []
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "score": float(row["score"]),
                        "payload": row["payload"] if row["payload"] else {},
                        "text_type": row["text_type"]  # Track which text type matched
                    })

                logger.debug(f"BM25 FTS search returned {len(results)} results from {normalized_name}")
                return results

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    async def create_alias(self, alias_name: str, collection_name: str) -> bool:
        """Create collection alias"""
        try:
            async with self.get_connection() as conn:
                # Create aliases table if it doesn't exist
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS collection_aliases (
                        alias_name TEXT PRIMARY KEY,
                        collection_name TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # Insert or update alias
                await conn.execute("""
                    INSERT INTO collection_aliases (alias_name, collection_name)
                    VALUES ($1, $2)
                    ON CONFLICT (alias_name) DO UPDATE SET
                        collection_name = EXCLUDED.collection_name;
                """, alias_name, collection_name.lower())

                logger.info(f"Created alias: {alias_name} -> {collection_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create alias {alias_name} -> {collection_name}: {e}")
            return False

    async def get_all_aliases(self) -> List[Dict[str, str]]:
        """Get all collection aliases"""
        try:
            async with self.get_connection() as conn:
                # Create aliases table if it doesn't exist
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS collection_aliases (
                        alias_name TEXT PRIMARY KEY,
                        collection_name TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                rows = await conn.fetch("SELECT alias_name, collection_name FROM collection_aliases")
                return [{"alias_name": row["alias_name"], "collection_name": row["collection_name"]} for row in rows]

        except Exception as e:
            logger.error(f"Failed to get aliases: {e}")
            return []

    async def resolve_collection_name(self, name: str) -> str:
        """Resolve alias to actual collection name, or return original name if not an alias"""
        try:
            async with self.get_connection() as conn:
                # Try to find alias
                result = await conn.fetchval(
                    "SELECT collection_name FROM collection_aliases WHERE LOWER(alias_name) = LOWER($1)",
                    name
                )
                return result if result else name.lower()

        except Exception as e:
            logger.debug(f"Error resolving alias {name}: {e}")
            return name.lower()

    async def search_dense_vector(
        self,
        collection_name: str,
        query_vector: List[float],
        vector_field: str,
        limit: int = 40,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search using a single dense vector field (question_dense or answer_dense)"""
        try:
            normalized_name = await self.resolve_collection_name(collection_name)

            async with self.get_connection() as conn:
                vector_str = "[" + ",".join(map(str, query_vector)) + "]"

                query = f"""
                    SELECT id, payload, {vector_field},
                           1 - ({vector_field} <=> '{vector_str}') as score
                    FROM {normalized_name}
                    WHERE {vector_field} IS NOT NULL
                      AND (1 - ({vector_field} <=> '{vector_str}')) >= $1
                    ORDER BY score DESC
                    LIMIT $2
                """

                rows = await conn.fetch(query, score_threshold, limit)

                results = []
                for row in rows:
                    results.append({
                        "id": row["id"],
                        "score": float(row["score"]),
                        "payload": row["payload"] if row["payload"] else {},
                        "vector_field": vector_field
                    })

                return results

        except Exception as e:
            logger.error(f"Dense vector search failed for {vector_field}: {e}")
            return []

    async def search_sparse_vector(
        self,
        collection_name: str,
        sparse_query: Dict[str, Any],
        vector_field: str,
        limit: int = 40
    ) -> List[Dict[str, Any]]:
        """Search using sparse vector (simulated BM25 scoring)"""
        try:
            normalized_name = await self.resolve_collection_name(collection_name)

            # Extract indices and values from sparse query
            indices = sparse_query.get("indices", [])
            values = sparse_query.get("values", [])

            if not indices or not values:
                return []

            async with self.get_connection() as conn:
                # Simulate sparse vector matching by checking JSON overlap
                # This is a simplified approach - in production you'd want proper sparse vector support
                query = f"""
                    SELECT id, payload, {vector_field},
                           -- Simple sparse scoring based on JSON key overlap
                           (
                               SELECT COUNT(*)::float / GREATEST(
                                   jsonb_array_length({vector_field}->'indices'::text), 1
                               )
                               FROM jsonb_array_elements_text({vector_field}->'indices') AS elem
                               WHERE elem::int = ANY($1)
                           ) as score
                    FROM {normalized_name}
                    WHERE {vector_field} IS NOT NULL
                      AND {vector_field} ? 'indices'
                    ORDER BY score DESC
                    LIMIT $2
                """

                rows = await conn.fetch(query, indices, limit)

                results = []
                for row in rows:
                    if row["score"] > 0:  # Only return results with actual matches
                        results.append({
                            "id": row["id"],
                            "score": float(row["score"]),
                            "payload": row["payload"] if row["payload"] else {},
                            "vector_field": vector_field
                        })

                return results

        except Exception as e:
            logger.error(f"Sparse vector search failed for {vector_field}: {e}")
            return []

    async def apply_rrf_fusion(
        self,
        prefetch_results: List[Dict[str, Any]],
        limit: int = 8,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """Apply Reciprocal Rank Fusion to combine multiple search results"""
        try:
            # Collect all unique documents and their RRF scores
            document_scores = {}

            for result_set in prefetch_results:
                results = result_set["results"]
                using = result_set["using"]

                for rank, doc in enumerate(results, 1):
                    doc_id = doc["id"]
                    rrf_score = 1.0 / (rrf_k + rank)

                    if doc_id not in document_scores:
                        # Ensure payload is a dict, not a JSON string
                        payload = parse_payload(doc["payload"])

                        document_scores[doc_id] = {
                            "id": doc_id,
                            "payload": payload,
                            "total_score": 0.0,
                            "individual_scores": {}
                        }

                    document_scores[doc_id]["total_score"] += rrf_score
                    document_scores[doc_id]["individual_scores"][using] = {
                        "score": doc["score"],
                        "rank": rank,
                        "rrf_score": rrf_score
                    }

            # Sort by total RRF score and return top results
            sorted_docs = sorted(
                document_scores.values(),
                key=lambda x: x["total_score"],
                reverse=True
            )

            logger.info(f"RRF fusion: {len(document_scores)} unique docs, returning top {limit}")

            return sorted_docs[:limit]

        except Exception as e:
            logger.error(f"RRF fusion failed: {e}")
            return []


# Global database service instance
db_service = DatabaseService()