"""Domain models for software install path suggestion."""

from smart_filer.domain.models.llm_models import (
    LLMInstallPathRequest,
    LLMInstallPathResponse,
)
from smart_filer.domain.models.install_suggestion import InstallSuggestion
from smart_filer.domain.models.parsed_rules import ParsedInstallRules
from smart_filer.domain.models.rule_metadata import (
    FallbackStatus,
    RuleBasis,
    RulePriority,
    RuleSource,
)
from smart_filer.domain.models.software_category import SoftwareCategory

__all__ = [
    "FallbackStatus",
    "InstallSuggestion",
    "LLMInstallPathRequest",
    "LLMInstallPathResponse",
    "ParsedInstallRules",
    "RuleBasis",
    "RulePriority",
    "RuleSource",
    "SoftwareCategory",
]
