"""Parse machine-readable rule document text into install-path rules."""

from __future__ import annotations

import re

from smart_filer.domain.models.parsed_rules import ParsedInstallRules
from smart_filer.domain.models.software_category import SoftwareCategory


class RuleDocumentParseError(ValueError):
    """Raised when machine rules document cannot be parsed or validated."""


_REQUIRED_TOP_LEVEL_KEYS = {
    "metadata",
    "global_rules",
    "categories",
    "software_overrides",
    "conflict_resolution",
    "validation_examples",
}
_REQUIRED_CONFLICT_ORDER = [
    "exact_name",
    "alias",
    "override_keyword",
    "category_keyword",
    "category_default",
    "global_hard_rule",
    "fallback",
]
_REQUIRED_OVERRIDE_FIELDS = {
    "software_id",
    "display_names",
    "aliases",
    "priority",
    "category",
    "install_path",
    "reason",
}
_WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:\\")


def _normalize_rule_value(raw_value: str) -> str:
    value = raw_value.strip().strip('"').strip("'")
    return value.replace("\\\\", "\\")


def _normalize_windows_path(path: str) -> str:
    return _normalize_rule_value(path).replace("/", "\\")


def _is_windows_absolute_path(path: str) -> bool:
    return bool(_WINDOWS_ABSOLUTE_PATH.match(path))


def _extract_machine_rules_yaml_block(document_text: str) -> str:
    fenced = re.search(r"```yaml\s*(.*?)\s*```", document_text, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)
    return document_text


