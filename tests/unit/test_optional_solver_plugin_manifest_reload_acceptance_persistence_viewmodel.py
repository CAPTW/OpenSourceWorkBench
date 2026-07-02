from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

from osw.experimental.optional_solvers import (
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DIAGNOSTIC_CODES,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY,
    RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS,
    RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_KIND,
    RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
    RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_ID,
    RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION,
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
    OptionalSolverPluginManifestReloadAcceptanceViewModel,
    OptionalSolverPluginManifestReloadViewModel,
    ReloadAcceptancePersistenceReadiness,
    ReloadAcceptancePersistenceState,
    all_reload_acceptance_persistence_acknowledgements,
    build_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel,
    from_acceptance_mapping,
    from_acceptance_viewmodel,
    render_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel,
    unavailable,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "osw" / "experimental" / "optional_solvers" / (
    "plugin_manifest_reload_acceptance_persistence_viewmodel.py"
)
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel.md"
)
DECISION_LOG_PATH = REPO_ROOT / "docs" / "07_decision_log.md"


def _ready_reload() -> OptionalSolverPluginManifestReloadViewModel:
    return OptionalSolverPluginManifestReloadViewModel.sample_ready_for_review()


def _ready_acceptance() -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    return OptionalSolverPluginManifestReloadAcceptanceViewModel.ready_for_future_acceptance(
        _ready_reload()
    )


def _accepted_acceptance() -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    return (
        OptionalSolverPluginManifestReloadAcceptanceViewModel.accepted_for_session_review(
            _ready_reload()
        )
    )


def _ready_persistence() -> (
    OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel
):
    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.ready_for_future_writer(
            _ready_acceptance()
        )
    )


def _codes(
    view_model: OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
) -> set[str]:
    return {row.code for row in view_model.diagnostics}


def _text(
    view_model: OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
) -> str:
    return "\n".join(view_model.to_text_lines())


def _module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _imported_modules() -> set[str]:
    tree = ast.parse(_module_source())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return {module.lower() for module in modules}


def _called_names() -> set[str]:
    tree = ast.parse(_module_source())
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    return {call.lower() for call in calls}


def test_module_imports_and_public_package_exports() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers."
        "plugin_manifest_reload_acceptance_persistence_viewmodel"
    )
    assert hasattr(
        module,
        "OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel",
    )
    assert hasattr(module, "ReloadAcceptancePersistenceState")
    assert hasattr(module, "ReloadAcceptancePersistenceReadiness")
    assert hasattr(module, "ReloadAcceptancePersistenceAction")
    assert hasattr(module, "ReloadAcceptancePersistenceSummary")
    assert hasattr(module, "ReloadAcceptancePersistenceWritePlan")
    assert hasattr(module, "ReloadAcceptancePersistenceAcknowledgementRow")
    assert all_reload_acceptance_persistence_acknowledgements() == (
        RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS
    )


def test_source_imports_avoid_reader_writer_gui_cli_file_io_and_execution() -> None:
    imports = _imported_modules() - {"__future__"}
    assert imports == {"collections.abc", "dataclasses", "enum"}
    assert imports.isdisjoint(
        {
            "pathlib",
            "os",
            "subprocess",
            "socket",
            "requests",
            "urllib",
            "osw.cli",
            "pyside6",
            "plugin_manifest_reload_file_reader",
            "plugin_manifest_state_writer",
            "plugin_manifest_reload_acceptance_viewmodel",
            "project_schema",
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
            "read_optional_solver_plugin_manifest_reload_file",
            "write_optional_solver_plugin_manifest_state",
            "discover_optional_solver_manifests",
            "validate_optional_solver_manifest",
            "execute_solver",
        }
    )


def test_unavailable_state_has_no_acceptance_and_no_write_plan() -> None:
    view_model = OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.unavailable()
    assert view_model.summary.state == ReloadAcceptancePersistenceState.NO_ACCEPTANCE_VIEWMODEL
    assert view_model.summary.readiness == (
        ReloadAcceptancePersistenceReadiness.ACCEPTANCE_MISSING
    )
    assert view_model.summary.acceptance_available is False
    assert view_model.summary.ready_for_future_write_plan is False
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING in _codes(view_model)
    assert all(action.enabled is False for action in view_model.action_rows)


