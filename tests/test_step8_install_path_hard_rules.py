from smart_filer.domain.models.parsed_rules import ParsedInstallRules
from smart_filer.domain.models.software_category import SoftwareCategory
from smart_filer.domain.services.install_path_hard_rules import (
    apply_install_path_hard_rules,
)


def _parsed_rules_fixture() -> ParsedInstallRules:
    return ParsedInstallRules(
        d_drive_preferred=True,
        discourage_s_drive_install=True,
        category_install_paths={
            SoftwareCategory.DEVELOPMENT_ENVIRONMENT: r"D:\10_Environments",
            SoftwareCategory.ENGINEERING: r"D:\30_Engineering",
            SoftwareCategory.PRODUCTIVITY: r"D:\40_Productivity",
            SoftwareCategory.MEDIA_DESIGN: r"D:\50_Media_Design",
            SoftwareCategory.SYSTEM_UTILITIES: r"D:\60_System_Utilities",
            SoftwareCategory.GAMES_ENTERTAIN: r"D:\70_Games_Entertain",
        },
        warnings=[],
        rule_basis=["数据归 S 盘，执行归 D 盘。"],
    )


def test_hard_rules_prefer_category_mapping_over_llm_path() -> None:
    result = apply_install_path_hard_rules(
        software_category=SoftwareCategory.MEDIA_DESIGN,
        llm_suggested_path=r"D:\40_Productivity",
        parsed_rules=_parsed_rules_fixture(),
    )

    assert result.final_install_path == r"D:\50_Media_Design"
    assert result.path_overridden is True


def test_hard_rules_rewrite_s_drive_path_to_d_drive() -> None:
    result = apply_install_path_hard_rules(
        software_category=SoftwareCategory.UNKNOWN,
        llm_suggested_path=r"S:\001_Workspace\Tools",
        parsed_rules=_parsed_rules_fixture(),
    )

    assert result.final_install_path.startswith("D:\\")
    assert result.path_overridden is True
    assert any("S drive" in message for message in result.violations)


def test_hard_rules_keep_valid_d_drive_when_no_category_mapping() -> None:
    result = apply_install_path_hard_rules(
        software_category=SoftwareCategory.UNKNOWN,
        llm_suggested_path=r"D:\90_CustomTools",
        parsed_rules=_parsed_rules_fixture(),
    )

    assert result.final_install_path == r"D:\90_CustomTools"
    assert result.path_overridden is False


def test_hard_rules_rewrite_non_d_drive_path() -> None:
    result = apply_install_path_hard_rules(
        software_category=SoftwareCategory.UNKNOWN,
        llm_suggested_path=r"C:\Program Files\SomeTool",
        parsed_rules=_parsed_rules_fixture(),
    )

    assert result.final_install_path.startswith("D:\\")
    assert result.path_overridden is True
    assert any("must be under D drive" in message for message in result.violations)
