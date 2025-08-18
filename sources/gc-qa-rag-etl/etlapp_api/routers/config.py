from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import json
from pathlib import Path

config_router = APIRouter(prefix="/api")


@config_router.get("/get_config")
def get_config_api():
    def dataclass_to_dict(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: dataclass_to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {k: dataclass_to_dict(v) for k, v in obj.items()}
        else:
            return obj

    from etlapp.common.config import app_config

    return dataclass_to_dict(app_config)


@config_router.post("/update_config")
async def update_config_api(request: Request):
    try:
        data = await request.json()
        from etlapp.common.config import app_config

        # 创建保存的配置文件路径
        saved_config_path = Path(f".config.{app_config.environment}.saved.json")
        
        # 如果保存的配置文件已存在，先加载现有内容
        saved_config_raw = {}
        if saved_config_path.exists():
            try:
                with open(saved_config_path, "r", encoding="utf-8") as f:
                    saved_config_raw = json.load(f)
            except json.JSONDecodeError:
                # 如果文件损坏，从空配置开始
                saved_config_raw = {}

        # 更新配置数据
        for key in ["llm", "embedding", "vector_db", "root_path", "log_path", "das"]:
            if key in data:
                saved_config_raw[key] = data[key]

        # 写入保存的配置文件
        with open(saved_config_path, "w", encoding="utf-8") as f:
            json.dump(saved_config_raw, f, ensure_ascii=False, indent=4)

        # 重新加载配置
        from etlapp.common.config import reload_config
        reload_config()

        return {
            "msg": "Config updated successfully",
            "saved_to": str(saved_config_path),
            "note": "Configuration has been saved to .saved.json file with highest priority"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": f"Failed to update configuration: {str(e)}"}
        )


@config_router.delete("/reset_config")
async def reset_config_api():
    """删除保存的配置文件，恢复到默认配置优先级"""
    try:
        from etlapp.common.config import app_config
        
        saved_config_path = Path(f".config.{app_config.environment}.saved.json")
        
        if saved_config_path.exists():
            saved_config_path.unlink()  # 删除文件
            
            # 重新加载配置
            from etlapp.common.config import reload_config
            reload_config()
            
            return {
                "msg": "Saved configuration reset successfully",
                "deleted_file": str(saved_config_path),
                "note": "Configuration priority has been restored to: ENV > .env > JSON"
            }
        else:
            return {
                "msg": "No saved configuration file found",
                "note": "Already using default configuration priority"
            }
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to reset configuration: {str(e)}"}
        )
