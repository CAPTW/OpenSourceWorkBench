from __future__ import annotations

import ast
import importlib
from pathlib import Path

from osw.experimental.optional_solvers import (
    PERSISTENCE_REQUIRED_ACKS,
    OptionalSolverPluginManifestActivationCandidateInput,
    OptionalSolverPluginManifestDeactivationCandidateInput,
    OptionalSolverPluginManifestDiscoveryRefreshSourceInput,
    OptionalSolverPluginManifestPersistenceAction,
    OptionalSolverPluginManifestPersistenceReadiness,
    OptionalSolverPluginManifestReactivationCandidateInput,
    build_optional_solver_plugin_manifest_activation_viewmodel,
    build_optional_solver_plugin_manifest_deactivation_viewmodel,
    build_optional_solver_plugin_manifest_discovery_refresh_viewmodel,
    build_optional_solver_plugin_manifest_reactivation_viewmodel,
    redact_optional_solver_plugin_manifest_persistence_source_reference,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceCandidateInput as Cand,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceSchemaInput as Schema,
)
from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestPersistenceViewModel as VM,
)
from osw.experimental.optional_solvers import (
    build_optional_solver_plugin_manifest_persistence_viewmodel as build,
)
from osw.experimental.optional_solvers import (
    plugin_manifest_persistence_viewmodel as module_under_test,
)
from osw.experimental.optional_solvers import (
    render_optional_solver_plugin_manifest_persistence_summary as render_summary,
)
from osw.experimental.optional_solvers import (
    summarize_optional_solver_plugin_manifest_persistence_viewmodel as summarize,
)
from osw.experimental.optional_solvers.plugin_manifest_persistence_viewmodel import (
    ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD,
    ACK_LOCAL_PATH_REDACTION_REVIEWED,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
    ACK_PERSISTENCE_NO_SOLVER_EXECUTION,
    ACK_PERSISTENCE_NOT_INSTALL,
    ACK_PERSISTENCE_NOT_ISSUE_CLOSURE,
    ACK_PERSISTENCE_NOT_RELEASE_MUTATION,
    ACK_PERSISTENCE_NOT_TRUST_RESTORATION,
    ACK_PERSISTENCE_NOT_VALIDATION,
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
    ACK_TRUST_LABEL_NOT_CERTIFICATION,
    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
    OSPMG_PERSISTENCE_ACK_REQUIRED,
    OSPMG_PERSISTENCE_CONFLICT_BLOCKED,
    OSPMG_PERSISTENCE_EVIDENCE_RETAINED,
    OSPMG_PERSISTENCE_FUTURE_GATE,
    OSPMG_PERSISTENCE_HISTORY_RETAINED,
    OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION,
    OSPMG_PERSISTENCE_NO_INSTALL,
    OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT,
    OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION,
    OSPMG_PERSISTENCE_NOT_IMPLEMENTED,
    OSPMG_PERSISTENCE_NOT_VALIDATION,
    OSPMG_PERSISTENCE_REDACTION_REQUIRED,
    OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED,
    OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED,
    OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED,
    OSPMG_PERSISTENCE_UNSAFE_CLAIM,
    OSPMG_PERSISTENCE_UNTRUSTED_SOURCE,
)

_ALL_ACKS = {ack: True for ack in PERSISTENCE_REQUIRED_ACKS}
_SCHEMA = Schema(
    schema_version_display="osw-exp-092-preview",
    schema_version_present=True,
)
_Readiness = OptionalSolverPluginManifestPersistenceReadiness

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_persistence_viewmodel.md"
)


def _codes(view_model) -> set[str]:
    return {d.code for d in view_model.diagnostics}


def _candidate(**kwargs) -> Cand:
    base = {"stack_id": "user_stack"}
    base.update(kwargs)
    return Cand(**base)


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


