"""Intermediate rule representation parsed from rule documents."""

from pydantic import BaseModel, ConfigDict, Field

from smart_filer.domain.models.software_category import SoftwareCategory


class CategoryRuleProfile(BaseModel):
    """Structured category guidance extracted from the machine rules document."""

    model_config = ConfigDict(extra="forbid")

    definition: str = Field(min_length=1)
    includes: list[str] = Field(default_factory=list)
    excludes: list[str] = Field(default_factory=list)


class ParsedInstallRules(BaseModel):
    """Structured install-path rules extracted from rule documents."""

    model_config = ConfigDict(extra="forbid")

    d_drive_preferred: bool
    discourage_s_drive_install: bool
    fallback_install_path: str = Field(default=r"D:\10_Environments", min_length=1)
    category_install_paths: dict[SoftwareCategory, str] = Field(default_factory=dict)
    category_profiles: dict[SoftwareCategory, CategoryRuleProfile] = Field(
        default_factory=dict
    )
    warnings: list[str] = Field(default_factory=list)
    rule_basis: list[str] = Field(default_factory=list)

    def default_d_drive_path(self) -> str:
        """Return a conservative D-drive fallback path."""

        fallback_path = self.fallback_install_path.strip()
        if fallback_path:
            return fallback_path

        for path in self.category_install_paths.values():
            if path.upper().startswith("D:\\"):
                return path

        return r"D:\10_Environments"
