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
    )

    first = builder.build_messages(request)[1]["content"]
    second = builder.build_messages(request)[1]["content"]

    assert first == second
    assert first.index("Rule A") < first.index("Rule B") < first.index("Rule C")