def test_preview_acceptance_supplied_but_persistence_not_requested_is_review_only() -> None:
    view_model = from_acceptance_viewmodel(_ready_acceptance())
    assert view_model.summary.state == (
        ReloadAcceptancePersistenceState.PERSISTENCE_NOT_REQUESTED
    )
    assert view_model.summary.readiness == (
        ReloadAcceptancePersistenceReadiness.PERSISTENCE_NOT_REQUESTED
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED in _codes(view_model)
    assert view_model.summary.acceptance_available is True
    assert view_model.summary.persistence_requested is False
    assert view_model.summary.ready_for_future_write_plan is False


def test_requested_persistence_requires_acknowledgements_storage_policy_and_dry_run() -> None:
    view_model = from_acceptance_viewmodel(_ready_acceptance(), persistence_requested=True)
    assert view_model.summary.readiness == (
        ReloadAcceptancePersistenceReadiness.BLOCKED_ACKNOWLEDGEMENT
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED in _codes(
        view_model
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED in _codes(
        view_model
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED in _codes(view_model)
    assert view_model.summary.missing_acknowledgement_count == len(
        RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS
    )
    assert all(row.blocking is True for row in view_model.acknowledgement_rows)


def test_expired_acknowledgement_blocks_future_persistence() -> None:
    view_model = from_acceptance_viewmodel(
        _ready_acceptance(),
        persistence_requested=True,
        acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
        expired_acknowledgements=("acceptance_not_validation",),
        storage_policy_id="explicit",
        target_display="reload-acceptance-state.json",
        dry_run_confirmed=True,
    )
    assert view_model.summary.readiness == (
        ReloadAcceptancePersistenceReadiness.BLOCKED_ACKNOWLEDGEMENT
    )
    assert view_model.summary.expired_acknowledgement_count == 1
    expired = [row for row in view_model.acknowledgement_rows if row.expired]
    assert expired[0].acknowledgement_id == "acceptance_not_validation"


def test_ready_future_writer_plan_is_disabled_and_non_mutating() -> None:
    view_model = _ready_persistence()
    assert view_model.summary.state == (
        ReloadAcceptancePersistenceState.PERSISTENCE_READY_FUTURE_ONLY
    )
    assert view_model.summary.readiness == (
        ReloadAcceptancePersistenceReadiness.WRITER_FUTURE_ONLY
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY in _codes(view_model)
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY in _codes(view_model)
    assert view_model.write_plan.writer_future_only is True
    assert view_model.write_plan.write_performed is False
    assert view_model.write_plan.persistence_write_performed is False
    assert view_model.write_plan.project_schema_mutated is False
    assert all(action.enabled is False for action in view_model.action_rows)
    assert all(action.future_only is True for action in view_model.action_rows)


def test_accepted_for_session_review_input_stays_untrusted_review_scope() -> None:
    view_model = (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.ready_for_future_writer(
            _accepted_acceptance()
        )
    )
    assert view_model.summary.accepted_for_session_review is True
    assert view_model.summary.accepted_state_scope == "session_review_only"
    assert view_model.summary.untrusted_by_default is True
    assert view_model.summary.persistence_readiness_is_runtime_acceptance is False
    assert view_model.summary.persistence_readiness_is_validation_evidence is False
    assert view_model.summary.persistence_readiness_is_validation_failure is False
    assert view_model.summary.persistence_readiness_restores_trust is False


def test_mapping_is_deterministic_json_compatible_and_complete() -> None:
    view_model = _ready_persistence()
    first = view_model.to_mapping()
    second = view_model.to_mapping()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["required_acknowledgements"] == list(
        RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS
    )
    assert first["expiry_reasons"] == list(
        RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS
    )
    assert first["reserved_diagnostic_codes"] == list(
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DIAGNOSTIC_CODES
    )
    assert "write_plan" in first
    assert "non_action_flags" in first
    assert "actions" in first


def test_text_rendering_includes_safety_schema_lifecycle_and_history_guidance() -> None:
    rendered = _text(_ready_persistence()).lower()
    assert "not runtime reload acceptance" in rendered
    assert "not validation evidence" in rendered
    assert "not validation failure" in rendered
    assert "does not restore trust" in rendered
    assert "does not mutate projectschema" in rendered
    assert "schema remains separate from projectschema" in rendered
    assert "no automatic activation" in rendered
    assert "reference-only" in rendered


def test_acknowledgement_rows_cover_required_acceptance_acknowledgements() -> None:
    view_model = _ready_persistence()
    assert tuple(row.acknowledgement_id for row in view_model.acknowledgement_rows) == (
        RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS
    )
    assert all(row.required is True for row in view_model.acknowledgement_rows)
    assert all(row.satisfied is True for row in view_model.acknowledgement_rows)
    assert all(
        row.acknowledgement_is_validation_evidence is False
        for row in view_model.acknowledgement_rows
    )
    assert all(
        row.acknowledgement_restores_trust is False
        for row in view_model.acknowledgement_rows
    )


def test_acknowledgement_expiry_rows_cover_persistence_and_prior_policy_reasons() -> None:
    view_model = _ready_persistence()
    reason_ids = {row.reason_id for row in view_model.expiry_rows}
    assert set(RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS) == reason_ids
    assert "persistence_schema_change" in reason_ids
    assert "persistence_storage_policy_change" in reason_ids
    assert "validation_issue_state_change" in reason_ids
    assert all(row.active is True for row in view_model.expiry_rows)


def test_storage_schema_and_write_plan_are_future_only_and_project_schema_safe() -> None:
    view_model = _ready_persistence()
    storage = view_model.storage_options[0]
    schema = view_model.schema_rows[0]
    assert storage.explicit_user_selected is True
    assert storage.raw_path_hidden is True
    assert storage.default_path_used is False
    assert storage.allowed_in_this_gate is False
    assert storage.future_only is True
    assert schema.schema_id == RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_ID
    assert schema.schema_version == RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION
    assert schema.payload_kind == RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_KIND
    assert schema.separate_from_project_schema is True
    assert schema.repairs_or_migrates_files is False


def test_provenance_redacts_paths_secrets_and_keeps_fingerprints_non_trust_signals() -> None:
    mapping = _ready_acceptance().to_mapping()
    mapping["source_provenance"] = [
        {
            "source_id": "source-1",
            "source_display": "C:/Users/USER/secret=abc/state.json",
            "source_kind": "supplied_acceptance_viewmodel",
            "payload_fingerprint": "token=abc123",
        }
    ]
    view_model = from_acceptance_mapping(
        mapping,
        persistence_requested=True,
        acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
        storage_policy_id="explicit",
        target_display="D:/private/reload-acceptance-state.json",
        dry_run_confirmed=True,
    )
    provenance = view_model.provenance_rows[0]
    rendered = json.dumps(view_model.to_mapping(), sort_keys=True)
    assert provenance.source_display == "<redacted-secret-like-value>"
    assert provenance.payload_fingerprint == ""
    assert provenance.raw_reference_hidden is True
    assert provenance.untrusted_by_default is True
    assert provenance.trust_label_not_certification is True
    assert "C:/Users/USER" not in rendered
    assert "secret=abc" not in rendered
    assert "token=abc123" not in rendered


def test_stale_source_requires_repreview_and_does_not_read_source_files() -> None:
    view_model = from_acceptance_viewmodel(
        _ready_acceptance(),
        persistence_requested=True,
        acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
        storage_policy_id="explicit",
        target_display="state.json",
        dry_run_confirmed=True,
        policy_flags={"stale_source_requires_repreview": True},
    )
    assert view_model.summary.readiness == (
        ReloadAcceptancePersistenceReadiness.BLOCKED_STALE_SOURCE_REPREVIEW
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED in (
        _codes(view_model)
    )
    assert any("Re-preview" in row.required_action for row in view_model.blocker_rows)


def test_conflict_and_shared_stack_review_are_visible_blockers() -> None:
    conflict = from_acceptance_viewmodel(
        _ready_acceptance(),
        persistence_requested=True,
        acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
        storage_policy_id="explicit",
        target_display="state.json",
        dry_run_confirmed=True,
        policy_flags={"conflict_review_required": True},
    )
    shared_stack = from_acceptance_viewmodel(
        _ready_acceptance(),
        persistence_requested=True,
        acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
        storage_policy_id="explicit",
        target_display="state.json",
        dry_run_confirmed=True,
        policy_flags={"shared_stack_review_required": True},
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED in _codes(
        conflict
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED in _codes(
        shared_stack
    )
    assert conflict.summary.state == (
        ReloadAcceptancePersistenceState.CONFLICT_REVIEW_REQUIRED
    )
    assert shared_stack.summary.state == (
        ReloadAcceptancePersistenceState.CONFLICT_REVIEW_REQUIRED
    )


def test_unsafe_claims_are_blocked_and_not_rendered_as_truth() -> None:
    view_model = from_acceptance_viewmodel(
        _ready_acceptance(),
        persistence_requested=True,
        acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
        storage_policy_id="explicit",
        target_display="state.json",
        dry_run_confirmed=True,
        policy_flags={"unsafe_claim_blocked": True},
    )
    assert view_model.summary.state == ReloadAcceptancePersistenceState.UNSAFE_CLAIM_BLOCKED
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED in _codes(view_model)
    rendered = _text(view_model).lower()
    assert "validation success" not in rendered
    assert "issue closure" not in rendered
    assert "certification" in rendered


def test_schema_migration_and_privacy_flags_block_future_persistence() -> None:
    cases = [
        (
            {"unsupported_schema": True},
            ReloadAcceptancePersistenceReadiness.BLOCKED_SCHEMA_UNSUPPORTED,
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED,
        ),
        (
            {"migration_required": True},
            ReloadAcceptancePersistenceReadiness.BLOCKED_MIGRATION_REQUIRED,
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED,
        ),
        (
            {"unredacted_path_blocked": True},
            ReloadAcceptancePersistenceReadiness.BLOCKED_UNREDACTED_PATH,
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED,
        ),
        (
            {"secret_like_value_blocked": True},
            ReloadAcceptancePersistenceReadiness.BLOCKED_SECRET_LIKE_VALUE,
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED,
        ),
    ]
    for flags, readiness, code in cases:
        view_model = from_acceptance_viewmodel(
            _ready_acceptance(),
            persistence_requested=True,
            acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
            storage_policy_id="explicit",
            target_display="state.json",
            dry_run_confirmed=True,
            policy_flags=flags,
        )
        assert view_model.summary.readiness == readiness
        assert code in _codes(view_model)


def test_policy_fingerprint_and_trust_changes_block_future_persistence() -> None:
    view_model = from_acceptance_viewmodel(
        _ready_acceptance(),
        persistence_requested=True,
        acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
        storage_policy_id="explicit",
        target_display="state.json",
        dry_run_confirmed=True,
        policy_flags={
            "trust_policy_changed": True,
            "source_fingerprint_changed": True,
            "persistence_schema_changed": True,
        },
    )
    codes = _codes(view_model)
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED in codes
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED in codes
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED in codes
    assert view_model.summary.readiness == (
        ReloadAcceptancePersistenceReadiness.BLOCKED_POLICY_CHANGE
    )


def test_acceptance_viewmodel_diagnostics_map_to_persistence_blockers() -> None:
    acceptance = OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        OptionalSolverPluginManifestReloadViewModel.unavailable(),
        requested=True,
        acknowledged=(),
    )
    view_model = from_acceptance_viewmodel(
        acceptance,
        persistence_requested=True,
        acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
        storage_policy_id="explicit",
        target_display="state.json",
        dry_run_confirmed=True,
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING in _codes(view_model)
    assert OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED in _codes(
        view_model
    )
    assert view_model.summary.blocker_count >= 1


def test_non_action_flags_are_all_false_and_include_required_boundaries() -> None:
    flags = _ready_persistence().non_action_flags.to_mapping()
    assert all(value is False for value in flags.values())
    for key in (
        "runtime_reload_acceptance_performed",
        "persistence_write_performed",
        "project_schema_mutated",
        "default_reload_path_used",
        "background_reload_performed",
        "directory_scan_performed",
        "network_fetch_performed",
        "plugin_package_imported",
        "cli_subprocess_used",
        "gui_subprocess_used",
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
        assert key in flags


def test_disabled_future_actions_include_writer_and_downstream_mutation_actions() -> None:
    actions = {row.action.value: row for row in _ready_persistence().action_rows}
    for action_id in (
        "persist_acceptance_record",
        "write_acceptance_state",
        "accept_for_session_review",
        "accept_as_trusted",
        "activate_reloaded_candidate",
        "refresh_discovery",
        "validate_solver",
        "execute_solver",
        "install_dependency",
        "uninstall_dependency",
        "uninstall_solver",
        "mutate_project_schema",
        "create_export_summary",
        "create_report_file",
        "create_reloadable_bundle",
        "copy_to_clipboard",
        "attach_to_report",
        "open_output_folder",
        "close_issue",
        "mutate_release",
        "push_tag",
        "upload_asset",
        "claim_validation_success",
        "claim_validation_failure",
        "claim_certification",
    ):
        assert actions[action_id].enabled is False
        assert actions[action_id].future_only is True


def test_evidence_history_is_reference_only_and_not_rewritten() -> None:
    evidence = _ready_persistence().evidence_history_rows[0]
    assert evidence.retained_reference_only is True
    assert evidence.not_validation_evidence is True
    assert evidence.not_validation_failure is True
    assert evidence.no_evidence_deleted_or_rewritten is True
    assert evidence.issue_closure_implied is False


def test_helper_functions_match_class_methods_and_render_text() -> None:
    acceptance = _ready_acceptance()
    direct = from_acceptance_viewmodel(acceptance)
    from_mapping = from_acceptance_mapping(acceptance.to_mapping())
    built = build_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel(
        acceptance_mapping=acceptance.to_mapping()
    )
    assert direct.to_mapping() == from_mapping.to_mapping()
    assert from_mapping.to_mapping() == built.to_mapping()
    assert unavailable().summary.acceptance_available is False
    assert render_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel(
        direct
    ) == direct.to_text_lines()


def test_no_output_runtime_state_export_report_or_reloadable_files_are_created(
    tmp_path: Path,
) -> None:
    before = set(tmp_path.iterdir())
    view_model = _ready_persistence()
    _ = view_model.to_mapping()
    _ = view_model.to_text_lines()
    _ = json.dumps(view_model.to_mapping(), sort_keys=True)
    after = set(tmp_path.iterdir())
    assert after == before


def test_text_and_json_do_not_claim_validation_issue_release_or_certification_success() -> None:
    view_model = _ready_persistence()
    rendered = _text(view_model).lower()
    payload = json.dumps(view_model.to_mapping(), sort_keys=True).lower()
    combined = f"{rendered}\n{payload}"
    assert "validation_pass_claimed\": true" not in combined
    assert "validation_fail_claimed\": true" not in combined
    assert "issue_closure_claimed\": true" not in combined
    assert "release_mutated\": true" not in combined
    assert "certification_claimed\": true" not in combined
    assert "validation evidence" in combined
    assert "not validation evidence" in combined
    assert "certification" in combined


def test_documentation_and_adr_record_non_writing_boundary() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    for heading in (
        "## 1. Status",
        "## 3. Public module/class names",
        "## 7. Write-plan model",
        "## 23. Non-action flags",
        "## 36. Future gates",
    ):
        assert heading in doc
    for phrase in (
        "Experimental reload acceptance persistence view-model implemented",
        "Pure in-memory",
        "Future-writer-only",
        "No persistence writes",
        "No checked-in state files",
        "No file IO",
        "No ProjectSchema mutation",
        "No discovery/validation/solver execution",
        "No automatic activation",
        "No trust restoration",
    ):
        assert phrase in doc
    assert "ADR-0159" in decision_log
    assert "Persistence ViewModel Is Non-Writing" in decision_log
