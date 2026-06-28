from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from osw.cli.main import build_parser, main
from osw.cli.optional_solver_manifest_export_summary import (
    OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_COMMAND,
)

COMMAND = OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_COMMAND
MODULE_NAME = "osw.cli.optional_solver_manifest_export_summary"


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main([COMMAND, *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _module_source() -> str:
    module = importlib.import_module(MODULE_NAME)
    return Path(module.__file__).read_text(encoding="utf-8")


def _imported_modules() -> set[str]:
    tree = ast.parse(_module_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {module.lower() for module in modules}


def test_cli_module_imports_without_gui_extras() -> None:
    module = importlib.import_module(MODULE_NAME)
    assert hasattr(module, "run_optional_solver_plugin_manifest_export_summary_cli")
    for imported in _imported_modules():
        assert "pyside" not in imported
        assert "pyqt" not in imported
        assert not imported.startswith("qt")


def test_cli_module_avoids_forbidden_integration_imports() -> None:
    forbidden_roots = {
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "shutil",
        "os",
        "pathlib",
        "gmsh",
        "meshio",
        "pyvista",
        "vtk",
        "coolprop",
        "cantera",
    }
    for imported in _imported_modules():
        root = imported.split(".", 1)[0]
        assert root not in forbidden_roots, imported
        assert not imported.startswith("osw.gui")
        assert not imported.startswith("osw.plugins")
        assert not imported.startswith("osw.solvers")
        assert not imported.startswith("osw.core")
        assert not imported.startswith("osw.post")


def test_cli_source_has_no_discovery_validation_solver_or_release_calls() -> None:
    source = _module_source()
    for phrase in (
        "discover_optional_solver_manifests",
        "discover_local_plugin_manifests",
        "load_optional_solver_plugin_manifest_json",
        "run_discovery(",
        "run_validation(",
        "execute_solver(",
        "pip install",
        "pip uninstall",
        "gh issue",
        "gh release",
        "ProjectSchema(",
        ".write_text(",
        ".write_bytes(",
        "open(",
    ):
        assert phrase not in source, phrase


def test_command_registration_is_visible_from_main_cli() -> None:
    help_text = build_parser().format_help()
    assert COMMAND in help_text


def test_explain_command_succeeds_and_states_boundaries(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["explain", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    for phrase in (
        "redaction-first, stdout-first",
        "Export summary is not validation evidence.",
        "Export summary is not persistence.",
        "Export summary is not a reloadable bundle.",
        "Export summary is not trust restoration.",
        "Export summary is not automatic activation.",
        "Export summary is not issue closure.",
        "Export summary is not release mutation.",
        "A trust label is not certification.",
        "No live discovery.",
        "No plugin package import.",
        "No validation execution.",
        "No solver execution.",
    ):
        assert phrase in out


def test_preview_defaults_to_unavailable_no_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["preview"], capsys)
    assert code == 0
    assert err == ""
    assert "unavailable in-memory state" in out
    assert "readiness: unavailable_no_state" in out
    assert "file output: disabled" in out


def test_preview_sample_state_succeeds_with_stable_labels(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["preview", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    for phrase in (
        "Optional Solver Plugin Manifest Export-Summary CLI",
        "Preview:",
        "sources:",
        "candidates:",
        "diagnostics:",
        "limitations:",
        "redaction required:",
        "stale sources:",
        "conflicts:",
        "unsafe claims:",
        "evidence retained:",
        "history retained:",
    ):
        assert phrase in out


@pytest.mark.parametrize(
    "subcommand, expected",
    [
        ("sections", "Sections:"),
        ("sources", "Sources/provenance:"),
        ("candidates", "Candidates:"),
        ("acknowledgements", "Acknowledgements:"),
        ("diagnostics", "Diagnostics:"),
        ("redaction", "Redaction/privacy:"),
        ("stale-sources", "Stale sources / re-preview:"),
        ("conflicts", "Conflicts/shared stacks:"),
        ("unsafe-claims", "Unsafe claims:"),
        ("evidence", "Evidence/history:"),
        ("limitations", "Limitations:"),
        ("actions", "Actions:"),
    ],
)
def test_review_commands_succeed(
    subcommand: str,
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run([subcommand, "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert expected in out
    assert "Safety boundary:" in out


def test_sources_output_preserves_trust_provenance_boundary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["sources", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "User/plugin manifests remain untrusted by default." in out
    assert "Built-ins are authoritative by default." in out
    assert "A trust label is not certification." in out
    assert "user-gmsh.json" in out
    assert "C:/Users/Research" not in out


def test_redaction_output_does_not_leak_raw_absolute_paths(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["redaction", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "Raw absolute paths are hidden by default." in out
    assert "secret_like_content_blocked" in out
    assert "C:/Users/Research" not in out
    assert "C:\\Users\\Research" not in out


def test_stale_conflict_unsafe_and_evidence_outputs_state_boundaries(
    capsys: pytest.CaptureFixture[str],
) -> None:
    checks = {
        "stale-sources": "Stale sources are not silently trusted.",
        "conflicts": "Built-ins win by default.",
        "unsafe-claims": "Unsafe claims are not exported as truth.",
        "evidence": "Skipped-missing remains skipped-missing.",
    }
    for subcommand, phrase in checks.items():
        code, out, err = _run([subcommand, "--sample-state"], capsys)
        assert code == 0
        assert err == ""
        assert phrase in out


def test_actions_output_marks_side_effect_actions_future_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["actions", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    for phrase in (
        "write export-summary file: disabled/future-only",
        "create report file: disabled/future-only",
        "copy to clipboard: disabled/future-only",
        "open output folder: disabled/future-only",
        "create reloadable bundle: disabled/future-only",
        "run discovery: disabled/future-only",
        "run validation: disabled/future-only",
        "execute solver: disabled/future-only",
        "close issue: disabled/future-only",
        "mutate release: disabled/future-only",
        "claim certification: disabled/future-only",
    ):
        assert phrase in out


def test_json_output_is_deterministic_valid_and_redacted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = ["preview", "--sample-state", "--format", "json"]
    code, out, err = _run(args, capsys)
    assert code == 0
    assert err == ""
    payload = json.loads(out)

    code_again, out_again, err_again = _run(args, capsys)
    assert code_again == 0
    assert err_again == ""
    assert out_again == out

    assert payload["stdout_first"] is True
    assert payload["file_output_enabled"] is False
    assert payload["state_source_policy"]["live_discovery_performed"] is False
    assert payload["state_source_policy"]["validation_execution_performed"] is False
    assert payload["state_source_policy"]["solver_execution_performed"] is False
    assert "OSPMG_EXPORT_SUMMARY_CLI_STDOUT_ONLY" in payload["cli_diagnostics"]
    assert "C:/Users/Research" not in out
    assert "validation-pass claim" in out
    assert "certification claim" in out


def test_write_summary_is_disabled_future_only_and_does_not_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())
    code, out, err = _run(["write-summary", "--sample-state"], capsys)
    after = set(tmp_path.iterdir())
    assert code == 2
    assert out == ""
    assert after == before
    assert "write-summary: blocked" in err
    assert "OSPMG_EXPORT_SUMMARY_CLI_FILE_OUTPUT_DISABLED" in err
    assert "creates no export file" in err


def test_review_commands_create_no_export_report_or_bundle_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())
    for subcommand in (
        "explain",
        "preview",
        "sections",
        "sources",
        "candidates",
        "acknowledgements",
        "diagnostics",
        "redaction",
        "stale-sources",
        "conflicts",
        "unsafe-claims",
        "evidence",
        "limitations",
        "actions",
    ):
        code, _out, err = _run([subcommand, "--sample-state"], capsys)
        assert code == 0
        assert err == ""
    after = set(tmp_path.iterdir())
    assert after == before


def test_output_confirms_no_projectschema_discovery_validation_solver_or_mutation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["preview", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    for phrase in (
        "No ProjectSchema mutation.",
        "No discovery execution.",
        "No plugin package import.",
        "No validation execution.",
        "No solver execution.",
        "No dependency installation.",
        "No dependency uninstall.",
        "No solver uninstall.",
        "No issue mutation.",
        "No release mutation.",
        "No tag mutation.",
        "No asset mutation.",
        "No validation-pass claim.",
        "No validation-fail claim.",
        "No issue-closure claim.",
        "No bundled-solver claim.",
        "No certification claim.",
    ):
        assert phrase in out
