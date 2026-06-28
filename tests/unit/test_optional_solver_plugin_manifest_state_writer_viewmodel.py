from __future__ import annotations

import ast
import importlib
from pathlib import Path

from osw.experimental.optional_solvers import (
    OSPMG_STATE_WRITER_ACK_REQUIRED,
    OSPMG_STATE_WRITER_CONFLICT_BLOCKED,
    OSPMG_STATE_WRITER_DIAGNOSTIC_CODES,
    OSPMG_STATE_WRITER_DRY_RUN_ONLY,
    OSPMG_STATE_WRITER_EVIDENCE_RETAINED,
    OSPMG_STATE_WRITER_EXPORT_DISABLED,
    OSPMG_STATE_WRITER_FUTURE_GATE,
    OSPMG_STATE_WRITER_HISTORY_RETAINED,
    OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION,
    OSPMG_STATE_WRITER_NO_INSTALL,
    OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT,
    OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION,
    OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION,
    OSPMG_STATE_WRITER_NOT_CERTIFICATION,
    OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE,
    OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION,
    OSPMG_STATE_WRITER_NOT_TRUST_RESTORE,
    OSPMG_STATE_WRITER_NOT_VALIDATION,
    OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED,
    OSPMG_STATE_WRITER_REDACTION_REQUIRED,
    OSPMG_STATE_WRITER_RELOAD_DISABLED,
    OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED,
    OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED,
    OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED,
    OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED,
    OSPMG_STATE_WRITER_SHARED_STACK_WARNING,
    OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED,
    OSPMG_STATE_WRITER_UNSAFE_CLAIM,
    OSPMG_STATE_WRITER_UNTRUSTED_SOURCE,
    STATE_WRITER_REQUIRED_ACKS,
    OptionalSolverPluginManifestExportSummaryViewModel,
    OptionalSolverPluginManifestPersistenceCandidateInput,
    OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord,
    OptionalSolverPluginManifestPersistenceSchemaCandidateRecord,
    OptionalSolverPluginManifestPersistenceSchemaInput,
    OptionalSolverPluginManifestPersistenceSchemaSourceRecord,
    OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord,
    OptionalSolverPluginManifestStateWriterAction,
    OptionalSolverPluginManifestStateWriterConflictRow,
    OptionalSolverPluginManifestStateWriterEvidenceHistoryRow,
    OptionalSolverPluginManifestStateWriterReadiness,
    OptionalSolverPluginManifestStateWriterSourceRow,
    OptionalSolverPluginManifestStateWriterStaleSourceRow,
    OptionalSolverPluginManifestStateWriterUnsafeClaimRow,
    OptionalSolverPluginManifestStateWriterViewModel,
    build_optional_solver_plugin_manifest_persistence_schema_model,
    build_optional_solver_plugin_manifest_persistence_viewmodel,
    build_optional_solver_plugin_manifest_state_writer_viewmodel,
    redact_optional_solver_plugin_manifest_state_writer_source_reference,
    render_optional_solver_plugin_manifest_state_writer_viewmodel,
    summarize_optional_solver_plugin_manifest_state_writer_viewmodel,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_state_writer_viewmodel as module_under_test,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_state_writer_viewmodel.md"
)
DESIGN_DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_state_writer_design.md"
)


def _all_acks() -> dict[str, bool]:
    return {ack: True for ack in STATE_WRITER_REQUIRED_ACKS}


def _codes(view_model) -> set[str]:
    return {diagnostic.code for diagnostic in view_model.diagnostics}


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


def _source(**kwargs) -> dict[str, object]:
    base: dict[str, object] = {
        "source_id": "s1",
        "source_type": "user_selected_json_file",
        "source_reference_display": "plugin.json",
        "source_reference_redacted": True,
    }
    base.update(kwargs)
    return base


def _candidate(**kwargs) -> dict[str, object]:
    base: dict[str, object] = {
        "stack_id": "gmsh",
        "display_name": "Gmsh",
        "source_id": "s1",
        "source_type": "user_selected_json_file",
        "trust_label": "untrusted_user_file",
    }
    base.update(kwargs)
    return base


