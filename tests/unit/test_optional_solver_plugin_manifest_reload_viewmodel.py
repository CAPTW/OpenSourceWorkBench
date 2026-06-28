from __future__ import annotations

import ast
import copy
import importlib
from pathlib import Path

import pytest

from osw.experimental.optional_solvers import (
    OSPMG_RELOAD_ACK_EXPIRED,
    OSPMG_RELOAD_ACK_REQUIRED,
    OSPMG_RELOAD_CONFLICT_VISIBLE,
    OSPMG_RELOAD_EVIDENCE_RETAINED,
    OSPMG_RELOAD_HISTORY_RETAINED,
    OSPMG_RELOAD_NO_DISCOVERY_EXECUTION,
    OSPMG_RELOAD_NO_PLUGIN_IMPORT,
    OSPMG_RELOAD_NO_SOLVER_EXECUTION,
    OSPMG_RELOAD_NO_VALIDATION_EXECUTION,
    OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION,
    OSPMG_RELOAD_NOT_TRUST_RESTORE,
    OSPMG_RELOAD_NOT_VALIDATION,
    OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH,
    OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED,
    OSPMG_RELOAD_REDACTION_REQUIRED,
    OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED,
    OSPMG_RELOAD_SCHEMA_UNSUPPORTED,
    OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED,
    OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED,
    OSPMG_RELOAD_SHARED_STACK_VISIBLE,
    OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED,
    OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED,
    RELOAD_REQUIRED_ACKS,
    STATE_WRITER_PAYLOAD_KIND,
    STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
    OptionalSolverPluginManifestReloadAction,
    OptionalSolverPluginManifestReloadReadiness,
    OptionalSolverPluginManifestReloadState,
    OptionalSolverPluginManifestReloadViewModel,
    build_optional_solver_plugin_manifest_reload_viewmodel,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "osw" / "experimental" / "optional_solvers" / (
    "plugin_manifest_reload_viewmodel.py"
)
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_viewmodel.md"
)


def _acks() -> list[dict[str, object]]:
    return [
        {
            "acknowledgement_id": ack,
            "satisfied": True,
            "expired": False,
            "expiry_reasons": [
                "reload",
                "source_fingerprint_change",
                "schema_version_change",
                "unsafe_claim_appearance",
                "trust_policy_change",
                "future_discovery_refresh_result",
            ],
        }
        for ack in RELOAD_REQUIRED_ACKS
    ]


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "payload_kind": STATE_WRITER_PAYLOAD_KIND,
        "payload_schema_version": STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
        "writer_version": "osw-exp-102",
        "sources": [
            {
                "source_id": "user-source",
                "source_type": "user_selected_state",
                "source_reference_display": "state.json",
                "source_reference_redacted": True,
                "trust_label": "untrusted_user_source",
            }
        ],
        "candidates": [
            {
                "candidate_id": "ccx",
                "display_name": "CalculiX",
                "lifecycle_state": "inactive",
                "source_type": "user",
                "validation_state": "skipped_missing",
            }
        ],
        "acknowledgements": _acks(),
        "redaction_privacy": [
            {
                "redaction_required": True,
                "redaction_review_required": False,
                "unredacted_path_blocked": False,
                "secret_like_content_blocked": False,
            }
        ],
        "evidence_history": [
            {
                "evidence_id": "history",
                "candidate_id": "ccx",
                "evidence_type": "deactivation_history",
                "skipped_missing_remains_skipped_missing": True,
            }
        ],
    }
    base.update(overrides)
    return base


def _codes(view_model: OptionalSolverPluginManifestReloadViewModel) -> set[str]:
    return {row.code for row in view_model.diagnostics}


