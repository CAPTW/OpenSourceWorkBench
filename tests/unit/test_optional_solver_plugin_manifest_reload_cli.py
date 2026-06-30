from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from osw.cli.main import build_parser, main
from osw.cli.optional_solver_manifest_reload import (
    OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND,
)

COMMAND = OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_COMMAND
MODULE_NAME = "osw.cli.optional_solver_manifest_reload"


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
    assert hasattr(module, "run_optional_solver_plugin_manifest_reload_cli")
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


def test_cli_source_has_no_file_reader_parser_or_runtime_side_effect_calls() -> None:
    source = _module_source()
    for phrase in (
        "open(",
        "Path(",
        "pathlib",
        "json.load(",
        "json.loads(",
        ".read_text(",
        ".read_bytes(",
        ".write_text(",
        ".write_bytes(",
        "discover_optional_solver_manifests",
        "discover_local_plugin_manifests",
        "load_optional_solver_plugin_manifest_json",
        "run_discovery(",
        "run_validation(",
        "execute_solver(",
        "subprocess",
        "webbrowser",
        "pyperclip",
        "clipboard.copy",
        "copy_to_clipboard(",
        "os.startfile",
        "Popen",
        "pip install",
        "pip uninstall",
        "gh issue",
        "gh release",
        "ProjectSchema(",
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
        "stdout-first, review-only",
        "Reloaded manifest UX state is not validation evidence.",
        "Reloaded manifest UX state is not validation failure.",
        "Reloaded manifest UX state is not trust restoration.",
        "Reloaded manifest UX state is not automatic activation.",
        "Reloaded manifest UX state is not issue closure.",
        "Reloaded manifest UX state is not release mutation.",
        "Reloaded manifest UX state is not certification.",
        "No file reader/parser implementation.",
        "No persisted state file reading.",
        "No persisted state file parsing.",
        "No live discovery.",
        "No plugin package import.",
        "No validation execution.",
        "No solver execution.",
    ):
        assert phrase in out


def test_preview_defaults_to_unavailable_no_payload_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["preview"], capsys)
    assert code == 0
    assert err == ""
    assert "unavailable in-memory state" in out
    assert "readiness: unavailable_no_payload" in out
    assert "file reader: disabled" in out
    assert "file parser: disabled" in out


