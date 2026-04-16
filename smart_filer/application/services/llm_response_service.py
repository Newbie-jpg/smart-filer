"""Convert provider output into install suggestions with fallback guards."""

from __future__ import annotations

from typing import Final

from smart_filer.domain.models.install_suggestion import InstallSuggestion
from smart_filer.domain.models.parsed_rules import ParsedInstallRules
from smart_filer.domain.models.rule_metadata import (
    FallbackStatus,
    RuleBasis,
    RulePriority,
    RuleSource,
)
from smart_filer.domain.models.software_category import SoftwareCategory
from smart_filer.domain.services.install_path_hard_rules import apply_install_path_hard_rules
from smart_filer.infrastructure.providers.siliconflow_adapter import (
    SiliconFlowAdapterResult,
    SiliconFlowResponseError,
)


DEFAULT_LOW_CONFIDENCE_THRESHOLD: Final[float] = 0.65
FALLBACK_CONFIDENCE: Final[float] = 0.2


def build_install_suggestion_from_llm(
    *,
    software_name: str,
    parsed_rules: ParsedInstallRules,
    llm_result: SiliconFlowAdapterResult | None = None,
    llm_error: Exception | None = None,
    low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
) -> InstallSuggestion:
    """Resolve LLM output to a stable suggestion and fallback when needed."""

    if llm_result is None and llm_error is None:
        raise ValueError("Either llm_result or llm_error must be provided.")
    if llm_result is not None and llm_error is not None:
        raise ValueError("llm_result and llm_error cannot be provided together.")
    if not 0.0 <= low_confidence_threshold <= 1.0:
        raise ValueError("low_confidence_threshold must be between 0.0 and 1.0.")

    if llm_error is not None:
        status = (
            FallbackStatus.USED_VALIDATION_ERROR
            if isinstance(llm_error, SiliconFlowResponseError)
            else FallbackStatus.USED_LLM_ERROR
        )
        return _build_fallback_suggestion(
            software_name=software_name,
            parsed_rules=parsed_rules,
            fallback_status=status,
            reason=f"LLM request failed: {llm_error}",
        )

    assert llm_result is not None
    response = llm_result.response

    resolved_category = response.software_category

    if resolved_category is SoftwareCategory.UNKNOWN:
        return _build_fallback_suggestion(
            software_name=software_name,
            parsed_rules=parsed_rules,
            fallback_status=FallbackStatus.USED_UNCERTAIN_RESULT,
            reason="LLM returned unknown software category.",
        )

    if response.confidence < low_confidence_threshold:
        return _build_fallback_suggestion(
            software_name=software_name,
            parsed_rules=parsed_rules,
            fallback_status=FallbackStatus.USED_UNCERTAIN_RESULT,
            reason=(
                "LLM confidence %.2f is below threshold %.2f."
                % (response.confidence, low_confidence_threshold)
            ),
            category=resolved_category,
        )

    hard_rule_decision = apply_install_path_hard_rules(
        software_category=resolved_category,
        llm_suggested_path=None,
        parsed_rules=parsed_rules,
    )
    llm_rule_summary = (
        "LLM category accepted; install path selected from local category mapping."
    )
    rule_basis = [
        RuleBasis(
            source=RuleSource.LLM,
            priority=RulePriority.LLM_HINT,
            summary=llm_rule_summary,
        ),
        *hard_rule_decision.rule_basis,
    ]

    return InstallSuggestion(
        software_name=software_name,
        software_category=resolved_category,
        suggested_install_path=hard_rule_decision.final_install_path,
        reason=response.reason,
        confidence=response.confidence,
        needs_confirmation=True,
        fallback_status=FallbackStatus.NOT_USED,
        fallback_used=False,
        rule_basis=rule_basis,
    )


def _build_fallback_suggestion(
    *,
    software_name: str,
    parsed_rules: ParsedInstallRules,
    fallback_status: FallbackStatus,
    reason: str,
    category: SoftwareCategory = SoftwareCategory.UNKNOWN,
) -> InstallSuggestion:
    return InstallSuggestion(
        software_name=software_name,
        software_category=category,
        suggested_install_path=parsed_rules.default_d_drive_path(),
        reason=reason,
        confidence=FALLBACK_CONFIDENCE,
        needs_confirmation=True,
        fallback_status=fallback_status,
        fallback_used=True,
        rule_basis=[
            RuleBasis(
                source=RuleSource.FALLBACK,
                priority=RulePriority.FALLBACK_GUARD,
                summary=reason,
            ),
            RuleBasis(
                source=RuleSource.HARD_RULE,
                priority=RulePriority.HARD_CONSTRAINT,
                summary="Fallback keeps install suggestion inside D-drive hierarchy.",
            ),
        ],
    )