def _ready_vm() -> OptionalSolverPluginManifestStateWriterViewModel:
    return OptionalSolverPluginManifestStateWriterViewModel.ready_for_future_write()


def test_module_imports_without_gui_or_cli_extras() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers.plugin_manifest_state_writer_viewmodel"
    )
    vm = _ready_vm()
    assert hasattr(module, "OptionalSolverPluginManifestStateWriterViewModel")
    assert "non-writing" in summarize_optional_solver_plugin_manifest_state_writer_viewmodel(
        vm
    )


def test_module_has_no_gui_cli_heavy_or_unsafe_imports() -> None:
    forbidden_roots = {
        "argparse",
        "click",
        "typer",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "pathlib",
        "os",
        "shutil",
        "gmsh",
        "meshio",
        "pyvista",
        "vtk",
        "coolprop",
        "cantera",
    }
    for module in _imported_modules():
        root = module.split(".", 1)[0]
        assert root not in forbidden_roots, module
        assert "pyside" not in module
        assert "pyqt" not in module
        assert not module.startswith("qt")


def test_module_source_has_no_io_mutation_discovery_or_solver_paths() -> None:
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
        "pip install",
        "pip uninstall",
        "conda remove",
        "gh issue",
        "gh release",
        ".unlink(",
        ".rmdir(",
        "shutil.rmtree",
        ".write_text(",
        ".write_bytes(",
        ".read_text(",
        ".exists(",
        "open(",
        "json.load(",
        "ProjectSchema(",
        "load_optional_solver_plugin_manifest_json",
    ):
        assert phrase not in source, phrase


def test_unavailable_and_no_explicit_request_states() -> None:
    unavailable = OptionalSolverPluginManifestStateWriterViewModel.unavailable()
    assert unavailable.summary.readiness == "unavailable_no_state"
    assert unavailable.summary.writer_performed is False
    assert unavailable.write_plans[0].would_write is False

    no_request = OptionalSolverPluginManifestStateWriterViewModel.from_records(
        sources=(_source(),),
        candidates=(_candidate(),),
        acknowledgements=_all_acks(),
        explicit_write_request=False,
    )
    assert no_request.summary.readiness == "unavailable_no_explicit_request"


def test_dry_run_only_and_ready_states_keep_write_plan_false() -> None:
    dry_run = OptionalSolverPluginManifestStateWriterViewModel.dry_run_only(
        sources=(_source(),),
        candidates=(_candidate(),),
        acknowledgements=_all_acks(),
    )
    assert dry_run.summary.readiness == "dry_run_only"
    assert OSPMG_STATE_WRITER_DRY_RUN_ONLY in _codes(dry_run)

    ready = _ready_vm()
    assert ready.summary.readiness == "ready_for_future_write"
    plan = ready.write_plans[0]
    assert plan.would_write is False
    assert plan.would_create_directory is False
    assert plan.would_mutate_project_schema is False
    assert plan.would_reload is False
    assert plan.would_export is False


def test_storage_options_are_future_only_and_not_allowed_in_this_gate() -> None:
    vm = _ready_vm()
    ids = {row.storage_option_id for row in vm.storage_options}
    assert {
        "project_local",
        "user_profile_cache",
        "session_local_ephemeral",
        "explicit_user_chosen_file",
        "no_default_write_path",
    } <= ids
    assert all(row.future_only for row in vm.storage_options)
    assert all(not row.allowed_in_this_gate for row in vm.storage_options)


def test_schema_missing_unsupported_and_migration_block_readiness() -> None:
    missing = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_schema(
        reason="missing"
    )
    unsupported = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_schema(
        reason="unsupported",
        schema_version_display="old-schema",
    )
    migration = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_schema(
        reason="migration_required",
        schema_version_display="old-schema",
    )
    assert missing.summary.readiness == "blocked_schema_version_missing"
    assert unsupported.summary.readiness == "blocked_schema_unsupported"
    assert migration.summary.readiness == "blocked_schema_migration_required"
    assert OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED in _codes(missing)
    assert OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED in _codes(unsupported)
    assert OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED in _codes(migration)


