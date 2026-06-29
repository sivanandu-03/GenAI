import logging
import sys
from pathlib import Path
from app.config import settings

def setup_logger():
    """Sets up standard application logging to both console and file."""
    # Ensure logs directory exists
    settings.LOGS_PATH.mkdir(parents=True, exist_ok=True)
    log_file = settings.LOGS_PATH / "edugenie.log"

    # Create logger formatter
    log_format = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Root application logger
    logger = logging.getLogger("edugenie")
    
    # Set logging levels
    if settings.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if logger already initialized
    if not logger.handlers:
        # Console logging handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_format)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

        # File logging handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    return logger

# Export instantiated logger instance
logger = setup_logger()
