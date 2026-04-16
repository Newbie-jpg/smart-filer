"""Process entrypoint for smart-filer CLI."""

from smart_filer.cli import run_cli


def main() -> None:
    """Run CLI and exit with proper status code."""

    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
