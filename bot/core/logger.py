import logging
from pathlib import Path

def setup_logging(log_file: Path) -> logging.Logger:
    """Configure logging with file and console handlers"""
    # Create logger for the 'bot' package
    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)
    
    # Avoid adding duplicate handlers if they already exist
    if logger.handlers:
        return logger

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
