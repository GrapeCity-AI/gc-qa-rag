"""
Configuration - Pydantic Settings-based configuration management.

Centralized configuration using environment variables with sensible defaults.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        extra="ignore",
    )

    api_key: str = Field(default="", description="LLM API key")
    base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1/",
        description="LLM API base URL",
    )
    model: str = Field(default="qwen-plus", description="LLM model name")


class EmbeddingSettings(BaseSettings):
    """DashScope embedding configuration."""

    model_config = SettingsConfigDict(
        env_prefix="DASHSCOPE_",
        extra="ignore",
    )

    api_key: str = Field(default="", description="DashScope API key")
    model_name: str = Field(
        default="text-embedding-v4",
        description="Embedding model name",
    )
    dimensions: int = Field(default=1024, description="Embedding dimensions")


class QdrantSettings(BaseSettings):
    """Qdrant vector database configuration."""

    model_config = SettingsConfigDict(
        env_prefix="QDRANT_",
        extra="ignore",
    )

    url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL",
    )
    api_key: Optional[str] = Field(default=None, description="Qdrant API key")
    timeout: float = Field(default=60.0, description="Request timeout in seconds")


class StorageSettings(BaseSettings):
    """Storage path configuration."""

    model_config = SettingsConfigDict(
        env_prefix="STORAGE_",
        extra="ignore",
    )

    base_path: str = Field(
        default="./data",
        description="Base path for file storage",
    )

    @property
    def raw_files_path(self) -> Path:
        """Path for raw file storage."""
        return Path(self.base_path) / "raw_files"

    @property
    def metadata_db_path(self) -> Path:
        """Path for metadata SQLite database."""
        return Path(self.base_path) / "metadata.db"

    @property
    def versions_db_path(self) -> Path:
        """Path for versions SQLite database."""
        return Path(self.base_path) / "versions.db"


class SchedulerSettings(BaseSettings):
    """Task scheduler configuration."""

    model_config = SettingsConfigDict(
        env_prefix="SCHEDULER_",
        extra="ignore",
    )

    max_workers: int = Field(
        default=2,
        description="Maximum number of worker threads",
        ge=1,
        le=16,
    )
    poll_interval: float = Field(
        default=1.0,
        description="Queue poll interval in seconds",
        ge=0.1,
        le=60.0,
    )


class AppSettings(BaseSettings):
    """Main application settings aggregating all sub-settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Sub-settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)

    # Application settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.storage.raw_files_path.mkdir(parents=True, exist_ok=True)
        self.storage.metadata_db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> AppSettings:
    """Get cached application settings."""
    return AppSettings()


def get_fresh_settings() -> AppSettings:
    """Get fresh application settings (bypasses cache)."""
    return AppSettings()
