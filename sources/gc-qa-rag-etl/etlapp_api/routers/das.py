from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse, Response
import os
import shutil
import threading
import time
import json
from etlapp.common.file import ensure_folder_exists
from etlapp.common.config import app_config
from etlapp.das.das_generic import das_generic_single_file
from fastapi import HTTPException

das_router = APIRouter(prefix="/api")

das_progress_status = {}

@das_router.post("/das_upload")
async def das_upload_file(product: str = Form(...), file: UploadFile = File(...)):
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    ensure_folder_exists(input_dir)
    file_path = os.path.join(input_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": file.filename}

@das_router.get("/das_files")
def das_list_files(product: str):
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    if not os.path.exists(input_dir):
        return {"files": []}
    files = os.listdir(input_dir)
    return {"files": files}

@das_router.post("/das_start")
def das_start_execution(product: str = Form(...), filename: str = Form(...)):
    task_id = f"{product}_{filename}_{int(time.time())}"
    das_progress_status[task_id] = {"status": "running", "progress": 0, "msg": ""}

    def run_etl_task():
        try:
            das_progress_status[task_id]["msg"] = f"DAS started for {filename}"
            das_generic_single_file(product, filename)
            das_progress_status[task_id]["status"] = "done"
            das_progress_status[task_id]["progress"] = 100
            das_progress_status[task_id]["msg"] = f"DAS finished for {filename}"
        except Exception as e:
            das_progress_status[task_id]["status"] = "error"
            das_progress_status[task_id]["msg"] = str(e)

    threading.Thread(target=run_etl_task, daemon=True).start()
    return {"task_id": task_id}

@das_router.get("/das_progress")
def das_get_progress(task_id: str):
    if task_id not in das_progress_status:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return das_progress_status[task_id]

@das_router.get("/das_result_content")
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

@das_router.get("/raw_file/{product}/{filename:path}")
def get_raw_file(product: str, filename: str):
    # 只允许访问 generic_input/{product}/ 下的文件, 防止目录穿越
    output_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    file_path = os.path.abspath(os.path.join(output_dir, filename))
    # 校验路径必须在 output_dir 下
    if not file_path.startswith(os.path.abspath(output_dir)):
        raise HTTPException(status_code=403, detail="非法路径")
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 根据扩展名确定媒体类型
    ext = os.path.splitext(file_path)[1].lower()
    media_type_map = {
        ".md": "text/markdown",
        ".markdown": "text/markdown",
        ".json": "application/json",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".ppt": "application/vnd.ms-powerpoint",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".csv": "text/csv",
        ".xml": "application/xml",
        ".html": "text/html",
        ".htm": "text/html",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")

    # 文本类型使用文本模式读取，其他使用二进制模式
    text_extensions = {".md", ".markdown", ".json", ".txt", ".csv", ".xml", ".html", ".htm"}
    if ext in text_extensions:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return PlainTextResponse(content, media_type=media_type)
    else:
        # 二进制文件直接返回 FileResponse
        return FileResponse(file_path, media_type=media_type, filename=os.path.basename(file_path))

@das_router.get("/products")
def list_products():
    input_root = os.path.join(app_config.root_path, "das/.temp/generic_input")
    if not os.path.exists(input_root):
        ensure_folder_exists(input_root)
    products = [
        name
        for name in os.listdir(input_root)
        if os.path.isdir(os.path.join(input_root, name))
    ]
    return {"products": sorted(list(products))}

@das_router.post("/create_product")
def create_product(product: str = Form(...)):
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    if os.path.exists(input_dir):
        raise HTTPException(status_code=400, detail="Product already exists")
    ensure_folder_exists(input_dir)
    return {"msg": "Product created", "product": product}