def test_preview_sample_state_succeeds_with_stable_labels(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["preview", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    for phrase in (
        "Optional Solver Plugin Manifest Reload CLI",
        "Preview:",
        "sources:",
        "candidates:",
        "acknowledgements:",
        "diagnostics:",
        "redaction rows:",
        "stale sources:",
        "conflicts:",
        "unsafe claims:",
        "evidence rows:",
        "model line: Optional Solver Plugin Manifest Reload View-Model",
    ):
        assert phrase in out


@pytest.mark.parametrize(
    ("subcommand", "expected"),
    [
        ("schema", "Schema/migration:"),
        ("sources", "Sources/provenance:"),
        ("candidates", "Candidates:"),
        ("acknowledgements", "Acknowledgements:"),
        ("diagnostics", "Diagnostics:"),
        ("redaction", "Redaction/privacy:"),
        ("stale-sources", "Stale sources / re-preview:"),
        ("conflicts", "Conflicts/shared stacks:"),
        ("unsafe-claims", "Unsafe claims:"),
        ("evidence", "Evidence/history:"),
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


def test_schema_output_keeps_project_schema_boundary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["schema", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "Schema mismatch is not validation failure." in out
    assert "Reload schema is separate from ProjectSchema." in out
    assert "supported=True" in out


def test_sources_output_preserves_trust_provenance_boundary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["sources", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "User/plugin manifests remain untrusted by default." in out
    assert "Built-ins are authoritative by default." in out
    assert "A trust label is not certification." in out
    assert "sample.json" in out


def test_candidates_output_keeps_activation_and_trust_disabled(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["candidates", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "automatic activation" in out
    assert "trust restoration" in out
    assert "no_automatic_activation=True" in out
    assert "no_trust_restoration=True" in out


def test_acknowledgements_output_lists_required_acks_and_expiry(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["acknowledgements", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "required acknowledgements:" in out
    assert "reload_not_validation" in out
    assert "source_fingerprint_change" in out
    assert "future_discovery_refresh_result" in out


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
        "unsafe-claims": "Unsafe claims are not reloaded as truth.",
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
        "read reload file: disabled/future-only",
        "parse reload file: disabled/future-only",
        "runtime reload: disabled/future-only",
        "create reloadable bundle: disabled/future-only",
        "create export file: disabled/future-only",
        "create report file: disabled/future-only",
        "copy to clipboard: disabled/future-only",
        "attach to report: disabled/future-only",
        "open output folder: disabled/future-only",
        "run discovery: disabled/future-only",
        "run validation: disabled/future-only",
        "execute solver: disabled/future-only",
        "close issue: disabled/future-only",
        "mutate release: disabled/future-only",
        "claim validation success/failure: disabled/future-only",
        "claim certification: disabled/future-only",
    ):
        assert phrase in out


def test_load_preview_is_disabled_future_only_and_does_not_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())
    code, out, err = _run(["load-preview", "--sample-state"], capsys)
    after = set(tmp_path.iterdir())
    assert code == 2
    assert out == ""
    assert after == before
    assert "load-preview: blocked" in err
    assert "OSPMG_RELOAD_CLI_FILE_READER_DISABLED" in err
    assert "OSPMG_RELOAD_CLI_FILE_PARSER_DISABLED" in err
    assert "without implying validation failure" in err


def test_review_commands_create_no_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.iterdir())
    for subcommand in (
        "explain",
        "preview",
        "schema",
        "sources",
        "candidates",
        "acknowledgements",
        "diagnostics",
        "redaction",
        "stale-sources",
        "conflicts",
        "unsafe-claims",
        "evidence",
        "actions",
    ):
        code, _out, err = _run([subcommand, "--sample-state"], capsys)
        assert code == 0
        assert err == ""
    after = set(tmp_path.iterdir())
    assert after == before


def test_json_output_is_deterministic_valid_and_bounded(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = ["preview", "--sample-state", "--json"]
    code, out, err = _run(args, capsys)
    assert code == 0
    assert err == ""
    payload = json.loads(out)

    code_again, out_again, err_again = _run(args, capsys)
    assert code_again == 0
    assert err_again == ""
    assert out_again == out

    assert payload["stdout_first"] is True
    assert payload["file_reader_enabled"] is False
    assert payload["file_parser_enabled"] is False
    assert payload["load_preview_enabled"] is False
    assert payload["state_source_policy"]["file_reader_performed"] is False
    assert payload["state_source_policy"]["file_parser_performed"] is False
    assert payload["state_source_policy"]["runtime_reload_performed"] is False
    assert payload["state_source_policy"]["validation_execution_performed"] is False
    assert payload["state_source_policy"]["solver_execution_performed"] is False
    assert "OSPMG_RELOAD_CLI_STDOUT_ONLY" in payload["cli_diagnostics"]
    assert "C:/Users/Research" not in out


def test_json_selected_payload_matches_section(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["sources", "--sample-state", "--json"], capsys)
    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert payload["subcommand"] == "sources"
    assert payload["selected"] == payload["view_model"]["sources"]


def test_state_source_flags_are_mutually_exclusive(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(
        ["preview", "--sample-state", "--empty-state"],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "Select only one state source" in err


def test_empty_and_unavailable_states_are_explicit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    empty_code, empty_out, empty_err = _run(["preview", "--empty-state"], capsys)
    unavailable_code, unavailable_out, unavailable_err = _run(
        ["preview", "--unavailable-state"],
        capsys,
    )
    assert empty_code == 0
    assert unavailable_code == 0
    assert empty_err == ""
    assert unavailable_err == ""
    assert "deterministic empty in-memory state" in empty_out
    assert "unavailable in-memory state" in unavailable_out
    assert "readiness: unavailable_no_payload" in empty_out
    assert "readiness: unavailable_no_payload" in unavailable_out


def test_output_confirms_no_validation_trust_activation_issue_release_or_certification(
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
        "No automatic activation.",
        "No trust restoration.",
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
