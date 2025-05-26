from fastapi import APIRouter
import os
import datetime
from etlapp.common.config import app_config
import tailer

log_router = APIRouter(prefix="/generic")

@log_router.get("/server_log")
def get_server_log(lines: int = 100):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(app_config.log_path, ".logs", today, "app.log")
    if not os.path.exists(log_path):
        return {"log": ""}
    with open(log_path, "r", encoding="utf-8") as f:
        last_lines = tailer.tail(f, lines)
    return {"log": "\n".join(last_lines)} 