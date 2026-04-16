"""Application use case for software install-path suggestion."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from smart_filer.application.services.llm_response_service import (
    DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    build_install_suggestion_from_llm,
)
from smart_filer.config import AppSettings
from smart_filer.domain.models import (
    InstallSuggestion,
    LLMInstallPathRequest,
    ParsedInstallRules,
)
from smart_filer.infrastructure.providers.siliconflow_adapter import (
    SiliconFlowAdapter,
    SiliconFlowAdapterResult,
)
from smart_filer.infrastructure.rules.document_loader import load_rules_document
from smart_filer.infrastructure.rules.document_parser import parse_install_rules


class SupportsSoftwareClassification(Protocol):
    """Minimal adapter contract required by this use case."""

    def classify_software(
        self, request: LLMInstallPathRequest
    ) -> SiliconFlowAdapterResult:
        """Classify software and return structured provider result."""


RulesDocumentLoader = Callable[[Path], str]
RulesDocumentParser = Callable[[str], ParsedInstallRules]


class SuggestInstallPathUseCase:
    """Orchestrates rule loading, LLM classification, and fallback guards."""

    def __init__(
        self,
        *,
        settings: AppSettings,
        llm_classifier: SupportsSoftwareClassification | None = None,
        rules_loader: RulesDocumentLoader = load_rules_document,
        rules_parser: RulesDocumentParser = parse_install_rules,
        low_confidence_threshold: float = DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    ) -> None:
        if not 0.0 <= low_confidence_threshold <= 1.0:
            raise ValueError("low_confidence_threshold must be between 0.0 and 1.0.")

        self._settings = settings
        self._llm_classifier = llm_classifier
        self._rules_loader = rules_loader
        self._rules_parser = rules_parser
        self._low_confidence_threshold = low_confidence_threshold

    def execute(
        self,
        *,
        software_name: str,
        aliases: list[str] | None = None,
        context: str | None = None,
    ) -> InstallSuggestion:
        """Generate a structured install-path suggestion for one software name."""

        normalized_name = software_name.strip()
        if not normalized_name:
            raise ValueError("software_name cannot be empty.")

        parsed_rules = self._load_parsed_rules()
        llm_request = LLMInstallPathRequest(
            software_name=normalized_name,
            rule_summary=_build_rule_summary(parsed_rules),
            aliases=aliases or [],
            context=context,
        )

        if not self._settings.llm_enabled:
            return build_install_suggestion_from_llm(
                software_name=normalized_name,
                parsed_rules=parsed_rules,
                llm_error=RuntimeError("LLM is disabled in current settings."),
                low_confidence_threshold=self._low_confidence_threshold,
            )

        llm_classifier, classifier_error = self._resolve_llm_classifier()
        if classifier_error is not None:
            return build_install_suggestion_from_llm(
                software_name=normalized_name,
                parsed_rules=parsed_rules,
                llm_error=classifier_error,
                low_confidence_threshold=self._low_confidence_threshold,
            )

        assert llm_classifier is not None
        try:
            llm_result = llm_classifier.classify_software(llm_request)
        except Exception as error:
            return build_install_suggestion_from_llm(
                software_name=normalized_name,
                parsed_rules=parsed_rules,
                llm_error=error,
                low_confidence_threshold=self._low_confidence_threshold,
            )

        return build_install_suggestion_from_llm(
            software_name=normalized_name,
            parsed_rules=parsed_rules,
            llm_result=llm_result,
            low_confidence_threshold=self._low_confidence_threshold,
        )

    def _load_parsed_rules(self) -> ParsedInstallRules:
        raw_rules_text = self._rules_loader(self._settings.rules_document_path)
        return self._rules_parser(raw_rules_text)

    def _resolve_llm_classifier(
        self,
    ) -> tuple[SupportsSoftwareClassification | None, Exception | None]:
        if self._llm_classifier is not None:
            return self._llm_classifier, None

        try:
            return SiliconFlowAdapter.from_settings(self._settings), None
        except Exception as error:
            return None, error


def _build_rule_summary(parsed_rules: ParsedInstallRules) -> list[str]:
    summary_lines: list[str] = []

    summary_lines.extend(parsed_rules.rule_basis)
    if parsed_rules.d_drive_preferred:
        summary_lines.append("Software and runtime should stay in D drive hierarchy.")
    if parsed_rules.discourage_s_drive_install:
        summary_lines.append("Software install path should not be on S drive.")

    for category, path in sorted(
        parsed_rules.category_install_paths.items(),
        key=lambda item: item[0].value,
    ):
        summary_lines.append(f"{category.value} -> {path}")

    for warning in parsed_rules.warnings:
        summary_lines.append(f"Parser warning: {warning}")

    cleaned_summary = [line.strip() for line in summary_lines if line.strip()]
    if not cleaned_summary:
        cleaned_summary.append("Keep software install suggestions inside D drive.")

    return _deduplicate_preserve_order(cleaned_summary)


def _deduplicate_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items

