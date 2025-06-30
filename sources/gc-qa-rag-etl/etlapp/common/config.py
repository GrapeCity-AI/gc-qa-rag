import os
import json
from typing import Optional
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


@dataclass
class EmbeddingConfig:
    api_key: str


@dataclass
class VectorDbConfig:
    type: str  # 'qdrant' or 'milvus'
    host: str
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    def __post_init__(self):
        if self.type not in ['qdrant', 'milvus']:
            raise ValueError(f"Unsupported vector database type: {self.type}")


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
        config_path = Path(f".config.{environment}.json")
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path) as f:
                config_raw = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")

        return cls(
            environment=environment,
            das=DasConfig(
                base_url_page=config_raw["das"]["base_url_page"],
                base_url_thread=config_raw["das"]["base_url_thread"],
                token=config_raw["das"]["token"],
            ),
            llm=LlmConfig(
                api_key=config_raw["llm"]["api_key"],
                api_base=config_raw["llm"]["api_base"],
                model_name=config_raw["llm"]["model_name"],
            ),
            embedding=EmbeddingConfig(api_key=config_raw["embedding"]["api_key"]),
            vector_db=VectorDbConfig(
                type=config_raw["vector_db"]["type"],
                host=config_raw["vector_db"]["host"],
                port=config_raw["vector_db"].get("port"),
                username=config_raw["vector_db"].get("username"),
                password=config_raw["vector_db"].get("password"),
            ),
            root_path=config_raw.get(
                "root_path", user_cache_dir("gc-qa-rag", ensure_exists=True)
            ),
            log_path=config_raw.get(
                "log_path", user_log_dir("gc-qa-rag", ensure_exists=True)
            ),
        )


def get_config() -> Config:
    """Get the application configuration."""
    load_dotenv()
    environment = os.getenv("GC_QA_RAG_ENV")
    if not environment:
        raise ValueError("GC_QA_RAG_ENV environment variable is not set")

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
