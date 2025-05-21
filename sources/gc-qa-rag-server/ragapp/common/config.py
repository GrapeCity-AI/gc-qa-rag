import os
import json
from typing import Optional
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


def _get_llm_config(
    config_raw: dict, config_key: str, default_config: Optional[LlmConfig] = None
) -> LlmConfig:
    """Get LLM configuration with fallback to default config if specified config doesn't exist."""
    if config_key in config_raw:
        config = config_raw[config_key]
        return LlmConfig(
            api_key=config["api_key"],
            api_base=config["api_base"],
            model_name=config["model_name"],
        )
    return (
        default_config
        if default_config
        else LlmConfig(
            api_key=config_raw["llm_default"]["api_key"],
            api_base=config_raw["llm_default"]["api_base"],
            model_name=config_raw["llm_default"]["model_name"],
        )
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

        # Initialize default config first
        llm_default = LlmConfig(
            api_key=config_raw["llm_default"]["api_key"],
            api_base=config_raw["llm_default"]["api_base"],
            model_name=config_raw["llm_default"]["model_name"],
        )

        return cls(
            environment=environment,
            llm_default=llm_default,
            llm_summary=_get_llm_config(config_raw, "llm_summary", llm_default),
            llm_think=_get_llm_config(config_raw, "llm_think", llm_default),
            llm_query=_get_llm_config(config_raw, "llm_query", llm_default),
            llm_research=_get_llm_config(config_raw, "llm_research", llm_default),
            embedding=EmbeddingConfig(api_key=config_raw["embedding"]["api_key"]),
            vector_db=VectorDbConfig(host=config_raw["vector_db"]["host"]),
            db=DbConfig(connection_string=config_raw["db"]["connection_string"]),
            log_path=config_raw.get(
                "log_path", user_log_dir("gc-qa-rag-server", ensure_exists=True)
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