def _module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


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
        "osw.experimental.optional_solvers.plugin_manifest_reload_viewmodel"
    )
    assert hasattr(module, "OptionalSolverPluginManifestReloadViewModel")
    assert hasattr(module, "OptionalSolverPluginManifestReloadSummary")
    assert hasattr(module, "OptionalSolverPluginManifestReloadSourceRow")
    assert hasattr(module, "OptionalSolverPluginManifestReloadCandidateRow")
    assert hasattr(module, "OptionalSolverPluginManifestReloadAcknowledgementRow")
    assert hasattr(module, "OptionalSolverPluginManifestReloadDiagnostic")
    assert hasattr(module, "OptionalSolverPluginManifestReloadActionState")
    assert hasattr(module, "OptionalSolverPluginManifestReloadEvidenceRow")
    assert hasattr(module, "OptionalSolverPluginManifestReloadConflictRow")
    assert hasattr(module, "OptionalSolverPluginManifestReloadUnsafeClaimRow")
    assert hasattr(module, "OptionalSolverPluginManifestReloadState")
    assert hasattr(module, "OptionalSolverPluginManifestReloadReadiness")
    assert hasattr(module, "OptionalSolverPluginManifestReloadAction")
    assert hasattr(module, "OptionalSolverPluginManifestReloadInput")


def test_module_imports_and_source_avoid_forbidden_runtime_paths() -> None:
    imports = _imported_modules() - {"__future__"}
    assert imports == {"collections.abc", "dataclasses", "enum"}
    source = _module_source()
    forbidden_phrases = (
        "PySide",
        "PyQt",
        "osw.cli",
        "pathlib",
        "import os",
        "open(",
        "read_text(",
        "read_bytes(",
        "glob(",
        "iterdir(",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "pip install",
        "pip uninstall",
        "gh issue",
        "gh release",
    )
    for phrase in forbidden_phrases:
        assert phrase not in source, phrase


def test_unavailable_and_empty_are_deterministic_no_payload_states() -> None:
    unavailable = OptionalSolverPluginManifestReloadViewModel.unavailable()
    empty = OptionalSolverPluginManifestReloadViewModel.empty()
    assert unavailable.summary.state == (
        OptionalSolverPluginManifestReloadState.NO_RELOAD_REQUEST
    )
    assert unavailable.summary.readiness == (
        OptionalSolverPluginManifestReloadReadiness.UNAVAILABLE_NO_PAYLOAD
    )
    assert empty.to_mapping() == OptionalSolverPluginManifestReloadViewModel.empty().to_mapping()
    assert all(action.enabled is False for action in unavailable.action_states)


def test_valid_mapping_is_review_ready_and_redacts_path_like_source_label() -> None:
    view_model = OptionalSolverPluginManifestReloadViewModel.from_payload_mapping(
        _payload(),
        source_label=r"C:\Users\USER\state.json",
    )
    mapping = view_model.to_mapping()
    assert view_model.summary.readiness == (
        OptionalSolverPluginManifestReloadReadiness.READY_REVIEW_ONLY
    )
    assert view_model.summary.source_display == "state.json"
    assert view_model.summary.source_reference_redacted is True
    assert r"C:\Users\USER" not in str(mapping)
    assert view_model.summary.reload_is_validation_evidence is False
    assert view_model.summary.reload_is_validation_failure is False
    assert view_model.summary.reload_restores_trust is False
    assert view_model.summary.reload_automatically_activates is False
    assert view_model.summary.reload_runs_discovery is False
    assert view_model.summary.reload_imports_plugin_package is False
    assert view_model.summary.reload_runs_validation is False
    assert view_model.summary.reload_executes_solver is False
    assert view_model.summary.reload_mutates_project_schema is False
    assert view_model.summary.reload_closes_issue is False
    assert view_model.summary.reload_mutates_release is False
    assert view_model.summary.reload_certifies_manifest is False


