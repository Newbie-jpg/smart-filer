"""Global configuration entry point for smart-filer."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping, MutableMapping, Optional
import os


ENV_PREFIX = "SMART_FILER_"


class SettingsError(ValueError):
    """Raised when configuration is invalid."""


def _parse_bool(raw_value: str, variable_name: str) -> bool:
    normalized = raw_value.strip().lower()
    truthy = {"1", "true", "yes", "on"}
    falsy = {"0", "false", "no", "off"}

    if normalized in truthy:
        return True
    if normalized in falsy:
        return False
    raise SettingsError(
        "Invalid boolean value for {name}: {value}".format(
            name=variable_name, value=raw_value
        )
    )


def _get_prefixed_env(
    env: Mapping[str, str], key: str, default: Optional[str] = None
) -> Optional[str]:
    return env.get("{prefix}{key}".format(prefix=ENV_PREFIX, key=key), default)


@dataclass(frozen=True)
class AppSettings:
    rules_document_path: Path
    siliconflow_api_key: Optional[str]
    siliconflow_base_url: str
    siliconflow_model_id: Optional[str]
    log_dir: Path
    llm_enabled: bool
    request_timeout_seconds: float
    fallback_requires_confirmation: bool


def _effective_env(overrides: Optional[Mapping[str, str]]) -> MutableMapping[str, str]:
    if overrides is None:
        return dict(os.environ)
    return dict(overrides)


def load_settings(overrides: Optional[Mapping[str, str]] = None) -> AppSettings:
    env = _effective_env(overrides)

    default_rules_document = "文档结构.rule.md"
    rules_document_path = Path(
        _get_prefixed_env(env, "RULES_DOCUMENT_PATH", default_rules_document)
        or default_rules_document
    )
    siliconflow_api_key = _get_prefixed_env(env, "SILICONFLOW_API_KEY")
    siliconflow_base_url = (
        _get_prefixed_env(env, "SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        or "https://api.siliconflow.cn/v1"
    )
    siliconflow_model_id = _get_prefixed_env(env, "SILICONFLOW_MODEL_ID")
    log_dir = Path(_get_prefixed_env(env, "LOG_DIR", "logs") or "logs")

    llm_enabled_raw = _get_prefixed_env(env, "LLM_ENABLED", "true") or "true"
    llm_enabled = _parse_bool(llm_enabled_raw, "SMART_FILER_LLM_ENABLED")

    timeout_raw = (
        _get_prefixed_env(env, "REQUEST_TIMEOUT_SECONDS", "30.0") or "30.0"
    ).strip()
    try:
        request_timeout_seconds = float(timeout_raw)
    except ValueError as error:
        raise SettingsError(
            "Invalid numeric value for SMART_FILER_REQUEST_TIMEOUT_SECONDS: {value}".format(
                value=timeout_raw
            )
        ) from error

    fallback_raw = (
        _get_prefixed_env(env, "FALLBACK_REQUIRES_CONFIRMATION", "true") or "true"
    )
    fallback_requires_confirmation = _parse_bool(
        fallback_raw,
        "SMART_FILER_FALLBACK_REQUIRES_CONFIRMATION",
    )

    settings = AppSettings(
        rules_document_path=rules_document_path,
        siliconflow_api_key=siliconflow_api_key,
        siliconflow_base_url=siliconflow_base_url,
        siliconflow_model_id=siliconflow_model_id,
        log_dir=log_dir,
        llm_enabled=llm_enabled,
        request_timeout_seconds=request_timeout_seconds,
        fallback_requires_confirmation=fallback_requires_confirmation,
    )
    _validate_settings(settings)
    return settings


def _validate_settings(settings: AppSettings) -> None:
    if settings.request_timeout_seconds <= 0:
        raise SettingsError("SMART_FILER_REQUEST_TIMEOUT_SECONDS must be > 0")

    if not settings.siliconflow_base_url.strip():
        raise SettingsError("SMART_FILER_SILICONFLOW_BASE_URL cannot be empty")

    if settings.llm_enabled:
        missing = []
        if not settings.siliconflow_api_key:
            missing.append("SMART_FILER_SILICONFLOW_API_KEY")
        if not settings.siliconflow_model_id:
            missing.append("SMART_FILER_SILICONFLOW_MODEL_ID")
        if missing:
            raise SettingsError(
                "Missing required configuration when LLM is enabled: {missing}".format(
                    missing=", ".join(missing)
                )
            )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return load_settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()

