from __future__ import annotations

import ast
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from osw.experimental.optional_solvers import (
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ATOMIC_REPLACE_FAILED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CALLER_ACK_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_MISSING,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_NOT_DIRECTORY,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_SECRET_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_UNREDACTED_PATH_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_MISMATCH,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_DIRECTORY_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_EXISTS,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_SYMLINK_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PLANNED,
    RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PAYLOAD_KIND,
    RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_SCHEMA_VERSION,
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
    OptionalSolverPluginManifestReloadAcceptancePersistenceWriter,
    OptionalSolverPluginManifestReloadAcceptanceViewModel,
    OptionalSolverPluginManifestReloadViewModel,
    ReloadAcceptancePersistenceWritePathPolicy,
    ReloadAcceptancePersistenceWriteRequest,
    ReloadAcceptancePersistenceWriteResult,
    ReloadAcceptancePersistenceWriteStatus,
    build_reload_acceptance_persistence_write_payload,
    plan_reload_acceptance_persistence_write,
    write_reload_acceptance_persistence_record,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_reload_acceptance_persistence_writer as module_under_test,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "osw" / "experimental" / "optional_solvers" / (
    "plugin_manifest_reload_acceptance_persistence_writer.py"
)


def _ready_acceptance() -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    return OptionalSolverPluginManifestReloadAcceptanceViewModel.ready_for_future_acceptance(
        OptionalSolverPluginManifestReloadViewModel.sample_ready_for_review()
    )


def _ready_vm() -> (
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel
):
    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.ready_for_future_writer(
            _ready_acceptance()
        )
    )


def _blocked_vm() -> (
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel
):
    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.from_acceptance_viewmodel(
            _ready_acceptance(),
            persistence_requested=True,
        )
    )


def _request(path: Path | None, **kwargs) -> ReloadAcceptancePersistenceWriteRequest:
    return ReloadAcceptancePersistenceWriteRequest(
        persistence_viewmodel=_ready_vm(),
        target_path=path,
        **kwargs,
    )


def _write_request(path: Path, **kwargs) -> ReloadAcceptancePersistenceWriteRequest:
    return _request(
        path,
        dry_run=False,
        caller_acknowledged_persistence_write=True,
        **kwargs,
    )


def _codes(result: ReloadAcceptancePersistenceWriteResult) -> set[str]:
    return {row.code for row in result.diagnostics}


def _source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _imports() -> set[str]:
    tree = ast.parse(_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {module.lower() for module in modules}


def _called_names() -> set[str]:
    tree = ast.parse(_source())
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    return {call.lower() for call in calls}


def test_module_imports_and_package_exports() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers."
        "plugin_manifest_reload_acceptance_persistence_writer"
    )
    assert hasattr(module, "OptionalSolverPluginManifestReloadAcceptancePersistenceWriter")
    assert hasattr(module, "ReloadAcceptancePersistenceWriteRequest")
    assert hasattr(module, "ReloadAcceptancePersistenceWriteResult")
    assert hasattr(module, "ReloadAcceptancePersistenceWriteStatus")
    assert hasattr(module, "ReloadAcceptancePersistenceWritePathPolicy")
    assert ReloadAcceptancePersistenceWritePathPolicy().default_path_used is False


def test_request_defaults_to_dry_run() -> None:
    request = ReloadAcceptancePersistenceWriteRequest(
        persistence_viewmodel=_ready_vm(),
        target_path="state.json",
    )
    assert request.dry_run is True
    assert request.allow_replace is False
    assert request.caller_acknowledged_persistence_write is False


def test_missing_target_path_blocks_without_write() -> None:
    result = OptionalSolverPluginManifestReloadAcceptancePersistenceWriter().write(
        _request(None)
    )
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_REQUIRED in _codes(result)
    assert result.write_performed is False


def test_directory_target_blocks(tmp_path: Path) -> None:
    result = write_reload_acceptance_persistence_record(_write_request(tmp_path))
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_DIRECTORY_BLOCKED in _codes(result)


