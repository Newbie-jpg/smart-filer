"""Rule document text loader."""

from pathlib import Path


class RulesDocumentError(ValueError):
    """Raised when a rules document cannot be read as valid text."""


def load_rules_document(document_path: Path) -> str:
    """Load rule document text from disk with strict validation."""

    if not document_path.exists():
        raise RulesDocumentError(
            "Rules document does not exist: {path}".format(path=document_path)
        )
    if not document_path.is_file():
        raise RulesDocumentError(
            "Rules document path is not a file: {path}".format(path=document_path)
        )

    try:
        content = document_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise RulesDocumentError(
            "Rules document encoding is invalid UTF-8: {path}".format(
                path=document_path
            )
        ) from error

    if not content.strip():
        raise RulesDocumentError(
            "Rules document is empty: {path}".format(path=document_path)
        )

    return content