@pytest.mark.parametrize(
    ("payload", "readiness", "diagnostic"),
    [
        (
            _payload(payload_kind="wrong"),
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_PAYLOAD_KIND_MISMATCH,
            OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH,
        ),
        (
            _payload(payload_schema_version=""),
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_SCHEMA_VERSION_MISSING,
            OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED,
        ),
        (
            _payload(payload_schema_version="unsupported"),
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_SCHEMA_UNSUPPORTED,
            OSPMG_RELOAD_SCHEMA_UNSUPPORTED,
        ),
        (
            _payload(schema_migration_required=True),
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_SCHEMA_MIGRATION_REQUIRED,
            OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED,
        ),
    ],
)
def test_payload_kind_and_schema_blockers_are_deterministic(
    payload: dict[str, object],
    readiness: OptionalSolverPluginManifestReloadReadiness,
    diagnostic: str,
) -> None:
    view_model = build_optional_solver_plugin_manifest_reload_viewmodel(payload)
    assert view_model.summary.readiness == readiness
    assert diagnostic in _codes(view_model)
    assert view_model.schema_rows[0].schema_mismatch_not_validation_failure is True
    assert view_model.schema_rows[0].schema_model_separate_from_project_schema is True


@pytest.mark.parametrize(
    ("redaction_row", "readiness", "diagnostic"),
    [
        (
            {"redaction_review_required": True},
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_REDACTION_REVIEW,
            OSPMG_RELOAD_REDACTION_REQUIRED,
        ),
        (
            {"unredacted_path_blocked": True},
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_UNREDACTED_PATH,
            OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED,
        ),
        (
            {"secret_like_content_blocked": True},
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_SECRET_LIKE_CONTENT,
            OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED,
        ),
    ],
)
def test_redaction_and_secret_blockers_are_surfaced(
    redaction_row: dict[str, object],
    readiness: OptionalSolverPluginManifestReloadReadiness,
    diagnostic: str,
) -> None:
    row = {
        "redaction_required": True,
        "redaction_review_required": False,
        "unredacted_path_blocked": False,
        "secret_like_content_blocked": False,
    }
    row.update(redaction_row)
    view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(redaction_privacy=[row])
    )
    assert view_model.summary.readiness == readiness
    assert diagnostic in _codes(view_model)
    assert view_model.redaction_rows[0].raw_paths_hidden_by_default is True
    assert view_model.redaction_rows[0].fingerprints_not_trust_signals is True


def test_missing_and_expired_acknowledgements_block_reload_review() -> None:
    missing = _acks()[1:]
    missing_view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(acknowledgements=missing)
    )
    assert missing_view_model.summary.readiness == (
        OptionalSolverPluginManifestReloadReadiness.BLOCKED_ACKNOWLEDGEMENT
    )
    assert OSPMG_RELOAD_ACK_REQUIRED in _codes(missing_view_model)

    expired = _acks()
    expired[0] = {**expired[0], "expired": True}
    expired_view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(acknowledgements=expired)
    )
    assert expired_view_model.summary.readiness == (
        OptionalSolverPluginManifestReloadReadiness.BLOCKED_ACKNOWLEDGEMENT
    )
    assert OSPMG_RELOAD_ACK_EXPIRED in _codes(expired_view_model)
    assert "schema_version_change" in expired_view_model.acknowledgement_rows[0].expiry_reasons


def test_stale_source_conflict_and_shared_stack_states_are_surfaced() -> None:
    stale_view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(stale_sources=[{"source_id": "user-source", "repreview_required": True}])
    )
    assert stale_view_model.summary.readiness == (
        OptionalSolverPluginManifestReloadReadiness.BLOCKED_STALE_SOURCE_REPREVIEW
    )
    assert OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED in _codes(stale_view_model)
    assert stale_view_model.stale_source_rows[0].old_preview_not_silently_trusted is True
    assert stale_view_model.stale_source_rows[0].no_source_file_io is True

    conflict_view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(conflicts=[{"conflict_id": "conflict", "blocker": True}])
    )
    assert conflict_view_model.summary.readiness == (
        OptionalSolverPluginManifestReloadReadiness.BLOCKED_CONFLICT
    )
    assert OSPMG_RELOAD_CONFLICT_VISIBLE in _codes(conflict_view_model)
    assert conflict_view_model.conflict_rows[0].persisted_state_overrides_built_ins is False
    assert conflict_view_model.conflict_rows[0].reload_resolves_conflict is False

    shared_view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(
            conflicts=[
                {
                    "conflict_id": "shared",
                    "blocker": False,
                    "shared_stack_warning_visible": True,
                }
            ]
        )
    )
    assert shared_view_model.summary.readiness == (
        OptionalSolverPluginManifestReloadReadiness.BLOCKED_SHARED_STACK_WARNING
    )
    assert OSPMG_RELOAD_SHARED_STACK_VISIBLE in _codes(shared_view_model)