def test_redaction_unredacted_path_and_secret_like_content_block_readiness() -> None:
    review = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_redaction(
        reviewed=False
    )
    path = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_redaction(
        reviewed=True
    )
    secret_case = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_redaction(
        secret_like=True,
        reviewed=True,
    )
    assert review.summary.readiness == "blocked_redaction_review"
    assert path.summary.readiness == "blocked_unredacted_path"
    assert secret_case.summary.readiness == "blocked_secret_like_content"
    assert OSPMG_STATE_WRITER_REDACTION_REQUIRED in _codes(review)
    assert OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED in _codes(path)
    assert OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED in _codes(secret_case)


def test_stale_source_conflict_shared_stack_and_unsafe_claims_block() -> None:
    stale = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_stale_source()
    conflict = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_conflict()
    shared = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_conflict(
        shared_stack_warning=True
    )
    unsafe = OptionalSolverPluginManifestStateWriterViewModel.blocked_by_unsafe_claim()
    assert stale.summary.readiness == "blocked_stale_source_repreview"
    assert conflict.summary.readiness == "blocked_conflict"
    assert shared.summary.readiness == "blocked_shared_stack_warning"
    assert unsafe.summary.readiness == "blocked_unsafe_claim"
    assert OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED in _codes(stale)
    assert OSPMG_STATE_WRITER_CONFLICT_BLOCKED in _codes(conflict)
    assert OSPMG_STATE_WRITER_SHARED_STACK_WARNING in _codes(shared)
    assert OSPMG_STATE_WRITER_UNSAFE_CLAIM in _codes(unsafe)


def test_missing_acknowledgement_blocks_and_required_categories_are_visible() -> None:
    vm = OptionalSolverPluginManifestStateWriterViewModel.from_records(
        sources=(_source(),),
        candidates=(_candidate(),),
        acknowledgements={},
    )
    assert vm.summary.readiness == "blocked_acknowledgement"
    assert OSPMG_STATE_WRITER_ACK_REQUIRED in _codes(vm)
    ack_ids = {row.acknowledgement_id for row in vm.acknowledgement_rows}
    assert set(STATE_WRITER_REQUIRED_ACKS) <= ack_ids
    assert any(row.expires_on_reload for row in vm.acknowledgement_rows)
    assert any(row.expires_on_source_fingerprint_change for row in vm.acknowledgement_rows)
    assert any(row.expires_on_schema_change for row in vm.acknowledgement_rows)
    assert any(row.expires_on_unsafe_claim_change for row in vm.acknowledgement_rows)
    assert any(row.expires_on_trust_policy_change for row in vm.acknowledgement_rows)


def test_source_rows_are_redacted_and_untrusted_by_default() -> None:
    vm = OptionalSolverPluginManifestStateWriterViewModel.from_records(
        sources=(
            _source(
                source_reference_display="C:/private/manifests/plugin.json",
                source_reference_redacted=False,
            ),
        ),
        candidates=(_candidate(),),
        acknowledgements=_all_acks(),
        redaction_reviewed=True,
    )
    source = vm.source_rows[0]
    assert source.source_reference_display == "plugin.json"
    assert source.source_reference_redacted is True
    assert source.trust_label == "untrusted_user_file"
    assert source.trust_label_not_certification is True
    assert source.persisted_state_is_not_validation_evidence is True
    assert source.persisted_state_is_not_trust_restoration is True
    assert OSPMG_STATE_WRITER_UNTRUSTED_SOURCE in _codes(vm)


def test_candidate_rows_preserve_lifecycle_without_implying_mutation() -> None:
    vm = OptionalSolverPluginManifestStateWriterViewModel.from_records(
        sources=(_source(),),
        candidates=(
            _candidate(
                activation_state="inactive_preview",
                deactivation_state="deactivated_preview",
                reactivation_state="review_required",
                discovery_refresh_state="not_refreshed",
                persistence_state="session_only",
            ),
        ),
        acknowledgements=_all_acks(),
    )
    row = vm.candidate_rows[0]
    assert row.activation_state == "inactive_preview"
    assert row.deactivation_state == "deactivated_preview"
    assert row.reactivation_state == "review_required"
    assert row.discovery_refresh_state == "not_refreshed"
    assert row.persistence_state == "session_only"
    assert row.issue_closure_implied is False
    assert row.automatic_activation_implied is False
    assert row.trust_restoration_implied is False


