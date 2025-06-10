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

def etl_process_single_file(product: str, etl_type: str, filename: str):
    """Process a single file with ETL for the given product."""
    from etlapp.common.context import EtlContext
    from etlapp.etl.flow import etl_generic_embedding_flow, etl_generic_full_flow
    from etlapp.etl.etl_generic.generate import start_generate_generic
    
    # Remove file extension to get the base filename
    file_base = os.path.splitext(filename)[0]
    
    # Create ETL context for the specific file
    context = EtlContext(
        root_path=app_config.root_path,
        doc_type="generic",
        product=product,
        index=file_base
    )
    
    # Choose the appropriate processing function based on etl_type
    if etl_type == "qa":
        # QA generation only
        start_generate_generic(context)
    elif etl_type == "embedding":
        # Full embedding flow (generate, merge, embedding)
        etl_generic_embedding_flow(context)
    elif etl_type == "full":
        # Full answer generation
        etl_generic_full_flow(context)
    else:
        raise ValueError(f"Unknown etl_type: {etl_type}")

@etl_router.post("/etl_start")
def etl_start_execution(
    product: str = Form(...),
    etl_type: str = Form(...),  # embedding, qa, full
    filename: str = Form(...),
):
    import subprocess

    task_id = f"etl_{product}_{etl_type}_{filename}_{int(time.time())}"
    etl_progress_status[task_id] = {"status": "running", "progress": 0, "msg": ""}

    def run_etl_task():
        try:
            etl_progress_status[task_id]["msg"] = f"ETL-{etl_type} started for {filename}"
            etl_process_single_file(product, etl_type, filename)
            etl_progress_status[task_id]["status"] = "done"
            etl_progress_status[task_id]["progress"] = 100
            etl_progress_status[task_id]["msg"] = f"ETL-{etl_type} finished for {filename}"
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