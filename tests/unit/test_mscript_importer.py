from __future__ import annotations

from pathlib import Path

import pytest

from osw.scripts.mscript.importer import (
    MScriptImportError,
    MScriptResultStatus,
    create_script_ref,
    import_mscript_preview,
    preview_mscript,
)
from osw.scripts.mscript.script_model import MScriptKind, ScriptKind

FIXTURES = Path(__file__).parents[1] / "fixtures" / "mscript"


def test_import_script_preview_never_executes_code(tmp_path: Path) -> None:
    marker = tmp_path / "should_not_exist.txt"
    script_path = tmp_path / "unsafe_preview.m"
    script_path.write_text(
        "\n".join(
            [
                "x = 1:3;",
                "y = x.^2;",
                f"system('echo unsafe > {marker.as_posix()}');",
                "plot(x, y);",
            ]
        ),
        encoding="utf-8",
    )

    preview = import_mscript_preview(script_path)

    assert preview.kind is MScriptKind.SCRIPT
    assert preview.name == "unsafe_preview"
    assert preview.line_count == 4
    assert preview.executable_line_count == 4
    assert preview.contains_plot_call is True
    assert preview.safety.findings[0].function == "system"
    assert not marker.exists()


def test_function_classification_and_name_parsing(tmp_path: Path) -> None:
    function_path = tmp_path / "myfun.m"
    function_path.write_text(
        "\n".join(
            [
                "function y = myfun(x)",
                "y = x + 1;",
                "end",
            ]
        ),
        encoding="utf-8",
    )

    preview = import_mscript_preview(function_path)

    assert preview.kind is MScriptKind.FUNCTION
    assert preview.name == "myfun"
    assert preview.entrypoint == "myfun"


def test_fixture_script_preview_detects_plots_and_help() -> None:
    result = preview_mscript(FIXTURES / "simple_plot.m")

    assert result.status is MScriptResultStatus.OK
    assert result.preview is not None
    assert result.preview.kind is ScriptKind.SCRIPT
    assert result.preview.name == "simple_plot"
    assert "Simple plot preview fixture" in result.preview.help_text
    assert {hint.command for hint in result.preview.plot_hints} >= {"plot", "title", "xlabel"}
    assert result.preview.safety_findings == ()


def test_fixture_function_signatures_are_extracted() -> None:
    basic = preview_mscript(FIXTURES / "function_basic.m").preview
    multi = preview_mscript(FIXTURES / "function_multi_output.m").preview

    assert basic is not None
    assert basic.kind is ScriptKind.FUNCTION
    assert basic.function_signature is not None
    assert basic.function_signature.name == "function_basic"
    assert basic.function_signature.inputs == ("x",)
    assert basic.function_signature.outputs == ("y",)

    assert multi is not None
    assert multi.function_signature is not None
    assert multi.function_signature.inputs == ("x", "y")
    assert multi.function_signature.outputs == ("a", "b")


def test_classdef_comments_and_empty_fixtures_are_friendly() -> None:
    classdef = preview_mscript(FIXTURES / "classdef_example.m")
    comments = preview_mscript(FIXTURES / "comments_only.m")
    empty = preview_mscript(FIXTURES / "empty_script.m")

    assert classdef.preview is not None
    assert classdef.preview.kind is ScriptKind.CLASSDEF
    assert "classdef" in classdef.diagnostics.summary().lower()
    assert comments.preview is not None
    assert "Comments only fixture" in comments.preview.help_text
    assert empty.preview is not None
    assert empty.status is MScriptResultStatus.WARNING
    assert "empty" in empty.diagnostics.summary().lower()


def test_plain_script_classification_uses_stem_name(tmp_path: Path) -> None:
    script_path = tmp_path / "plot_demo.m"
    script_path.write_text(
        """
        % preview-only plotting script
        x = linspace(0, 1, 10);
        plot(x, x);
        """,
        encoding="utf-8",
    )

    preview = import_mscript_preview(script_path)

    assert preview.kind is MScriptKind.SCRIPT
    assert preview.name == "plot_demo"
    assert preview.entrypoint is None
    assert preview.comment_line_count == 1


def test_create_script_ref_is_preview_first() -> None:
    preview = import_mscript_preview(FIXTURES / "dangerous_system.m")

    script_ref = create_script_ref(preview)

    assert script_ref.language == "matlab_octave"
    assert script_ref.safe_preview_required is True
    assert script_ref.status == "previewed"
    assert script_ref.metadata["can_execute"] is False
    assert script_ref.metadata["kind"] == "script"
    assert "high=" in script_ref.metadata["safety_summary"]
    assert not Path(script_ref.path).with_suffix(".marker").exists()


def test_result_api_reports_missing_and_unsupported_paths(tmp_path: Path) -> None:
    txt_path = tmp_path / "notes.txt"
    txt_path.write_text("x = 1;", encoding="utf-8")

    unsupported = preview_mscript(txt_path)
    missing = preview_mscript(tmp_path / "missing.m")

    assert unsupported.status is MScriptResultStatus.ERROR
    assert "Only .m" in unsupported.diagnostics.summary()
    assert missing.status is MScriptResultStatus.ERROR
    assert "does not exist" in missing.diagnostics.summary()


def test_unsupported_extension_is_friendly(tmp_path: Path) -> None:
    script_path = tmp_path / "notes.txt"
    script_path.write_text("x = 1;", encoding="utf-8")

    with pytest.raises(MScriptImportError, match="Only .m script preview is supported"):
        import_mscript_preview(script_path)


def test_missing_script_is_friendly(tmp_path: Path) -> None:
    with pytest.raises(MScriptImportError, match="M-script file does not exist"):
        import_mscript_preview(tmp_path / "missing.m")
