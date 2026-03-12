import logging
import os
from datetime import datetime

_loggers = {}


def setup_logger(name: str = "wildfire_scraper", log_dir: str = "logs") -> logging.Logger:
    """Setup logger with file and console handlers."""
    if name in _loggers:
        return _loggers[name]

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger


def get_logger(name: str = "wildfire_scraper") -> logging.Logger:
    """Get an existing logger or create a new one."""
    if name not in _loggers:
        return setup_logger(name)
    return _loggers[name]
