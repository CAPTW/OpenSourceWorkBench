from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

import pytest

from osw.cli.main import build_parser, main
from osw.cli.optional_solver_manifest_reload_acceptance_persistence import (
    OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_COMMAND,
)
from osw.experimental.optional_solvers import (
    RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS,
    RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
)

COMMAND = OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_COMMAND
MODULE_NAME = "osw.cli.optional_solver_manifest_reload_acceptance_persistence"
REPO_ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTATION_DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_cli_implementation.md"
)
DESIGN_DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md"
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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_non_claim_text(text: str) -> None:
    for phrase in (
        "Exit code 0 is not validation success.",
        "Exit code 0 is not validation failure.",
        "Exit code 0 is not runtime acceptance.",
        "Exit code 0 is not persistence write.",
        "Dry-run planning success is not ProjectSchema mutation.",
        "Dry-run planning success is not trust restoration.",
        "Dry-run planning success is not automatic activation.",
        "Trust labels are not certification.",
    ):
        assert phrase in text
    forbidden = (
        "validation_success: True",
        "validation_failure: True",
        "persistence_write_performed: True",
        "issue_closure: True",
        "release_mutation: True",
        "certification: True",
        "validation-pass evidence",
        "validation-fail evidence",
        "certified manifest",
    )
    for phrase in forbidden:
        assert phrase not in text


def test_module_imports_and_dispatcher_registration() -> None:
    module = importlib.import_module(MODULE_NAME)
    assert hasattr(
        module,
        "run_optional_solver_plugin_manifest_reload_acceptance_persistence_cli",
    )
    assert hasattr(
        module,
        "add_optional_solver_plugin_manifest_reload_acceptance_persistence_parser",
    )
    assert COMMAND in build_parser().format_help()


def test_implementation_docs_and_meta_entries_are_present() -> None:
    doc = _read(IMPLEMENTATION_DOC)
    normalised = " ".join(doc.lower().split())
    for phrase in (
        "Experimental reload acceptance persistence CLI implemented",
        "stdout-first",
        "dry-run planning only",
        "write-future disabled",
        "no actual CLI writes",
        "no input state-file reading",
        "no reload file-reader invocation",
        "no OSW-EXP-102 state-writer invocation",
        "Exit-Code Policy",
        "Relationship To OSW-EXP-126 Writer",
        "Relationship To Live Optional Validation Issues",
    ):
        assert phrase in doc or " ".join(phrase.lower().split()) in normalised
    assert "Implementation Follow-Up (OSW-EXP-128)" in _read(DESIGN_DOC)
    assert "ADR-0162" in _read(DECISION_LOG)
    assert "reload acceptance persistence CLI implementation" in _read(GUARDRAILS)
    assert "reload acceptance persistence CLI implementation" in _read(
        RISK_REGISTER
    )
    assert "automated CLI implementation evidence" in _read(VALIDATION_MATRIX)
    assert "reload acceptance persistence CLI implementation" in _read(
        RELEASE_CHECKLIST
    )
    assert "Acceptance Persistence CLI Implementation" in _read(CHANGELOG)


def test_default_preview_is_unavailable_and_non_mutating(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["preview"], capsys)
    assert code == 0
    assert err == ""
    assert "unavailable in-memory state; no input file is read" in out
    assert "state: no_acceptance_viewmodel" in out
    assert "readiness: acceptance_missing" in out
    assert "no actual CLI writes" in out
    assert "no input state-file reading" in out
    assert "no reload file-reader invocation" in out
    _assert_non_claim_text(out)


def test_explain_renders_purpose_and_non_actions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["explain", "--sample-state"], capsys)
    assert code == 0
    assert err == ""
    assert "Definition:" in out
    assert "plan command calls the writer only with dry_run=True" in out
    for phrase in (
        "Persistence CLI performs no actual CLI writes.",
        "Persistence CLI reads no input state files.",
        "Persistence CLI parses no input state files.",
        "Persistence CLI invokes no reload file reader.",
        "Persistence CLI invokes no OSW-EXP-102 state writer.",
        "Persistence CLI calls no GUI code.",
        "Persistence CLI uses no subprocesses.",
        "Persistence CLI mutates no ProjectSchema.",
        "Persistence CLI executes no validation.",
        "Persistence CLI executes no solver.",
        "Persistence CLI claims no certification.",
    ):
        assert phrase in out


def test_plan_without_target_renders_target_required_without_write(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["plan", "--writer-ready-state"], capsys)
    assert code == 0
    assert err == ""
    assert "Dry-run/write-plan:" in out
    assert "writer_dry_run: True" in out
    assert "writer_written: False" in out
    assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_REQUIRED" in out
    assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_TARGET_REQUIRED" in out
    _assert_non_claim_text(out)


