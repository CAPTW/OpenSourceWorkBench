from __future__ import annotations

import ast
import copy
import importlib
import json
from pathlib import Path

import pytest

from osw.experimental.optional_solvers import (
    OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW,
    OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_DIAGNOSTIC_CODES,
    OSPMG_RELOAD_ACCEPTANCE_ERROR,
    OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_NOT_REQUESTED,
    OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED,
    OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING,
    OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_READY,
    OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED,
    OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED,
    OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED,
    OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED,
    RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS,
    RELOAD_ACCEPTANCE_REQUIRED_ACKS,
    OptionalSolverPluginManifestReloadAcceptanceViewModel,
    OptionalSolverPluginManifestReloadViewModel,
    ReloadAcceptanceAction,
    ReloadAcceptanceReadiness,
    ReloadAcceptanceState,
    all_reload_acceptance_acknowledgements,
    build_optional_solver_plugin_manifest_reload_acceptance_viewmodel,
    render_optional_solver_plugin_manifest_reload_acceptance_viewmodel,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "osw" / "experimental" / "optional_solvers" / (
    "plugin_manifest_reload_acceptance_viewmodel.py"
)


def _ready_reload() -> OptionalSolverPluginManifestReloadViewModel:
    return OptionalSolverPluginManifestReloadViewModel.sample_ready_for_review()


def _ready_acceptance() -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    return OptionalSolverPluginManifestReloadAcceptanceViewModel.ready_for_future_acceptance(
        _ready_reload()
    )


def _codes(
    view_model: OptionalSolverPluginManifestReloadAcceptanceViewModel,
) -> set[str]:
    return {row.code for row in view_model.diagnostics}


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
        "osw.experimental.optional_solvers.plugin_manifest_reload_acceptance_viewmodel"
    )
    assert hasattr(module, "OptionalSolverPluginManifestReloadAcceptanceViewModel")
    assert hasattr(module, "ReloadAcceptanceState")
    assert hasattr(module, "ReloadAcceptanceReadiness")
    assert hasattr(module, "ReloadAcceptanceAction")
    assert hasattr(module, "ReloadAcceptanceSummary")
    assert hasattr(module, "ReloadAcceptanceAcknowledgementRow")
    assert hasattr(module, "ReloadAcceptanceDiagnostic")
    assert hasattr(module, "ReloadAcceptanceBlockerRow")
    assert hasattr(module, "ReloadAcceptanceActionState")
    assert hasattr(module, "ReloadAcceptanceAcceptedStateRow")
    assert hasattr(module, "ReloadAcceptanceSourceProvenanceRow")
    assert hasattr(module, "ReloadAcceptanceEvidenceHistoryRow")
    assert hasattr(module, "ReloadAcceptanceTrustBadge")
    assert all_reload_acceptance_acknowledgements() == RELOAD_ACCEPTANCE_REQUIRED_ACKS


def test_module_imports_avoid_gui_cli_reader_file_io_and_execution_paths() -> None:
    imports = _imported_modules() - {"__future__"}
    assert imports == {
        "collections.abc",
        "dataclasses",
        "enum",
        "plugin_manifest_reload_viewmodel",
    }
    forbidden_imports = {
        "pathlib",
        "os",
        "shutil",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "osw.cli",
        "pyside6",
        "pyqt6",
        "plugin_manifest_reload_file_reader",
    }
    assert imports.isdisjoint(forbidden_imports)
    forbidden_calls = {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "glob",
        "iterdir",
        "discover_optional_solver_manifests",
        "validate_optional_solver_manifest",
        "execute_solver",
    }
    assert _called_names().isdisjoint(forbidden_calls)


def test_unavailable_no_preview_blocks_acceptance_action() -> None:
    view_model = OptionalSolverPluginManifestReloadAcceptanceViewModel.unavailable()
    assert view_model.summary.state == ReloadAcceptanceState.NO_PREVIEW
    assert view_model.summary.readiness == (
        ReloadAcceptanceReadiness.UNAVAILABLE_NO_PREVIEW
    )
    assert OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING in _codes(view_model)
    assert view_model.summary.preview_available is False
    assert all(action.enabled is False for action in view_model.action_states)


