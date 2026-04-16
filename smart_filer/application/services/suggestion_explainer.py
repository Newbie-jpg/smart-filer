"""Readable explanation builder for install suggestions."""

from pydantic import BaseModel, ConfigDict, Field

from smart_filer.domain.models import InstallSuggestion


class SuggestionExplanation(BaseModel):
    """Presentation-ready explanation for one install suggestion."""

    model_config = ConfigDict(extra="forbid")

    why_this_path: str = Field(min_length=1)
    rule_basis: list[str] = Field(min_length=1)
    fallback_note: str = Field(min_length=1)


def build_suggestion_explanation(
    suggestion: InstallSuggestion,
) -> SuggestionExplanation:
    """Convert a domain suggestion into stable, readable explanation fields."""

    why_this_path = (
        f"{suggestion.software_name} is classified as "
        f"{suggestion.software_category.value}, so the suggested install path is "
        f"{suggestion.suggested_install_path}. Reason: {suggestion.reason}"
    )

    sorted_basis = sorted(
        suggestion.rule_basis,
        key=lambda item: (-int(item.priority), item.source.value, item.summary.lower()),
    )
    readable_rule_basis = [
        (
            f"{item.source.value} (priority={int(item.priority)}): "
            f"{item.summary}"
        )
        for item in sorted_basis
    ]

    if suggestion.fallback_used:
        fallback_note = (
            f"Fallback used ({suggestion.fallback_status.value}). "
            f"Trigger: {suggestion.reason}"
        )
    else:
        fallback_note = (
            "Fallback not used. Suggestion still requires manual confirmation."
        )

    return SuggestionExplanation(
        why_this_path=why_this_path,
        rule_basis=readable_rule_basis,
        fallback_note=fallback_note,
    )

