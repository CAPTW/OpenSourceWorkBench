from __future__ import annotations

import ast
import importlib
from pathlib import Path

from osw.experimental.optional_solvers import (
    EXPORT_SUMMARY_REQUIRED_ACKS,
    OSPMG_EXPORT_SUMMARY_ACK_REQUIRED,
    OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED,
    OSPMG_EXPORT_SUMMARY_DIAGNOSTIC_CODES,
    OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED,
    OSPMG_EXPORT_SUMMARY_FUTURE_GATE,
    OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED,
    OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION,
    OSPMG_EXPORT_SUMMARY_NO_INSTALL,
    OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT,
    OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION,
    OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED,
    OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE,
    OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE,
    OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION,
    OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE,
    OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE,
    OSPMG_EXPORT_SUMMARY_NOT_VALIDATION,
    OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED,
    OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED,
    OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM,
    OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE,
    PERSISTENCE_REQUIRED_ACKS,
    OptionalSolverPluginManifestExportSummaryAction,
    OptionalSolverPluginManifestExportSummaryCandidateRow,
    OptionalSolverPluginManifestExportSummaryConflictRow,
    OptionalSolverPluginManifestExportSummaryDiagnosticRow,
    OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow,
    OptionalSolverPluginManifestExportSummaryLimitationRow,
    OptionalSolverPluginManifestExportSummarySourceRow,
    OptionalSolverPluginManifestExportSummaryViewModel,
    OptionalSolverPluginManifestPersistenceCandidateInput,
    OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord,
    OptionalSolverPluginManifestPersistenceSchemaCandidateRecord,
    OptionalSolverPluginManifestPersistenceSchemaInput,
    OptionalSolverPluginManifestPersistenceSchemaSourceRecord,
    OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord,
    build_optional_solver_plugin_manifest_persistence_schema_model,
    build_optional_solver_plugin_manifest_persistence_viewmodel,
    redact_optional_solver_plugin_manifest_export_summary_source_reference,
    render_optional_solver_plugin_manifest_export_summary,
    summarize_optional_solver_plugin_manifest_export_summary_viewmodel,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_export_summary_viewmodel as module_under_test,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_export_summary_viewmodel.md"
)
DESIGN_DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_state_export_summary_design.md"
)


def _all_acks() -> dict[str, bool]:
    return {ack: True for ack in EXPORT_SUMMARY_REQUIRED_ACKS}


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


def _source(**kwargs) -> OptionalSolverPluginManifestExportSummarySourceRow:
    base = {
        "source_id": "s1",
        "source_type": "user_selected_json_file",
        "source_reference_display": "C:/private/manifests/plugin.json",
    }
    base.update(kwargs)
    return OptionalSolverPluginManifestExportSummarySourceRow(**base)


def _candidate(**kwargs) -> OptionalSolverPluginManifestExportSummaryCandidateRow:
    base = {
        "stack_id": "gmsh",
        "display_name": "Gmsh",
        "source_id": "s1",
        "source_type": "user_selected_json_file",
        "trust_label": "untrusted_user_file",
        "activation_state": "inactive_preview",
        "deactivation_state": "not_deactivated",
        "reactivation_state": "not_requested",
        "discovery_refresh_state": "not_refreshed",
        "persistence_state": "session_only",
    }
    base.update(kwargs)
    return OptionalSolverPluginManifestExportSummaryCandidateRow(**base)


def _ready_vm():
    return OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(
            _source(
                source_reference_display="plugin.json",
                source_reference_redacted=True,
            ),
        ),
        candidates=(_candidate(source_reference_display="plugin.json"),),
        acknowledgements=_all_acks(),
    )


def test_module_imports_without_gui_extras() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers.plugin_manifest_export_summary_viewmodel"
    )
    vm = OptionalSolverPluginManifestExportSummaryViewModel.empty()
    assert hasattr(module, "OptionalSolverPluginManifestExportSummaryViewModel")
    assert "export summary" in summarize_optional_solver_plugin_manifest_export_summary_viewmodel(
        vm
    ).lower()


def test_module_has_no_gui_heavy_or_unsafe_imports() -> None:
    forbidden_roots = {
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


def test_empty_no_state_is_unavailable_and_non_action() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.unavailable()
    assert vm.header.readiness == "unavailable_no_state"
    assert vm.header.export_summary_state == "export_summary_unavailable"
    assert vm.header.source_count == 0
    assert vm.header.candidate_count == 0
    assert vm.header.export_performed is False
    assert vm.header.file_write_performed is False
    assert vm.header.clipboard_performed is False
    assert vm.header.report_attachment_performed is False
    assert vm.header.reloadable_bundle_created is False
    assert vm.header.persistence_performed is False
    assert OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED in _codes(vm)


def test_source_records_are_redacted_by_default_and_raw_paths_block() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(_source(),),
        acknowledgements=_all_acks(),
    )
    row = vm.source_rows[0]
    assert row.source_reference_display == "plugin.json"
    assert row.source_reference_redacted is True
    assert row.raw_reference_blocked is True
    assert "/" not in row.source_reference_display
    assert chr(92) not in row.source_reference_display
    assert vm.header.readiness == "blocked_unredacted_path"
    assert OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED in _codes(vm)


