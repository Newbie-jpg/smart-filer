"""Parse rule document text into install-path rules."""

from __future__ import annotations

import re

from smart_filer.domain.models.parsed_rules import ParsedInstallRules
from smart_filer.domain.models.software_category import SoftwareCategory


def _normalize_windows_path(path: str) -> str:
    return path.strip().replace("/", "\\")


def _infer_category_from_line(line: str) -> SoftwareCategory | None:
    normalized = line.lower()

    if any(keyword in normalized for keyword in ["python", "toolchain", "sdk", "开发"]):
        return SoftwareCategory.DEVELOPMENT_ENVIRONMENT
    if any(keyword in normalized for keyword in ["engineering", "eda", "cad", "工程"]):
        return SoftwareCategory.ENGINEERING
    if any(keyword in normalized for keyword in ["productivity", "办公"]):
        return SoftwareCategory.PRODUCTIVITY
    if any(
        keyword in normalized
        for keyword in ["media_design", "photoshop", "premiere", "obs", "图像", "音频", "视频"]
    ):
        return SoftwareCategory.MEDIA_DESIGN
    if any(
        keyword in normalized
        for keyword in ["system_utilities", "7-zip", "everything", "系统", "工具"]
    ):
        return SoftwareCategory.SYSTEM_UTILITIES
    if any(keyword in normalized for keyword in ["games_entertain", "steam", "epic", "游戏"]):
        return SoftwareCategory.GAMES_ENTERTAIN
    return None


def parse_install_rules(document_text: str) -> ParsedInstallRules:
    """Extract install-related hard rules from rule document text."""

    lines = [line.rstrip() for line in document_text.splitlines()]
    warnings: list[str] = []
    rule_basis: list[str] = []

    d_drive_preferred = False
    discourage_s_drive_install = False
    category_install_paths: dict[SoftwareCategory, str] = {}

    directory_pattern = re.compile(r"^(10|30|40|50|60|70)_[A-Za-z_]+$")

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        lower_line = line.lower()
        if ("执行归" in line and "d:" in lower_line) or ("软件" in line and "d:" in lower_line):
            d_drive_preferred = True
            rule_basis.append(line)

        if (
            ("数据归" in line and "s:" in lower_line and "执行归" in line and "d:" in lower_line)
            or ("不建议" in line and "s:" in lower_line and "安装" in line)
            or ("软件不" in line and "s:" in lower_line)
        ):
            discourage_s_drive_install = True
            rule_basis.append(line)

        if "->" in line and "D:\\" in line:
            category = _infer_category_from_line(line)
            path = _normalize_windows_path(line.split("->", maxsplit=1)[1])
            if category:
                category_install_paths[category] = path
            else:
                warnings.append(
                    "Unrecognized mapping line, cannot infer software category: {line}".format(
                        line=line
                    )
                )

        # Parse directory roles, e.g. `30_Engineering`: ...
        if "`" in line:
            category = _infer_category_from_line(line)
            if category:
                marker_start = line.find("`")
                marker_end = line.find("`", marker_start + 1)
                if marker_start >= 0 and marker_end > marker_start:
                    directory_name = line[marker_start + 1 : marker_end]
                    if directory_pattern.match(directory_name):
                        category_install_paths.setdefault(
                            category,
                            _normalize_windows_path(r"D:\{dir}".format(dir=directory_name)),
                        )

    if d_drive_preferred and not discourage_s_drive_install:
        discourage_s_drive_install = True
        rule_basis.append("数据归 S 盘、执行归 D 盘 -> 软件安装不建议放在 S 盘。")

    if not d_drive_preferred:
        warnings.append("Cannot explicitly confirm D-drive preference from document text.")
    if not category_install_paths:
        warnings.append("No category install-path mappings were extracted from document.")

    return ParsedInstallRules(
        d_drive_preferred=d_drive_preferred,
        discourage_s_drive_install=discourage_s_drive_install,
        category_install_paths=category_install_paths,
        warnings=warnings,
        rule_basis=rule_basis,
    )
