from importlib import import_module
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_required_layer_directories_exist() -> None:
    expected_dirs = [
        REPO_ROOT / "smart_filer",
        REPO_ROOT / "smart_filer" / "cli",
        REPO_ROOT / "smart_filer" / "application",
        REPO_ROOT / "smart_filer" / "domain",
        REPO_ROOT / "smart_filer" / "infrastructure",
        REPO_ROOT / "tests",
    ]

    for expected_dir in expected_dirs:
        assert expected_dir.is_dir(), f"Missing directory: {expected_dir}"


def test_required_packages_have_init_files() -> None:
    expected_init_files = [
        REPO_ROOT / "smart_filer" / "__init__.py",
        REPO_ROOT / "smart_filer" / "cli" / "__init__.py",
        REPO_ROOT / "smart_filer" / "application" / "__init__.py",
        REPO_ROOT / "smart_filer" / "domain" / "__init__.py",
        REPO_ROOT / "smart_filer" / "infrastructure" / "__init__.py",
        REPO_ROOT / "tests" / "__init__.py",
    ]

    for init_file in expected_init_files:
        assert init_file.is_file(), f"Missing package init file: {init_file}"


def test_layer_packages_are_importable() -> None:
    package_names = [
        "smart_filer",
        "smart_filer.cli",
        "smart_filer.application",
        "smart_filer.domain",
        "smart_filer.infrastructure",
    ]

    for package_name in package_names:
        module = import_module(package_name)
        assert module is not None

