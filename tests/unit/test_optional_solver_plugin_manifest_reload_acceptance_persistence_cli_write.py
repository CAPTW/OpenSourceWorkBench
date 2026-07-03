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

COMMAND = OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_PERSISTENCE_COMMAND
MODULE_NAME = "osw.cli.optional_solver_manifest_reload_acceptance_persistence"


def _run(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main([COMMAND, *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _module_source() -> str:
    module = importlib.import_module(MODULE_NAME)
    return Path(module.__file__).read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_module_source())


def _called_names() -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    return {call.lower() for call in calls}


def _imported_modules() -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {module.lower() for module in modules}


def test_write_subcommand_is_registered() -> None:
    parser = build_parser()
    parsed = parser.parse_args([COMMAND, "write", "--writer-ready-state"])
    assert parsed.command == COMMAND
    assert parsed.persistence_command == "write"


def test_write_requires_explicit_target_acknowledgement_and_confirmation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"

    code, out, err = _run(
        ["write", "--writer-ready-state", "--acknowledge-persistence-write"],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_TARGET_REQUIRED" in err
    assert target.exists() is False

    code, out, err = _run(
        ["write", "--writer-ready-state", "--target", str(target)],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_ACK_REQUIRED" in err
    assert target.exists() is False

    code, out, err = _run(
        [
            "write",
            "--writer-ready-state",
            "--target",
            str(target),
            "--acknowledge-persistence-write",
        ],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_CONFIRM_REQUIRED" in err
    assert target.exists() is False


def test_write_success_runs_dry_run_first_then_writes_local_review_record(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "reload-acceptance-state.json"
    code, out, err = _run(
        [
            "write",
            "--writer-ready-state",
            "--target",
            str(target),
            "--acknowledge-persistence-write",
            "--confirm-persistence-write",
            "--json",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert target.exists()
    assert str(target) not in out
    assert "reload-acceptance-state.json" in out

    payload = json.loads(out)
    assert payload["actual_cli_writes_enabled"] is True
    assert payload["dry_run_only"] is False
    assert payload["dry_run_first"] is True
    assert payload["dry_run_plan"]["status"] == "planned"
    assert payload["dry_run_plan"]["dry_run"] is True
    assert payload["dry_run_plan"]["written"] is False

    write_result = payload["write_result"]["writer_result"]
    assert write_result["status"] == "completed"
    assert write_result["dry_run"] is False
    assert write_result["written"] is True
    assert write_result["write_performed"] is True
    assert write_result["persistence_write_performed"] is True
    assert write_result["runtime_reload_acceptance_performed"] is False
    assert write_result["project_schema_mutated"] is False
    assert write_result["temp_file_used"] is True
    assert write_result["atomic_replace_performed"] is True

    flags = payload["non_action_flags"]
    assert flags["actual_cli_write_performed"] is True
    assert flags["writer_called_with_dry_run_false"] is True
    assert flags["persistence_write_performed"] is True
    for key in (
        "runtime_reload_acceptance_performed",
        "active_acceptance_mutation_performed",
        "project_schema_mutated",
        "directory_scan_performed",
        "network_fetch_performed",
        "plugin_package_imported",
        "cli_subprocess_used",
        "validation_executed",
        "solver_executed",
        "candidate_activated",
        "trust_restored",
        "issue_mutated",
        "release_mutated",
        "tag_mutated",
        "asset_mutated",
        "version_bumped",
        "validation_pass_claimed",
        "validation_fail_claimed",
        "issue_closure_claimed",
        "bundled_solver_claimed",
        "certification_claimed",
    ):
        assert flags[key] is False

    record = json.loads(target.read_text(encoding="utf-8"))
    assert record["summary"]["write_success_is_validation_success"] is False
    assert record["summary"]["write_success_is_validation_failure"] is False
    assert record["summary"]["persisted_review_record_is_runtime_acceptance"] is False
    assert record["summary"]["write_success_mutates_project_schema"] is False
    assert record["summary"]["write_success_closes_issue"] is False
    assert record["summary"]["write_success_mutates_release"] is False
    assert record["summary"]["write_success_is_certification"] is False


def test_write_text_output_states_local_only_safety_boundaries(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    code, out, err = _run(
        [
            "write",
            "--writer-ready-state",
            "--target",
            str(target),
            "--acknowledge-persistence-write",
            "--confirm-persistence-write",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert "Write:" in out
    assert "local review-record persistence only" in out
    for phrase in (
        "write success is not runtime acceptance",
        "write success is not validation success",
        "write success is not validation failure",
        "write success is not ProjectSchema mutation",
        "write success is not trust restoration",
        "write success is not automatic activation",
        "write success is not issue closure",
        "write success is not release mutation",
        "write success is not certification",
    ):
        assert phrase in out


def test_existing_target_blocks_unless_allow_replace_is_explicit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    target.write_text("original", encoding="utf-8")

    code, out, err = _run(
        [
            "write",
            "--writer-ready-state",
            "--target",
            str(target),
            "--acknowledge-persistence-write",
            "--confirm-persistence-write",
        ],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_EXISTS" in err
    assert target.read_text(encoding="utf-8") == "original"

    code, out, err = _run(
        [
            "write",
            "--writer-ready-state",
            "--target",
            str(target),
            "--allow-replace",
            "--acknowledge-persistence-write",
            "--confirm-persistence-write",
            "--json",
        ],
        capsys,
    )
    assert code == 0
    assert err == ""
    assert json.loads(out)["write_result"]["writer_result"]["status"] == "completed"
    assert json.loads(target.read_text(encoding="utf-8"))["payload_kind"]


def test_blocked_viewmodel_stops_after_dry_run_and_writes_no_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "blocked.json"
    code, out, err = _run(
        [
            "write",
            "--blocked-state",
            "--target",
            str(target),
            "--acknowledge-persistence-write",
            "--confirm-persistence-write",
        ],
        capsys,
    )
    assert code == 2
    assert out == ""
    assert "phase: dry_run" in err
    assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_BLOCKED" in err
    assert target.exists() is False


def test_writer_error_returns_one_without_runtime_side_effects(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    original = module.write_reload_acceptance_persistence_record
    calls: list[bool] = []

    def fake_writer(request: object) -> object:
        calls.append(bool(request.dry_run))
        if request.dry_run:
            return original(request)
        return {
            "status": "error",
            "target_display": "state.json",
            "target_redacted": True,
            "dry_run": False,
            "planned": False,
            "written": False,
            "bytes_count": 0,
            "sha256": "",
            "payload_kind": "",
            "payload_schema_version": "",
            "diagnostics": [
                {
                    "severity": "error",
                    "code": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_ERROR",
                    "message": "simulated writer failure",
                    "blocker": True,
                }
            ],
            "blockers": ["simulated writer failure"],
            "warnings": [],
            "non_action_flags": {
                "persistence_write_performed": False,
                "runtime_reload_acceptance_performed": False,
                "project_schema_mutated": False,
            },
            "payload": {},
            "write_performed": False,
            "persistence_write_performed": False,
            "runtime_reload_acceptance_performed": False,
            "project_schema_mutated": False,
        }

    monkeypatch.setattr(module, "write_reload_acceptance_persistence_record", fake_writer)
    target = tmp_path / "state.json"
    code, out, err = _run(
        [
            "write",
            "--writer-ready-state",
            "--target",
            str(target),
            "--acknowledge-persistence-write",
            "--confirm-persistence-write",
        ],
        capsys,
    )
    assert code == 1
    assert out == ""
    assert "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_ERROR" in err
    assert "simulated writer failure" in err
    assert target.exists() is False
    assert calls == [True, False]


def test_review_commands_and_write_future_still_create_no_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "state.json"
    for args in (
        ["preview", "--writer-ready-state"],
        ["plan", "--writer-ready-state", "--target", str(target)],
        ["write-future", "--writer-ready-state", "--target", str(target)],
    ):
        _run(args, capsys)
    assert list(tmp_path.iterdir()) == []


def test_no_path_option_is_accepted(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([COMMAND, "write", "--path", "state.json"])
    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "--path" in captured.err


def test_source_guardrails_allow_only_explicit_writer_write_path() -> None:
    source = _module_source()
    assert "write_reload_acceptance_persistence_record" in source
    assert "dry_run=True" in source
    assert "dry_run=False" in source
    assert source.index("dry_run=True") < source.index("dry_run=False")
    assert "read_optional_solver_plugin_manifest_reload_file" not in source
    assert "write_optional_solver_plugin_manifest_state" not in source
    assert "discover_optional_solver_manifests" not in source
    assert "validate_optional_solver_manifest" not in source
    assert "execute_solver" not in source
    assert _imported_modules().isdisjoint(
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
            "write_text",
            "write_bytes",
            "glob",
            "iterdir",
            "run",
            "popen",
            "read_optional_solver_plugin_manifest_reload_file",
            "write_optional_solver_plugin_manifest_state",
        }
    )

    request_calls = [
        node
        for node in ast.walk(_tree())
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", "") == "ReloadAcceptancePersistenceWriteRequest"
    ]
    dry_run_values = [
        keyword.value.value
        for call in request_calls
        for keyword in call.keywords
        if keyword.arg == "dry_run" and isinstance(keyword.value, ast.Constant)
    ]
    assert True in dry_run_values
    assert False in dry_run_values