def test_secret_like_content_is_blocked_and_redacted() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(
            _source(
                source_reference_display="token=abc123",
                source_reference_redacted=False,
            ),
        ),
        acknowledgements=_all_acks(),
    )
    row = vm.source_rows[0]
    assert row.source_reference_display == "<redacted-secret-like-reference>"
    assert row.secret_like_content_blocked is True
    assert row.raw_reference_blocked is True
    assert vm.redaction_rows[0].secret_like_content_blocked is True


def test_source_trust_labels_are_not_certification() -> None:
    vm = _ready_vm()
    source = vm.source_rows[0]
    assert source.trust_label == "untrusted_user_file"
    assert source.trust_label_not_certification is True
    assert source.not_validation_evidence is True
    assert OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE in _codes(vm)


def test_user_plugin_manifests_untrusted_and_builtins_authoritative() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(
            _source(source_id="user", trust_label="untrusted_plugin_manifest"),
            _source(
                source_id="builtin",
                source_type="built_in",
                source_reference_display="builtin",
                trust_label="built_in",
            ),
        ),
        candidates=(
            _candidate(source_id="user", trust_label="untrusted_plugin_manifest"),
            _candidate(
                stack_id="builtin_gmsh",
                source_id="builtin",
                source_type="built_in",
                trust_label="built_in",
            ),
        ),
        acknowledgements=_all_acks(),
    )
    user = next(row for row in vm.candidate_rows if row.source_id == "user")
    builtin = next(row for row in vm.candidate_rows if row.source_id == "builtin")
    assert user.is_untrusted is True
    assert user.trusted_source_implied is False
    assert builtin.built_in_authoritative is True
    assert builtin.built_in_relationship == "built_in_authoritative"


def test_candidate_row_preserves_lifecycle_states_without_implying_actions() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(_source(source_reference_display="plugin.json"),),
        candidates=(
            _candidate(
                activation_state="active_candidate",
                deactivation_state="deactivated",
                reactivation_state="reactivation_requested",
                discovery_refresh_state="included",
                persistence_state="persistence_ready_preview",
                stale_source_state="fresh",
                redaction_status="redacted",
            ),
        ),
        acknowledgements=_all_acks(),
    )
    row = vm.candidate_rows[0]
    assert row.activation_state == "active_candidate"
    assert row.deactivation_state == "deactivated"
    assert row.reactivation_state == "reactivation_requested"
    assert row.discovery_refresh_state == "included"
    assert row.persistence_state == "persistence_ready_preview"
    assert row.automatic_activation_implied is False
    assert row.validation_evidence_implied is False
    assert row.issue_closure_implied is False


def test_required_acknowledgements_are_visible() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(_source(source_reference_display="plugin.json"),),
        acknowledgements={},
    )
    ack_ids = {row.acknowledgement_id for row in vm.acknowledgement_rows}
    assert ack_ids == set(EXPORT_SUMMARY_REQUIRED_ACKS)
    for ack in (
        "export_not_validation",
        "export_not_persistence",
        "export_not_reloadable_bundle",
        "export_not_trust_restoration",
        "export_not_install",
        "export_no_solver_execution",
        "export_not_issue_closure",
        "export_not_release_mutation",
        "redaction_reviewed",
        "unredacted_paths_blocked",
        "stale_source_requires_repreview",
        "untrusted_source_remains_untrusted",
        "no_discovery_execution",
        "no_plugin_package_import",
        "trust_label_not_certification",
    ):
        assert ack in ack_ids


def test_missing_acknowledgements_block_and_satisfied_acknowledgements_ready() -> None:
    blocked = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(_source(source_reference_display="plugin.json"),),
        acknowledgements={},
    )
    assert blocked.header.readiness == "blocked_redaction_review"
    assert OSPMG_EXPORT_SUMMARY_ACK_REQUIRED in _codes(blocked)
    assert any(row.blocking for row in blocked.acknowledgement_rows)

    ready = _ready_vm()
    assert ready.header.readiness == "ready_preview_only"
    assert ready.header.export_summary_state == "export_summary_ready_preview"
    assert ready.header.export_performed is False
    assert ready.header.validation_success_claimed is False
    assert ready.header.validation_failure_claimed is False


