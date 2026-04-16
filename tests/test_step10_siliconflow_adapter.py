import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from smart_filer.config import AppSettings
from smart_filer.domain.models import LLMInstallPathRequest
from smart_filer.infrastructure.providers.siliconflow_adapter import (
    SiliconFlowAdapter,
    SiliconFlowResponseError,
    SiliconFlowTimeoutError,
)


def _completion_with_content(content: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class _RecordingCompletions:
    def __init__(
        self,
        *,
        response: SimpleNamespace | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self._error = error
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        assert self._response is not None
        return self._response


def _request_fixture() -> LLMInstallPathRequest:
    return LLMInstallPathRequest(
        software_name="OBS Studio",
        rule_summary=[
            "Software and runtime should be installed under D drive.",
            "Media design software should use D:\\50_Media_Design.",
        ],
        aliases=["OBS"],
    )


def test_adapter_builds_request_and_uses_configured_model_and_timeout() -> None:
    completions = _RecordingCompletions(
        response=_completion_with_content(
            json.dumps(
                {
                    "category": "media_design",
                    "suggested_path": r"D:\50_Media_Design",
                    "reason": "OBS is mainly used for recording and live streaming.",
                    "confidence": 0.91,
                }
            )
        )
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    adapter = SiliconFlowAdapter(
        api_key="test-key",
        base_url="https://api.siliconflow.cn/v1",
        model_id="Qwen/Qwen2.5-7B-Instruct",
        timeout_seconds=12.5,
        client=client,
    )

    request = _request_fixture()
    result = adapter.classify_software(request)
    call = completions.calls[0]

    assert call["model"] == "Qwen/Qwen2.5-7B-Instruct"
    assert call["timeout"] == 12.5
    assert call["response_format"] == {"type": "json_object"}
    assert request.rule_summary[0] in str(call["messages"])
    assert result.model_id == "Qwen/Qwen2.5-7B-Instruct"
    assert result.response.suggested_install_path == r"D:\50_Media_Design"


def test_adapter_uses_base_url_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    completions = _RecordingCompletions(
        response=_completion_with_content(
            json.dumps(
                {
                    "category": "engineering",
                    "suggested_path": r"D:\30_Engineering",
                    "reason": "EDA tools should be classified as engineering software.",
                    "confidence": 0.82,
                }
            )
        )
    )

    def _fake_openai(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(chat=SimpleNamespace(completions=completions))

    monkeypatch.setattr(
        "smart_filer.infrastructure.providers.siliconflow_adapter.OpenAI",
        _fake_openai,
    )

    settings = AppSettings(
        rules_document_path=Path("文件结构.md"),
        siliconflow_api_key="sf-key",
        siliconflow_base_url="https://api.siliconflow.cn/v1",
        siliconflow_model_id="sf-model-id",
        log_dir=Path("logs"),
        llm_enabled=True,
        request_timeout_seconds=20.0,
        fallback_requires_confirmation=True,
    )
    adapter = SiliconFlowAdapter.from_settings(settings)

    adapter.classify_software(_request_fixture())
    first_call = completions.calls[0]

    assert captured["base_url"] == "https://api.siliconflow.cn/v1"
    assert captured["timeout"] == 20.0
    assert first_call["model"] == "sf-model-id"


def test_adapter_wraps_timeout_error() -> None:
    completions = _RecordingCompletions(error=TimeoutError("timed out"))
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    adapter = SiliconFlowAdapter(
        api_key="test-key",
        base_url="https://api.siliconflow.cn/v1",
        model_id="sf-model-id",
        timeout_seconds=5.0,
        client=client,
    )

    with pytest.raises(SiliconFlowTimeoutError):
        adapter.classify_software(_request_fixture())


def test_adapter_raises_clear_error_on_empty_response() -> None:
    response = SimpleNamespace(choices=[])
    completions = _RecordingCompletions(response=response)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    adapter = SiliconFlowAdapter(
        api_key="test-key",
        base_url="https://api.siliconflow.cn/v1",
        model_id="sf-model-id",
        timeout_seconds=5.0,
        client=client,
    )

    with pytest.raises(SiliconFlowResponseError) as error:
        adapter.classify_software(_request_fixture())

    assert "empty choices" in str(error.value)


def test_adapter_raises_clear_error_on_non_json_response() -> None:
    completions = _RecordingCompletions(
        response=_completion_with_content("This is plain text, not JSON.")
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    adapter = SiliconFlowAdapter(
        api_key="test-key",
        base_url="https://api.siliconflow.cn/v1",
        model_id="sf-model-id",
        timeout_seconds=5.0,
        client=client,
    )

    with pytest.raises(SiliconFlowResponseError) as error:
        adapter.classify_software(_request_fixture())

    assert "non-JSON" in str(error.value)
