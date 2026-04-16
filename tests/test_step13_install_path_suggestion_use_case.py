from pathlib import Path

import pytest

from smart_filer.application.use_cases import SuggestInstallPathUseCase
from smart_filer.config import AppSettings
from smart_filer.domain.models import (
    CategoryRuleProfile,
    LLMInstallPathResponse,
    ParsedInstallRules,
    SoftwareCategory,
)
from smart_filer.domain.models.rule_metadata import FallbackStatus
from smart_filer.infrastructure.providers.siliconflow_adapter import SiliconFlowAdapterResult


def _settings_fixture() -> AppSettings:
    return AppSettings(
        rules_document_path=Path("文档结构.rule.md"),
        siliconflow_api_key="test-key",
        siliconflow_base_url="https://api.siliconflow.cn/v1",
        siliconflow_model_id="test-model",
        log_dir=Path("logs"),
        llm_enabled=True,
        request_timeout_seconds=15.0,
        fallback_requires_confirmation=True,
    )


def _parsed_rules_fixture() -> ParsedInstallRules:
    return ParsedInstallRules(
        d_drive_preferred=True,
        discourage_s_drive_install=True,
        category_install_paths={
            SoftwareCategory.DEVELOPMENT_ENVIRONMENT: r"D:\10_Environments",
            SoftwareCategory.ENGINEERING: r"D:\30_Engineering",
            SoftwareCategory.PRODUCTIVITY: r"D:\40_Productivity",
            SoftwareCategory.MEDIA_DESIGN: r"D:\50_Media_Design",
            SoftwareCategory.SYSTEM_UTILITIES: r"D:\60_System_Utilities",
            SoftwareCategory.GAMES_ENTERTAIN: r"D:\70_Games_Entertain",
        },
        category_profiles={
            SoftwareCategory.PRODUCTIVITY: CategoryRuleProfile(
                definition="Communication and collaboration software.",
                includes=["Team Chat", "Voice Collaboration"],
                excludes=["System Maintenance"],
            ),
            SoftwareCategory.SYSTEM_UTILITIES: CategoryRuleProfile(
                definition="Diagnostics and maintenance tools.",
                includes=["System Monitor"],
                excludes=["Team Communication"],
            ),
        },
        warnings=[],
        rule_basis=["软件和运行环境优先放在 D 盘体系。"],
    )


class _StubClassifier:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.last_request = None

    def classify_software(self, request):
        self.last_request = request
        return SiliconFlowAdapterResult(
            response=LLMInstallPathResponse.model_validate(self._payload),
            raw_response_text=str(self._payload),
            model_id="stub-model",
        )


@pytest.mark.parametrize(
    ("software_name", "payload", "expected_category", "expected_path"),
    [
        (
            "Altium Designer",
            {
                "category": "engineering",
                "suggested_path": r"D:\30_Engineering",
                "reason": "EDA software belongs to engineering tools.",
                "confidence": 0.91,
            },
            SoftwareCategory.ENGINEERING,
            r"D:\30_Engineering",
        ),
        (
            "Notion",
            {
                "category": "productivity",
                "suggested_path": r"D:\40_Productivity",
                "reason": "Knowledge and note tools are productivity software.",
                "confidence": 0.89,
            },
            SoftwareCategory.PRODUCTIVITY,
            r"D:\40_Productivity",
        ),
        (
            "OBS Studio",
            {
                "category": "media_design",
                "suggested_path": r"D:\50_Media_Design",
                "reason": "Streaming and recording tools belong to media design.",
                "confidence": 0.93,
            },
            SoftwareCategory.MEDIA_DESIGN,
            r"D:\50_Media_Design",
        ),
        (
            "7-Zip",
            {
                "category": "system_utilities",
                "suggested_path": r"D:\60_System_Utilities",
                "reason": "Compression utility belongs to system tools.",
                "confidence": 0.92,
            },
            SoftwareCategory.SYSTEM_UTILITIES,
            r"D:\60_System_Utilities",
        ),
        (
            "Steam",
            {
                "category": "games_entertain",
                "suggested_path": r"D:\70_Games_Entertain",
                "reason": "Steam is a game and entertainment platform.",
                "confidence": 0.95,
            },
            SoftwareCategory.GAMES_ENTERTAIN,
            r"D:\70_Games_Entertain",
        ),
    ],
)
def test_use_case_handles_core_software_categories(
    software_name: str,
    payload: dict[str, object],
    expected_category: SoftwareCategory,
    expected_path: str,
) -> None:
    classifier = _StubClassifier(payload)
    use_case = SuggestInstallPathUseCase(
        settings=_settings_fixture(),
        llm_classifier=classifier,
        rules_loader=lambda _path: "mock-rules",
        rules_parser=lambda _text: _parsed_rules_fixture(),
    )

    result = use_case.execute(software_name=software_name)

    assert result.software_category is expected_category
    assert result.suggested_install_path == expected_path
    assert result.fallback_used is False
    assert result.needs_confirmation is True
    assert classifier.last_request is not None
    assert any("D drive" in item for item in classifier.last_request.rule_summary)
    assert (
        classifier.last_request.category_profiles[SoftwareCategory.PRODUCTIVITY].definition
        == "Communication and collaboration software."
    )


def test_use_case_falls_back_when_software_cannot_be_reliably_classified() -> None:
    classifier = _StubClassifier(
        {
            "category": "unknown",
            "suggested_path": r"D:\80_Misc",
            "reason": "Category is uncertain.",
            "confidence": 0.71,
        }
    )
    use_case = SuggestInstallPathUseCase(
        settings=_settings_fixture(),
        llm_classifier=classifier,
        rules_loader=lambda _path: "mock-rules",
        rules_parser=lambda _text: _parsed_rules_fixture(),
    )

    result = use_case.execute(software_name="Some Niche Tool")

    assert result.fallback_used is True
    assert result.fallback_status is FallbackStatus.USED_UNCERTAIN_RESULT
    assert result.suggested_install_path.startswith("D:\\")
    assert result.needs_confirmation is True

