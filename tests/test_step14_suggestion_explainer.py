from smart_filer.application.services.suggestion_explainer import (
    build_suggestion_explanation,
)
from smart_filer.domain.models import InstallSuggestion, SoftwareCategory
from smart_filer.domain.models.rule_metadata import (
    FallbackStatus,
    RuleBasis,
    RulePriority,
    RuleSource,
)


def test_explainer_produces_stable_readable_reason_and_rule_basis() -> None:
    suggestion = InstallSuggestion(
        software_name="OBS Studio",
        software_category=SoftwareCategory.MEDIA_DESIGN,
        suggested_install_path=r"D:\50_Media_Design",
        reason="OBS is used for recording and live streaming tasks.",
        confidence=0.9,
        needs_confirmation=True,
        fallback_status=FallbackStatus.NOT_USED,
        fallback_used=False,
        rule_basis=[
            RuleBasis(
                source=RuleSource.LLM,
                priority=RulePriority.LLM_HINT,
                summary="LLM classified OBS as media_design.",
            ),
            RuleBasis(
                source=RuleSource.HARD_RULE,
                priority=RulePriority.HARD_CONSTRAINT,
                summary="Software install suggestions must stay in D drive.",
            ),
        ],
    )

    first = build_suggestion_explanation(suggestion)
    second = build_suggestion_explanation(suggestion)

    assert first == second
    assert "OBS Studio" in first.why_this_path
    assert r"D:\50_Media_Design" in first.why_this_path
    assert "Reason:" in first.why_this_path
    assert first.rule_basis[0].startswith("hard_rule (priority=900)")
    assert "Fallback not used" in first.fallback_note


def test_explainer_keeps_fallback_reason_complete_when_fallback_is_used() -> None:
    suggestion = InstallSuggestion(
        software_name="Unknown Tool",
        software_category=SoftwareCategory.UNKNOWN,
        suggested_install_path=r"D:\10_Environments",
        reason="LLM confidence 0.20 is below threshold 0.65.",
        confidence=0.2,
        needs_confirmation=True,
        fallback_status=FallbackStatus.USED_UNCERTAIN_RESULT,
        fallback_used=True,
        rule_basis=[
            RuleBasis(
                source=RuleSource.FALLBACK,
                priority=RulePriority.FALLBACK_GUARD,
                summary="Fallback keeps suggestion inside D drive hierarchy.",
            )
        ],
    )

    explanation = build_suggestion_explanation(suggestion)

    assert "Fallback used (used_uncertain_result)" in explanation.fallback_note
    assert suggestion.reason in explanation.fallback_note
    assert explanation.rule_basis[0].startswith("fallback (priority=1000)")