def test_plan_with_target_calls_writer_dry_run_and_creates_no_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "reload-acceptance-state.json"
    code, out, err = _run(
        ["plan", "--writer-ready-state", "--target", str(target)],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert target.exists() is False
    assert "writer_status: planned" in out
    assert "writer_dry_run: True" in out
    assert "writer_planned: True" in out
    assert "writer_written: False" in out
    assert "writer_write_performed: False" in out
    assert "reload-acceptance-state.json" in out
    assert str(target) not in out
    _assert_non_claim_text(out)


def test_plan_json_is_deterministic_and_non_mutating(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    args = ["plan", "--writer-ready-state", "--target", str(target), "--json"]
    code, first, err = _run(args, capsys)
    assert code == 0
    assert err == ""
    code, second, err = _run(args, capsys)
    assert code == 0
    assert err == ""
    assert first == second
    assert target.exists() is False

    payload = json.loads(first)
    assert payload["stdout_first"] is True
    assert payload["dry_run_only"] is True
    assert payload["actual_cli_writes_enabled"] is False
    assert payload["writer_plan_result"]["dry_run"] is True
    assert payload["writer_plan_result"]["planned"] is True
    assert payload["writer_plan_result"]["written"] is False
    assert payload["writer_plan_result"]["write_performed"] is False
    flags = payload["non_action_flags"]
    assert flags["actual_cli_write_performed"] is False
    assert flags["writer_called_with_dry_run_false"] is False
    assert flags["input_state_file_read"] is False
    assert flags["input_state_file_parsed"] is False
    assert flags["reload_file_reader_invoked"] is False
    assert flags["state_writer_invoked"] is False
    assert flags["persistence_write_performed"] is False
    assert flags["project_schema_mutated"] is False
    assert payload["exit_semantics"]["validation_success"] is False
    assert payload["exit_semantics"]["validation_failure"] is False
    assert payload["exit_semantics"]["runtime_acceptance"] is False
    assert payload["exit_semantics"]["persistence_write"] is False
    actions = {row["action"]: row for row in payload["disabled_future_actions"]}
    assert actions["write_acceptance_review_record"]["enabled"] is False
    assert actions["plan_persistence_write"]["enabled"] is True
    assert actions["mutate_project_schema"]["enabled"] is False
    assert actions["validate_solver"]["enabled"] is False
    assert actions["execute_solver"]["enabled"] is False


@pytest.mark.parametrize(
    ("subcommand", "expected"),
    [
        ("diagnostics", "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_"),
        ("acknowledgements", "Acknowledgements:"),
        ("expiry", "Acknowledgement expiry:"),
        ("storage", "Storage/target policy:"),
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
    _assert_non_claim_text(out)


def test_acknowledgements_and_expiry_ids_are_visible(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = _run(["acknowledgements", "--ready-state"], capsys)
    assert code == 0
    assert err == ""
    for ack_id in RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS:
        assert ack_id in out
    assert "acknowledgement_is_validation_evidence=False" in out
    assert "acknowledgement_restores_trust=False" in out

    code, out, err = _run(["expiry", "--ready-state"], capsys)
    assert code == 0
    assert err == ""
    for reason in RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS:
        assert reason in out


def test_state_source_flags_render_expected_diagnostics(
    capsys: pytest.CaptureFixture[str],
) -> None:
    expectations = {
        "--sample-state": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED",
        "--blocked-state": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED",
        "--ready-state": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY",
        "--writer-ready-state": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY",
    }
    for flag, expected in expectations.items():
        code, out, err = _run(["diagnostics", flag], capsys)
        assert code == 0
        assert err == ""
        assert expected in out


def test_write_future_returns_two_and_creates_no_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    code, out, err = _run(
        ["write-future", "--writer-ready-state", "--target", str(target)],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "Write-future:" in err
    assert "status: disabled/future-only" in err
    assert "no file is created" in err
    assert target.exists() is False


def test_target_text_is_redacted_and_secret_like_values_do_not_leak(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "secret-token-state.json"
    code, out, err = _run(
        ["plan", "--writer-ready-state", "--target", str(target)],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert target.exists() is False
    assert str(target) not in out
    assert "secret-token-state" not in out
    assert "<redacted-secret-like-value>" in out

    payload = _json(
        ["plan", "--writer-ready-state", "--target", str(target)],
        capsys,
    )
    serialized = json.dumps(payload, sort_keys=True)
    assert str(target) not in serialized
    assert "secret-token-state" not in serialized


def test_no_path_option_is_accepted(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([COMMAND, "plan", "--path", "state.json"])
    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "--path" in captured.err


def test_source_guardrails_forbidden_imports_calls_and_writer_mode() -> None:
    source = _module_source()
    assert "write_reload_acceptance_persistence_record" not in source
    assert "dry_run=False" not in source
    assert "dry_run = False" not in source
    assert "dry_run=True" in source

    imports = _imported_modules() - {"__future__"}
    assert imports.isdisjoint(
        {
            "os",
            "subprocess",
            "socket",
            "requests",
            "urllib",
            "pyside6",
            "osw.gui",
            "osw.core.project_schema",
            "osw.plugins",
            "osw.solvers",
            "plugin_manifest_reload_file_reader",
            "plugin_manifest_state_writer",
        }
    )
    assert _called_names().isdisjoint(
        {
            "open",
            "read",
            "read_text",
            "read_bytes",
            "write",
            "write_text",
            "write_bytes",
            "glob",
            "iterdir",
            "run",
            "popen",
            "discover_optional_solver_manifests",
            "validate_optional_solver_manifest",
            "execute_solver",
            "read_optional_solver_plugin_manifest_reload_file",
            "write_optional_solver_plugin_manifest_state",
        }
    )

    tree = _tree()
    request_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", "") == "ReloadAcceptancePersistenceWriteRequest"
    ]
    assert request_calls
    for call in request_calls:
        dry_run_keyword = next(
            keyword for keyword in call.keywords if keyword.arg == "dry_run"
        )
        assert isinstance(dry_run_keyword.value, ast.Constant)
        assert dry_run_keyword.value.value is True


def test_no_output_or_runtime_state_files_created_by_review_commands(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    before = sorted(path.name for path in tmp_path.iterdir())
    assert before == []
    for args in (
        ["preview", "--writer-ready-state"],
        ["plan", "--writer-ready-state", "--target", str(target)],
        ["write-future", "--writer-ready-state", "--target", str(target)],
    ):
        _run(args, capsys)
    after = sorted(path.name for path in tmp_path.iterdir())
    assert after == []
