"""Structured LLM request/response models for software classification."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from smart_filer.domain.models.parsed_rules import CategoryRuleProfile
from smart_filer.domain.models.software_category import SoftwareCategory


class LLMInstallPathRequest(BaseModel):
    """Input payload sent to LLM provider for software classification."""

    model_config = ConfigDict(extra="forbid")

    software_name: str = Field(min_length=1)
    rule_summary: list[str] = Field(min_length=1)
    category_profiles: dict[SoftwareCategory, CategoryRuleProfile] = Field(
        default_factory=dict
    )
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

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    software_category: SoftwareCategory = Field(alias="category")
    suggested_install_path: str = Field(alias="suggested_path", min_length=1)
    reason: str = Field(min_length=1)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]

    @model_validator(mode="before")
    @classmethod
    def _normalize_common_response_keys(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        normalized = dict(value)

        category_aliases = (
            "software_category",
            "classification",
            "category_name",
            "type",
        )
        path_aliases = (
            "install_path",
            "recommended_path",
            "final_path",
            "path",
        )

        if "category" not in normalized:
            for alias in category_aliases:
                alias_value = normalized.get(alias)
                if alias_value is not None:
                    normalized["category"] = alias_value
                    break

        if "suggested_path" not in normalized:
            for alias in path_aliases:
                alias_value = normalized.get(alias)
                if alias_value is not None:
                    normalized["suggested_path"] = alias_value
                    break

        return normalized

    @field_validator("software_category", mode="before")
    @classmethod
    def _normalize_software_category(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        normalized = value.strip().lower()
        if not normalized:
            return SoftwareCategory.UNKNOWN.value

        canonical = normalized.replace("-", "_").replace(" ", "_")
        aliases = {
            "development_tools": SoftwareCategory.DEVELOPMENT_ENVIRONMENT.value,
            "dev_environment": SoftwareCategory.DEVELOPMENT_ENVIRONMENT.value,
            "development_environment_sdk": SoftwareCategory.DEVELOPMENT_ENVIRONMENT.value,
            "media": SoftwareCategory.MEDIA_DESIGN.value,
            "media_design_tools": SoftwareCategory.MEDIA_DESIGN.value,
            "system_utility": SoftwareCategory.SYSTEM_UTILITIES.value,
            "utilities": SoftwareCategory.SYSTEM_UTILITIES.value,
            "game_entertainment": SoftwareCategory.GAMES_ENTERTAIN.value,
            "games": SoftwareCategory.GAMES_ENTERTAIN.value,
        }
        allowed_values = {item.value for item in SoftwareCategory}
        if canonical in allowed_values:
            return canonical
        return aliases.get(canonical, SoftwareCategory.UNKNOWN.value)

    @field_validator("confidence", mode="before")
    @classmethod
    def _normalize_confidence(cls, value: object) -> object:
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned.endswith("%"):
                number = float(cleaned[:-1].strip())
                return number / 100.0
            return float(cleaned)
        return value
