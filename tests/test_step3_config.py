from pathlib import Path

import pytest

from smart_filer.config import SettingsError, load_settings


def test_config_defaults_load_successfully() -> None:
    settings = load_settings(
        overrides={
            "SMART_FILER_SILICONFLOW_API_KEY": "test-api-key",
            "SMART_FILER_SILICONFLOW_MODEL_ID": "sf-model-1",
        }
    )

    assert settings.rules_document_path == Path("文档结构.rule.md")
    assert settings.siliconflow_base_url == "https://api.siliconflow.cn/v1"
    assert settings.log_dir == Path("logs")
    assert settings.llm_enabled is True
    assert settings.request_timeout_seconds == 30.0
    assert settings.fallback_requires_confirmation is True


def test_config_environment_overrides_defaults() -> None:
    env = {
        "SMART_FILER_RULES_DOCUMENT_PATH": "custom-rules.md",
        "SMART_FILER_SILICONFLOW_API_KEY": "test-api-key",
        "SMART_FILER_SILICONFLOW_BASE_URL": "https://example.test/v1",
        "SMART_FILER_SILICONFLOW_MODEL_ID": "sf-model-1",
        "SMART_FILER_LOG_DIR": "runtime-logs",
        "SMART_FILER_LLM_ENABLED": "true",
        "SMART_FILER_REQUEST_TIMEOUT_SECONDS": "45",
        "SMART_FILER_FALLBACK_REQUIRES_CONFIRMATION": "false",
    }

    settings = load_settings(overrides=env)

    assert settings.rules_document_path == Path("custom-rules.md")
    assert settings.siliconflow_api_key == "test-api-key"
    assert settings.siliconflow_base_url == "https://example.test/v1"
    assert settings.siliconflow_model_id == "sf-model-1"
    assert settings.log_dir == Path("runtime-logs")
    assert settings.llm_enabled is True
    assert settings.request_timeout_seconds == 45.0
    assert settings.fallback_requires_confirmation is False


def test_config_raises_clear_error_for_missing_required_llm_fields() -> None:
    env = {
        "SMART_FILER_LLM_ENABLED": "true",
        "SMART_FILER_SILICONFLOW_MODEL_ID": "sf-model-1",
    }

    with pytest.raises(SettingsError) as error:
        load_settings(overrides=env)

    assert "SMART_FILER_SILICONFLOW_API_KEY" in str(error.value)
