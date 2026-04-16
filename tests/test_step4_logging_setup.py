import logging
from pathlib import Path
from uuid import uuid4

from smart_filer.config import AppSettings
from smart_filer.infrastructure.logging_setup import (
    DEFAULT_LOG_FILE,
    configure_logging,
    initialize_logging,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_TEST_DIR = REPO_ROOT / ".test-runtime" / "logging"


def _new_log_dir() -> Path:
    target = RUNTIME_TEST_DIR / str(uuid4())
    target.mkdir(parents=True, exist_ok=True)
    return target


def test_logging_configuration_creates_logger_and_log_file() -> None:
    log_dir = _new_log_dir()
    logger_name = "smart_filer.tests.create"
    logger = configure_logging(
        log_dir=log_dir,
        level=logging.INFO,
        logger_name=logger_name,
    )

    logger.info("hello")

    assert logger.name == logger_name
    assert (log_dir / DEFAULT_LOG_FILE).exists()
    assert len(logger.handlers) == 2


def test_logging_configuration_is_idempotent() -> None:
    log_dir = _new_log_dir()
    logger_name = "smart_filer.tests.idempotent"

    logger = configure_logging(
        log_dir=log_dir,
        level=logging.DEBUG,
        logger_name=logger_name,
    )
    first_count = len(logger.handlers)

    logger = configure_logging(
        log_dir=log_dir,
        level=logging.DEBUG,
        logger_name=logger_name,
    )
    second_count = len(logger.handlers)

    assert first_count == 2
    assert second_count == 2


def test_initialize_logging_uses_settings_log_dir() -> None:
    log_dir = _new_log_dir()
    logger_name = "smart_filer.tests.initialize"
    settings = AppSettings(
        rules_document_path=Path("文档结构.rule.md"),
        siliconflow_api_key=None,
        siliconflow_base_url="https://api.siliconflow.cn/v1",
        siliconflow_model_id=None,
        log_dir=log_dir,
        llm_enabled=False,
        request_timeout_seconds=30.0,
        fallback_requires_confirmation=True,
    )

    logger = initialize_logging(
        settings=settings,
        level=logging.WARNING,
        logger_name=logger_name,
    )

    logger.warning("from initialize")

    assert logger.name == logger_name
    assert (log_dir / DEFAULT_LOG_FILE).exists()

