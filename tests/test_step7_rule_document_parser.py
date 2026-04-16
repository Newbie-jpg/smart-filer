from pathlib import Path

from smart_filer.domain.models.software_category import SoftwareCategory
from smart_filer.infrastructure.rules.document_loader import load_rules_document
from smart_filer.infrastructure.rules.document_parser import parse_install_rules


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parser_extracts_d_drive_and_s_drive_constraints_from_rules_doc() -> None:
    text = load_rules_document(REPO_ROOT / "文件结构.md")

    rules = parse_install_rules(text)

    assert rules.d_drive_preferred is True
    assert rules.discourage_s_drive_install is True


def test_parser_extracts_category_to_install_path_mappings() -> None:
    text = load_rules_document(REPO_ROOT / "文件结构.md")

    rules = parse_install_rules(text)

    assert (
        rules.category_install_paths[SoftwareCategory.DEVELOPMENT_ENVIRONMENT]
        == r"D:\10_Environments"
    )
    assert (
        rules.category_install_paths[SoftwareCategory.ENGINEERING]
        == r"D:\30_Engineering"
    )
    assert (
        rules.category_install_paths[SoftwareCategory.PRODUCTIVITY]
        == r"D:\40_Productivity"
    )
    assert (
        rules.category_install_paths[SoftwareCategory.MEDIA_DESIGN]
        == r"D:\50_Media_Design"
    )
    assert (
        rules.category_install_paths[SoftwareCategory.SYSTEM_UTILITIES]
        == r"D:\60_System_Utilities"
    )
    assert (
        rules.category_install_paths[SoftwareCategory.GAMES_ENTERTAIN]
        == r"D:\70_Games_Entertain"
    )


def test_parser_keeps_warning_for_unknown_mapping_format() -> None:
    text = """
    总原则：数据归 `S:`，执行归 `D:`。
    怪异映射：神秘类别 -> D:\\99_Misc
    """

    rules = parse_install_rules(text)

    assert rules.warnings
    assert any("Unrecognized mapping line" in warning for warning in rules.warnings)