def _split_top_level_sections(document_text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_key: str | None = None

    for line in document_text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue

        top_level_key = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$", line)
        if top_level_key is not None:
            current_key = top_level_key.group(1)
            sections[current_key] = []
            inline_value = top_level_key.group(2).strip()
            if inline_value:
                sections[current_key].append(inline_value)
            continue

        if current_key is not None:
            sections[current_key].append(line)

    return sections


def _extract_scalar(lines: list[str], key: str) -> str | None:
    pattern = re.compile(rf"^\s*(?:-\s+)?{re.escape(key)}\s*:\s*(.+?)\s*$")
    for line in lines:
        match = pattern.match(line)
        if match is not None:
            return _normalize_rule_value(match.group(1))
    return None


def _extract_block_list(lines: list[str], key: str) -> list[str]:
    values: list[str] = []
    key_pattern = re.compile(rf"^\s+{re.escape(key)}\s*:\s*$")

    index = 0
    while index < len(lines):
        line = lines[index]
        if key_pattern.match(line) is None:
            index += 1
            continue

        index += 1
        while index < len(lines):
            item_line = lines[index]
            list_item = re.match(r"^\s+-\s+(.+?)\s*$", item_line)
            if list_item is None:
                break
            values.append(_normalize_rule_value(list_item.group(1)))
            index += 1
        break

    return values


def _collect_blocks(lines: list[str], start_pattern: re.Pattern[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] | None = None

    for line in lines:
        if start_pattern.match(line):
            if current:
                blocks.append(current)
            current = [line]
            continue

        if current is not None:
            current.append(line)

    if current:
        blocks.append(current)

    return blocks


def _parse_metadata(lines: list[str]) -> None:
    rules_version = _extract_scalar(lines, "rules_version")
    document_type = _extract_scalar(lines, "document_type")
    platform = _extract_scalar(lines, "platform")
    path_style = _extract_scalar(lines, "path_style")

    if rules_version is None or not rules_version.isdigit():
        raise RuleDocumentParseError("metadata.rules_version must be an integer.")
    if document_type != "smart_filer_machine_rules":
        raise RuleDocumentParseError(
            "metadata.document_type must be smart_filer_machine_rules."
        )
    if platform != "windows":
        raise RuleDocumentParseError("metadata.platform must be windows.")
    if path_style != "windows_absolute":
        raise RuleDocumentParseError("metadata.path_style must be windows_absolute.")


def _parse_global_rules(lines: list[str]) -> tuple[bool, bool, str, list[str]]:
    preferred_install_drive = _extract_scalar(lines, "preferred_install_drive")
    forbidden_install_roots = [
        _normalize_windows_path(item) for item in _extract_block_list(lines, "forbidden_install_roots")
    ]
    fallback_install_path = _extract_scalar(lines, "fallback_install_path")
    allow_only_local_paths = _extract_scalar(lines, "allow_only_local_paths")

    if preferred_install_drive != "D:":
        raise RuleDocumentParseError(
            "global_rules.preferred_install_drive must be D:."
        )
    if not forbidden_install_roots:
        raise RuleDocumentParseError(
            "global_rules.forbidden_install_roots must contain at least one path."
        )
    if not any(root.upper().startswith("S:\\") for root in forbidden_install_roots):
        raise RuleDocumentParseError(
            "global_rules.forbidden_install_roots must include S:\\."
        )

    if fallback_install_path is None:
        raise RuleDocumentParseError(
            "global_rules.fallback_install_path is required."
        )
    normalized_fallback_path = _normalize_windows_path(fallback_install_path)
    if not _is_windows_absolute_path(normalized_fallback_path):
        raise RuleDocumentParseError(
            "global_rules.fallback_install_path must be a Windows absolute path."
        )
    if not normalized_fallback_path.upper().startswith("D:\\"):
        raise RuleDocumentParseError(
            "global_rules.fallback_install_path must be under D drive."
        )

    if (allow_only_local_paths or "").lower() != "true":
        raise RuleDocumentParseError(
            "global_rules.allow_only_local_paths must be true."
        )

    rule_basis = [
        "preferred_install_drive: D:",
        "forbidden_install_roots: " + ", ".join(forbidden_install_roots),
        f"fallback_install_path: {normalized_fallback_path}",
    ]

    return True, True, normalized_fallback_path, rule_basis


def _parse_categories(lines: list[str]) -> dict[SoftwareCategory, str]:
    category_blocks = _collect_blocks(
        lines,
        re.compile(r"^\s*-\s+id\s*:\s*.+$"),
    )
    if not category_blocks:
        raise RuleDocumentParseError("categories must define at least one category.")

    category_paths: dict[SoftwareCategory, str] = {}

    for block in category_blocks:
        category_raw = _extract_scalar(block, "id")
        if category_raw is None:
            raise RuleDocumentParseError("categories[].id is required.")

        try:
            category = SoftwareCategory(category_raw)
        except ValueError as error:
            raise RuleDocumentParseError(
                f"categories[].id is not a supported category: {category_raw}"
            ) from error

        if category is SoftwareCategory.UNKNOWN:
            raise RuleDocumentParseError("categories[].id must not be unknown.")

        default_install_path_raw = _extract_scalar(block, "default_install_path")
        if default_install_path_raw is None:
            raise RuleDocumentParseError(
                f"categories[{category.value}].default_install_path is required."
            )

        default_install_path = _normalize_windows_path(default_install_path_raw)
        if not _is_windows_absolute_path(default_install_path):
            raise RuleDocumentParseError(
                f"categories[{category.value}].default_install_path must be a Windows absolute path."
            )
        if not default_install_path.upper().startswith("D:\\"):
            raise RuleDocumentParseError(
                f"categories[{category.value}].default_install_path must be under D drive."
            )

        includes = _extract_block_list(block, "includes")
        excludes = _extract_block_list(block, "excludes")
        if not includes:
            raise RuleDocumentParseError(
                f"categories[{category.value}].includes must contain at least one item."
            )
        if not excludes:
            raise RuleDocumentParseError(
                f"categories[{category.value}].excludes must contain at least one item."
            )

        allowed_install_paths = [
            _normalize_windows_path(item)
            for item in _extract_block_list(block, "allowed_install_paths")
        ]
        if not allowed_install_paths:
            raise RuleDocumentParseError(
                f"categories[{category.value}].allowed_install_paths must contain at least one path."
            )
        if default_install_path not in allowed_install_paths:
            raise RuleDocumentParseError(
                f"categories[{category.value}].default_install_path must exist in allowed_install_paths."
            )

        category_paths[category] = default_install_path

    return category_paths


def _validate_software_overrides(lines: list[str]) -> None:
    override_blocks = _collect_blocks(
        lines,
        re.compile(r"^\s*-\s+software_id\s*:\s*.+$"),
    )

    for block in override_blocks:
        for field in _REQUIRED_OVERRIDE_FIELDS:
            has_field = _extract_scalar(block, field) is not None
            has_list_field = bool(_extract_block_list(block, field))
            if not has_field and not has_list_field:
                raise RuleDocumentParseError(
                    f"software_overrides[].{field} is required."
                )


def _validate_conflict_resolution(lines: list[str]) -> None:
    order = _extract_block_list(lines, "order")
    if order != _REQUIRED_CONFLICT_ORDER:
        raise RuleDocumentParseError(
            "conflict_resolution.order must exactly match the required precedence order."
        )


def _validate_validation_examples(lines: list[str]) -> None:
    example_blocks = _collect_blocks(
        lines,
        re.compile(r"^\s*-\s+software_name\s*:\s*.+$"),
    )
    if len(example_blocks) < 10:
        raise RuleDocumentParseError(
            "validation_examples must contain at least 10 examples."
        )

    for block in example_blocks:
        for field in (
            "software_name",
            "expected_category",
            "expected_install_path",
            "expected_rule_source",
        ):
            if _extract_scalar(block, field) is None:
                raise RuleDocumentParseError(
                    f"validation_examples[].{field} is required."
                )


def parse_install_rules(document_text: str) -> ParsedInstallRules:
    """Extract install-related hard rules from machine rules document text."""

    yaml_like_text = _extract_machine_rules_yaml_block(document_text)
    sections = _split_top_level_sections(yaml_like_text)

    missing = sorted(_REQUIRED_TOP_LEVEL_KEYS - set(sections.keys()))
    if missing:
        raise RuleDocumentParseError(
            "Missing required top-level section(s): " + ", ".join(missing)
        )

    _parse_metadata(sections["metadata"])
    d_drive_preferred, discourage_s_drive_install, fallback_install_path, rule_basis = (
        _parse_global_rules(sections["global_rules"])
    )
    category_install_paths = _parse_categories(sections["categories"])
    _validate_software_overrides(sections["software_overrides"])
    _validate_conflict_resolution(sections["conflict_resolution"])
    _validate_validation_examples(sections["validation_examples"])

    for category, path in sorted(category_install_paths.items(), key=lambda item: item[0].value):
        rule_basis.append(f"{category.value} -> {path}")

    return ParsedInstallRules(
        d_drive_preferred=d_drive_preferred,
        discourage_s_drive_install=discourage_s_drive_install,
        fallback_install_path=fallback_install_path,
        category_install_paths=category_install_paths,
        warnings=[],
        rule_basis=rule_basis,
    )
