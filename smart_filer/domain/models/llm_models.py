"""Structured LLM request/response models for software classification."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from smart_filer.domain.models.software_category import SoftwareCategory


class LLMInstallPathRequest(BaseModel):
    """Input payload sent to LLM provider for software classification."""

    model_config = ConfigDict(extra="forbid")

    software_name: str = Field(min_length=1)
    rule_summary: list[str] = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    context: str | None = None

    @field_validator("rule_summary", "aliases")
    @classmethod
    def _validate_non_empty_items(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for item in values:
            cleaned = item.strip()
            if not cleaned:
                raise ValueError("List items must be non-empty strings.")
            normalized.append(cleaned)
        return normalized


class LLMInstallPathResponse(BaseModel):
    """Structured LLM response used by downstream rule validation."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    software_category: SoftwareCategory = Field(alias="category")
    suggested_install_path: str = Field(alias="suggested_path", min_length=1)
    reason: str = Field(min_length=1)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
