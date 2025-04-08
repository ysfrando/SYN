import logging
import os
import sys
from logging import RotatingFileHandler

def setup_logger(
    logger_name: str = "app",
    log_level: int = logging.INFO,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file: str = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure and return logger instance.
    """
    logger = logging.getLogger(logger_name)

    # Prevent duplicate handlers if logger is already set up
    if len(logger.handlers) > 0:
        return logger  # Logger already configured

    logger.setLevel(log_level)
    formatter = logging.Formatter(log_format)

    # File logging
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console logging
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger