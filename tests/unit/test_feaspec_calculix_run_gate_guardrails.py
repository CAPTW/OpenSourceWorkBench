from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_GATE_SOURCE = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "calculix_run_gate.py"
)
DIAGNOSTICS_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "feaspec"
    / "calculix_run_diagnostics.py"
)
PROJECT_SCHEMA_SOURCE = REPO_ROOT / "src" / "osw" / "core" / "project_schema.py"
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_run_gate_installed_only.md"
)


def _run_gate_text() -> str:
    return RUN_GATE_SOURCE.read_text(encoding="utf-8")


def _run_gate_tree() -> ast.Module:
    return ast.parse(_run_gate_text())


def test_run_gate_imports_only_local_process_boundary_not_gui_solver_or_network() -> None:
    forbidden_roots = {
        "osw.gui",
        "osw.solvers",
        "osw.runners",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "openai",
        "anthropic",
        "google.generativeai",
    }
    imported_modules: list[str] = []
    for node in ast.walk(_run_gate_tree()):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")

    assert "subprocess" in imported_modules
    for module in imported_modules:
        assert not any(
            module == root or module.startswith(f"{root}.") for root in forbidden_roots
        )


def test_run_gate_does_not_reference_solver_adapter_runner_or_result_import() -> None:
    text = _run_gate_text()
    forbidden_tokens = (
        "SolverAdapter",
        "CalculiXRunner",
        "ExternalCommandRunner",
        "osw.solvers",
        "osw.runners",
        "parse_calculix_results",
        "parse_calculix_run_artifacts",
        "ResultDataset",
        "gh release",
        "gh issue",
        "release upload",
        "asset upload",
    )
    for token in forbidden_tokens:
        assert token not in text


def test_run_gate_does_not_add_vlm_api_or_credentials() -> None:
    combined = (_run_gate_text() + "\n" + DIAGNOSTICS_SOURCE.read_text(encoding="utf-8")).lower()
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


def test_run_gate_does_not_mutate_project_schema_source() -> None:
    text = PROJECT_SCHEMA_SOURCE.read_text(encoding="utf-8")

    assert "FEASpecCalculiXRunResult" not in text
    assert "run_calculix_installed_only" not in text
    assert "CalculiXRuntimeDiscovery" not in text


def test_run_gate_docs_preserve_installed_only_boundaries() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "installed-only" in text
    assert "no solver install" in text
    assert "no result import" in text
    assert "issue `#8` remains open" in text
    assert "no solveradapter" in text
    assert "no broad runner integration" in text
    assert "no projectschema mutation" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text
    assert "no release mutation" in text
    assert "no issue mutation" in text
    for forbidden_claim in (
        "ccx validation passed",
        "external solvers are bundled",
        "industrial certification is provided",
        "stable production",
        "issue #8 can close",
        "issue `#8` can close",
        "vlm api is implemented",
    ):
        assert forbidden_claim not in text
