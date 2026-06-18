from __future__ import annotations

import ast
from pathlib import Path

from osw.cli.main import build_parser

REPO_ROOT = Path(__file__).resolve().parents[2]
IMPORT_SOURCE = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "calculix_result_import.py"
)
DIAGNOSTICS_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "feaspec"
    / "calculix_result_diagnostics.py"
)
PROJECT_SCHEMA_SOURCE = REPO_ROOT / "src" / "osw" / "core" / "project_schema.py"
DOC_PATH = (
    REPO_ROOT / "docs" / "experimental" / "feaspec_calculix_result_import_model.md"
)
MODEL_TEST_SOURCE = (
    REPO_ROOT / "tests" / "unit" / "test_feaspec_calculix_result_import_model.py"
)


def _source_text() -> str:
    return IMPORT_SOURCE.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_source_text())


def _subcommand_names() -> set[str]:
    parser = build_parser()
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            return set(choices)
    return set()


def test_result_import_model_imports_no_solver_runner_gui_command_or_network_modules() -> None:
    forbidden_roots = {
        "osw.gui",
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


def test_result_import_model_has_no_parser_function_or_external_execution_tokens() -> None:
    text = _source_text()
    forbidden_tokens = (
        "parse_frd",
        "parse_dat",
        "parse_calculix_results",
        "CalculiXRunner",
        "SolverAdapter",
        "ExternalCommandRunner",
        "run_input_deck",
        "Popen",
        "ccx.exe",
        "ResultDataset(",
        "write_text(",
        "write_bytes(",
        "mkdir(",
    )
    for token in forbidden_tokens:
        assert token not in text
    assert "sub" + "process" not in text


def test_result_import_model_does_not_add_vlm_api_or_credentials() -> None:
    combined = (
        _source_text().lower()
        + "\n"
        + DIAGNOSTICS_SOURCE.read_text(encoding="utf-8").lower()
    )
    forbidden_tokens = (
        "openai_api_key",
        "anthropic_api_key",
        "gemini_api_key",
        "api_key",
        "credentials",
        "vlmprovider",
    )
    for token in forbidden_tokens:
        assert token not in combined


def test_result_import_model_does_not_mutate_project_schema_source() -> None:
    text = PROJECT_SCHEMA_SOURCE.read_text(encoding="utf-8")

    assert "FEASpecCalculiXResultImportPlan" not in text
    assert "FEASpecCalculiXResultDatasetDraft" not in text
    assert "plan_calculix_result_import" not in text


def test_result_import_cli_command_is_not_registered() -> None:
    assert "feaspec-calculix-result-import" not in _subcommand_names()


def test_result_import_tests_use_tmp_path_not_tracked_result_fixtures() -> None:
    text = MODEL_TEST_SOURCE.read_text(encoding="utf-8")

    assert "tmp_path" in text
    assert "tests/fixtures" not in text
    assert "fixtures/calculix" not in text


def test_result_import_docs_preserve_model_only_boundaries() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "result import model only" in text
    assert "no numerical parser" in text
    assert "no solver execution" in text
    assert "no resultdataset write" in text
    assert "issue `#8` remains open" in text
    assert "no industrial certification" in text
    assert "no bundled solver" in text
    assert "no vlm api" in text
    assert "no provider credentials" in text
    for forbidden_claim in (
        "ccx validation has passed",
        "result parsing exists",
        "numerical parser exists",
        "resultdataset persistence exists",
        "industrial certification is provided",
        "external solvers are bundled",
        "stable production",
    ):
        assert forbidden_claim not in text
