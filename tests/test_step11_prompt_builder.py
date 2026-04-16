from smart_filer.domain.models import LLMInstallPathRequest
from smart_filer.infrastructure.providers.prompt_builder import InstallPathPromptBuilder


def test_prompt_builder_includes_all_required_input_sections() -> None:
    builder = InstallPathPromptBuilder()
    request = LLMInstallPathRequest(
        software_name="OBS Studio",
        rule_summary=[
            "Software and runtime should stay on D drive.",
            "Media-design software should use D:\\50_Media_Design.",
        ],
        category_profiles={},
        aliases=["OBS"],
        context="User plans to record and stream videos.",
    )

    messages = builder.build_messages(request)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "category" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "OBS Studio" in messages[1]["content"]
    assert "OBS" in messages[1]["content"]
    assert "Rule Summary" in messages[1]["content"]
    assert "Category Reference" in messages[1]["content"]
    for line in request.rule_summary:
        assert line in messages[1]["content"]


def test_prompt_builder_keeps_rule_summary_order_stable() -> None:
    builder = InstallPathPromptBuilder()
    request = LLMInstallPathRequest(
        software_name="7-Zip",
        rule_summary=[
            "Rule A: prefer D drive.",
            "Rule B: avoid S drive.",
            "Rule C: system utilities map to D:\\60_System_Utilities.",
        ],
        category_profiles={},
    )

    first = builder.build_messages(request)[1]["content"]
    second = builder.build_messages(request)[1]["content"]

    assert first == second
    assert first.index("Rule A") < first.index("Rule B") < first.index("Rule C")

def test_prompt_builder_includes_category_profiles_in_user_prompt() -> None:
    builder = InstallPathPromptBuilder()
    request = LLMInstallPathRequest(
        software_name="Generic Voice Platform",
        rule_summary=["productivity -> D:\\40_Productivity"],
        category_profiles={
            "productivity": {
                "definition": "Communication and collaboration software.",
                "includes": ["Team Chat", "Voice Collaboration"],
                "excludes": ["System Maintenance"],
            },
            "system_utilities": {
                "definition": "Diagnostics and OS enhancement tools.",
                "includes": ["System Monitor"],
                "excludes": ["Team Communication"],
            },
        },
    )

    user_prompt = builder.build_messages(request)[1]["content"]

    assert "- productivity" in user_prompt
    assert "definition: Communication and collaboration software." in user_prompt
    assert "includes: Team Chat, Voice Collaboration" in user_prompt
    assert "excludes: System Maintenance" in user_prompt
