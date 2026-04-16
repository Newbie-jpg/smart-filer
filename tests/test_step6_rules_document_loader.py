from pathlib import Path
from uuid import uuid4

import pytest

from smart_filer.infrastructure.rules.document_loader import (
    RulesDocumentError,
    load_rules_document,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_TEST_DIR = REPO_ROOT / ".test-runtime" / "rule-loader"


def _new_runtime_file(suffix: str) -> Path:
    RUNTIME_TEST_DIR.mkdir(parents=True, exist_ok=True)
    return RUNTIME_TEST_DIR / "{name}{suffix}".format(name=uuid4(), suffix=suffix)


def test_loader_reads_repository_rules_document() -> None:
    content = load_rules_document(REPO_ROOT / "文档结构.rule.md")

    assert len(content) > 20
    assert "global_rules:" in content


def test_loader_reads_utf8_chinese_content_correctly() -> None:
    file_path = _new_runtime_file(".md")
    expected = "中文规则：软件与运行环境优先进入 D 盘。"
    file_path.write_text(expected, encoding="utf-8")

    loaded = load_rules_document(file_path)
    assert loaded == expected


def test_loader_raises_clear_error_when_file_missing() -> None:
    missing = _new_runtime_file(".missing.md")

    with pytest.raises(RulesDocumentError) as error:
        load_rules_document(missing)

    assert str(missing) in str(error.value)
    assert "does not exist" in str(error.value)


def test_loader_raises_clear_error_for_empty_file() -> None:
    empty_file = _new_runtime_file(".empty.md")
    empty_file.write_text("   \n\t", encoding="utf-8")

    with pytest.raises(RulesDocumentError) as error:
        load_rules_document(empty_file)

    assert "is empty" in str(error.value)


def test_loader_raises_clear_error_for_invalid_encoding() -> None:
    invalid = _new_runtime_file(".bin")
    invalid.write_bytes(b"\xff\xfe\x00\x00\x81")

    with pytest.raises(RulesDocumentError) as error:
        load_rules_document(invalid)

    assert "invalid UTF-8" in str(error.value)
