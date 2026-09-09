"""
Utility Functions for RetailSense-AI ETL Pipeline.
Provides logging setup, path resolution, and execution timing helpers.
"""

import os
import time
import logging
from typing import Callable, Any
from pathlib import Path


def setup_logger(name: str = "RetailSense_ETL", log_file: str = "airflow/logs/etl_pipeline.log") -> logging.Logger:
    """
    Configures and returns a logger instance with console and file handlers.
    
    Args:
        name: Name of the logger instance.
        log_file: Target log file path.
        
    Returns:
        logging.Logger: Configured logger.
    """
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if logger is already configured
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Stream / Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def ensure_directory(path: str) -> str:
    """
    Ensures that a directory path exists. Creates it if missing.
    
    Args:
        path: Path string for directory or file.
        
    Returns:
        str: Absolute path of the directory.
    """
    dir_path = os.path.dirname(path) if os.path.splitext(path)[1] else path
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    return str(Path(dir_path).resolve()) if dir_path else str(Path(".").resolve())
