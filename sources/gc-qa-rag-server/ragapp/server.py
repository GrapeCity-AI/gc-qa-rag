from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from qdrant_client import QdrantClient
import logging
import time
from typing import Dict, Any, Optional

from ragapp.common.config import app_config
from ragapp.common.db import db
from ragapp.common.log import setup_logging
from ragapp.services.search import search_sementic_hybrid
from ragapp.services.query import chat_for_query
from ragapp.services.summary import summary_hits
from ragapp.services.think import summary_hits_think
from ragapp.services.research import research_hits
from ragapp.services.product import get_available_products
from ragapp.common.limiter import rate_limiter
from ragapp.common.llm import get_llm_sse_result, get_llm_full_result

# Initialize logger
logger = logging.getLogger(__name__)

# Product cache configuration
PRODUCTS_CACHE_TTL = 10  # Cache for 10 seconds
_products_cache: Dict[
    str, Dict[str, Any]
] = {}  # {mode: {data: result, timestamp: time}}


class SearchModel(BaseModel):
    keyword: str
    mode: str
    product: str = "forguncy"
    session_id: str = ""
    session_index: int = 0


class ChatModel(BaseModel):
    keyword: str
    messages: list
    product: str = "forguncy"


class FeedbackModel(BaseModel):
    question: str
    answer: str
    rating: int
    comments: str
    product: str = "forguncy"


class SearchHistoryRequest(BaseModel):
    date: str
    token: str


# Initialize log
setup_logging()

# Initialize app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector database
url = app_config.vector_db.host
client = QdrantClient(url)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/search/")
def search(item: SearchModel, background_tasks: BackgroundTasks):
    if item.mode not in ["search", "chat", "think"]:
        raise HTTPException(status_code=403, detail="mode should be search or chat")

    if len(item.keyword) > 1000:
        raise HTTPException(
            status_code=403, detail="keyword should be less than 1000 characters"
        )

    if len(item.product) > 100:
        raise HTTPException(
            status_code=403, detail="product should be less than 100 characters"
        )

    rate_limiter.hit_search()

    background_tasks.add_task(
        db.add_search_history,
        item.keyword,
        item.mode,
        item.product,
        item.session_id,
        item.session_index,
    )

    hits = search_sementic_hybrid(client, item.keyword, item.product)

    return hits


@app.post("/chat_streaming/")
async def chat_streaming(item: ChatModel):
    if len(item.keyword) > 1000:
        raise HTTPException(
            status_code=403, detail="keyword should be less than 1000 characters"
        )

    if len(item.product) > 100:
        raise HTTPException(
            status_code=403, detail="product should be less than 100 characters"
        )

    rate_limiter.hit_chat()

    if len(item.messages) == 1:
        keyword = item.messages[0]["content"]
    elif len(item.messages) >= 7:
        stream = await getLimitText()
        return StreamingResponse(stream, media_type="text/event-stream")
    else:
        keyword = await get_llm_full_result(chat_for_query, item.messages)

    logger.info(f"Keyword: {keyword}")

    hits = search_sementic_hybrid(client, keyword, item.product)
    stream = await get_llm_sse_result(summary_hits, keyword, item.messages, hits)
    return StreamingResponse(stream, media_type="text/event-stream")


@app.post("/think_streaming/")
async def think_streaming(item: ChatModel):
    if len(item.keyword) > 1000:
        raise HTTPException(
            status_code=403, detail="keyword should be less than 1000 characters"
        )

    if len(item.product) > 100:
        raise HTTPException(
            status_code=403, detail="product should be less than 100 characters"
        )

    rate_limiter.hit_think()

    if len(item.messages) == 1:
        keyword = item.messages[0]["content"]
    elif len(item.messages) >= 7:
        stream = await getLimitText()
        return StreamingResponse(stream, media_type="text/event-stream")
    else:
        keyword = await get_llm_full_result(chat_for_query, item.messages)

    logger.info(f"Keyword: {keyword}")

    hits = search_sementic_hybrid(client, keyword, item.product)
    stream = await get_llm_sse_result(summary_hits_think, keyword, item.messages, hits)
    return StreamingResponse(stream, media_type="text/event-stream")


