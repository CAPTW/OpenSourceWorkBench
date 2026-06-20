from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WRITER_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "feaspec"
    / "calculix_result_dataset_writer.py"
)
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_dataset_writer.md"
)
CLI_SOURCE = REPO_ROOT / "src" / "osw" / "cli" / "main.py"


def _source_text() -> str:
    return WRITER_SOURCE.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_source_text())


def test_writer_imports_no_solver_runner_gui_network_or_vlm_modules() -> None:
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


def test_writer_source_has_no_execution_artifact_copy_or_provider_tokens() -> None:
    text = _source_text()
    forbidden_tokens = (
        "shutil.copy",
        "CalculiXRunner",
        "SolverAdapter",
        "ExternalCommandRunner",
        "Popen",
        "ccx.exe",
        "parse_frd",
        "parse_calculix_results",
        "ProjectSchema",
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


def test_no_cli_write_command_was_added() -> None:
    text = CLI_SOURCE.read_text(encoding="utf-8")

    assert "feaspec-calculix-result-import-write" not in text
    assert "write_calculix_result_dataset" not in text


def test_writer_docs_preserve_safety_boundary() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "experimental library writer implemented" in text
    assert "no cli write command" in text
    assert "no gui write command" in text
    assert "no solver execution" in text
    assert "no artifact copying" in text
    assert "no subprocess" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no projectschema mutation" in text
    assert "issue `#8` remains open" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text
    assert "no vlm api" in text
    assert "no provider credentials" in text
    for code in (
        "fdw_write_completed",
        "fdw_temp_write_failed",
        "fdw_target_replace_failed",
        "fdw_unplanned_file_collision",
        "fdw_artifact_copy_forbidden",
    ):
        assert code in text
    for forbidden_claim in (
        "cli write command exists",
        "gui write command exists",
        "solver execution is allowed",
        "live validation passed",
        "ccx validation has passed",
        "external solvers are bundled",
        "industrial certification is provided",
    ):
        assert forbidden_claim not in text


def test_writer_tests_use_tmp_path_not_tracked_result_fixtures() -> None:
    test_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            REPO_ROOT
            / "tests"
            / "unit"
            / "test_feaspec_calculix_result_dataset_writer.py",
            REPO_ROOT
            / "tests"
            / "unit"
            / "test_feaspec_calculix_result_dataset_writer_atomic.py",
        )
    )

    assert "tmp_path" in test_text
    assert "tests/" + "fixtures" not in test_text
    assert "fixtures/" + "calculix" not in test_text
