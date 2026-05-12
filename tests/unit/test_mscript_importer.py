from __future__ import annotations

from pathlib import Path

import pytest

from osw.scripts.mscript.importer import MScriptImportError, import_mscript_preview
from osw.scripts.mscript.script_model import MScriptKind


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


def test_unsupported_extension_is_friendly(tmp_path: Path) -> None:
    script_path = tmp_path / "notes.txt"
    script_path.write_text("x = 1;", encoding="utf-8")

    with pytest.raises(MScriptImportError, match="Only .m script preview is supported"):
        import_mscript_preview(script_path)


def test_missing_script_is_friendly(tmp_path: Path) -> None:
    with pytest.raises(MScriptImportError, match="M-script file does not exist"):
        import_mscript_preview(tmp_path / "missing.m")