def test_diagnostic_vocabularies_surface_expected_codes() -> None:
    vm = _ready_vm()
    codes = _codes(vm)
    for code in (
        OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED,
        OSPMG_EXPORT_SUMMARY_NOT_VALIDATION,
        OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE,
        OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE,
        OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE,
        OSPMG_EXPORT_SUMMARY_NO_INSTALL,
        OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION,
        OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE,
        OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION,
        OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED,
        OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE,
        OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED,
        OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED,
        OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION,
        OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT,
        OSPMG_EXPORT_SUMMARY_FUTURE_GATE,
    ):
        assert code in codes
        assert code in OSPMG_EXPORT_SUMMARY_DIAGNOSTIC_CODES

    diag = OptionalSolverPluginManifestExportSummaryDiagnosticRow(
        severity="warning",
        category="export_summary",
        code=OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED,
        message="conflict",
        blocker=True,
    )
    assert diag.code.startswith("OSPMG_EXPORT_SUMMARY_")


def test_redaction_required_helper_surfaces_diagnostic() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.redaction_required(
        "C:/private/plugin.json"
    )
    assert vm.header.readiness == "blocked_unredacted_path"
    assert OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED in _codes(vm)
    assert OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED in _codes(vm)


def test_stale_source_repreview_row_preserves_no_file_mutation_policy() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.stale_source_repreview_required()
    row = vm.stale_source_rows[0]
    assert row.stale_source_state == "stale"
    assert row.repreview_required is True
    assert row.old_preview_not_silently_trusted is True
    assert row.no_file_io_performed is True
    assert row.no_file_restoration_performed is True
    assert row.no_file_rewrite_performed is True
    assert row.no_file_deletion_performed is True
    assert OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED in _codes(vm)


def test_conflict_shared_stack_row_preserves_builtins_win_policy() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        conflicts=(
            OptionalSolverPluginManifestExportSummaryConflictRow(
                stack_id="gmsh",
                built_in_source_id="builtin",
                user_or_plugin_source_id="user",
            ),
        ),
        acknowledgements=_all_acks(),
    )
    row = vm.conflict_rows[0]
    assert row.built_ins_win_by_default is True
    assert row.conflict_visible is True
    assert row.exported_state_does_not_override_builtin is True
    assert vm.header.readiness == "blocked_conflict"
    assert OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED in _codes(vm)


def test_unsafe_claim_row_remains_blocked_and_not_accepted() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.unsafe_claim_blocked(
        claim_text="validated and ready to close issue"
    )
    row = vm.unsafe_claim_rows[0]
    assert row.blocked is True
    assert row.accepted_by_export_summary is False
    assert vm.header.readiness == "blocked_unsafe_claim"
    assert OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM in _codes(vm)


def test_evidence_history_row_retains_history_and_skipped_missing() -> None:
    vm = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(_source(source_reference_display="plugin.json"),),
        evidence_history=(
            OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow(
                stack_id="gmsh",
                deactivation_history_retained=True,
                reactivation_history_retained=True,
                historical_validation_evidence_retained=True,
                skipped_missing_remains_skipped_missing=True,
            ),
        ),
        acknowledgements=_all_acks(),
    )
    row = vm.evidence_history_rows[0]
    assert row.deactivation_history_retained is True
    assert row.reactivation_history_retained is True
    assert row.historical_validation_evidence_retained is True
    assert row.skipped_missing_remains_skipped_missing is True
    assert row.issue_closure_implied is False
    assert row.validation_success_claimed is False
    assert row.validation_failure_claimed is False
    assert row.evidence_deleted_or_rewritten is False


def test_limitation_rows_are_visible_and_counts_are_deterministic() -> None:
    first = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(_source(source_reference_display="plugin.json"),),
        limitations=(
            OptionalSolverPluginManifestExportSummaryLimitationRow(
                limitation_id="custom",
                title="Custom",
                message="Custom limitation.",
            ),
        ),
        acknowledgements=_all_acks(),
    )
    second = OptionalSolverPluginManifestExportSummaryViewModel.from_records(
        sources=(_source(source_reference_display="plugin.json"),),
        limitations=(
            OptionalSolverPluginManifestExportSummaryLimitationRow(
                limitation_id="custom",
                title="Custom",
                message="Custom limitation.",
            ),
        ),
        acknowledgements=_all_acks(),
    )
    assert all(row.must_show for row in first.limitation_rows)
    assert first.header.limitations_count == second.header.limitations_count
    assert first.header.diagnostic_count == second.header.diagnostic_count


def test_in_memory_text_and_mapping_render_without_export_file_creation() -> None:
    vm = _ready_vm()
    lines = vm.to_text_lines()
    mapping = vm.to_mapping()
    rendered = render_optional_solver_plugin_manifest_export_summary(vm)
    assert any("no file export" in line for line in lines)
    assert mapping == rendered
    assert mapping["header"]["export_file_created"] is False
    assert mapping["non_action_flags"]["export_file_created"] is False
    assert mapping["not_validation_evidence"] is True


