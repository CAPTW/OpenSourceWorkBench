from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "feaspec"
    / "calculix_result_write_viewmodel.py"
)
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_write_viewmodel.md"
)
PROJECT_SCHEMA_SOURCE = REPO_ROOT / "src" / "osw" / "core" / "project_schema.py"


def _source_text() -> str:
    return SOURCE_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_source_text())


def test_write_viewmodel_imports_no_gui_solver_writer_network_or_vlm_modules() -> None:
    forbidden_roots = {
        "osw.gui",
        "PySide6",
        "PyQt6",
        "QtWidgets",
        "osw.solvers",
        "osw.runners",
        "sub" + "process",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "openai",
        "anthropic",
        "google.generativeai",
    }
    imported_modules: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")

    for module in imported_modules:
        assert not any(
            module == root or module.startswith(f"{root}.")
            for root in forbidden_roots
        )


def test_write_viewmodel_source_has_no_writer_invocation_or_file_dialog_tokens() -> None:
    text = _source_text()
    forbidden_tokens = (
        "write_calculix_result_dataset",
        "prepare_calculix_result_dataset_write_payloads",
        "QFileDialog",
        "QDialog",
        "QWidget",
        "CalculiXRunner",
        "SolverAdapter",
        "ExternalCommandRunner",
        "Popen",
        "ccx.exe",
        "openai_api_key",
        "anthropic_api_key",
        "gemini_api_key",
        "api_key",
        "credentials",
        "vlmprovider",
    )

    for token in forbidden_tokens:
        assert token not in text
    assert "sub" + "process" not in text


def test_write_viewmodel_does_not_mutate_project_schema_source() -> None:
    text = PROJECT_SCHEMA_SOURCE.read_text(encoding="utf-8")

    assert "FEASpecCalculiXResultWriteViewModel" not in text
    assert "calculix_result_write_viewmodel" not in text
    assert "feaspec-calculix-result-import-write" not in text


def test_write_viewmodel_docs_preserve_required_safety_boundary() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "experimental ui-agnostic view-model implemented" in text
    assert "no gui dialog implementation" in text
    assert "no file dialog implementation" in text
    assert "no writer invocation" in text
    assert "no resultdataset file write" in text
    assert "no solver execution" in text
    assert "no subprocess" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no projectschema mutation" in text
    assert "no vlm api" in text
    assert "no provider credentials" in text
    assert "issue `#8` remains open" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text


def test_write_viewmodel_docs_do_not_claim_forbidden_capabilities() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    forbidden_claims = (
        "gui write command exists",
        "file dialog exists",
        "writer is invoked by the view-model",
        "solver execution is allowed",
        "live ccx validation passed",
        "issue `#8` can close",
        "external solvers are bundled",
        "industrial certification is provided",
        "stable production",
    )

    for claim in forbidden_claims:
        assert claim not in text


def test_write_viewmodel_tests_use_tmp_path_not_tracked_result_fixtures() -> None:
    test_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            REPO_ROOT
            / "tests"
            / "unit"
            / "test_feaspec_calculix_result_write_viewmodel.py",
            REPO_ROOT
            / "tests"
            / "unit"
            / "test_feaspec_calculix_result_write_viewmodel_actions.py",
        )
    )

    assert "tmp_path" in test_text
    assert "tests/" + "fixtures" not in test_text
    assert "fixtures/" + "calculix" not in test_text
