"""Prompt builder for software install-path LLM requests."""

from smart_filer.domain.models.llm_models import LLMInstallPathRequest


class InstallPathPromptBuilder:
    """Build stable prompt messages for install-path classification."""

    def build_messages(self, request: LLMInstallPathRequest) -> list[dict[str, str]]:
        aliases_text = ", ".join(request.aliases) if request.aliases else "N/A"
        context_text = request.context.strip() if request.context else "N/A"
        rules_text = "\n".join(f"- {item}" for item in request.rule_summary)
        category_reference_text = self._build_category_reference_text(request)

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
            "Category Reference:\n"
            f"{category_reference_text}\n\n"
            "Return one JSON object with exactly these keys:\n"
            '{"category":"<allowed_category>","suggested_path":"<windows_path>",'
            '"reason":"<short_reason>","confidence":0.0}\n\n'
            "Please infer the software category and suggest an install path."
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_category_reference_text(self, request: LLMInstallPathRequest) -> str:
        if not request.category_profiles:
            return "N/A"

        lines: list[str] = []
        for category in sorted(request.category_profiles.keys(), key=lambda item: item.value):
            profile = request.category_profiles[category]
            includes = ", ".join(profile.includes) if profile.includes else "N/A"
            excludes = ", ".join(profile.excludes) if profile.excludes else "N/A"
            lines.append(f"- {category.value}")
            lines.append(f"  definition: {profile.definition}")
            lines.append(f"  includes: {includes}")
            lines.append(f"  excludes: {excludes}")
        return "\n".join(lines)
