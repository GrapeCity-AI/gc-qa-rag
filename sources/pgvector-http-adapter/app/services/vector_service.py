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

    def calculate_quad_rrf_score(
        self,
        question_dense_results: List[Dict[str, Any]],
        answer_dense_results: List[Dict[str, Any]],
        question_text_results: List[Dict[str, Any]],
        answer_text_results: List[Dict[str, Any]],
        k: int = 10,  # 降低k值，增加排名差异
        weights: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate 4-way Reciprocal Rank Fusion (RRF) scores with improved scoring strategy
        RRF formula: score = sum(weight / (k + rank))
        """
        if weights is None:
            # 改进权重分配：更重视question匹配，适当平衡dense和sparse
            weights = {
                "question_dense": 0.35,  # 问题向量匹配最重要
                "answer_dense": 0.25,    # 答案向量次重要
                "question_text": 0.25,   # 问题文本匹配重要
                "answer_text": 0.15     # 答案文本补充
            }

        # Normalize scores for each search type to ensure fairness
        self._normalize_search_scores(question_dense_results, target_range=(0.1, 1.0))
        self._normalize_search_scores(answer_dense_results, target_range=(0.1, 1.0))
        self._normalize_search_scores(question_text_results, target_range=(0.1, 1.0))
        self._normalize_search_scores(answer_text_results, target_range=(0.1, 1.0))

        # Create lookup dictionaries for ranks by document ID
        lookups = {
            "question_dense": {item["id"]: idx for idx, item in enumerate(question_dense_results)},
            "answer_dense": {item["id"]: idx for idx, item in enumerate(answer_dense_results)},
            "question_text": {item["id"]: idx for idx, item in enumerate(question_text_results)},
            "answer_text": {item["id"]: idx for idx, item in enumerate(answer_text_results)}
        }

        # Collect all unique document IDs
        all_ids = set()
        for lookup in lookups.values():
            all_ids.update(lookup.keys())

        # Calculate RRF scores
        rrf_scores = {}
        for doc_id in all_ids:
            rrf_score = 0.0

            # Add contribution from each search type
            for search_type, lookup in lookups.items():
                if doc_id in lookup:
                    rank = lookup[doc_id] + 1  # Rank starts from 1
                    rrf_score += weights[search_type] / (k + rank)

            rrf_scores[doc_id] = rrf_score

        # Merge results with original metadata
        result_lookup = {}
        all_results = [question_dense_results, answer_dense_results, question_text_results, answer_text_results]
        for results in all_results:
            for item in results:
                if item["id"] not in result_lookup:
                    result_lookup[item["id"]] = item

        # Apply score normalization to improve differentiation
        if rrf_scores:
            scores = list(rrf_scores.values())
            min_score, max_score = min(scores), max(scores)
            target_min, target_max = 0.1, 1.0

            if max_score > min_score:
                # Linear normalization to target range
                range_span = target_max - target_min
                for doc_id in rrf_scores:
                    normalized = (rrf_scores[doc_id] - min_score) / (max_score - min_score)
                    rrf_scores[doc_id] = target_min + range_span * normalized
            else:
                # If all scores are same, give progressive scores
                step = (target_max - target_min) / max(len(rrf_scores), 1)
                for i, doc_id in enumerate(rrf_scores):
                    rrf_scores[doc_id] = target_max - (i * step * 0.1)

        # Create final ranked results
        final_results = []
        for doc_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            result = result_lookup[doc_id].copy()
            result["score"] = rrf_score
            final_results.append(result)

        return final_results

    def _normalize_search_scores(self, results: List[Dict[str, Any]], target_range: tuple = (0.1, 1.0)) -> None:
        """
        Normalize search scores to ensure fairness across different search types
        Modifies results in-place
        """
        if not results:
            return

        scores = [item.get("score", 0.0) for item in results]
        if not scores:
            return

        min_score, max_score = min(scores), max(scores)
        target_min, target_max = target_range

        if max_score > min_score:
            # Linear normalization to target range
            range_span = target_max - target_min
            for item in results:
                original_score = item.get("score", 0.0)
                normalized = (original_score - min_score) / (max_score - min_score)
                item["score"] = target_min + range_span * normalized
        else:
            # If all scores are same, give progressive scores
            step = (target_max - target_min) / max(len(results), 1)
            for i, item in enumerate(results):
                item["score"] = target_max - (i * step * 0.1)

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
        Perform 4-way hybrid search combining dense vector search (question+answer) and text search (question+answer)
        Note: query_vector should be provided by caller (via AI service)
        """
        try:
            if fusion_weights is None:
                fusion_weights = {
                    "question_dense": 0.3,
                    "answer_dense": 0.3,
                    "question_text": 0.2,
                    "answer_text": 0.2
                }

            if not query_vector:
                logger.error("No query vector provided")
                return []

            # Perform both searches concurrently
            dense_task = db_service.search_similar(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit * 3,  # Get more results for better 4-way fusion
                offset=0,  # Always start from 0 for fusion
                filter_conditions=filter_conditions
            )

            sparse_task = db_service.bm25_search(
                collection_name=collection_name,
                query_text=query_text,
                limit=limit * 3,  # Get more results for better 4-way fusion
                offset=0  # Always start from 0 for fusion
            )

            dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)

            # Separate results by vector/text type
            question_dense_results = [r for r in dense_results if r.get("vector_type") == "question_dense"]
            answer_dense_results = [r for r in dense_results if r.get("vector_type") == "answer_dense"]
            question_text_results = [r for r in sparse_results if r.get("text_type") == "question_text"]
            answer_text_results = [r for r in sparse_results if r.get("text_type") == "answer_text"]

            # Perform 4-way RRF fusion
            fused_results = self.calculate_quad_rrf_score(
                question_dense_results=question_dense_results,
                answer_dense_results=answer_dense_results,
                question_text_results=question_text_results,
                answer_text_results=answer_text_results,
                weights=fusion_weights
            )

            # Apply offset and limit to final results
            start_idx = offset
            end_idx = offset + limit
            final_results = fused_results[start_idx:end_idx]

            logger.info(f"4-way hybrid search returned {len(final_results)} results for query: {query_text[:50]}...")
            logger.debug(f"Search breakdown: Q-Dense:{len(question_dense_results)}, A-Dense:{len(answer_dense_results)}, Q-Text:{len(question_text_results)}, A-Text:{len(answer_text_results)}")
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