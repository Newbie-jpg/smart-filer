"""Typer root application for smart-filer CLI."""

from __future__ import annotations

import typer

from smart_filer.cli.commands import suggest_install_path_command
from smart_filer.cli.output import emit_error


app = typer.Typer(
    name="smart-filer",
    help="smart-filer CLI for software install path suggestions.",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def root_callback(ctx: typer.Context) -> None:
    """Root callback for smart-filer CLI."""

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


app.command("suggest-install-path")(suggest_install_path_command)


def run_cli() -> int:
    """Run CLI app with unified top-level exception handling."""

    try:
        app(standalone_mode=False)
    except typer.Exit as exit_signal:
        return int(exit_signal.exit_code or 0)
    except Exception as error:
        emit_error(f"Unexpected error: {error}")
        return 1
    return 0
