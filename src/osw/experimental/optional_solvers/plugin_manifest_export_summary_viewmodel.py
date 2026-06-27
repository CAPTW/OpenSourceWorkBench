"""Pure view-model for optional solver plugin manifest export summaries.

This module is the OSW-EXP-097 implementation of the export-summary
view-model designed in OSW-EXP-091. It transforms already-supplied optional
solver plugin manifest UX state into deterministic, redacted, human-reviewable,
non-authoritative summary records.

It performs no side effects. It does not export files, write files, create
report files, create settings files, create runtime state files, create schema
files, create reloadable bundles, parse JSON from paths, inspect path
existence, import PySide/Qt, import plugin packages, scan directories, fetch
URLs, run discovery, run validation, execute solvers, install or uninstall
dependencies, uninstall solvers, mutate ProjectSchema, mutate issues/releases,
or claim validation success/failure or certification. All state, provenance,
acknowledgement, redaction, stale-source, conflict, unsafe-claim, and evidence
inputs are supplied by the caller; this layer only classifies and renders them.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED = "OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED"
OSPMG_EXPORT_SUMMARY_ACK_REQUIRED = "OSPMG_EXPORT_SUMMARY_ACK_REQUIRED"
OSPMG_EXPORT_SUMMARY_NOT_VALIDATION = "OSPMG_EXPORT_SUMMARY_NOT_VALIDATION"
OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE = "OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE"
OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE = (
    "OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE"
)
OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE = "OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE"
OSPMG_EXPORT_SUMMARY_NO_INSTALL = "OSPMG_EXPORT_SUMMARY_NO_INSTALL"
OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION = (
    "OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION"
)
OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE = (
    "OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE"
)
OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION = (
    "OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION"
)
OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED = (
    "OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED"
)
OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED = (
    "OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED"
)
OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED = (
    "OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED"
)
OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE = "OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE"
OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED = "OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED"
OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM = "OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM"
OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED = (
    "OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED"
)
OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED = "OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED"
OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION = (
    "OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION"
)
OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT = "OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT"
OSPMG_EXPORT_SUMMARY_FUTURE_GATE = "OSPMG_EXPORT_SUMMARY_FUTURE_GATE"

OSPMG_EXPORT_SUMMARY_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED,
    OSPMG_EXPORT_SUMMARY_ACK_REQUIRED,
    OSPMG_EXPORT_SUMMARY_NOT_VALIDATION,
    OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE,
    OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE,
    OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE,
    OSPMG_EXPORT_SUMMARY_NO_INSTALL,
    OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION,
    OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE,
    OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION,
    OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED,
    OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED,
    OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE,
    OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED,
    OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM,
    OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED,
    OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED,
    OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION,
    OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT,
    OSPMG_EXPORT_SUMMARY_FUTURE_GATE,
)

ACK_EXPORT_NOT_VALIDATION = "export_not_validation"
ACK_EXPORT_NOT_PERSISTENCE = "export_not_persistence"
ACK_EXPORT_NOT_RELOADABLE_BUNDLE = "export_not_reloadable_bundle"
ACK_EXPORT_NOT_TRUST_RESTORATION = "export_not_trust_restoration"
ACK_EXPORT_NOT_INSTALL = "export_not_install"
ACK_EXPORT_NO_SOLVER_EXECUTION = "export_no_solver_execution"
ACK_EXPORT_NOT_ISSUE_CLOSURE = "export_not_issue_closure"
ACK_EXPORT_NOT_RELEASE_MUTATION = "export_not_release_mutation"
ACK_REDACTION_REVIEWED = "redaction_reviewed"
ACK_UNREDACTED_PATHS_BLOCKED = "unredacted_paths_blocked"
ACK_STALE_SOURCE_REQUIRES_REPREVIEW = "stale_source_requires_repreview"
ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED = "untrusted_source_remains_untrusted"
ACK_NO_DISCOVERY_EXECUTION = "no_discovery_execution"
ACK_NO_PLUGIN_PACKAGE_IMPORT = "no_plugin_package_import"
ACK_TRUST_LABEL_NOT_CERTIFICATION = "trust_label_not_certification"

EXPORT_SUMMARY_REQUIRED_ACKS: tuple[str, ...] = (
    ACK_EXPORT_NOT_VALIDATION,
    ACK_EXPORT_NOT_PERSISTENCE,
    ACK_EXPORT_NOT_RELOADABLE_BUNDLE,
    ACK_EXPORT_NOT_TRUST_RESTORATION,
    ACK_EXPORT_NOT_INSTALL,
    ACK_EXPORT_NO_SOLVER_EXECUTION,
    ACK_EXPORT_NOT_ISSUE_CLOSURE,
    ACK_EXPORT_NOT_RELEASE_MUTATION,
    ACK_REDACTION_REVIEWED,
    ACK_UNREDACTED_PATHS_BLOCKED,
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_TRUST_LABEL_NOT_CERTIFICATION,
)

_ACK_LABELS: dict[str, str] = {
    ACK_EXPORT_NOT_VALIDATION: "I understand export summaries are not validation.",
    ACK_EXPORT_NOT_PERSISTENCE: "I understand export summaries are not persistence.",
    ACK_EXPORT_NOT_RELOADABLE_BUNDLE: (
        "I understand export summaries are not reloadable bundles."
    ),
    ACK_EXPORT_NOT_TRUST_RESTORATION: (
        "I understand export summaries do not restore trust."
    ),
    ACK_EXPORT_NOT_INSTALL: (
        "I understand export summaries do not install dependencies."
    ),
    ACK_EXPORT_NO_SOLVER_EXECUTION: (
        "I understand export summaries do not execute solvers."
    ),
    ACK_EXPORT_NOT_ISSUE_CLOSURE: (
        "I understand export summaries do not close issues."
    ),
    ACK_EXPORT_NOT_RELEASE_MUTATION: (
        "I understand export summaries do not mutate releases."
    ),
    ACK_REDACTION_REVIEWED: "I reviewed export-summary redaction.",
    ACK_UNREDACTED_PATHS_BLOCKED: (
        "I understand unredacted paths are blocked."
    ),
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW: (
        "I understand stale sources require re-preview."
    ),
    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED: (
        "I understand untrusted sources remain untrusted."
    ),
    ACK_NO_DISCOVERY_EXECUTION: (
        "I understand export summaries do not run discovery."
    ),
    ACK_NO_PLUGIN_PACKAGE_IMPORT: (
        "I understand export summaries do not import plugin packages."
    ),
    ACK_TRUST_LABEL_NOT_CERTIFICATION: (
        "I understand a trust label is not certification."
    ),
}

EXPORT_SUMMARY_NOT_VALIDATION_TEXT = (
    "An export summary is not validation evidence."
)
EXPORT_SUMMARY_NOT_PERSISTENCE_TEXT = "An export summary is not persistence."
EXPORT_SUMMARY_NOT_RELOADABLE_TEXT = (
    "An export summary is not a reloadable state bundle."
)
EXPORT_SUMMARY_NOT_TRUST_RESTORE_TEXT = (
    "An export summary does not restore trust."
)
EXPORT_SUMMARY_NOT_AUTOMATIC_ACTIVATION_TEXT = (
    "An export summary is not automatic activation."
)
TRUST_NOT_CERTIFICATION_TEXT = "A trust label is not certification."
EXPORT_SUMMARY_NOT_IMPLEMENTED_TEXT = (
    "Export-summary file output, clipboard integration, report attachment, "
    "reloadable bundles, persistence writers, GUI behavior, CLI behavior, "
    "discovery, validation, solver execution, issue mutation, release mutation, "
    "tag mutation, asset mutation, version bumps, and certification claims are "
    "future gates; this view-model only builds in-memory display records."
)


class OptionalSolverPluginManifestExportSummaryState(str, Enum):
    """Export-summary lifecycle state."""

    EXPORT_SUMMARY_UNAVAILABLE = "export_summary_unavailable"
    EXPORT_SUMMARY_REQUESTED = "export_summary_requested"
    EXPORT_SUMMARY_BLOCKED = "export_summary_blocked"
    EXPORT_SUMMARY_READY_PREVIEW = "export_summary_ready_preview"
    EXPORT_SUMMARY_FUTURE_FILE_EXPORT_REQUIRED = (
        "export_summary_future_file_export_required"
    )
    EXPORT_SUMMARY_FUTURE_CLIPBOARD_REQUIRED = (
        "export_summary_future_clipboard_required"
    )
    EXPORT_SUMMARY_FUTURE_REPORT_ATTACHMENT_REQUIRED = (
        "export_summary_future_report_attachment_required"
    )
    EXPORT_SUMMARY_FUTURE_RELOADABLE_BUNDLE_REQUIRED = (
        "export_summary_future_reloadable_bundle_required"
    )
    EXPORT_SUMMARY_ERROR = "export_summary_error"


class OptionalSolverPluginManifestExportSummaryReadiness(str, Enum):
    """Export-summary readiness classification."""

    UNAVAILABLE_NO_STATE = "unavailable_no_state"
    UNAVAILABLE_NO_EXPLICIT_REQUEST = "unavailable_no_explicit_request"
    BLOCKED_ACKNOWLEDGEMENT = "blocked_acknowledgement"
    BLOCKED_REDACTION_REVIEW = "blocked_redaction_review"
    BLOCKED_UNREDACTED_PATH = "blocked_unredacted_path"
    BLOCKED_STALE_SOURCE_REPREVIEW = "blocked_stale_source_repreview"
    BLOCKED_CONFLICT = "blocked_conflict"
    BLOCKED_SHARED_STACK_WARNING = "blocked_shared_stack_warning"
    BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_claim"
    READY_PREVIEW_ONLY = "ready_preview_only"
    FUTURE_FILE_EXPORT_REQUIRED = "future_file_export_required"
    FUTURE_CLIPBOARD_REQUIRED = "future_clipboard_required"
    FUTURE_REPORT_ATTACHMENT_REQUIRED = "future_report_attachment_required"
    FUTURE_RELOADABLE_BUNDLE_REQUIRED = "future_reloadable_bundle_required"
    ERROR = "error"


class OptionalSolverPluginManifestExportSummaryAction(str, Enum):
    """Display-only action identifiers for future export-summary surfaces."""

    REVIEW_EXPORT_SUMMARY = "review_export_summary"
    REVIEW_REDACTION = "review_redaction"
    ACKNOWLEDGE_EXPORT_NOT_VALIDATION = "acknowledge_export_not_validation"
    ACKNOWLEDGE_EXPORT_NOT_PERSISTENCE = "acknowledge_export_not_persistence"
    ACKNOWLEDGE_EXPORT_NOT_RELOADABLE_BUNDLE = (
        "acknowledge_export_not_reloadable_bundle"
    )
    ACKNOWLEDGE_EXPORT_NOT_TRUST_RESTORATION = (
        "acknowledge_export_not_trust_restoration"
    )
    ACKNOWLEDGE_NO_INSTALL = "acknowledge_no_install"
    ACKNOWLEDGE_NO_SOLVER_EXECUTION = "acknowledge_no_solver_execution"
    ACKNOWLEDGE_NO_ISSUE_CLOSURE = "acknowledge_no_issue_closure"
    ACKNOWLEDGE_NO_RELEASE_MUTATION = "acknowledge_no_release_mutation"
    ACKNOWLEDGE_REDACTION_REVIEWED = "acknowledge_redaction_reviewed"
    ACKNOWLEDGE_UNREDACTED_PATHS_BLOCKED = (
        "acknowledge_unredacted_paths_blocked"
    )
    ACKNOWLEDGE_STALE_SOURCE_REQUIRES_REPREVIEW = (
        "acknowledge_stale_source_requires_repreview"
    )
    ACKNOWLEDGE_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED = (
        "acknowledge_untrusted_source_remains_untrusted"
    )
    ACKNOWLEDGE_NO_DISCOVERY_EXECUTION = "acknowledge_no_discovery_execution"
    ACKNOWLEDGE_NO_PLUGIN_PACKAGE_IMPORT = "acknowledge_no_plugin_package_import"
    ACKNOWLEDGE_TRUST_LABEL_NOT_CERTIFICATION = (
        "acknowledge_trust_label_not_certification"
    )
    WRITE_EXPORT_FILE = "write_export_file"
    COPY_TO_CLIPBOARD = "copy_to_clipboard"
    ATTACH_TO_REPORT = "attach_to_report"
    CREATE_RELOADABLE_BUNDLE = "create_reloadable_bundle"
    PERSIST_STATE = "persist_state"
    RELOAD_STATE = "reload_state"
    MUTATE_PROJECT_SCHEMA = "mutate_project_schema"
    RUN_DISCOVERY = "run_discovery"
    RUN_VALIDATION = "run_validation"
    INSTALL_DEPENDENCY = "install_dependency"
    UNINSTALL_DEPENDENCY = "uninstall_dependency"
    UNINSTALL_SOLVER = "uninstall_solver"
    EXECUTE_SOLVER = "execute_solver"
    CLOSE_ISSUE = "close_issue"
    MUTATE_RELEASE = "mutate_release"
    PUSH_TAG = "push_tag"
    UPLOAD_ASSET = "upload_asset"


_UNSAFE_ACTIONS: frozenset[str] = frozenset(
    {
        OptionalSolverPluginManifestExportSummaryAction.WRITE_EXPORT_FILE.value,
        OptionalSolverPluginManifestExportSummaryAction.COPY_TO_CLIPBOARD.value,
        OptionalSolverPluginManifestExportSummaryAction.ATTACH_TO_REPORT.value,
        OptionalSolverPluginManifestExportSummaryAction.CREATE_RELOADABLE_BUNDLE.value,
        OptionalSolverPluginManifestExportSummaryAction.PERSIST_STATE.value,
        OptionalSolverPluginManifestExportSummaryAction.RELOAD_STATE.value,
        OptionalSolverPluginManifestExportSummaryAction.MUTATE_PROJECT_SCHEMA.value,
        OptionalSolverPluginManifestExportSummaryAction.RUN_DISCOVERY.value,
        OptionalSolverPluginManifestExportSummaryAction.RUN_VALIDATION.value,
        OptionalSolverPluginManifestExportSummaryAction.INSTALL_DEPENDENCY.value,
        OptionalSolverPluginManifestExportSummaryAction.UNINSTALL_DEPENDENCY.value,
        OptionalSolverPluginManifestExportSummaryAction.UNINSTALL_SOLVER.value,
        OptionalSolverPluginManifestExportSummaryAction.EXECUTE_SOLVER.value,
        OptionalSolverPluginManifestExportSummaryAction.CLOSE_ISSUE.value,
        OptionalSolverPluginManifestExportSummaryAction.MUTATE_RELEASE.value,
        OptionalSolverPluginManifestExportSummaryAction.PUSH_TAG.value,
        OptionalSolverPluginManifestExportSummaryAction.UPLOAD_ASSET.value,
    }
)

EXPORT_SUMMARY_BLOCKED_TRANSITIONS: tuple[str, ...] = (
    "exported state directly to active candidate",
    "exported state directly to trusted source",
    "exported state directly to persistence",
    "exported state directly to reloadable bundle",
    "exported state directly to file output in this gate",
    "exported state directly to clipboard",
    "exported state directly to report attachment",
    "exported state directly to discovery execution",
    "exported state directly to validation execution",
    "exported state directly to dependency install",
    "exported state directly to solver execution",
    "exported state directly to issue closure",
    "exported state directly to release mutation",
    "exported state directly to certification claim",
)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryHeader:
    """Summary header values for an export-summary view-model."""

    summary_kind: str
    state_scope: str
    generated_by_display: str
    schema_version_display: str
    source_count: int
    candidate_count: int
    acknowledgement_count: int
    diagnostic_count: int
    warning_count: int
    error_count: int
    conflict_count: int
    unsafe_claim_count: int
    stale_source_count: int
    redaction_required_count: int
    evidence_retained_count: int
    history_retained_count: int
    limitations_count: int
    readiness: str
    export_summary_state: str
    status_text: str
    export_performed: bool = False
    file_write_performed: bool = False
    export_file_created: bool = False
    clipboard_performed: bool = False
    report_attachment_performed: bool = False
    reloadable_bundle_created: bool = False
    persistence_performed: bool = False
    validation_success_claimed: bool = False
    validation_failure_claimed: bool = False
    issue_closure_claimed: bool = False
    release_mutation_performed: bool = False
    certification_claimed: bool = False
    not_validation_evidence: bool = True
    not_persistence: bool = True
    not_reloadable_bundle: bool = True
    third_party_manifests_trusted_by_default: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummarySection:
    """Renderable in-memory section record."""

    section_id: str
    title: str
    severity: str
    lines: tuple[str, ...] = ()
    rows: tuple[object, ...] = ()
    diagnostics: tuple[str, ...] = ()
    visible: bool = True
    collapsed_by_default: bool = False
    limitation: bool = False
    blocker: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummarySourceRow:
    """Source/provenance summary row."""

    source_id: str
    source_type: str = "user_selected_json_file"
    source_label: str = ""
    source_reference_display: str = ""
    source_reference_redacted: bool = True
    trust_label: str = "untrusted_user_file"
    export_summary_kind: str = "session_summary"
    persisted_state_kind: str = ""
    source_fingerprint_display: str = ""
    stale_source_state: str = "fresh"
    repreview_required: bool = False
    raw_reference_blocked: bool = False
    trust_label_not_certification: bool = True
    not_validation_evidence: bool = True
    diagnostics: tuple[str, ...] = ()
    secret_like_content_blocked: bool = False
    built_in_authoritative: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryCandidateRow:
    """Candidate summary row for supplied plugin manifest UX state."""

    stack_id: str
    display_name: str = ""
    source_id: str = ""
    source_type: str = "user_selected_json_file"
    trust_label: str = "untrusted_user_file"
    activation_state: str = "inactive_preview"
    deactivation_state: str = ""
    reactivation_state: str = ""
    discovery_refresh_state: str = ""
    persistence_state: str = ""
    export_summary_state: str = ""
    readiness: str = ""
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    required_acknowledgements: tuple[str, ...] = EXPORT_SUMMARY_REQUIRED_ACKS
    diagnostics: tuple[str, ...] = ()
    stale_source_state: str = "fresh"
    repreview_required: bool = False
    redaction_status: str = "redacted"
    built_in_relationship: str = ""
    shared_stack_indicators: tuple[str, ...] = ()
    deactivation_history_state: str = "retained"
    reactivation_history_state: str = "retained"
    historical_evidence_state: str = "retained"
    validation_evidence_state: str = "not_validation_evidence"
    issue_closure_implied: bool = False
    source_reference_display: str = ""
    source_reference_redacted: bool = True
    automatic_activation_implied: bool = False
    trusted_source_implied: bool = False
    validation_evidence_implied: bool = False
    is_untrusted: bool = True
    built_in_authoritative: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryAcknowledgementRow:
    """Acknowledgement row and expiry policy."""

    acknowledgement_id: str
    label: str = ""
    required: bool = True
    satisfied: bool = False
    persisted: bool = False
    expires_on_reload: bool = True
    expires_on_source_change: bool = True
    expires_on_schema_change: bool = True
    expires_on_unsafe_claim: bool = True
    blocking: bool = False
    reason: str = ""
    related_candidate_id: str = ""
    related_source_id: str = ""
    warning_text: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryDiagnosticRow:
    """Export-summary diagnostic row."""

    severity: str
    category: str
    code: str
    message: str
    source_reference_display: str = ""
    stack_id: str = ""
    suggested_fix: str = ""
    blocker: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryRedactionRow:
    """Redaction/privacy summary row."""

    raw_reference_supplied: bool
    display_reference: str
    redaction_status: str
    redaction_required: bool
    unredacted_path_blocked: bool
    redaction_reviewed: bool
    secret_like_content_blocked: bool
    privacy_warning: str
    fingerprint_is_not_trust_signal: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryStaleSourceRow:
    """Stale-source/re-preview summary row."""

    stale_source_state: str
    repreview_required: bool
    source_reference_display: str
    old_preview_not_silently_trusted: bool = True
    no_file_io_performed: bool = True
    no_file_restoration_performed: bool = True
    no_file_rewrite_performed: bool = True
    no_file_deletion_performed: bool = True
    future_policy_required: bool = True
    source_reference_redacted: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryConflictRow:
    """Conflict/shared-stack summary row."""

    stack_id: str
    built_in_source_id: str = ""
    user_or_plugin_source_id: str = ""
    active_source_state: str = ""
    deactivated_source_state: str = ""
    reactivation_source_state: str = ""
    persistence_state: str = ""
    export_summary_state: str = "conflict_visible"
    built_ins_win_by_default: bool = True
    conflict_visible: bool = True
    exported_state_does_not_override_builtin: bool = True
    future_policy_required: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryUnsafeClaimRow:
    """Unsafe-claim summary row."""

    claim_id: str
    related_candidate_id: str = ""
    related_source_id: str = ""
    claim_text: str = ""
    blocked: bool = True
    warning_text: str = "Unsafe claims are not accepted by export summaries."
    accepted_by_export_summary: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow:
    """Evidence/history summary row."""

    deactivation_history_retained: bool = True
    reactivation_history_retained: bool = True
    historical_validation_evidence_retained: bool = True
    skipped_missing_remains_skipped_missing: bool = True
    issue_closure_implied: bool = False
    validation_success_claimed: bool = False
    validation_failure_claimed: bool = False
    evidence_deleted_or_rewritten: bool = False
    export_summary_is_not_validation_evidence: bool = True
    stack_id: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryLimitationRow:
    """Visible limitation row."""

    limitation_id: str
    title: str
    message: str
    severity: str = "info"
    related_section: str = ""
    related_source_id: str = ""
    related_candidate_id: str = ""
    must_show: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryNonActionFlags:
    """Non-action flags; all remain false in this gate."""

    export_performed: bool = False
    file_write_performed: bool = False
    export_file_created: bool = False
    clipboard_performed: bool = False
    report_attachment_performed: bool = False
    reloadable_bundle_created: bool = False
    persistence_performed: bool = False
    settings_file_created: bool = False
    runtime_state_file_created: bool = False
    schema_file_created: bool = False
    project_schema_mutation_performed: bool = False
    gui_behavior_added: bool = False
    cli_behavior_added: bool = False
    reload_behavior_added: bool = False
    automatic_activation_performed: bool = False
    trust_restoration_performed: bool = False
    file_restoration_performed: bool = False
    file_rewrite_performed: bool = False
    file_deletion_performed: bool = False
    dependency_installation_performed: bool = False
    dependency_uninstall_performed: bool = False
    solver_uninstall_performed: bool = False
    plugin_package_import_performed: bool = False
    directory_scan_performed: bool = False
    network_fetch_performed: bool = False
    discovery_execution_performed: bool = False
    validation_execution_performed: bool = False
    solver_execution_performed: bool = False
    issue_mutation_performed: bool = False
    issue_closure_claimed: bool = False
    release_mutation_performed: bool = False
    tag_mutation_performed: bool = False
    asset_mutation_performed: bool = False
    version_bump_performed: bool = False
    validation_success_claimed: bool = False
    validation_failure_claimed: bool = False
    bundled_solver_claimed: bool = False
    certification_claimed: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryActionState:
    """Display-only state for current and future actions."""

    action: OptionalSolverPluginManifestExportSummaryAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExportSummaryViewModel:
    """Complete pure export-summary view-model."""

    header: OptionalSolverPluginManifestExportSummaryHeader
    sections: tuple[OptionalSolverPluginManifestExportSummarySection, ...]
    source_rows: tuple[OptionalSolverPluginManifestExportSummarySourceRow, ...] = ()
    candidate_rows: tuple[
        OptionalSolverPluginManifestExportSummaryCandidateRow, ...
    ] = ()
    acknowledgement_rows: tuple[
        OptionalSolverPluginManifestExportSummaryAcknowledgementRow, ...
    ] = ()
    diagnostics: tuple[OptionalSolverPluginManifestExportSummaryDiagnosticRow, ...] = ()
    redaction_rows: tuple[
        OptionalSolverPluginManifestExportSummaryRedactionRow, ...
    ] = ()
    stale_source_rows: tuple[
        OptionalSolverPluginManifestExportSummaryStaleSourceRow, ...
    ] = ()
    conflict_rows: tuple[
        OptionalSolverPluginManifestExportSummaryConflictRow, ...
    ] = ()
    unsafe_claim_rows: tuple[
        OptionalSolverPluginManifestExportSummaryUnsafeClaimRow, ...
    ] = ()
    evidence_history_rows: tuple[
        OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow, ...
    ] = ()
    limitation_rows: tuple[
        OptionalSolverPluginManifestExportSummaryLimitationRow, ...
    ] = ()
    non_action_flags: OptionalSolverPluginManifestExportSummaryNonActionFlags = (
        OptionalSolverPluginManifestExportSummaryNonActionFlags()
    )
    actions: tuple[OptionalSolverPluginManifestExportSummaryActionState, ...] = ()
    guidance_text: tuple[str, ...] = ()
    safety_text: tuple[str, ...] = ()
    blocked_transitions: tuple[str, ...] = EXPORT_SUMMARY_BLOCKED_TRANSITIONS
    reserved_diagnostic_codes: tuple[str, ...] = OSPMG_EXPORT_SUMMARY_DIAGNOSTIC_CODES
    not_validation_evidence: bool = True

    @classmethod
    def empty(
        cls,
        *,
        summary_kind: str = "session_summary",
        state_scope: str = "session_only",
    ) -> OptionalSolverPluginManifestExportSummaryViewModel:
        return build_optional_solver_plugin_manifest_export_summary_viewmodel(
            summary_kind=summary_kind,
            state_scope=state_scope,
            export_summary_requested=False,
        )

    @classmethod
    def unavailable(
        cls,
        *,
        summary_kind: str = "session_summary",
        state_scope: str = "session_only",
    ) -> OptionalSolverPluginManifestExportSummaryViewModel:
        return cls.empty(summary_kind=summary_kind, state_scope=state_scope)

    @classmethod
    def from_records(
        cls,
        *,
        sources: Sequence[object] = (),
        candidates: Sequence[object] = (),
        acknowledgements: Mapping[str, bool] | Sequence[object] | None = None,
        diagnostics: Sequence[object] = (),
        redaction_rows: Sequence[object] = (),
        stale_source_rows: Sequence[object] = (),
        conflicts: Sequence[object] = (),
        unsafe_claims: Sequence[object] = (),
        evidence_history: Sequence[object] = (),
        limitations: Sequence[object] = (),
        summary_kind: str = "session_summary",
        state_scope: str = "session_only",
        generated_by_display: str = "OSW optional solver plugin manifest UX",
        schema_version_display: str = "osw-exp-097-preview",
        export_summary_requested: bool = True,
        future_file_export_required: bool = False,
        future_clipboard_required: bool = False,
        future_report_attachment_required: bool = False,
        future_reloadable_bundle_required: bool = False,
    ) -> OptionalSolverPluginManifestExportSummaryViewModel:
        return build_optional_solver_plugin_manifest_export_summary_viewmodel(
            sources=sources,
            candidates=candidates,
            acknowledgements=acknowledgements,
            diagnostics=diagnostics,
            redaction_rows=redaction_rows,
            stale_source_rows=stale_source_rows,
            conflicts=conflicts,
            unsafe_claims=unsafe_claims,
            evidence_history=evidence_history,
            limitations=limitations,
            summary_kind=summary_kind,
            state_scope=state_scope,
            generated_by_display=generated_by_display,
            schema_version_display=schema_version_display,
            export_summary_requested=export_summary_requested,
            future_file_export_required=future_file_export_required,
            future_clipboard_required=future_clipboard_required,
            future_report_attachment_required=future_report_attachment_required,
            future_reloadable_bundle_required=future_reloadable_bundle_required,
        )

    @classmethod
    def from_persistence_viewmodel(
        cls,
        view_model: object,
        *,
        acknowledgements: Mapping[str, bool] | Sequence[object] | None = None,
        export_summary_requested: bool = True,
    ) -> OptionalSolverPluginManifestExportSummaryViewModel:
        return _from_persistence_viewmodel(
            view_model,
            acknowledgements=acknowledgements,
            export_summary_requested=export_summary_requested,
        )

    @classmethod
    def from_persistence_schema_model(
        cls,
        schema_model: object,
        *,
        acknowledgements: Mapping[str, bool] | Sequence[object] | None = None,
        export_summary_requested: bool = True,
    ) -> OptionalSolverPluginManifestExportSummaryViewModel:
        return _from_persistence_schema_model(
            schema_model,
            acknowledgements=acknowledgements,
            export_summary_requested=export_summary_requested,
        )

    @classmethod
    def redaction_required(
        cls,
        reference: object = "",
        *,
        source_id: str = "redaction_required_source",
    ) -> OptionalSolverPluginManifestExportSummaryViewModel:
        display, redacted, blocked, secret_blocked = _redact_reference_details(
            reference
        )
        source = OptionalSolverPluginManifestExportSummarySourceRow(
            source_id=source_id,
            source_reference_display=display,
            source_reference_redacted=redacted,
            raw_reference_blocked=blocked,
            diagnostics=(OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED,),
            secret_like_content_blocked=secret_blocked,
        )
        return build_optional_solver_plugin_manifest_export_summary_viewmodel(
            sources=(source,),
            redaction_rows=(
                OptionalSolverPluginManifestExportSummaryRedactionRow(
                    raw_reference_supplied=bool(str(reference or "")),
                    display_reference=display,
                    redaction_status="review_required",
                    redaction_required=True,
                    unredacted_path_blocked=blocked,
                    redaction_reviewed=False,
                    secret_like_content_blocked=secret_blocked,
                    privacy_warning=_redaction_privacy_warning(blocked),
                ),
            ),
            acknowledgements={},
            export_summary_requested=True,
        )

    @classmethod
    def stale_source_repreview_required(
        cls,
        *,
        source_id: str = "stale_source",
        source_reference_display: str = "stale manifest source",
    ) -> OptionalSolverPluginManifestExportSummaryViewModel:
        source = OptionalSolverPluginManifestExportSummarySourceRow(
            source_id=source_id,
            source_reference_display=source_reference_display,
            stale_source_state="stale",
            repreview_required=True,
            diagnostics=(OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED,),
        )
        return build_optional_solver_plugin_manifest_export_summary_viewmodel(
            sources=(source,),
            stale_source_rows=(
                OptionalSolverPluginManifestExportSummaryStaleSourceRow(
                    stale_source_state="stale",
                    repreview_required=True,
                    source_reference_display=source_reference_display,
                ),
            ),
            acknowledgements={},
            export_summary_requested=True,
        )

    @classmethod
    def unsafe_claim_blocked(
        cls,
        *,
        claim_id: str = "unsafe_claim",
        claim_text: str = "Export summary cannot accept unsafe validation claims.",
    ) -> OptionalSolverPluginManifestExportSummaryViewModel:
        return build_optional_solver_plugin_manifest_export_summary_viewmodel(
            unsafe_claims=(
                OptionalSolverPluginManifestExportSummaryUnsafeClaimRow(
                    claim_id=claim_id,
                    claim_text=claim_text,
                    blocked=True,
                ),
            ),
            acknowledgements={},
            export_summary_requested=True,
        )

    def to_sections(self) -> tuple[OptionalSolverPluginManifestExportSummarySection, ...]:
        return self.sections

    def to_text_lines(self) -> tuple[str, ...]:
        return _text_lines(self)

    def to_mapping(self) -> dict[str, object]:
        return _view_model_to_mapping(self)


def build_optional_solver_plugin_manifest_export_summary_viewmodel(
    *,
    sources: Sequence[object] = (),
    candidates: Sequence[object] = (),
    acknowledgements: Mapping[str, bool] | Sequence[object] | None = None,
    diagnostics: Sequence[object] = (),
    redaction_rows: Sequence[object] = (),
    stale_source_rows: Sequence[object] = (),
    conflicts: Sequence[object] = (),
    unsafe_claims: Sequence[object] = (),
    evidence_history: Sequence[object] = (),
    limitations: Sequence[object] = (),
    summary_kind: str = "session_summary",
    state_scope: str = "session_only",
    generated_by_display: str = "OSW optional solver plugin manifest UX",
    schema_version_display: str = "osw-exp-097-preview",
    export_summary_requested: bool = True,
    future_file_export_required: bool = False,
    future_clipboard_required: bool = False,
    future_report_attachment_required: bool = False,
    future_reloadable_bundle_required: bool = False,
) -> OptionalSolverPluginManifestExportSummaryViewModel:
    """Build the export-summary view-model from supplied state only."""

    source_rows = _source_rows(sources)
    candidate_rows_initial = _candidate_rows(candidates, source_rows=source_rows)
    all_source_rows = source_rows or _sources_from_candidates(candidate_rows_initial)
    redaction = _redaction_rows(redaction_rows, all_source_rows, candidate_rows_initial)
    stale_rows = _stale_rows(stale_source_rows, all_source_rows, candidate_rows_initial)
    conflict_rows = _conflict_rows(conflicts, candidate_rows_initial)
    unsafe_rows = _unsafe_claim_rows(unsafe_claims, candidate_rows_initial)
    evidence_rows = _evidence_history_rows(evidence_history, candidate_rows_initial)
    ack_rows = _acknowledgement_rows(acknowledgements)
    limit_rows = _limitation_rows(limitations)
    supplied_diagnostics = tuple(_diagnostic_row(d) for d in diagnostics)
    readiness = _readiness(
        source_rows=all_source_rows,
        candidate_rows=candidate_rows_initial,
        acknowledgement_rows=ack_rows,
        redaction_rows=redaction,
        stale_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_rows=unsafe_rows,
        export_summary_requested=export_summary_requested,
        future_file_export_required=future_file_export_required,
        future_clipboard_required=future_clipboard_required,
        future_report_attachment_required=future_report_attachment_required,
        future_reloadable_bundle_required=future_reloadable_bundle_required,
    )
    state = _state_for_readiness(readiness)
    candidate_rows = tuple(
        _candidate_with_readiness(row, readiness=_candidate_readiness(row, ack_rows))
        for row in candidate_rows_initial
    )
    diagnostics_all = _diagnostics(
        readiness=readiness,
        source_rows=all_source_rows,
        candidate_rows=candidate_rows,
        acknowledgement_rows=ack_rows,
        redaction_rows=redaction,
        stale_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_rows=unsafe_rows,
        evidence_rows=evidence_rows,
        supplied_diagnostics=supplied_diagnostics,
    )
    header = _header(
        summary_kind=summary_kind,
        state_scope=state_scope,
        generated_by_display=generated_by_display,
        schema_version_display=schema_version_display,
        readiness=readiness,
        state=state,
        source_rows=all_source_rows,
        candidate_rows=candidate_rows,
        acknowledgement_rows=ack_rows,
        diagnostics=diagnostics_all,
        conflict_rows=conflict_rows,
        unsafe_rows=unsafe_rows,
        stale_rows=stale_rows,
        redaction_rows=redaction,
        evidence_rows=evidence_rows,
        limitation_rows=limit_rows,
    )
    actions = _action_states()
    sections = _sections(
        header=header,
        source_rows=all_source_rows,
        candidate_rows=candidate_rows,
        acknowledgement_rows=ack_rows,
        diagnostics=diagnostics_all,
        redaction_rows=redaction,
        stale_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_rows=unsafe_rows,
        evidence_rows=evidence_rows,
        limitation_rows=limit_rows,
        actions=actions,
    )
    return OptionalSolverPluginManifestExportSummaryViewModel(
        header=header,
        sections=sections,
        source_rows=all_source_rows,
        candidate_rows=candidate_rows,
        acknowledgement_rows=ack_rows,
        diagnostics=diagnostics_all,
        redaction_rows=redaction,
        stale_source_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_claim_rows=unsafe_rows,
        evidence_history_rows=evidence_rows,
        limitation_rows=limit_rows,
        actions=actions,
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
    )


def redact_optional_solver_plugin_manifest_export_summary_source_reference(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool]:
    """Return a safe display reference and a redaction flag."""

    display, redacted, _blocked, _secret_blocked = _redact_reference_details(
        reference,
        provided_label=provided_label,
    )
    return display, redacted


def render_optional_solver_plugin_manifest_export_summary(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> dict[str, object]:
    """Return an in-memory, redacted, JSON-like summary mapping."""

    return view_model.to_mapping()


def summarize_optional_solver_plugin_manifest_export_summary_viewmodel(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> str:
    """Return a concise export-summary status string."""

    h = view_model.header
    return (
        "Optional solver plugin manifest export summary: "
        f"readiness={h.readiness}; state={h.export_summary_state}; "
        f"sources={h.source_count}; candidates={h.candidate_count}; "
        f"diagnostics={h.diagnostic_count}; limitations={h.limitations_count}. "
        f"{EXPORT_SUMMARY_NOT_IMPLEMENTED_TEXT}"
    )


def explain_optional_solver_plugin_manifest_export_summary_viewmodel(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> str:
    """Explain the safety boundary of the export-summary view-model."""

    disabled = ", ".join(
        action.action.value for action in view_model.actions if not action.enabled
    )
    return (
        summarize_optional_solver_plugin_manifest_export_summary_viewmodel(view_model)
        + " The view-model transforms supplied manifest UX state only; it does "
        "not export files, touch the clipboard, attach reports, create "
        "reloadable bundles, persist state, create settings files, mutate "
        "ProjectSchema, implement GUI or CLI behavior, reload, import plugin "
        "packages, scan directories, fetch network manifests, run discovery, "
        "run validation, execute solvers, install or uninstall dependencies, "
        "mutate issues, mutate releases, push tags, upload assets, or certify "
        f"results. Disabled or future-only actions: {disabled}."
    )


def _from_persistence_viewmodel(
    view_model: object,
    *,
    acknowledgements: Mapping[str, bool] | Sequence[object] | None,
    export_summary_requested: bool,
) -> OptionalSolverPluginManifestExportSummaryViewModel:
    schema_display = _attr(_attr(view_model, "summary"), "schema_version_display")
    return build_optional_solver_plugin_manifest_export_summary_viewmodel(
        sources=tuple(_attr(view_model, "source_rows", ())),
        candidates=tuple(_attr(view_model, "candidate_rows", ())),
        acknowledgements=acknowledgements
        if acknowledgements is not None
        else tuple(_attr(view_model, "acknowledgement_rows", ())),
        diagnostics=tuple(_attr(view_model, "diagnostics", ())),
        redaction_rows=tuple(_attr(view_model, "redaction_rows", ())),
        stale_source_rows=tuple(_attr(view_model, "stale_source_rows", ())),
        conflicts=tuple(_attr(view_model, "conflict_rows", ())),
        unsafe_claims=tuple(_attr(view_model, "unsafe_claim_rows", ())),
        evidence_history=tuple(_attr(view_model, "evidence_history_rows", ())),
        summary_kind="persistence_viewmodel_summary",
        state_scope=_attr(_attr(view_model, "summary"), "state_scope", "session_only"),
        schema_version_display=schema_display or "osw-exp-092-preview",
        export_summary_requested=export_summary_requested,
    )


def _from_persistence_schema_model(
    schema_model: object,
    *,
    acknowledgements: Mapping[str, bool] | Sequence[object] | None,
    export_summary_requested: bool,
) -> OptionalSolverPluginManifestExportSummaryViewModel:
    header = _attr(schema_model, "header")
    evidence = _attr(schema_model, "evidence_history")
    return build_optional_solver_plugin_manifest_export_summary_viewmodel(
        sources=tuple(_attr(schema_model, "sources", ())),
        candidates=tuple(_attr(schema_model, "candidates", ())),
        acknowledgements=acknowledgements
        if acknowledgements is not None
        else tuple(_attr(schema_model, "acknowledgements", ())),
        diagnostics=tuple(_attr(schema_model, "diagnostics", ())),
        conflicts=tuple(_attr(schema_model, "conflicts", ())),
        unsafe_claims=tuple(_attr(schema_model, "unsafe_claims", ())),
        evidence_history=(evidence,) if evidence else (),
        summary_kind="persistence_schema_model_summary",
        state_scope=_attr(header, "state_scope", "session_only"),
        schema_version_display=_attr(header, "schema_version", "osw-exp-093-schema-1"),
        export_summary_requested=export_summary_requested,
    )


def _source_rows(
    sources: Sequence[object],
) -> tuple[OptionalSolverPluginManifestExportSummarySourceRow, ...]:
    rows = tuple(_source_row(source) for source in sources)
    return tuple(sorted(rows, key=lambda row: (row.source_id, row.source_type)))


def _source_row(source: object) -> OptionalSolverPluginManifestExportSummarySourceRow:
    source_id = str(_attr(source, "source_id", "source") or "source")
    source_type = str(_attr(source, "source_type", "user_selected_json_file") or "")
    source_label = str(_attr(source, "source_label", "") or "")
    display_input = str(
        _attr(
            source,
            "source_reference_display",
            _attr(source, "source_reference", ""),
        )
        or ""
    )
    display, redacted, blocked, secret_blocked = _redact_reference_details(
        display_input,
        provided_label=source_label
        if not display_input and _attr(source, "source_reference_display", "") == ""
        else "",
    )
    raw_blocked = bool(
        _attr(source, "raw_reference_blocked", False)
        or _attr(source, "raw_path_blocked", False)
        or _attr(source, "unredacted_path_blocked", False)
        or blocked
    )
    trust_label = str(_attr(source, "trust_label", "untrusted_user_file") or "")
    built_in = _is_built_in(source_type, trust_label)
    diagnostics = tuple(
        _translate_code(str(code))
        for code in _attr(source, "diagnostics", ()) or ()
    )
    if raw_blocked and OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED not in diagnostics:
        diagnostics += (OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED,)
    repreview_required = bool(_attr(source, "repreview_required", False))
    stale_source = _attr(source, "stale_source_state", "") == "stale"
    if (
        repreview_required or stale_source
    ) and OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED not in diagnostics:
        diagnostics += (OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED,)
    return OptionalSolverPluginManifestExportSummarySourceRow(
        source_id=source_id,
        source_type=source_type or "user_selected_json_file",
        source_label=source_label,
        source_reference_display=display,
        source_reference_redacted=bool(
            _attr(source, "source_reference_redacted", redacted)
            or _attr(source, "redacted_source_reference", redacted)
            or redacted
            or raw_blocked
        ),
        trust_label=trust_label or ("built_in" if built_in else "untrusted_user_file"),
        export_summary_kind=str(
            _attr(source, "export_summary_kind", "session_summary") or "session_summary"
        ),
        persisted_state_kind=str(
            _attr(
                source,
                "persisted_state_kind",
                _attr(source, "persistence_source_kind", ""),
            )
            or ""
        ),
        source_fingerprint_display=str(
            _attr(source, "source_fingerprint_display", "") or ""
        ),
        stale_source_state=str(_attr(source, "stale_source_state", "fresh") or "fresh"),
        repreview_required=bool(_attr(source, "repreview_required", False)),
        raw_reference_blocked=raw_blocked,
        diagnostics=diagnostics,
        secret_like_content_blocked=bool(
            _attr(source, "secret_like_content_blocked", False) or secret_blocked
        ),
        built_in_authoritative=built_in,
    )


def _sources_from_candidates(
    candidates: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
) -> tuple[OptionalSolverPluginManifestExportSummarySourceRow, ...]:
    rows = []
    seen: set[str] = set()
    for candidate in candidates:
        source_id = candidate.source_id or f"{candidate.stack_id}:source"
        if source_id in seen:
            continue
        seen.add(source_id)
        rows.append(
            OptionalSolverPluginManifestExportSummarySourceRow(
                source_id=source_id,
                source_type=candidate.source_type,
                source_label=candidate.display_name,
                source_reference_display=candidate.source_reference_display,
                source_reference_redacted=candidate.source_reference_redacted,
                trust_label=candidate.trust_label,
                stale_source_state=candidate.stale_source_state,
                repreview_required=candidate.repreview_required,
                built_in_authoritative=candidate.built_in_authoritative,
            )
        )
    return tuple(rows)


def _candidate_rows(
    candidates: Sequence[object],
    *,
    source_rows: Sequence[OptionalSolverPluginManifestExportSummarySourceRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryCandidateRow, ...]:
    rows = tuple(_candidate_row(candidate, source_rows=source_rows) for candidate in candidates)
    return tuple(sorted(rows, key=lambda row: (row.stack_id, row.source_type)))


def _candidate_row(
    candidate: object,
    *,
    source_rows: Sequence[OptionalSolverPluginManifestExportSummarySourceRow],
) -> OptionalSolverPluginManifestExportSummaryCandidateRow:
    stack_id = str(_attr(candidate, "stack_id", "candidate") or "candidate")
    display_name = str(_attr(candidate, "display_name", "") or stack_id)
    source_id = str(_attr(candidate, "source_id", "") or "")
    source_type = str(_attr(candidate, "source_type", "user_selected_json_file") or "")
    trust_label = str(_attr(candidate, "trust_label", "untrusted_user_file") or "")
    source_reference = str(_attr(candidate, "source_reference_display", "") or "")
    display, redacted, blocked, secret_blocked = _redact_reference_details(
        source_reference
    )
    matching_source = _source_by_id(source_rows, source_id)
    if matching_source and not display:
        display = matching_source.source_reference_display
        redacted = matching_source.source_reference_redacted
        blocked = matching_source.raw_reference_blocked
    built_in = bool(
        _attr(candidate, "built_in_authoritative", False)
        or _is_built_in(source_type, trust_label)
    )
    is_untrusted = bool(
        _attr(candidate, "is_untrusted", not built_in)
        and trust_label not in {"built_in", "reviewed_builtin"}
    )
    diagnostics = tuple(
        _translate_code(str(code))
        for code in _attr(candidate, "diagnostics", ()) or ()
    )
    if is_untrusted and OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE not in diagnostics:
        diagnostics += (OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE,)
    if blocked and OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED not in diagnostics:
        diagnostics += (OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED,)
    warnings = tuple(_attr(candidate, "warnings", ()) or ())
    warnings += (TRUST_NOT_CERTIFICATION_TEXT, EXPORT_SUMMARY_NOT_VALIDATION_TEXT)
    if is_untrusted:
        warnings += ("User/plugin manifests remain untrusted by default.",)
    return OptionalSolverPluginManifestExportSummaryCandidateRow(
        stack_id=stack_id,
        display_name=display_name,
        source_id=source_id,
        source_type=source_type or "user_selected_json_file",
        trust_label=trust_label or ("built_in" if built_in else "untrusted_user_file"),
        activation_state=str(_attr(candidate, "activation_state", "inactive_preview") or ""),
        deactivation_state=str(_attr(candidate, "deactivation_state", "") or ""),
        reactivation_state=str(_attr(candidate, "reactivation_state", "") or ""),
        discovery_refresh_state=str(
            _attr(candidate, "discovery_refresh_state", "") or ""
        ),
        persistence_state=str(_attr(candidate, "persistence_state", "") or ""),
        export_summary_state=str(
            _attr(candidate, "export_summary_state", "") or ""
        ),
        readiness=str(_attr(candidate, "readiness", "") or ""),
        blockers=tuple(_attr(candidate, "blockers", ()) or ()),
        warnings=tuple(dict.fromkeys(warnings)),
        required_acknowledgements=EXPORT_SUMMARY_REQUIRED_ACKS,
        diagnostics=diagnostics,
        stale_source_state=str(_attr(candidate, "stale_source_state", "fresh") or "fresh"),
        repreview_required=bool(_attr(candidate, "repreview_required", False)),
        redaction_status=str(_attr(candidate, "redaction_status", "redacted") or "redacted"),
        built_in_relationship=(
            str(_attr(candidate, "built_in_relationship", "") or "")
            or ("built_in_authoritative" if built_in else "")
        ),
        shared_stack_indicators=tuple(
            _attr(candidate, "shared_stack_indicators", ()) or ()
        ),
        deactivation_history_state=str(
            _attr(candidate, "deactivation_history_state", "retained") or "retained"
        ),
        reactivation_history_state=str(
            _attr(candidate, "reactivation_history_state", "retained") or "retained"
        ),
        historical_evidence_state=str(
            _attr(candidate, "historical_evidence_state", "retained") or "retained"
        ),
        validation_evidence_state=str(
            _attr(candidate, "validation_evidence_state", "not_validation_evidence")
            or "not_validation_evidence"
        ),
        source_reference_display=display,
        source_reference_redacted=bool(redacted or blocked),
        is_untrusted=is_untrusted,
        built_in_authoritative=built_in,
    )


def _candidate_with_readiness(
    row: OptionalSolverPluginManifestExportSummaryCandidateRow,
    *,
    readiness: OptionalSolverPluginManifestExportSummaryReadiness,
) -> OptionalSolverPluginManifestExportSummaryCandidateRow:
    blockers = tuple(dict.fromkeys(row.blockers + _blockers_for_readiness(readiness)))
    state = row.export_summary_state or _state_for_readiness(readiness).value
    return OptionalSolverPluginManifestExportSummaryCandidateRow(
        stack_id=row.stack_id,
        display_name=row.display_name,
        source_id=row.source_id,
        source_type=row.source_type,
        trust_label=row.trust_label,
        activation_state=row.activation_state,
        deactivation_state=row.deactivation_state,
        reactivation_state=row.reactivation_state,
        discovery_refresh_state=row.discovery_refresh_state,
        persistence_state=row.persistence_state,
        export_summary_state=state,
        readiness=readiness.value,
        blockers=blockers,
        warnings=row.warnings,
        required_acknowledgements=row.required_acknowledgements,
        diagnostics=row.diagnostics,
        stale_source_state=row.stale_source_state,
        repreview_required=row.repreview_required,
        redaction_status=row.redaction_status,
        built_in_relationship=row.built_in_relationship,
        shared_stack_indicators=row.shared_stack_indicators,
        deactivation_history_state=row.deactivation_history_state,
        reactivation_history_state=row.reactivation_history_state,
        historical_evidence_state=row.historical_evidence_state,
        validation_evidence_state=row.validation_evidence_state,
        source_reference_display=row.source_reference_display,
        source_reference_redacted=row.source_reference_redacted,
        is_untrusted=row.is_untrusted,
        built_in_authoritative=row.built_in_authoritative,
    )


def _acknowledgement_rows(
    acknowledgements: Mapping[str, bool] | Sequence[object] | None,
) -> tuple[OptionalSolverPluginManifestExportSummaryAcknowledgementRow, ...]:
    if isinstance(acknowledgements, Mapping):
        supplied = {str(key): bool(value) for key, value in acknowledgements.items()}
        rows = tuple(_ack_row_from_map(ack, supplied) for ack in EXPORT_SUMMARY_REQUIRED_ACKS)
    elif acknowledgements is None:
        rows = tuple(_ack_row_from_map(ack, {}) for ack in EXPORT_SUMMARY_REQUIRED_ACKS)
    else:
        by_id = {
            str(_attr(row, "acknowledgement_id", "")): row for row in acknowledgements
        }
        rows = tuple(
            _ack_row_from_object(ack, by_id.get(ack))
            for ack in EXPORT_SUMMARY_REQUIRED_ACKS
        )
    return rows


def _ack_row_from_map(
    ack_id: str,
    supplied: Mapping[str, bool],
) -> OptionalSolverPluginManifestExportSummaryAcknowledgementRow:
    satisfied = bool(supplied.get(ack_id, False))
    return OptionalSolverPluginManifestExportSummaryAcknowledgementRow(
        acknowledgement_id=ack_id,
        label=_ACK_LABELS[ack_id],
        required=True,
        satisfied=satisfied,
        blocking=not satisfied,
        reason="" if satisfied else "Required export-summary acknowledgement missing.",
        warning_text="" if satisfied else _ack_warning(ack_id),
    )


def _ack_row_from_object(
    ack_id: str,
    row: object | None,
) -> OptionalSolverPluginManifestExportSummaryAcknowledgementRow:
    if row is None:
        return _ack_row_from_map(ack_id, {})
    satisfied = bool(_attr(row, "satisfied", False))
    return OptionalSolverPluginManifestExportSummaryAcknowledgementRow(
        acknowledgement_id=ack_id,
        label=str(_attr(row, "label", _ACK_LABELS[ack_id]) or _ACK_LABELS[ack_id]),
        required=bool(_attr(row, "required", True)),
        satisfied=satisfied,
        persisted=bool(_attr(row, "persisted", False)),
        expires_on_reload=bool(_attr(row, "expires_on_reload", True)),
        expires_on_source_change=bool(_attr(row, "expires_on_source_change", True)),
        expires_on_schema_change=bool(_attr(row, "expires_on_schema_change", True)),
        expires_on_unsafe_claim=bool(_attr(row, "expires_on_unsafe_claim", True)),
        blocking=bool(_attr(row, "blocking", not satisfied)),
        reason=str(
            _attr(
                row,
                "reason",
                "" if satisfied else "Required export-summary acknowledgement missing.",
            )
            or ""
        ),
        related_candidate_id=str(_attr(row, "related_candidate_id", "") or ""),
        related_source_id=str(_attr(row, "related_source_id", "") or ""),
        warning_text=str(_attr(row, "warning_text", "") or ""),
    )


def _redaction_rows(
    supplied_rows: Sequence[object],
    source_rows: Sequence[OptionalSolverPluginManifestExportSummarySourceRow],
    candidate_rows: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryRedactionRow, ...]:
    rows = tuple(_redaction_row(row) for row in supplied_rows)
    generated: list[OptionalSolverPluginManifestExportSummaryRedactionRow] = list(rows)
    for source in source_rows:
        if source.raw_reference_blocked or source.source_reference_redacted:
            generated.append(
                OptionalSolverPluginManifestExportSummaryRedactionRow(
                    raw_reference_supplied=bool(source.source_reference_display),
                    display_reference=source.source_reference_display,
                    redaction_status=(
                        "blocked" if source.raw_reference_blocked else "redacted"
                    ),
                    redaction_required=source.source_reference_redacted,
                    unredacted_path_blocked=source.raw_reference_blocked,
                    redaction_reviewed=False,
                    secret_like_content_blocked=source.secret_like_content_blocked,
                    privacy_warning=_redaction_privacy_warning(
                        source.raw_reference_blocked
                    ),
                )
            )
    for candidate in candidate_rows:
        if candidate.source_reference_redacted:
            generated.append(
                OptionalSolverPluginManifestExportSummaryRedactionRow(
                    raw_reference_supplied=bool(candidate.source_reference_display),
                    display_reference=candidate.source_reference_display,
                    redaction_status=candidate.redaction_status,
                    redaction_required=True,
                    unredacted_path_blocked=False,
                    redaction_reviewed=False,
                    secret_like_content_blocked=False,
                    privacy_warning=_redaction_privacy_warning(False),
                )
            )
    return tuple(_dedupe_redaction_rows(generated))


def _redaction_row(
    row: object,
) -> OptionalSolverPluginManifestExportSummaryRedactionRow:
    display = str(_attr(row, "display_reference", "") or "")
    display, redacted, blocked, sensitive_content_blocked = _redact_reference_details(
        display
    )
    return OptionalSolverPluginManifestExportSummaryRedactionRow(
        raw_reference_supplied=bool(_attr(row, "raw_reference_supplied", bool(display))),
        display_reference=display,
        redaction_status=str(
            _attr(row, "redaction_status", "redacted" if redacted else "") or ""
        ),
        redaction_required=bool(_attr(row, "redaction_required", redacted)),
        unredacted_path_blocked=bool(
            _attr(row, "unredacted_path_blocked", False) or blocked
        ),
        redaction_reviewed=bool(_attr(row, "redaction_reviewed", False)),
        secret_like_content_blocked=bool(
            _attr(row, "secret_like_content_blocked", False)
            or sensitive_content_blocked
        ),
        privacy_warning=str(
            _attr(row, "privacy_warning", _redaction_privacy_warning(blocked)) or ""
        ),
        fingerprint_is_not_trust_signal=bool(
            _attr(row, "fingerprint_is_not_trust_signal", True)
        ),
    )


def _stale_rows(
    supplied_rows: Sequence[object],
    source_rows: Sequence[OptionalSolverPluginManifestExportSummarySourceRow],
    candidate_rows: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryStaleSourceRow, ...]:
    rows = [_stale_row(row) for row in supplied_rows]
    for source in source_rows:
        if source.repreview_required or source.stale_source_state == "stale":
            rows.append(
                OptionalSolverPluginManifestExportSummaryStaleSourceRow(
                    stale_source_state=source.stale_source_state or "stale",
                    repreview_required=True,
                    source_reference_display=source.source_reference_display,
                    source_reference_redacted=source.source_reference_redacted,
                )
            )
    for candidate in candidate_rows:
        if candidate.repreview_required or candidate.stale_source_state == "stale":
            rows.append(
                OptionalSolverPluginManifestExportSummaryStaleSourceRow(
                    stale_source_state=candidate.stale_source_state or "stale",
                    repreview_required=True,
                    source_reference_display=candidate.source_reference_display,
                    source_reference_redacted=candidate.source_reference_redacted,
                )
            )
    return tuple(
        sorted(
            _dedupe_stale_rows(rows),
            key=lambda row: (row.source_reference_display, row.stale_source_state),
        )
    )


def _stale_row(row: object) -> OptionalSolverPluginManifestExportSummaryStaleSourceRow:
    display = str(_attr(row, "source_reference_display", "") or "")
    display, redacted, _blocked, _secret = _redact_reference_details(display)
    return OptionalSolverPluginManifestExportSummaryStaleSourceRow(
        stale_source_state=str(_attr(row, "stale_source_state", "stale") or "stale"),
        repreview_required=bool(_attr(row, "repreview_required", True)),
        source_reference_display=display,
        old_preview_not_silently_trusted=bool(
            _attr(row, "old_preview_not_silently_trusted", True)
        ),
        no_file_io_performed=bool(_attr(row, "no_file_io_performed", True)),
        no_file_restoration_performed=bool(
            _attr(row, "no_file_restoration_performed", True)
        ),
        no_file_rewrite_performed=bool(_attr(row, "no_file_rewrite_performed", True)),
        no_file_deletion_performed=bool(_attr(row, "no_file_deletion_performed", True)),
        future_policy_required=bool(_attr(row, "future_policy_required", True)),
        source_reference_redacted=bool(
            _attr(row, "source_reference_redacted", redacted) or redacted
        ),
    )


def _conflict_rows(
    conflicts: Sequence[object],
    candidate_rows: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryConflictRow, ...]:
    rows = [_conflict_row(conflict) for conflict in conflicts]
    for candidate in candidate_rows:
        if candidate.shared_stack_indicators:
            rows.append(
                OptionalSolverPluginManifestExportSummaryConflictRow(
                    stack_id=candidate.stack_id,
                    user_or_plugin_source_id=candidate.source_id,
                    active_source_state=candidate.activation_state,
                    deactivated_source_state=candidate.deactivation_state,
                    reactivation_source_state=candidate.reactivation_state,
                    persistence_state=candidate.persistence_state,
                )
            )
    return tuple(sorted(rows, key=lambda row: row.stack_id))


def _conflict_row(
    row: object,
) -> OptionalSolverPluginManifestExportSummaryConflictRow:
    return OptionalSolverPluginManifestExportSummaryConflictRow(
        stack_id=str(_attr(row, "stack_id", "conflict") or "conflict"),
        built_in_source_id=str(
            _attr(row, "built_in_source_id", _attr(row, "built_in_source", ""))
            or ""
        ),
        user_or_plugin_source_id=str(
            _attr(row, "user_or_plugin_source_id", _attr(row, "user_plugin_source", ""))
            or ""
        ),
        active_source_state=str(
            _attr(row, "active_source_state", _attr(row, "activation_state", "")) or ""
        ),
        deactivated_source_state=str(
            _attr(row, "deactivated_source_state", _attr(row, "deactivation_state", ""))
            or ""
        ),
        reactivation_source_state=str(
            _attr(row, "reactivation_source_state", _attr(row, "reactivation_state", ""))
            or ""
        ),
        persistence_state=str(_attr(row, "persistence_state", "") or ""),
        export_summary_state=str(
            _attr(row, "export_summary_state", "conflict_visible") or "conflict_visible"
        ),
        built_ins_win_by_default=bool(_attr(row, "built_ins_win_by_default", True)),
        conflict_visible=bool(_attr(row, "conflict_visible", True)),
        exported_state_does_not_override_builtin=bool(
            _attr(row, "exported_state_does_not_override_builtin", True)
        ),
        future_policy_required=bool(_attr(row, "future_policy_required", True)),
    )


def _unsafe_claim_rows(
    unsafe_claims: Sequence[object],
    candidate_rows: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryUnsafeClaimRow, ...]:
    rows = [_unsafe_claim_row(claim) for claim in unsafe_claims]
    for candidate in candidate_rows:
        if OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM in candidate.diagnostics:
            rows.append(
                OptionalSolverPluginManifestExportSummaryUnsafeClaimRow(
                    claim_id=f"{candidate.stack_id}:unsafe_claim",
                    related_candidate_id=candidate.stack_id,
                    related_source_id=candidate.source_id,
                    claim_text="Unsafe claim remains blocked.",
                )
            )
    return tuple(sorted(rows, key=lambda row: row.claim_id))


def _unsafe_claim_row(
    row: object,
) -> OptionalSolverPluginManifestExportSummaryUnsafeClaimRow:
    return OptionalSolverPluginManifestExportSummaryUnsafeClaimRow(
        claim_id=str(_attr(row, "claim_id", "unsafe_claim") or "unsafe_claim"),
        related_candidate_id=str(
            _attr(row, "related_candidate_id", _attr(row, "related", "")) or ""
        ),
        related_source_id=str(_attr(row, "related_source_id", "") or ""),
        claim_text=str(_attr(row, "claim_text", "") or ""),
        blocked=bool(_attr(row, "blocked", True)),
        warning_text=str(
            _attr(
                row,
                "warning_text",
                "Unsafe claims are not accepted by export summaries.",
            )
            or ""
        ),
        accepted_by_export_summary=bool(
            _attr(row, "accepted_by_export_summary", False)
        ),
    )


def _evidence_history_rows(
    evidence_history: Sequence[object],
    candidate_rows: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow, ...]:
    rows = [_evidence_history_row(row) for row in evidence_history]
    if not rows and candidate_rows:
        rows = [
            OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow(
                stack_id=candidate.stack_id,
                deactivation_history_retained=True,
                reactivation_history_retained=True,
                historical_validation_evidence_retained=True,
            )
            for candidate in candidate_rows
        ]
    if not rows:
        rows = [OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow()]
    return tuple(sorted(rows, key=lambda row: row.stack_id))


def _evidence_history_row(
    row: object,
) -> OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow:
    return OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow(
        deactivation_history_retained=bool(
            _attr(row, "deactivation_history_retained", True)
        ),
        reactivation_history_retained=bool(
            _attr(row, "reactivation_history_retained", True)
        ),
        historical_validation_evidence_retained=bool(
            _attr(row, "historical_validation_evidence_retained", True)
        ),
        skipped_missing_remains_skipped_missing=bool(
            _attr(row, "skipped_missing_remains_skipped_missing", True)
        ),
        issue_closure_implied=bool(_attr(row, "issue_closure_implied", False)),
        validation_success_claimed=bool(
            _attr(row, "validation_success_claimed", False)
        ),
        validation_failure_claimed=bool(
            _attr(row, "validation_failure_claimed", False)
        ),
        evidence_deleted_or_rewritten=bool(
            _attr(row, "evidence_deleted_or_rewritten", False)
        ),
        export_summary_is_not_validation_evidence=bool(
            _attr(row, "export_summary_is_not_validation_evidence", True)
        ),
        stack_id=str(_attr(row, "stack_id", "") or ""),
    )


def _limitation_rows(
    limitations: Sequence[object],
) -> tuple[OptionalSolverPluginManifestExportSummaryLimitationRow, ...]:
    rows = [_limitation_row(row) for row in limitations]
    rows.extend(_default_limitations())
    return tuple(
        sorted(
            _dedupe_limitations(rows),
            key=lambda row: (row.related_section, row.limitation_id),
        )
    )


def _limitation_row(
    row: object,
) -> OptionalSolverPluginManifestExportSummaryLimitationRow:
    return OptionalSolverPluginManifestExportSummaryLimitationRow(
        limitation_id=str(_attr(row, "limitation_id", "limitation") or "limitation"),
        title=str(_attr(row, "title", "Limitation") or "Limitation"),
        message=str(_attr(row, "message", "") or ""),
        severity=str(_attr(row, "severity", "info") or "info"),
        related_section=str(_attr(row, "related_section", "") or ""),
        related_source_id=str(_attr(row, "related_source_id", "") or ""),
        related_candidate_id=str(_attr(row, "related_candidate_id", "") or ""),
        must_show=bool(_attr(row, "must_show", True)),
    )


def _readiness(
    *,
    source_rows: Sequence[OptionalSolverPluginManifestExportSummarySourceRow],
    candidate_rows: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestExportSummaryAcknowledgementRow
    ],
    redaction_rows: Sequence[OptionalSolverPluginManifestExportSummaryRedactionRow],
    stale_rows: Sequence[OptionalSolverPluginManifestExportSummaryStaleSourceRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestExportSummaryConflictRow],
    unsafe_rows: Sequence[OptionalSolverPluginManifestExportSummaryUnsafeClaimRow],
    export_summary_requested: bool,
    future_file_export_required: bool,
    future_clipboard_required: bool,
    future_report_attachment_required: bool,
    future_reloadable_bundle_required: bool,
) -> OptionalSolverPluginManifestExportSummaryReadiness:
    Readiness = OptionalSolverPluginManifestExportSummaryReadiness
    if not (
        source_rows
        or candidate_rows
        or redaction_rows
        or stale_rows
        or conflict_rows
        or unsafe_rows
    ):
        return Readiness.UNAVAILABLE_NO_STATE
    if not export_summary_requested:
        return Readiness.UNAVAILABLE_NO_EXPLICIT_REQUEST
    if any(row.unredacted_path_blocked for row in redaction_rows) or any(
        row.raw_reference_blocked for row in source_rows
    ):
        return Readiness.BLOCKED_UNREDACTED_PATH
    if _redaction_required(redaction_rows) and not _ack_satisfied(
        acknowledgement_rows, ACK_REDACTION_REVIEWED
    ):
        return Readiness.BLOCKED_REDACTION_REVIEW
    if stale_rows and not _ack_satisfied(
        acknowledgement_rows, ACK_STALE_SOURCE_REQUIRES_REPREVIEW
    ):
        return Readiness.BLOCKED_STALE_SOURCE_REPREVIEW
    if conflict_rows:
        return Readiness.BLOCKED_CONFLICT
    if any(row.blocked for row in unsafe_rows):
        return Readiness.BLOCKED_UNSAFE_CLAIM
    if any(row.required and not row.satisfied for row in acknowledgement_rows):
        return Readiness.BLOCKED_ACKNOWLEDGEMENT
    if future_file_export_required:
        return Readiness.FUTURE_FILE_EXPORT_REQUIRED
    if future_clipboard_required:
        return Readiness.FUTURE_CLIPBOARD_REQUIRED
    if future_report_attachment_required:
        return Readiness.FUTURE_REPORT_ATTACHMENT_REQUIRED
    if future_reloadable_bundle_required:
        return Readiness.FUTURE_RELOADABLE_BUNDLE_REQUIRED
    return Readiness.READY_PREVIEW_ONLY


def _candidate_readiness(
    row: OptionalSolverPluginManifestExportSummaryCandidateRow,
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestExportSummaryAcknowledgementRow
    ],
) -> OptionalSolverPluginManifestExportSummaryReadiness:
    Readiness = OptionalSolverPluginManifestExportSummaryReadiness
    if row.repreview_required or row.stale_source_state == "stale":
        return Readiness.BLOCKED_STALE_SOURCE_REPREVIEW
    if row.shared_stack_indicators:
        return Readiness.BLOCKED_SHARED_STACK_WARNING
    if OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM in row.diagnostics:
        return Readiness.BLOCKED_UNSAFE_CLAIM
    if any(row.required and not row.satisfied for row in acknowledgement_rows):
        return Readiness.BLOCKED_ACKNOWLEDGEMENT
    return Readiness.READY_PREVIEW_ONLY


def _state_for_readiness(
    readiness: OptionalSolverPluginManifestExportSummaryReadiness,
) -> OptionalSolverPluginManifestExportSummaryState:
    State = OptionalSolverPluginManifestExportSummaryState
    Readiness = OptionalSolverPluginManifestExportSummaryReadiness
    if readiness == Readiness.ERROR:
        return State.EXPORT_SUMMARY_ERROR
    if readiness in {
        Readiness.UNAVAILABLE_NO_STATE,
        Readiness.UNAVAILABLE_NO_EXPLICIT_REQUEST,
    }:
        return State.EXPORT_SUMMARY_UNAVAILABLE
    if readiness == Readiness.READY_PREVIEW_ONLY:
        return State.EXPORT_SUMMARY_READY_PREVIEW
    if readiness == Readiness.FUTURE_FILE_EXPORT_REQUIRED:
        return State.EXPORT_SUMMARY_FUTURE_FILE_EXPORT_REQUIRED
    if readiness == Readiness.FUTURE_CLIPBOARD_REQUIRED:
        return State.EXPORT_SUMMARY_FUTURE_CLIPBOARD_REQUIRED
    if readiness == Readiness.FUTURE_REPORT_ATTACHMENT_REQUIRED:
        return State.EXPORT_SUMMARY_FUTURE_REPORT_ATTACHMENT_REQUIRED
    if readiness == Readiness.FUTURE_RELOADABLE_BUNDLE_REQUIRED:
        return State.EXPORT_SUMMARY_FUTURE_RELOADABLE_BUNDLE_REQUIRED
    return State.EXPORT_SUMMARY_BLOCKED


def _blockers_for_readiness(
    readiness: OptionalSolverPluginManifestExportSummaryReadiness,
) -> tuple[str, ...]:
    return {
        OptionalSolverPluginManifestExportSummaryReadiness.UNAVAILABLE_NO_STATE: (
            "No candidate or source state was supplied.",
        ),
        OptionalSolverPluginManifestExportSummaryReadiness.UNAVAILABLE_NO_EXPLICIT_REQUEST: (
            "Export summary requires an explicit caller-supplied request.",
        ),
        OptionalSolverPluginManifestExportSummaryReadiness.BLOCKED_ACKNOWLEDGEMENT: (
            "Required export-summary acknowledgements are missing.",
        ),
        OptionalSolverPluginManifestExportSummaryReadiness.BLOCKED_REDACTION_REVIEW: (
            "Redaction review acknowledgement is missing.",
        ),
        OptionalSolverPluginManifestExportSummaryReadiness.BLOCKED_UNREDACTED_PATH: (
            "Unredacted path display is blocked.",
        ),
        OptionalSolverPluginManifestExportSummaryReadiness.BLOCKED_STALE_SOURCE_REPREVIEW: (
            "Stale source requires re-preview.",
        ),
        OptionalSolverPluginManifestExportSummaryReadiness.BLOCKED_CONFLICT: (
            "Built-ins win by default; conflict remains visible.",
        ),
        OptionalSolverPluginManifestExportSummaryReadiness.BLOCKED_SHARED_STACK_WARNING: (
            "Shared-stack warning remains visible.",
        ),
        OptionalSolverPluginManifestExportSummaryReadiness.BLOCKED_UNSAFE_CLAIM: (
            "Unsafe claims are not accepted by export summaries.",
        ),
        OptionalSolverPluginManifestExportSummaryReadiness.ERROR: (
            "Supplied export-summary state is an error.",
        ),
    }.get(readiness, ())


def _diagnostics(
    *,
    readiness: OptionalSolverPluginManifestExportSummaryReadiness,
    source_rows: Sequence[OptionalSolverPluginManifestExportSummarySourceRow],
    candidate_rows: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestExportSummaryAcknowledgementRow
    ],
    redaction_rows: Sequence[OptionalSolverPluginManifestExportSummaryRedactionRow],
    stale_rows: Sequence[OptionalSolverPluginManifestExportSummaryStaleSourceRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestExportSummaryConflictRow],
    unsafe_rows: Sequence[OptionalSolverPluginManifestExportSummaryUnsafeClaimRow],
    evidence_rows: Sequence[
        OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow
    ],
    supplied_diagnostics: Sequence[
        OptionalSolverPluginManifestExportSummaryDiagnosticRow
    ],
) -> tuple[OptionalSolverPluginManifestExportSummaryDiagnosticRow, ...]:
    rows: list[OptionalSolverPluginManifestExportSummaryDiagnosticRow] = []

    def add(code: str, severity: str = "info", blocker: bool = False) -> None:
        rows.append(
            OptionalSolverPluginManifestExportSummaryDiagnosticRow(
                severity=severity,
                category="export_summary",
                code=code,
                message=_diagnostic_message(code),
                suggested_fix=_diagnostic_fix(code),
                blocker=blocker,
            )
        )

    rows.extend(supplied_diagnostics)
    add(OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED)
    add(OSPMG_EXPORT_SUMMARY_NOT_VALIDATION)
    add(OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE)
    add(OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE)
    add(OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE)
    add(OSPMG_EXPORT_SUMMARY_NO_INSTALL)
    add(OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION)
    add(OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE)
    add(OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION)
    add(OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION)
    add(OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT)
    add(OSPMG_EXPORT_SUMMARY_FUTURE_GATE)
    if any(row.required and not row.satisfied for row in acknowledgement_rows):
        add(OSPMG_EXPORT_SUMMARY_ACK_REQUIRED, "warning", blocker=True)
    if redaction_rows:
        add(OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED, "info")
    if any(row.unredacted_path_blocked for row in redaction_rows) or any(
        row.raw_reference_blocked for row in source_rows
    ):
        add(OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED, "error", blocker=True)
    if stale_rows:
        add(
            OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED,
            "warning",
            blocker=True,
        )
    if any(
        row.trust_label not in {"built_in", "reviewed_builtin"}
        for row in source_rows
    ) or any(row.is_untrusted for row in candidate_rows):
        add(OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE, "warning")
    if conflict_rows:
        add(OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED, "warning", blocker=True)
    if unsafe_rows:
        add(OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM, "error", blocker=True)
    if any(row.historical_validation_evidence_retained for row in evidence_rows):
        add(OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED)
    if any(
        row.deactivation_history_retained or row.reactivation_history_retained
        for row in evidence_rows
    ):
        add(OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED)
    if readiness == OptionalSolverPluginManifestExportSummaryReadiness.ERROR:
        rows.append(
            OptionalSolverPluginManifestExportSummaryDiagnosticRow(
                severity="error",
                category="export_summary",
                code="OSPMG_EXPORT_SUMMARY_ERROR",
                message="Supplied export-summary state is an error.",
                blocker=True,
            )
        )
    return _dedupe_diagnostics(rows)


def _diagnostic_row(
    row: object,
) -> OptionalSolverPluginManifestExportSummaryDiagnosticRow:
    code = _translate_code(str(_attr(row, "code", "") or ""))
    return OptionalSolverPluginManifestExportSummaryDiagnosticRow(
        severity=str(_attr(row, "severity", "info") or "info"),
        category=str(_attr(row, "category", "export_summary") or "export_summary"),
        code=code or OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED,
        message=str(_attr(row, "message", "") or _diagnostic_message(code)),
        source_reference_display=str(_attr(row, "source_reference_display", "") or ""),
        stack_id=str(_attr(row, "stack_id", "") or ""),
        suggested_fix=str(_attr(row, "suggested_fix", "") or _diagnostic_fix(code)),
        blocker=bool(_attr(row, "blocker", False)),
    )


def _diagnostic_message(code: str) -> str:
    return {
        OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED: EXPORT_SUMMARY_NOT_IMPLEMENTED_TEXT,
        OSPMG_EXPORT_SUMMARY_ACK_REQUIRED: (
            "Required export-summary acknowledgements are missing."
        ),
        OSPMG_EXPORT_SUMMARY_NOT_VALIDATION: EXPORT_SUMMARY_NOT_VALIDATION_TEXT,
        OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE: EXPORT_SUMMARY_NOT_PERSISTENCE_TEXT,
        OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE: EXPORT_SUMMARY_NOT_RELOADABLE_TEXT,
        OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE: (
            EXPORT_SUMMARY_NOT_TRUST_RESTORE_TEXT
        ),
        OSPMG_EXPORT_SUMMARY_NO_INSTALL: (
            "Export summaries do not install dependencies."
        ),
        OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION: (
            "Export summaries do not execute solvers."
        ),
        OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE: (
            "Export summaries do not close issues."
        ),
        OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION: (
            "Export summaries do not mutate releases."
        ),
        OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED: (
            "Redaction-first export-summary policy applies."
        ),
        OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED: (
            "An unredacted/raw path is blocked."
        ),
        OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED: (
            "A stale source requires re-preview."
        ),
        OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE: (
            "User/plugin manifests remain untrusted by default."
        ),
        OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED: (
            "A conflict/shared-stack record is visible; built-ins win by default."
        ),
        OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM: (
            "Unsafe claims are not accepted by export summaries."
        ),
        OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED: (
            "Historical validation evidence is retained."
        ),
        OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED: (
            "Deactivation/reactivation history is retained."
        ),
        OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION: (
            "Export summaries do not run discovery."
        ),
        OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT: (
            "Export summaries do not import plugin packages."
        ),
        OSPMG_EXPORT_SUMMARY_FUTURE_GATE: (
            "File export, clipboard, report attachment, reloadable bundles, "
            "GUI, CLI, persistence, discovery, validation, solver execution, "
            "and issue/release actions require future gates."
        ),
    }.get(code, "Export-summary diagnostic.")


def _diagnostic_fix(code: str) -> str:
    if code == OSPMG_EXPORT_SUMMARY_ACK_REQUIRED:
        return "Satisfy required export-summary acknowledgements in caller state."
    if code == OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED:
        return "Use a redacted display reference or a caller-reviewed label."
    if code == OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED:
        return "Re-preview the source in a future explicit source-review gate."
    if code == OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED:
        return "Keep the conflict visible; built-ins win until future policy changes."
    if code == OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM:
        return "Remove validation, issue closure, release, install, or certification claims."
    return ""


def _header(
    *,
    summary_kind: str,
    state_scope: str,
    generated_by_display: str,
    schema_version_display: str,
    readiness: OptionalSolverPluginManifestExportSummaryReadiness,
    state: OptionalSolverPluginManifestExportSummaryState,
    source_rows: Sequence[OptionalSolverPluginManifestExportSummarySourceRow],
    candidate_rows: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestExportSummaryAcknowledgementRow
    ],
    diagnostics: Sequence[OptionalSolverPluginManifestExportSummaryDiagnosticRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestExportSummaryConflictRow],
    unsafe_rows: Sequence[OptionalSolverPluginManifestExportSummaryUnsafeClaimRow],
    stale_rows: Sequence[OptionalSolverPluginManifestExportSummaryStaleSourceRow],
    redaction_rows: Sequence[OptionalSolverPluginManifestExportSummaryRedactionRow],
    evidence_rows: Sequence[
        OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow
    ],
    limitation_rows: Sequence[OptionalSolverPluginManifestExportSummaryLimitationRow],
) -> OptionalSolverPluginManifestExportSummaryHeader:
    warning_count = sum(1 for row in diagnostics if row.severity == "warning")
    error_count = sum(1 for row in diagnostics if row.severity in {"error", "blocker"})
    status_text = (
        "Ready for in-memory preview only."
        if readiness
        == OptionalSolverPluginManifestExportSummaryReadiness.READY_PREVIEW_ONLY
        else "Not ready for export-summary preview."
    )
    return OptionalSolverPluginManifestExportSummaryHeader(
        summary_kind=summary_kind,
        state_scope=state_scope,
        generated_by_display=generated_by_display,
        schema_version_display=schema_version_display,
        source_count=len(source_rows),
        candidate_count=len(candidate_rows),
        acknowledgement_count=len(acknowledgement_rows),
        diagnostic_count=len(diagnostics),
        warning_count=warning_count,
        error_count=error_count,
        conflict_count=len(conflict_rows),
        unsafe_claim_count=len(unsafe_rows),
        stale_source_count=len(stale_rows),
        redaction_required_count=sum(
            1 for row in redaction_rows if row.redaction_required
        ),
        evidence_retained_count=sum(
            1 for row in evidence_rows if row.historical_validation_evidence_retained
        ),
        history_retained_count=sum(
            1
            for row in evidence_rows
            if row.deactivation_history_retained or row.reactivation_history_retained
        ),
        limitations_count=len(limitation_rows),
        readiness=readiness.value,
        export_summary_state=state.value,
        status_text=status_text,
    )


def _sections(
    *,
    header: OptionalSolverPluginManifestExportSummaryHeader,
    source_rows: Sequence[OptionalSolverPluginManifestExportSummarySourceRow],
    candidate_rows: Sequence[OptionalSolverPluginManifestExportSummaryCandidateRow],
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestExportSummaryAcknowledgementRow
    ],
    diagnostics: Sequence[OptionalSolverPluginManifestExportSummaryDiagnosticRow],
    redaction_rows: Sequence[OptionalSolverPluginManifestExportSummaryRedactionRow],
    stale_rows: Sequence[OptionalSolverPluginManifestExportSummaryStaleSourceRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestExportSummaryConflictRow],
    unsafe_rows: Sequence[OptionalSolverPluginManifestExportSummaryUnsafeClaimRow],
    evidence_rows: Sequence[
        OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow
    ],
    limitation_rows: Sequence[OptionalSolverPluginManifestExportSummaryLimitationRow],
    actions: Sequence[OptionalSolverPluginManifestExportSummaryActionState],
) -> tuple[OptionalSolverPluginManifestExportSummarySection, ...]:
    return (
        OptionalSolverPluginManifestExportSummarySection(
            section_id="header",
            title="Export Summary",
            severity="info",
            lines=(
                f"readiness={header.readiness}",
                f"state={header.export_summary_state}",
                EXPORT_SUMMARY_NOT_VALIDATION_TEXT,
                EXPORT_SUMMARY_NOT_PERSISTENCE_TEXT,
            ),
            rows=(header,),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="sources",
            title="Sources And Provenance",
            severity="warning" if any(row.raw_reference_blocked for row in source_rows) else "info",
            rows=tuple(source_rows),
            diagnostics=tuple(code for row in source_rows for code in row.diagnostics),
            blocker=any(row.raw_reference_blocked for row in source_rows),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="candidates",
            title="Candidate State",
            severity="info",
            rows=tuple(candidate_rows),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="acknowledgements",
            title="Acknowledgements",
            severity="warning"
            if any(row.required and not row.satisfied for row in acknowledgement_rows)
            else "info",
            rows=tuple(acknowledgement_rows),
            blocker=any(row.required and not row.satisfied for row in acknowledgement_rows),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="diagnostics",
            title="Diagnostics",
            severity="warning" if diagnostics else "info",
            rows=tuple(diagnostics),
            diagnostics=tuple(row.code for row in diagnostics),
            blocker=any(row.blocker for row in diagnostics),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="redaction",
            title="Redaction And Privacy",
            severity="warning" if redaction_rows else "info",
            rows=tuple(redaction_rows),
            blocker=any(row.unredacted_path_blocked for row in redaction_rows),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="stale_sources",
            title="Stale Sources And Re-Preview",
            severity="warning" if stale_rows else "info",
            rows=tuple(stale_rows),
            blocker=bool(stale_rows),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="conflicts",
            title="Conflicts And Shared Stacks",
            severity="warning" if conflict_rows else "info",
            rows=tuple(conflict_rows),
            blocker=bool(conflict_rows),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="unsafe_claims",
            title="Unsafe Claims",
            severity="error" if unsafe_rows else "info",
            rows=tuple(unsafe_rows),
            blocker=any(row.blocked for row in unsafe_rows),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="evidence_history",
            title="Evidence And History",
            severity="info",
            rows=tuple(evidence_rows),
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="limitations",
            title="Limitations",
            severity="info",
            rows=tuple(limitation_rows),
            limitation=True,
        ),
        OptionalSolverPluginManifestExportSummarySection(
            section_id="actions",
            title="Actions",
            severity="info",
            rows=tuple(actions),
            lines=("Unsafe/future actions are disabled or future-only.",),
        ),
    )


def _text_lines(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> tuple[str, ...]:
    h = view_model.header
    lines = [
        "Optional Solver Plugin Manifest Export Summary",
        f"readiness: {h.readiness}",
        f"state: {h.export_summary_state}",
        f"sources: {h.source_count}",
        f"candidates: {h.candidate_count}",
        f"diagnostics: {h.diagnostic_count}",
        "non-actions: no file export, no file write, no clipboard, no report "
        "attachment, no reloadable bundle, no persistence, no discovery, no "
        "validation, no solver execution, no issue or release mutation",
    ]
    for source in view_model.source_rows:
        lines.append(
            "source: "
            f"{source.source_id} {source.source_type} {source.trust_label} "
            f"{source.source_reference_display}"
        )
    for candidate in view_model.candidate_rows:
        lines.append(
            "candidate: "
            f"{candidate.stack_id} readiness={candidate.readiness} "
            f"trust={candidate.trust_label}"
        )
    for diagnostic in view_model.diagnostics:
        lines.append(f"diagnostic: {diagnostic.severity} {diagnostic.code}")
    return tuple(lines)


def _view_model_to_mapping(
    view_model: OptionalSolverPluginManifestExportSummaryViewModel,
) -> dict[str, object]:
    return {
        "header": _record_to_mapping(view_model.header),
        "sources": [_record_to_mapping(row) for row in view_model.source_rows],
        "candidates": [_record_to_mapping(row) for row in view_model.candidate_rows],
        "acknowledgements": [
            _record_to_mapping(row) for row in view_model.acknowledgement_rows
        ],
        "diagnostics": [_record_to_mapping(row) for row in view_model.diagnostics],
        "redaction": [_record_to_mapping(row) for row in view_model.redaction_rows],
        "stale_sources": [
            _record_to_mapping(row) for row in view_model.stale_source_rows
        ],
        "conflicts": [_record_to_mapping(row) for row in view_model.conflict_rows],
        "unsafe_claims": [
            _record_to_mapping(row) for row in view_model.unsafe_claim_rows
        ],
        "evidence_history": [
            _record_to_mapping(row) for row in view_model.evidence_history_rows
        ],
        "limitations": [
            _record_to_mapping(row) for row in view_model.limitation_rows
        ],
        "non_action_flags": _record_to_mapping(view_model.non_action_flags),
        "actions": [_record_to_mapping(row) for row in view_model.actions],
        "sections": [_record_to_mapping(section) for section in view_model.sections],
        "reserved_diagnostic_codes": list(view_model.reserved_diagnostic_codes),
        "not_validation_evidence": True,
    }


def _record_to_mapping(record: object) -> dict[str, object]:
    result: dict[str, object] = {}
    for slot in getattr(record, "__slots__", ()):
        value = getattr(record, slot)
        result[slot] = _value_to_mapping(value)
    return result


def _value_to_mapping(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__slots__"):
        return _record_to_mapping(value)
    if isinstance(value, tuple):
        return [_value_to_mapping(item) for item in value]
    return value


def _action_states() -> tuple[OptionalSolverPluginManifestExportSummaryActionState, ...]:
    return tuple(
        OptionalSolverPluginManifestExportSummaryActionState(
            action=action,
            label=action.value.replace("_", " "),
            enabled=action.value not in _UNSAFE_ACTIONS,
            available=action.value not in _UNSAFE_ACTIONS,
            reason=_action_reason(action),
            future_action=action.value in _UNSAFE_ACTIONS,
        )
        for action in OptionalSolverPluginManifestExportSummaryAction
    )


def _action_reason(action: OptionalSolverPluginManifestExportSummaryAction) -> str:
    if action.value not in _UNSAFE_ACTIONS:
        return "Display-only in-memory review action."
    return {
        OptionalSolverPluginManifestExportSummaryAction.WRITE_EXPORT_FILE: (
            "File export requires a future explicit write gate."
        ),
        OptionalSolverPluginManifestExportSummaryAction.COPY_TO_CLIPBOARD: (
            "Clipboard behavior requires a future explicit integration gate."
        ),
        OptionalSolverPluginManifestExportSummaryAction.ATTACH_TO_REPORT: (
            "Report attachment requires a future report integration gate."
        ),
        OptionalSolverPluginManifestExportSummaryAction.CREATE_RELOADABLE_BUNDLE: (
            "Reloadable bundles require a future bundle gate."
        ),
        OptionalSolverPluginManifestExportSummaryAction.PERSIST_STATE: (
            "Persistence writers require a future persistence gate."
        ),
        OptionalSolverPluginManifestExportSummaryAction.RELOAD_STATE: (
            "Reload behavior requires a future reload gate."
        ),
        OptionalSolverPluginManifestExportSummaryAction.MUTATE_PROJECT_SCHEMA: (
            "ProjectSchema mutation is out of scope for export summaries."
        ),
        OptionalSolverPluginManifestExportSummaryAction.RUN_DISCOVERY: (
            "Discovery execution is not part of export summaries."
        ),
        OptionalSolverPluginManifestExportSummaryAction.RUN_VALIDATION: (
            "Validation execution is not part of export summaries."
        ),
        OptionalSolverPluginManifestExportSummaryAction.INSTALL_DEPENDENCY: (
            "Dependency installation is out of scope."
        ),
        OptionalSolverPluginManifestExportSummaryAction.UNINSTALL_DEPENDENCY: (
            "Dependency uninstall is out of scope."
        ),
        OptionalSolverPluginManifestExportSummaryAction.UNINSTALL_SOLVER: (
            "Solver uninstall is out of scope."
        ),
        OptionalSolverPluginManifestExportSummaryAction.EXECUTE_SOLVER: (
            "Solver execution is out of scope."
        ),
        OptionalSolverPluginManifestExportSummaryAction.CLOSE_ISSUE: (
            "Issue closure requires a separate issue gate."
        ),
        OptionalSolverPluginManifestExportSummaryAction.MUTATE_RELEASE: (
            "Release mutation requires a separate release gate."
        ),
        OptionalSolverPluginManifestExportSummaryAction.PUSH_TAG: (
            "Tag mutation requires a separate release/tag gate."
        ),
        OptionalSolverPluginManifestExportSummaryAction.UPLOAD_ASSET: (
            "Asset upload requires a separate release asset gate."
        ),
    }[action]


def _redact_reference_details(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool, bool, bool]:
    label = str(provided_label or "").strip()
    if label:
        if _secret_like(label):
            return "<redacted-secret-like-reference>", True, True, True
        display = _basename_if_path(label)
        return display, display != label, display != label, False
    text = str(reference or "").strip()
    if not text:
        return "", False, False, False
    if _secret_like(text):
        return "<redacted-secret-like-reference>", True, True, True
    display = _basename_if_path(text)
    redacted = display != text
    return display, redacted, redacted, False


def _basename_if_path(text: str) -> str:
    normalized = text.replace("\\", "/")
    if "/" in normalized:
        return normalized.rsplit("/", 1)[-1] or "redacted-source"
    if len(text) > 2 and text[1] == ":":
        return text.rsplit(":", 1)[-1] or "redacted-source"
    return text


def _secret_like(text: str) -> bool:
    lowered = text.lower()
    markers = (
        "token=",
        "token:",
        "secret=",
        "secret:",
        "password=",
        "password:",
        "api_key",
        "apikey",
        "credential=",
        "credential:",
        "bearer ",
        "private_key",
    )
    return any(marker in lowered for marker in markers)


def _redaction_privacy_warning(blocked: bool) -> str:
    if blocked:
        return (
            "Raw path or secret-like source references are blocked; use a "
            "redacted display label."
        )
    return (
        "Source references are redacted by default; fingerprints are not trust "
        "signals."
    )


def _redaction_required(
    rows: Sequence[OptionalSolverPluginManifestExportSummaryRedactionRow],
) -> bool:
    return any(row.redaction_required and not row.redaction_reviewed for row in rows)


def _ack_satisfied(
    rows: Sequence[OptionalSolverPluginManifestExportSummaryAcknowledgementRow],
    ack_id: str,
) -> bool:
    return any(row.acknowledgement_id == ack_id and row.satisfied for row in rows)


def _source_by_id(
    rows: Sequence[OptionalSolverPluginManifestExportSummarySourceRow],
    source_id: str,
) -> OptionalSolverPluginManifestExportSummarySourceRow | None:
    return next((row for row in rows if row.source_id == source_id), None)


def _is_built_in(source_type: str, trust_label: str) -> bool:
    return source_type == "built_in" or trust_label in {"built_in", "reviewed_builtin"}


def _translate_code(code: str) -> str:
    if not code:
        return ""
    replacements = (
        ("OSPMG_PERSISTENCE_", "OSPMG_EXPORT_SUMMARY_"),
        ("OSPMG_ACTIVATION_", "OSPMG_EXPORT_SUMMARY_"),
        ("OSPMG_DEACTIVATION_", "OSPMG_EXPORT_SUMMARY_"),
        ("OSPMG_REACTIVATION_", "OSPMG_EXPORT_SUMMARY_"),
        ("OSPMG_DISCOVERY_REFRESH_", "OSPMG_EXPORT_SUMMARY_"),
    )
    translated = code
    for prefix, export_prefix in replacements:
        if translated.startswith(prefix):
            translated = translated.replace(prefix, export_prefix, 1)
    aliases = {
        "OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORATION": (
            OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE
        ),
        "OSPMG_EXPORT_SUMMARY_NO_PLUGIN_PACKAGE_IMPORT": (
            OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT
        ),
    }
    return aliases.get(translated, translated)


def _dedupe_diagnostics(
    rows: Sequence[OptionalSolverPluginManifestExportSummaryDiagnosticRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryDiagnosticRow, ...]:
    seen: set[tuple[str, str]] = set()
    result: list[OptionalSolverPluginManifestExportSummaryDiagnosticRow] = []
    for row in rows:
        key = (row.code, row.stack_id)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return tuple(sorted(result, key=lambda row: (row.severity, row.code, row.stack_id)))


def _dedupe_redaction_rows(
    rows: Sequence[OptionalSolverPluginManifestExportSummaryRedactionRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryRedactionRow, ...]:
    seen: set[tuple[str, str]] = set()
    result: list[OptionalSolverPluginManifestExportSummaryRedactionRow] = []
    for row in rows:
        key = (row.display_reference, row.redaction_status)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return tuple(result)


def _dedupe_stale_rows(
    rows: Sequence[OptionalSolverPluginManifestExportSummaryStaleSourceRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryStaleSourceRow, ...]:
    seen: set[tuple[str, str]] = set()
    result: list[OptionalSolverPluginManifestExportSummaryStaleSourceRow] = []
    for row in rows:
        key = (row.source_reference_display, row.stale_source_state)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return tuple(result)


def _dedupe_limitations(
    rows: Sequence[OptionalSolverPluginManifestExportSummaryLimitationRow],
) -> tuple[OptionalSolverPluginManifestExportSummaryLimitationRow, ...]:
    seen: set[str] = set()
    result: list[OptionalSolverPluginManifestExportSummaryLimitationRow] = []
    for row in rows:
        if row.limitation_id in seen:
            continue
        seen.add(row.limitation_id)
        result.append(row)
    return tuple(result)


def _default_limitations() -> list[OptionalSolverPluginManifestExportSummaryLimitationRow]:
    return [
        OptionalSolverPluginManifestExportSummaryLimitationRow(
            limitation_id="not_validation",
            title="Not validation",
            message=EXPORT_SUMMARY_NOT_VALIDATION_TEXT,
            related_section="limitations",
        ),
        OptionalSolverPluginManifestExportSummaryLimitationRow(
            limitation_id="not_persistence",
            title="Not persistence",
            message=EXPORT_SUMMARY_NOT_PERSISTENCE_TEXT,
            related_section="limitations",
        ),
        OptionalSolverPluginManifestExportSummaryLimitationRow(
            limitation_id="not_reloadable_bundle",
            title="Not reloadable",
            message=EXPORT_SUMMARY_NOT_RELOADABLE_TEXT,
            related_section="limitations",
        ),
        OptionalSolverPluginManifestExportSummaryLimitationRow(
            limitation_id="not_trust_restoration",
            title="Not trust restoration",
            message=EXPORT_SUMMARY_NOT_TRUST_RESTORE_TEXT,
            related_section="limitations",
        ),
        OptionalSolverPluginManifestExportSummaryLimitationRow(
            limitation_id="not_install",
            title="Not dependency installation",
            message="Export summaries do not install dependencies.",
            related_section="limitations",
        ),
        OptionalSolverPluginManifestExportSummaryLimitationRow(
            limitation_id="not_solver_execution",
            title="Not solver execution",
            message="Export summaries do not execute solvers.",
            related_section="limitations",
        ),
        OptionalSolverPluginManifestExportSummaryLimitationRow(
            limitation_id="not_issue_closure",
            title="Not issue closure",
            message="Export summaries do not close issues.",
            related_section="limitations",
        ),
        OptionalSolverPluginManifestExportSummaryLimitationRow(
            limitation_id="not_release_mutation",
            title="Not release mutation",
            message="Export summaries do not mutate releases, tags, or assets.",
            related_section="limitations",
        ),
        OptionalSolverPluginManifestExportSummaryLimitationRow(
            limitation_id="not_certification",
            title="Not certification",
            message=TRUST_NOT_CERTIFICATION_TEXT,
            related_section="limitations",
        ),
    ]


def _ack_warning(ack_id: str) -> str:
    return {
        ACK_EXPORT_NOT_VALIDATION: EXPORT_SUMMARY_NOT_VALIDATION_TEXT,
        ACK_EXPORT_NOT_PERSISTENCE: EXPORT_SUMMARY_NOT_PERSISTENCE_TEXT,
        ACK_EXPORT_NOT_RELOADABLE_BUNDLE: EXPORT_SUMMARY_NOT_RELOADABLE_TEXT,
        ACK_EXPORT_NOT_TRUST_RESTORATION: EXPORT_SUMMARY_NOT_TRUST_RESTORE_TEXT,
        ACK_EXPORT_NOT_INSTALL: "Export summaries do not install dependencies.",
        ACK_EXPORT_NO_SOLVER_EXECUTION: "Export summaries do not execute solvers.",
        ACK_EXPORT_NOT_ISSUE_CLOSURE: "Export summaries do not close issues.",
        ACK_EXPORT_NOT_RELEASE_MUTATION: "Export summaries do not mutate releases.",
        ACK_REDACTION_REVIEWED: "Redaction review is required.",
        ACK_UNREDACTED_PATHS_BLOCKED: "Unredacted paths are blocked.",
        ACK_STALE_SOURCE_REQUIRES_REPREVIEW: "Stale sources require re-preview.",
        ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED: (
            "Untrusted sources remain untrusted."
        ),
        ACK_NO_DISCOVERY_EXECUTION: "Export summaries do not run discovery.",
        ACK_NO_PLUGIN_PACKAGE_IMPORT: (
            "Export summaries do not import plugin packages."
        ),
        ACK_TRUST_LABEL_NOT_CERTIFICATION: TRUST_NOT_CERTIFICATION_TEXT,
    }[ack_id]


def _guidance_text() -> tuple[str, ...]:
    return (
        "Review source provenance, trust labels, redaction, acknowledgements, "
        "stale-source state, conflicts, unsafe claims, and history before future "
        "export surfaces use this view-model.",
        "Export-summary records are in-memory only and are not validation evidence.",
    )


def _safety_text() -> tuple[str, ...]:
    return (
        EXPORT_SUMMARY_NOT_VALIDATION_TEXT,
        EXPORT_SUMMARY_NOT_PERSISTENCE_TEXT,
        EXPORT_SUMMARY_NOT_RELOADABLE_TEXT,
        EXPORT_SUMMARY_NOT_TRUST_RESTORE_TEXT,
        EXPORT_SUMMARY_NOT_AUTOMATIC_ACTIVATION_TEXT,
        "User/plugin manifests remain untrusted by default.",
        "Built-ins remain authoritative by default.",
        "Skipped-missing optional validation remains skipped-missing.",
        "Issues #6 through #11 remain open until a separate validation/issue gate.",
    )


def _attr(value: object, name: str, default: object = "") -> object:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


__all__ = [
    "ACK_EXPORT_NO_SOLVER_EXECUTION",
    "ACK_EXPORT_NOT_INSTALL",
    "ACK_EXPORT_NOT_ISSUE_CLOSURE",
    "ACK_EXPORT_NOT_PERSISTENCE",
    "ACK_EXPORT_NOT_RELEASE_MUTATION",
    "ACK_EXPORT_NOT_RELOADABLE_BUNDLE",
    "ACK_EXPORT_NOT_TRUST_RESTORATION",
    "ACK_EXPORT_NOT_VALIDATION",
    "ACK_NO_DISCOVERY_EXECUTION",
    "ACK_NO_PLUGIN_PACKAGE_IMPORT",
    "ACK_REDACTION_REVIEWED",
    "ACK_STALE_SOURCE_REQUIRES_REPREVIEW",
    "ACK_TRUST_LABEL_NOT_CERTIFICATION",
    "ACK_UNREDACTED_PATHS_BLOCKED",
    "ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED",
    "EXPORT_SUMMARY_BLOCKED_TRANSITIONS",
    "EXPORT_SUMMARY_REQUIRED_ACKS",
    "OSPMG_EXPORT_SUMMARY_ACK_REQUIRED",
    "OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED",
    "OSPMG_EXPORT_SUMMARY_DIAGNOSTIC_CODES",
    "OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED",
    "OSPMG_EXPORT_SUMMARY_FUTURE_GATE",
    "OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED",
    "OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED",
    "OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE",
    "OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE",
    "OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION",
    "OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE",
    "OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE",
    "OSPMG_EXPORT_SUMMARY_NOT_VALIDATION",
    "OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION",
    "OSPMG_EXPORT_SUMMARY_NO_INSTALL",
    "OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT",
    "OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION",
    "OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED",
    "OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED",
    "OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED",
    "OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM",
    "OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE",
    "OptionalSolverPluginManifestExportSummaryAcknowledgementRow",
    "OptionalSolverPluginManifestExportSummaryAction",
    "OptionalSolverPluginManifestExportSummaryActionState",
    "OptionalSolverPluginManifestExportSummaryCandidateRow",
    "OptionalSolverPluginManifestExportSummaryConflictRow",
    "OptionalSolverPluginManifestExportSummaryDiagnosticRow",
    "OptionalSolverPluginManifestExportSummaryEvidenceHistoryRow",
    "OptionalSolverPluginManifestExportSummaryHeader",
    "OptionalSolverPluginManifestExportSummaryLimitationRow",
    "OptionalSolverPluginManifestExportSummaryNonActionFlags",
    "OptionalSolverPluginManifestExportSummaryReadiness",
    "OptionalSolverPluginManifestExportSummaryRedactionRow",
    "OptionalSolverPluginManifestExportSummarySection",
    "OptionalSolverPluginManifestExportSummarySourceRow",
    "OptionalSolverPluginManifestExportSummaryStaleSourceRow",
    "OptionalSolverPluginManifestExportSummaryState",
    "OptionalSolverPluginManifestExportSummaryUnsafeClaimRow",
    "OptionalSolverPluginManifestExportSummaryViewModel",
    "build_optional_solver_plugin_manifest_export_summary_viewmodel",
    "explain_optional_solver_plugin_manifest_export_summary_viewmodel",
    "redact_optional_solver_plugin_manifest_export_summary_source_reference",
    "render_optional_solver_plugin_manifest_export_summary",
    "summarize_optional_solver_plugin_manifest_export_summary_viewmodel",
]
