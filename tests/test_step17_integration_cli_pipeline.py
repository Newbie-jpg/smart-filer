import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import smart_filer.application.use_cases.install_path_suggestion as use_case_module
import smart_filer.cli.commands.suggest_install_path as command_module
from smart_filer.cli.app import app
from smart_filer.config import clear_settings_cache
from smart_filer.domain.models import LLMInstallPathResponse
from smart_filer.domain.models.llm_models import LLMInstallPathRequest
from smart_filer.infrastructure.providers.siliconflow_adapter import (
    SiliconFlowAdapterResult,
    SiliconFlowResponseError,
)


class _RuleAwareClassifier:
    def __init__(self, *, raise_validation_error: bool = False) -> None:
        self._raise_validation_error = raise_validation_error

    def classify_software(
        self, request: LLMInstallPathRequest
    ) -> SiliconFlowAdapterResult:
        if self._raise_validation_error:
            raise SiliconFlowResponseError("invalid structured response")

        engineering_path = _extract_category_mapping_path(
            request.rule_summary,
            "engineering",
        ) or r"D:\30_Engineering"

        response = LLMInstallPathResponse.model_validate(
            {
                "category": "engineering",
                "suggested_path": engineering_path,
                "reason": "Classifier inferred engineering software category.",
                "confidence": 0.91,
            }
        )
        return SiliconFlowAdapterResult(
            response=response,
            raw_response_text='{"category":"engineering"}',
            model_id="stub-model",
        )


def _extract_category_mapping_path(summary_lines: list[str], category: str) -> str | None:
    prefix = f"{category} -> "
    for line in summary_lines:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _write_rules_document(path: Path, *, engineering_path: str) -> None:
    path.write_text(
        f"""
metadata:
  rules_version: 1
  document_type: smart_filer_machine_rules
  document_status: active
  platform: windows
  path_style: windows_absolute

global_rules:
  preferred_install_drive: "D:"
  forbidden_install_roots:
    - "S:\\\\"
  fallback_install_path: "D:\\\\10_Environments"
  allow_only_local_paths: true

categories:
  - id: development_environment
    display_name: Development Environment
    priority: 100
    definition: "SDKs and runtimes."
    includes:
      - "Python"
    excludes:
      - "Steam"
    default_install_path: "D:\\\\10_Environments"
    allowed_install_paths:
      - "D:\\\\10_Environments"
  - id: engineering
    display_name: Engineering
    priority: 200
    definition: "Engineering tools."
    includes:
      - "EDA"
    excludes:
      - "Office"
    default_install_path: "{engineering_path.replace('\\', '\\\\')}"
    allowed_install_paths:
      - "{engineering_path.replace('\\', '\\\\')}"
  - id: productivity
    display_name: Productivity
    priority: 300
    definition: "Office tools."
    includes:
      - "Office"
    excludes:
      - "Steam"
    default_install_path: "D:\\\\40_Productivity"
    allowed_install_paths:
      - "D:\\\\40_Productivity"
  - id: media_design
    display_name: Media Design
    priority: 400
    definition: "Media tools."
    includes:
      - "OBS"
    excludes:
      - "Compiler"
    default_install_path: "D:\\\\50_Media_Design"
    allowed_install_paths:
      - "D:\\\\50_Media_Design"
  - id: system_utilities
    display_name: System Utilities
    priority: 500
    definition: "Utilities."
    includes:
      - "Everything"
    excludes:
      - "Steam"
    default_install_path: "D:\\\\60_System_Utilities"
    allowed_install_paths:
      - "D:\\\\60_System_Utilities"
  - id: games_entertain
    display_name: Games and Entertainment
    priority: 600
    definition: "Entertainment clients."
    includes:
      - "Steam"
    excludes:
      - "Office"
    default_install_path: "D:\\\\70_Games_Entertain"
    allowed_install_paths:
      - "D:\\\\70_Games_Entertain"

software_overrides: []

conflict_resolution:
  order:
    - exact_name
    - alias
    - override_keyword
    - category_keyword
    - category_default
    - global_hard_rule
    - fallback

validation_examples:
  - software_name: "OBS Studio"
    expected_category: media_design
    expected_install_path: "D:\\\\50_Media_Design"
    expected_rule_source: category_default
  - software_name: "Altium Designer"
    expected_category: engineering
    expected_install_path: "{engineering_path.replace('\\', '\\\\')}"
    expected_rule_source: category_default
  - software_name: "Office 365"
    expected_category: productivity
    expected_install_path: "D:\\\\40_Productivity"
    expected_rule_source: category_default
  - software_name: "Steam"
    expected_category: games_entertain
    expected_install_path: "D:\\\\70_Games_Entertain"
    expected_rule_source: category_default
  - software_name: "Everything"
    expected_category: system_utilities
    expected_install_path: "D:\\\\60_System_Utilities"
    expected_rule_source: category_default
  - software_name: "Python 3.12"
    expected_category: development_environment
    expected_install_path: "D:\\\\10_Environments"
    expected_rule_source: category_default
  - software_name: "Notion"
    expected_category: productivity
    expected_install_path: "D:\\\\40_Productivity"
    expected_rule_source: category_default
  - software_name: "Photoshop 2024"
    expected_category: media_design
    expected_install_path: "D:\\\\50_Media_Design"
    expected_rule_source: category_default
  - software_name: "AutoCAD"
    expected_category: engineering
    expected_install_path: "{engineering_path.replace('\\', '\\\\')}"
    expected_rule_source: category_default
  - software_name: "7-Zip"
    expected_category: system_utilities
    expected_install_path: "D:\\\\60_System_Utilities"
    expected_rule_source: category_default
""".strip(),
        encoding="utf-8",
    )


