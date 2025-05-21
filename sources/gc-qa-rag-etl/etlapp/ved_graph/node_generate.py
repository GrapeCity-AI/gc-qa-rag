import os
import json
from qdrant_client import QdrantClient

from etlapp.ved_graph.node_search import search_sementic_hybrid_single_pair
from etlapp.common.config import app_config

# Preview features


def start_generate_node():
    client = QdrantClient(url=app_config.vector_db.host)
    product = "forguncy"
    collection_name = f"doc_{product}_collection_qa_sub_category_v3"

    current_offset = 0
    while current_offset is not None:
        fetch_result = client.scroll(
            collection_name=collection_name,
            with_vectors=True,
            limit=100,
            offset=current_offset,
        )

        points = fetch_result[0]
        print("points:" + str(len(points)))

        objs = []

        for point in points:
            pair = point.vector
            hits = search_sementic_hybrid_single_pair(client, pair, collection_name)
            obj = {"id": point.id, "payload": point.payload, "hits": hits}
            objs.append(obj)

        file_path_r = os.path.join(
            app_config.root_path,
            f"ved_graph/.temp/{product}/{str(current_offset)}.json",
        )
        file = open(file_path_r, "w")
        file.write(json.dumps(objs, ensure_ascii=False, default=vars))
        file.close()

        current_offset = fetch_result[1]
