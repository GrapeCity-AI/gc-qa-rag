from typing import List
from http import HTTPStatus
from qdrant_client import QdrantClient, models

from etlapp.common.embedding import embedding_multiple_text

# Preview features


collection_name_map = {
    "doc": {
        "forguncy": "doc_forguncy_prod",
        "wyn": "doc_wyn_prod",
        "spreadjs": "doc_spreadjs_prod",
        "gcexcel": "doc_gcexcel_prod",
    },
    "forum_qa": {
        "forguncy": "forum_qa_forguncy_prod",
        "wyn": "forum_qa_wyn_prod",
        "spreadjs": "forum_qa_spreadjsgcexcel_prod",
        "gcexcel": "",
    },
    "forum_tutorial": {
        "forguncy": "forum_tutorial_forguncy_prod",
        "wyn": "forum_tutorial_wyn_prod",
        "spreadjs": "forum_tutorial_spreadjsgcexcel_prod",
        "gcexcel": "",
    },
}


def transform_sparse(embedding):
    return {
        "indices": [item["index"] for item in embedding],
        "values": [item["value"] for item in embedding],
    }


def get_embedding_pair(inputs: List):
    resp = embedding_multiple_text(inputs)

    if resp.status_code == HTTPStatus.OK:
        return resp.output["embeddings"][0]
    else:
        return {"embedding": [], "sparse_embedding": []}


def distinct_search_hits(hits):
    seen_ids = set()
    unique_data = []

    for hit in hits:
        key = (
            str(hit.payload["file_index"])
            + "_"
            + str(hit.payload.get("group_index", "_"))
            + "_"
            + str(hit.payload["question_index"])
        )
        if key not in seen_ids:
            seen_ids.add(key)
            unique_data.append(hit)

    return unique_data


def search_sementic_hybrid_single_pair(client: QdrantClient, pair, collection):
    dense = pair["question_dense"]
    sparse = pair["question_sparse"]

    result = client.query_points(
        collection_name=collection,
        prefetch=[
            models.Prefetch(
                query=dense, using="question_dense", limit=20, score_threshold=0.4
            ),
            models.Prefetch(
                query=dense, using="answer_dense", limit=20, score_threshold=0.4
            ),
            models.Prefetch(
                query=models.SparseVector(indices=sparse.indices, values=sparse.values),
                using="question_sparse",
                limit=20,
            ),
            models.Prefetch(
                query=models.SparseVector(indices=sparse.indices, values=sparse.values),
                using="answer_sparse",
                limit=20,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=8,
        score_threshold=0.4,
    )
    return distinct_search_hits(result.points)