def test_preview_exists_but_acceptance_not_requested_is_review_only() -> None:
    view_model = OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        _ready_reload()
    )
    assert view_model.summary.state == ReloadAcceptanceState.NOT_REQUESTED
    assert view_model.summary.readiness == ReloadAcceptanceReadiness.NOT_REQUESTED
    assert OSPMG_RELOAD_ACCEPTANCE_NOT_REQUESTED in _codes(view_model)
    assert view_model.summary.preview_available is True
    assert view_model.summary.ready_for_future_acceptance is False
    assert all(row.blocker is False for row in view_model.acknowledgement_rows)


def test_missing_acknowledgements_block_requested_acceptance() -> None:
    view_model = OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        _ready_reload(),
        requested=True,
        acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS[:-1],
    )
    assert view_model.summary.readiness == (
        ReloadAcceptanceReadiness.BLOCKED_ACKNOWLEDGEMENT
    )
    assert OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED in _codes(view_model)
    assert view_model.summary.missing_acknowledgement_count == 1
    assert view_model.acknowledgement_rows[-1].blocker is True


def test_all_acknowledgements_ready_but_future_only_no_side_effects() -> None:
    view_model = _ready_acceptance()
    assert view_model.summary.state == (
        ReloadAcceptanceState.READY_FOR_FUTURE_ACCEPTANCE
    )
    assert view_model.summary.readiness == ReloadAcceptanceReadiness.READY_FUTURE_ONLY
    assert view_model.summary.ready_for_future_acceptance is True
    assert OSPMG_RELOAD_ACCEPTANCE_READY in _codes(view_model)
    assert all(row.satisfied is True for row in view_model.acknowledgement_rows)
    assert all(action.enabled is False for action in view_model.action_states)
    assert all(action.future_only is True for action in view_model.action_states)


def test_accepted_for_session_review_is_representation_only_and_untrusted() -> None:
    view_model = (
        OptionalSolverPluginManifestReloadAcceptanceViewModel.accepted_for_session_review(
            _ready_reload()
        )
    )
    assert view_model.summary.state == ReloadAcceptanceState.ACCEPTED_FOR_SESSION_REVIEW
    assert view_model.summary.readiness == (
        ReloadAcceptanceReadiness.ACCEPTED_FOR_SESSION_REVIEW
    )
    assert OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW in _codes(view_model)
    accepted = view_model.accepted_state_rows[0]
    assert accepted.accepted_for_session_review is True
    assert accepted.scope == "session_review_only"
    assert accepted.untrusted_by_default is True
    assert accepted.persisted_state is False
    assert accepted.project_schema_state is False
    assert accepted.validation_evidence is False
    assert accepted.validation_failure is False
    assert accepted.automatic_activation is False
    assert accepted.trust_restoration is False


def test_reader_blocked_input_blocks_acceptance_without_reader_invocation() -> None:
    view_model = OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        _ready_reload(),
        requested=True,
        acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
        reader_diagnostics=("OSPMG_RELOAD_READER_FILE_MISSING",),
    )
    assert view_model.summary.readiness == ReloadAcceptanceReadiness.BLOCKED_READER
    assert OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED in _codes(view_model)


def test_viewmodel_blocked_input_blocks_acceptance() -> None:
    reload_view_model = OptionalSolverPluginManifestReloadViewModel.blocked(
        diagnostics=("OSPMG_RELOAD_CUSTOM_BLOCKER",)
    )
    view_model = OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        reload_view_model,
        requested=True,
        acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
    )
    assert view_model.summary.readiness == ReloadAcceptanceReadiness.BLOCKED_VIEWMODEL
    assert OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED in _codes(view_model)


