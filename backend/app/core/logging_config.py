import logging
import os
from logging.handlers import RotatingFileHandler
from app.core.config import LOGGER_PATH

#Format for the logs 
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Creating the logs file and adding input to the file
def configure_logging():
    log_dir = LOGGER_PATH
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, "articlehub.log")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5_000_000,
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
