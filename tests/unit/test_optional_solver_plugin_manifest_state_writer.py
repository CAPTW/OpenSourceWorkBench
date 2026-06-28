from __future__ import annotations

import ast
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from osw.experimental.optional_solvers import (
    OSPMG_STATE_WRITER_CALLER_ACK_REQUIRED,
    OSPMG_STATE_WRITER_PARENT_MISSING,
    OSPMG_STATE_WRITER_PAYLOAD_SECRET_BLOCKED,
    OSPMG_STATE_WRITER_SCHEMA_VERSION_MISMATCH,
    OSPMG_STATE_WRITER_SERIALIZATION_ERROR,
    OSPMG_STATE_WRITER_TARGET_DIRECTORY_BLOCKED,
    OSPMG_STATE_WRITER_TARGET_EXISTS,
    OSPMG_STATE_WRITER_TARGET_REQUIRED,
    OSPMG_STATE_WRITER_TARGET_SYMLINK_BLOCKED,
    OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
    OSPMG_STATE_WRITER_WRITE_BLOCKED,
    OSPMG_STATE_WRITER_WRITE_COMPLETED,
    OSPMG_STATE_WRITER_WRITE_PLANNED,
    STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
    STATE_WRITER_REQUIRED_ACKS,
    OptionalSolverPluginManifestStateWriter,
    OptionalSolverPluginManifestStateWriterRequest,
    OptionalSolverPluginManifestStateWriterStatus,
    OptionalSolverPluginManifestStateWriterViewModel,
    build_optional_solver_plugin_manifest_state_writer_payload,
    plan_optional_solver_plugin_manifest_state_write,
    write_optional_solver_plugin_manifest_state,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_state_writer as module_under_test,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_state_writer_implementation.md"
)


def _all_acks() -> dict[str, bool]:
    return {ack: True for ack in STATE_WRITER_REQUIRED_ACKS}


def _writer() -> OptionalSolverPluginManifestStateWriter:
    return OptionalSolverPluginManifestStateWriter()


def _ready_vm() -> OptionalSolverPluginManifestStateWriterViewModel:
    return OptionalSolverPluginManifestStateWriterViewModel.ready_for_future_write()


def _write_request(path: Path, **kwargs) -> OptionalSolverPluginManifestStateWriterRequest:
    return OptionalSolverPluginManifestStateWriterRequest(
        target_path=path,
        dry_run=False,
        caller_acknowledged_write=True,
        **kwargs,
    )


def _codes(result) -> set[str]:
    return {row.code for row in result.diagnostics}


def _module_source() -> str:
    return Path(module_under_test.__file__).read_text(encoding="utf-8")


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


def _flatten(value) -> list[object]:
    if isinstance(value, dict):
        flattened: list[object] = []
        for item in value.values():
            flattened.extend(_flatten(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten(item))
        return flattened
    return [value]


def test_module_imports_without_gui_or_cli_extras() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers.plugin_manifest_state_writer"
    )
    assert hasattr(module, "OptionalSolverPluginManifestStateWriter")
    assert hasattr(module, "OptionalSolverPluginManifestStateWriterRequest")
    assert hasattr(module, "OptionalSolverPluginManifestStateWriterResult")
    assert hasattr(module, "OptionalSolverPluginManifestStateWriterStatus")
    assert hasattr(module, "OptionalSolverPluginManifestStateWriterDiagnostic")


def test_module_imports_are_local_writer_only() -> None:
    imports = _imported_modules()
    forbidden_roots = {
        "argparse",
        "click",
        "typer",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "shutil",
        "gmsh",
        "meshio",
        "pyvista",
        "vtk",
        "coolprop",
        "cantera",
    }
    for module in imports:
        root = module.split(".", 1)[0]
        assert root not in forbidden_roots, module
        assert "pyside" not in module
        assert "pyqt" not in module
        assert not module.startswith("qt")
    assert "osw.core" not in imports
    assert "osw.cli" not in imports
    assert "osw.gui" not in imports
    assert "osw.plugins" not in imports
    assert "osw.solvers" not in imports


