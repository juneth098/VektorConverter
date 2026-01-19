#logger.py
import sys
import logging
from logging import StreamHandler
from datetime import datetime, timedelta
import os

LOG_FILE = "app.log"
LOG_RETENTION_DAYS = 7

_logger = None
_file_handler = None
_logger_initialized = False

def cleanup_old_logs():
    if not os.path.exists(LOG_FILE):
        return

    new_lines = []
    cutoff = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                ts_str = line.split(" | ")[0]
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                if ts >= cutoff:
                    new_lines.append(line)
            except:
                continue
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def init_logger():
    """Initialize logger (console always on, file optional)"""
    global _logger, _file_handler, _logger_initialized
    if _logger_initialized:
        return

    cleanup_old_logs()

    _logger = logging.getLogger("VektorLogger")
    _logger.setLevel(logging.INFO)
    _logger.handlers.clear()

    console_handler = StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s | %(message)s", "%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    # File handler (disabled by default)
    _file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    _file_handler.setFormatter(formatter)

    _logger_initialized = True

def enable_file_logging():
    global _logger, _file_handler
    if _logger and _file_handler and _file_handler not in _logger.handlers:
        _logger.addHandler(_file_handler)

def disable_file_logging():
    global _logger, _file_handler
    if _logger and _file_handler and _file_handler in _logger.handlers:
        _logger.removeHandler(_file_handler)

def log(msg):
    global _logger
    if _logger:
        _logger.info(msg)

def close_logger():
    global _logger, _file_handler
    if _logger:
        for handler in _logger.handlers[:]:
            try:
                handler.close()
            except:
                pass
            _logger.removeHandler(handler)
