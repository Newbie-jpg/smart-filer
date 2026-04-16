import pytest
from pydantic import ValidationError

from smart_filer.domain.models import LLMInstallPathRequest, LLMInstallPathResponse


def test_llm_request_model_accepts_required_fields() -> None:
    request = LLMInstallPathRequest(
        software_name="OBS Studio",
        rule_summary=[
            "软件与运行环境优先进入 D 盘体系。",
            "媒体设计类软件优先安装到 D:\\50_Media_Design。",
        ],
        aliases=["OBS"],
        context="用户主要用于直播录屏。",
    )

    dumped = request.model_dump(mode="json")
    assert dumped["software_name"] == "OBS Studio"
    assert dumped["aliases"] == ["OBS"]
    assert len(dumped["rule_summary"]) == 2


def test_llm_request_model_rejects_empty_rule_summary_item() -> None:
    with pytest.raises(ValidationError):
        LLMInstallPathRequest(
            software_name="7-Zip",
            rule_summary=["", "软件不建议安装到 S 盘。"],
        )


def test_llm_response_model_parses_controlled_fields_from_llm_json() -> None:
    payload = {
        "category": "system_utilities",
        "suggested_path": r"D:\60_System_Utilities",
        "reason": "压缩工具属于系统工具类。",
        "confidence": 0.88,
    }

    response = LLMInstallPathResponse.model_validate(payload)
    serialized = response.model_dump(mode="json", by_alias=True)

    assert serialized["category"] == "system_utilities"
    assert serialized["suggested_path"] == r"D:\60_System_Utilities"


def test_llm_response_model_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        LLMInstallPathResponse.model_validate(
            {
                "category": "engineering",
                "suggested_path": r"D:\30_Engineering",
                "confidence": 0.74,
            }
        )


def test_llm_response_model_normalizes_common_category_and_confidence_formats() -> None:
    payload = {
        "category": "Development Tools",
        "suggested_path": r"D:\10_Environments",
        "reason": "Development tools should stay under environments path.",
        "confidence": "84%",
    }

    response = LLMInstallPathResponse.model_validate(payload)

    assert response.software_category.value == "development_environment"
    assert response.confidence == pytest.approx(0.84)


def test_llm_response_model_ignores_extra_keys() -> None:
    payload = {
        "category": "media_design",
        "suggested_path": r"D:\50_Media_Design",
        "reason": "Media tool.",
        "confidence": 0.8,
        "needs_confirmation": True,
        "software_recommendation": None,
    }

    response = LLMInstallPathResponse.model_validate(payload)
    dumped = response.model_dump(mode="json", by_alias=True)

    assert dumped["category"] == "media_design"
    assert "needs_confirmation" not in dumped
