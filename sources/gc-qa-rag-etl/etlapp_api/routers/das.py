from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import shutil
import threading
import time
import json
from etlapp.common.file import ensure_folder_exists
from etlapp.common.config import app_config
from etlapp.das.das_generic import das_generic_main

das_router = APIRouter(prefix="/api")

das_progress_status = {}

def das_generic_single_file(product: str, filename: str):
    """Process a single file with DAS for the given product."""
    from etlapp.das.das_generic import collect_files, process_files
    from markitdown import MarkItDown
    
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    output_dir = os.path.join(app_config.root_path, f"das/.temp/generic_output/{product}")
    
    ensure_folder_exists(input_dir)
    ensure_folder_exists(output_dir)
    
    # Check if the specific file exists
    file_path = os.path.join(input_dir, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {filename} not found in {input_dir}")
    
    # Process only the specific file
    rel_path = filename  # Since it's directly in the input_dir
    files = [(file_path, rel_path)]
    
    markitdown_inst = MarkItDown()
    process_files(product, files, markitdown_inst, output_dir)

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
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Product already exists")
    ensure_folder_exists(input_dir)
    return {"msg": "Product created", "product": product} 