def test_symlink_target_blocks_if_platform_allows_symlink(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    backing = tmp_path / "backing.json"
    backing.write_text("existing\n", encoding="utf-8")
    try:
        target.symlink_to(backing)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    result = write_reload_acceptance_persistence_record(_write_request(target))
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_SYMLINK_BLOCKED in _codes(result)


def test_missing_parent_blocks_and_does_not_create_directory(tmp_path: Path) -> None:
    target = tmp_path / "missing" / "state.json"
    result = write_reload_acceptance_persistence_record(_write_request(target))
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_MISSING in _codes(result)
    assert target.exists() is False
    assert target.parent.exists() is False


def test_parent_not_directory_blocks(tmp_path: Path) -> None:
    parent = tmp_path / "parent-file"
    parent.write_text("not a directory\n", encoding="utf-8")
    target = parent / "state.json"
    result = write_reload_acceptance_persistence_record(_write_request(target))
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PARENT_NOT_DIRECTORY in _codes(result)


def test_existing_target_blocks_unless_allow_replace(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_text("existing\n", encoding="utf-8")
    result = write_reload_acceptance_persistence_record(_write_request(target))
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TARGET_EXISTS in _codes(result)
    assert target.read_text(encoding="utf-8") == "existing\n"


def test_dry_run_with_valid_target_plans_payload_but_creates_no_file(
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    result = write_reload_acceptance_persistence_record(_request(target))
    assert result.status == ReloadAcceptancePersistenceWriteStatus.PLANNED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PLANNED in _codes(result)
    assert result.bytes_count > 0
    assert result.sha256
    assert target.exists() is False
    assert result.write_performed is False
    assert result.persistence_write_performed is False


def test_dry_run_hash_is_deterministic(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    first = plan_reload_acceptance_persistence_write(_request(target))
    second = plan_reload_acceptance_persistence_write(_request(target))
    assert first.sha256 == second.sha256
    assert first.bytes_count == second.bytes_count


def test_actual_write_without_caller_acknowledgement_blocks(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    request = _request(target, dry_run=False)
    result = write_reload_acceptance_persistence_record(request)
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CALLER_ACK_REQUIRED in _codes(result)
    assert target.exists() is False


def test_actual_write_with_acknowledgement_writes_deterministic_json(
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    request = _write_request(target)
    result = write_reload_acceptance_persistence_record(request)
    assert result.status == ReloadAcceptancePersistenceWriteStatus.COMPLETED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_COMPLETED in _codes(result)
    assert target.exists() is True
    text = target.read_text(encoding="utf-8")
    payload = json.loads(text)
    assert payload["payload_kind"] == RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_PAYLOAD_KIND
    assert payload["payload_schema_version"] == (
        RELOAD_ACCEPTANCE_PERSISTENCE_WRITE_SCHEMA_VERSION
    )
    assert text.endswith("\n")
    assert result.sha256 == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert result.bytes_count == len(text.encode("utf-8"))
    assert result.write_performed is True
    assert result.persistence_write_performed is True
    assert result.atomic_replace_performed is True
    assert result.runtime_reload_acceptance_performed is False
    assert result.project_schema_mutated is False


def test_actual_write_leaves_no_temp_file_on_success(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    result = write_reload_acceptance_persistence_record(_write_request(target))
    assert result.status == ReloadAcceptancePersistenceWriteStatus.COMPLETED
    assert list(tmp_path.glob("*.tmp")) == []
    assert list(tmp_path.glob(".state.json.*.tmp")) == []


def test_write_failure_attempts_temp_cleanup(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "state.json"

    def fail_replace(_src, _dst) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(module_under_test.os, "replace", fail_replace)
    result = write_reload_acceptance_persistence_record(_write_request(target))
    assert result.status == ReloadAcceptancePersistenceWriteStatus.ERROR
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ATOMIC_REPLACE_FAILED in _codes(result)
    assert result.cleanup_performed is True
    assert result.temp_file_left_behind is False
    assert target.exists() is False
    assert list(tmp_path.glob(".state.json.*.tmp")) == []


def test_allow_replace_replaces_existing_target_only_when_explicit(
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    target.write_text("existing\n", encoding="utf-8")
    blocked = write_reload_acceptance_persistence_record(_write_request(target))
    assert blocked.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    replaced = write_reload_acceptance_persistence_record(
        _write_request(target, allow_replace=True)
    )
    assert replaced.status == ReloadAcceptancePersistenceWriteStatus.COMPLETED
    assert target.read_text(encoding="utf-8") != "existing\n"


def test_blocked_persistence_viewmodel_prevents_actual_write(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    request = ReloadAcceptancePersistenceWriteRequest(
        persistence_viewmodel=_blocked_vm(),
        target_path=target,
        dry_run=False,
        caller_acknowledged_persistence_write=True,
    )
    result = write_reload_acceptance_persistence_record(request)
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_BLOCKED in _codes(result)
    assert target.exists() is False


def test_missing_acknowledgements_block_actual_write(tmp_path: Path) -> None:
    result = write_reload_acceptance_persistence_record(
        ReloadAcceptancePersistenceWriteRequest(
            persistence_viewmodel=_blocked_vm(),
            target_path=tmp_path / "state.json",
            dry_run=False,
            caller_acknowledged_persistence_write=True,
        )
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_BLOCKED in _codes(result)


@pytest.mark.parametrize(
    "policy_flag",
    [
        "stale_source_requires_repreview",
        "conflict_review_required",
        "unsafe_claim_blocked",
        "unsupported_schema",
        "unredacted_path_blocked",
    ],
)
def test_policy_blockers_prevent_actual_write(tmp_path: Path, policy_flag: str) -> None:
    vm = OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.from_acceptance_viewmodel(
        _ready_acceptance(),
        persistence_requested=True,
        acknowledged=tuple(
            row.acknowledgement_id for row in _ready_vm().acknowledgement_rows
        ),
        storage_policy_id="explicit",
        target_display="state.json",
        dry_run_confirmed=True,
        policy_flags={policy_flag: True},
    )
    result = write_reload_acceptance_persistence_record(
        ReloadAcceptancePersistenceWriteRequest(
            persistence_viewmodel=vm,
            target_path=tmp_path / "state.json",
            dry_run=False,
            caller_acknowledged_persistence_write=True,
        )
    )
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED


def test_payload_contains_required_sections(tmp_path: Path) -> None:
    payload = build_reload_acceptance_persistence_write_payload(
        _request(tmp_path / "state.json")
    )
    for key in (
        "payload_kind",
        "payload_schema_version",
        "summary",
        "storage",
        "write_plan",
        "acceptance_persistence",
        "acknowledgements",
        "expiry",
        "provenance",
        "schema",
        "redaction_privacy",
        "candidate_lifecycle",
        "stale_sources",
        "conflicts",
        "unsafe_claims",
        "evidence_history",
        "diagnostics",
        "non_action_flags",
        "disabled_future_actions",
        "safety_guidance",
    ):
        assert key in payload


def test_payload_and_text_safety_claims(tmp_path: Path) -> None:
    result = write_reload_acceptance_persistence_record(_request(tmp_path / "state.json"))
    combined = "\n".join(result.to_text_lines()).lower()
    payload = json.dumps(result.to_mapping(), sort_keys=True).lower()
    for phrase in (
        "not runtime acceptance",
        "not validation success",
        "not validation failure",
        "not projectschema mutation",
        "not trust restoration",
        "not automatic activation",
        "not issue closure",
        "not release mutation",
        "not certification",
    ):
        assert phrase in combined or phrase in payload


def test_raw_absolute_paths_are_not_leaked_in_result_text(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "state.json"
    target.parent.mkdir()
    result = write_reload_acceptance_persistence_record(_request(target))
    text = "\n".join(result.to_text_lines())
    assert str(tmp_path) not in text
    assert "state.json" in text


def test_secret_like_values_are_blocked_and_not_leaked_in_text(tmp_path: Path) -> None:
    mapping = _ready_vm().to_mapping()
    mapping["summary"]["secret_token"] = "token=abc123"
    result = write_reload_acceptance_persistence_record(
        ReloadAcceptancePersistenceWriteRequest(
            persistence_viewmodel=mapping,
            target_path=tmp_path / "state.json",
            dry_run=False,
            caller_acknowledged_persistence_write=True,
        )
    )
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_SECRET_BLOCKED in _codes(result)
    assert "token=abc123" not in "\n".join(result.to_text_lines())


def test_unredacted_path_values_are_blocked_and_not_leaked_in_text(tmp_path: Path) -> None:
    mapping = _ready_vm().to_mapping()
    mapping["summary"]["raw_path"] = "C:/Users/USER/private/state.json"
    result = write_reload_acceptance_persistence_record(
        ReloadAcceptancePersistenceWriteRequest(
            persistence_viewmodel=mapping,
            target_path=tmp_path / "state.json",
            dry_run=False,
            caller_acknowledged_persistence_write=True,
        )
    )
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_UNREDACTED_PATH_BLOCKED in (
        _codes(result)
    )
    assert "C:/Users/USER" not in "\n".join(result.to_text_lines())


def test_non_action_flags_remain_false_except_completed_review_record_write(
    tmp_path: Path,
) -> None:
    dry_run = write_reload_acceptance_persistence_record(_request(tmp_path / "a.json"))
    assert all(value is False for value in dry_run.non_action_flags.values())
    completed = write_reload_acceptance_persistence_record(
        _write_request(tmp_path / "b.json")
    )
    assert completed.non_action_flags["persistence_write_performed"] is True
    for key, value in completed.non_action_flags.items():
        if key != "persistence_write_performed":
            assert value is False, key


def test_schema_expectation_mismatch_blocks(tmp_path: Path) -> None:
    result = write_reload_acceptance_persistence_record(
        _write_request(
            tmp_path / "state.json",
            expected_schema_version="wrong",
        )
    )
    assert result.status == ReloadAcceptancePersistenceWriteStatus.BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_MISMATCH in _codes(result)


def test_source_imports_avoid_forbidden_runtime_boundaries() -> None:
    imports = _imports()
    forbidden = {
        "argparse",
        "click",
        "typer",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "osw.cli",
        "osw.gui",
        "osw.core",
        "osw.plugins",
        "osw.solvers",
        "plugin_manifest_reload_file_reader",
        "plugin_manifest_state_writer",
    }
    assert imports.isdisjoint(forbidden)
    assert not any("pyside" in module or "pyqt" in module for module in imports)


def test_source_does_not_scan_create_parents_read_inputs_or_call_runtime() -> None:
    calls = _called_names()
    assert calls.isdisjoint(
        {
            "glob",
            "iterdir",
            "listdir",
            "walk",
            "mkdir",
            "makedirs",
            "read_text",
            "read_bytes",
            "read",
            "run",
            "popen",
            "read_optional_solver_plugin_manifest_reload_file",
            "write_optional_solver_plugin_manifest_state",
            "discover_optional_solver_manifests",
            "validate_optional_solver_manifest",
            "execute_solver",
        }
    )


def test_no_output_files_are_created_by_dry_run(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())
    result = write_reload_acceptance_persistence_record(_request(tmp_path / "state.json"))
    after = set(tmp_path.iterdir())
    assert result.status == ReloadAcceptancePersistenceWriteStatus.PLANNED
    assert after == before


def test_no_runtime_export_report_or_bundle_files_are_created_by_dry_run(
    tmp_path: Path,
) -> None:
    write_reload_acceptance_persistence_record(_request(tmp_path / "state.json"))
    assert list(tmp_path.rglob("*")) == []
