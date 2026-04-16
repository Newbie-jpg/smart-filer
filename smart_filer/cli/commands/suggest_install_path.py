"""CLI command for software install-path suggestion."""

from __future__ import annotations

import typer

from smart_filer.application.services import build_suggestion_explanation
from smart_filer.application.use_cases import SuggestInstallPathUseCase
from smart_filer.cli.output import build_suggestion_payload, emit_error, emit_json
from smart_filer.config import AppSettings, get_settings
from smart_filer.infrastructure.logging_setup import initialize_logging


def _build_use_case(settings: AppSettings) -> SuggestInstallPathUseCase:
    """Factory function for the install-path suggestion use case."""

    return SuggestInstallPathUseCase(settings=settings)


def suggest_install_path_command(
    software_name: str = typer.Argument(
        ...,
        help="Software name, for example: OBS Studio",
    ),
) -> None:
    """Suggest an install path for a software name."""

    normalized_name = software_name.strip()
    if not normalized_name:
        emit_error("software_name cannot be empty.")
        raise typer.Exit(code=2)

    try:
        settings = get_settings()
        initialize_logging(settings=settings)
        use_case = _build_use_case(settings)
        suggestion = use_case.execute(software_name=normalized_name)
        explanation = build_suggestion_explanation(suggestion)
        payload = build_suggestion_payload(
            suggestion=suggestion,
            explanation=explanation,
        )
        emit_json(payload)
    except typer.Exit:
        raise
    except Exception as error:
        emit_error(str(error))
        raise typer.Exit(code=1) from error