def test_module_source_avoids_discovery_solver_network_release_and_cli_paths() -> None:
    source = _module_source()
    for phrase in (
        "QProcess",
        "subprocess",
        "os.system",
        "argparse",
        "click.",
        "typer.",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
        "load_optional_solver_plugin_manifest_json",
        "pip install",
        "pip uninstall",
        "conda remove",
        "gh issue",
        "gh release",
        "requests.",
        "urllib",
        "socket.",
        "run_discovery(",
        "run_validation(",
        "execute_solver(",
    ):
        assert phrase not in source, phrase


def test_dry_run_with_ready_view_model_plans_without_writing(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    request = OptionalSolverPluginManifestStateWriterRequest(target_path=target)
    result = _writer().write_state(_ready_vm(), request)
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.DRY_RUN_PLANNED
    assert target.exists() is False
    assert result.bytes_planned > 0
    assert result.bytes_written == 0
    assert result.sha256
    assert OSPMG_STATE_WRITER_WRITE_PLANNED in _codes(result)
    assert result.write_performed is False
    assert result.file_write_performed is False


def test_plan_write_function_returns_same_deterministic_hash(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    request = OptionalSolverPluginManifestStateWriterRequest(target_path=target)
    first = plan_optional_solver_plugin_manifest_state_write(_ready_vm(), request)
    second = plan_optional_solver_plugin_manifest_state_write(_ready_vm(), request)
    assert first.status == OptionalSolverPluginManifestStateWriterStatus.DRY_RUN_PLANNED
    assert first.sha256 == second.sha256
    assert first.bytes_planned == second.bytes_planned


def test_write_without_caller_acknowledgement_is_blocked(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    request = OptionalSolverPluginManifestStateWriterRequest(
        target_path=target,
        dry_run=False,
        caller_acknowledged_write=False,
    )
    result = _writer().write_state(_ready_vm(), request)
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert OSPMG_STATE_WRITER_CALLER_ACK_REQUIRED in _codes(result)
    assert target.exists() is False


def test_missing_target_path_is_unavailable_and_writes_nothing() -> None:
    request = OptionalSolverPluginManifestStateWriterRequest(target_path=None)
    result = _writer().write_state(_ready_vm(), request)
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.UNAVAILABLE
    assert OSPMG_STATE_WRITER_TARGET_REQUIRED in _codes(result)
    assert result.write_performed is False


def test_directory_target_is_blocked(tmp_path: Path) -> None:
    result = _writer().write_state(_ready_vm(), _write_request(tmp_path))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert OSPMG_STATE_WRITER_TARGET_DIRECTORY_BLOCKED in _codes(result)


def test_missing_parent_is_blocked_and_directory_is_not_created(tmp_path: Path) -> None:
    missing_parent = tmp_path / "missing" / "state.json"
    result = _writer().write_state(_ready_vm(), _write_request(missing_parent))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert OSPMG_STATE_WRITER_PARENT_MISSING in _codes(result)
    assert missing_parent.parent.exists() is False
    assert missing_parent.exists() is False


def test_existing_target_without_allow_replace_is_blocked(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_text("existing\n", encoding="utf-8")
    result = _writer().write_state(_ready_vm(), _write_request(target))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert OSPMG_STATE_WRITER_TARGET_EXISTS in _codes(result)
    assert target.read_text(encoding="utf-8") == "existing\n"


def test_existing_target_with_allow_replace_succeeds(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_text("existing\n", encoding="utf-8")
    result = _writer().write_state(
        _ready_vm(),
        _write_request(target, allow_replace=True),
    )
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.WRITTEN
    assert OSPMG_STATE_WRITER_WRITE_COMPLETED in _codes(result)
    assert target.read_text(encoding="utf-8") != "existing\n"
    assert json.loads(target.read_text(encoding="utf-8"))["payload_kind"] == (
        "optional_solver_plugin_manifest_state_writer_state"
    )


def test_symlink_target_is_blocked_if_platform_allows_symlink(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    backing = tmp_path / "backing.json"
    backing.write_text("existing\n", encoding="utf-8")
    try:
        target.symlink_to(backing)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable: {exc}")
    result = _writer().write_state(_ready_vm(), _write_request(target, allow_replace=True))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert OSPMG_STATE_WRITER_TARGET_SYMLINK_BLOCKED in _codes(result)
    assert backing.read_text(encoding="utf-8") == "existing\n"


def test_successful_write_creates_only_target_json_with_trailing_newline(
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    result = write_optional_solver_plugin_manifest_state(
        _ready_vm(),
        _write_request(target),
    )
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.WRITTEN
    assert sorted(path.name for path in tmp_path.iterdir()) == ["state.json"]
    raw = target.read_bytes()
    assert raw.endswith(b"\n")
    payload = json.loads(raw.decode("utf-8"))
    assert payload["payload_schema_version"] == STATE_WRITER_PAYLOAD_SCHEMA_VERSION
    assert result.bytes_written == len(raw)
    assert result.sha256 == hashlib.sha256(raw).hexdigest()
    assert result.temp_file_used is True
    assert result.atomic_replace_performed is True


def test_serialization_is_stable_sorted_and_deterministic() -> None:
    payload = build_optional_solver_plugin_manifest_state_writer_payload(_ready_vm())
    writer = _writer()
    first = writer.serialize_payload(payload)
    second = writer.serialize_payload(payload)
    assert first == second
    decoded = first.decode("utf-8")
    assert decoded.endswith("\n")
    assert decoded.index('"acknowledgements"') < decoded.index('"atomicity_error')
    assert json.loads(decoded) == json.loads(second.decode("utf-8"))


def test_serialization_failure_leaves_no_target_file(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    bad_payload = {
        "payload_kind": "optional_solver_plugin_manifest_state_writer_state",
        "bad": object(),
    }
    result = _writer().write_state(bad_payload, _write_request(target))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.ERROR
    assert OSPMG_STATE_WRITER_SERIALIZATION_ERROR in _codes(result)
    assert target.exists() is False


def test_temp_file_is_cleaned_up_when_atomic_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"

    def fail_replace(_source, _target) -> None:
        raise PermissionError("simulated replace failure")

    monkeypatch.setattr(module_under_test.os, "replace", fail_replace)
    result = _writer().write_state(_ready_vm(), _write_request(target))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.ERROR
    assert target.exists() is False
    assert list(tmp_path.iterdir()) == []


def test_payload_contains_required_sections_and_safety_boundaries() -> None:
    payload = build_optional_solver_plugin_manifest_state_writer_payload(_ready_vm())
    for key in (
        "payload_kind",
        "payload_schema_version",
        "writer_version",
        "generated_by",
        "state_scope",
        "header",
        "summary",
        "storage_options",
        "write_plan",
        "file_format",
        "schema_boundary",
        "sources",
        "provenance",
        "candidates",
        "acknowledgements",
        "redaction_privacy",
        "schema_migration",
        "stale_sources",
        "conflicts",
        "unsafe_claims",
        "evidence_history",
        "atomicity_error_handling_plan",
        "diagnostics",
        "limitations",
        "non_action_flags",
        "action_states",
        "migration_notes",
        "safety_boundary",
    ):
        assert key in payload, key
    assert payload["summary"]["not_validation_evidence"] is True
    assert payload["header"]["default_write_path_selected"] is False
    assert payload["non_action_flags"]["project_schema_mutation_performed"] is False


def test_payload_preserves_trust_redaction_acknowledgement_history_and_claim_safety() -> None:
    vm = OptionalSolverPluginManifestStateWriterViewModel.from_records(
        sources=(
            {
                "source_id": "s1",
                "source_reference_display": "plugin.json",
                "trust_label": "untrusted_user_file",
            },
        ),
        candidates=(
            {
                "stack_id": "gmsh",
                "source_id": "s1",
                "trust_label": "untrusted_user_file",
                "validation_evidence_state": "skipped_missing",
            },
        ),
        acknowledgements=_all_acks(),
        evidence_history=(module_under_test.OptionalSolverPluginManifestStateWriterViewModel.ready_for_future_write().evidence_history_rows),
    )
    payload = build_optional_solver_plugin_manifest_state_writer_payload(vm)
    flattened = _flatten(payload)
    assert "untrusted_user_file" in flattened
    assert "Persisted state is not validation evidence." in flattened
    assert "Persisted state is not trust restoration." in flattened
    assert "Persisted state is not automatic activation." in flattened
    assert "A trust label is not certification." in flattened
    text = json.dumps(payload, sort_keys=True)
    assert '"validation_success_claimed": true' not in text
    assert '"validation_failure_claimed": true' not in text
    assert '"issue_closure_claimed": true' not in text
    assert '"certification_claimed": true' not in text


@pytest.mark.parametrize(
    ("view_model", "expected_code"),
    [
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_schema(
                reason="missing"
            ),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_schema(
                reason="unsupported",
                schema_version_display="old-schema",
            ),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_schema(
                reason="migration_required",
                schema_version_display="old-schema",
            ),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_redaction(
                reviewed=False
            ),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_redaction(
                reviewed=True
            ),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_redaction(
                reviewed=True,
                secret_like=True,
            ),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_stale_source(),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_conflict(),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_conflict(
                shared_stack_warning=True
            ),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.blocked_by_unsafe_claim(),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
        (
            OptionalSolverPluginManifestStateWriterViewModel.from_records(
                sources=({"source_id": "s1", "source_reference_display": "plugin.json"},),
                candidates=({"stack_id": "gmsh", "source_id": "s1"},),
                acknowledgements={},
            ),
            OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY,
        ),
    ],
)
def test_blocked_view_model_states_do_not_write(
    tmp_path: Path,
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
    expected_code: str,
) -> None:
    target = tmp_path / "state.json"
    result = _writer().write_state(view_model, _write_request(target))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert expected_code in _codes(result)
    assert target.exists() is False


def test_future_writer_required_state_is_handled_explicitly_and_safely(
    tmp_path: Path,
) -> None:
    vm = OptionalSolverPluginManifestStateWriterViewModel.from_records(
        sources=({"source_id": "s1", "source_reference_display": "plugin.json"},),
        candidates=({"stack_id": "gmsh", "source_id": "s1"},),
        acknowledgements=_all_acks(),
        future_writer_required=True,
    )
    result = _writer().write_state(vm, _write_request(tmp_path / "state.json"))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert OSPMG_STATE_WRITER_VIEWMODEL_NOT_READY in _codes(result)


def test_dry_run_only_state_can_plan_but_cannot_write(tmp_path: Path) -> None:
    vm = OptionalSolverPluginManifestStateWriterViewModel.dry_run_only(
        sources=({"source_id": "s1", "source_reference_display": "plugin.json"},),
        candidates=({"stack_id": "gmsh", "source_id": "s1"},),
        acknowledgements=_all_acks(),
    )
    dry_run = _writer().write_state(
        vm,
        OptionalSolverPluginManifestStateWriterRequest(target_path=tmp_path / "a.json"),
    )
    actual = _writer().write_state(vm, _write_request(tmp_path / "b.json"))
    assert dry_run.status == OptionalSolverPluginManifestStateWriterStatus.DRY_RUN_PLANNED
    assert actual.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert (tmp_path / "a.json").exists() is False
    assert (tmp_path / "b.json").exists() is False


def test_schema_version_mismatch_blocks_write(tmp_path: Path) -> None:
    result = _writer().write_state(
        _ready_vm(),
        _write_request(tmp_path / "state.json", expected_schema_version="wrong"),
    )
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert OSPMG_STATE_WRITER_SCHEMA_VERSION_MISMATCH in _codes(result)


def test_secret_like_payload_mapping_blocks_write(tmp_path: Path) -> None:
    payload = build_optional_solver_plugin_manifest_state_writer_payload(_ready_vm())
    payload["unsafe_extra"] = "token=secret-value"
    result = _writer().write_state(payload, _write_request(tmp_path / "state.json"))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.BLOCKED
    assert OSPMG_STATE_WRITER_PAYLOAD_SECRET_BLOCKED in _codes(result)
    assert (tmp_path / "state.json").exists() is False


def test_result_mapping_redacts_absolute_target_path(tmp_path: Path) -> None:
    target = tmp_path / "private" / "state.json"
    target.parent.mkdir()
    result = _writer().write_state(_ready_vm(), _write_request(target))
    mapping = result.to_mapping()
    assert mapping["target_reference_display"] == "state.json"
    assert mapping["target_reference_redacted"] is True
    assert str(tmp_path) not in json.dumps(mapping)


def test_result_non_action_flags_remain_false_after_actual_write(tmp_path: Path) -> None:
    result = _writer().write_state(_ready_vm(), _write_request(tmp_path / "state.json"))
    mapping = result.to_mapping()
    assert mapping["write_performed"] is True
    assert mapping["file_write_performed"] is True
    for key in (
        "runtime_state_file_created",
        "settings_file_created",
        "schema_file_created",
        "export_file_created",
        "report_file_created",
        "reloadable_bundle_created",
        "project_schema_mutation_performed",
        "gui_behavior_added",
        "cli_behavior_added",
        "reload_behavior_added",
        "export_behavior_added",
        "clipboard_performed",
        "report_attachment_performed",
        "open_output_folder_performed",
        "discovery_execution_performed",
        "validation_execution_performed",
        "solver_execution_performed",
        "issue_mutation_performed",
        "release_mutation_performed",
        "tag_mutation_performed",
        "asset_mutation_performed",
        "version_bump_performed",
        "validation_success_claimed",
        "validation_failure_claimed",
        "issue_closure_claimed",
        "certification_claimed",
    ):
        assert mapping[key] is False, key


def test_payload_mapping_input_is_supported(tmp_path: Path) -> None:
    payload = build_optional_solver_plugin_manifest_state_writer_payload(_ready_vm())
    result = _writer().write_state(payload, _write_request(tmp_path / "state.json"))
    assert result.status == OptionalSolverPluginManifestStateWriterStatus.WRITTEN
    saved = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert saved["payload_schema_version"] == STATE_WRITER_PAYLOAD_SCHEMA_VERSION


def test_diagnostics_include_planned_completed_and_blocked_codes(tmp_path: Path) -> None:
    planned = _writer().write_state(
        _ready_vm(),
        OptionalSolverPluginManifestStateWriterRequest(target_path=tmp_path / "a.json"),
    )
    written = _writer().write_state(_ready_vm(), _write_request(tmp_path / "b.json"))
    blocked = _writer().write_state(
        OptionalSolverPluginManifestStateWriterViewModel.blocked_by_unsafe_claim(),
        _write_request(tmp_path / "c.json"),
    )
    assert OSPMG_STATE_WRITER_WRITE_PLANNED in _codes(planned)
    assert OSPMG_STATE_WRITER_WRITE_COMPLETED in _codes(written)
    assert OSPMG_STATE_WRITER_WRITE_BLOCKED in _codes(blocked)


def test_implementation_doc_exists_and_records_writer_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8").lower()
    for phrase in (
        "explicit local state writer",
        "caller-supplied target path",
        "deterministic json",
        "dry-run",
        "atomic temp-file/replace",
        "no default write path",
        "no directory creation",
        "no settings file creation",
        "no schema file creation",
        "no export file creation",
        "no report file creation",
        "no reloadable bundle creation",
        "no projectschema mutation",
        "no gui behavior",
        "no cli behavior",
        "no reload behavior",
        "no export behavior",
        "no clipboard behavior",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "no issue mutation",
        "no release mutation",
        "no validation-pass claim",
        "no validation-fail claim",
        "no certification claim",
    ):
        assert phrase in text, phrase
