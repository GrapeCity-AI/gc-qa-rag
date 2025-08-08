"""
Vector service for hybrid search operations (no embedding computation)
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from app.core.config import settings
from app.services.database import db_service

logger = logging.getLogger(__name__)


class VectorService:
    """Service for vector operations and hybrid search (embedding-free)"""

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        """Initialize service (no heavy models to load)"""
        if self._initialized:
            return

        self._initialized = True
        logger.info("VectorService initialized successfully (embedding-free mode)")

    def calculate_rrf_score(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60,
        weights: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate Reciprocal Rank Fusion (RRF) scores
        RRF formula: score = sum(weight / (k + rank))
        """
        if weights is None:
            weights = {"dense": 0.7, "sparse": 0.3}

        # Create lookup dictionaries for scores by document ID
        dense_lookup = {item["id"]: idx for idx, item in enumerate(dense_results)}
        sparse_lookup = {item["id"]: idx for idx, item in enumerate(sparse_results)}

        # Collect all unique document IDs
        all_ids = set(dense_lookup.keys()) | set(sparse_lookup.keys())

        # Calculate RRF scores
        rrf_scores = {}
        for doc_id in all_ids:
            rrf_score = 0.0

            # Add dense component
            if doc_id in dense_lookup:
                dense_rank = dense_lookup[doc_id] + 1  # Rank starts from 1
                rrf_score += weights["dense"] / (k + dense_rank)

            # Add sparse component
            if doc_id in sparse_lookup:
                sparse_rank = sparse_lookup[doc_id] + 1  # Rank starts from 1
                rrf_score += weights["sparse"] / (k + sparse_rank)

            rrf_scores[doc_id] = rrf_score

        # Merge results with original metadata
        result_lookup = {}
        for item in dense_results:
            result_lookup[item["id"]] = item
        for item in sparse_results:
            if item["id"] not in result_lookup:
                result_lookup[item["id"]] = item

        # Create final ranked results
        final_results = []
        for doc_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            result = result_lookup[doc_id].copy()
            result["score"] = rrf_score
            final_results.append(result)

        return final_results

    async def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_text: str,
        limit: int = 10,
        offset: int = 0,
        fusion_weights: Dict[str, float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining dense vector search and BM25 sparse search
        Note: query_vector should be provided by caller (via AI service)
        """
        try:
            if fusion_weights is None:
                fusion_weights = {"dense": 0.7, "sparse": 0.3}

            if not query_vector:
                logger.error("No query vector provided")
                return []

            # Perform both searches concurrently
            dense_task = db_service.search_similar(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit * 2,  # Get more results for better fusion
                offset=0,  # Always start from 0 for fusion
                filter_conditions=filter_conditions
            )

            sparse_task = db_service.bm25_search(
                collection_name=collection_name,
                query_text=query_text,
                limit=limit * 2,  # Get more results for better fusion
                offset=0  # Always start from 0 for fusion
            )

            dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)

            # Perform RRF fusion
            fused_results = self.calculate_rrf_score(
                dense_results=dense_results,
                sparse_results=sparse_results,
                weights=fusion_weights
            )

            # Apply offset and limit to final results
            start_idx = offset
            end_idx = offset + limit
            final_results = fused_results[start_idx:end_idx]

            logger.info(f"Hybrid search returned {len(final_results)} results for query: {query_text[:50]}...")
            return final_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def create_collection_with_vectors(
        self,
        collection_name: str,
        vector_size: int = None
    ) -> bool:
        """Create collection with proper vector configuration"""
        if vector_size is None:
            vector_size = settings.default_vector_dimension

        return await db_service.create_collection(collection_name, vector_size)


# Global vector service instance
vector_service = VectorService()