def _configure_settings_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    rules_document_path: Path,
) -> None:
    monkeypatch.setenv("SMART_FILER_RULES_DOCUMENT_PATH", str(rules_document_path))
    monkeypatch.setenv("SMART_FILER_SILICONFLOW_API_KEY", "test-key")
    monkeypatch.setenv("SMART_FILER_SILICONFLOW_MODEL_ID", "test-model")
    monkeypatch.setenv("SMART_FILER_SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setenv("SMART_FILER_LLM_ENABLED", "true")
    monkeypatch.setenv("SMART_FILER_REQUEST_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("SMART_FILER_FALLBACK_REQUIRES_CONFIRMATION", "true")
    clear_settings_cache()


def _patch_classifier(
    monkeypatch: pytest.MonkeyPatch,
    *,
    classifier: _RuleAwareClassifier,
) -> None:
    def _from_settings(_cls, _settings, **_kwargs) -> _RuleAwareClassifier:
        return classifier

    monkeypatch.setattr(
        use_case_module.SiliconFlowAdapter,
        "from_settings",
        classmethod(_from_settings),
    )
    monkeypatch.setattr(command_module, "initialize_logging", lambda **_kwargs: None)


def _invoke_command(software_name: str):
    runner = CliRunner()
    return runner.invoke(app, ["suggest-install-path", software_name])


def test_cli_integration_returns_expected_path_for_valid_classification(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "rules.rule.md"
    _write_rules_document(rules_path, engineering_path=r"D:\30_Engineering")
    _configure_settings_env(monkeypatch, rules_document_path=rules_path)
    _patch_classifier(monkeypatch, classifier=_RuleAwareClassifier())

    result = _invoke_command("Altium Designer")

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["suggestion"]["software_name"] == "Altium Designer"
    assert payload["suggestion"]["software_category"] == "engineering"
    assert payload["suggestion"]["suggested_install_path"] == r"D:\30_Engineering"
    assert payload["suggestion"]["fallback_used"] is False


def test_cli_integration_falls_back_when_llm_returns_invalid_structure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "rules.rule.md"
    _write_rules_document(rules_path, engineering_path=r"D:\30_Engineering")
    _configure_settings_env(monkeypatch, rules_document_path=rules_path)
    _patch_classifier(
        monkeypatch,
        classifier=_RuleAwareClassifier(raise_validation_error=True),
    )

    result = _invoke_command("Altium Designer")

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["suggestion"]["fallback_used"] is True
    assert payload["suggestion"]["fallback_status"] == "used_validation_error"
    assert payload["suggestion"]["suggested_install_path"] == r"D:\10_Environments"


def test_cli_integration_returns_error_when_rules_document_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing_rules_path = tmp_path / "missing-rules.rule.md"
    _configure_settings_env(monkeypatch, rules_document_path=missing_rules_path)
    _patch_classifier(monkeypatch, classifier=_RuleAwareClassifier())

    result = _invoke_command("Altium Designer")

    assert result.exit_code == 1
    assert "Rules document does not exist" in (result.stdout + result.stderr)


def test_cli_integration_reloads_modified_rules_document_between_calls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "rules.rule.md"
    _configure_settings_env(monkeypatch, rules_document_path=rules_path)
    _patch_classifier(monkeypatch, classifier=_RuleAwareClassifier())

    _write_rules_document(rules_path, engineering_path=r"D:\30_Engineering")
    first = _invoke_command("Altium Designer")
    first_payload = json.loads(first.stdout)

    _write_rules_document(rules_path, engineering_path=r"D:\31_Engineering_Beta")
    second = _invoke_command("Altium Designer")
    second_payload = json.loads(second.stdout)

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first_payload["suggestion"]["suggested_install_path"] == r"D:\30_Engineering"
    assert (
        second_payload["suggestion"]["suggested_install_path"]
        == r"D:\31_Engineering_Beta"
    )
    assert second_payload["suggestion"]["fallback_used"] is False