def test_non_action_flags_are_all_false() -> None:
    vm = _ready_vm()
    flags = vm.non_action_flags
    for slot in flags.__slots__:
        assert getattr(flags, slot) is False, slot


def test_action_states_disable_or_mark_unsafe_future_actions() -> None:
    vm = _ready_vm()
    by_action = {state.action: state for state in vm.actions}
    for action in (
        OptionalSolverPluginManifestExportSummaryAction.WRITE_EXPORT_FILE,
        OptionalSolverPluginManifestExportSummaryAction.COPY_TO_CLIPBOARD,
        OptionalSolverPluginManifestExportSummaryAction.ATTACH_TO_REPORT,
        OptionalSolverPluginManifestExportSummaryAction.CREATE_RELOADABLE_BUNDLE,
        OptionalSolverPluginManifestExportSummaryAction.PERSIST_STATE,
        OptionalSolverPluginManifestExportSummaryAction.RELOAD_STATE,
        OptionalSolverPluginManifestExportSummaryAction.MUTATE_PROJECT_SCHEMA,
        OptionalSolverPluginManifestExportSummaryAction.RUN_DISCOVERY,
        OptionalSolverPluginManifestExportSummaryAction.RUN_VALIDATION,
        OptionalSolverPluginManifestExportSummaryAction.INSTALL_DEPENDENCY,
        OptionalSolverPluginManifestExportSummaryAction.UNINSTALL_DEPENDENCY,
        OptionalSolverPluginManifestExportSummaryAction.UNINSTALL_SOLVER,
        OptionalSolverPluginManifestExportSummaryAction.EXECUTE_SOLVER,
        OptionalSolverPluginManifestExportSummaryAction.CLOSE_ISSUE,
        OptionalSolverPluginManifestExportSummaryAction.MUTATE_RELEASE,
        OptionalSolverPluginManifestExportSummaryAction.PUSH_TAG,
        OptionalSolverPluginManifestExportSummaryAction.UPLOAD_ASSET,
    ):
        assert by_action[action].enabled is False
        assert by_action[action].future_action is True
    assert by_action[
        OptionalSolverPluginManifestExportSummaryAction.REVIEW_EXPORT_SUMMARY
    ].enabled is True


def test_from_persistence_viewmodel_consumes_supplied_records_without_mutation() -> None:
    persistence_vm = build_optional_solver_plugin_manifest_persistence_viewmodel(
        (
            OptionalSolverPluginManifestPersistenceCandidateInput(
                stack_id="gmsh",
                source_reference="C:/private/plugin.json",
                persistence_requested=True,
            ),
        ),
        acknowledgements={ack: True for ack in PERSISTENCE_REQUIRED_ACKS},
        persistence_requested=True,
        schema=OptionalSolverPluginManifestPersistenceSchemaInput(
            schema_version_display="osw-exp-092-preview",
            schema_version_present=True,
        ),
    )
    before = persistence_vm.candidate_rows[0].source_reference_display
    export_vm = OptionalSolverPluginManifestExportSummaryViewModel.from_persistence_viewmodel(
        persistence_vm,
        acknowledgements=_all_acks(),
    )
    assert persistence_vm.candidate_rows[0].source_reference_display == before
    assert export_vm.candidate_rows[0].stack_id == "gmsh"
    assert export_vm.candidate_rows[0].persistence_state


def test_from_persistence_schema_model_consumes_supplied_records_without_mutation() -> None:
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
                acknowledgement_id="export_not_validation",
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
    export_vm = OptionalSolverPluginManifestExportSummaryViewModel.from_persistence_schema_model(
        schema_model,
        acknowledgements=_all_acks(),
    )
    assert schema_model.sources[0].source_reference_display == before
    assert export_vm.source_rows[0].source_id == "s1"
    assert export_vm.candidate_rows[0].stack_id == "gmsh"
    assert export_vm.unsafe_claim_rows[0].accepted_by_export_summary is False


def test_redaction_helper_returns_basename_only() -> None:
    display, redacted = redact_optional_solver_plugin_manifest_export_summary_source_reference(
        "C:/secret/path/plugin.json"
    )
    assert display == "plugin.json"
    assert redacted is True


def test_docs_mention_non_actions_and_future_gates() -> None:
    doc = DOC.read_text(encoding="utf-8").lower()
    design = DESIGN_DOC.read_text(encoding="utf-8").lower()
    for phrase in (
        "pure",
        "side-effect-free",
        "no file export",
        "no file writes",
        "no clipboard",
        "no report attachment",
        "no reloadable bundle",
        "no persistence writer",
        "no gui behavior",
        "no cli behavior",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "no issue closure",
        "no release mutation",
        "future gate",
    ):
        assert phrase in doc
    assert "osw-exp-097" in design
