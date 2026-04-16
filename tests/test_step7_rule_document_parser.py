from pathlib import Path

import pytest

from smart_filer.domain.models.software_category import SoftwareCategory
from smart_filer.infrastructure.rules.document_loader import load_rules_document
from smart_filer.infrastructure.rules.document_parser import (
    RuleDocumentParseError,
    parse_install_rules,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parser_extracts_global_constraints_from_machine_rules_doc() -> None:
    text = load_rules_document(REPO_ROOT / "文档结构.rule.md")

    rules = parse_install_rules(text)

    assert rules.d_drive_preferred is True
    assert rules.discourage_s_drive_install is True
    assert rules.fallback_install_path == r"D:\60_System_Utilities"


def test_parser_extracts_category_to_install_path_mappings_from_machine_rules_doc() -> None:
    text = load_rules_document(REPO_ROOT / "文档结构.rule.md")

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


def test_parser_raises_clear_error_when_required_section_missing() -> None:
    text = """
metadata:
  rules_version: 1
  document_type: smart_filer_machine_rules
  document_status: active
  platform: windows
  path_style: windows_absolute
"""

    with pytest.raises(RuleDocumentParseError) as error:
        parse_install_rules(text)

    assert "Missing required top-level section" in str(error.value)
