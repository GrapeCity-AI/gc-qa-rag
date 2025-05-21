import os
import logging.config
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from ragapp.common.config import app_config


def ensure_folder_exists(folder_path: str) -> None:
    """
    Create a folder if it doesn't exist.

    Args:
        folder_path: Path to the folder to create
    """
    Path(folder_path).mkdir(parents=True, exist_ok=True)


def get_dated_log_path(base_filename: str) -> str:
    """Get the path for a log file with today's date in the path.

    Args:
        base_filename: The base name of the log file

    Returns:
        str: Full path to the log file
    """
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = os.path.join(app_config.log_path, ".logs", today)
    ensure_folder_exists(log_dir)
    return os.path.join(log_dir, base_filename)


def create_formatters() -> Dict[str, Dict[str, Any]]:
    """Create formatters for different logging scenarios.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of formatter configurations
    """
    return {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d - %(funcName)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }


def create_handlers() -> Dict[str, Dict[str, Any]]:
    """Create handlers for different logging destinations.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of handler configurations
    """
    return {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "json",
            "filename": get_dated_log_path("app.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 5,
            "level": "DEBUG",
            "encoding": "utf-8",
        },
        "error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "verbose",
            "filename": get_dated_log_path("errors.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 5,
            "level": "ERROR",
            "encoding": "utf-8",
        },
    }


def create_loggers() -> Dict[str, Dict[str, Any]]:
    """Create logger configurations for different components.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of logger configurations
    """
    return {
        "": {  # root logger
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG",
            "propagate": True,
        }
    }


def create_logging_config() -> Dict[str, Any]:
    """Create the complete logging configuration.

    Returns:
        Dict[str, Any]: Complete logging configuration dictionary
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": create_formatters(),
        "handlers": create_handlers(),
        "loggers": create_loggers(),
    }


def setup_logging() -> None:
    """Initialize the logging configuration."""
    logging_config = create_logging_config()
    logging.config.dictConfig(logging_config)

    logger = logging.getLogger(__name__)
    logger.info(f"App log path: {app_config.log_path}")
    logger.info("Logging system initialized successfully")
