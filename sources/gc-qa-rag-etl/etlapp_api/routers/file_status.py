from fastapi import APIRouter
import os
import glob
import datetime
from etlapp.common.config import app_config

file_status_router = APIRouter(prefix="/api")


def get_running_task_status(filename: str, task_type: str, product: str):
    """Check if there is a running task and return its status"""

    from etlapp_api.routers.das import das_progress_status
    from etlapp_api.routers.etl import etl_progress_status
    
    if task_type == "das":
        task_prefix = f"{product}_{filename}_"
        for task_id, status in das_progress_status.items():
            if task_id.startswith(task_prefix) and status["status"] == "running":
                return "running"
    
    elif task_type in ["embedding", "qa", "full"]:
        task_prefix = f"etl_{product}_{task_type}_{filename}_"
        for task_id, status in etl_progress_status.items():
            if task_id.startswith(task_prefix) and status["status"] == "running":
                return "running"
    
    return None


@file_status_router.get("/files_status")
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
        das_result_prefix = fname
        das_result_pattern = das_result_prefix + "_*.json"
        das_result_files = glob.glob(os.path.join(das_output_dir, das_result_pattern))
        if das_result_files:
            das_status = "done"
            das_result_file = os.path.basename(das_result_files[0])
        else:
            running_status = get_running_task_status(fname, "das", product)
            das_status = running_status if running_status else "not_started"
            das_result_file = None
        etl_status = {}
        etl_result_files = {}
        for etl_type, etl_dir in etl_dirs.items():
            if etl_type == "full":
                etl_result_pattern = (
                    das_result_prefix + "_*/" + das_result_prefix + "_*.md"
                )
            else:
                etl_result_pattern = das_result_prefix + "_*.json"

            etl_result_files_list = glob.glob(os.path.join(etl_dir, etl_result_pattern))
            if etl_result_files_list:
                etl_status[etl_type] = "done"
                if etl_type == "full":
                    etl_result_files[etl_type] = (
                        os.path.basename(os.path.dirname(etl_result_files_list[0]))
                        + "/"
                        + os.path.basename(etl_result_files_list[0])
                    )
                else:
                    etl_result_files[etl_type] = os.path.basename(
                        etl_result_files_list[0]
                    )
            else:
                running_status = get_running_task_status(fname, etl_type, product)
                etl_status[etl_type] = running_status if running_status else "not_started"
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