@pytest.mark.parametrize(
    ("flag", "expected_code", "expected_readiness"),
    [
        (
            "stale_source_requires_repreview",
            OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED,
            ReloadAcceptanceReadiness.BLOCKED_STALE_SOURCE_REPREVIEW,
        ),
        (
            "conflict_review_required",
            OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED,
            ReloadAcceptanceReadiness.BLOCKED_CONFLICT_REVIEW,
        ),
        (
            "shared_stack_review_required",
            OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED,
            ReloadAcceptanceReadiness.BLOCKED_SHARED_STACK_REVIEW,
        ),
        (
            "unsafe_claim_blocked",
            OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED,
            ReloadAcceptanceReadiness.BLOCKED_UNSAFE_CLAIM,
        ),
        (
            "unsupported_schema",
            OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED,
            ReloadAcceptanceReadiness.BLOCKED_SCHEMA_UNSUPPORTED,
        ),
        (
            "migration_required",
            OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED,
            ReloadAcceptanceReadiness.BLOCKED_MIGRATION_REQUIRED,
        ),
        (
            "unredacted_path_blocked",
            OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED,
            ReloadAcceptanceReadiness.BLOCKED_UNREDACTED_PATH,
        ),
        (
            "secret_like_value_blocked",
            OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED,
            ReloadAcceptanceReadiness.BLOCKED_SECRET_LIKE_VALUE,
        ),
        (
            "trust_policy_changed",
            OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED,
            ReloadAcceptanceReadiness.BLOCKED_POLICY_CHANGE,
        ),
        (
            "source_fingerprint_changed",
            OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED,
            ReloadAcceptanceReadiness.BLOCKED_POLICY_CHANGE,
        ),
        (
            "policy_changed",
            OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED,
            ReloadAcceptanceReadiness.BLOCKED_POLICY_CHANGE,
        ),
    ],
)
def test_policy_and_preview_blockers_are_mapped_to_acceptance_diagnostics(
    flag: str,
    expected_code: str,
    expected_readiness: ReloadAcceptanceReadiness,
) -> None:
    view_model = OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        _ready_reload(),
        requested=True,
        acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
        policy_flags={flag: True},
    )
    assert view_model.summary.readiness == expected_readiness
    assert expected_code in _codes(view_model)
    assert view_model.blocker_rows[0].blocks_acceptance is True


def test_future_activation_and_discovery_review_requirements_are_visible() -> None:
    mapping = copy.deepcopy(_ready_reload().to_mapping())
    mapping["candidates"] = [
        {
            "candidate_id": "active",
            "requires_future_activation_review": True,
        },
        {
            "candidate_id": "refresh",
            "requires_future_discovery_refresh": True,
        },
    ]
    view_model = OptionalSolverPluginManifestReloadAcceptanceViewModel.from_preview_mapping(
        mapping,
        requested=True,
        acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
    )
    assert OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED in _codes(
        view_model
    )
    assert OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED in _codes(
        view_model
    )
    assert view_model.summary.future_activation_review_required is True
    assert view_model.summary.future_discovery_refresh_required is True


def test_acknowledgements_and_expiry_reasons_are_deterministic() -> None:
    view_model = OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        _ready_reload(),
        requested=True,
        acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
        expired_acknowledgements=(RELOAD_ACCEPTANCE_REQUIRED_ACKS[0],),
    )
    assert view_model.summary.readiness == (
        ReloadAcceptanceReadiness.BLOCKED_ACKNOWLEDGEMENT
    )
    first = view_model.acknowledgement_rows[0]
    assert first.expired is True
    assert first.blocker is True
    assert first.expiry_reasons == RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS
    assert "validation_issue_state_change" in first.expiry_reasons


def test_candidate_lifecycle_trust_and_evidence_remain_review_only() -> None:
    view_model = _ready_acceptance()
    assert view_model.source_provenance_rows
    assert view_model.trust_badges
    assert all(row.trust_restored is False for row in view_model.trust_badges)
    assert all(row.trust_label_is_certification is False for row in view_model.trust_badges)
    assert all(row.certification_claimed is False for row in view_model.trust_badges)
    assert view_model.evidence_history_rows
    assert all(row.retained_reference_only is True for row in view_model.evidence_history_rows)
    assert all(row.not_validation_evidence is True for row in view_model.evidence_history_rows)
    assert all(row.issue_closure_implied is False for row in view_model.evidence_history_rows)


def test_non_action_flags_are_all_false() -> None:
    flags = _ready_acceptance().non_action_flags.to_mapping()
    assert flags
    assert set(flags.values()) == {False}
    for key in (
        "implemented_reload_acceptance",
        "runtime_reload_acceptance_performed",
        "persistence_write_performed",
        "project_schema_mutated",
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
        "bundled_solver_claimed",
        "certification_claimed",
    ):
        assert flags[key] is False


