"""Output helpers for CLI presentation."""

from __future__ import annotations

import json
from typing import Any

import typer

from smart_filer.application.services import SuggestionExplanation
from smart_filer.domain.models import InstallSuggestion


def build_suggestion_payload(
    *,
    suggestion: InstallSuggestion,
    explanation: SuggestionExplanation,
) -> dict[str, Any]:
    """Build a stable JSON payload for CLI output."""

    return {
        "suggestion": suggestion.model_dump(mode="json"),
        "explanation": explanation.model_dump(mode="json"),
    }


def emit_json(payload: dict[str, Any]) -> None:
    """Print structured JSON payload."""

    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def emit_error(message: str) -> None:
    """Print user-facing error text to stderr."""

    typer.secho(f"Error: {message}", fg=typer.colors.RED, err=True)
