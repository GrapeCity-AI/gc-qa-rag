import os
import json
import uuid
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from qdrant_client.models import PointStruct
from etlapp.common.context import EtlRagContext
from etlapp.common.format import extract_markdown_content
from etlapp.common.vector import VectorClient
from etlapp.common.file import get_file_names_in_directory, read_text_from_file

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingData:
    embedding: List[float]
    sparse_embedding: List[Dict[str, Any]]


@dataclass
class QAObject:
    question: str
    answer: str
    question_embedding: Optional[EmbeddingData] = None
    answer_embedding: Optional[EmbeddingData] = None
    sub: Optional[Dict[str, Any]] = None


@dataclass
class GroupObject:
    summary: str
    possible_qa: List[QAObject]


@dataclass
class DocumentObject:
    product: str
    url: str
    title: str
    category: str
    groups: List[GroupObject]


def transform_sparse(embedding: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    return {
        "indices": [item["index"] for item in embedding],
        "values": [item["value"] for item in embedding],
    }


def extract_object(text: str) -> DocumentObject:
    try:
        data = json.loads(text)
        return DocumentObject(
            product=data.get("Product", ""),
            url=data.get("Url", ""),
            title=data.get("Title", ""),
            category=data.get("Category", ""),
            groups=[
                GroupObject(
                    summary=group.get("Summary", ""),
                    possible_qa=[
                        QAObject(
                            question=qa.get("Question", ""),
                            answer=qa.get("Answer", ""),
                            question_embedding=EmbeddingData(
                                embedding=qa.get("QuestionEmbedding", {}).get(
                                    "embedding", []
                                ),
                                sparse_embedding=qa.get("QuestionEmbedding", {}).get(
                                    "sparse_embedding", []
                                ),
                            )
                            if "QuestionEmbedding" in qa
                            else None,
                            answer_embedding=EmbeddingData(
                                embedding=qa.get("AnswerEmbedding", {}).get(
                                    "embedding", []
                                ),
                                sparse_embedding=qa.get("AnswerEmbedding", {}).get(
                                    "sparse_embedding", []
                                ),
                            )
                            if "AnswerEmbedding" in qa
                            else None,
                            sub=qa.get("Sub"),
                        )
                        for qa in group.get("PossibleQA", [])
                    ],
                )
                for group in data.get("Groups", [])
            ],
        )
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON, returning empty document object")
        return DocumentObject(groups=[GroupObject(summary="", possible_qa=[])])


def create_point(
    qa: QAObject, metadata: Dict[str, Any], full_answer: str = ""
) -> Optional[PointStruct]:
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
        "full_answer": full_answer,
    }
    return PointStruct(id=new_item_id, vector=new_item_vector, payload=new_item_payload)


def process_group(
    group: GroupObject,
    file_index: str,
    group_index: int,
    doc: DocumentObject,
    folder_path_full: str,
    is_root: bool = True,
) -> List[PointStruct]:
    points = []
    # 去除 hash 后缀，假设 file_index 形如 'xxx_xxxxxxxx'，去掉最后一个下划线及其后内容再加 .md
    if "_" in file_index:
        original_filename = "_".join(file_index.split("_")[:-1])
    else:
        original_filename = file_index
    for qa_index, qa in enumerate(group.possible_qa):
        url = f"/api/raw_file/{doc.product}/{original_filename}"
        metadata = {
            "file_index": file_index,
            "group_index": group_index,
            "question_index": qa_index if is_root else 0,
            "product": doc.product,
            "url": url,
            "title": doc.title,
            "category": doc.category,
            "summary": group.summary,
        }
        full_answer = ""
        if is_root:
            file_path = os.path.join(
                folder_path_full,
                file_index,
                f"{file_index}_{group_index}_{qa_index}.md",
            )
            if os.path.exists(file_path):
                full_answer = extract_markdown_content(read_text_from_file(file_path))
        point = create_point(qa, metadata, full_answer)
        if point:
            points.append(point)
    return points


def start_initialize_generic(context: EtlRagContext) -> None:
    root_path = context.root
    url = context.base_url
    product = context.product
    collection_name = f"generic_{product}_{context.tag}"
    client = VectorClient(url)
    client.ensure_collection_exists(collection_name)
    folder_path = os.path.join(
        root_path, f"etl_generic/.temp/outputs_embedding/{product}"
    )
    folder_path_full = os.path.join(
        root_path, f"etl_generic/.temp/outputs_generate_qa_full/{product}"
    )

    for file_path in get_file_names_in_directory(folder_path):
        logger.info(f"Processing generic document: {os.path.basename(file_path)}")
        content = read_text_from_file(file_path)
        doc = extract_object(content)
        file_index = os.path.splitext(os.path.basename(file_path))[0]
        for group_index, group in enumerate(doc.groups):
            points = process_group(
                group=group,
                file_index=file_index,
                group_index=group_index,
                doc=doc,
                folder_path_full=os.path.join(folder_path_full, product),
            )
            if points:
                client.insert_to_collection(collection_name, points)
