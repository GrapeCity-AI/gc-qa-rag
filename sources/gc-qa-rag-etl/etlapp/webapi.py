from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import threading
import time
import json
from typing import List
from etlapp.common.file import ensure_folder_exists
from etlapp.common.config import app_config
from etlapp.das.das_generic import das_generic_main

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Generic ETL API Router ---
generic_router = APIRouter(prefix="/generic")

# 用于简单进度追踪（生产建议用 redis/db）
progress_status = {}

@generic_router.post("/upload")
async def upload_file(product: str = Form(...), file: UploadFile = File(...)):
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    ensure_folder_exists(input_dir)
    file_path = os.path.join(input_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": file.filename}

@generic_router.get("/files")
def list_files(product: str):
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    if not os.path.exists(input_dir):
        return {"files": []}
    files = os.listdir(input_dir)
    return {"files": files}

@generic_router.post("/start_etl")
def start_etl(product: str = Form(...)):
    task_id = f"{product}_{int(time.time())}"
    progress_status[task_id] = {"status": "running", "progress": 0, "msg": ""}

    def run_etl_task():
        try:
            progress_status[task_id]["msg"] = "ETL started"
            das_generic_main(product)
            progress_status[task_id]["status"] = "done"
            progress_status[task_id]["progress"] = 100
            progress_status[task_id]["msg"] = "ETL finished"
        except Exception as e:
            progress_status[task_id]["status"] = "error"
            progress_status[task_id]["msg"] = str(e)

    threading.Thread(target=run_etl_task, daemon=True).start()
    return {"task_id": task_id}

@generic_router.get("/progress/{task_id}")
def get_progress(task_id: str):
    return progress_status.get(task_id, {"status": "not_found"})

@generic_router.get("/results")
def list_results(product: str):
    output_dir = os.path.join(app_config.root_path, f"das/.temp/generic_output/{product}")
    if not os.path.exists(output_dir):
        return {"files": []}
    files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    return {"files": files}

@generic_router.get("/result_content")
def get_result_content(product: str, filename: str):
    output_dir = os.path.join(app_config.root_path, f"das/.temp/generic_output/{product}")
    file_path = os.path.join(output_dir, filename)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)
    return content

app.include_router(generic_router)