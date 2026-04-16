from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
INSTALL_DOC_PATH = REPO_ROOT / "docs" / "dependency-installation.md"


def _normalize_dependency_name(spec: str) -> str:
    return re.split(r"[<>=!~\[\]\s]", spec.strip().lower(), maxsplit=1)[0]


def _extract_section(content: str, section_name: str) -> str:
    pattern = re.compile(
        rf"(?ms)^\[{re.escape(section_name)}\]\s*(.*?)(?=^\[|\Z)",
    )
    matched = pattern.search(content)
    assert matched is not None, f"Missing section [{section_name}] in pyproject.toml"
    return matched.group(1)


def _extract_list_items(section_content: str, key_name: str) -> list[str]:
    key_pattern = re.compile(
        rf'(?ms)^{re.escape(key_name)}\s*=\s*\[(.*?)\]',
    )
    matched = key_pattern.search(section_content)
    assert matched is not None, f"Missing list key `{key_name}` in section"
    return re.findall(r'"([^"]+)"', matched.group(1))


def _project_dependencies() -> tuple[set[str], set[str]]:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    project_section = _extract_section(content, "project")
    dependency_group_section = _extract_section(content, "dependency-groups")

    runtime_specs = _extract_list_items(project_section, "dependencies")
    dev_specs = _extract_list_items(dependency_group_section, "dev")

    runtime = {_normalize_dependency_name(spec) for spec in runtime_specs}
    dev = {_normalize_dependency_name(spec) for spec in dev_specs}
    return runtime, dev


def test_python_version_and_required_runtime_dependencies() -> None:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    project_section = _extract_section(content, "project")
    assert 'requires-python = ">=3.12,<3.13"' in project_section

    runtime, _ = _project_dependencies()
    required = {"typer", "pydantic", "pydantic-settings", "openai"}
    assert required.issubset(runtime)


def test_dev_dependencies_are_separated() -> None:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    assert "[dependency-groups]" in content

    _, dev = _project_dependencies()
    assert "pytest" in dev


def test_forbidden_stack_items_not_declared_as_dependencies() -> None:
    runtime, dev = _project_dependencies()
    declared = runtime | dev

    forbidden = {"fastapi", "langchain", "psycopg", "psycopg2", "electron"}
    assert forbidden.isdisjoint(declared)


def test_installation_document_defines_source_venv_and_cache_locations() -> None:
    content = INSTALL_DOC_PATH.read_text(encoding="utf-8")

    assert "S:\\001_Workspace\\smart-filer" in content
    assert "D:\\10_Environments\\Python" in content
    assert "D:\\00_Temp_Cache" in content

    assert "UV_PROJECT_ENVIRONMENT" in content
    assert "UV_CACHE_DIR" in content
    assert "`S:`" in content


def test_installation_document_matches_core_drive_layout_rules() -> None:
    content = INSTALL_DOC_PATH.read_text(encoding="utf-8")

    assert "D:\\10_Environments" in content
    assert "D:\\00_Temp_Cache" in content
    assert "FastAPI" in content
    assert "LangChain" in content