@pytest.mark.parametrize(
    ("claim_text", "claim_type"),
    [
        ("validation success was achieved", "validation_success"),
        ("validation failure was achieved", "validation_failure"),
        ("issue should close", "issue_closure"),
        ("release mutation is complete", "release_mutation"),
        ("bundled solver support exists", "bundled_solver"),
        ("dependency installation happened", "dependency_installation"),
        ("solver execution happened", "solver_execution"),
        ("trust restoration happened", "trust_restoration"),
        ("industrial certification", "certification"),
    ],
)
def test_unsafe_claims_are_blocked_not_reloaded_as_truth(
    claim_text: str,
    claim_type: str,
) -> None:
    view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(unsafe_claims=[{"claim_id": claim_type, "claim_text": claim_text}])
    )
    assert view_model.summary.state == (
        OptionalSolverPluginManifestReloadState.UNSAFE_CLAIM_BLOCKED
    )
    assert OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED in _codes(view_model)
    assert view_model.unsafe_claim_rows[0].claim_type == claim_type
    assert view_model.unsafe_claim_rows[0].not_reloaded_as_truth is True


@pytest.mark.parametrize(
    ("lifecycle", "review_state", "future_activation", "future_refresh"),
    [
        ("inactive", "review_only", False, False),
        ("active", "future_activation_review_required", True, False),
        ("deactivated", "deactivated_review_state", False, False),
        ("reactivation", "future_activation_review_required", True, False),
        ("discovery_refresh", "future_discovery_refresh_required", False, True),
    ],
)
def test_candidate_lifecycle_state_remains_review_only(
    lifecycle: str,
    review_state: str,
    future_activation: bool,
    future_refresh: bool,
) -> None:
    view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(
            candidates=[
                {
                    "candidate_id": lifecycle,
                    "display_name": lifecycle,
                    "lifecycle_state": lifecycle,
                    "validation_state": "skipped_missing",
                }
            ]
        )
    )
    row = view_model.candidate_rows[0]
    assert row.reload_review_state == review_state
    assert row.requires_future_activation_review is future_activation
    assert row.requires_future_discovery_refresh is future_refresh
    assert row.no_automatic_activation is True
    assert row.no_trust_restoration is True
    assert row.skipped_missing_remains_skipped_missing is True


def test_evidence_history_and_trust_boundaries_are_retained() -> None:
    view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(
            sources=[
                {
                    "source_id": "built-in",
                    "source_type": "built_in",
                    "source_reference_display": "builtin",
                    "trust_label": "built_in_authoritative",
                },
                {
                    "source_id": "plugin",
                    "source_type": "plugin",
                    "source_reference_display": "plugin.json",
                    "trust_label": "untrusted_plugin_manifest",
                },
            ]
        )
    )
    assert OSPMG_RELOAD_EVIDENCE_RETAINED in _codes(view_model)
    assert OSPMG_RELOAD_HISTORY_RETAINED in _codes(view_model)
    assert view_model.evidence_rows[0].historical_evidence_reference_only is True
    assert view_model.evidence_rows[0].skipped_missing_remains_skipped_missing is True
    assert view_model.evidence_rows[0].issue_closure_implied is False
    assert view_model.source_rows[0].built_ins_authoritative_by_default is True
    assert view_model.source_rows[0].trust_label_is_certification is False
    assert view_model.source_rows[1].user_plugin_sources_untrusted_by_default is True


