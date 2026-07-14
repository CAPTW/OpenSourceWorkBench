"""Pure state-writer planning view-model for optional solver plugin manifests.

This module is the OSW-EXP-101 implementation of the state-writer planning
layer designed in OSW-EXP-100. It transforms already-supplied optional solver
plugin manifest UX state into deterministic, redacted, human-reviewable,
non-authoritative write-plan records.

It performs no side effects. It does not implement a writer, write files,
create directories, create runtime state files, create settings files, create
schema files, create export files, create report files, create reloadable
bundles, parse JSON from paths, inspect path existence, import PySide/Qt,
import CLI parser libraries, import plugin packages, scan directories, fetch
URLs, run discovery, run validation, execute solvers, install or uninstall
dependencies, uninstall solvers, mutate ProjectSchema, mutate issues/releases,
mutate tags/assets, or claim validation success/failure or certification. All
state, provenance, acknowledgement, redaction, stale-source, conflict,
unsafe-claim, and evidence inputs are supplied by the caller; this layer only
classifies and renders them in memory.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum

OSPMG_STATE_WRITER_NOT_IMPLEMENTED = "OSPMG_STATE_WRITER_NOT_IMPLEMENTED"
OSPMG_STATE_WRITER_DRY_RUN_ONLY = "OSPMG_STATE_WRITER_DRY_RUN_ONLY"
OSPMG_STATE_WRITER_ACK_REQUIRED = "OSPMG_STATE_WRITER_ACK_REQUIRED"
OSPMG_STATE_WRITER_NOT_VALIDATION = "OSPMG_STATE_WRITER_NOT_VALIDATION"
OSPMG_STATE_WRITER_NOT_TRUST_RESTORE = "OSPMG_STATE_WRITER_NOT_TRUST_RESTORE"
OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION = (
    "OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION"
)
OSPMG_STATE_WRITER_NO_INSTALL = "OSPMG_STATE_WRITER_NO_INSTALL"
OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION = "OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION"
OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE = "OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE"
OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION = (
    "OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION"
)
OSPMG_STATE_WRITER_NOT_CERTIFICATION = "OSPMG_STATE_WRITER_NOT_CERTIFICATION"
OSPMG_STATE_WRITER_REDACTION_REQUIRED = "OSPMG_STATE_WRITER_REDACTION_REQUIRED"
OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED = (
    "OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED"
)
OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED = (
    "OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED"
)
OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED = (
    "OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED"
)
OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED = "OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED"
OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED = (
    "OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED"
)
OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED = (
    "OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED"
)
OSPMG_STATE_WRITER_UNTRUSTED_SOURCE = "OSPMG_STATE_WRITER_UNTRUSTED_SOURCE"
OSPMG_STATE_WRITER_CONFLICT_BLOCKED = "OSPMG_STATE_WRITER_CONFLICT_BLOCKED"
OSPMG_STATE_WRITER_SHARED_STACK_WARNING = (
    "OSPMG_STATE_WRITER_SHARED_STACK_WARNING"
)
OSPMG_STATE_WRITER_UNSAFE_CLAIM = "OSPMG_STATE_WRITER_UNSAFE_CLAIM"
OSPMG_STATE_WRITER_EVIDENCE_RETAINED = "OSPMG_STATE_WRITER_EVIDENCE_RETAINED"
OSPMG_STATE_WRITER_HISTORY_RETAINED = "OSPMG_STATE_WRITER_HISTORY_RETAINED"
OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION = (
    "OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION"
)
OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT = "OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT"
OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED = (
    "OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED"
)
OSPMG_STATE_WRITER_RELOAD_DISABLED = "OSPMG_STATE_WRITER_RELOAD_DISABLED"
OSPMG_STATE_WRITER_EXPORT_DISABLED = "OSPMG_STATE_WRITER_EXPORT_DISABLED"
OSPMG_STATE_WRITER_FUTURE_GATE = "OSPMG_STATE_WRITER_FUTURE_GATE"

OSPMG_STATE_WRITER_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_STATE_WRITER_NOT_IMPLEMENTED,
    OSPMG_STATE_WRITER_DRY_RUN_ONLY,
    OSPMG_STATE_WRITER_ACK_REQUIRED,
    OSPMG_STATE_WRITER_NOT_VALIDATION,
    OSPMG_STATE_WRITER_NOT_TRUST_RESTORE,
    OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION,
    OSPMG_STATE_WRITER_NO_INSTALL,
    OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION,
    OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE,
    OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION,
    OSPMG_STATE_WRITER_NOT_CERTIFICATION,
    OSPMG_STATE_WRITER_REDACTION_REQUIRED,
    OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED,
    OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED,
    OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED,
    OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED,
    OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED,
    OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_STATE_WRITER_UNTRUSTED_SOURCE,
    OSPMG_STATE_WRITER_CONFLICT_BLOCKED,
    OSPMG_STATE_WRITER_SHARED_STACK_WARNING,
    OSPMG_STATE_WRITER_UNSAFE_CLAIM,
    OSPMG_STATE_WRITER_EVIDENCE_RETAINED,
    OSPMG_STATE_WRITER_HISTORY_RETAINED,
    OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION,
    OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT,
    OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED,
    OSPMG_STATE_WRITER_RELOAD_DISABLED,
    OSPMG_STATE_WRITER_EXPORT_DISABLED,
    OSPMG_STATE_WRITER_FUTURE_GATE,
)

ACK_STATE_WRITE_NOT_VALIDATION = "state_write_not_validation"
ACK_STATE_WRITE_NOT_TRUST_RESTORATION = "state_write_not_trust_restoration"
ACK_STATE_WRITE_NOT_AUTOMATIC_ACTIVATION = (
    "state_write_not_automatic_activation"
)
ACK_STATE_WRITE_NOT_DEPENDENCY_INSTALL = "state_write_not_dependency_install"
ACK_STATE_WRITE_NO_SOLVER_EXECUTION = "state_write_no_solver_execution"
ACK_STATE_WRITE_NOT_ISSUE_CLOSURE = "state_write_not_issue_closure"
ACK_STATE_WRITE_NOT_RELEASE_MUTATION = "state_write_not_release_mutation"
ACK_STATE_WRITE_NOT_CERTIFICATION = "state_write_not_certification"
ACK_LOCAL_PATH_REDACTION_REVIEWED = "local_path_redaction_reviewed"
ACK_UNREDACTED_PATHS_BLOCKED = "unredacted_paths_blocked"
ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE = (
    "persisted_acknowledgements_may_expire"
)
ACK_STALE_SOURCE_REQUIRES_REPREVIEW = "stale_source_requires_repreview"
ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED = "untrusted_source_remains_untrusted"
ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD = (
    "activation_review_required_after_reload"
)
ACK_NO_DISCOVERY_EXECUTION = "no_discovery_execution"
ACK_NO_PLUGIN_PACKAGE_IMPORT = "no_plugin_package_import"
ACK_TRUST_LABEL_NOT_CERTIFICATION = "trust_label_not_certification"
ACK_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE = "export_summary_not_reloadable_bundle"

STATE_WRITER_REQUIRED_ACKS: tuple[str, ...] = (
    ACK_STATE_WRITE_NOT_VALIDATION,
    ACK_STATE_WRITE_NOT_TRUST_RESTORATION,
    ACK_STATE_WRITE_NOT_AUTOMATIC_ACTIVATION,
    ACK_STATE_WRITE_NOT_DEPENDENCY_INSTALL,
    ACK_STATE_WRITE_NO_SOLVER_EXECUTION,
    ACK_STATE_WRITE_NOT_ISSUE_CLOSURE,
    ACK_STATE_WRITE_NOT_RELEASE_MUTATION,
    ACK_STATE_WRITE_NOT_CERTIFICATION,
    ACK_LOCAL_PATH_REDACTION_REVIEWED,
    ACK_UNREDACTED_PATHS_BLOCKED,
    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
    ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_TRUST_LABEL_NOT_CERTIFICATION,
    ACK_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE,
)

_ACK_LABELS: dict[str, str] = {
    ACK_STATE_WRITE_NOT_VALIDATION: (
        "I understand persisted state is not validation evidence."
    ),
    ACK_STATE_WRITE_NOT_TRUST_RESTORATION: (
        "I understand persisted state does not restore trust."
    ),
    ACK_STATE_WRITE_NOT_AUTOMATIC_ACTIVATION: (
        "I understand persisted state does not automatically activate candidates."
    ),
    ACK_STATE_WRITE_NOT_DEPENDENCY_INSTALL: (
        "I understand persisted state does not install dependencies."
    ),
    ACK_STATE_WRITE_NO_SOLVER_EXECUTION: (
        "I understand persisted state does not execute solvers."
    ),
    ACK_STATE_WRITE_NOT_ISSUE_CLOSURE: (
        "I understand persisted state does not close issues."
    ),
    ACK_STATE_WRITE_NOT_RELEASE_MUTATION: (
        "I understand persisted state does not mutate releases."
    ),
    ACK_STATE_WRITE_NOT_CERTIFICATION: (
        "I understand persisted state is not certification."
    ),
    ACK_LOCAL_PATH_REDACTION_REVIEWED: "I reviewed local path redaction.",
    ACK_UNREDACTED_PATHS_BLOCKED: "I understand unredacted paths are blocked.",
    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE: (
        "I understand persisted acknowledgements may expire."
    ),
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW: (
        "I understand stale sources require re-preview."
    ),
    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED: (
        "I understand untrusted sources remain untrusted."
    ),
    ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD: (
        "I understand activation must be reviewed after reload."
    ),
    ACK_NO_DISCOVERY_EXECUTION: (
        "I understand state writing does not run discovery."
    ),
    ACK_NO_PLUGIN_PACKAGE_IMPORT: (
        "I understand state writing does not import plugin packages."
    ),
    ACK_TRUST_LABEL_NOT_CERTIFICATION: (
        "I understand a trust label is not certification."
    ),
    ACK_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE: (
        "I understand export summaries are not reloadable bundles."
    ),
}

STATE_WRITER_NOT_VALIDATION_TEXT = "Persisted state is not validation evidence."
STATE_WRITER_NOT_TRUST_RESTORE_TEXT = "Persisted state does not restore trust."
STATE_WRITER_NOT_AUTOMATIC_ACTIVATION_TEXT = (
    "Persisted state does not automatically activate candidates."
)
TRUST_NOT_CERTIFICATION_TEXT = "A trust label is not certification."
STATE_SCHEMA_NOT_PROJECT_SCHEMA_TEXT = (
    "State-writer schema records are not ProjectSchema records."
)


class OptionalSolverPluginManifestStateWriterReadiness(str, Enum):
    """Readiness vocabulary for future state-writer planning."""

    UNAVAILABLE_NO_STATE = "unavailable_no_state"
    UNAVAILABLE_NO_EXPLICIT_REQUEST = "unavailable_no_explicit_request"
    DRY_RUN_ONLY = "dry_run_only"
    BLOCKED_ACKNOWLEDGEMENT = "blocked_acknowledgement"
    BLOCKED_REDACTION_REVIEW = "blocked_redaction_review"
    BLOCKED_UNREDACTED_PATH = "blocked_unredacted_path"
    BLOCKED_SECRET_LIKE_CONTENT = "blocked_secret_like_content"
    BLOCKED_SCHEMA_VERSION_MISSING = "blocked_schema_version_missing"
    BLOCKED_SCHEMA_UNSUPPORTED = "blocked_schema_unsupported"
    BLOCKED_SCHEMA_MIGRATION_REQUIRED = "blocked_schema_migration_required"
    BLOCKED_STALE_SOURCE_REPREVIEW = "blocked_stale_source_repreview"
    BLOCKED_CONFLICT = "blocked_conflict"
    BLOCKED_SHARED_STACK_WARNING = "blocked_shared_stack_warning"
    BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_claim"
    READY_FOR_FUTURE_WRITE = "ready_for_future_write"
    FUTURE_WRITER_REQUIRED = "future_writer_required"
    ERROR = "error"


class OptionalSolverPluginManifestStateWriterAction(str, Enum):
    """Display-only current and future actions surfaced by the view-model."""

    REQUEST_DRY_RUN = "request_dry_run"
    REVIEW_WRITE_PLAN = "review_write_plan"
    REVIEW_REDACTION = "review_redaction"
    REVIEW_SCHEMA = "review_schema"
    REVIEW_MIGRATION = "review_migration"
    REVIEW_STALE_SOURCE = "review_stale_source"
    REVIEW_CONFLICT = "review_conflict"
    REVIEW_UNSAFE_CLAIM = "review_unsafe_claim"
    ACKNOWLEDGE_SAFETY = "acknowledge_safety"
    WRITE_STATE_FILE = "write_state_file"
    CREATE_RUNTIME_STATE_FILE = "create_runtime_state_file"
    CREATE_SETTINGS_FILE = "create_settings_file"
    CREATE_SCHEMA_FILE = "create_schema_file"
    CREATE_EXPORT_FILE = "create_export_file"
    CREATE_REPORT_FILE = "create_report_file"
    CREATE_RELOADABLE_BUNDLE = "create_reloadable_bundle"
    MUTATE_PROJECT_SCHEMA = "mutate_project_schema"
    RELOAD_STATE = "reload_state"
    EXPORT_STATE = "export_state"
    COPY_TO_CLIPBOARD = "copy_to_clipboard"
    ATTACH_REPORT = "attach_report"
    OPEN_OUTPUT_FOLDER = "open_output_folder"
    IMPORT_PLUGIN_PACKAGE = "import_plugin_package"
    SCAN_DIRECTORY = "scan_directory"
    FETCH_NETWORK_MANIFEST = "fetch_network_manifest"
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


_SAFE_REVIEW_ACTIONS: frozenset[str] = frozenset(
    {
        OptionalSolverPluginManifestStateWriterAction.REQUEST_DRY_RUN.value,
        OptionalSolverPluginManifestStateWriterAction.REVIEW_WRITE_PLAN.value,
        OptionalSolverPluginManifestStateWriterAction.REVIEW_REDACTION.value,
        OptionalSolverPluginManifestStateWriterAction.REVIEW_SCHEMA.value,
        OptionalSolverPluginManifestStateWriterAction.REVIEW_MIGRATION.value,
        OptionalSolverPluginManifestStateWriterAction.REVIEW_STALE_SOURCE.value,
        OptionalSolverPluginManifestStateWriterAction.REVIEW_CONFLICT.value,
        OptionalSolverPluginManifestStateWriterAction.REVIEW_UNSAFE_CLAIM.value,
        OptionalSolverPluginManifestStateWriterAction.ACKNOWLEDGE_SAFETY.value,
    }
)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterDiagnosticRow:
    """Diagnostic emitted by the state-writer planning layer."""

    severity: str
    category: str
    code: str
    message: str
    source_reference_display: str = ""
    stack_id: str = ""
    suggested_fix: str = ""
    blocker: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterStorageOption:
    """Future storage option record; no option is writable in this gate."""

    storage_option_id: str
    label: str
    description: str
    default_selected: bool = False
    allowed_in_this_gate: bool = False
    future_only: bool = True
    privacy_risk: str = ""
    stale_state_risk: str = ""
    project_schema_confusion_risk: str = ""
    portability_risk: str = ""
    cleanup_risk: str = ""
    diagnostics: tuple[str, ...] = (OSPMG_STATE_WRITER_FUTURE_GATE,)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterWritePlan:
    """In-memory write-plan record. All write flags remain false."""

    plan_id: str
    readiness: OptionalSolverPluginManifestStateWriterReadiness
    state_scope: str
    schema_version_display: str
    target_reference_display: str
    target_reference_redacted: bool
    target_reference_approved: bool
    would_write: bool = False
    would_create_directory: bool = False
    would_mutate_project_schema: bool = False
    would_reload: bool = False
    would_export: bool = False
    planned_storage_option_count: int = 0
    planned_source_count: int = 0
    planned_candidate_count: int = 0
    planned_acknowledgement_count: int = 0
    planned_diagnostic_count: int = 0
    planned_warning_count: int = 0
    planned_error_count: int = 0
    planned_blocker_count: int = 0
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterFileFormatBoundary:
    """Conceptual file-format/schema boundary for future writers."""

    format_kind: str = "state_writer_payload"
    conceptual_format: str = "versioned_json_compatible_mapping"
    schema_version_required: bool = True
    schema_version_supported: bool = True
    schema_migration_required: bool = False
    schema_file_created: bool = False
    actual_json_writer_implemented: bool = False
    stable_keys_required: bool = True
    deterministic_ordering_required: bool = True
    redaction_metadata_required: bool = True
    migration_notes_retained: bool = True
    project_schema_state: str = "not_project_schema"
    diagnostics: tuple[str, ...] = (OSPMG_STATE_WRITER_FUTURE_GATE,)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterSourceRow:
    """Source/provenance record used by a future write plan."""

    source_id: str
    source_type: str = "user_selected_json_file"
    source_label: str = "Optional solver plugin manifest source"
    source_reference_display: str = ""
    source_reference_redacted: bool = True
    trust_label: str = "untrusted_user_file"
    persisted_state_kind: str = "state_writer_preview"
    source_fingerprint_display: str = ""
    stale_source_state: str = "current"
    repreview_required: bool = False
    raw_reference_blocked: bool = False
    trust_label_not_certification: bool = True
    persisted_state_is_not_validation_evidence: bool = True
    persisted_state_is_not_trust_restoration: bool = True
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterCandidateRow:
    """Candidate state planned for future persistence."""

    stack_id: str
    display_name: str = ""
    source_id: str = ""
    source_type: str = "user_selected_json_file"
    trust_label: str = "untrusted_user_file"
    activation_state: str = "inactive_preview"
    deactivation_state: str = "not_deactivated"
    reactivation_state: str = "not_requested"
    discovery_refresh_state: str = "not_refreshed"
    persistence_state: str = "session_only"
    writer_state: str = "writer_planning_only"
    readiness: str = "unavailable_no_state"
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    required_acknowledgements: tuple[str, ...] = STATE_WRITER_REQUIRED_ACKS
    diagnostics: tuple[str, ...] = ()
    stale_source_state: str = "current"
    repreview_required: bool = False
    redaction_status: str = "redacted"
    built_in_relationship: str = "not_built_in"
    shared_stack_indicators: tuple[str, ...] = ()
    deactivation_history_state: str = "retained_if_supplied"
    reactivation_history_state: str = "retained_if_supplied"
    historical_evidence_state: str = "retained_as_reference"
    validation_evidence_state: str = "not_validation_evidence"
    issue_closure_implied: bool = False
    automatic_activation_implied: bool = False
    trust_restoration_implied: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterAcknowledgementRow:
    """Acknowledgement and expiry policy record."""

    acknowledgement_id: str
    label: str
    required: bool = True
    satisfied: bool = False
    persisted: bool = False
    expires_on_reload: bool = True
    expires_on_source_fingerprint_change: bool = True
    expires_on_schema_change: bool = True
    expires_on_unsafe_claim_change: bool = True
    expires_on_trust_policy_change: bool = True
    blocking: bool = True
    reason: str = ""
    related_candidate_id: str = ""
    related_source_id: str = ""
    warning_text: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterRedactionRow:
    """Redaction/privacy record for source and target references."""

    raw_reference_supplied: bool
    display_reference: str
    redaction_status: str
    redaction_required: bool
    unredacted_path_blocked: bool
    secret_like_content_blocked: bool
    redaction_reviewed: bool
    privacy_warning: str
    fingerprint_is_not_trust_signal: bool = True
    safe_to_share: bool = False
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterSchemaMigrationRow:
    """Schema/migration readiness record."""

    schema_version_display: str
    schema_version_required: bool = True
    schema_supported: bool = True
    schema_unsupported_blocking: bool = False
    migration_required: bool = False
    migration_executed: bool = False
    migration_notes: str = ""
    schema_file_created: bool = False
    state_schema_is_not_project_schema: bool = True
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterStaleSourceRow:
    """Stale-source/re-preview policy record."""

    stale_source_state: str
    repreview_required: bool
    source_reference_display: str
    old_preview_not_silently_trusted: bool = True
    no_file_io_performed: bool = True
    no_file_restoration_performed: bool = True
    no_file_rewrite_performed: bool = True
    no_file_deletion_performed: bool = True
    future_policy_required: bool = True
    blocks_future_write: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterConflictRow:
    """Conflict/shared-stack policy record."""

    stack_id: str
    built_in_source_id: str = ""
    user_source_id: str = ""
    plugin_source_id: str = ""
    built_in_source_state: str = "authoritative"
    user_source_state: str = "untrusted"
    plugin_source_state: str = "untrusted"
    persistence_state: str = "session_only"
    writer_state: str = "conflict_review_required"
    built_ins_win_by_default: bool = True
    conflict_visible: bool = True
    persisted_state_does_not_override_builtin: bool = True
    shared_stack_warning_ack_required: bool = True
    future_policy_required: bool = True
    blocks_future_write: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterUnsafeClaimRow:
    """Unsafe claim that must not be accepted as truth."""

    claim_id: str
    related_candidate_id: str = ""
    related_source_id: str = ""
    claim_text: str = ""
    blocked: bool = True
    warning_text: str = "Unsafe claims are blocked by the state-writer plan."
    accepted_by_writer: bool = False
    persisted_as_truth: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterEvidenceHistoryRow:
    """Evidence/history retention record."""

    deactivation_history_retained: bool = True
    reactivation_history_retained: bool = True
    historical_validation_evidence_retained: bool = True
    skipped_missing_remains_skipped_missing: bool = True
    issue_closure_rewritten: bool = False
    validation_evidence_rewritten: bool = False
    historical_evidence_rewritten: bool = False
    writer_state_is_not_validation_evidence: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterAtomicityPlanRow:
    """Future atomicity/error handling policy record."""

    write_plan_first_required: bool = True
    target_path_policy_required: bool = True
    atomic_temp_replace_future_required: bool = True
    diagnostic_path_redaction_reserved: bool = True
    diagnostic_atomic_failure_reserved: bool = True
    diagnostic_permission_failure_reserved: bool = True
    rollback_policy_future_required: bool = True
    no_partial_write_claim_in_this_gate: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterNonActionFlags:
    """Flags that must remain false for this planning-only gate."""

    writer_implemented: bool = False
    dry_run_performed: bool = False
    file_write_performed: bool = False
    runtime_state_file_created: bool = False
    settings_file_created: bool = False
    schema_file_created: bool = False
    export_file_created: bool = False
    report_file_created: bool = False
    reloadable_bundle_created: bool = False
    project_schema_mutation_performed: bool = False
    gui_behavior_added: bool = False
    cli_behavior_added: bool = False
    reload_behavior_added: bool = False
    export_behavior_added: bool = False
    clipboard_performed: bool = False
    report_attachment_performed: bool = False
    open_output_folder_performed: bool = False
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
    certification_claimed: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterActionState:
    """Display-only state for current and future actions."""

    action: OptionalSolverPluginManifestStateWriterAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterSection:
    """Simple section summary for renderers."""

    section_id: str
    title: str
    row_count: int
    diagnostic_count: int = 0
    blocker_count: int = 0


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterSummary:
    """Header/summary record for state-writer planning."""

    writer_kind: str
    state_scope: str
    generated_by_display: str
    schema_version_display: str
    writer_version_display: str
    readiness: OptionalSolverPluginManifestStateWriterReadiness
    writer_state: str
    storage_option_count: int
    source_count: int
    candidate_count: int
    acknowledgement_count: int
    required_acknowledgement_count: int
    satisfied_acknowledgement_count: int
    diagnostic_count: int
    warning_count: int
    error_count: int
    blocker_count: int
    conflict_count: int
    unsafe_claim_count: int
    stale_source_count: int
    redaction_required_count: int
    schema_issue_count: int
    migration_required_count: int
    evidence_history_count: int
    evidence_retained_count: int
    history_retained_count: int
    dry_run_performed: bool = False
    writer_performed: bool = False
    file_write_performed: bool = False
    runtime_state_file_created: bool = False
    settings_file_created: bool = False
    schema_file_created: bool = False
    export_file_created: bool = False
    report_file_created: bool = False
    reloadable_bundle_created: bool = False
    project_schema_mutation_performed: bool = False
    validation_success_claimed: bool = False
    validation_failure_claimed: bool = False
    issue_closure_claimed: bool = False
    release_mutation_performed: bool = False
    certification_claimed: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestStateWriterViewModel:
    """Complete pure state-writer planning view-model."""

    summary: OptionalSolverPluginManifestStateWriterSummary
    sections: tuple[OptionalSolverPluginManifestStateWriterSection, ...]
    storage_options: tuple[OptionalSolverPluginManifestStateWriterStorageOption, ...]
    write_plans: tuple[OptionalSolverPluginManifestStateWriterWritePlan, ...]
    file_format_boundaries: tuple[
        OptionalSolverPluginManifestStateWriterFileFormatBoundary, ...
    ]
    source_rows: tuple[OptionalSolverPluginManifestStateWriterSourceRow, ...] = ()
    candidate_rows: tuple[OptionalSolverPluginManifestStateWriterCandidateRow, ...] = ()
    acknowledgement_rows: tuple[
        OptionalSolverPluginManifestStateWriterAcknowledgementRow, ...
    ] = ()
    diagnostics: tuple[OptionalSolverPluginManifestStateWriterDiagnosticRow, ...] = ()
    redaction_rows: tuple[OptionalSolverPluginManifestStateWriterRedactionRow, ...] = ()
    schema_migration_rows: tuple[
        OptionalSolverPluginManifestStateWriterSchemaMigrationRow, ...
    ] = ()
    stale_source_rows: tuple[
        OptionalSolverPluginManifestStateWriterStaleSourceRow, ...
    ] = ()
    conflict_rows: tuple[OptionalSolverPluginManifestStateWriterConflictRow, ...] = ()
    unsafe_claim_rows: tuple[
        OptionalSolverPluginManifestStateWriterUnsafeClaimRow, ...
    ] = ()
    evidence_history_rows: tuple[
        OptionalSolverPluginManifestStateWriterEvidenceHistoryRow, ...
    ] = ()
    atomicity_plan_rows: tuple[
        OptionalSolverPluginManifestStateWriterAtomicityPlanRow, ...
    ] = (OptionalSolverPluginManifestStateWriterAtomicityPlanRow(),)
    non_action_flags: OptionalSolverPluginManifestStateWriterNonActionFlags = (
        OptionalSolverPluginManifestStateWriterNonActionFlags()
    )
    actions: tuple[OptionalSolverPluginManifestStateWriterActionState, ...] = ()
    guidance_text: tuple[str, ...] = ()
    safety_text: tuple[str, ...] = ()
    reserved_diagnostic_codes: tuple[str, ...] = OSPMG_STATE_WRITER_DIAGNOSTIC_CODES
    not_validation_evidence: bool = True

    @classmethod
    def unavailable(
        cls,
        *,
        state_scope: str = "session_only",
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            state_scope=state_scope,
            explicit_write_request=False,
            schema_version_display="",
            schema_version_present=False,
            acknowledgements={},
        )

    @classmethod
    def dry_run_only(
        cls,
        *,
        sources: Sequence[object] = (),
        candidates: Sequence[object] = (),
        acknowledgements: Mapping[str, bool] | Sequence[object] | None = None,
        schema_version_display: str = "osw-exp-101-preview",
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=sources,
            candidates=candidates,
            acknowledgements=acknowledgements,
            schema_version_display=schema_version_display,
            dry_run_requested=True,
            future_write_requested=False,
        )

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
        storage_options: Sequence[object] = (),
        file_format_boundaries: Sequence[object] = (),
        state_scope: str = "session_only",
        generated_by_display: str = "OSW optional solver plugin manifest UX",
        schema_version_display: str = "osw-exp-101-preview",
        schema_version_present: bool = True,
        schema_version_supported: bool = True,
        schema_migration_required: bool = False,
        schema_migration_notes: str = "",
        writer_version_display: str = "osw-exp-101-preview",
        explicit_write_request: bool = True,
        dry_run_requested: bool = False,
        future_write_requested: bool = True,
        redaction_reviewed: bool = True,
        future_writer_required: bool = False,
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=sources,
            candidates=candidates,
            acknowledgements=acknowledgements,
            diagnostics=diagnostics,
            redaction_rows=redaction_rows,
            stale_source_rows=stale_source_rows,
            conflicts=conflicts,
            unsafe_claims=unsafe_claims,
            evidence_history=evidence_history,
            storage_options=storage_options,
            file_format_boundaries=file_format_boundaries,
            state_scope=state_scope,
            generated_by_display=generated_by_display,
            schema_version_display=schema_version_display,
            schema_version_present=schema_version_present,
            schema_version_supported=schema_version_supported,
            schema_migration_required=schema_migration_required,
            schema_migration_notes=schema_migration_notes,
            writer_version_display=writer_version_display,
            explicit_write_request=explicit_write_request,
            dry_run_requested=dry_run_requested,
            future_write_requested=future_write_requested,
            redaction_reviewed=redaction_reviewed,
            future_writer_required=future_writer_required,
        )

    @classmethod
    def from_persistence_viewmodel(
        cls,
        view_model: object,
        *,
        acknowledgements: Mapping[str, bool] | Sequence[object] | None = None,
        explicit_write_request: bool = True,
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        mapping = _object_to_supplied_mapping(view_model)
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=_extract_sequence(mapping, "sources", "source_rows"),
            candidates=_extract_sequence(mapping, "candidates", "candidate_rows"),
            acknowledgements=acknowledgements
            if acknowledgements is not None
            else _extract_sequence(mapping, "acknowledgements", "acknowledgement_rows"),
            diagnostics=_extract_sequence(mapping, "diagnostics"),
            redaction_rows=_extract_sequence(mapping, "redaction", "redaction_rows"),
            stale_source_rows=_extract_sequence(
                mapping, "stale_sources", "stale_source_rows"
            ),
            conflicts=_extract_sequence(mapping, "conflicts", "conflict_rows"),
            unsafe_claims=_extract_sequence(
                mapping, "unsafe_claims", "unsafe_claim_rows"
            ),
            evidence_history=_extract_sequence(
                mapping, "evidence_history", "evidence_history_rows"
            ),
            explicit_write_request=explicit_write_request,
        )

    @classmethod
    def from_schema_model(
        cls,
        schema_model: object,
        *,
        acknowledgements: Mapping[str, bool] | Sequence[object] | None = None,
        explicit_write_request: bool = True,
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        mapping = _object_to_supplied_mapping(schema_model)
        schema_mapping = _extract_first_mapping(mapping, "schema_migration")
        header_mapping = _extract_first_mapping(mapping, "header")
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=_extract_sequence(mapping, "sources", "source_rows"),
            candidates=_extract_sequence(mapping, "candidates", "candidate_rows"),
            acknowledgements=acknowledgements
            if acknowledgements is not None
            else _extract_sequence(mapping, "acknowledgements", "acknowledgement_rows"),
            diagnostics=_extract_sequence(mapping, "diagnostics"),
            conflicts=_extract_sequence(mapping, "conflicts", "conflict_rows"),
            unsafe_claims=_extract_sequence(
                mapping, "unsafe_claims", "unsafe_claim_rows"
            ),
            evidence_history=_extract_sequence(
                mapping, "evidence_history", "evidence_history_rows"
            ),
            schema_version_display=str(
                schema_mapping.get(
                    "schema_version_display",
                    header_mapping.get("schema_version", "osw-exp-101-preview"),
                )
            ),
            schema_version_supported=bool(
                schema_mapping.get("schema_supported", True)
            ),
            schema_migration_required=bool(
                schema_mapping.get("migration_required", False)
            ),
            schema_migration_notes=str(schema_mapping.get("migration_notes", "")),
            explicit_write_request=explicit_write_request,
        )

    @classmethod
    def from_persistence_schema_model(
        cls,
        schema_model: object,
        *,
        acknowledgements: Mapping[str, bool] | Sequence[object] | None = None,
        explicit_write_request: bool = True,
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        return cls.from_schema_model(
            schema_model,
            acknowledgements=acknowledgements,
            explicit_write_request=explicit_write_request,
        )

    @classmethod
    def from_export_summary_viewmodel(
        cls,
        view_model: object,
        *,
        acknowledgements: Mapping[str, bool] | Sequence[object] | None = None,
        explicit_write_request: bool = True,
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        mapping = _object_to_supplied_mapping(view_model)
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=_extract_sequence(mapping, "sources", "source_rows"),
            candidates=_extract_sequence(mapping, "candidates", "candidate_rows"),
            acknowledgements=acknowledgements
            if acknowledgements is not None
            else _extract_sequence(mapping, "acknowledgements", "acknowledgement_rows"),
            diagnostics=_extract_sequence(mapping, "diagnostics"),
            redaction_rows=_extract_sequence(mapping, "redaction", "redaction_rows"),
            stale_source_rows=_extract_sequence(
                mapping, "stale_sources", "stale_source_rows"
            ),
            conflicts=_extract_sequence(mapping, "conflicts", "conflict_rows"),
            unsafe_claims=_extract_sequence(
                mapping, "unsafe_claims", "unsafe_claim_rows"
            ),
            evidence_history=_extract_sequence(
                mapping, "evidence_history", "evidence_history_rows"
            ),
            explicit_write_request=explicit_write_request,
        )

    @classmethod
    def blocked_by_schema(
        cls,
        *,
        reason: str = "missing",
        schema_version_display: str = "",
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=(OptionalSolverPluginManifestStateWriterSourceRow(source_id="s1"),),
            candidates=(
                OptionalSolverPluginManifestStateWriterCandidateRow(stack_id="stack"),
            ),
            acknowledgements={ack: True for ack in STATE_WRITER_REQUIRED_ACKS},
            schema_version_display=schema_version_display,
            schema_version_present=reason != "missing",
            schema_version_supported=reason != "unsupported",
            schema_migration_required=reason == "migration_required",
            schema_migration_notes=(
                "Schema migration is required before future state writing."
                if reason == "migration_required"
                else ""
            ),
        )

    @classmethod
    def blocked_by_redaction(
        cls,
        *,
        secret_like: bool = False,
        reviewed: bool = False,
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        reference = (
            "token=secret-value"
            if secret_like
            else "C:/private/optional-solver/plugin.json"
        )
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=(
                {
                    "source_id": "s1",
                    "source_reference_display": reference,
                },
            ),
            candidates=({"stack_id": "stack", "source_id": "s1"},),
            acknowledgements={ack: True for ack in STATE_WRITER_REQUIRED_ACKS},
            redaction_reviewed=reviewed,
        )

    @classmethod
    def blocked_by_stale_source(
        cls,
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=(
                {
                    "source_id": "s1",
                    "source_reference_display": "plugin.json",
                    "stale_source_state": "stale",
                    "repreview_required": True,
                },
            ),
            candidates=({"stack_id": "stack", "source_id": "s1"},),
            stale_source_rows=(
                OptionalSolverPluginManifestStateWriterStaleSourceRow(
                    stale_source_state="stale",
                    repreview_required=True,
                    source_reference_display="plugin.json",
                ),
            ),
            acknowledgements={ack: True for ack in STATE_WRITER_REQUIRED_ACKS},
        )

    @classmethod
    def blocked_by_conflict(
        cls,
        *,
        shared_stack_warning: bool = False,
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=({"source_id": "s1", "source_reference_display": "plugin.json"},),
            candidates=({"stack_id": "gmsh", "source_id": "s1"},),
            conflicts=(
                OptionalSolverPluginManifestStateWriterConflictRow(
                    stack_id="gmsh",
                    blocks_future_write=not shared_stack_warning,
                    shared_stack_warning_ack_required=shared_stack_warning,
                ),
            ),
            acknowledgements={ack: True for ack in STATE_WRITER_REQUIRED_ACKS},
        )

    @classmethod
    def blocked_by_unsafe_claim(
        cls,
        *,
        claim_text: str = "This manifest contains a prohibited qualification claim.",
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=({"source_id": "s1", "source_reference_display": "plugin.json"},),
            candidates=({"stack_id": "stack", "source_id": "s1"},),
            unsafe_claims=(
                OptionalSolverPluginManifestStateWriterUnsafeClaimRow(
                    claim_id="unsafe_claim",
                    related_candidate_id="stack",
                    claim_text=claim_text,
                ),
            ),
            acknowledgements={ack: True for ack in STATE_WRITER_REQUIRED_ACKS},
        )

    @classmethod
    def ready_for_future_write(
        cls,
    ) -> OptionalSolverPluginManifestStateWriterViewModel:
        return build_optional_solver_plugin_manifest_state_writer_viewmodel(
            sources=(
                {
                    "source_id": "s1",
                    "source_reference_display": "plugin.json",
                    "source_reference_redacted": True,
                },
            ),
            candidates=({"stack_id": "stack", "source_id": "s1"},),
            acknowledgements={ack: True for ack in STATE_WRITER_REQUIRED_ACKS},
        )

    def to_sections(self) -> tuple[OptionalSolverPluginManifestStateWriterSection, ...]:
        return self.sections

    def to_text_lines(self) -> tuple[str, ...]:
        return _text_lines(self)

    def to_mapping(self) -> dict[str, object]:
        return _view_model_to_mapping(self)


def build_optional_solver_plugin_manifest_state_writer_viewmodel(
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
    storage_options: Sequence[object] = (),
    file_format_boundaries: Sequence[object] = (),
    state_scope: str = "session_only",
    generated_by_display: str = "OSW optional solver plugin manifest UX",
    schema_version_display: str = "osw-exp-101-preview",
    schema_version_present: bool = True,
    schema_version_supported: bool = True,
    schema_migration_required: bool = False,
    schema_migration_notes: str = "",
    writer_version_display: str = "osw-exp-101-preview",
    explicit_write_request: bool = True,
    dry_run_requested: bool = False,
    future_write_requested: bool = True,
    redaction_reviewed: bool = True,
    future_writer_required: bool = False,
) -> OptionalSolverPluginManifestStateWriterViewModel:
    """Build a deterministic state-writer view-model from supplied state only."""

    candidate_inputs = tuple(candidates)
    supplied_sources = tuple(sources) or _sources_from_candidates(candidate_inputs)
    source_rows = tuple(_source_row(source) for source in supplied_sources)
    candidate_rows_initial = tuple(
        _candidate_row(candidate, source_rows=source_rows)
        for candidate in candidate_inputs
    )
    all_source_rows = source_rows or _sources_from_candidates(candidate_rows_initial)
    if not source_rows and all_source_rows:
        source_rows = tuple(_source_row(source) for source in all_source_rows)
        candidate_rows_initial = tuple(
            _candidate_row(candidate, source_rows=source_rows)
            for candidate in candidate_inputs
        )

    storage = tuple(_storage_option(row) for row in storage_options) or (
        _default_storage_options()
    )
    file_boundaries = tuple(
        _file_format_boundary(row) for row in file_format_boundaries
    ) or (
        OptionalSolverPluginManifestStateWriterFileFormatBoundary(
            schema_version_supported=schema_version_supported,
            schema_migration_required=schema_migration_required,
            diagnostics=_schema_diagnostic_codes(
                schema_version_display=schema_version_display,
                schema_version_present=schema_version_present,
                schema_version_supported=schema_version_supported,
                schema_migration_required=schema_migration_required,
            ),
        ),
    )
    schema_rows = (
        OptionalSolverPluginManifestStateWriterSchemaMigrationRow(
            schema_version_display=schema_version_display if schema_version_present else "",
            schema_supported=schema_version_supported,
            schema_unsupported_blocking=not schema_version_supported,
            migration_required=schema_migration_required,
            migration_notes=schema_migration_notes,
            diagnostics=_schema_diagnostic_codes(
                schema_version_display=schema_version_display,
                schema_version_present=schema_version_present,
                schema_version_supported=schema_version_supported,
                schema_migration_required=schema_migration_required,
            ),
        ),
    )
    redaction = _redaction_rows(
        redaction_rows,
        source_rows,
        redaction_reviewed=redaction_reviewed,
    )
    stale_rows = _stale_rows(stale_source_rows, source_rows, candidate_rows_initial)
    conflict_rows = tuple(_conflict_row(row) for row in conflicts)
    unsafe_rows = tuple(_unsafe_claim_row(row) for row in unsafe_claims)
    evidence_rows = _evidence_history_rows(evidence_history, candidate_rows_initial)
    ack_rows = _acknowledgement_rows(acknowledgements)
    has_state = bool(source_rows or candidate_rows_initial)

    readiness = _readiness(
        has_state=has_state,
        explicit_write_request=explicit_write_request,
        dry_run_requested=dry_run_requested,
        future_write_requested=future_write_requested,
        schema_rows=schema_rows,
        redaction_rows=redaction,
        stale_source_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_claim_rows=unsafe_rows,
        acknowledgement_rows=ack_rows,
        future_writer_required=future_writer_required,
    )
    diagnostics_rows = _diagnostic_rows(
        supplied=diagnostics,
        readiness=readiness,
        source_rows=source_rows,
        acknowledgement_rows=ack_rows,
        redaction_rows=redaction,
        schema_rows=schema_rows,
        stale_source_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_claim_rows=unsafe_rows,
        evidence_history_rows=evidence_rows,
    )
    blockers = tuple(row.code for row in diagnostics_rows if row.blocker)
    warnings = tuple(row.code for row in diagnostics_rows if row.severity == "warning")
    candidate_rows = tuple(
        _candidate_with_readiness(row, readiness, blockers, warnings)
        for row in candidate_rows_initial
    )
    write_plans = (
        OptionalSolverPluginManifestStateWriterWritePlan(
            plan_id="state_writer_plan",
            readiness=readiness,
            state_scope=state_scope,
            schema_version_display=schema_version_display if schema_version_present else "",
            target_reference_display="no default write path",
            target_reference_redacted=True,
            target_reference_approved=False,
            planned_storage_option_count=len(storage),
            planned_source_count=len(source_rows),
            planned_candidate_count=len(candidate_rows),
            planned_acknowledgement_count=len(ack_rows),
            planned_diagnostic_count=len(diagnostics_rows),
            planned_warning_count=len(warnings),
            planned_error_count=sum(1 for row in diagnostics_rows if row.severity == "error"),
            planned_blocker_count=len(blockers),
            blockers=blockers,
            warnings=warnings,
            diagnostics=tuple(row.code for row in diagnostics_rows),
        ),
    )
    summary = _summary(
        state_scope=state_scope,
        generated_by_display=generated_by_display,
        schema_version_display=schema_version_display if schema_version_present else "",
        writer_version_display=writer_version_display,
        readiness=readiness,
        storage_options=storage,
        source_rows=source_rows,
        candidate_rows=candidate_rows,
        acknowledgement_rows=ack_rows,
        diagnostics=diagnostics_rows,
        redaction_rows=redaction,
        schema_rows=schema_rows,
        stale_source_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_claim_rows=unsafe_rows,
        evidence_history_rows=evidence_rows,
    )
    actions = _action_states()
    return OptionalSolverPluginManifestStateWriterViewModel(
        summary=summary,
        sections=_sections(
            storage,
            write_plans,
            file_boundaries,
            source_rows,
            candidate_rows,
            ack_rows,
            diagnostics_rows,
            redaction,
            schema_rows,
            stale_rows,
            conflict_rows,
            unsafe_rows,
            evidence_rows,
        ),
        storage_options=storage,
        write_plans=write_plans,
        file_format_boundaries=file_boundaries,
        source_rows=source_rows,
        candidate_rows=candidate_rows,
        acknowledgement_rows=ack_rows,
        diagnostics=diagnostics_rows,
        redaction_rows=redaction,
        schema_migration_rows=schema_rows,
        stale_source_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_claim_rows=unsafe_rows,
        evidence_history_rows=evidence_rows,
        actions=actions,
        guidance_text=_guidance_text(readiness),
        safety_text=_safety_text(),
    )


def summarize_optional_solver_plugin_manifest_state_writer_viewmodel(
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
) -> str:
    summary = view_model.summary
    return (
        "Optional solver plugin manifest state-writer plan: "
        f"{summary.readiness.value}; "
        f"{summary.source_count} sources; "
        f"{summary.candidate_count} candidates; "
        f"{summary.blocker_count} blockers; non-writing."
    )


def explain_optional_solver_plugin_manifest_state_writer_viewmodel(
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
) -> tuple[str, ...]:
    return view_model.to_text_lines()


def render_optional_solver_plugin_manifest_state_writer_viewmodel(
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
) -> dict[str, object]:
    return view_model.to_mapping()


def redact_optional_solver_plugin_manifest_state_writer_source_reference(
    reference: object,
) -> tuple[str, bool]:
    display, redacted, _blocked, _secret = _redact_reference_details(reference)
    return display, redacted


def _default_storage_options() -> tuple[
    OptionalSolverPluginManifestStateWriterStorageOption, ...
]:
    return (
        OptionalSolverPluginManifestStateWriterStorageOption(
            storage_option_id="project_local",
            label="Project-local state file",
            description="Future portable project-local UX state.",
            privacy_risk="Local paths may leak into a project tree.",
            stale_state_risk="Project moves can leave stale source references.",
            project_schema_confusion_risk=(
                "Users may confuse local UX state with ProjectSchema."
            ),
            portability_risk="Portable only after a future redaction policy.",
            cleanup_risk="Project cleanup policy is future work.",
        ),
        OptionalSolverPluginManifestStateWriterStorageOption(
            storage_option_id="user_profile_cache",
            label="User-profile cache",
            description="Future per-user acknowledgement and review cache.",
            privacy_risk="Profile state can reveal private source names.",
            stale_state_risk="Cross-project state can become stale.",
            project_schema_confusion_risk="Not a ProjectSchema extension.",
            portability_risk="Not portable across machines.",
            cleanup_risk="Profile cleanup policy is future work.",
        ),
        OptionalSolverPluginManifestStateWriterStorageOption(
            storage_option_id="session_local_ephemeral",
            label="Session-local ephemeral state",
            description="Future temporary review state for one session.",
            privacy_risk="Still must redact source references.",
            stale_state_risk="Expires after the session.",
            project_schema_confusion_risk="Not durable project state.",
            portability_risk="Not portable.",
            cleanup_risk="Ephemeral cleanup policy is future work.",
        ),
        OptionalSolverPluginManifestStateWriterStorageOption(
            storage_option_id="explicit_user_chosen_file",
            label="Explicit user-chosen file",
            description="Future explicit reviewed target path.",
            privacy_risk="User-selected targets can expose private paths.",
            stale_state_risk="Targets can outlive their source previews.",
            project_schema_confusion_risk="Not a ProjectSchema file.",
            portability_risk="User must choose portable locations.",
            cleanup_risk="User-owned cleanup policy is future work.",
        ),
        OptionalSolverPluginManifestStateWriterStorageOption(
            storage_option_id="no_default_write_path",
            label="No default write path",
            description="Safest default before writer implementation.",
            default_selected=True,
            privacy_risk="Lowest risk in this gate.",
            stale_state_risk="No durable state is written.",
            project_schema_confusion_risk="No ProjectSchema confusion.",
            portability_risk="No file is created.",
            cleanup_risk="No cleanup is required.",
        ),
    )


def _storage_option(
    value: object,
) -> OptionalSolverPluginManifestStateWriterStorageOption:
    if isinstance(value, OptionalSolverPluginManifestStateWriterStorageOption):
        return value
    return OptionalSolverPluginManifestStateWriterStorageOption(
        storage_option_id=str(_get(value, "storage_option_id", "storage_option")),
        label=str(_get(value, "label", "Storage option")),
        description=str(_get(value, "description", "")),
        default_selected=bool(_get(value, "default_selected", False)),
        allowed_in_this_gate=bool(_get(value, "allowed_in_this_gate", False)),
        future_only=bool(_get(value, "future_only", True)),
        privacy_risk=str(_get(value, "privacy_risk", "")),
        stale_state_risk=str(_get(value, "stale_state_risk", "")),
        project_schema_confusion_risk=str(
            _get(value, "project_schema_confusion_risk", "")
        ),
        portability_risk=str(_get(value, "portability_risk", "")),
        cleanup_risk=str(_get(value, "cleanup_risk", "")),
        diagnostics=_tuple_of_text(_get(value, "diagnostics", ())),
    )


def _file_format_boundary(
    value: object,
) -> OptionalSolverPluginManifestStateWriterFileFormatBoundary:
    if isinstance(value, OptionalSolverPluginManifestStateWriterFileFormatBoundary):
        return value
    return OptionalSolverPluginManifestStateWriterFileFormatBoundary(
        format_kind=str(_get(value, "format_kind", "state_writer_payload")),
        conceptual_format=str(
            _get(value, "conceptual_format", "versioned_json_compatible_mapping")
        ),
        schema_version_required=bool(_get(value, "schema_version_required", True)),
        schema_version_supported=bool(_get(value, "schema_version_supported", True)),
        schema_migration_required=bool(
            _get(value, "schema_migration_required", False)
        ),
        schema_file_created=bool(_get(value, "schema_file_created", False)),
        actual_json_writer_implemented=bool(
            _get(value, "actual_json_writer_implemented", False)
        ),
        stable_keys_required=bool(_get(value, "stable_keys_required", True)),
        deterministic_ordering_required=bool(
            _get(value, "deterministic_ordering_required", True)
        ),
        redaction_metadata_required=bool(
            _get(value, "redaction_metadata_required", True)
        ),
        migration_notes_retained=bool(_get(value, "migration_notes_retained", True)),
        project_schema_state=str(_get(value, "project_schema_state", "not_project_schema")),
        diagnostics=_tuple_of_text(_get(value, "diagnostics", ())),
    )


def _source_row(value: object) -> OptionalSolverPluginManifestStateWriterSourceRow:
    if isinstance(value, OptionalSolverPluginManifestStateWriterSourceRow):
        return value
    reference = _get(
        value,
        "source_reference_display",
        _get(value, "source_reference", _get(value, "reference", "")),
    )
    display, redacted, blocked, secret_blocked = _redact_reference_details(
        reference,
        provided_label=str(_get(value, "source_label_display", "")),
    )
    source_type = str(_get(value, "source_type", "user_selected_json_file"))
    trust_label = str(
        _get(
            value,
            "trust_label",
            "built_in_manifest" if "built" in source_type else "untrusted_user_file",
        )
    )
    supplied_diagnostics = _tuple_of_text(_get(value, "diagnostics", ()))
    diagnostics = supplied_diagnostics
    if trust_label != "built_in_manifest":
        diagnostics = _append_unique(diagnostics, OSPMG_STATE_WRITER_UNTRUSTED_SOURCE)
    if blocked:
        diagnostics = _append_unique(
            diagnostics, OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED
        )
    if secret_blocked:
        diagnostics = _append_unique(
            diagnostics, OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED
        )
    stale_source_state = str(_get(value, "stale_source_state", "current"))
    repreview_required = bool(_get(value, "repreview_required", False)) or (
        stale_source_state not in {"", "current", "fresh", "not_stale"}
    )
    if repreview_required:
        diagnostics = _append_unique(
            diagnostics, OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED
        )
    return OptionalSolverPluginManifestStateWriterSourceRow(
        source_id=str(_get(value, "source_id", "source")),
        source_type=source_type,
        source_label=str(
            _get(value, "source_label", "Optional solver plugin manifest source")
        ),
        source_reference_display=display,
        source_reference_redacted=redacted
        or bool(_get(value, "source_reference_redacted", bool(display))),
        trust_label=trust_label,
        persisted_state_kind=str(
            _get(value, "persisted_state_kind", "state_writer_preview")
        ),
        source_fingerprint_display=str(_get(value, "source_fingerprint_display", "")),
        stale_source_state=stale_source_state,
        repreview_required=repreview_required,
        raw_reference_blocked=bool(_get(value, "raw_reference_blocked", blocked)),
        diagnostics=diagnostics,
    )


def _candidate_row(
    value: object,
    *,
    source_rows: Sequence[OptionalSolverPluginManifestStateWriterSourceRow],
) -> OptionalSolverPluginManifestStateWriterCandidateRow:
    if isinstance(value, OptionalSolverPluginManifestStateWriterCandidateRow):
        return value
    stack_id = str(_get(value, "stack_id", _get(value, "candidate_id", "stack")))
    source_id = str(_get(value, "source_id", ""))
    source = _source_for_candidate(source_id, source_rows)
    source_type = str(_get(value, "source_type", source.source_type if source else ""))
    trust_label = str(
        _get(
            value,
            "trust_label",
            source.trust_label if source else "untrusted_user_file",
        )
    )
    stale_source_state = str(
        _get(
            value,
            "stale_source_state",
            source.stale_source_state if source else "current",
        )
    )
    repreview_required = bool(
        _get(
            value,
            "repreview_required",
            source.repreview_required if source else False,
        )
    )
    diagnostics = _tuple_of_text(_get(value, "diagnostics", ()))
    if trust_label != "built_in_manifest":
        diagnostics = _append_unique(diagnostics, OSPMG_STATE_WRITER_UNTRUSTED_SOURCE)
    if repreview_required:
        diagnostics = _append_unique(
            diagnostics, OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED
        )
    return OptionalSolverPluginManifestStateWriterCandidateRow(
        stack_id=stack_id,
        display_name=str(_get(value, "display_name", stack_id)),
        source_id=source_id or (source.source_id if source else ""),
        source_type=source_type or "user_selected_json_file",
        trust_label=trust_label,
        activation_state=str(_get(value, "activation_state", "inactive_preview")),
        deactivation_state=str(_get(value, "deactivation_state", "not_deactivated")),
        reactivation_state=str(_get(value, "reactivation_state", "not_requested")),
        discovery_refresh_state=str(
            _get(value, "discovery_refresh_state", "not_refreshed")
        ),
        persistence_state=str(_get(value, "persistence_state", "session_only")),
        diagnostics=diagnostics,
        stale_source_state=stale_source_state,
        repreview_required=repreview_required,
        redaction_status=str(_get(value, "redaction_status", "redacted")),
        built_in_relationship=str(_get(value, "built_in_relationship", "not_built_in")),
        shared_stack_indicators=_tuple_of_text(
            _get(value, "shared_stack_indicators", ())
        ),
        deactivation_history_state=str(
            _get(value, "deactivation_history_state", "retained_if_supplied")
        ),
        reactivation_history_state=str(
            _get(value, "reactivation_history_state", "retained_if_supplied")
        ),
        historical_evidence_state=str(
            _get(value, "historical_evidence_state", "retained_as_reference")
        ),
        validation_evidence_state=str(
            _get(value, "validation_evidence_state", "not_validation_evidence")
        ),
    )


def _candidate_with_readiness(
    row: OptionalSolverPluginManifestStateWriterCandidateRow,
    readiness: OptionalSolverPluginManifestStateWriterReadiness,
    blockers: tuple[str, ...],
    warnings: tuple[str, ...],
) -> OptionalSolverPluginManifestStateWriterCandidateRow:
    diagnostics = row.diagnostics
    for code in blockers + warnings:
        diagnostics = _append_unique(diagnostics, code)
    return replace(
        row,
        readiness=readiness.value,
        writer_state=_writer_state(readiness),
        blockers=blockers,
        warnings=warnings,
        diagnostics=diagnostics,
    )


def _sources_from_candidates(candidates: Sequence[object]) -> tuple[object, ...]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for candidate in candidates:
        source_id = str(_get(candidate, "source_id", "source"))
        if source_id in seen:
            continue
        seen.add(source_id)
        rows.append(
            {
                "source_id": source_id,
                "source_type": _get(candidate, "source_type", "user_selected_json_file"),
                "source_reference_display": _get(
                    candidate,
                    "source_reference_display",
                    _get(candidate, "source_reference", ""),
                ),
                "trust_label": _get(candidate, "trust_label", "untrusted_user_file"),
                "stale_source_state": _get(candidate, "stale_source_state", "current"),
                "repreview_required": _get(candidate, "repreview_required", False),
            }
        )
    return tuple(rows)


def _source_for_candidate(
    source_id: str,
    source_rows: Sequence[OptionalSolverPluginManifestStateWriterSourceRow],
) -> OptionalSolverPluginManifestStateWriterSourceRow | None:
    if source_id:
        for source in source_rows:
            if source.source_id == source_id:
                return source
    return source_rows[0] if source_rows else None


def _acknowledgement_rows(
    acknowledgements: Mapping[str, bool] | Sequence[object] | None,
) -> tuple[OptionalSolverPluginManifestStateWriterAcknowledgementRow, ...]:
    supplied: dict[str, object] = {}
    if isinstance(acknowledgements, Mapping):
        supplied = {str(key): value for key, value in acknowledgements.items()}
    elif acknowledgements:
        supplied = {
            str(_get(row, "acknowledgement_id", "")): row
            for row in acknowledgements
            if str(_get(row, "acknowledgement_id", ""))
        }

    rows: list[OptionalSolverPluginManifestStateWriterAcknowledgementRow] = []
    for ack_id in STATE_WRITER_REQUIRED_ACKS:
        supplied_row = supplied.get(ack_id)
        if isinstance(supplied_row, bool):
            satisfied = supplied_row
            persisted = False
        else:
            satisfied = bool(_get(supplied_row, "satisfied", False))
            persisted = bool(_get(supplied_row, "persisted", False))
        rows.append(
            OptionalSolverPluginManifestStateWriterAcknowledgementRow(
                acknowledgement_id=ack_id,
                label=_ACK_LABELS[ack_id],
                satisfied=satisfied,
                persisted=persisted,
                blocking=not satisfied,
                reason="" if satisfied else "Required before future state writing.",
                warning_text=(
                    "Persisted acknowledgement may expire and must be reviewed."
                    if ack_id == ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE
                    else ""
                ),
            )
        )
    if not isinstance(acknowledgements, Mapping) and acknowledgements:
        for row in acknowledgements:
            ack_id = str(_get(row, "acknowledgement_id", ""))
            if not ack_id or ack_id in STATE_WRITER_REQUIRED_ACKS:
                continue
            rows.append(
                OptionalSolverPluginManifestStateWriterAcknowledgementRow(
                    acknowledgement_id=ack_id,
                    label=str(_get(row, "label", ack_id.replace("_", " "))),
                    required=bool(_get(row, "required", False)),
                    satisfied=bool(_get(row, "satisfied", False)),
                    persisted=bool(_get(row, "persisted", False)),
                    blocking=bool(_get(row, "blocking", False)),
                    reason=str(_get(row, "reason", "")),
                    related_candidate_id=str(_get(row, "related_candidate_id", "")),
                    related_source_id=str(_get(row, "related_source_id", "")),
                    warning_text=str(_get(row, "warning_text", "")),
                )
            )
    return tuple(rows)


def _redaction_rows(
    supplied: Sequence[object],
    source_rows: Sequence[OptionalSolverPluginManifestStateWriterSourceRow],
    *,
    redaction_reviewed: bool,
) -> tuple[OptionalSolverPluginManifestStateWriterRedactionRow, ...]:
    rows = [_redaction_row(row) for row in supplied]
    for source in source_rows:
        if not (
            source.raw_reference_blocked
            or source.repreview_required
            or OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED in source.diagnostics
        ):
            continue
        secret_blocked = (
            OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED in source.diagnostics
        )
        diagnostics: tuple[str, ...] = (OSPMG_STATE_WRITER_REDACTION_REQUIRED,)
        if source.raw_reference_blocked:
            diagnostics = _append_unique(
                diagnostics, OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED
            )
        if secret_blocked:
            diagnostics = _append_unique(
                diagnostics, OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED
            )
        rows.append(
            OptionalSolverPluginManifestStateWriterRedactionRow(
                raw_reference_supplied=True,
                display_reference=source.source_reference_display,
                redaction_status="reviewed" if redaction_reviewed else "review_required",
                redaction_required=True,
                unredacted_path_blocked=source.raw_reference_blocked,
                secret_like_content_blocked=secret_blocked,
                redaction_reviewed=redaction_reviewed,
                privacy_warning=_redaction_privacy_warning(
                    source.raw_reference_blocked, secret_blocked
                ),
                safe_to_share=(
                    redaction_reviewed
                    and not source.raw_reference_blocked
                    and not secret_blocked
                ),
                diagnostics=diagnostics,
            )
        )
    return tuple(rows)


def _redaction_row(
    value: object,
) -> OptionalSolverPluginManifestStateWriterRedactionRow:
    if isinstance(value, OptionalSolverPluginManifestStateWriterRedactionRow):
        return value
    return OptionalSolverPluginManifestStateWriterRedactionRow(
        raw_reference_supplied=bool(_get(value, "raw_reference_supplied", False)),
        display_reference=str(_get(value, "display_reference", "")),
        redaction_status=str(_get(value, "redaction_status", "review_required")),
        redaction_required=bool(_get(value, "redaction_required", True)),
        unredacted_path_blocked=bool(_get(value, "unredacted_path_blocked", False)),
        secret_like_content_blocked=bool(
            _get(value, "secret_like_content_blocked", False)
        ),
        redaction_reviewed=bool(_get(value, "redaction_reviewed", False)),
        privacy_warning=str(
            _get(value, "privacy_warning", "Redaction must be reviewed.")
        ),
        fingerprint_is_not_trust_signal=bool(
            _get(value, "fingerprint_is_not_trust_signal", True)
        ),
        safe_to_share=bool(_get(value, "safe_to_share", False)),
        diagnostics=_tuple_of_text(_get(value, "diagnostics", ())),
    )


def _schema_diagnostic_codes(
    *,
    schema_version_display: str,
    schema_version_present: bool,
    schema_version_supported: bool,
    schema_migration_required: bool,
) -> tuple[str, ...]:
    codes: tuple[str, ...] = ()
    if not schema_version_present or not schema_version_display:
        codes = _append_unique(codes, OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED)
    if not schema_version_supported:
        codes = _append_unique(codes, OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED)
    if schema_migration_required:
        codes = _append_unique(codes, OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED)
    return codes


def _stale_rows(
    supplied: Sequence[object],
    source_rows: Sequence[OptionalSolverPluginManifestStateWriterSourceRow],
    candidate_rows: Sequence[OptionalSolverPluginManifestStateWriterCandidateRow],
) -> tuple[OptionalSolverPluginManifestStateWriterStaleSourceRow, ...]:
    rows = [_stale_row(row) for row in supplied]
    seen = {row.source_reference_display for row in rows}
    for source in source_rows:
        if not source.repreview_required or source.source_reference_display in seen:
            continue
        rows.append(
            OptionalSolverPluginManifestStateWriterStaleSourceRow(
                stale_source_state=source.stale_source_state,
                repreview_required=True,
                source_reference_display=source.source_reference_display,
            )
        )
    for candidate in candidate_rows:
        if not candidate.repreview_required or candidate.stack_id in seen:
            continue
        rows.append(
            OptionalSolverPluginManifestStateWriterStaleSourceRow(
                stale_source_state=candidate.stale_source_state,
                repreview_required=True,
                source_reference_display=candidate.stack_id,
            )
        )
    return tuple(rows)


def _stale_row(value: object) -> OptionalSolverPluginManifestStateWriterStaleSourceRow:
    if isinstance(value, OptionalSolverPluginManifestStateWriterStaleSourceRow):
        return value
    return OptionalSolverPluginManifestStateWriterStaleSourceRow(
        stale_source_state=str(_get(value, "stale_source_state", "stale")),
        repreview_required=bool(_get(value, "repreview_required", True)),
        source_reference_display=str(_get(value, "source_reference_display", "")),
        old_preview_not_silently_trusted=bool(
            _get(value, "old_preview_not_silently_trusted", True)
        ),
        no_file_io_performed=bool(_get(value, "no_file_io_performed", True)),
        no_file_restoration_performed=bool(
            _get(value, "no_file_restoration_performed", True)
        ),
        no_file_rewrite_performed=bool(_get(value, "no_file_rewrite_performed", True)),
        no_file_deletion_performed=bool(
            _get(value, "no_file_deletion_performed", True)
        ),
        future_policy_required=bool(_get(value, "future_policy_required", True)),
        blocks_future_write=bool(_get(value, "blocks_future_write", True)),
    )


def _conflict_row(
    value: object,
) -> OptionalSolverPluginManifestStateWriterConflictRow:
    if isinstance(value, OptionalSolverPluginManifestStateWriterConflictRow):
        return value
    return OptionalSolverPluginManifestStateWriterConflictRow(
        stack_id=str(_get(value, "stack_id", "stack")),
        built_in_source_id=str(_get(value, "built_in_source_id", "")),
        user_source_id=str(_get(value, "user_source_id", "")),
        plugin_source_id=str(_get(value, "plugin_source_id", "")),
        built_in_source_state=str(_get(value, "built_in_source_state", "authoritative")),
        user_source_state=str(_get(value, "user_source_state", "untrusted")),
        plugin_source_state=str(_get(value, "plugin_source_state", "untrusted")),
        persistence_state=str(_get(value, "persistence_state", "session_only")),
        writer_state=str(_get(value, "writer_state", "conflict_review_required")),
        built_ins_win_by_default=bool(_get(value, "built_ins_win_by_default", True)),
        conflict_visible=bool(_get(value, "conflict_visible", True)),
        persisted_state_does_not_override_builtin=bool(
            _get(value, "persisted_state_does_not_override_builtin", True)
        ),
        shared_stack_warning_ack_required=bool(
            _get(value, "shared_stack_warning_ack_required", True)
        ),
        future_policy_required=bool(_get(value, "future_policy_required", True)),
        blocks_future_write=bool(_get(value, "blocks_future_write", True)),
    )


def _unsafe_claim_row(
    value: object,
) -> OptionalSolverPluginManifestStateWriterUnsafeClaimRow:
    if isinstance(value, OptionalSolverPluginManifestStateWriterUnsafeClaimRow):
        return value
    return OptionalSolverPluginManifestStateWriterUnsafeClaimRow(
        claim_id=str(_get(value, "claim_id", "unsafe_claim")),
        related_candidate_id=str(_get(value, "related_candidate_id", "")),
        related_source_id=str(_get(value, "related_source_id", "")),
        claim_text=str(_get(value, "claim_text", "")),
        blocked=bool(_get(value, "blocked", True)),
        warning_text=str(
            _get(
                value,
                "warning_text",
                "Unsafe claims are blocked by the state-writer plan.",
            )
        ),
        accepted_by_writer=bool(_get(value, "accepted_by_writer", False)),
        persisted_as_truth=bool(_get(value, "persisted_as_truth", False)),
    )


def _evidence_history_rows(
    supplied: Sequence[object],
    candidate_rows: Sequence[OptionalSolverPluginManifestStateWriterCandidateRow],
) -> tuple[OptionalSolverPluginManifestStateWriterEvidenceHistoryRow, ...]:
    if supplied:
        return tuple(_evidence_history_row(row) for row in supplied)
    if candidate_rows:
        return (OptionalSolverPluginManifestStateWriterEvidenceHistoryRow(),)
    return ()


def _evidence_history_row(
    value: object,
) -> OptionalSolverPluginManifestStateWriterEvidenceHistoryRow:
    if isinstance(value, OptionalSolverPluginManifestStateWriterEvidenceHistoryRow):
        return value
    return OptionalSolverPluginManifestStateWriterEvidenceHistoryRow(
        deactivation_history_retained=bool(
            _get(value, "deactivation_history_retained", True)
        ),
        reactivation_history_retained=bool(
            _get(value, "reactivation_history_retained", True)
        ),
        historical_validation_evidence_retained=bool(
            _get(value, "historical_validation_evidence_retained", True)
        ),
        skipped_missing_remains_skipped_missing=bool(
            _get(value, "skipped_missing_remains_skipped_missing", True)
        ),
        issue_closure_rewritten=bool(_get(value, "issue_closure_rewritten", False)),
        validation_evidence_rewritten=bool(
            _get(value, "validation_evidence_rewritten", False)
        ),
        historical_evidence_rewritten=bool(
            _get(value, "historical_evidence_rewritten", False)
        ),
        writer_state_is_not_validation_evidence=bool(
            _get(value, "writer_state_is_not_validation_evidence", True)
        ),
    )


def _readiness(
    *,
    has_state: bool,
    explicit_write_request: bool,
    dry_run_requested: bool,
    future_write_requested: bool,
    schema_rows: Sequence[OptionalSolverPluginManifestStateWriterSchemaMigrationRow],
    redaction_rows: Sequence[OptionalSolverPluginManifestStateWriterRedactionRow],
    stale_source_rows: Sequence[OptionalSolverPluginManifestStateWriterStaleSourceRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestStateWriterConflictRow],
    unsafe_claim_rows: Sequence[OptionalSolverPluginManifestStateWriterUnsafeClaimRow],
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestStateWriterAcknowledgementRow
    ],
    future_writer_required: bool,
) -> OptionalSolverPluginManifestStateWriterReadiness:
    Readiness = OptionalSolverPluginManifestStateWriterReadiness
    if not has_state:
        return Readiness.UNAVAILABLE_NO_STATE
    if not explicit_write_request:
        return Readiness.UNAVAILABLE_NO_EXPLICIT_REQUEST
    if any(not row.schema_version_display for row in schema_rows if row.schema_version_required):
        return Readiness.BLOCKED_SCHEMA_VERSION_MISSING
    if any(row.schema_unsupported_blocking for row in schema_rows):
        return Readiness.BLOCKED_SCHEMA_UNSUPPORTED
    if any(row.migration_required and not row.migration_executed for row in schema_rows):
        return Readiness.BLOCKED_SCHEMA_MIGRATION_REQUIRED
    if any(row.redaction_required and not row.redaction_reviewed for row in redaction_rows):
        return Readiness.BLOCKED_REDACTION_REVIEW
    if any(row.unredacted_path_blocked for row in redaction_rows):
        return Readiness.BLOCKED_UNREDACTED_PATH
    if any(row.secret_like_content_blocked for row in redaction_rows):
        return Readiness.BLOCKED_SECRET_LIKE_CONTENT
    if any(row.blocks_future_write and row.repreview_required for row in stale_source_rows):
        return Readiness.BLOCKED_STALE_SOURCE_REPREVIEW
    if any(row.blocks_future_write for row in conflict_rows):
        return Readiness.BLOCKED_CONFLICT
    if any(
        row.shared_stack_warning_ack_required and row.future_policy_required
        for row in conflict_rows
    ):
        return Readiness.BLOCKED_SHARED_STACK_WARNING
    if any(row.blocked for row in unsafe_claim_rows):
        return Readiness.BLOCKED_UNSAFE_CLAIM
    if any(row.required and not row.satisfied for row in acknowledgement_rows):
        return Readiness.BLOCKED_ACKNOWLEDGEMENT
    if future_writer_required:
        return Readiness.FUTURE_WRITER_REQUIRED
    if dry_run_requested and not future_write_requested:
        return Readiness.DRY_RUN_ONLY
    return Readiness.READY_FOR_FUTURE_WRITE


def _diagnostic_rows(
    *,
    supplied: Sequence[object],
    readiness: OptionalSolverPluginManifestStateWriterReadiness,
    source_rows: Sequence[OptionalSolverPluginManifestStateWriterSourceRow],
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestStateWriterAcknowledgementRow
    ],
    redaction_rows: Sequence[OptionalSolverPluginManifestStateWriterRedactionRow],
    schema_rows: Sequence[OptionalSolverPluginManifestStateWriterSchemaMigrationRow],
    stale_source_rows: Sequence[OptionalSolverPluginManifestStateWriterStaleSourceRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestStateWriterConflictRow],
    unsafe_claim_rows: Sequence[OptionalSolverPluginManifestStateWriterUnsafeClaimRow],
    evidence_history_rows: Sequence[
        OptionalSolverPluginManifestStateWriterEvidenceHistoryRow
    ],
) -> tuple[OptionalSolverPluginManifestStateWriterDiagnosticRow, ...]:
    rows = [_diagnostic_row(row) for row in supplied]
    codes = {row.code for row in rows}

    def add(
        code: str,
        message: str,
        *,
        severity: str = "warning",
        category: str = "state_writer",
        blocker: bool = False,
        suggested_fix: str = "Review the state-writer plan in a future gate.",
    ) -> None:
        if code in codes:
            return
        codes.add(code)
        rows.append(
            OptionalSolverPluginManifestStateWriterDiagnosticRow(
                severity=severity,
                category=category,
                code=code,
                message=message,
                suggested_fix=suggested_fix,
                blocker=blocker,
            )
        )

    blocker_code = _readiness_blocker_code(readiness)
    if blocker_code:
        add(
            blocker_code,
            _readiness_message(readiness),
            severity="error"
            if readiness == OptionalSolverPluginManifestStateWriterReadiness.ERROR
            else "warning",
            blocker=True,
        )
    if readiness == OptionalSolverPluginManifestStateWriterReadiness.DRY_RUN_ONLY:
        add(
            OSPMG_STATE_WRITER_DRY_RUN_ONLY,
            "Only in-memory dry-run planning is available in this gate.",
        )
    if any(row.required and not row.satisfied for row in acknowledgement_rows):
        add(
            OSPMG_STATE_WRITER_ACK_REQUIRED,
            "Required state-writer acknowledgements are missing.",
            blocker=readiness.value == "blocked_acknowledgement",
        )
    if any(row.trust_label != "built_in_manifest" for row in source_rows):
        add(
            OSPMG_STATE_WRITER_UNTRUSTED_SOURCE,
            "User/plugin manifest sources remain untrusted by default.",
        )
    if any(row.redaction_required for row in redaction_rows):
        add(
            OSPMG_STATE_WRITER_REDACTION_REQUIRED,
            "State-writer redaction review is required.",
            blocker=readiness.value == "blocked_redaction_review",
        )
    if any(row.unredacted_path_blocked for row in redaction_rows):
        add(
            OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED,
            "Unredacted local paths are blocked.",
            blocker=readiness.value == "blocked_unredacted_path",
        )
    if any(row.secret_like_content_blocked for row in redaction_rows):
        add(
            OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED,
            "Secret-like source content is blocked.",
            blocker=readiness.value == "blocked_secret_like_content",
        )
    if any(not row.schema_version_display for row in schema_rows):
        add(
            OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED,
            "A state schema version is required before future writing.",
            blocker=readiness.value == "blocked_schema_version_missing",
        )
    if any(row.schema_unsupported_blocking for row in schema_rows):
        add(
            OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED,
            "Unsupported state schema versions are blocked.",
            blocker=readiness.value == "blocked_schema_unsupported",
        )
    if any(row.migration_required for row in schema_rows):
        add(
            OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED,
            "Schema migration review is required before future writing.",
            blocker=readiness.value == "blocked_schema_migration_required",
        )
    if stale_source_rows:
        add(
            OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED,
            "Stale sources require re-preview before future writing.",
            blocker=readiness.value == "blocked_stale_source_repreview",
        )
    if any(row.blocks_future_write for row in conflict_rows):
        add(
            OSPMG_STATE_WRITER_CONFLICT_BLOCKED,
            "Conflicts block future state writing.",
            blocker=readiness.value == "blocked_conflict",
        )
    if any(row.shared_stack_warning_ack_required for row in conflict_rows):
        add(
            OSPMG_STATE_WRITER_SHARED_STACK_WARNING,
            "Shared-stack warnings require future policy review.",
            blocker=readiness.value == "blocked_shared_stack_warning",
        )
    if unsafe_claim_rows:
        add(
            OSPMG_STATE_WRITER_UNSAFE_CLAIM,
            "Unsafe claims are blocked and are not persisted as truth.",
            blocker=readiness.value == "blocked_unsafe_claim",
        )
    if evidence_history_rows:
        add(
            OSPMG_STATE_WRITER_EVIDENCE_RETAINED,
            "Evidence references are retained as references, not validation truth.",
        )
        add(
            OSPMG_STATE_WRITER_HISTORY_RETAINED,
            "Deactivation/reactivation history is retained when supplied.",
        )

    for code, message in (
        (OSPMG_STATE_WRITER_NOT_VALIDATION, STATE_WRITER_NOT_VALIDATION_TEXT),
        (
            OSPMG_STATE_WRITER_NOT_TRUST_RESTORE,
            STATE_WRITER_NOT_TRUST_RESTORE_TEXT,
        ),
        (
            OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION,
            STATE_WRITER_NOT_AUTOMATIC_ACTIVATION_TEXT,
        ),
        (
            OSPMG_STATE_WRITER_NO_INSTALL,
            "State writing does not install dependencies.",
        ),
        (
            OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION,
            "State writing does not execute solvers.",
        ),
        (
            OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE,
            "State writing does not close issues.",
        ),
        (
            OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION,
            "State writing does not mutate releases.",
        ),
        (
            OSPMG_STATE_WRITER_NOT_CERTIFICATION,
            "State writing is not certification.",
        ),
        (
            OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION,
            "State writing does not run discovery.",
        ),
        (
            OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT,
            "State writing does not import plugin packages.",
        ),
        (
            OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED,
            "ProjectSchema mutation is disabled.",
        ),
        (OSPMG_STATE_WRITER_RELOAD_DISABLED, "Reload behavior is disabled."),
        (OSPMG_STATE_WRITER_EXPORT_DISABLED, "Export behavior is disabled."),
        (
            OSPMG_STATE_WRITER_FUTURE_GATE,
            "Actual state writing requires a future gate.",
        ),
    ):
        add(code, message, severity="info", category="non_action")
    return tuple(rows)


def _diagnostic_row(
    value: object,
) -> OptionalSolverPluginManifestStateWriterDiagnosticRow:
    if isinstance(value, OptionalSolverPluginManifestStateWriterDiagnosticRow):
        return value
    return OptionalSolverPluginManifestStateWriterDiagnosticRow(
        severity=str(_get(value, "severity", "warning")),
        category=str(_get(value, "category", "state_writer")),
        code=str(_get(value, "code", "OSPMG_STATE_WRITER_DIAGNOSTIC")),
        message=str(_get(value, "message", "")),
        source_reference_display=str(_get(value, "source_reference_display", "")),
        stack_id=str(_get(value, "stack_id", "")),
        suggested_fix=str(_get(value, "suggested_fix", "")),
        blocker=bool(_get(value, "blocker", False)),
    )


def _readiness_blocker_code(
    readiness: OptionalSolverPluginManifestStateWriterReadiness,
) -> str:
    return {
        OptionalSolverPluginManifestStateWriterReadiness.UNAVAILABLE_NO_STATE: (
            OSPMG_STATE_WRITER_NOT_IMPLEMENTED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.UNAVAILABLE_NO_EXPLICIT_REQUEST: (
            OSPMG_STATE_WRITER_NOT_IMPLEMENTED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_ACKNOWLEDGEMENT: (
            OSPMG_STATE_WRITER_ACK_REQUIRED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_REDACTION_REVIEW: (
            OSPMG_STATE_WRITER_REDACTION_REQUIRED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_UNREDACTED_PATH: (
            OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SECRET_LIKE_CONTENT: (
            OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SCHEMA_VERSION_MISSING: (
            OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SCHEMA_UNSUPPORTED: (
            OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SCHEMA_MIGRATION_REQUIRED: (
            OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_STALE_SOURCE_REPREVIEW: (
            OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_CONFLICT: (
            OSPMG_STATE_WRITER_CONFLICT_BLOCKED
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SHARED_STACK_WARNING: (
            OSPMG_STATE_WRITER_SHARED_STACK_WARNING
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_UNSAFE_CLAIM: (
            OSPMG_STATE_WRITER_UNSAFE_CLAIM
        ),
        OptionalSolverPluginManifestStateWriterReadiness.FUTURE_WRITER_REQUIRED: (
            OSPMG_STATE_WRITER_FUTURE_GATE
        ),
        OptionalSolverPluginManifestStateWriterReadiness.ERROR: (
            "OSPMG_STATE_WRITER_ERROR"
        ),
    }.get(readiness, "")


def _readiness_message(
    readiness: OptionalSolverPluginManifestStateWriterReadiness,
) -> str:
    return {
        OptionalSolverPluginManifestStateWriterReadiness.UNAVAILABLE_NO_STATE: (
            "No supplied state is available for writer planning."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.UNAVAILABLE_NO_EXPLICIT_REQUEST: (
            "An explicit future write request is required."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_ACKNOWLEDGEMENT: (
            "Required acknowledgements are not satisfied."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_REDACTION_REVIEW: (
            "Redaction review is required."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_UNREDACTED_PATH: (
            "Unredacted path references are blocked."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SECRET_LIKE_CONTENT: (
            "Secret-like content is blocked."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SCHEMA_VERSION_MISSING: (
            "Schema version is missing."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SCHEMA_UNSUPPORTED: (
            "Schema version is unsupported."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SCHEMA_MIGRATION_REQUIRED: (
            "Schema migration is required."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_STALE_SOURCE_REPREVIEW: (
            "Stale sources require re-preview."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_CONFLICT: (
            "Conflicts block future writing."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_SHARED_STACK_WARNING: (
            "Shared-stack warning acknowledgement is required."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.BLOCKED_UNSAFE_CLAIM: (
            "Unsafe claims block future writing."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.FUTURE_WRITER_REQUIRED: (
            "A future writer implementation gate is required."
        ),
        OptionalSolverPluginManifestStateWriterReadiness.ERROR: (
            "State-writer planning encountered an error."
        ),
    }.get(readiness, readiness.value)


def _summary(
    *,
    state_scope: str,
    generated_by_display: str,
    schema_version_display: str,
    writer_version_display: str,
    readiness: OptionalSolverPluginManifestStateWriterReadiness,
    storage_options: Sequence[OptionalSolverPluginManifestStateWriterStorageOption],
    source_rows: Sequence[OptionalSolverPluginManifestStateWriterSourceRow],
    candidate_rows: Sequence[OptionalSolverPluginManifestStateWriterCandidateRow],
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestStateWriterAcknowledgementRow
    ],
    diagnostics: Sequence[OptionalSolverPluginManifestStateWriterDiagnosticRow],
    redaction_rows: Sequence[OptionalSolverPluginManifestStateWriterRedactionRow],
    schema_rows: Sequence[OptionalSolverPluginManifestStateWriterSchemaMigrationRow],
    stale_source_rows: Sequence[OptionalSolverPluginManifestStateWriterStaleSourceRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestStateWriterConflictRow],
    unsafe_claim_rows: Sequence[OptionalSolverPluginManifestStateWriterUnsafeClaimRow],
    evidence_history_rows: Sequence[
        OptionalSolverPluginManifestStateWriterEvidenceHistoryRow
    ],
) -> OptionalSolverPluginManifestStateWriterSummary:
    return OptionalSolverPluginManifestStateWriterSummary(
        writer_kind="optional_solver_plugin_manifest_state_writer_plan",
        state_scope=state_scope,
        generated_by_display=generated_by_display,
        schema_version_display=schema_version_display,
        writer_version_display=writer_version_display,
        readiness=readiness,
        writer_state=_writer_state(readiness),
        storage_option_count=len(storage_options),
        source_count=len(source_rows),
        candidate_count=len(candidate_rows),
        acknowledgement_count=len(acknowledgement_rows),
        required_acknowledgement_count=sum(1 for row in acknowledgement_rows if row.required),
        satisfied_acknowledgement_count=sum(
            1 for row in acknowledgement_rows if row.required and row.satisfied
        ),
        diagnostic_count=len(diagnostics),
        warning_count=sum(1 for row in diagnostics if row.severity == "warning"),
        error_count=sum(1 for row in diagnostics if row.severity == "error"),
        blocker_count=sum(1 for row in diagnostics if row.blocker),
        conflict_count=len(conflict_rows),
        unsafe_claim_count=len(unsafe_claim_rows),
        stale_source_count=len(stale_source_rows),
        redaction_required_count=sum(1 for row in redaction_rows if row.redaction_required),
        schema_issue_count=sum(1 for row in schema_rows if row.diagnostics),
        migration_required_count=sum(1 for row in schema_rows if row.migration_required),
        evidence_history_count=len(evidence_history_rows),
        evidence_retained_count=sum(
            1
            for row in evidence_history_rows
            if row.historical_validation_evidence_retained
        ),
        history_retained_count=sum(
            1
            for row in evidence_history_rows
            if row.deactivation_history_retained or row.reactivation_history_retained
        ),
    )


def _writer_state(readiness: OptionalSolverPluginManifestStateWriterReadiness) -> str:
    if readiness.value.startswith("blocked_"):
        return "future_write_blocked"
    if readiness.value.startswith("unavailable_"):
        return "writer_unavailable"
    if readiness == OptionalSolverPluginManifestStateWriterReadiness.DRY_RUN_ONLY:
        return "dry_run_plan_only"
    if readiness == OptionalSolverPluginManifestStateWriterReadiness.READY_FOR_FUTURE_WRITE:
        return "ready_for_future_write_no_writer"
    if readiness == OptionalSolverPluginManifestStateWriterReadiness.FUTURE_WRITER_REQUIRED:
        return "future_writer_required"
    return "error"


def _sections(
    storage_options: Sequence[OptionalSolverPluginManifestStateWriterStorageOption],
    write_plans: Sequence[OptionalSolverPluginManifestStateWriterWritePlan],
    file_boundaries: Sequence[OptionalSolverPluginManifestStateWriterFileFormatBoundary],
    source_rows: Sequence[OptionalSolverPluginManifestStateWriterSourceRow],
    candidate_rows: Sequence[OptionalSolverPluginManifestStateWriterCandidateRow],
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestStateWriterAcknowledgementRow
    ],
    diagnostics: Sequence[OptionalSolverPluginManifestStateWriterDiagnosticRow],
    redaction_rows: Sequence[OptionalSolverPluginManifestStateWriterRedactionRow],
    schema_rows: Sequence[OptionalSolverPluginManifestStateWriterSchemaMigrationRow],
    stale_source_rows: Sequence[OptionalSolverPluginManifestStateWriterStaleSourceRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestStateWriterConflictRow],
    unsafe_claim_rows: Sequence[OptionalSolverPluginManifestStateWriterUnsafeClaimRow],
    evidence_history_rows: Sequence[
        OptionalSolverPluginManifestStateWriterEvidenceHistoryRow
    ],
) -> tuple[OptionalSolverPluginManifestStateWriterSection, ...]:
    return (
        _section("storage_options", "Storage options", len(storage_options)),
        _section("write_plan", "Write plan", len(write_plans)),
        _section("file_format", "File format and schema", len(file_boundaries)),
        _section("sources", "Sources and provenance", len(source_rows)),
        _section("candidates", "Candidate writer state", len(candidate_rows)),
        _section("acknowledgements", "Acknowledgements", len(acknowledgement_rows)),
        _section("diagnostics", "Diagnostics", len(diagnostics), diagnostics),
        _section("redaction", "Redaction and privacy", len(redaction_rows)),
        _section("schema_migration", "Schema and migration", len(schema_rows)),
        _section("stale_sources", "Stale sources", len(stale_source_rows)),
        _section("conflicts", "Conflicts and shared stacks", len(conflict_rows)),
        _section("unsafe_claims", "Unsafe claims", len(unsafe_claim_rows)),
        _section("evidence_history", "Evidence and history", len(evidence_history_rows)),
    )


def _section(
    section_id: str,
    title: str,
    row_count: int,
    diagnostics: Sequence[OptionalSolverPluginManifestStateWriterDiagnosticRow] = (),
) -> OptionalSolverPluginManifestStateWriterSection:
    return OptionalSolverPluginManifestStateWriterSection(
        section_id=section_id,
        title=title,
        row_count=row_count,
        diagnostic_count=len(diagnostics),
        blocker_count=sum(1 for row in diagnostics if row.blocker),
    )


def _action_states() -> tuple[OptionalSolverPluginManifestStateWriterActionState, ...]:
    return tuple(
        OptionalSolverPluginManifestStateWriterActionState(
            action=action,
            label=action.value.replace("_", " "),
            enabled=action.value in _SAFE_REVIEW_ACTIONS,
            available=action.value in _SAFE_REVIEW_ACTIONS,
            reason=_action_reason(action),
            future_action=action.value not in _SAFE_REVIEW_ACTIONS,
        )
        for action in OptionalSolverPluginManifestStateWriterAction
    )


def _action_reason(action: OptionalSolverPluginManifestStateWriterAction) -> str:
    if action.value in _SAFE_REVIEW_ACTIONS:
        return "In-memory review action only."
    return {
        OptionalSolverPluginManifestStateWriterAction.WRITE_STATE_FILE: (
            "Actual state writing requires a future writer gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.CREATE_RUNTIME_STATE_FILE: (
            "Runtime state file creation requires a future writer gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.CREATE_SETTINGS_FILE: (
            "Settings files require a future settings gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.CREATE_SCHEMA_FILE: (
            "Schema file creation is out of scope for this gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.CREATE_EXPORT_FILE: (
            "Export files require a future export gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.CREATE_REPORT_FILE: (
            "Report files require a future report gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.CREATE_RELOADABLE_BUNDLE: (
            "Reloadable bundles require a future bundle gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.MUTATE_PROJECT_SCHEMA: (
            "ProjectSchema mutation is disabled."
        ),
        OptionalSolverPluginManifestStateWriterAction.RELOAD_STATE: (
            "Reload behavior requires a future reload gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.EXPORT_STATE: (
            "Export behavior requires a future export gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.COPY_TO_CLIPBOARD: (
            "Clipboard behavior requires a future integration gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.ATTACH_REPORT: (
            "Report attachment requires a future report integration gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.OPEN_OUTPUT_FOLDER: (
            "Opening output folders requires a future GUI/OS integration gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.IMPORT_PLUGIN_PACKAGE: (
            "Plugin package import is unavailable."
        ),
        OptionalSolverPluginManifestStateWriterAction.SCAN_DIRECTORY: (
            "Directory scanning is unavailable."
        ),
        OptionalSolverPluginManifestStateWriterAction.FETCH_NETWORK_MANIFEST: (
            "Network manifest fetching is unavailable."
        ),
        OptionalSolverPluginManifestStateWriterAction.RUN_DISCOVERY: (
            "Discovery execution is unavailable."
        ),
        OptionalSolverPluginManifestStateWriterAction.RUN_VALIDATION: (
            "Validation requires a separate validation gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.INSTALL_DEPENDENCY: (
            "Dependency installation is unavailable."
        ),
        OptionalSolverPluginManifestStateWriterAction.UNINSTALL_DEPENDENCY: (
            "Dependency uninstall is unavailable."
        ),
        OptionalSolverPluginManifestStateWriterAction.UNINSTALL_SOLVER: (
            "Solver uninstall is unavailable."
        ),
        OptionalSolverPluginManifestStateWriterAction.EXECUTE_SOLVER: (
            "Solver execution is unavailable."
        ),
        OptionalSolverPluginManifestStateWriterAction.CLOSE_ISSUE: (
            "Issue closure requires a separate issue gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.MUTATE_RELEASE: (
            "Release mutation requires a separate release gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.PUSH_TAG: (
            "Tag mutation requires a separate release/tag gate."
        ),
        OptionalSolverPluginManifestStateWriterAction.UPLOAD_ASSET: (
            "Asset upload requires a separate release asset gate."
        ),
    }[action]


def _text_lines(
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
) -> tuple[str, ...]:
    summary = view_model.summary
    lines = [
        "Optional Solver Plugin Manifest State Writer Plan",
        f"readiness: {summary.readiness.value}",
        f"writer state: {summary.writer_state}",
        f"sources: {summary.source_count}",
        f"candidates: {summary.candidate_count}",
        f"diagnostics: {summary.diagnostic_count}",
        "non-actions: no writer implementation, no file write, no directory "
        "creation, no runtime state file, no settings file, no schema file, "
        "no export, no report, no reloadable bundle, no ProjectSchema mutation, "
        "no GUI or CLI behavior, no reload, no discovery, no validation, no "
        "solver execution, no issue or release mutation",
    ]
    for plan in view_model.write_plans:
        lines.append(
            "write-plan: "
            f"{plan.plan_id} readiness={plan.readiness.value} "
            f"would_write={plan.would_write}"
        )
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
    view_model: OptionalSolverPluginManifestStateWriterViewModel,
) -> dict[str, object]:
    return {
        "summary": _record_to_mapping(view_model.summary),
        "sections": [_record_to_mapping(row) for row in view_model.sections],
        "storage_options": [
            _record_to_mapping(row) for row in view_model.storage_options
        ],
        "write_plans": [_record_to_mapping(row) for row in view_model.write_plans],
        "file_format_boundaries": [
            _record_to_mapping(row) for row in view_model.file_format_boundaries
        ],
        "sources": [_record_to_mapping(row) for row in view_model.source_rows],
        "candidates": [_record_to_mapping(row) for row in view_model.candidate_rows],
        "acknowledgements": [
            _record_to_mapping(row) for row in view_model.acknowledgement_rows
        ],
        "diagnostics": [_record_to_mapping(row) for row in view_model.diagnostics],
        "redaction": [_record_to_mapping(row) for row in view_model.redaction_rows],
        "schema_migration": [
            _record_to_mapping(row) for row in view_model.schema_migration_rows
        ],
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
        "atomicity_plan": [
            _record_to_mapping(row) for row in view_model.atomicity_plan_rows
        ],
        "non_action_flags": _record_to_mapping(view_model.non_action_flags),
        "actions": [_record_to_mapping(row) for row in view_model.actions],
        "guidance_text": list(view_model.guidance_text),
        "safety_text": list(view_model.safety_text),
        "reserved_diagnostic_codes": list(view_model.reserved_diagnostic_codes),
        "not_validation_evidence": True,
    }


def _record_to_mapping(record: object) -> dict[str, object]:
    result: dict[str, object] = {}
    for slot in getattr(record, "__slots__", ()):
        result[slot] = _value_to_mapping(getattr(record, slot))
    return result


def _value_to_mapping(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__slots__"):
        return _record_to_mapping(value)
    if isinstance(value, tuple):
        return [_value_to_mapping(item) for item in value]
    return value


def _object_to_supplied_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            return mapped
    return {
        "sources": tuple(
            _get(value, "source_rows", _get(value, "sources", ()))
        ),
        "candidates": tuple(
            _get(value, "candidate_rows", _get(value, "candidates", ()))
        ),
        "acknowledgements": tuple(
            _get(value, "acknowledgement_rows", _get(value, "acknowledgements", ()))
        ),
        "diagnostics": tuple(_get(value, "diagnostics", ())),
        "redaction": tuple(_get(value, "redaction_rows", ())),
        "stale_sources": tuple(_get(value, "stale_source_rows", ())),
        "conflicts": tuple(_get(value, "conflict_rows", _get(value, "conflicts", ()))),
        "unsafe_claims": tuple(
            _get(value, "unsafe_claim_rows", _get(value, "unsafe_claims", ()))
        ),
        "evidence_history": tuple(_get(value, "evidence_history_rows", ())),
    }


def _extract_sequence(mapping: Mapping[str, object], *names: str) -> tuple[object, ...]:
    for name in names:
        if name not in mapping:
            continue
        value = mapping[name]
        if isinstance(value, Sequence) and not isinstance(value, str):
            return tuple(value)
        if value:
            return (value,)
    return ()


def _extract_first_mapping(mapping: Mapping[str, object], name: str) -> Mapping[str, object]:
    value = mapping.get(name, {})
    if isinstance(value, Mapping):
        return value
    if isinstance(value, Sequence) and not isinstance(value, str) and value:
        first = value[0]
        if isinstance(first, Mapping):
            return first
        if hasattr(first, "__slots__"):
            return _record_to_mapping(first)
    return {}


def _redact_reference_details(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool, bool, bool]:
    label = str(provided_label or "").strip()
    if label:
        if _secret_like(label):
            return "<redacted-secret-like-reference>", True, False, True
        display = _basename_if_path(label)
        return display, display != label, display != label, False
    text = str(reference or "").strip()
    if not text:
        return "", False, False, False
    if _secret_like(text):
        return "<redacted-secret-like-reference>", True, False, True
    display = _basename_if_path(text)
    redacted = display != text
    return display, redacted, redacted, False


def _basename_if_path(text: str) -> str:
    normalized = text.replace("\\", "/")
    if "/" in normalized:
        return normalized.rsplit("/", 1)[-1] or "redacted-source"
    return text


def _secret_like(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in (
            "token=",
            "secret=",
            "password=",
            "apikey",
            "api_key",
            "bearer ",
            "github_pat",
            "ghp_",
        )
    )


def _redaction_privacy_warning(path_blocked: bool, secret_blocked: bool) -> str:
    if secret_blocked:
        return "Secret-like content is blocked and must not be persisted."
    if path_blocked:
        return "Local paths are redacted and raw references are blocked."
    return "Redaction metadata must be reviewed before future writing."


def _guidance_text(
    readiness: OptionalSolverPluginManifestStateWriterReadiness,
) -> tuple[str, ...]:
    return (
        f"Writer readiness: {readiness.value}.",
        "Review redaction, schema, acknowledgements, stale sources, conflicts, "
        "unsafe claims, and evidence/history before any future writer gate.",
        "This view-model writes nothing and creates no runtime state.",
    )


def _safety_text() -> tuple[str, ...]:
    return (
        STATE_WRITER_NOT_VALIDATION_TEXT,
        STATE_WRITER_NOT_TRUST_RESTORE_TEXT,
        STATE_WRITER_NOT_AUTOMATIC_ACTIVATION_TEXT,
        TRUST_NOT_CERTIFICATION_TEXT,
        STATE_SCHEMA_NOT_PROJECT_SCHEMA_TEXT,
        "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
        "bounded, issue-specific evidence.",
    )


def _tuple_of_text(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _append_unique(values: tuple[str, ...], value: str) -> tuple[str, ...]:
    if value in values:
        return values
    return values + (value,)


def _get(value: object, name: str, default: object = "") -> object:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


__all__ = [
    "ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD",
    "ACK_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE",
    "ACK_LOCAL_PATH_REDACTION_REVIEWED",
    "ACK_NO_DISCOVERY_EXECUTION",
    "ACK_NO_PLUGIN_PACKAGE_IMPORT",
    "ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE",
    "ACK_STALE_SOURCE_REQUIRES_REPREVIEW",
    "ACK_STATE_WRITE_NO_SOLVER_EXECUTION",
    "ACK_STATE_WRITE_NOT_AUTOMATIC_ACTIVATION",
    "ACK_STATE_WRITE_NOT_CERTIFICATION",
    "ACK_STATE_WRITE_NOT_DEPENDENCY_INSTALL",
    "ACK_STATE_WRITE_NOT_ISSUE_CLOSURE",
    "ACK_STATE_WRITE_NOT_RELEASE_MUTATION",
    "ACK_STATE_WRITE_NOT_TRUST_RESTORATION",
    "ACK_STATE_WRITE_NOT_VALIDATION",
    "ACK_TRUST_LABEL_NOT_CERTIFICATION",
    "ACK_UNREDACTED_PATHS_BLOCKED",
    "ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED",
    "OSPMG_STATE_WRITER_ACK_REQUIRED",
    "OSPMG_STATE_WRITER_CONFLICT_BLOCKED",
    "OSPMG_STATE_WRITER_DIAGNOSTIC_CODES",
    "OSPMG_STATE_WRITER_DRY_RUN_ONLY",
    "OSPMG_STATE_WRITER_EVIDENCE_RETAINED",
    "OSPMG_STATE_WRITER_EXPORT_DISABLED",
    "OSPMG_STATE_WRITER_FUTURE_GATE",
    "OSPMG_STATE_WRITER_HISTORY_RETAINED",
    "OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION",
    "OSPMG_STATE_WRITER_NOT_CERTIFICATION",
    "OSPMG_STATE_WRITER_NOT_IMPLEMENTED",
    "OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE",
    "OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION",
    "OSPMG_STATE_WRITER_NOT_TRUST_RESTORE",
    "OSPMG_STATE_WRITER_NOT_VALIDATION",
    "OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION",
    "OSPMG_STATE_WRITER_NO_INSTALL",
    "OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT",
    "OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION",
    "OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED",
    "OSPMG_STATE_WRITER_REDACTION_REQUIRED",
    "OSPMG_STATE_WRITER_RELOAD_DISABLED",
    "OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED",
    "OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED",
    "OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED",
    "OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED",
    "OSPMG_STATE_WRITER_SHARED_STACK_WARNING",
    "OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED",
    "OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED",
    "OSPMG_STATE_WRITER_UNSAFE_CLAIM",
    "OSPMG_STATE_WRITER_UNTRUSTED_SOURCE",
    "OptionalSolverPluginManifestStateWriterAcknowledgementRow",
    "OptionalSolverPluginManifestStateWriterAction",
    "OptionalSolverPluginManifestStateWriterActionState",
    "OptionalSolverPluginManifestStateWriterAtomicityPlanRow",
    "OptionalSolverPluginManifestStateWriterCandidateRow",
    "OptionalSolverPluginManifestStateWriterConflictRow",
    "OptionalSolverPluginManifestStateWriterDiagnosticRow",
    "OptionalSolverPluginManifestStateWriterEvidenceHistoryRow",
    "OptionalSolverPluginManifestStateWriterFileFormatBoundary",
    "OptionalSolverPluginManifestStateWriterNonActionFlags",
    "OptionalSolverPluginManifestStateWriterReadiness",
    "OptionalSolverPluginManifestStateWriterRedactionRow",
    "OptionalSolverPluginManifestStateWriterSchemaMigrationRow",
    "OptionalSolverPluginManifestStateWriterSection",
    "OptionalSolverPluginManifestStateWriterSourceRow",
    "OptionalSolverPluginManifestStateWriterStaleSourceRow",
    "OptionalSolverPluginManifestStateWriterStorageOption",
    "OptionalSolverPluginManifestStateWriterSummary",
    "OptionalSolverPluginManifestStateWriterUnsafeClaimRow",
    "OptionalSolverPluginManifestStateWriterViewModel",
    "OptionalSolverPluginManifestStateWriterWritePlan",
    "STATE_WRITER_REQUIRED_ACKS",
    "build_optional_solver_plugin_manifest_state_writer_viewmodel",
    "explain_optional_solver_plugin_manifest_state_writer_viewmodel",
    "redact_optional_solver_plugin_manifest_state_writer_source_reference",
    "render_optional_solver_plugin_manifest_state_writer_viewmodel",
    "summarize_optional_solver_plugin_manifest_state_writer_viewmodel",
]
