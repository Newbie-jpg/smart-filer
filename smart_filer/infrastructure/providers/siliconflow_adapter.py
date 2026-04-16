"""SiliconFlow provider adapter based on OpenAI-compatible SDK."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from openai import APITimeoutError, OpenAI
from pydantic import ValidationError

from smart_filer.config import AppSettings
from smart_filer.domain.models.llm_models import (
    LLMInstallPathRequest,
    LLMInstallPathResponse,
)
from smart_filer.infrastructure.providers.prompt_builder import InstallPathPromptBuilder


class SiliconFlowAdapterError(RuntimeError):
    """Base error for provider adapter failures."""


class SiliconFlowTimeoutError(SiliconFlowAdapterError):
    """Raised when SiliconFlow request timed out."""


class SiliconFlowResponseError(SiliconFlowAdapterError):
    """Raised when SiliconFlow response is empty or invalid."""


@dataclass(frozen=True)
class SiliconFlowAdapterResult:
    """Structured adapter output with raw response record."""

    response: LLMInstallPathResponse
    raw_response_text: str
    model_id: str


class SiliconFlowAdapter:
    """OpenAI-compatible SiliconFlow adapter."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model_id: str,
        timeout_seconds: float,
        client: Any | None = None,
        prompt_builder: InstallPathPromptBuilder | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("api_key cannot be empty.")
        if not base_url.strip():
            raise ValueError("base_url cannot be empty.")
        if not model_id.strip():
            raise ValueError("model_id cannot be empty.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0.")

        self._model_id = model_id
        self._timeout_seconds = timeout_seconds
        self._prompt_builder = prompt_builder or InstallPathPromptBuilder()
        self._client = client or OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )

    @classmethod
    def from_settings(
        cls,
        settings: AppSettings,
        *,
        client: Any | None = None,
        prompt_builder: InstallPathPromptBuilder | None = None,
    ) -> "SiliconFlowAdapter":
        if not settings.siliconflow_api_key:
            raise ValueError("SMART_FILER_SILICONFLOW_API_KEY is required.")
        if not settings.siliconflow_model_id:
            raise ValueError("SMART_FILER_SILICONFLOW_MODEL_ID is required.")

        return cls(
            api_key=settings.siliconflow_api_key,
            base_url=settings.siliconflow_base_url,
            model_id=settings.siliconflow_model_id,
            timeout_seconds=settings.request_timeout_seconds,
            client=client,
            prompt_builder=prompt_builder,
        )

    def classify_software(
        self, request: LLMInstallPathRequest
    ) -> SiliconFlowAdapterResult:
        messages = self._prompt_builder.build_messages(request)

        try:
            completion = self._client.chat.completions.create(
                model=self._model_id,
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"},
                timeout=self._timeout_seconds,
            )
        except (APITimeoutError, TimeoutError) as error:
            raise SiliconFlowTimeoutError(
                "SiliconFlow request timed out while classifying software."
            ) from error
        except Exception as error:
            raise SiliconFlowAdapterError(
                "SiliconFlow request failed before receiving a valid response."
            ) from error

        raw_content = _extract_response_text(completion)
        parsed_response = _parse_structured_response(raw_content)

        return SiliconFlowAdapterResult(
            response=parsed_response,
            raw_response_text=raw_content,
            model_id=self._model_id,
        )


def _extract_response_text(completion: Any) -> str:
    choices = getattr(completion, "choices", None)
    if not choices:
        raise SiliconFlowResponseError("SiliconFlow returned empty choices.")

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    content = getattr(message, "content", None) if message else None
    if not isinstance(content, str) or not content.strip():
        raise SiliconFlowResponseError("SiliconFlow returned empty message content.")

    return content.strip()


def _parse_structured_response(raw_content: str) -> LLMInstallPathResponse:
    try:
        payload = json.loads(raw_content)
    except json.JSONDecodeError as error:
        raise SiliconFlowResponseError(
            "SiliconFlow returned non-JSON structured content."
        ) from error

    try:
        return LLMInstallPathResponse.model_validate(payload)
    except ValidationError as error:
        raise SiliconFlowResponseError(
            "SiliconFlow returned JSON but failed schema validation."
        ) from error
