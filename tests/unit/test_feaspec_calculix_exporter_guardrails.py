from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

from osw.cli.main import (
    _build_feaspec_calculix_export_preview,
    _planned_feaspec_calculix_files,
    _print_feaspec_calculix_export_preview,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTER_SOURCE = (
    REPO_ROOT / "src" / "osw" / "experimental" / "feaspec" / "calculix_exporter.py"
)
DIAGNOSTICS_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "feaspec"
    / "calculix_export_diagnostics.py"
)
PROJECT_SCHEMA = REPO_ROOT / "src" / "osw" / "core" / "project_schema.py"
DOC_PATH = REPO_ROOT / "docs" / "experimental" / "feaspec_calculix_exporter_no_run.md"
CLI_DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_exporter_cli_preview.md"
)


def _exporter_text() -> str:
    return EXPORTER_SOURCE.read_text(encoding="utf-8")


def _exporter_tree() -> ast.Module:
    return ast.parse(_exporter_text())


def test_exporter_does_not_import_solver_runner_gui_command_or_network_modules() -> None:
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
    for node in ast.walk(_exporter_tree()):
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


def test_exporter_does_not_reference_solver_adapter_runner_or_external_commands() -> None:
    text = _exporter_text()
    forbidden_tokens = (
        "SolverAdapter",
        "CalculiXRunner",
        "ExternalCommandRunner",
        "sub" + "process",
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


def test_exporter_does_not_add_vlm_api_or_credentials() -> None:
    combined = (
        _exporter_text().lower()
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


def test_exporter_does_not_mutate_project_schema_source() -> None:
    text = PROJECT_SCHEMA.read_text(encoding="utf-8")

    assert "FEASpecCalculiXExportResult" not in text
    assert "export_calculix_case" not in text


def test_export_preview_cli_helper_has_no_write_or_execution_calls() -> None:
    source = "\n".join(
        (
            inspect.getsource(_build_feaspec_calculix_export_preview),
            inspect.getsource(_planned_feaspec_calculix_files),
            inspect.getsource(_print_feaspec_calculix_export_preview),
        )
    )

    forbidden_tokens = (
        "export_calculix_case(",
        "write_calculix_inp(",
        "SolverAdapter",
        "CalculiXRunner",
        "ExternalCommandRunner",
        "sub" + "process",
        "Popen",
        "run_input_deck",
        "ccx.exe",
        "mkdir",
        "write_text",
        "write_bytes",
    )
    for token in forbidden_tokens:
        assert token not in source
    for pattern in (
        r"\bos\.system\s*\(",
        r"\bos\.popen\s*\(",
        r"\bspawn\s*\(",
        r"\bexecv",
    ):
        assert re.search(pattern, source) is None


def test_feaspec_tracked_inp_fixtures_stay_in_dedicated_directory() -> None:
    fixture_root = REPO_ROOT / "tests" / "fixtures" / "feaspec"
    allowed_root = fixture_root / "calculix_golden"
    fixtures = list(fixture_root.rglob("*.inp"))

    assert fixtures
    for fixture in fixtures:
        assert fixture.is_relative_to(allowed_root)


def test_exporter_docs_keep_no_run_and_live_validation_boundaries() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "no solver execution" in text
    assert "no `ccx` invocation" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no subprocess" in text
    assert "issue `#8`" in text
    assert "live calculix validation remains separate" in text
    assert "does not validate installed `ccx`" in text
    assert "no production certification" in text
    assert "no bundled external solver" in text
    for forbidden_claim in (
        "ccx validation passed",
        "external solvers are bundled",
        "solver execution exists",
        "industrial certification is provided",
        "stable production",
        "vlm api is implemented",
    ):
        assert forbidden_claim not in text


def test_export_preview_cli_docs_keep_no_write_and_live_validation_boundaries() -> None:
    text = CLI_DOC_PATH.read_text(encoding="utf-8").lower()

    assert "experimental preview command" in text
    assert "no files written" in text
    assert "no solver execution" in text
    assert "no `.inp`" in text
    assert "no manifest" in text
    assert "no readme" in text
    assert "no ccx" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no subprocess" in text
    assert "issue `#8`" in text
    assert "live calculix validation remains separate" in text
    assert "no bundled solver" in text
    assert "no industrial certification" in text
    for forbidden_claim in (
        "ccx validation passed",
        "external solvers are bundled",
        "solver execution exists",
        "industrial certification is provided",
        "stable production",
        "vlm api is implemented",
    ):
        assert forbidden_claim not in text
