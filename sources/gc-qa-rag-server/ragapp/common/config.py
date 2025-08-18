import os
import json
from typing import Optional, Union
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from platformdirs import user_log_dir


@dataclass
class LlmConfig:
    api_key: str
    api_base: str
    model_name: str


@dataclass
class EmbeddingConfig:
    api_key: str


@dataclass
class VectorDbConfig:
    host: str


@dataclass
class DbConfig:
    connection_string: str


def _get_config_value(key: str, config_raw: dict, default: Optional[str] = None) -> str:
    """Get configuration value with priority: ENV > .env > JSON."""
    # First check environment variables
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    
    # Then check nested JSON structure
    keys = key.lower().split('_')
    # Skip the 'gc_qa_rag' prefix for JSON lookup
    if keys[0] == 'gc' and keys[1] == 'qa' and keys[2] == 'rag':
        keys = keys[3:]
    
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


def _get_llm_config(
    config_raw: dict, config_type: str, default_config: Optional[LlmConfig] = None
) -> LlmConfig:
    """Get LLM configuration with fallback to default config if specified config doesn't exist."""
    # Try to get from environment variables first
    env_prefix = f"GC_QA_RAG_{config_type.upper()}"
    api_key = os.getenv(f"{env_prefix}_API_KEY")
    api_base = os.getenv(f"{env_prefix}_API_BASE")
    model_name = os.getenv(f"{env_prefix}_MODEL_NAME")
    
    # If all env vars are set, use them
    if api_key and api_base and model_name:
        return LlmConfig(
            api_key=api_key,
            api_base=api_base,
            model_name=model_name,
        )
    
    # Otherwise, try JSON config
    if config_type in config_raw:
        config = config_raw[config_type]
        return LlmConfig(
            api_key=api_key or config.get("api_key", ""),
            api_base=api_base or config.get("api_base", ""),
            model_name=model_name or config.get("model_name", ""),
        )
    
    # Fall back to default config
    if default_config:
        return LlmConfig(
            api_key=api_key or default_config.api_key,
            api_base=api_base or default_config.api_base,
            model_name=model_name or default_config.model_name,
        )
    
    # Last resort: use default LLM config from env/JSON
    return LlmConfig(
        api_key=api_key or _get_config_value("GC_QA_RAG_LLM_DEFAULT_API_KEY", config_raw),
        api_base=api_base or _get_config_value("GC_QA_RAG_LLM_DEFAULT_API_BASE", config_raw, "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model_name=model_name or _get_config_value("GC_QA_RAG_LLM_DEFAULT_MODEL_NAME", config_raw, "qwen-plus"),
    )


@dataclass
class Config:
    environment: str
    llm_default: LlmConfig
    llm_summary: LlmConfig
    llm_think: LlmConfig
    llm_query: LlmConfig
    llm_research: LlmConfig
    embedding: EmbeddingConfig
    vector_db: VectorDbConfig
    db: DbConfig
    log_path: str
    etl_base_url: str

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

        # Initialize default config first
        llm_default = _get_llm_config(config_raw, "llm_default")

        return cls(
            environment=environment,
            llm_default=llm_default,
            llm_summary=_get_llm_config(config_raw, "llm_summary", llm_default),
            llm_think=_get_llm_config(config_raw, "llm_think", llm_default),
            llm_query=_get_llm_config(config_raw, "llm_query", llm_default),
            llm_research=_get_llm_config(config_raw, "llm_research", llm_default),
            embedding=EmbeddingConfig(
                api_key=_get_config_value("GC_QA_RAG_EMBEDDING_API_KEY", config_raw)
            ),
            vector_db=VectorDbConfig(
                host=_get_config_value("GC_QA_RAG_VECTOR_DB_HOST", config_raw, "http://rag_qdrant_container:6333")
            ),
            db=DbConfig(
                connection_string=_get_config_value("GC_QA_RAG_DB_CONNECTION_STRING", config_raw, "mysql+mysqlconnector://root:12345678@rag_mysql_container:3306/search_db")
            ),
            log_path=_get_config_value("GC_QA_RAG_LOG_PATH", config_raw, user_log_dir("gc-qa-rag-server", ensure_exists=True)),
            etl_base_url=_get_config_value("GC_QA_RAG_ETL_BASE_URL", config_raw, "http://host.docker.internal:8001"),
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
