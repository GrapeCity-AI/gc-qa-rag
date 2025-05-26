from fastapi import APIRouter, Form
import threading
import time
from etlapp.ved_index import ved_index_start

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