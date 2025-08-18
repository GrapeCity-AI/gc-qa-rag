import os
import json
from typing import Optional, Union
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from platformdirs import user_cache_dir, user_log_dir


@dataclass
class DasConfig:
    base_url_page: str
    base_url_thread: str
    token: str


@dataclass
class LlmConfig:
    api_key: str
    api_base: str
    model_name: str
    max_rpm: int = 100  # Maximum requests per minute, default 100


@dataclass
class EmbeddingConfig:
    api_key: str


@dataclass
class VectorDbConfig:
    host: str


def _get_config_value(key: str, config_raw: dict, saved_config_raw: dict, default: Optional[str] = None) -> str:
    """
    Get configuration value with priority: saved.json > ENV > .env > JSON.
    
    Key format: GC_QA_RAG.SECTION.FIELD (e.g., GC_QA_RAG.LLM.API_KEY)
    - For JSON: uses dot notation to navigate nested structure
    - For ENV: converts dots to underscores (GC_QA_RAG_LLM_API_KEY)
    """
    
    def _get_value_from_json(config_dict: dict, dot_key: str) -> Optional[str]:
        """Navigate JSON structure using dot notation."""
        if not config_dict:
            return None
        
        # Remove GC_QA_RAG prefix and split by dots
        if dot_key.startswith("GC_QA_RAG."):
            path = dot_key[10:].split('.')  # Remove "GC_QA_RAG." prefix
        else:
            path = dot_key.split('.')
        
        current = config_dict
        try:
            for key_part in path:
                current = current[key_part.lower()]
            return str(current)
        except (KeyError, TypeError):
            return None
    
    # 1. Check saved config first (highest priority)
    saved_value = _get_value_from_json(saved_config_raw, key)
    if saved_value is not None:
        return saved_value
    
    # 2. Then check environment variables (convert dots to underscores)
    env_key = key.replace('.', '_').upper()
    env_value = os.getenv(env_key)
    if env_value is not None:
        return env_value
    
    # 3. Then check JSON config
    json_value = _get_value_from_json(config_raw, key)
    if json_value is not None:
        return json_value
    
    # 4. Return default if provided
    if default is not None:
        return default
    
    raise ValueError(f"Configuration value not found for key: {key}")


def _get_config_int(key: str, config_raw: dict, saved_config_raw: dict, default: Optional[int] = None) -> int:
    """Get integer configuration value with priority: saved.json > ENV > .env > JSON."""
    value = _get_config_value(key, config_raw, saved_config_raw, str(default) if default is not None else None)
    try:
        return int(value)
    except (ValueError, TypeError):
        if default is not None:
            return default
        raise ValueError(f"Invalid integer value for key {key}: {value}")


@dataclass
class Config:
    environment: str
    das: DasConfig
    llm: LlmConfig
    embedding: EmbeddingConfig
    vector_db: VectorDbConfig
    root_path: str
    log_path: str

    @classmethod
    def from_environment(cls, environment: str) -> "Config":
        """Create a Config instance from environment name."""
        # Load .env file first (lower priority than direct env vars)
        load_dotenv()
        
        # Try to load JSON config, but make it optional
        config_raw = {}
        config_path = Path(f".config.{environment}.json")
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config_raw = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in configuration file: {e}")

        # Try to load saved config (highest priority)
        saved_config_raw = {}
        saved_config_path = Path(f".config.{environment}.saved.json")
        if saved_config_path.exists():
            try:
                with open(saved_config_path) as f:
                    saved_config_raw = json.load(f)
                print(f"Loaded saved configuration from: {saved_config_path}")
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in saved configuration file: {e}")

        return cls(
            environment=environment,
            das=DasConfig(
                base_url_page=_get_config_value("GC_QA_RAG.DAS.BASE_URL_PAGE", config_raw, saved_config_raw, ""),
                base_url_thread=_get_config_value("GC_QA_RAG.DAS.BASE_URL_THREAD", config_raw, saved_config_raw, ""),
                token=_get_config_value("GC_QA_RAG.DAS.TOKEN", config_raw, saved_config_raw, ""),
            ),
            llm=LlmConfig(
                api_key=_get_config_value("GC_QA_RAG.LLM.API_KEY", config_raw, saved_config_raw),
                api_base=_get_config_value("GC_QA_RAG.LLM.API_BASE", config_raw, saved_config_raw, "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                model_name=_get_config_value("GC_QA_RAG.LLM.MODEL_NAME", config_raw, saved_config_raw, "qwen-plus"),
                max_rpm=_get_config_int("GC_QA_RAG.LLM.MAX_RPM", config_raw, saved_config_raw, 100),
            ),
            embedding=EmbeddingConfig(
                api_key=_get_config_value("GC_QA_RAG.EMBEDDING.API_KEY", config_raw, saved_config_raw)
            ),
            vector_db=VectorDbConfig(
                host=_get_config_value("GC_QA_RAG.VECTOR_DB.HOST", config_raw, saved_config_raw, "http://host.docker.internal:6333")
            ),
            root_path=_get_config_value("GC_QA_RAG.ROOT_PATH", config_raw, saved_config_raw, user_cache_dir("gc-qa-rag", ensure_exists=True)),
            log_path=_get_config_value("GC_QA_RAG.LOG_PATH", config_raw, saved_config_raw, user_log_dir("gc-qa-rag", ensure_exists=True)),
        )


def get_config() -> Config:
    """Get the application configuration."""
    environment = os.getenv("GC_QA_RAG_ENV", "production")
    return Config.from_environment(environment)


# Initialize configuration
app_config: Optional[Config] = None
try:
    app_config = get_config()
    print(f"The current environment is: {app_config.environment}")
except Exception as e:
    print(f"Failed to load configuration: {e}")
    raise


def reload_config():
    """Reload the global app_config."""
    global app_config
    app_config = get_config()
    print(f"Reloaded config for environment: {app_config.environment}")
