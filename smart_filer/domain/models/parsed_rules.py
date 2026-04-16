"""Intermediate rule representation parsed from rule documents."""

from pydantic import BaseModel, ConfigDict, Field

from smart_filer.domain.models.software_category import SoftwareCategory


class ParsedInstallRules(BaseModel):
    """Structured install-path rules extracted from rule documents."""

    model_config = ConfigDict(extra="forbid")

    d_drive_preferred: bool
    discourage_s_drive_install: bool
    category_install_paths: dict[SoftwareCategory, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    rule_basis: list[str] = Field(default_factory=list)

    def default_d_drive_path(self) -> str:
        """Return a conservative D-drive fallback path."""

        development_path = self.category_install_paths.get(
            SoftwareCategory.DEVELOPMENT_ENVIRONMENT
        )
        if development_path:
            return development_path

        for path in self.category_install_paths.values():
            if path.upper().startswith("D:\\"):
                return path

        return r"D:\10_Environments"