def test_stale_conflict_unsafe_and_evidence_rows_preserve_safety_policies() -> None:
    stale = OptionalSolverPluginManifestStateWriterStaleSourceRow(
        stale_source_state="missing",
        repreview_required=True,
        source_reference_display="plugin.json",
    )
    conflict = OptionalSolverPluginManifestStateWriterConflictRow(stack_id="gmsh")
    unsafe = OptionalSolverPluginManifestStateWriterUnsafeClaimRow(
        claim_id="claim",
        claim_text="validated and certified",
    )
    evidence = OptionalSolverPluginManifestStateWriterEvidenceHistoryRow()
    vm = build_optional_solver_plugin_manifest_state_writer_viewmodel(
        sources=(_source(),),
        candidates=(_candidate(),),
        stale_source_rows=(stale,),
        conflicts=(conflict,),
        unsafe_claims=(unsafe,),
        evidence_history=(evidence,),
        acknowledgements=_all_acks(),
    )
    assert vm.stale_source_rows[0].old_preview_not_silently_trusted is True
    assert vm.stale_source_rows[0].no_file_io_performed is True
    assert vm.stale_source_rows[0].no_file_restoration_performed is True
    assert vm.stale_source_rows[0].no_file_rewrite_performed is True
    assert vm.stale_source_rows[0].no_file_deletion_performed is True
    assert vm.conflict_rows[0].built_ins_win_by_default is True
    assert vm.conflict_rows[0].persisted_state_does_not_override_builtin is True
    assert vm.unsafe_claim_rows[0].blocked is True
    assert vm.unsafe_claim_rows[0].accepted_by_writer is False
    assert vm.unsafe_claim_rows[0].persisted_as_truth is False
    assert vm.evidence_history_rows[0].deactivation_history_retained is True
    assert vm.evidence_history_rows[0].reactivation_history_retained is True
    assert vm.evidence_history_rows[0].historical_validation_evidence_retained is True
    assert vm.evidence_history_rows[0].skipped_missing_remains_skipped_missing is True
    assert OSPMG_STATE_WRITER_EVIDENCE_RETAINED in _codes(vm)
    assert OSPMG_STATE_WRITER_HISTORY_RETAINED in _codes(vm)


def test_atomicity_and_schema_boundary_are_future_only() -> None:
    vm = _ready_vm()
    atomic = vm.atomicity_plan_rows[0]
    boundary = vm.file_format_boundaries[0]
    assert atomic.write_plan_first_required is True
    assert atomic.target_path_policy_required is True
    assert atomic.atomic_temp_replace_future_required is True
    assert atomic.rollback_policy_future_required is True
    assert atomic.no_partial_write_claim_in_this_gate is True
    assert boundary.schema_file_created is False
    assert boundary.actual_json_writer_implemented is False
    assert boundary.project_schema_state == "not_project_schema"


def test_non_action_flags_are_all_false() -> None:
    flags = _ready_vm().non_action_flags
    for slot in flags.__slots__:
        assert getattr(flags, slot) is False, slot


