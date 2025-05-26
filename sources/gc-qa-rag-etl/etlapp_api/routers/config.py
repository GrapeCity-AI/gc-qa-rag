from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from etlapp.common.config import app_config
import json
from pathlib import Path

config_router = APIRouter(prefix="/generic")

@config_router.get("/get_config")
def get_config_api():
    def dataclass_to_dict(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: dataclass_to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {k: dataclass_to_dict(v) for k, v in obj.items()}
        else:
            return obj
    return dataclass_to_dict(app_config)

@config_router.post("/update_config")
async def update_config_api(request: Request):
    data = await request.json()
    config_path = Path(f".config.{app_config.environment}.json")
    if not config_path.exists():
        return JSONResponse(status_code=404, content={"error": "Config file not found"})
    with open(config_path, "r", encoding="utf-8") as f:
        config_raw = json.load(f)
    for key in ["llm", "embedding", "vector_db", "root_path", "log_path"]:
        if key in data:
            config_raw[key] = data[key]
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_raw, f, ensure_ascii=False, indent=4)
    return {"msg": "Config updated"} 