def test_disabled_future_action_states_cover_runtime_issue_release_and_claims() -> None:
    actions = {row.action: row for row in _ready_acceptance().action_states}
    for action in (
        ReloadAcceptanceAction.REQUEST_ACCEPTANCE,
        ReloadAcceptanceAction.ACCEPT_FOR_SESSION_REVIEW,
        ReloadAcceptanceAction.ACCEPT_AS_TRUSTED,
        ReloadAcceptanceAction.ACTIVATE_RELOADED_CANDIDATE,
        ReloadAcceptanceAction.REFRESH_DISCOVERY,
        ReloadAcceptanceAction.VALIDATE_SOLVER,
        ReloadAcceptanceAction.EXECUTE_SOLVER,
        ReloadAcceptanceAction.INSTALL_DEPENDENCY,
        ReloadAcceptanceAction.UNINSTALL_DEPENDENCY,
        ReloadAcceptanceAction.UNINSTALL_SOLVER,
        ReloadAcceptanceAction.MUTATE_PROJECT_SCHEMA,
        ReloadAcceptanceAction.PERSIST_STATE,
        ReloadAcceptanceAction.CREATE_EXPORT_SUMMARY,
        ReloadAcceptanceAction.CREATE_REPORT_FILE,
        ReloadAcceptanceAction.CREATE_RELOADABLE_BUNDLE,
        ReloadAcceptanceAction.COPY_TO_CLIPBOARD,
        ReloadAcceptanceAction.ATTACH_TO_REPORT,
        ReloadAcceptanceAction.OPEN_OUTPUT_FOLDER,
        ReloadAcceptanceAction.CLOSE_ISSUE,
        ReloadAcceptanceAction.MUTATE_RELEASE,
        ReloadAcceptanceAction.PUSH_TAG,
        ReloadAcceptanceAction.UPLOAD_ASSET,
        ReloadAcceptanceAction.CLAIM_VALIDATION_SUCCESS,
        ReloadAcceptanceAction.CLAIM_VALIDATION_FAILURE,
        ReloadAcceptanceAction.CLAIM_CERTIFICATION,
    ):
        assert actions[action].enabled is False
        assert actions[action].future_only is True


def test_mapping_and_text_output_are_deterministic_serializable_and_safe() -> None:
    view_model = _ready_acceptance()
    first = view_model.to_mapping()
    second = view_model.to_mapping()
    assert first == second
    json.dumps(first, sort_keys=True)
    assert render_optional_solver_plugin_manifest_reload_acceptance_viewmodel(
        view_model
    ) == view_model.to_text_lines()
    text = "\n".join(view_model.to_text_lines()).lower()
    assert "not validation evidence" in text
    assert "not validation failure" in text
    assert "does not restore trust" in text
    assert "does not mutate projectschema" in text
    assert "certify manifests" in text


def test_reserved_diagnostics_include_full_vocabulary() -> None:
    mapping = _ready_acceptance().to_mapping()
    assert tuple(mapping["reserved_diagnostic_codes"]) == (
        OSPMG_RELOAD_ACCEPTANCE_DIAGNOSTIC_CODES
    )
    assert OSPMG_RELOAD_ACCEPTANCE_READY in _codes(_ready_acceptance())
    assert set(OSPMG_RELOAD_ACCEPTANCE_DIAGNOSTIC_CODES) >= {
        OSPMG_RELOAD_ACCEPTANCE_NOT_REQUESTED,
        OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING,
        OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED,
        OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED,
        OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED,
        OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED,
        OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED,
        OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED,
        OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED,
        OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED,
        OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED,
        OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED,
        OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED,
        OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED,
        OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED,
        OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED,
        OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW,
        OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED,
        OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED,
        OSPMG_RELOAD_ACCEPTANCE_ERROR,
    }


def test_error_state_is_reported_without_exception() -> None:
    view_model = OptionalSolverPluginManifestReloadAcceptanceViewModel.error(
        "synthetic problem"
    )
    assert view_model.summary.state == ReloadAcceptanceState.ERROR
    assert view_model.summary.readiness == ReloadAcceptanceReadiness.ERROR
    assert OSPMG_RELOAD_ACCEPTANCE_ERROR in _codes(view_model)


def test_builder_accepts_input_or_supplied_viewmodel_without_mutating_it() -> None:
    reload_mapping = copy.deepcopy(_ready_reload().to_mapping())
    original = copy.deepcopy(reload_mapping)
    view_model = build_optional_solver_plugin_manifest_reload_acceptance_viewmodel(
        reload_mapping,
        requested=True,
        acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
    )
    assert view_model.summary.readiness == ReloadAcceptanceReadiness.READY_FUTURE_ONLY
    assert reload_mapping == original
