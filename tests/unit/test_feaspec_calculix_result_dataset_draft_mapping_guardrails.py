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
    / "calculix_result_dataset_draft_mapping.py"
)
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_dataset_draft_mapping.md"
)


def _source_text() -> str:
    return SOURCE_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_source_text())


def test_draft_mapping_imports_no_solver_runner_gui_network_or_vlm_modules() -> None:
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


def test_draft_mapping_source_has_no_write_persistence_or_execution_tokens() -> None:
    text = _source_text()
    forbidden_tokens = (
        "ResultDataset(",
        "write_text(",
        "write_bytes(",
        "mkdir(",
        "parse_frd",
        "parse_calculix_results",
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


def test_draft_mapping_docs_preserve_safety_boundary() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "draft mapping only" in text
    assert "no resultdataset persistence" in text
    assert "no numerical `.frd` parser" in text
    assert "no mesh reconstruction" in text
    assert "no solver execution" in text
    assert "issue `#8` remains open" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text
    assert "no vlm api" in text
    assert "no provider credentials" in text
    for forbidden_claim in (
        "resultdataset persistence exists",
        "frd numerical parsing exists",
        "mesh reconstruction exists",
        "ccx validation has passed",
        "external solvers are bundled",
        "industrial certification is provided",
        "stable production",
    ):
        assert forbidden_claim not in text
