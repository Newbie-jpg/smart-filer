"""Hard-rule enforcement for software install path suggestions."""

from pydantic import BaseModel, ConfigDict, Field

from smart_filer.domain.models.parsed_rules import ParsedInstallRules
from smart_filer.domain.models.rule_metadata import RuleBasis, RulePriority, RuleSource
from smart_filer.domain.models.software_category import SoftwareCategory


class HardRuleDecision(BaseModel):
    """Decision result after hard-rule enforcement."""

    model_config = ConfigDict(extra="forbid")

    final_install_path: str = Field(min_length=1)
    path_overridden: bool
    violations: list[str] = Field(default_factory=list)
    rule_basis: list[RuleBasis] = Field(min_length=1)


def _is_d_drive_path(path: str) -> bool:
    normalized = path.strip().replace("/", "\\")
    return normalized.upper().startswith("D:\\")


def apply_install_path_hard_rules(
    software_category: SoftwareCategory,
    llm_suggested_path: str | None,
    parsed_rules: ParsedInstallRules,
) -> HardRuleDecision:
    """Apply hard constraints on top of LLM suggestions."""

    candidate = (llm_suggested_path or "").strip()
    mapped_path = parsed_rules.category_install_paths.get(software_category)

    rule_basis: list[RuleBasis] = []
    violations: list[str] = []
    overridden = False

    if mapped_path:
        final_path = mapped_path
        if candidate and candidate != mapped_path:
            overridden = True
        rule_basis.append(
            RuleBasis(
                source=RuleSource.DOCUMENT,
                priority=RulePriority.DOCUMENT_RULE,
                summary=(
                    "Category mapping from rule document is preferred "
                    "for install path suggestion."
                ),
            )
        )
    else:
        final_path = candidate

    if not final_path or not _is_d_drive_path(final_path):
        fallback_path = parsed_rules.default_d_drive_path()
        if candidate.upper().startswith("S:\\"):
            violations.append("Install path on S drive is not allowed for software.")
        elif candidate:
            violations.append("Install path must be under D drive software hierarchy.")
        else:
            violations.append("Missing install path from upstream suggestion.")

        final_path = fallback_path
        overridden = True
        rule_basis.append(
            RuleBasis(
                source=RuleSource.HARD_RULE,
                priority=RulePriority.HARD_CONSTRAINT,
                summary="Software install suggestions must stay in D drive hierarchy.",
            )
        )

    if parsed_rules.discourage_s_drive_install:
        rule_basis.append(
            RuleBasis(
                source=RuleSource.HARD_RULE,
                priority=RulePriority.HARD_CONSTRAINT,
                summary="S drive is for data, not software installation.",
            )
        )

    if not rule_basis:
        rule_basis.append(
            RuleBasis(
                source=RuleSource.HARD_RULE,
                priority=RulePriority.HARD_CONSTRAINT,
                summary="Default D drive hard rule applied.",
            )
        )

    return HardRuleDecision(
        final_install_path=final_path,
        path_overridden=overridden,
        violations=violations,
        rule_basis=rule_basis,
    )
