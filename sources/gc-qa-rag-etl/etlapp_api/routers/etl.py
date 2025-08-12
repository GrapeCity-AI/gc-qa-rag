from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from etlapp.common.config import app_config
from etlapp.common.file import read_text_from_file

etl_router = APIRouter(prefix="/api")

etl_progress_status = {}

# 单独存储future对象（避免JSON序列化问题）
etl_task_futures = {}

# 线程池配置：限制并发ETL任务数量
MAX_CONCURRENT_ETL_TASKS = 5  # 最多5个并发ETL任务
etl_thread_pool = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_ETL_TASKS, thread_name_prefix="ETL-Worker")

print(f"🔧 [ETL-INIT] ETL thread pool initialized with max {MAX_CONCURRENT_ETL_TASKS} concurrent tasks")


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
        index=file_base,
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
    # 检查配置完整性
    config_errors = []

    # 检查LLM配置
    if not app_config.llm.api_key:
        config_errors.append("LLM API密钥未配置")
    if not app_config.llm.api_base:
        config_errors.append("LLM API基础地址未配置")
    if not app_config.llm.model_name:
        config_errors.append("LLM模型名称未配置")

    # 检查Embedding配置
    if not app_config.embedding.api_key:
        config_errors.append("Embedding API密钥未配置")

    # 如果有配置错误，返回错误信息
    if config_errors:
        return JSONResponse(
            status_code=400,
            content={"error": "配置不完整", "details": config_errors}
        )

    task_id = f"etl_{product}_{etl_type}_{filename}_{int(time.time())}"

    # 检查当前排队的任务数
    queued_tasks = sum(1 for status in etl_progress_status.values()
                      if status["status"] in ["queued", "running"])

    # 初始化任务状态
    if queued_tasks >= MAX_CONCURRENT_ETL_TASKS:
        etl_progress_status[task_id] = {
            "status": "queued",
            "progress": 0,
            "msg": f"Task queued (position: {queued_tasks - MAX_CONCURRENT_ETL_TASKS + 1})"
        }
        print(f"🚦 [ETL-QUEUE] Task {task_id} queued, {queued_tasks} tasks ahead")
    else:
        etl_progress_status[task_id] = {
            "status": "running",
            "progress": 0,
            "msg": f"ETL-{etl_type} starting for {filename}"
        }
        print(f"🚀 [ETL-START] Task {task_id} starting immediately")

    def run_etl_task():
        try:
            # 更新状态为正在运行
            etl_progress_status[task_id]["status"] = "running"
            etl_progress_status[task_id]["msg"] = f"ETL-{etl_type} processing {filename}"
            print(f"🔄 [ETL-WORKER] Starting {etl_type} processing for {filename}")

            # 执行实际的ETL任务
            etl_process_single_file(product, etl_type, filename)

            # 成功完成
            etl_progress_status[task_id]["status"] = "done"
            etl_progress_status[task_id]["progress"] = 100
            etl_progress_status[task_id]["msg"] = f"ETL-{etl_type} completed for {filename}"
            print(f"✅ [ETL-WORKER] Completed {etl_type} processing for {filename}")

        except Exception as e:
            etl_progress_status[task_id]["status"] = "error"
            etl_progress_status[task_id]["msg"] = f"ETL-{etl_type} failed for {filename}: {str(e)}"
            print(f"❌ [ETL-WORKER] Failed {etl_type} processing for {filename}: {str(e)}")

    # 使用线程池提交任务而不是直接创建线程
    future = etl_thread_pool.submit(run_etl_task)

    # 单独存储future引用（避免JSON序列化问题）
    etl_task_futures[task_id] = future

    return {"task_id": task_id}


@etl_router.get("/etl_stats")
def etl_get_stats():
    """获取ETL系统的整体状态统计"""
    active_tasks = sum(1 for status in etl_progress_status.values()
                      if status["status"] == "running")
    queued_tasks = sum(1 for status in etl_progress_status.values()
                      if status["status"] == "queued")
    completed_tasks = sum(1 for status in etl_progress_status.values()
                         if status["status"] == "done")
    failed_tasks = sum(1 for status in etl_progress_status.values()
                      if status["status"] == "error")

    return {
        "thread_pool": {
            "max_workers": MAX_CONCURRENT_ETL_TASKS,
            "active_threads": etl_thread_pool._threads if hasattr(etl_thread_pool, '_threads') else 0,
        },
        "tasks": {
            "active": active_tasks,
            "queued": queued_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks,
            "total": len(etl_progress_status)
        }
    }


@etl_router.post("/etl_cleanup_completed")
def etl_cleanup_completed_tasks():
    """清理已完成的ETL任务状态，释放内存"""
    initial_count = len(etl_progress_status)

    # 清理已完成或失败的任务（保留最近的50个）
    completed_tasks = [(task_id, status) for task_id, status in etl_progress_status.items()
                      if status["status"] in ["done", "error"]]

    if len(completed_tasks) > 50:
        # 按任务ID排序（包含时间戳），保留最新的50个
        completed_tasks.sort(key=lambda x: x[0])
        tasks_to_remove = completed_tasks[:-50]

        for task_id, _ in tasks_to_remove:
            # 清理future引用
            if task_id in etl_task_futures:
                del etl_task_futures[task_id]
            del etl_progress_status[task_id]

    cleaned_count = initial_count - len(etl_progress_status)
    print(f"🧹 [ETL-CLEANUP] Cleaned up {cleaned_count} completed tasks")

    return {
        "message": f"Cleaned up {cleaned_count} completed tasks",
        "remaining_tasks": len(etl_progress_status)
    }


@etl_router.post("/etl_config")
def etl_update_config(max_concurrent_tasks: int = Form(5)):
    """动态调整ETL并发任务数量限制"""
    global MAX_CONCURRENT_ETL_TASKS, etl_thread_pool

    if max_concurrent_tasks < 1 or max_concurrent_tasks > 20:
        return JSONResponse(
            status_code=400,
            content={"error": "max_concurrent_tasks must be between 1 and 20"}
        )

    old_limit = MAX_CONCURRENT_ETL_TASKS
    MAX_CONCURRENT_ETL_TASKS = max_concurrent_tasks

    # 注意：ThreadPoolExecutor不支持动态调整，需要重启服务生效
    print(f"⚙️ [ETL-CONFIG] Updated max concurrent tasks from {old_limit} to {max_concurrent_tasks}")
    print("ℹ️ [ETL-CONFIG] Note: This change requires service restart to take full effect")

    return {
        "message": f"Updated max concurrent tasks to {max_concurrent_tasks} (restart required)",
        "old_limit": old_limit,
        "new_limit": max_concurrent_tasks
    }


@etl_router.get("/etl_progress")
def etl_get_progress(task_id: str):
    if task_id not in etl_progress_status:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return etl_progress_status[task_id]


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

    return read_text_from_file(file_path)
