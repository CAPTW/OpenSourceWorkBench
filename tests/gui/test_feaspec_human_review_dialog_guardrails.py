from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT / "src" / "osw" / "gui" / "dialogs" / "feaspec_human_review_dialog.py"
)
IMPLEMENTATION_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_human_review_gui_dialog_implementation.md"
)
DESIGN_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_human_review_gui_dialog_design.md"
)
VIEWMODEL_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_human_review_gui_dialog_viewmodel.md"
)
SAVE_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_human_review_gui_save_integration.md"
)


def _module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _imported_modules() -> set[str]:
    tree = ast.parse(_module_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _docs_text() -> str:
    return " ".join(
        (
            IMPLEMENTATION_DOC.read_text(encoding="utf-8")
            + "\n"
            + DESIGN_DOC.read_text(encoding="utf-8")
            + "\n"
            + VIEWMODEL_DOC.read_text(encoding="utf-8")
            + "\n"
            + SAVE_DOC.read_text(encoding="utf-8")
        )
        .lower()
        .split()
    )


def test_dialog_imports_only_gui_and_viewmodel_safe_layers() -> None:
    imports = _imported_modules()

    assert "PySide6" in imports
    assert "osw.experimental.feaspec.human_review_io" in imports
    assert "osw.experimental.feaspec.human_review_viewmodel" in imports
    assert "osw.gui.qt_compat" in imports
    assert "osw.gui.theme_tokens" in imports
    assert not any(module.startswith("osw.solvers") for module in imports)
    assert not any(module.startswith("osw.runners") for module in imports)


def test_dialog_does_not_import_or_reference_solver_execution_paths() -> None:
    source = _module_source()
    imports = _imported_modules()

    assert "subprocess" not in imports
    assert "SolverAdapter" not in source
    assert "run_input_deck" not in source
    assert "run_calculix" not in source
    assert "ccx.exe" not in source
    assert not any("runner" in module for module in imports)
    assert not any("adapter" in module and "solvers" in module for module in imports)


def test_dialog_does_not_import_exporter_renderer_or_result_import_paths() -> None:
    source = _module_source()
    imports = _imported_modules()

    assert "calculix_exporter" not in source
    assert "calculix_inp_renderer" not in source
    assert "result_import" not in source
    assert not any("exporter" in module for module in imports)
    assert not any("renderer" in module for module in imports)
    assert not any("result" in module and "import" in module for module in imports)


def test_dialog_does_not_write_files_or_open_file_dialogs() -> None:
    source = _module_source()

    assert "QFileDialog" not in source
    assert "dump_human_review_record" in source
    assert ".write_text(" not in source
    assert ".write_bytes(" not in source
    assert "open(" not in source
    assert "Path(" not in source


def test_dialog_does_not_mutate_projectschema_or_provider_credentials() -> None:
    source = _module_source()
    imports = _imported_modules()

    assert "ProjectSchema" not in source
    assert not any("project_schema" in module for module in imports)
    assert "OPENAI_API_KEY" not in source
    assert "ANTHROPIC_API_KEY" not in source
    assert "GEMINI_API_KEY" not in source
    assert "VLMProvider" not in source
    assert "api_key" not in source.casefold()
    assert "credential" not in source.casefold()


def test_docs_describe_read_only_no_side_effect_gui() -> None:
    text = _docs_text()

    assert "read-only gui dialog implemented" in text
    assert "explicit json review-record save implemented" in text
    assert "no file dialog" in text
    assert "no export bundle" in text
    assert "no result import implementation" in text
    assert "no installed-only run gate implementation" in text
    assert "no solver execution" in text


def test_docs_keep_release_and_validation_claims_bounded() -> None:
    text = _docs_text()

    assert "issue `#8` live validation remains separate" in text
    assert "external solvers are optional and not bundled" in text
    assert "no industrial certification" in text
    assert "vfea remains experimental" in text
    assert "stable production release" not in text
    assert "stable production ready" not in text
    assert "live calculix validation passed" not in text
