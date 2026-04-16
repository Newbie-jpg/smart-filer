"""Prompt builder for software install-path LLM requests."""

from smart_filer.domain.models.llm_models import LLMInstallPathRequest


class InstallPathPromptBuilder:
    """Build stable prompt messages for install-path classification."""

    def build_messages(self, request: LLMInstallPathRequest) -> list[dict[str, str]]:
        aliases_text = ", ".join(request.aliases) if request.aliases else "N/A"
        context_text = request.context.strip() if request.context else "N/A"
        rules_text = "\n".join(f"- {item}" for item in request.rule_summary)

        system_prompt = (
            "You are a software installation routing assistant for Windows.\n"
            "Always return a strict JSON object only.\n"
            "Required fields: category, suggested_path, reason, confidence.\n"
            "Allowed category values only: "
            "development_environment, engineering, productivity, "
            "media_design, system_utilities, games_entertain, unknown.\n"
            "confidence must be a number between 0 and 1.\n"
            "Do not add markdown, comments, or any extra keys."
        )
        user_prompt = (
            "Software Name:\n"
            f"{request.software_name}\n\n"
            "Aliases:\n"
            f"{aliases_text}\n\n"
            "Context:\n"
            f"{context_text}\n\n"
            "Rule Summary:\n"
            f"{rules_text}\n\n"
            "Please infer the software category and suggest an install path."
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
