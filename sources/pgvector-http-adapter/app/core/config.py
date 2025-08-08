"""
Configuration settings for PgVector HTTP Adapter
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Service configuration
    service_name: str = "pgvector-http-adapter"
    service_version: str = "1.0.0"
    service_port: int = Field(default=6333, env="SERVICE_PORT")

    # PostgreSQL configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    postgres_database: str = Field(default="vector_db", env="POSTGRES_DATABASE")

    # Connection pool configuration
    postgres_min_connections: int = Field(default=5, env="POSTGRES_MIN_CONNECTIONS")
    postgres_max_connections: int = Field(default=20, env="POSTGRES_MAX_CONNECTIONS")

    # Vector configuration (dimension set by caller)
    default_vector_dimension: int = Field(default=384, env="DEFAULT_VECTOR_DIMENSION")

    # Search configuration
    default_search_limit: int = Field(default=10, env="DEFAULT_SEARCH_LIMIT")
    max_search_limit: int = Field(default=100, env="MAX_SEARCH_LIMIT")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"

    @property
    def async_postgres_url(self) -> str:
        """Get async PostgreSQL connection URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()