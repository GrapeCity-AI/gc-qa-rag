from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from qdrant_client import QdrantClient
import logging

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
    return "当前达到最大对话轮次，请重新开始一个对话。"


@app.get("/products/")
def get_products(mode: str = "fixed"):
    """获取可用的产品列表"""
    return get_available_products(mode)