def test_action_states_disable_future_and_unsafe_actions() -> None:
    vm = _ready_vm()
    by_action = {row.action: row for row in vm.actions}
    for action in (
        OptionalSolverPluginManifestStateWriterAction.WRITE_STATE_FILE,
        OptionalSolverPluginManifestStateWriterAction.CREATE_RUNTIME_STATE_FILE,
        OptionalSolverPluginManifestStateWriterAction.CREATE_SETTINGS_FILE,
        OptionalSolverPluginManifestStateWriterAction.CREATE_SCHEMA_FILE,
        OptionalSolverPluginManifestStateWriterAction.CREATE_EXPORT_FILE,
        OptionalSolverPluginManifestStateWriterAction.CREATE_REPORT_FILE,
        OptionalSolverPluginManifestStateWriterAction.CREATE_RELOADABLE_BUNDLE,
        OptionalSolverPluginManifestStateWriterAction.MUTATE_PROJECT_SCHEMA,
        OptionalSolverPluginManifestStateWriterAction.RELOAD_STATE,
        OptionalSolverPluginManifestStateWriterAction.EXPORT_STATE,
        OptionalSolverPluginManifestStateWriterAction.COPY_TO_CLIPBOARD,
        OptionalSolverPluginManifestStateWriterAction.ATTACH_REPORT,
        OptionalSolverPluginManifestStateWriterAction.OPEN_OUTPUT_FOLDER,
        OptionalSolverPluginManifestStateWriterAction.IMPORT_PLUGIN_PACKAGE,
        OptionalSolverPluginManifestStateWriterAction.SCAN_DIRECTORY,
        OptionalSolverPluginManifestStateWriterAction.FETCH_NETWORK_MANIFEST,
        OptionalSolverPluginManifestStateWriterAction.RUN_DISCOVERY,
        OptionalSolverPluginManifestStateWriterAction.RUN_VALIDATION,
        OptionalSolverPluginManifestStateWriterAction.INSTALL_DEPENDENCY,
        OptionalSolverPluginManifestStateWriterAction.UNINSTALL_DEPENDENCY,
        OptionalSolverPluginManifestStateWriterAction.UNINSTALL_SOLVER,
        OptionalSolverPluginManifestStateWriterAction.EXECUTE_SOLVER,
        OptionalSolverPluginManifestStateWriterAction.CLOSE_ISSUE,
        OptionalSolverPluginManifestStateWriterAction.MUTATE_RELEASE,
        OptionalSolverPluginManifestStateWriterAction.PUSH_TAG,
        OptionalSolverPluginManifestStateWriterAction.UPLOAD_ASSET,
    ):
        assert by_action[action].enabled is False
        assert by_action[action].available is False
        assert by_action[action].future_action is True
    assert by_action[OptionalSolverPluginManifestStateWriterAction.REQUEST_DRY_RUN].enabled is True
    assert (
        by_action[OptionalSolverPluginManifestStateWriterAction.REVIEW_WRITE_PLAN].enabled
        is True
    )


def test_diagnostic_vocabulary_and_safety_codes_are_surfaced() -> None:
    vm = _ready_vm()
    codes = _codes(vm)
    for code in (
        OSPMG_STATE_WRITER_NOT_VALIDATION,
        OSPMG_STATE_WRITER_NOT_TRUST_RESTORE,
        OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION,
        OSPMG_STATE_WRITER_NO_INSTALL,
        OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION,
        OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE,
        OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION,
        OSPMG_STATE_WRITER_NOT_CERTIFICATION,
        OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION,
        OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT,
        OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED,
        OSPMG_STATE_WRITER_RELOAD_DISABLED,
        OSPMG_STATE_WRITER_EXPORT_DISABLED,
        OSPMG_STATE_WRITER_FUTURE_GATE,
    ):
        assert code in codes
    assert set(OSPMG_STATE_WRITER_DIAGNOSTIC_CODES) <= set(
        vm.reserved_diagnostic_codes
    )


def test_text_and_mapping_render_in_memory_without_file_creation_claims() -> None:
    vm = _ready_vm()
    lines = vm.to_text_lines()
    mapping = vm.to_mapping()
    rendered = render_optional_solver_plugin_manifest_state_writer_viewmodel(vm)
    assert any("no writer implementation" in line for line in lines)
    assert mapping == rendered
    assert mapping["summary"]["file_write_performed"] is False
    assert mapping["write_plans"][0]["would_write"] is False
    assert mapping["non_action_flags"]["runtime_state_file_created"] is False
    assert mapping["not_validation_evidence"] is True


