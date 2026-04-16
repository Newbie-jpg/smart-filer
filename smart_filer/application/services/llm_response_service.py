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
    used_path_inference = False

    if resolved_category is SoftwareCategory.UNKNOWN:
        inferred_category = _infer_category_from_path(
            suggested_install_path=response.suggested_install_path,
            parsed_rules=parsed_rules,
        )
        if inferred_category is SoftwareCategory.UNKNOWN:
            return _build_fallback_suggestion(
                software_name=software_name,
                parsed_rules=parsed_rules,
                fallback_status=FallbackStatus.USED_UNCERTAIN_RESULT,
                reason="LLM returned unknown software category.",
            )
        resolved_category = inferred_category
        used_path_inference = True

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

    if _is_invalid_install_path(response.suggested_install_path):
        return _build_fallback_suggestion(
            software_name=software_name,
            parsed_rules=parsed_rules,
            fallback_status=FallbackStatus.USED_VALIDATION_ERROR,
            reason="LLM suggested an install path outside D-drive software hierarchy.",
            category=resolved_category,
        )

    if _has_category_conflict(
        software_category=resolved_category,
        suggested_install_path=response.suggested_install_path,
        parsed_rules=parsed_rules,
    ):
        return _build_fallback_suggestion(
            software_name=software_name,
            parsed_rules=parsed_rules,
            fallback_status=FallbackStatus.USED_VALIDATION_ERROR,
            reason="LLM category conflicts with document-defined category mapping.",
            category=resolved_category,
        )

    hard_rule_decision = apply_install_path_hard_rules(
        software_category=resolved_category,
        llm_suggested_path=response.suggested_install_path,
        parsed_rules=parsed_rules,
    )
    llm_rule_summary = (
        "LLM returned unknown category; category inferred from mapped suggested path."
        if used_path_inference
        else "LLM returned valid structured category and path suggestion."
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


def _normalize_windows_path(path: str) -> str:
    return path.strip().replace("/", "\\").rstrip("\\")


def _is_invalid_install_path(path: str) -> bool:
    normalized = _normalize_windows_path(path).upper()
    if normalized.startswith("S:\\"):
        return True
    return not normalized.startswith("D:\\")


def _has_category_conflict(
    *,
    software_category: SoftwareCategory,
    suggested_install_path: str,
    parsed_rules: ParsedInstallRules,
) -> bool:
    mapped_path = parsed_rules.category_install_paths.get(software_category)
    if not mapped_path:
        return False
    return _normalize_windows_path(mapped_path) != _normalize_windows_path(
        suggested_install_path
    )


def _infer_category_from_path(
    *,
    suggested_install_path: str,
    parsed_rules: ParsedInstallRules,
) -> SoftwareCategory:
    normalized_path = _normalize_windows_path(suggested_install_path)
    for category, mapped_path in parsed_rules.category_install_paths.items():
        if _normalize_windows_path(mapped_path) == normalized_path:
            return category
    return SoftwareCategory.UNKNOWN
