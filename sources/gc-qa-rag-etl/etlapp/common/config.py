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
    """Get configuration value with priority: saved.json > ENV > .env > JSON."""
    # First check saved configuration (highest priority)
    keys = key.lower().split('_')
    # Skip the 'gc_qa_rag' prefix for JSON lookup
    if len(keys) >= 4 and keys[0] == 'gc' and keys[1] == 'qa' and keys[2] == 'rag':
        keys = keys[3:]
    
    # Check saved config first
    current = saved_config_raw
    try:
        for k in keys:
            current = current[k]
        return str(current)
    except (KeyError, TypeError):
        pass
    
    # Then check environment variables
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    
    # Then check nested JSON structure
    current = config_raw
    try:
        for k in keys:
            current = current[k]
        return str(current)
    except (KeyError, TypeError):
        pass
    
    # Return default if provided
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
                base_url_page=_get_config_value("GC_QA_RAG_DAS_BASE_URL_PAGE", config_raw, saved_config_raw, ""),
                base_url_thread=_get_config_value("GC_QA_RAG_DAS_BASE_URL_THREAD", config_raw, saved_config_raw, ""),
                token=_get_config_value("GC_QA_RAG_DAS_TOKEN", config_raw, saved_config_raw, ""),
            ),
            llm=LlmConfig(
                api_key=_get_config_value("GC_QA_RAG_LLM_API_KEY", config_raw, saved_config_raw),
                api_base=_get_config_value("GC_QA_RAG_LLM_API_BASE", config_raw, saved_config_raw, "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                model_name=_get_config_value("GC_QA_RAG_LLM_MODEL_NAME", config_raw, saved_config_raw, "qwen-plus"),
                max_rpm=_get_config_int("GC_QA_RAG_LLM_MAX_RPM", config_raw, saved_config_raw, 100),
            ),
            embedding=EmbeddingConfig(
                api_key=_get_config_value("GC_QA_RAG_EMBEDDING_API_KEY", config_raw, saved_config_raw)
            ),
            vector_db=VectorDbConfig(
                host=_get_config_value("GC_QA_RAG_VECTOR_DB_HOST", config_raw, saved_config_raw, "http://host.docker.internal:6333")
            ),
            root_path=_get_config_value("GC_QA_RAG_ROOT_PATH", config_raw, saved_config_raw, user_cache_dir("gc-qa-rag", ensure_exists=True)),
            log_path=_get_config_value("GC_QA_RAG_LOG_PATH", config_raw, saved_config_raw, user_log_dir("gc-qa-rag", ensure_exists=True)),
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
