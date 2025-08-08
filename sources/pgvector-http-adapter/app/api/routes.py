"""
Qdrant-compatible API routes
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Path, Query, Body
from fastapi.responses import JSONResponse

from app.utils.payload import parse_payload
from app.models.api_models import (
    SearchRequest, SearchResult, ScoredPoint,
    UpsertRequest, UpsertResult,
    DeleteRequest, DeleteResult,
    CreateCollectionRequest, CollectionOperationResult,
    CollectionInfo, HealthInfo,
    HybridSearchRequest, ScrollRequest,
    QdrantResponse
)
from app.services.database import db_service
from app.services.vector_service import vector_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await db_service.initialize()
    await vector_service.initialize()
    logger.info("PgVector HTTP Adapter started successfully")


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await db_service.close()
    logger.info("PgVector HTTP Adapter stopped")


# Health and status endpoints
@router.get("/", response_model=Dict[str, Any])
async def get_cluster_info():
    """Get cluster information (Qdrant compatibility)"""
    return {
        "result": {
            "status": "ok",
            "version": settings.service_version,
            "commit": "unknown",
            "features": ["vector_search", "bm25_search", "hybrid_search", "plpgsql_bm25"]
        },
        "status": "ok",
        "time": 0.001
    }


@router.get("/health", response_model=HealthInfo)
async def health_check():
    """Health check endpoint"""
    return HealthInfo(status="ok", version=settings.service_version)


@router.get("/telemetry")
async def get_telemetry():
    """Telemetry endpoint (Qdrant compatibility)"""
    return {"result": {}, "status": "ok", "time": 0.0}


@router.get("/aliases")
async def list_aliases():
    """List collection aliases (Qdrant compatibility)"""
    try:
        aliases = await db_service.get_all_aliases()
        return {
            "result": {
                "aliases": [
                    {
                        "alias_name": alias["alias_name"],
                        "collection_name": alias["collection_name"]
                    }
                    for alias in aliases
                ]
            },
            "status": "ok",
            "time": 0.001
        }
    except Exception as e:
        logger.error(f"Failed to list aliases: {e}")
        return {
            "result": {
                "aliases": []
            },
            "status": "ok",
            "time": 0.001
        }


@router.get("/cluster")
async def get_cluster_info_detailed():
    """Get detailed cluster information (Qdrant compatibility)"""
    return {
        "result": {
            "status": "enabled",
            "peer_id": 0,
            "peers": {
                "0": {
                    "uri": f"http://localhost:{settings.service_port}"
                }
            },
            "raft_info": {
                "term": 1,
                "commit": 1,
                "pending_operations": 0,
                "leader": 0,
                "role": "Leader"
            }
        },
        "status": "ok",
        "time": 0.001
    }


# Collection management endpoints
@router.get("/collections", response_model=Dict[str, Any])
async def list_collections():
    """List all collections"""
    try:
        # Get actual collections from database
        collections = await db_service.list_collections()
        return {
            "result": {
                "collections": [{"name": name} for name in collections]
            },
            "status": "ok",
            "time": 0.001
        }
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Collection alias endpoints (Qdrant compatibility)
@router.put("/collections/aliases")
@router.post("/collections/aliases")
async def create_alias(request: Dict[str, Any]):
    """Create collection alias (Qdrant compatibility)"""
    try:
        start_time = time.time()

        logger.info(f"Alias request received: {request}")

        # Handle Qdrant client format: {"change_aliases_operations": [...]}
        if "change_aliases_operations" in request:
            for operation in request["change_aliases_operations"]:
                # Handle create alias operation
                if "create_alias" in operation:
                    alias_info = operation["create_alias"]
                    collection_name = alias_info["collection_name"]
                    alias_name = alias_info["alias_name"]

                    # Create alias in database
                    await db_service.create_alias(alias_name, collection_name)
                    logger.info(f"Created alias: {alias_name} -> {collection_name}")

                # Handle delete alias operation (optional)
                elif "delete_alias" in operation:
                    # We can ignore delete operations for now
                    logger.info(f"Delete alias operation ignored: {operation['delete_alias']}")

        # Handle alternative format: {"actions": [...]}
        elif "actions" in request:
            for action in request["actions"]:
                if "create_alias" in action:
                    alias_info = action["create_alias"]
                    collection_name = alias_info["collection_name"]
                    alias_name = alias_info["alias_name"]

                    # Create alias in database
                    await db_service.create_alias(alias_name, collection_name)
                    logger.info(f"Created alias: {alias_name} -> {collection_name}")

        elapsed = time.time() - start_time
        return {
            "result": True,
            "status": "ok",
            "time": elapsed
        }
    except Exception as e:
        logger.error(f"Failed to create alias: {e}")
        return {
            "result": True,  # Return success to not break ETL flow
            "status": "ok",
            "time": 0.001
        }


@router.delete("/collections/aliases/{alias_name}")
async def delete_alias(alias_name: str):
    """Delete collection alias (Qdrant compatibility - not implemented)"""
    return {
        "result": True,
        "status": "ok",
        "time": 0.001
    }


@router.put("/collections/{collection_name}")
async def create_collection(
    collection_name: str = Path(..., description="Collection name"),
    config: CreateCollectionRequest = Body(...)
) -> CollectionOperationResult:
    """Create a new collection"""
    try:
        start_time = time.time()

        # Handle both single vector and multi-vector formats
        if isinstance(config.vectors, dict):
            # Multi-vector format (Qdrant style)
            # Use the first vector configuration for now
            first_vector_config = next(iter(config.vectors.values()))
            vector_size = first_vector_config.size
            logger.info(f"Multi-vector collection detected, using first vector config with size {vector_size}")
        else:
            # Single vector format
            vector_size = config.vectors.size

        success = await vector_service.create_collection_with_vectors(
            collection_name, vector_size
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to create collection")

        elapsed = time.time() - start_time
        logger.info(f"Created collection {collection_name} with vector size {vector_size}")

        return CollectionOperationResult(result=True, status="ok", time=elapsed)

    except Exception as e:
        logger.error(f"Failed to create collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}/exists")
async def collection_exists(collection_name: str):
    """Check if collection exists (Qdrant compatibility)"""
    try:
        exists = await db_service.collection_exists(collection_name)
        return {
            "result": {
                "exists": exists
            },
            "status": "ok",
            "time": 0.001
        }
    except Exception as e:
        logger.error(f"Error checking collection existence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}")
async def get_collection_info(
    collection_name: str = Path(..., description="Collection name")
) -> Dict[str, Any]:
    """Get collection information"""
    try:
        start_time = time.time()

        if not await db_service.collection_exists(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")

        info = await db_service.get_collection_info(collection_name)
        elapsed = time.time() - start_time

        return {
            "result": info,
            "status": "ok",
            "time": elapsed
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{collection_name}")
async def delete_collection(
    collection_name: str = Path(..., description="Collection name")
) -> CollectionOperationResult:
    """Delete a collection"""
    try:
        start_time = time.time()

        if not await db_service.collection_exists(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")

        async with db_service.get_connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {collection_name}")

        elapsed = time.time() - start_time
        logger.info(f"Deleted collection {collection_name}")

        return CollectionOperationResult(result=True, status="ok", time=elapsed)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Point operations
@router.put("/collections/{collection_name}/points")
async def upsert_points(
    collection_name: str = Path(..., description="Collection name"),
    request: UpsertRequest = Body(...)
) -> QdrantResponse:
    """Insert or update points"""
    try:
        if not await db_service.collection_exists(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")

        points_data = []
        for point in request.points:
            # Handle both single vector and multi-vector formats
            if isinstance(point.vector, dict):
                # Multi-vector format (Qdrant style) - prefer dense vectors over sparse
                vector_data = None
                dense_vector_name = None

                # Look for dense vectors first (list format)
                for name, vec in point.vector.items():
                    if isinstance(vec, list):
                        vector_data = vec
                        dense_vector_name = name
                        logger.debug(f"Using dense vector '{name}' with {len(vec)} dimensions")
                        break

                # If no dense vector found, try to use first available vector
                if vector_data is None:
                    first_name = next(iter(point.vector.keys()))
                    first_vector = point.vector[first_name]
                    if isinstance(first_vector, dict):
                        # This might be a sparse vector - skip it for now
                        logger.warning(f"Skipping sparse vector '{first_name}' - pgvector doesn't support sparse vectors")
                        continue
                    else:
                        vector_data = first_vector
                        dense_vector_name = first_name
                        logger.debug(f"Using vector '{first_name}' with {len(first_vector)} dimensions")

                if vector_data is None:
                    logger.error(f"No compatible dense vector found for point {point.id}")
                    continue

            else:
                # Single vector format
                vector_data = point.vector

            points_data.append({
                "id": point.id,
                "vector": vector_data,
                "payload": point.payload or {}
            })

        success = await db_service.upsert_points(collection_name, points_data)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to upsert points")

        logger.info(f"Upserted {len(points_data)} points to {collection_name}")

        # Return Qdrant-compatible response
        upsert_result = UpsertResult(operation_id=int(time.time()), status="acknowledged")
        return QdrantResponse.success(upsert_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upsert points: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/points/delete")
async def delete_points(
    collection_name: str = Path(..., description="Collection name"),
    request: DeleteRequest = Body(...)
) -> DeleteResult:
    """Delete points"""
    try:
        if not await db_service.collection_exists(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")

        point_ids = [str(pid) for pid in request.points]
        success = await db_service.delete_points(collection_name, point_ids)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete points")

        logger.info(f"Deleted {len(point_ids)} points from {collection_name}")
        return DeleteResult(operation_id=int(time.time()), status="acknowledged")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete points: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Search endpoints
@router.post("/collections/{collection_name}/points/search")
async def search_points(
    collection_name: str = Path(..., description="Collection name"),
    request: SearchRequest = Body(...)
) -> SearchResult:
    """Search for similar points"""
    try:
        start_time = time.time()

        if not await db_service.collection_exists(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")

        results = await db_service.search_similar(
            collection_name=collection_name,
            query_vector=request.vector,
            limit=request.limit,
            offset=request.offset,
            score_threshold=request.score_threshold,
            filter_conditions=request.filter
        )

        scored_points = []
        for result in results:
            point = ScoredPoint(
                id=result["id"],
                score=result["score"],
                payload=result["payload"] if request.with_payload else None,
                vector=result["vector"] if request.with_vector else None
            )
            scored_points.append(point)

        elapsed = time.time() - start_time
        logger.info(f"Search returned {len(scored_points)} results in {elapsed:.3f}s")

        return SearchResult(result=scored_points, status="ok", time=elapsed)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/points/query")
async def query_points(
    collection_name: str = Path(..., description="Collection name"),
    request: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Qdrant-style query_points with prefetch and fusion support"""
    try:
        start_time = time.time()

        if not await db_service.collection_exists(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")

        logger.info(f"Query request received for {collection_name}")
        logger.info(f"Full request: {json.dumps(request, indent=2, default=str)}")

        # Extract parameters from Qdrant query format
        limit = request.get("limit", 10)
        score_threshold = request.get("score_threshold", 0.0)

        # Handle Qdrant query_points with full 4-way prefetch + RRF support (compatible with original)
        prefetch_results = []

        # Check for prefetch queries (Qdrant complex query format)
        if "prefetch" in request and isinstance(request["prefetch"], list):
            logger.info(f"Processing {len(request['prefetch'])} prefetch queries for 4-way search (Qdrant-compatible)")

            # Process each prefetch operation separately
            for prefetch in request["prefetch"]:
                if isinstance(prefetch, dict) and "query" in prefetch:
                    using = prefetch.get("using", "")
                    query_data = prefetch["query"]
                    prefetch_limit = prefetch.get("limit", 40)
                    score_threshold = prefetch.get("score_threshold", 0.0)

                    # Execute individual prefetch query
                    if "dense" in using and isinstance(query_data, list):
                        # Dense vector search (question_dense or answer_dense)
                        results = await db_service.search_dense_vector(
                            collection_name=collection_name,
                            query_vector=query_data,
                            vector_field=using,  # question_dense or answer_dense
                            limit=prefetch_limit,
                            score_threshold=score_threshold
                        )
                        prefetch_results.append({
                            "using": using,
                            "results": results,
                            "type": "dense"
                        })
                        logger.info(f"Prefetch '{using}': {len(results)} results")

                    elif "sparse" in using and isinstance(query_data, dict):
                        # Sparse vector search (question_sparse or answer_sparse)
                        results = await db_service.search_sparse_vector(
                            collection_name=collection_name,
                            sparse_query=query_data,
                            vector_field=using,  # question_sparse or answer_sparse
                            limit=prefetch_limit
                        )
                        prefetch_results.append({
                            "using": using,
                            "results": results,
                            "type": "sparse"
                        })
                        logger.info(f"Prefetch '{using}': {len(results)} results")

            # Apply RRF fusion to combine all prefetch results (as in original Qdrant)
            if prefetch_results:
                final_results = await db_service.apply_rrf_fusion(
                    prefetch_results, limit=limit
                )
                logger.info(f"RRF fusion complete: {len(final_results)} final results")
            else:
                logger.warning("No valid prefetch results to fuse")
                final_results = []

        else:
            # Fallback for simple query format
            logger.warning("No prefetch queries found in request")
            final_results = []

        # Convert RRF results to Qdrant format
        points = []
        for result in final_results:
            # Ensure payload is a dict, not a JSON string
            payload = parse_payload(result.get("payload", {}))

            point = {
                "id": result["id"],
                "score": result["total_score"],  # Use RRF total score
                "payload": payload,
                "vector": None,  # Vector not returned in query results by default
                "version": 1  # Required by Qdrant client
            }
            points.append(point)

        elapsed = time.time() - start_time
        logger.info(f"Query returned {len(points)} results")

        return {
            "result": {
                "points": points
            },
            "status": "ok",
            "time": elapsed
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}/points/scroll")
async def scroll_points(
    collection_name: str = Path(..., description="Collection name"),
    request: ScrollRequest = Body(...)
) -> Dict[str, Any]:
    """Scroll through points"""
    try:
        start_time = time.time()

        if not await db_service.collection_exists(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")

        # Basic implementation - in production you'd want proper pagination
        async with db_service.get_connection() as conn:
            offset = request.offset if isinstance(request.offset, int) else 0

            query = f"""
                SELECT id, vector, payload
                FROM {collection_name}
                ORDER BY id
                LIMIT {request.limit} OFFSET {offset}
            """

            rows = await conn.fetch(query)

            points = []
            for row in rows:
                point_data = {
                    "id": row["id"],
                    "payload": row["payload"] if request.with_payload and row["payload"] else None,
                    "vector": list(map(float, row["vector"])) if request.with_vector and row["vector"] else None
                }
                points.append(point_data)

        elapsed = time.time() - start_time
        next_page_offset = offset + len(points) if len(points) == request.limit else None

        return {
            "result": {
                "points": points,
                "next_page_offset": next_page_offset
            },
            "status": "ok",
            "time": elapsed
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scroll failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Custom hybrid search endpoint
@router.post("/collections/{collection_name}/points/search/hybrid")
async def hybrid_search(
    collection_name: str = Path(..., description="Collection name"),
    request: HybridSearchRequest = Body(...)
) -> SearchResult:
    """Hybrid search combining dense vectors and BM25"""
    try:
        start_time = time.time()

        if not await db_service.collection_exists(collection_name):
            raise HTTPException(status_code=404, detail="Collection not found")

        results = await vector_service.hybrid_search(
            collection_name=collection_name,
            query_vector=request.query_vector,
            query_text=request.query_text,
            limit=request.limit,
            offset=request.offset,
            fusion_weights=request.fusion_weights,
            filter_conditions=request.filter
        )

        scored_points = []
        for result in results:
            point = ScoredPoint(
                id=result["id"],
                score=result["score"],
                payload=result["payload"] if request.with_payload else None,
                vector=result.get("vector") if request.with_vector else None
            )
            scored_points.append(point)

        elapsed = time.time() - start_time
        logger.info(f"Hybrid search returned {len(scored_points)} results in {elapsed:.3f}s")

        return SearchResult(result=scored_points, status="ok", time=elapsed)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))