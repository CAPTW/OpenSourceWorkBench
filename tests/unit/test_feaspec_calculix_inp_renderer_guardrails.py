from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RENDERER_SOURCE = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "calculix_inp_renderer.py"
)
DIAGNOSTICS_SOURCE = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "calculix_inp_diagnostics.py"
)
PROJECT_SCHEMA = REPO_ROOT / "src" / "osw" / "core" / "project_schema.py"
IMPLEMENTATION_DOC = (
    REPO_ROOT / "docs" / "experimental" / "feaspec_to_calculix_inp_renderer_implementation.md"
)
DESIGN_DOC = REPO_ROOT / "docs" / "experimental" / "feaspec_to_calculix_inp_writer_design.md"


def _renderer_text() -> str:
    return RENDERER_SOURCE.read_text(encoding="utf-8")


def _renderer_tree() -> ast.Module:
    return ast.parse(_renderer_text())


def test_renderer_does_not_import_solver_runner_gui_command_or_network_modules() -> None:
    forbidden_roots = {
        "osw.gui",
        "osw.solvers",
        "osw.runners",
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "urllib",
        "openai",
        "anthropic",
        "google.generativeai",
    }
    for node in ast.walk(_renderer_tree()):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        else:
            continue
        for module in modules:
            assert not any(
                module == root or module.startswith(f"{root}.")
                for root in forbidden_roots
            )


def test_renderer_does_not_reference_solver_adapter_runner_or_external_commands() -> None:
    text = _renderer_text()
    forbidden_tokens = (
        "SolverAdapter",
        "CalculiXRunner",
        "ExternalCommandRunner",
        "subprocess",
        "Popen",
        "run_input_deck",
        "ccx.exe",
    )
    for token in forbidden_tokens:
        assert token not in text
    for pattern in (
        r"\bos\.system\s*\(",
        r"\bos\.popen\s*\(",
        r"\bspawn\s*\(",
        r"\bexecv",
    ):
        assert re.search(pattern, text) is None


def test_renderer_does_not_add_vlm_api_or_credentials() -> None:
    combined = (
        _renderer_text().lower()
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


def test_renderer_does_not_mutate_project_schema_source() -> None:
    text = PROJECT_SCHEMA.read_text(encoding="utf-8")

    assert "CalculiXInpRenderResult" not in text
    assert "render_calculix_inp" not in text


def test_no_tracked_feaspec_inp_golden_fixtures_are_required() -> None:
    fixture_root = REPO_ROOT / "tests" / "fixtures" / "feaspec"

    assert not list(fixture_root.rglob("*.inp"))


def test_renderer_docs_keep_no_run_and_live_validation_boundaries() -> None:
    text = (
        IMPLEMENTATION_DOC.read_text(encoding="utf-8").lower()
        + "\n"
        + DESIGN_DOC.read_text(encoding="utf-8").lower()
    )

    assert "no solver execution" in text
    assert "issue #8" in text or "issue `#8`" in text
    assert "live calculix" in text
    assert "remains separate" in text
    assert (
        "does not validate installed `ccx`" in text
        or "does not validate a local `ccx`" in text
    )
    for forbidden_claim in (
        "ccx validation passed",
        "external solvers are bundled",
        "solver execution exists",
        "industrial certification is provided",
    ):
        assert forbidden_claim not in text
    assert "stable production claim" in text
