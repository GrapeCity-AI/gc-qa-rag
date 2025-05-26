from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
import threading
import time
import json
from etlapp.common.file import ensure_folder_exists
from etlapp.common.config import app_config
from etlapp.das.das_generic import das_generic_main
import sys
import glob
import datetime
from etlapp.ved_index import ved_index_start
import tailer

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

# For simple progress tracking (Redis/DB recommended for production)

# --- DAS processing related ---

das_progress_status = {}


@generic_router.post("/das_upload")
async def das_upload_file(product: str = Form(...), file: UploadFile = File(...)):
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    ensure_folder_exists(input_dir)
    file_path = os.path.join(input_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": file.filename}


@generic_router.get("/das_files")
def das_list_files(product: str):
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    if not os.path.exists(input_dir):
        return {"files": []}
    files = os.listdir(input_dir)
    return {"files": files}


@generic_router.post("/das_start")
def das_start_execution(product: str = Form(...)):
    task_id = f"{product}_{int(time.time())}"
    das_progress_status[task_id] = {"status": "running", "progress": 0, "msg": ""}

    def run_etl_task():
        try:
            das_progress_status[task_id]["msg"] = "ETL started"
            das_generic_main(product)
            das_progress_status[task_id]["status"] = "done"
            das_progress_status[task_id]["progress"] = 100
            das_progress_status[task_id]["msg"] = "ETL finished"
        except Exception as e:
            das_progress_status[task_id]["status"] = "error"
            das_progress_status[task_id]["msg"] = str(e)

    threading.Thread(target=run_etl_task, daemon=True).start()
    return {"task_id": task_id}


@generic_router.get("/das_result_content")
def das_get_result_content(product: str, filename: str):
    output_dir = os.path.join(
        app_config.root_path, f"das/.temp/generic_output/{product}"
    )
    file_path = os.path.join(output_dir, filename)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)
    return content


@generic_router.get("/products")
def list_products():
    input_root = os.path.join(app_config.root_path, "das/.temp/generic_input")
    if not os.path.exists(input_root):
        ensure_folder_exists(input_root)
    # only list folders
    products = [
        name
        for name in os.listdir(input_root)
        if os.path.isdir(os.path.join(input_root, name))
    ]
    return {"products": sorted(list(products))}


@generic_router.post("/create_product")
def create_product(product: str = Form(...)):
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    if os.path.exists(input_dir):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Product already exists")
    ensure_folder_exists(input_dir)
    return {"msg": "Product created", "product": product}


# --- ETL processing related ---

etl_progress_status = {}


@generic_router.post("/etl_start")
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


@generic_router.get("/etl_result_content")
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


# --- File status related ---


@generic_router.get("/files_status")
def files_status(product: str):
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    das_output_dir = os.path.join(
        app_config.root_path, f"das/.temp/generic_output/{product}"
    )
    etl_dirs = {
        "embedding": os.path.join(
            app_config.root_path, f"etl_generic/.temp/outputs_embedding/{product}"
        ),
        "qa": os.path.join(
            app_config.root_path, f"etl_generic/.temp/outputs_generate_qa/{product}"
        ),
        "full": os.path.join(
            app_config.root_path,
            f"etl_generic/.temp/outputs_generate_qa_full/{product}",
        ),
    }
    if not os.path.exists(input_dir):
        return {"files": []}
    files = os.listdir(input_dir)
    result = []
    for fname in files:
        file_path = os.path.join(input_dir, fname)
        if not os.path.isfile(file_path):
            continue
        upload_time = datetime.datetime.fromtimestamp(
            os.path.getmtime(file_path)
        ).strftime("%Y-%m-%d %H:%M:%S")
        # DAS 状态
        das_result_prefix = fname
        das_result_pattern = das_result_prefix + "_*.json"
        das_result_files = glob.glob(os.path.join(das_output_dir, das_result_pattern))
        if das_result_files:
            das_status = "done"
            das_result_file = os.path.basename(das_result_files[0])
        else:
            das_status = "not_started"
            das_result_file = None
        # ETL 各阶段
        etl_status = {}
        etl_result_files = {}
        for etl_type, etl_dir in etl_dirs.items():
            etl_result_pattern = das_result_prefix + "_*.json"
            etl_result_files_list = glob.glob(os.path.join(etl_dir, etl_result_pattern))
            if etl_result_files_list:
                etl_status[etl_type] = "done"
                etl_result_files[etl_type] = os.path.basename(etl_result_files_list[0])
            else:
                etl_status[etl_type] = "not_started"
                etl_result_files[etl_type] = None
        result.append(
            {
                "filename": fname,
                "uploadTime": upload_time,
                "das": {
                    "status": das_status,
                    "resultFile": das_result_file,
                },
                "embedding": {
                    "status": etl_status["embedding"],
                    "resultFile": etl_result_files["embedding"],
                },
                "qa": {
                    "status": etl_status["qa"],
                    "resultFile": etl_result_files["qa"],
                },
                "full": {
                    "status": etl_status["full"],
                    "resultFile": etl_result_files["full"],
                },
            }
        )
    return {"files": result}


# --- Publish related ---


@generic_router.post("/publish")
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


@generic_router.get("/server_log")
def get_server_log(lines: int = 100):
    """
    返回 app.log 的最后 N 行
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(app_config.log_path, ".logs", today, "app.log")
    if not os.path.exists(log_path):
        return {"log": ""}
    with open(log_path, "r", encoding="utf-8") as f:
        last_lines = tailer.tail(f, lines)
    return {"log": "\n".join(last_lines)}


app.include_router(generic_router)

# --- Static files ---

# Mount static files
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    # Mount assets directory separately to handle JS/CSS files
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(static_path, "assets")),
        name="assets",
    )
    # Mount root path for HTML files
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
