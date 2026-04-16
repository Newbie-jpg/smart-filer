"""Infrastructure logging bootstrap for smart-filer."""

from pathlib import Path
from typing import Optional
import logging

from smart_filer.config import AppSettings, get_settings


DEFAULT_LOGGER_NAME = "smart_filer"
DEFAULT_LOG_FILE = "smart-filer.log"
_MANAGED_HANDLER_FLAG = "_smart_filer_managed_handler"


def _mark_handler(handler: logging.Handler) -> None:
    setattr(handler, _MANAGED_HANDLER_FLAG, True)


def _is_managed(handler: logging.Handler) -> bool:
    return bool(getattr(handler, _MANAGED_HANDLER_FLAG, False))


def configure_logging(
    log_dir: Path,
    level: int = logging.INFO,
    logger_name: str = DEFAULT_LOGGER_NAME,
) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    managed_handlers = [handler for handler in logger.handlers if _is_managed(handler)]
    if managed_handlers:
        for handler in managed_handlers:
            handler.setLevel(level)
        return logger

    file_handler = logging.FileHandler(
        filename=str(log_dir / DEFAULT_LOG_FILE),
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    _mark_handler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    _mark_handler(stream_handler)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def initialize_logging(
    settings: Optional[AppSettings] = None,
    level: int = logging.INFO,
    logger_name: str = DEFAULT_LOGGER_NAME,
) -> logging.Logger:
    resolved_settings = settings or get_settings()
    return configure_logging(
        log_dir=resolved_settings.log_dir,
        level=level,
        logger_name=logger_name,
    )

