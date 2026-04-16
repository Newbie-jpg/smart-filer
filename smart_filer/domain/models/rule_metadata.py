"""Rule-related domain objects."""

from enum import Enum, IntEnum

from pydantic import BaseModel, ConfigDict, Field


class RuleSource(str, Enum):
    """Where a rule or rule hint comes from."""

    DOCUMENT = "document"
    HARD_RULE = "hard_rule"
    LLM = "llm"
    FALLBACK = "fallback"


class RulePriority(IntEnum):
    """Rule priority. Larger value means higher priority."""

    LLM_HINT = 100
    DOCUMENT_RULE = 500
    HARD_CONSTRAINT = 900
    FALLBACK_GUARD = 1000


class FallbackStatus(str, Enum):
    """Status to indicate whether fallback is used."""

    NOT_USED = "not_used"
    USED_LLM_ERROR = "used_llm_error"
    USED_VALIDATION_ERROR = "used_validation_error"
    USED_UNCERTAIN_RESULT = "used_uncertain_result"


class RuleBasis(BaseModel):
    """Structured rule basis item used for explainability."""

    model_config = ConfigDict(extra="forbid")

    source: RuleSource
    priority: RulePriority
    summary: str = Field(min_length=1)
