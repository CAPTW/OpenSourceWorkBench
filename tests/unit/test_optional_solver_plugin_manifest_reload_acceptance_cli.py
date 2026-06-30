from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from osw.cli.main import build_parser, main
from osw.cli.optional_solver_manifest_reload_acceptance import (
    OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_COMMAND,
)
from osw.experimental.optional_solvers import (
    RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS,
    RELOAD_ACCEPTANCE_REQUIRED_ACKS,
)

COMMAND = OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_COMMAND
MODULE_NAME = "osw.cli.optional_solver_manifest_reload_acceptance"
REPO_ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTATION_DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_cli_implementation.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main([COMMAND, *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _json(args: list[str], capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    code, out, err = _run([*args, "--json"], capsys)
    assert code == 0
    assert err == ""
    payload = json.loads(out)
    assert isinstance(payload, dict)
    return payload


def _module_source() -> str:
    module = importlib.import_module(MODULE_NAME)
    return Path(module.__file__).read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_module_source())


def _imported_modules() -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {module.lower() for module in modules}


def _called_names() -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    return {call.lower() for call in calls}


def _assert_no_success_or_mutation_claims(text: str) -> None:
    forbidden = (
        "validation_success: True",
        "validation_failure: True",
        "issue_closure: True",
        "release_mutation: True",
        "certification: True",
        "validation-pass evidence",
        "validation-fail evidence",
        "issue closure evidence",
        "release mutation evidence",
        "certified manifest",
    )
    for phrase in forbidden:
        assert phrase not in text
    required_denials = (
        "Exit code 0 is not validation success.",
        "Exit code 0 is not validation failure.",
        "Acceptance readiness is not validation evidence.",
        "Acceptance readiness is not validation failure.",
        "Trust label is not certification.",
    )
    for phrase in required_denials:
        assert phrase in text


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_module_imports_and_main_dispatcher_registration() -> None:
    module = importlib.import_module(MODULE_NAME)
    assert hasattr(module, "run_optional_solver_plugin_manifest_reload_acceptance_cli")
    assert hasattr(module, "add_optional_solver_plugin_manifest_reload_acceptance_parser")
    assert COMMAND in build_parser().format_help()


def test_implementation_docs_and_meta_entries_are_present() -> None:
    doc = _read(IMPLEMENTATION_DOC)
    normalised = " ".join(doc.lower().split())
    for phrase in (
        "Experimental reload acceptance CLI review is implemented",
        "stdout-first",
        "review-only",
        "no runtime reload acceptance",
        "no file io",
        "no reader invocation",
        "no projectschema mutation",
        "Exit-Code Policy",
        "Relationship To Reload Acceptance View-Model",
        "Relationship To Live Optional Validation Issues",
        "OSW-EXP-124",
    ):
        assert phrase in doc or " ".join(phrase.lower().split()) in normalised
    assert "ADR-0157" in _read(DECISION_LOG)
    assert "reload acceptance CLI implementation" in _read(GUARDRAILS)
    assert "reload acceptance CLI implementation overreach" in _read(RISK_REGISTER)
    assert "automated CLI implementation evidence" in _read(VALIDATION_MATRIX)
    assert "reload acceptance CLI implementation" in _read(RELEASE_CHECKLIST)
    assert "Acceptance CLI Implementation" in _read(CHANGELOG)


def test_default_preview_is_unavailable_no_preview(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["preview"], capsys)
    assert code == 0
    assert err == ""
    assert "unavailable/no-preview in-memory state" in out
    assert "state: no_preview" in out
    assert "readiness: unavailable_no_preview" in out
    assert "missing preview blocks acceptance review" in out
    _assert_no_success_or_mutation_claims(out)


def test_explain_renders_purpose_and_non_actions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["explain", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "Definition:" in out
    assert "stdout" in out
    for phrase in (
        "CLI acceptance review performs no file IO.",
        "CLI acceptance review reads no files.",
        "CLI acceptance review parses no files.",
        "CLI acceptance review invokes no reload file reader.",
        "CLI acceptance review calls no GUI code.",
        "CLI acceptance review mutates no ProjectSchema.",
        "CLI acceptance review executes no validation.",
        "CLI acceptance review executes no solver.",
        "CLI acceptance review claims no certification.",
    ):
        assert phrase in out


@pytest.mark.parametrize(
    ("subcommand", "expected"),
    [
        ("preview", "Summary/readiness:"),
        ("summary", "action_state: disabled_future_only"),
        ("blockers", "Preconditions/blockers:"),
        ("acknowledgements", "Acknowledgements:"),
        ("expiry", "Acknowledgement expiry:"),
        ("diagnostics", "OSPMG_RELOAD_ACCEPTANCE_"),
        ("actions", "Disabled/future actions:"),
        ("safety", "Safety guidance:"),
    ],
)
def test_review_subcommands_render_expected_sections_and_return_zero(
    subcommand: str,
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run([subcommand, "--blocked-state"], capsys)
    assert code == 0
    assert err == ""
    assert expected in out
    assert "Exit-code policy:" in out
    _assert_no_success_or_mutation_claims(out)


def test_acknowledgements_and_expiry_rows_are_visible(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["acknowledgements", "--ready-state"], capsys)
    assert code == 0
    assert err == ""
    for ack_id in RELOAD_ACCEPTANCE_REQUIRED_ACKS:
        assert ack_id in out
    assert "not_validation_evidence=True" in out
    assert "not_trust_restoration=True" in out

    code, out, err = _run(["expiry", "--ready-state"], capsys)
    assert code == 0
    assert err == ""
    for reason in RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS:
        assert reason in out


def test_json_output_is_deterministic_and_contains_safety_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, first, err = _run(["preview", "--ready-state", "--json"], capsys)
    assert code == 0
    assert err == ""
    code, second, err = _run(["preview", "--ready-state", "--json"], capsys)
    assert code == 0
    assert err == ""
    assert first == second

    payload = json.loads(first)
    assert payload["stdout_first"] is True
    assert payload["review_only"] is True
    assert payload["state_source_policy"]["file_io_performed"] is False
    assert payload["state_source_policy"]["reader_invocation_performed"] is False
    assert payload["state_source_policy"]["project_schema_mutated"] is False
    assert payload["summary"]["readiness"] == "ready_future_only"
    assert payload["non_action_flags"]["runtime_reload_acceptance_performed"] is False
    assert payload["non_action_flags"]["validation_pass_claimed"] is False
    assert payload["non_action_flags"]["validation_fail_claimed"] is False
    assert payload["non_action_flags"]["issue_closure_claimed"] is False
    assert payload["non_action_flags"]["release_mutated"] is False
    assert payload["non_action_flags"]["certification_claimed"] is False
    actions = {row["action"]: row for row in payload["disabled_future_actions"]}
    assert actions["accept_for_session_review"]["enabled"] is False
    assert actions["accept_for_session_review"]["future_only"] is True
    assert actions["validate_solver"]["enabled"] is False
    assert actions["execute_solver"]["enabled"] is False
    assert payload["exit_semantics"]["validation_success"] is False
    assert payload["exit_semantics"]["validation_failure"] is False
    assert payload["exit_semantics"]["runtime_acceptance"] is False


@pytest.mark.parametrize(
    ("flag", "expected"),
    [
        ("--sample-state", "OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED"),
        ("--not-requested-state", "OSPMG_RELOAD_ACCEPTANCE_NOT_REQUESTED"),
        ("--blocked-state", "OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED"),
        ("--ready-state", "OSPMG_RELOAD_ACCEPTANCE_READY"),
        ("--accepted-state", "OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW"),
    ],
)
def test_state_source_flags_render_expected_diagnostics(
    flag: str,
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["diagnostics", flag], capsys)
    assert code == 0
    assert err == ""
    assert expected in out


def test_accepted_state_is_session_review_scoped_and_untrusted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["preview", "--accepted-state"], capsys)
    assert code == 0
    assert err == ""
    assert "accepted_for_session_review=True" in out
    assert "scope=session_review_only" in out
    assert "untrusted_by_default=True" in out
    assert "persisted_state=False" in out
    assert "project_schema_state=False" in out
    assert "validation_evidence=False" in out
    assert "automatic_activation=False" in out
    assert "trust_restoration=False" in out


def test_accept_future_is_disabled_non_mutating_and_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["accept-future", "--ready-state"], capsys)
    assert code == 2
    assert out == ""
    assert "accept-future: disabled/future-only" in err
    assert "No acceptance mutation is implemented" in err
    assert "No runtime reload acceptance is performed" in err
    assert "No persistence write is performed" in err
    assert "No ProjectSchema mutation is performed" in err
    assert "Exit-code policy:" in err
    assert "validation failure" in err


def test_no_path_or_file_input_is_accepted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, "preview", "--path", "C:/Users/example/secret.json"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "unrecognized arguments: --path" in captured.err


def test_text_output_uses_redacted_sample_and_does_not_leak_secret_like_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["preview", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "sample-state.json" in out
    assert "C:\\" not in out
    assert "/home/" not in out
    assert "D:/dev/" not in out
    assert "api_key=secret" not in out
    assert "token=secret" not in out
    assert "full file content display" in out


def test_source_module_avoids_forbidden_imports_and_calls() -> None:
    forbidden_roots = {
        "pathlib",
        "os",
        "shutil",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "webbrowser",
        "pyside6",
        "pyqt6",
        "gmsh",
        "meshio",
        "pyvista",
        "cantera",
        "coolprop",
    }
    for imported in _imported_modules():
        root = imported.split(".", 1)[0]
        assert root not in forbidden_roots, imported
        assert not imported.startswith("osw.gui")
        assert "plugin_manifest_reload_file_reader" not in imported
        assert not imported.startswith("osw.plugins")
        assert not imported.startswith("osw.solvers")
        assert not imported.startswith("osw.core")
        assert not imported.startswith("osw.post")

    forbidden_calls = {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "glob",
        "iterdir",
        "walk",
        "run",
        "popen",
        "call",
        "check_call",
        "check_output",
        "urlopen",
        "discover_optional_solver_manifests",
        "discover_local_plugin_manifests",
        "load_optional_solver_plugin_manifest_json",
        "run_validation",
        "execute_solver",
        "startfile",
    }
    assert _called_names().isdisjoint(forbidden_calls)


def test_cli_creates_no_output_or_runtime_state_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    code, out, err = _run(["preview", "--ready-state"], capsys)
    assert code == 0
    assert err == ""
    assert "ready_future_only" in out
    assert list(tmp_path.iterdir()) == []
