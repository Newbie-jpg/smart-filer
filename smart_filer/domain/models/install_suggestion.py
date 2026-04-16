"""Domain model for software install-path suggestion output."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from smart_filer.domain.models.rule_metadata import FallbackStatus, RuleBasis
from smart_filer.domain.models.software_category import SoftwareCategory


class InstallSuggestion(BaseModel):
    """Structured suggestion output for software install location."""

    model_config = ConfigDict(extra="forbid")

    software_name: str = Field(min_length=1)
    software_category: SoftwareCategory
    suggested_install_path: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    needs_confirmation: bool = True
    fallback_status: FallbackStatus = FallbackStatus.NOT_USED
    fallback_used: bool = False
    rule_basis: list[RuleBasis] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_fallback_flags(self) -> "InstallSuggestion":
        fallback_was_used = self.fallback_status != FallbackStatus.NOT_USED
        if fallback_was_used != self.fallback_used:
            raise ValueError(
                "fallback_used must match fallback_status (not_used vs used_*)."
            )
        if not self.needs_confirmation:
            raise ValueError("needs_confirmation must be true in current version.")
        return self