@app.post("/reasearch_streaming/")
async def reasearch_streaming(item: ChatModel):
    if len(item.keyword) > 1000:
        raise HTTPException(
            status_code=403, detail="keyword should be less than 1000 characters"
        )

    if len(item.product) > 100:
        raise HTTPException(
            status_code=403, detail="product should be less than 100 characters"
        )

    rate_limiter.hit_research()

    if len(item.messages) == 1:
        keyword = item.messages[0]["content"]
    elif len(item.messages) >= 7:
        stream = await getLimitText()
        return StreamingResponse(stream, media_type="text/event-stream")
    else:
        keyword = await get_llm_full_result(chat_for_query, item.messages)

    logger.info(f"Keyword: {keyword}")

    hits = search_sementic_hybrid(client, keyword, item.product)
    stream = await get_llm_sse_result(
        research_hits, client, keyword, item.messages, hits, item.product
    )
    return StreamingResponse(stream, media_type="text/event-stream")


@app.post("/feedback/")
def feedback(item: FeedbackModel, background_tasks: BackgroundTasks):
    if len(item.question) > 1000:
        raise HTTPException(
            status_code=403, detail="question should be less than 1000 characters"
        )

    if len(item.answer) > 10000:
        raise HTTPException(
            status_code=403, detail="answer should be less than 10000 characters"
        )

    if len(item.comments) > 1000:
        raise HTTPException(
            status_code=403, detail="comments should be less than 1000 characters"
        )

    if len(item.product) > 100:
        raise HTTPException(
            status_code=403, detail="product should be less than 100 characters"
        )

    rate_limiter.hit_feedback()

    background_tasks.add_task(
        db.add_qa_feedback,
        item.question,
        item.answer,
        item.rating,
        item.comments,
        item.product,
    )

    return "success"


async def getLimitText():
    return "Maximum conversation rounds reached, please start a new conversation."


def _get_cached_products(mode: str) -> Optional[Dict]:
    """Get cached product list"""
    if mode in _products_cache:
        cache_entry = _products_cache[mode]
        current_time = time.time()

        # Check if cache is expired
        if current_time - cache_entry["timestamp"] < PRODUCTS_CACHE_TTL:
            logger.info(f"Returning valid cached product list, mode: {mode}")
            return cache_entry["data"]
        else:
            # Cache expired, but still return cached data and mark for update
            logger.info(f"Returning expired cached product list, mode: {mode}")
            return cache_entry["data"]

    return None


def _is_cache_expired(mode: str) -> bool:
    """Check if cache is expired"""
    if mode in _products_cache:
        cache_entry = _products_cache[mode]
        current_time = time.time()
        return current_time - cache_entry["timestamp"] >= PRODUCTS_CACHE_TTL
    return True


def _set_cached_products(mode: str, data: Dict) -> None:
    """Set product list cache"""
    _products_cache[mode] = {"data": data, "timestamp": time.time()}
    logger.info(f"Updated product cache, mode: {mode}")


def _update_products_cache_background(mode: str) -> None:
    """Background task: update product cache"""
    try:
        logger.info(f"Background product cache update started, mode: {mode}")
        result = get_available_products(mode)
        _set_cached_products(mode, result)
        logger.info(f"Background product cache update completed, mode: {mode}")
    except Exception as e:
        logger.error(
            f"Background product cache update failed, mode: {mode}, error: {e}"
        )


@app.get("/products/")
def get_products(mode: str = "fixed", background_tasks: BackgroundTasks = None):
    """Get available product list (with cache and background update)"""
    # First try to get from cache
    cached_result = _get_cached_products(mode)

    if cached_result is not None:
        # Have cached data, check if expired
        if _is_cache_expired(mode):
            # Cache expired, start background task to update
            if background_tasks:
                background_tasks.add_task(_update_products_cache_background, mode)
                logger.info(
                    f"Started background task to update expired cache, mode: {mode}"
                )

        return cached_result

    # No cache at all, synchronously get data
    logger.info(f"First time getting product list, mode: {mode}")
    result = get_available_products(mode)

    # Update cache
    _set_cached_products(mode, result)

    return result
