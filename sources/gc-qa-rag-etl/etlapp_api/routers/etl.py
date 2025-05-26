from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import os
import sys
import threading
import time
import json
from etlapp.common.config import app_config

etl_router = APIRouter(prefix="/api")

etl_progress_status = {}

@etl_router.post("/etl_start")
def etl_start_execution(
    product: str = Form(...),
    etl_type: str = Form(...),  # embedding, qa, full
):
    import subprocess

    task_id = f"etl_{product}_{etl_type}_{int(time.time())}"
    etl_progress_status[task_id] = {"status": "running", "progress": 0, "msg": ""}

    def run_etl_task():
        try:
            etl_progress_status[task_id]["msg"] = f"ETL-{etl_type} started"
            if etl_type == "embedding":
                mode = "none"
            elif etl_type == "qa":
                mode = "none"
            elif etl_type == "full":
                mode = "full"
            else:
                etl_progress_status[task_id]["status"] = "error"
                etl_progress_status[task_id]["msg"] = f"Unknown etl_type: {etl_type}"
                return
            cmd = [
                sys.executable,
                "-m",
                "etlapp.etl_index",
                "--doc_type",
                "generic",
                "--product",
                product,
                "--mode",
                mode,
                "--parallel_count",
                "1",
            ]
            subprocess.run(cmd, check=True)
            etl_progress_status[task_id]["status"] = "done"
            etl_progress_status[task_id]["progress"] = 100
            etl_progress_status[task_id]["msg"] = f"ETL-{etl_type} finished"
        except Exception as e:
            etl_progress_status[task_id]["status"] = "error"
            etl_progress_status[task_id]["msg"] = str(e)

    threading.Thread(target=run_etl_task, daemon=True).start()
    return {"task_id": task_id}

@etl_router.get("/etl_result_content")
def etl_get_result_content(product: str, etl_type: str, filename: str):
    if etl_type == "embedding":
        output_dir = os.path.join(
            app_config.root_path, f"etl_generic/.temp/outputs_embedding/{product}"
        )
    elif etl_type == "qa":
        output_dir = os.path.join(
            app_config.root_path, f"etl_generic/.temp/outputs_generate_qa/{product}"
        )
    elif etl_type == "full":
        output_dir = os.path.join(
            app_config.root_path,
            f"etl_generic/.temp/outputs_generate_qa_full/{product}",
        )
    else:
        return JSONResponse(status_code=400, content={"error": "Unknown etl_type"})
    file_path = os.path.join(output_dir, filename)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)
    return content 