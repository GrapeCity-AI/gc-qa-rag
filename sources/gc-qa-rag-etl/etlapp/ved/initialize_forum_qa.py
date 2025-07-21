import os
import json
import time
import uuid
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from qdrant_client.models import PointStruct
from etlapp.common.context import EtlRagContext
from etlapp.common.hash import get_hash_folder
from etlapp.common.vector import VectorClient
from etlapp.common.file import read_text_from_file

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class EmbeddingData:
    """Represents embedding data for a question or answer."""

    embedding: List[float]
    sparse_embedding: List[Dict[str, Any]]


@dataclass
class QAObject:
    """Represents a question-answer pair with embeddings."""

    question: str
    answer: str
    question_embedding: Optional[EmbeddingData] = None
    answer_embedding: Optional[EmbeddingData] = None


@dataclass
class GroupObject:
    """Represents a group of Q&A pairs with a summary."""

    summary: str
    possible_qa: List[QAObject]


@dataclass
class ForumObject:
    """Represents a forum post with metadata and groups of Q&A pairs."""

    summary: str
    possible_qa: List[QAObject]


def transform_sparse(embedding: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    """Transform sparse embedding data into a format suitable for vector storage."""
    return {
        "indices": [item["index"] for item in embedding],
        "values": [item["value"] for item in embedding],
    }


def extract_object(text: str) -> ForumObject:
    """Extract and parse forum object from JSON text."""
    try:
        data = json.loads(text)
        return ForumObject(
            summary=data.get("Summary", ""),
            possible_qa=[
                QAObject(
                    question=qa.get("Question", ""),
                    answer=qa.get("Answer", ""),
                    question_embedding=EmbeddingData(
                        embedding=qa.get("QuestionEmbedding", {}).get("embedding", []),
                        sparse_embedding=qa.get("QuestionEmbedding", {}).get(
                            "sparse_embedding", []
                        ),
                    )
                    if "QuestionEmbedding" in qa
                    else None,
                    answer_embedding=EmbeddingData(
                        embedding=qa.get("AnswerEmbedding", {}).get("embedding", []),
                        sparse_embedding=qa.get("AnswerEmbedding", {}).get(
                            "sparse_embedding", []
                        ),
                    )
                    if "AnswerEmbedding" in qa
                    else None,
                )
                for qa in data.get("PossibleQA", [])
            ],
        )
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON, returning empty forum object")
        return ForumObject(summary="", possible_qa=[])


def create_point(qa: QAObject, metadata: Dict[str, Any]) -> Optional[PointStruct]:
    """Create a point structure for vector storage from a Q&A pair."""
    if not qa.question_embedding or not qa.answer_embedding:
        return None

    new_item_id = str(uuid.uuid4())
    new_item_vector = {
        "question_dense": qa.question_embedding.embedding,
        "answer_dense": qa.answer_embedding.embedding,
        "question_sparse": transform_sparse(qa.question_embedding.sparse_embedding),
        "answer_sparse": transform_sparse(qa.answer_embedding.sparse_embedding),
    }

    new_item_payload = {
        **metadata,
        "question": qa.question,
        "answer": qa.answer,
    }

    return PointStruct(id=new_item_id, vector=new_item_vector, payload=new_item_payload)


def process_forum_object(
    forum: ForumObject, file_index: str, question_index: int, metadata: Dict[str, Any]
) -> List[PointStruct]:
    """Process a forum object and create points for vector storage."""
    points = []

    for qa in forum.possible_qa:
        point = create_point(
            qa=qa,
            metadata={
                **metadata,
                "file_index": file_index,
                "question_index": question_index,
                "summary": forum.summary,
            },
        )
        if point:
            points.append(point)

    return points


def start_initialize_forum_qa(context: EtlRagContext) -> None:
    """Initialize forum QA processing and vector storage."""
    root_path = context.root
    product = context.product
    url = context.base_url
    collection_name = f"forum_qa_{product}_{context.tag}"

    client = VectorClient(url)
    client.ensure_collection_exists(collection_name)

    forum_file_path = f"{root_path}/das/.temp/forum/qa/{product}/combined.json"
    folder_path = f"{root_path}/etl_forum_qa/.temp/outputs_embedding/{product}"

    thread_list = json.loads(read_text_from_file(forum_file_path))['threads']
    thread_dict = {
        f"{thread['tid']}_{thread['postDate']}": thread for thread in thread_list
    }

    for file_index in thread_dict:
        actual_folder = os.path.join(folder_path, get_hash_folder(str(file_index)))
        file_path = os.path.join(folder_path, actual_folder, str(file_index) + ".json")
        logger.info(f"Processing forum post: {os.path.basename(file_path)}")

        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}, skipping")
            continue

        # Check if post date is within specified range (after 2021.01.01 12:00:00 AM)
        if thread_dict[file_index]["postDate"] < 1609459200:
            logger.info(
                f"Post date is outside specified range for file: {file_path}, skipping"
            )
            continue

        content = read_text_from_file(file_path)
        forum = extract_object(content)

        metadata = {
            "product": product,
            "url": thread_dict[file_index]["content"]["url"],
            "title": thread_dict[file_index]["content"]["title"],
            "category": thread_dict[file_index]["content"]["forumName"],
            "date": thread_dict[file_index]["postDate"],
        }

        points = process_forum_object(
            forum=forum, file_index=file_index, question_index=0, metadata=metadata
        )

        if points:
            # Retry up to 3 times
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    client.insert_to_collection(collection_name, points)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Failed to insert points after {max_retries} attempts: {str(e)}"
                        )
                    time.sleep(1)