def test_from_persistence_viewmodel_consumes_supplied_records_without_mutation() -> None:
    persistence_vm = build_optional_solver_plugin_manifest_persistence_viewmodel(
        (
            OptionalSolverPluginManifestPersistenceCandidateInput(
                stack_id="gmsh",
                source_reference="C:/private/plugin.json",
                persistence_requested=True,
            ),
        ),
        acknowledgements=_all_acks(),
        persistence_requested=True,
        schema=OptionalSolverPluginManifestPersistenceSchemaInput(
            schema_version_display="osw-exp-092-preview",
            schema_version_present=True,
        ),
    )
    before = persistence_vm.candidate_rows[0].source_reference_display
    writer_vm = OptionalSolverPluginManifestStateWriterViewModel.from_persistence_viewmodel(
        persistence_vm,
        acknowledgements=_all_acks(),
    )
    assert persistence_vm.candidate_rows[0].source_reference_display == before
    assert writer_vm.candidate_rows[0].stack_id == "gmsh"
    assert writer_vm.summary.writer_performed is False


def test_from_schema_model_consumes_supplied_records_without_mutation() -> None:
    source = OptionalSolverPluginManifestPersistenceSchemaSourceRecord(
        source_id="s1",
        source_reference_display="plugin.json",
        trust_label="untrusted_user_file",
    )
    candidate = OptionalSolverPluginManifestPersistenceSchemaCandidateRecord(
        stack_id="gmsh",
        source_id="s1",
        persistence_state="persistence_ready_preview",
    )
    schema_model = build_optional_solver_plugin_manifest_persistence_schema_model(
        sources=(source,),
        candidates=(candidate,),
        acknowledgements=(
            OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord(
                acknowledgement_id="state_write_not_validation",
                satisfied=True,
            ),
        ),
        unsafe_claims=(
            OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord(
                claim_id="unsafe",
                claim_text="certified",
            ),
        ),
    )
    before = schema_model.sources[0].source_reference_display
    writer_vm = OptionalSolverPluginManifestStateWriterViewModel.from_schema_model(
        schema_model,
        acknowledgements=_all_acks(),
    )
    assert schema_model.sources[0].source_reference_display == before
    assert writer_vm.source_rows[0].source_id == "s1"
    assert writer_vm.candidate_rows[0].stack_id == "gmsh"
    assert writer_vm.unsafe_claim_rows[0].persisted_as_truth is False


def test_from_export_summary_viewmodel_consumes_supplied_records_without_mutation() -> None:
    export_vm = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(OptionalSolverPluginManifestStateWriterSourceRow(source_id="s1"),),
        candidates=(_candidate(),),
        acknowledgements=_all_acks(),
    )
    before = export_vm.to_mapping()
    writer_vm = OptionalSolverPluginManifestStateWriterViewModel.from_export_summary_viewmodel(
        export_vm,
        acknowledgements=_all_acks(),
    )
    assert export_vm.to_mapping() == before
    assert writer_vm.source_rows[0].source_id == "s1"
    assert writer_vm.write_plans[0].would_write is False


def test_redaction_helper_returns_basename_only() -> None:
    display, redacted = redact_optional_solver_plugin_manifest_state_writer_source_reference(
        "C:/private/path/plugin.json"
    )
    assert display == "plugin.json"
    assert redacted is True


def test_docs_mention_non_actions_and_future_gates() -> None:
    doc = DOC.read_text(encoding="utf-8").lower()
    design = DESIGN_DOC.read_text(encoding="utf-8").lower()
    for phrase in (
        "pure",
        "side-effect-free",
        "no writer implementation",
        "no file writes",
        "no runtime state files",
        "no settings files",
        "no schema files",
        "no projectschema mutation",
        "no gui behavior",
        "no cli behavior",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "future gates",
        "osw-exp-102",
    ):
        assert phrase in doc
    assert "implementation follow-up" in design


def test_readiness_vocabulary_contains_required_values() -> None:
    values = {item.value for item in OptionalSolverPluginManifestStateWriterReadiness}
    assert {
        "unavailable_no_state",
        "unavailable_no_explicit_request",
        "dry_run_only",
        "blocked_acknowledgement",
        "blocked_redaction_review",
        "blocked_unredacted_path",
        "blocked_secret_like_content",
        "blocked_schema_version_missing",
        "blocked_schema_unsupported",
        "blocked_schema_migration_required",
        "blocked_stale_source_repreview",
        "blocked_conflict",
        "blocked_shared_stack_warning",
        "blocked_unsafe_claim",
        "ready_for_future_write",
        "future_writer_required",
        "error",
    } <= values
