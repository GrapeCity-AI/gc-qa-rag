from fastapi import APIRouter, Form
import threading
import time
from etlapp.ved_index import ved_index_start, ved_update_collections_aliases_by_product
from etlapp.common.vector import create_vector_client_from_config
from etlapp.common.config import app_config
import logging

logger = logging.getLogger(__name__)

das_progress_status = {}

publish_router = APIRouter(prefix="/api")

@publish_router.post("/publish")
def publish_to_vector_db(product: str = Form(...), tag: str = Form(...)):
    task_id = f"publish_{product}_{tag}_{int(time.time())}"
    das_progress_status[task_id] = {"status": "running", "progress": 0, "msg": ""}

    def run_publish_task():
        try:
            das_progress_status[task_id]["msg"] = "Publishing started"
            ved_index_start("generic", product, tag)
            das_progress_status[task_id]["status"] = "done"
            das_progress_status[task_id]["progress"] = 100
            das_progress_status[task_id]["msg"] = "Publishing finished"
        except Exception as e:
            das_progress_status[task_id]["status"] = "error"
            das_progress_status[task_id]["msg"] = str(e)

    threading.Thread(target=run_publish_task, daemon=True).start()
    return {"task_id": task_id}

@publish_router.post("/update_aliases")
def update_aliases(product: str = Form(...), tag: str = Form(...)):
    task_id = f"update_aliases_{product}_{tag}_{int(time.time())}"
    das_progress_status[task_id] = {"status": "running", "progress": 0, "msg": ""}

    def run_update_aliases_task():
        try:
            das_progress_status[task_id]["msg"] = f"Updating aliases for {product} started"
            ved_update_collections_aliases_by_product(product, tag)
            das_progress_status[task_id]["status"] = "done"
            das_progress_status[task_id]["progress"] = 100
            das_progress_status[task_id]["msg"] = f"Aliases updated successfully for {product}"
        except Exception as e:
            das_progress_status[task_id]["status"] = "error"
            das_progress_status[task_id]["msg"] = str(e)

    threading.Thread(target=run_update_aliases_task, daemon=True).start()
    return {"task_id": task_id}

@publish_router.get("/publish_progress")
def get_progress(task_id: str):
    return das_progress_status.get(task_id, {"status": "not_found", "progress": 0, "msg": "Task not found"})

@publish_router.get("/vector_collections")
def get_vector_collections():
    """Get information about all collections and aliases from vector database."""
    try:
        if not app_config.vector_db.host:
            return {"error": "向量数据库URL未配置"}
        
        client = create_vector_client_from_config()
        
        # 获取collections信息
        collections = client.get_collections_info()
        
        # 获取aliases信息
        aliases = client.get_collection_aliases()
        
        return {
            "collections": collections,
            "aliases": aliases
        }
    except Exception as e:
        logger.error(f"Failed to get vector collections info: {str(e)}")
        return {"error": f"获取向量数据库信息失败: {str(e)}"} 