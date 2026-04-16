import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import smart_filer.cli.commands.suggest_install_path as command_module
from smart_filer.cli.app import app
from smart_filer.config import AppSettings
from smart_filer.domain.models import InstallSuggestion, SoftwareCategory
from smart_filer.domain.models.rule_metadata import (
    FallbackStatus,
    RuleBasis,
    RulePriority,
    RuleSource,
)


def _settings_fixture() -> AppSettings:
    return AppSettings(
        rules_document_path=Path("文件结构.md"),
        siliconflow_api_key="test-key",
        siliconflow_base_url="https://api.siliconflow.cn/v1",
        siliconflow_model_id="test-model",
        log_dir=Path("logs"),
        llm_enabled=True,
        request_timeout_seconds=15.0,
        fallback_requires_confirmation=True,
    )


class _StubUseCase:
    def __init__(self, suggestion: InstallSuggestion) -> None:
        self._suggestion = suggestion
        self.last_software_name: str | None = None

    def execute(self, *, software_name: str, aliases=None, context=None) -> InstallSuggestion:
        del aliases, context
        self.last_software_name = software_name
        return self._suggestion


def _suggestion_fixture(
    *,
    software_name: str,
    category: SoftwareCategory,
    path: str,
    reason: str,
    confidence: float,
    fallback_status: FallbackStatus,
    fallback_used: bool,
) -> InstallSuggestion:
    basis_source = RuleSource.FALLBACK if fallback_used else RuleSource.HARD_RULE
    basis_priority = (
        RulePriority.FALLBACK_GUARD if fallback_used else RulePriority.HARD_CONSTRAINT
    )
    return InstallSuggestion(
        software_name=software_name,
        software_category=category,
        suggested_install_path=path,
        reason=reason,
        confidence=confidence,
        needs_confirmation=True,
        fallback_status=fallback_status,
        fallback_used=fallback_used,
        rule_basis=[
            RuleBasis(
                source=basis_source,
                priority=basis_priority,
                summary=reason,
            )
        ],
    )


def _invoke_with_stub_use_case(
    monkeypatch: pytest.MonkeyPatch,
    use_case: _StubUseCase,
    software_name: str,
):
    monkeypatch.setattr(command_module, "get_settings", _settings_fixture)
    monkeypatch.setattr(command_module, "initialize_logging", lambda **_kwargs: None)
    monkeypatch.setattr(command_module, "_build_use_case", lambda _settings: use_case)

    runner = CliRunner()
    return runner.invoke(app, ["suggest-install-path", software_name])


def test_command_returns_structured_result_for_normal_software_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suggestion = _suggestion_fixture(
        software_name="OBS Studio",
        category=SoftwareCategory.MEDIA_DESIGN,
        path=r"D:\50_Media_Design",
        reason="OBS is a media production tool.",
        confidence=0.93,
        fallback_status=FallbackStatus.NOT_USED,
        fallback_used=False,
    )
    use_case = _StubUseCase(suggestion)

    result = _invoke_with_stub_use_case(
        monkeypatch=monkeypatch,
        use_case=use_case,
        software_name="OBS Studio",
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["suggestion"]["software_name"] == "OBS Studio"
    assert payload["suggestion"]["fallback_used"] is False
    assert payload["suggestion"]["suggested_install_path"] == r"D:\50_Media_Design"
    assert payload["explanation"]["why_this_path"]
    assert use_case.last_software_name == "OBS Studio"


def test_command_rejects_empty_input(monkeypatch: pytest.MonkeyPatch) -> None:
    suggestion = _suggestion_fixture(
        software_name="Unused",
        category=SoftwareCategory.UNKNOWN,
        path=r"D:\10_Environments",
        reason="Unused",
        confidence=0.2,
        fallback_status=FallbackStatus.USED_UNCERTAIN_RESULT,
        fallback_used=True,
    )
    use_case = _StubUseCase(suggestion)

    result = _invoke_with_stub_use_case(
        monkeypatch=monkeypatch,
        use_case=use_case,
        software_name="   ",
    )

    assert result.exit_code == 2
    assert "software_name cannot be empty." in (result.stdout + result.stderr)


def test_command_handles_uncertain_classification_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suggestion = _suggestion_fixture(
        software_name="Some Niche Tool",
        category=SoftwareCategory.UNKNOWN,
        path=r"D:\10_Environments",
        reason="LLM returned unknown software category.",
        confidence=0.2,
        fallback_status=FallbackStatus.USED_UNCERTAIN_RESULT,
        fallback_used=True,
    )
    use_case = _StubUseCase(suggestion)

    result = _invoke_with_stub_use_case(
        monkeypatch=monkeypatch,
        use_case=use_case,
        software_name="Some Niche Tool",
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["suggestion"]["fallback_used"] is True
    assert payload["suggestion"]["fallback_status"] == "used_uncertain_result"
    assert payload["suggestion"]["needs_confirmation"] is True


def test_command_handles_llm_error_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    suggestion = _suggestion_fixture(
        software_name="Altium Designer",
        category=SoftwareCategory.UNKNOWN,
        path=r"D:\10_Environments",
        reason="LLM request failed: timeout",
        confidence=0.2,
        fallback_status=FallbackStatus.USED_LLM_ERROR,
        fallback_used=True,
    )
    use_case = _StubUseCase(suggestion)

    result = _invoke_with_stub_use_case(
        monkeypatch=monkeypatch,
        use_case=use_case,
        software_name="Altium Designer",
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["suggestion"]["fallback_status"] == "used_llm_error"
    assert "LLM request failed" in payload["suggestion"]["reason"]
