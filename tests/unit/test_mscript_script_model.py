from __future__ import annotations

from osw.scripts.mscript.script_model import (
    FunctionSignature,
    PlotHint,
    SafetyFinding,
    ScriptKind,
    ScriptPreview,
)


def test_safety_finding_serializes_and_preserves_compatibility_fields() -> None:
    finding = SafetyFinding(
        severity="high",
        code="mscript-high-system",
        message="External command token detected.",
        hint="Review manually.",
        line_no=3,
        token="system",
        context="system('echo preview')",
    )

    restored = SafetyFinding.from_dict(finding.to_dict())

    assert restored.severity == "high"
    assert restored.line == 3
    assert restored.line_no == 3
    assert restored.function == "system"
    assert restored.token == "system"
    assert "External command" in restored.message


def test_function_signature_and_plot_hint_round_trip() -> None:
    signature = FunctionSignature(
        name="foo",
        inputs=("x", "y"),
        outputs=("a", "b"),
        raw_signature="function [a,b] = foo(x,y)",
        line_no=1,
    )
    hint = PlotHint(command="plot", line_no=8, context="plot(x, y)")

    assert FunctionSignature.from_dict(signature.to_dict()) == signature
    assert PlotHint.from_dict(hint.to_dict()) == hint


def test_script_preview_round_trip() -> None:
    preview = ScriptPreview(
        id="script-foo",
        name="foo",
        source_path="scripts/foo.m",
        kind=ScriptKind.FUNCTION,
        line_count=4,
        character_count=64,
        help_text="Function help.",
        first_comment_block="Function help.",
        function_signature=FunctionSignature(
            name="foo",
            inputs=("x",),
            outputs=("y",),
            raw_signature="function y = foo(x)",
            line_no=1,
        ),
        plot_hints=(PlotHint("plot", 4, "plot(x, y)"),),
        safety_findings=(
            SafetyFinding(
                severity="warning",
                code="mscript-warning-save",
                message="Save token detected.",
                line_no=3,
                token="save",
            ),
        ),
        detected_calls=("foo", "plot"),
        metadata={"preview_only": True},
    )

    restored = ScriptPreview.from_dict(preview.to_dict())

    assert restored.id == "script-foo"
    assert restored.kind is ScriptKind.FUNCTION
    assert restored.function_signature is not None
    assert restored.function_signature.name == "foo"
    assert restored.plot_hints[0].command == "plot"
    assert restored.safety_findings[0].token == "save"
    assert restored.safe_preview_required is True
    assert restored.can_execute is False
