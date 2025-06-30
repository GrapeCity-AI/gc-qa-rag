from fastapi import APIRouter
import os
import glob
import datetime
import shutil
from fastapi import Form
from fastapi.responses import JSONResponse
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


@file_status_router.delete("/delete_file")
def delete_file(product: str, filename: str):
    """删除单个文件及其所有相关的处理结果"""
    try:
        # 删除原始文件
        input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
        input_file = os.path.join(input_dir, filename)
        if os.path.exists(input_file):
            os.remove(input_file)
        
        # 删除DAS输出文件
        das_output_dir = os.path.join(app_config.root_path, f"das/.temp/generic_output/{product}")
        file_base = filename
        das_pattern = os.path.join(das_output_dir, f"{file_base}_*.json")
        for file_path in glob.glob(das_pattern):
            os.remove(file_path)
        
        # 删除ETL输出文件
        etl_dirs = {
            "embedding": f"etl_generic/.temp/outputs_embedding/{product}",
            "qa": f"etl_generic/.temp/outputs_generate_qa/{product}",
            "full": f"etl_generic/.temp/outputs_generate_qa_full/{product}"
        }
        
        for etl_type, etl_dir_path in etl_dirs.items():
            etl_dir = os.path.join(app_config.root_path, etl_dir_path)
            if etl_type == "full":
                # full类型的文件存储在子目录中
                pattern = os.path.join(etl_dir, f"{file_base}_*")
                for dir_path in glob.glob(pattern):
                    if os.path.isdir(dir_path):
                        shutil.rmtree(dir_path)
            else:
                pattern = os.path.join(etl_dir, f"{file_base}_*.json")
                for file_path in glob.glob(pattern):
                    os.remove(file_path)
        
        return {"message": f"文件 {filename} 及其所有处理结果已删除"}
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"删除文件失败: {str(e)}"}
        )


@file_status_router.post("/delete_files")
def delete_files(product: str = Form(...), filenames: str = Form(...)):
    """批量删除文件及其所有相关的处理结果"""
    try:
        # 解析文件名列表
        filename_list = filenames.split(",")
        deleted_files = []
        failed_files = []
        
        for filename in filename_list:
            filename = filename.strip()
            if not filename:
                continue
                
            try:
                # 删除原始文件
                input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
                input_file = os.path.join(input_dir, filename)
                if os.path.exists(input_file):
                    os.remove(input_file)
                
                # 删除DAS输出文件
                das_output_dir = os.path.join(app_config.root_path, f"das/.temp/generic_output/{product}")
                file_base = filename
                das_pattern = os.path.join(das_output_dir, f"{file_base}_*.json")
                for file_path in glob.glob(das_pattern):
                    os.remove(file_path)
                
                # 删除ETL输出文件
                etl_dirs = {
                    "embedding": f"etl_generic/.temp/outputs_embedding/{product}",
                    "qa": f"etl_generic/.temp/outputs_generate_qa/{product}",
                    "full": f"etl_generic/.temp/outputs_generate_qa_full/{product}"
                }
                
                for etl_type, etl_dir_path in etl_dirs.items():
                    etl_dir = os.path.join(app_config.root_path, etl_dir_path)
                    if etl_type == "full":
                        # full类型的文件存储在子目录中
                        pattern = os.path.join(etl_dir, f"{file_base}_*")
                        for dir_path in glob.glob(pattern):
                            if os.path.isdir(dir_path):
                                shutil.rmtree(dir_path)
                    else:
                        pattern = os.path.join(etl_dir, f"{file_base}_*.json")
                        for file_path in glob.glob(pattern):
                            os.remove(file_path)
                
                deleted_files.append(filename)
                
            except Exception as e:
                failed_files.append({"filename": filename, "error": str(e)})
        
        result = {"deleted": deleted_files}
        if failed_files:
            result["failed"] = failed_files
        
        return result
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"批量删除失败: {str(e)}"}
        )
