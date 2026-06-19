from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "feaspec"
    / "calculix_result_dataset_write_plan.py"
)
DIAGNOSTIC_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "feaspec"
    / "calculix_result_dataset_write_diagnostics.py"
)
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_dataset_write_plan.md"
)


def _source_text() -> str:
    return PLAN_SOURCE.read_text(encoding="utf-8") + DIAGNOSTIC_SOURCE.read_text(
        encoding="utf-8"
    )


def _tree() -> ast.Module:
    return ast.parse(_source_text())


def test_write_plan_imports_no_solver_runner_gui_network_or_vlm_modules() -> None:
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


def test_write_plan_source_has_no_persistence_execution_or_cli_write_tokens() -> None:
    text = _source_text()
    forbidden_tokens = (
        "ResultDataset(",
        "write_text(",
        "write_bytes(",
        "mkdir(",
        "replace(",
        "rename(",
        "shutil.copy",
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


def test_write_plan_docs_preserve_safety_boundary() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "experimental in-memory write plan implemented" in text
    assert "no resultdataset persistence" in text
    assert "no actual file writes" in text
    assert "no solver execution" in text
    assert "no write-capable import cli" in text
    assert "issue `#8` remains open" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text
    assert "no vlm api" in text
    assert "no provider credentials" in text
    assert "fdw_atomic_write_not_implemented" in text
    assert "fdw_artifact_copy_not_implemented" in text
    assert "fdw_resultdataset_persistence_forbidden" in text
    for forbidden_claim in (
        "resultdataset persistence exists",
        "actual file writes are implemented",
        "write-capable import cli exists",
        "live validation passed",
        "ccx validation has passed",
        "external solvers are bundled",
        "industrial certification is provided",
        "stable production",
    ):
        assert forbidden_claim not in text


def test_write_plan_tests_use_tmp_path_not_tracked_solver_fixtures() -> None:
    test_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            REPO_ROOT
            / "tests"
            / "unit"
            / "test_feaspec_calculix_result_dataset_write_plan.py",
            REPO_ROOT
            / "tests"
            / "unit"
            / "test_feaspec_calculix_result_dataset_write_plan_paths.py",
        )
    )

    assert "tmp_path" in test_text
    assert "tests/" + "fixtures" not in test_text
    assert "fixtures/" + "calculix" not in test_text