def test_boundary_diagnostics_and_action_states_are_disabled_or_future_only() -> None:
    view_model = build_optional_solver_plugin_manifest_reload_viewmodel(_payload())
    codes = _codes(view_model)
    assert OSPMG_RELOAD_NOT_VALIDATION in codes
    assert OSPMG_RELOAD_NOT_TRUST_RESTORE in codes
    assert OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION in codes
    assert OSPMG_RELOAD_NO_DISCOVERY_EXECUTION in codes
    assert OSPMG_RELOAD_NO_PLUGIN_IMPORT in codes
    assert OSPMG_RELOAD_NO_VALIDATION_EXECUTION in codes
    assert OSPMG_RELOAD_NO_SOLVER_EXECUTION in codes
    assert OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED in codes

    actions = {row.action: row for row in view_model.action_states}
    for action in (
        OptionalSolverPluginManifestReloadAction.READ_RELOAD_FILE,
        OptionalSolverPluginManifestReloadAction.PARSE_RELOAD_FILE,
        OptionalSolverPluginManifestReloadAction.MIGRATE_SCHEMA,
        OptionalSolverPluginManifestReloadAction.ACTIVATE_RELOADED_CANDIDATE,
        OptionalSolverPluginManifestReloadAction.REFRESH_DISCOVERY,
        OptionalSolverPluginManifestReloadAction.VALIDATE_SOLVER,
        OptionalSolverPluginManifestReloadAction.EXECUTE_SOLVER,
        OptionalSolverPluginManifestReloadAction.INSTALL_DEPENDENCY,
        OptionalSolverPluginManifestReloadAction.UNINSTALL_DEPENDENCY,
        OptionalSolverPluginManifestReloadAction.UNINSTALL_SOLVER,
        OptionalSolverPluginManifestReloadAction.MUTATE_PROJECT_SCHEMA,
        OptionalSolverPluginManifestReloadAction.CLOSE_ISSUE,
        OptionalSolverPluginManifestReloadAction.MUTATE_RELEASE,
        OptionalSolverPluginManifestReloadAction.PUSH_TAG,
        OptionalSolverPluginManifestReloadAction.UPLOAD_ASSET,
        OptionalSolverPluginManifestReloadAction.CLAIM_VALIDATION_SUCCESS_FAILURE,
        OptionalSolverPluginManifestReloadAction.CLAIM_CERTIFICATION,
    ):
        assert actions[action].enabled is False
        assert actions[action].future_only is True


def test_mapping_text_output_is_stable_redacted_and_input_is_not_mutated() -> None:
    payload = _payload()
    original = copy.deepcopy(payload)
    view_model = build_optional_solver_plugin_manifest_reload_viewmodel(
        payload,
        source_label="/home/user/private/state.json",
    )
    assert payload == original
    assert view_model.to_mapping() == view_model.to_mapping()
    assert view_model.to_text_lines() == view_model.to_text_lines()
    text = "\n".join(view_model.to_text_lines())
    assert "not validation evidence" in text
    assert "does not restore trust" in text
    assert "does not automatically activate" in text
    assert "does not run discovery" in text
    assert "does not mutate ProjectSchema" in text
    assert "/home/user/private" not in str(view_model.to_mapping())


def test_view_model_does_not_create_files(tmp_path: Path) -> None:
    before = sorted(child.name for child in tmp_path.iterdir())
    build_optional_solver_plugin_manifest_reload_viewmodel(
        _payload(),
        source_label=str(tmp_path / "state.json"),
    )
    after = sorted(child.name for child in tmp_path.iterdir())
    assert after == before == []


def test_documentation_mentions_required_relationships_and_live_issues() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "Relationship to State Writer" in text
    assert "Relationship to Export Summary" in text
    assert "Relationship to ProjectSchema" in text
    assert "Relationship to Live Optional Validation Issues" in text
    assert "Issues #6 through #11 remain open" in text