def test_module_imports_without_gui_extras() -> None:
    module = importlib.import_module(
        "osw.experimental.optional_solvers.plugin_manifest_persistence_viewmodel"
    )
    vm = build(
        [_candidate()],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    assert hasattr(module, "OptionalSolverPluginManifestPersistenceViewModel")
    assert "persistence" in summarize(vm).lower()


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
        ".exists(",
        "open(",
        "ProjectSchema(",
        "load_optional_solver_plugin_manifest_json",
    ):
        assert phrase not in source


def test_unavailable_without_supplied_state() -> None:
    vm = VM.unavailable()
    assert vm.summary.readiness == _Readiness.UNAVAILABLE_NO_STATE.value
    assert vm.summary.persistence_state == "persistence_unavailable"
    assert vm.summary.candidate_count == 0
    assert vm.summary.source_count == 0
    assert vm.summary.persistence_performed is False
    assert vm.summary.file_write_performed is False
    assert vm.summary.settings_file_created is False
    assert vm.summary.project_schema_mutation_performed is False
    assert OSPMG_PERSISTENCE_NOT_IMPLEMENTED in _codes(vm)


def test_explicit_request_is_required() -> None:
    vm = build([_candidate()], acknowledgements=_ALL_ACKS, schema=_SCHEMA)
    assert vm.summary.readiness == _Readiness.UNAVAILABLE_NO_EXPLICIT_REQUEST.value
    assert vm.summary.persistence_state == "persistence_unavailable"


