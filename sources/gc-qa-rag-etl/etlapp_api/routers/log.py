from fastapi import APIRouter
import os
import datetime
from etlapp.common.config import app_config
import tailer

log_router = APIRouter(prefix="/api")

@log_router.get("/server_log")
def get_server_log(lines: int = 100, max_line_length: int = 1000):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(app_config.log_path, ".logs", today, "app.log")
    if not os.path.exists(log_path):
        return {"log": ""}
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        last_lines = tailer.tail(f, lines)
    # 截断过长的行以防止内存溢出
    truncated_lines = [
        line[:max_line_length] + "..." if len(line) > max_line_length else line
        for line in last_lines
    ]
    return {"log": "\n".join(truncated_lines)} 