import pytest
from pydantic import ValidationError

from smart_filer.domain.models import (
    FallbackStatus,
    InstallSuggestion,
    RuleBasis,
    RulePriority,
    RuleSource,
    SoftwareCategory,
)


def _sample_rule_basis() -> list[RuleBasis]:
    return [
        RuleBasis(
            source=RuleSource.DOCUMENT,
            priority=RulePriority.DOCUMENT_RULE,
            summary="软件与运行环境优先进入 D 盘体系",
        )
    ]


def test_software_category_enum_and_round_trip() -> None:
    category = SoftwareCategory("media_design")
    assert category is SoftwareCategory.MEDIA_DESIGN
    assert category.value == "media_design"

    payload = {
        "software_name": "OBS Studio",
        "software_category": "media_design",
        "suggested_install_path": r"D:\50_Media_Design",
        "reason": "音视频工具建议安装到媒体设计目录。",
        "confidence": 0.84,
        "needs_confirmation": True,
        "fallback_status": "not_used",
        "fallback_used": False,
        "rule_basis": [item.model_dump(mode="json") for item in _sample_rule_basis()],
    }
    model = InstallSuggestion.model_validate(payload)
    serialized = model.model_dump(mode="json")

    assert serialized["software_category"] == "media_design"
    assert InstallSuggestion.model_validate(serialized) == model


def test_invalid_enum_value_is_rejected() -> None:
    with pytest.raises(ValueError):
        SoftwareCategory("video_editor")


def test_install_suggestion_field_constraints_are_enforced() -> None:
    with pytest.raises(ValidationError):
        InstallSuggestion(
            software_name="",
            software_category=SoftwareCategory.SYSTEM_UTILITIES,
            suggested_install_path=r"D:\60_System_Utilities",
            reason="",
            confidence=1.2,
            needs_confirmation=True,
            fallback_status=FallbackStatus.NOT_USED,
            fallback_used=False,
            rule_basis=[],
        )


def test_install_suggestion_fallback_consistency_is_enforced() -> None:
    with pytest.raises(ValidationError):
        InstallSuggestion(
            software_name="Unknown Tool",
            software_category=SoftwareCategory.UNKNOWN,
            suggested_install_path=r"D:\10_Environments",
            reason="需要人工判定。",
            confidence=0.3,
            needs_confirmation=True,
            fallback_status=FallbackStatus.USED_LLM_ERROR,
            fallback_used=False,
            rule_basis=_sample_rule_basis(),
        )


def test_rule_basis_serialization_uses_controlled_enums() -> None:
    basis = RuleBasis(
        source=RuleSource.HARD_RULE,
        priority=RulePriority.HARD_CONSTRAINT,
        summary="不建议安装到 S 盘。",
    )

    dumped = basis.model_dump(mode="json")
    assert dumped == {
        "source": "hard_rule",
        "priority": 900,
        "summary": "不建议安装到 S 盘。",
    }
