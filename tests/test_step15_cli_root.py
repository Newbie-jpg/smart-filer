import importlib

import typer
from typer.testing import CliRunner

import pytest

cli_app_module = importlib.import_module("smart_filer.cli.app")


def test_root_command_can_start_and_show_help_by_default() -> None:
    runner = CliRunner()

    result = runner.invoke(cli_app_module.app, [])

    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "suggest-install-path" in result.stdout


def test_root_command_help_flag_shows_registered_commands() -> None:
    runner = CliRunner()

    result = runner.invoke(cli_app_module.app, ["--help"])

    assert result.exit_code == 0
    assert "suggest-install-path" in result.stdout


def test_run_cli_handles_unexpected_exception_with_friendly_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_messages: list[str] = []

    def _broken_app(*_args, **_kwargs) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_app_module, "app", _broken_app)
    monkeypatch.setattr(cli_app_module, "emit_error", captured_messages.append)

    exit_code = cli_app_module.run_cli()

    assert exit_code == 1
    assert captured_messages == ["Unexpected error: boom"]


def test_run_cli_returns_typer_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    def _exit_app(*_args, **_kwargs) -> None:
        raise typer.Exit(code=3)

    monkeypatch.setattr(cli_app_module, "app", _exit_app)

    exit_code = cli_app_module.run_cli()

    assert exit_code == 3
