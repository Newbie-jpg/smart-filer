from smart_filer.application.services.llm_response_service import (
    build_install_suggestion_from_llm,
)
from smart_filer.domain.models import LLMInstallPathResponse, ParsedInstallRules, SoftwareCategory
from smart_filer.domain.models.rule_metadata import FallbackStatus
from smart_filer.infrastructure.providers.siliconflow_adapter import (
    SiliconFlowAdapterResult,
    SiliconFlowResponseError,
    SiliconFlowTimeoutError,
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
        warnings=[],
        rule_basis=["Software should be installed on D drive."],
    )


def _adapter_result(payload: dict[str, object]) -> SiliconFlowAdapterResult:
    return SiliconFlowAdapterResult(
        response=LLMInstallPathResponse.model_validate(payload),
        raw_response_text=str(payload),
        model_id="test-model",
    )


def test_response_service_accepts_valid_structured_response() -> None:
    suggestion = build_install_suggestion_from_llm(
        software_name="OBS Studio",
        parsed_rules=_parsed_rules_fixture(),
        llm_result=_adapter_result(
            {
                "category": "media_design",
                "suggested_path": r"D:\50_Media_Design",
                "reason": "OBS is a media production tool.",
                "confidence": 0.9,
            }
        ),
    )

    assert suggestion.software_category is SoftwareCategory.MEDIA_DESIGN
    assert suggestion.suggested_install_path == r"D:\50_Media_Design"
    assert suggestion.fallback_used is False
    assert suggestion.fallback_status is FallbackStatus.NOT_USED


def test_response_service_falls_back_on_non_json_output() -> None:
    suggestion = build_install_suggestion_from_llm(
        software_name="OBS Studio",
        parsed_rules=_parsed_rules_fixture(),
        llm_error=SiliconFlowResponseError("non-JSON structured content"),
    )

    assert suggestion.fallback_used is True
    assert suggestion.fallback_status is FallbackStatus.USED_VALIDATION_ERROR
    assert suggestion.suggested_install_path.startswith("D:\\")


def test_response_service_falls_back_on_missing_required_fields() -> None:
    suggestion = build_install_suggestion_from_llm(
        software_name="OBS Studio",
        parsed_rules=_parsed_rules_fixture(),
        llm_error=SiliconFlowResponseError("failed schema validation"),
    )

    assert suggestion.fallback_used is True
    assert suggestion.fallback_status is FallbackStatus.USED_VALIDATION_ERROR


def test_response_service_falls_back_on_low_confidence() -> None:
    suggestion = build_install_suggestion_from_llm(
        software_name="Unknown Utility",
        parsed_rules=_parsed_rules_fixture(),
        llm_result=_adapter_result(
            {
                "category": "system_utilities",
                "suggested_path": r"D:\60_System_Utilities",
                "reason": "Likely a utility but uncertain.",
                "confidence": 0.3,
            }
        ),
    )

    assert suggestion.fallback_used is True
    assert suggestion.fallback_status is FallbackStatus.USED_UNCERTAIN_RESULT


def test_response_service_falls_back_on_s_drive_path() -> None:
    suggestion = build_install_suggestion_from_llm(
        software_name="OBS Studio",
        parsed_rules=_parsed_rules_fixture(),
        llm_result=_adapter_result(
            {
                "category": "media_design",
                "suggested_path": r"S:\001_Workspace\OBS",
                "reason": "Should be easy to access from workspace.",
                "confidence": 0.92,
            }
        ),
    )

    assert suggestion.fallback_used is True
    assert suggestion.fallback_status is FallbackStatus.USED_VALIDATION_ERROR
    assert suggestion.suggested_install_path.startswith("D:\\")


def test_response_service_falls_back_when_llm_request_fails() -> None:
    suggestion = build_install_suggestion_from_llm(
        software_name="Altium Designer",
        parsed_rules=_parsed_rules_fixture(),
        llm_error=SiliconFlowTimeoutError("timed out"),
    )

    assert suggestion.fallback_used is True
    assert suggestion.fallback_status is FallbackStatus.USED_LLM_ERROR
    assert suggestion.suggested_install_path.startswith("D:\\")
