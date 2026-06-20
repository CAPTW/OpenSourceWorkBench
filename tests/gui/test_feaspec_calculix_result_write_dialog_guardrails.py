from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "osw"
    / "gui"
    / "dialogs"
    / "feaspec_calculix_result_write_dialog.py"
)
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_write_gui_writer_integration.md"
)
POST_WRITE_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_write_gui_post_write_polish.md"
)


def _source_text() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _imported_modules() -> set[str]:
    tree = ast.parse(_source_text())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _doc_text() -> str:
    return " ".join(DOC_PATH.read_text(encoding="utf-8").lower().split())


def _post_write_doc_text() -> str:
    return " ".join(POST_WRITE_DOC_PATH.read_text(encoding="utf-8").lower().split())


def test_dialog_imports_only_gui_and_viewmodel_safe_layers() -> None:
    imports = _imported_modules()

    assert "PySide6" in imports
    assert "osw.experimental.feaspec.calculix_result_dataset_writer" in imports
    assert "osw.experimental.feaspec.calculix_result_write_viewmodel" in imports
    assert "osw.gui.qt_compat" in imports
    assert "osw.gui.theme_tokens" in imports
    assert not any(module.startswith("osw.solvers") for module in imports)
    assert not any(module.startswith("osw.runners") for module in imports)
    assert not any("calculix_result_import_write" in module for module in imports)


def test_dialog_uses_only_directory_chooser_and_no_execution_paths() -> None:
    source = _source_text()
    imports = _imported_modules()
    forbidden_tokens = (
        "clipboard",
        "pyperclip",
        "getSaveFileName",
        "getOpenFileName",
        "QDesktopServices",
        "startfile",
        "prepare_calculix_result_dataset_write_payloads",
        "SolverAdapter",
        "CalculiXRunner",
        "run_calculix",
        "ccx.exe",
        "ProjectSchema",
        "VLMProvider",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "api_key",
        "credential",
    )

    for token in forbidden_tokens:
        assert token not in source
    assert "QFileDialog" in source
    assert "getExistingDirectory" in source
    assert "ShowDirsOnly" in source
    assert "sub" + "process" not in source
    assert not any("runner" in module for module in imports)
    assert not any("solvers" in module and "adapter" in module for module in imports)


def test_dialog_does_not_write_files_or_mutate_runtime_state() -> None:
    source = _source_text()

    assert ".write_text(" not in source
    assert ".write_bytes(" not in source
    assert "open(" not in source
    assert ".mkdir(" not in source
    assert ".replace(" not in source
    assert ".unlink(" not in source


def test_docs_describe_guarded_gui_writer_boundary() -> None:
    text = _doc_text()

    assert "gui writer integration implemented" in text
    assert "accepts `feaspeccalculixresultwriteviewmodel`" in text
    assert "qfiledialog directory selection" in text
    assert "explicit confirmation" in text
    assert "existing library writer" in text
    assert "actual resultdataset file write" in text
    assert "selected output directory" in text
    assert "no cli behavior change" in text
    assert "no solver execution" in text
    assert "no subprocess" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no projectschema mutation" in text
    assert "no vlm api" in text
    assert "no provider credentials" in text


def test_docs_keep_release_and_validation_claims_bounded() -> None:
    text = _doc_text()

    assert "issue `#8` remains open" in text
    assert "external solvers are optional and not bundled" in text
    assert "no industrial certification" in text
    assert "stable production" not in text
    assert "live calculix validation passed" not in text
    assert "issue `#8` can close" not in text


def test_post_write_polish_docs_keep_gui_boundary_bounded() -> None:
    text = _post_write_doc_text()

    assert "post-write polish only" in text
    assert "no solver execution" in text
    assert "no artifact copying" in text
    assert "no open-output shell command" in text
    assert "no os clipboard integration" in text
    assert "issue `#8` remains open" in text
    assert "external solvers are optional and not bundled" in text
    assert "no industrial certification" in text
    assert "live calculix validation passed" not in text
    assert "issue `#8` can close" not in text


def test_dialog_tests_use_tmp_path_not_tracked_result_fixtures() -> None:
    test_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            REPO_ROOT
            / "tests"
            / "gui"
            / "test_feaspec_calculix_result_write_dialog.py",
            REPO_ROOT
            / "tests"
            / "gui"
            / "test_feaspec_calculix_result_write_dialog_actions.py",
            REPO_ROOT
            / "tests"
            / "gui"
            / "test_feaspec_calculix_result_write_dialog_writer_integration.py",
            REPO_ROOT
            / "tests"
            / "gui"
            / "test_feaspec_calculix_result_write_dialog_post_write.py",
        )
    )

    assert "tmp_path" in test_text
    assert "tests/" + "fixtures" not in test_text
    assert "fixtures/" + "calculix" not in test_text