def test_candidate_is_untrusted_and_redacted_by_default() -> None:
    vm = build(
        [_candidate(source_reference="C:/secret/path/manifest.json")],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    row = vm.candidate_rows[0]
    assert row.is_untrusted is True
    assert row.redacted_source_reference is True
    assert row.source_reference_display == "manifest.json"
    assert "/" not in row.source_reference_display
    assert chr(92) not in row.source_reference_display
    assert OSPMG_PERSISTENCE_UNTRUSTED_SOURCE in _codes(vm)


def test_required_acknowledgements_are_visible() -> None:
    vm = build([_candidate()], acknowledgements={}, persistence_requested=True, schema=_SCHEMA)
    ack_ids = {row.acknowledgement_id for row in vm.acknowledgement_rows}
    for ack in (
        ACK_PERSISTENCE_NOT_VALIDATION,
        ACK_PERSISTENCE_NOT_TRUST_RESTORATION,
        ACK_PERSISTENCE_NOT_INSTALL,
        ACK_PERSISTENCE_NO_SOLVER_EXECUTION,
        ACK_PERSISTENCE_NOT_ISSUE_CLOSURE,
        ACK_PERSISTENCE_NOT_RELEASE_MUTATION,
        ACK_LOCAL_PATH_REDACTION_REVIEWED,
        ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
        ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
        ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
        ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD,
        ACK_NO_DISCOVERY_EXECUTION,
        ACK_NO_PLUGIN_PACKAGE_IMPORT,
        ACK_TRUST_LABEL_NOT_CERTIFICATION,
    ):
        assert ack in ack_ids
    assert ack_ids == set(PERSISTENCE_REQUIRED_ACKS)


def test_missing_acknowledgements_block_readiness() -> None:
    vm = build([_candidate()], acknowledgements={}, persistence_requested=True, schema=_SCHEMA)
    assert vm.summary.readiness == _Readiness.BLOCKED_ACKNOWLEDGEMENT.value
    assert OSPMG_PERSISTENCE_ACK_REQUIRED in _codes(vm)
    assert any(row.blocking for row in vm.acknowledgement_rows)


def test_satisfied_acknowledgements_allow_ready_preview_only() -> None:
    vm = build(
        [_candidate()],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    assert vm.summary.readiness == _Readiness.READY_PREVIEW_ONLY.value
    assert vm.summary.persistence_state == "persistence_ready_preview"
    assert vm.summary.persistence_ready_count == 1
    assert vm.summary.persistence_performed is False
    assert vm.summary.automatic_activation_performed is False
    assert vm.summary.trust_restoration_performed is False
    assert vm.summary.file_write_performed is False
    assert vm.summary.export_performed is False


def test_redaction_review_and_unredacted_paths_block() -> None:
    no_redaction_ack = {
        ack: value for ack, value in _ALL_ACKS.items()
        if ack != ACK_LOCAL_PATH_REDACTION_REVIEWED
    }
    vm = build(
        [
            _candidate(
                source_reference="C:/private/manifest.json",
                redaction_required=True,
                redaction_status="review_required",
            )
        ],
        acknowledgements=no_redaction_ack,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    assert vm.summary.readiness == _Readiness.BLOCKED_REDACTION_REVIEW.value
    assert OSPMG_PERSISTENCE_REDACTION_REQUIRED in _codes(vm)
    assert vm.redaction_rows[0].display_reference == "manifest.json"

    blocked = build(
        [
            _candidate(
                source_reference="C:/private/manifest.json",
                unredacted_path_supplied=True,
            )
        ],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    assert blocked.summary.readiness == _Readiness.BLOCKED_UNREDACTED_PATH.value
    assert OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED in _codes(blocked)


def test_redaction_helper_does_not_inspect_paths() -> None:
    display, redacted = redact_optional_solver_plugin_manifest_persistence_source_reference(
        "C:/private/manifest.json"
    )
    assert (display, redacted) == ("manifest.json", True)
    assert redact_optional_solver_plugin_manifest_persistence_source_reference(
        "C:/private/manifest.json",
        provided_label="selected manifest",
    ) == ("selected manifest", False)


def test_schema_version_and_migration_block() -> None:
    no_schema = build(
        [_candidate()],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
    )
    assert no_schema.summary.readiness == _Readiness.BLOCKED_SCHEMA_VERSION.value
    assert OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED in _codes(no_schema)
    assert no_schema.schema_migration_rows[0].this_gate_creates_no_schema_file is True

    migration = build(
        [_candidate()],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=Schema(
            schema_version_display="future",
            schema_version_present=True,
            migration_required=True,
            migration_status="required",
        ),
    )
    assert migration.summary.readiness == _Readiness.BLOCKED_SCHEMA_MIGRATION.value
    assert OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED in _codes(migration)


def test_stale_source_conflict_shared_stack_and_unsafe_claims_block() -> None:
    stale = build(
        [_candidate(stale_source=True, source_reference="C:/moved/manifest.json")],
        acknowledgements={
            ack: value for ack, value in _ALL_ACKS.items()
            if ack != ACK_STALE_SOURCE_REQUIRES_REPREVIEW
        },
        persistence_requested=True,
        schema=_SCHEMA,
    )
    assert stale.summary.readiness == _Readiness.BLOCKED_STALE_SOURCE_REPREVIEW.value
    assert OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED in _codes(stale)
    assert stale.stale_source_rows[0].file_io_performed is False

    conflict = build(
        [_candidate(has_conflict=True)],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    assert conflict.summary.readiness == _Readiness.BLOCKED_CONFLICT.value
    assert OSPMG_PERSISTENCE_CONFLICT_BLOCKED in _codes(conflict)
    assert conflict.conflict_rows[0].built_ins_win_default is True

    shared = build(
        [_candidate(has_shared_stack=True)],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    assert shared.summary.readiness == _Readiness.BLOCKED_SHARED_STACK_WARNING.value
    assert shared.conflict_rows[0].built_ins_win_default is True

    unsafe = build(
        [_candidate(has_unsafe_claim=True, unsafe_claim_indicators=("certified",))],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    assert unsafe.summary.readiness == _Readiness.BLOCKED_UNSAFE_CLAIM.value
    assert OSPMG_PERSISTENCE_UNSAFE_CLAIM in _codes(unsafe)
    assert unsafe.unsafe_claim_rows[0].blocked is True


def test_evidence_history_and_trust_badges_are_retained_not_validating() -> None:
    vm = build(
        [
            _candidate(
                historical_evidence_state="skipped_missing",
                deactivation_history_state="deactivated_by_user",
                reactivation_history_state="not_reactivated",
            )
        ],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    assert OSPMG_PERSISTENCE_EVIDENCE_RETAINED in _codes(vm)
    assert OSPMG_PERSISTENCE_HISTORY_RETAINED in _codes(vm)
    row = vm.evidence_history_rows[0]
    assert row.historical_evidence_state == "skipped_missing"
    assert "not validation success" in row.persisted_state_not_validation_success.lower()
    assert "not validation failure" in row.persisted_state_not_validation_failure.lower()
    assert "issue closure" in row.issue_closure_not_implied_text.lower()
    assert vm.trust_badges
    assert all(
        "not certification" in badge.trust_label_is_not_certification.lower()
        for badge in vm.trust_badges
    )


def test_diagnostic_vocabulary_and_future_gate_non_actions_are_surfaced() -> None:
    vm = build(
        [_candidate()],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    codes = _codes(vm)
    for code in (
        OSPMG_PERSISTENCE_NOT_IMPLEMENTED,
        OSPMG_PERSISTENCE_NOT_VALIDATION,
        OSPMG_PERSISTENCE_NO_INSTALL,
        OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION,
        OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION,
        OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT,
        OSPMG_PERSISTENCE_FUTURE_GATE,
    ):
        assert code in codes
    assert any("No file writes." == text for text in vm.safety_text)
    assert any("No ProjectSchema mutation." == text for text in vm.safety_text)


def test_future_write_and_schema_review_states_are_future_only() -> None:
    write = build(
        [_candidate()],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
        future_write_required=True,
    )
    assert write.summary.readiness == _Readiness.FUTURE_WRITE_REQUIRED.value
    assert write.summary.persistence_state == "persistence_future_write_required"

    review = VM.schema_review_required([_candidate()])
    assert review.summary.readiness == _Readiness.SCHEMA_REVIEW_REQUIRED.value
    assert review.summary.persistence_state == "persistence_schema_review_required"


def test_action_states_disable_unsafe_and_future_actions() -> None:
    vm = build(
        [_candidate()],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    actions = {state.action.value: state for state in vm.actions}
    for action in (
        OptionalSolverPluginManifestPersistenceAction.SAVE_STATE.value,
        OptionalSolverPluginManifestPersistenceAction.CREATE_SETTINGS_FILE.value,
        OptionalSolverPluginManifestPersistenceAction.MUTATE_PROJECT_SCHEMA.value,
        OptionalSolverPluginManifestPersistenceAction.RELOAD_STATE.value,
        OptionalSolverPluginManifestPersistenceAction.EXPORT_SUMMARY.value,
        OptionalSolverPluginManifestPersistenceAction.CREATE_RELOADABLE_BUNDLE.value,
        OptionalSolverPluginManifestPersistenceAction.AUTOMATIC_ACTIVATION.value,
        OptionalSolverPluginManifestPersistenceAction.TRUST_RESTORATION.value,
        OptionalSolverPluginManifestPersistenceAction.RUN_DISCOVERY.value,
        OptionalSolverPluginManifestPersistenceAction.RUN_VALIDATION.value,
        OptionalSolverPluginManifestPersistenceAction.INSTALL_DEPENDENCY.value,
        OptionalSolverPluginManifestPersistenceAction.UNINSTALL_DEPENDENCY.value,
        OptionalSolverPluginManifestPersistenceAction.UNINSTALL_SOLVER.value,
        OptionalSolverPluginManifestPersistenceAction.EXECUTE_SOLVER.value,
        OptionalSolverPluginManifestPersistenceAction.CLOSE_ISSUE.value,
        OptionalSolverPluginManifestPersistenceAction.MUTATE_RELEASE.value,
    ):
        assert actions[action].enabled is False
        assert actions[action].available is False
    assert all(not state.enabled for state in vm.actions)


def test_render_summary_is_in_memory_redacted_and_honest(tmp_path: Path) -> None:
    vm = build(
        [_candidate(source_reference="C:/private/manifest.json")],
        acknowledgements=_ALL_ACKS,
        persistence_requested=True,
        schema=_SCHEMA,
    )
    payload = render_summary(vm)
    for flag in (
        "persistence_performed",
        "file_write_performed",
        "settings_file_created",
        "project_schema_mutation_performed",
        "automatic_activation_performed",
        "trust_restoration_performed",
        "dependency_installation_performed",
        "dependency_uninstall_performed",
        "solver_execution_performed",
        "discovery_execution_performed",
        "validation_execution_performed",
        "plugin_package_import_performed",
        "directory_scan_performed",
        "network_fetch_performed",
        "export_performed",
        "reload_performed",
        "reloadable_bundle_created",
        "file_restore_performed",
        "file_rewrite_performed",
        "file_deletion_performed",
        "solver_uninstall_performed",
        "issue_mutation_performed",
        "issue_closure_claimed",
        "release_mutation_performed",
        "tag_mutation_performed",
        "asset_mutation_performed",
        "version_bump_performed",
        "validation_pass_claimed",
        "validation_fail_claimed",
        "certification_claimed",
        "third_party_manifests_trusted_by_default",
    ):
        assert payload[flag] is False
    assert payload["not_validation_evidence"] is True
    assert payload["candidates"][0]["source_reference_display"] == "manifest.json"
    assert list(tmp_path.iterdir()) == []


def test_existing_viewmodel_adapters_are_non_mutating() -> None:
    activation = build_optional_solver_plugin_manifest_activation_viewmodel(
        [OptionalSolverPluginManifestActivationCandidateInput(stack_id="a")],
        active_stack_ids=["a"],
    )
    deactivation = build_optional_solver_plugin_manifest_deactivation_viewmodel(
        [OptionalSolverPluginManifestDeactivationCandidateInput(stack_id="d")]
    )
    reactivation = build_optional_solver_plugin_manifest_reactivation_viewmodel(
        [OptionalSolverPluginManifestReactivationCandidateInput(stack_id="r")],
        acknowledgements={},
    )
    discovery = build_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
        [OptionalSolverPluginManifestDiscoveryRefreshSourceInput(stack_id="s")]
    )
    before = (
        activation.candidate_rows,
        deactivation.candidate_rows,
        reactivation.candidate_rows,
        discovery.source_rows,
    )
    for vm in (
        VM.from_activation_viewmodel(
            activation,
            acknowledgements=_ALL_ACKS,
            persistence_requested=True,
            schema=_SCHEMA,
        ),
        VM.from_deactivation_viewmodel(
            deactivation,
            acknowledgements=_ALL_ACKS,
            persistence_requested=True,
            schema=_SCHEMA,
        ),
        VM.from_reactivation_viewmodel(
            reactivation,
            acknowledgements=_ALL_ACKS,
            persistence_requested=True,
            schema=_SCHEMA,
        ),
        VM.from_discovery_refresh_viewmodel(
            discovery,
            acknowledgements=_ALL_ACKS,
            persistence_requested=True,
            schema=_SCHEMA,
        ),
    ):
        assert vm.summary.readiness in {
            _Readiness.READY_PREVIEW_ONLY.value,
            _Readiness.BLOCKED_STALE_SOURCE_REPREVIEW.value,
            _Readiness.BLOCKED_ACKNOWLEDGEMENT.value,
        }
    assert before == (
        activation.candidate_rows,
        deactivation.candidate_rows,
        reactivation.candidate_rows,
        discovery.source_rows,
    )


def test_docs_mention_non_actions_relationships_and_future_gates() -> None:
    assert DOC.exists()
    text = " ".join(DOC.read_text(encoding="utf-8").lower().split())
    for phrase in (
        "non-actions",
        "future gates",
        "relationship to osw-exp-090 design",
        "relationship to activation/deactivation/reactivation/discovery-refresh",
        "relationship to gui and cli",
        "relationship to projectschema",
        "relationship to export-summary design",
        "relationship to live optional validation issues",
        "no persistence implementation",
        "no file writes",
        "no settings file creation",
        "no automatic activation",
        "no trust restoration",
        "no discovery execution",
        "no validation execution",
        "no solver execution",
        "trust label is not certification",
    ):
        assert phrase in text, phrase
