import logging

# For fetching the name of the logger

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
