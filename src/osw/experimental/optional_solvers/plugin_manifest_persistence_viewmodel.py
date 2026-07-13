"""Pure view-model for optional solver plugin manifest persistence readiness.

This module is the OSW-EXP-092 implementation of the persistence view-model
designed in OSW-EXP-090. It transforms already-supplied optional solver plugin
manifest UX state into deterministic persistence-readiness, acknowledgement,
diagnostic, redaction/privacy, schema/migration, stale-source/re-preview,
conflict, unsafe-claim, evidence/history, trust/provenance, and action-state
records.

It performs no side effects. It does not persist anything, read or write files,
create settings files, create schema files, parse JSON from paths, inspect path
existence, import PySide/Qt, import plugin packages, scan directories, fetch
URLs, run discovery, run validation, execute solvers, install or uninstall
dependencies, uninstall solvers, mutate ProjectSchema, mutate issues/releases,
or claim validation success/failure or certification. All lifecycle,
acknowledgement, schema, stale-source, conflict, unsafe-claim, and evidence
inputs are supplied by the caller; this layer only classifies and renders them.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

# Design vocabulary reserved by OSW-EXP-090 and implemented as data records here.
OSPMG_PERSISTENCE_NOT_IMPLEMENTED = "OSPMG_PERSISTENCE_NOT_IMPLEMENTED"
OSPMG_PERSISTENCE_ACK_REQUIRED = "OSPMG_PERSISTENCE_ACK_REQUIRED"
OSPMG_PERSISTENCE_NOT_VALIDATION = "OSPMG_PERSISTENCE_NOT_VALIDATION"
OSPMG_PERSISTENCE_NOT_TRUST_RESTORE = "OSPMG_PERSISTENCE_NOT_TRUST_RESTORE"
OSPMG_PERSISTENCE_NO_INSTALL = "OSPMG_PERSISTENCE_NO_INSTALL"
OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION = "OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION"
OSPMG_PERSISTENCE_NOT_ISSUE_CLOSURE = "OSPMG_PERSISTENCE_NOT_ISSUE_CLOSURE"
OSPMG_PERSISTENCE_NOT_RELEASE_MUTATION = "OSPMG_PERSISTENCE_NOT_RELEASE_MUTATION"
OSPMG_PERSISTENCE_REDACTION_REQUIRED = "OSPMG_PERSISTENCE_REDACTION_REQUIRED"
OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED = (
    "OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED"
)
OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED = (
    "OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED"
)
OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED = (
    "OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED"
)
OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED = (
    "OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED"
)
OSPMG_PERSISTENCE_UNTRUSTED_SOURCE = "OSPMG_PERSISTENCE_UNTRUSTED_SOURCE"
OSPMG_PERSISTENCE_CONFLICT_BLOCKED = "OSPMG_PERSISTENCE_CONFLICT_BLOCKED"
OSPMG_PERSISTENCE_UNSAFE_CLAIM = "OSPMG_PERSISTENCE_UNSAFE_CLAIM"
OSPMG_PERSISTENCE_EVIDENCE_RETAINED = "OSPMG_PERSISTENCE_EVIDENCE_RETAINED"
OSPMG_PERSISTENCE_HISTORY_RETAINED = "OSPMG_PERSISTENCE_HISTORY_RETAINED"
OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION = (
    "OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION"
)
OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT = "OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT"
OSPMG_PERSISTENCE_FUTURE_GATE = "OSPMG_PERSISTENCE_FUTURE_GATE"

OSPMG_PERSISTENCE_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_PERSISTENCE_NOT_IMPLEMENTED,
    OSPMG_PERSISTENCE_ACK_REQUIRED,
    OSPMG_PERSISTENCE_NOT_VALIDATION,
    OSPMG_PERSISTENCE_NOT_TRUST_RESTORE,
    OSPMG_PERSISTENCE_NO_INSTALL,
    OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION,
    OSPMG_PERSISTENCE_NOT_ISSUE_CLOSURE,
    OSPMG_PERSISTENCE_NOT_RELEASE_MUTATION,
    OSPMG_PERSISTENCE_REDACTION_REQUIRED,
    OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED,
    OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED,
    OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED,
    OSPMG_PERSISTENCE_UNTRUSTED_SOURCE,
    OSPMG_PERSISTENCE_CONFLICT_BLOCKED,
    OSPMG_PERSISTENCE_UNSAFE_CLAIM,
    OSPMG_PERSISTENCE_EVIDENCE_RETAINED,
    OSPMG_PERSISTENCE_HISTORY_RETAINED,
    OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION,
    OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT,
    OSPMG_PERSISTENCE_FUTURE_GATE,
)

ACK_PERSISTENCE_NOT_VALIDATION = "persistence_not_validation"
ACK_PERSISTENCE_NOT_TRUST_RESTORATION = "persistence_not_trust_restoration"
ACK_PERSISTENCE_NOT_INSTALL = "persistence_not_install"
ACK_PERSISTENCE_NO_SOLVER_EXECUTION = "persistence_no_solver_execution"
ACK_PERSISTENCE_NOT_ISSUE_CLOSURE = "persistence_not_issue_closure"
ACK_PERSISTENCE_NOT_RELEASE_MUTATION = "persistence_not_release_mutation"
ACK_LOCAL_PATH_REDACTION_REVIEWED = "local_path_redaction_reviewed"
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

PERSISTENCE_REQUIRED_ACKS: tuple[str, ...] = (
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
)

_ACK_LABELS: dict[str, str] = {
    ACK_PERSISTENCE_NOT_VALIDATION: "I understand persistence is not validation.",
    ACK_PERSISTENCE_NOT_TRUST_RESTORATION: (
        "I understand persistence does not restore trust."
    ),
    ACK_PERSISTENCE_NOT_INSTALL: "I understand persistence does not install dependencies.",
    ACK_PERSISTENCE_NO_SOLVER_EXECUTION: (
        "I understand persistence does not execute solvers."
    ),
    ACK_PERSISTENCE_NOT_ISSUE_CLOSURE: (
        "I understand persistence does not close issues."
    ),
    ACK_PERSISTENCE_NOT_RELEASE_MUTATION: (
        "I understand persistence does not mutate releases."
    ),
    ACK_LOCAL_PATH_REDACTION_REVIEWED: (
        "I reviewed local path redaction before persistence."
    ),
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
        "I understand activation review is required after reload."
    ),
    ACK_NO_DISCOVERY_EXECUTION: "I understand persistence does not run discovery.",
    ACK_NO_PLUGIN_PACKAGE_IMPORT: (
        "I understand persistence does not import plugin packages."
    ),
    ACK_TRUST_LABEL_NOT_CERTIFICATION: (
        "I understand a trust label is not certification."
    ),
}

TRUST_NOT_CERTIFICATION_TEXT = "A trust label is not certification."
PERSISTENCE_NOT_VALIDATION_TEXT = "Persisted state is not validation evidence."
PERSISTENCE_NOT_TRUST_RESTORE_TEXT = "Persistence is not trust restoration."
PERSISTENCE_NOT_AUTOMATIC_ACTIVATION_TEXT = (
    "Persistence is not automatic activation."
)
PERSISTENCE_NOT_IMPLEMENTED_TEXT = (
    "Persistence writes are a future gate; this view-model performs no file "
    "writes, settings-file creation, ProjectSchema mutation, reload, export, "
    "discovery, validation, install/uninstall, solver execution, issue mutation, "
    "release mutation, or certification claim."
)


class OptionalSolverPluginManifestPersistenceState(str, Enum):
    """Persistence lifecycle state (OSW-EXP-090 state machine)."""

    PERSISTENCE_UNAVAILABLE = "persistence_unavailable"
    PERSISTENCE_REQUESTED = "persistence_requested"
    PERSISTENCE_BLOCKED = "persistence_blocked"
    PERSISTENCE_READY_PREVIEW = "persistence_ready_preview"
    PERSISTENCE_FUTURE_WRITE_REQUIRED = "persistence_future_write_required"
    PERSISTENCE_SCHEMA_REVIEW_REQUIRED = "persistence_schema_review_required"
    PERSISTENCE_REDACTION_REVIEW_REQUIRED = "persistence_redaction_review_required"
    PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED = (
        "persistence_stale_source_repreview_required"
    )
    PERSISTENCE_ERROR = "persistence_error"


class OptionalSolverPluginManifestPersistenceReadiness(str, Enum):
    """Persistence readiness classification."""

    UNAVAILABLE_NO_STATE = "unavailable_no_state"
    UNAVAILABLE_NO_EXPLICIT_REQUEST = "unavailable_no_explicit_request"
    BLOCKED_ACKNOWLEDGEMENT = "blocked_acknowledgement"
    BLOCKED_REDACTION_REVIEW = "blocked_redaction_review"
    BLOCKED_UNREDACTED_PATH = "blocked_unredacted_path"
    BLOCKED_STALE_SOURCE_REPREVIEW = "blocked_stale_source_repreview"
    BLOCKED_SCHEMA_VERSION = "blocked_schema_version"
    BLOCKED_SCHEMA_MIGRATION = "blocked_schema_migration"
    BLOCKED_CONFLICT = "blocked_conflict"
    BLOCKED_SHARED_STACK_WARNING = "blocked_shared_stack_warning"
    BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_claim"
    READY_PREVIEW_ONLY = "ready_preview_only"
    FUTURE_WRITE_REQUIRED = "future_write_required"
    SCHEMA_REVIEW_REQUIRED = "schema_review_required"
    ERROR = "error"


class OptionalSolverPluginManifestPersistenceAction(str, Enum):
    """Future action identifiers for a persistence surface."""

    REQUEST_PERSISTENCE = "request_persistence"
    REVIEW_REDACTION = "review_redaction"
    ACKNOWLEDGE_PERSISTENCE_NOT_VALIDATION = (
        "acknowledge_persistence_not_validation"
    )
    ACKNOWLEDGE_PERSISTENCE_NOT_TRUST_RESTORATION = (
        "acknowledge_persistence_not_trust_restoration"
    )
    ACKNOWLEDGE_NO_INSTALL = "acknowledge_no_install"
    ACKNOWLEDGE_NO_SOLVER_EXECUTION = "acknowledge_no_solver_execution"
    ACKNOWLEDGE_NO_ISSUE_CLOSURE = "acknowledge_no_issue_closure"
    ACKNOWLEDGE_NO_RELEASE_MUTATION = "acknowledge_no_release_mutation"
    ACKNOWLEDGE_LOCAL_PATH_REDACTION_REVIEWED = (
        "acknowledge_local_path_redaction_reviewed"
    )
    ACKNOWLEDGE_ACKNOWLEDGEMENTS_MAY_EXPIRE = (
        "acknowledge_persisted_acknowledgements_may_expire"
    )
    ACKNOWLEDGE_STALE_SOURCE_REQUIRES_REPREVIEW = (
        "acknowledge_stale_source_requires_repreview"
    )
    ACKNOWLEDGE_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED = (
        "acknowledge_untrusted_source_remains_untrusted"
    )
    ACKNOWLEDGE_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD = (
        "acknowledge_activation_review_required_after_reload"
    )
    ACKNOWLEDGE_NO_DISCOVERY_EXECUTION = "acknowledge_no_discovery_execution"
    ACKNOWLEDGE_NO_PLUGIN_PACKAGE_IMPORT = "acknowledge_no_plugin_package_import"
    ACKNOWLEDGE_TRUST_LABEL_NOT_CERTIFICATION = (
        "acknowledge_trust_label_not_certification"
    )
    SAVE_STATE = "save_state"
    CREATE_SETTINGS_FILE = "create_settings_file"
    MUTATE_PROJECT_SCHEMA = "mutate_project_schema"
    RELOAD_STATE = "reload_state"
    EXPORT_SUMMARY = "export_summary"
    CREATE_RELOADABLE_BUNDLE = "create_reloadable_bundle"
    AUTOMATIC_ACTIVATION = "automatic_activation"
    TRUST_RESTORATION = "trust_restoration"
    RUN_DISCOVERY = "run_discovery"
    RUN_VALIDATION = "run_validation"
    INSTALL_DEPENDENCY = "install_dependency"
    UNINSTALL_DEPENDENCY = "uninstall_dependency"
    UNINSTALL_SOLVER = "uninstall_solver"
    EXECUTE_SOLVER = "execute_solver"
    CLOSE_ISSUE = "close_issue"
    MUTATE_RELEASE = "mutate_release"


_UNSAFE_ACTIONS: frozenset[str] = frozenset(
    {
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
    }
)

PERSISTENCE_BLOCKED_TRANSITIONS: tuple[str, ...] = (
    "persisted state directly to active candidate without review",
    "persisted state directly to trusted source",
    "persisted state directly to file write in this gate",
    "persisted state directly to settings file creation",
    "persisted state directly to ProjectSchema mutation",
    "persisted state directly to discovery execution",
    "persisted state directly to validation execution",
    "persisted state directly to dependency install",
    "persisted state directly to solver execution",
    "persisted state directly to issue closure",
    "persisted state directly to release mutation",
    "persisted state directly to certification claim",
)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceCandidateInput:
    """Caller-supplied persistence candidate; no IO or trust change occurs."""

    stack_id: str
    display_name: str = ""
    source_type: str = "user_selected_json_file"
    source_label: str = ""
    source_reference: str = ""
    source_reference_display: str = ""
    trust_label: str = "untrusted_user_file"
    is_untrusted: bool = True
    source_id: str = ""
    persistence_source_kind: str = "session_only"
    activation_state: str = "inactive_preview"
    deactivation_state: str = ""
    reactivation_state: str = ""
    discovery_refresh_state: str = ""
    persistence_state: str = ""
    persistence_requested: bool = False
    built_in: bool = False
    built_in_relationship: str = ""
    has_conflict: bool = False
    conflict_resolved: bool = False
    has_shared_stack: bool = False
    shared_stack_reviewed: bool = False
    shared_stack_indicators: tuple[str, ...] = ()
    has_unsafe_claim: bool = False
    unsafe_claim_indicators: tuple[str, ...] = ()
    unsafe_claim_handled: bool = False
    stale_source: bool = False
    stale_source_state: str = ""
    stale_source_resolved: bool = False
    repreview_required: bool = False
    deactivation_history_state: str = ""
    deactivation_history_retained: bool = True
    reactivation_history_state: str = ""
    reactivation_history_retained: bool = True
    historical_evidence_state: str = ""
    evidence_retained: bool = True
    redaction_status: str = "redacted"
    redaction_required: bool = False
    redaction_reviewed: bool = False
    raw_reference_supplied: bool = False
    unredacted_path_supplied: bool = False
    secret_like_content_blocked: bool = False
    has_error: bool = False
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSourceInput:
    """Caller-supplied source/provenance record."""

    source_id: str
    source_type: str = "user_selected_json_file"
    source_label: str = ""
    source_reference: str = ""
    source_reference_display: str = ""
    trust_label: str = "untrusted_user_file"
    persistence_source_kind: str = "session_only"
    source_fingerprint_display: str = ""
    stale_source_state: str = ""
    repreview_required: bool = False
    redaction_status: str = "redacted"
    redaction_required: bool = False
    redaction_reviewed: bool = False
    raw_reference_supplied: bool = False
    raw_path_blocked: bool = False
    secret_like_content_blocked: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaInput:
    """Caller-supplied schema/migration metadata."""

    schema_version_display: str = ""
    schema_version_present: bool = False
    placeholder_schema_version_accepted: bool = False
    migration_required: bool = False
    migration_status: str = "not_required"
    migration_notes_display: str = ""
    blocker_text: str = ""
    warning_text: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceConflictInput:
    """Caller-supplied shared-stack/conflict record."""

    stack_id: str
    built_in_source: str = ""
    user_plugin_source: str = ""
    activation_state: str = ""
    deactivation_state: str = ""
    reactivation_state: str = ""
    persistence_state: str = ""
    unresolved: bool = True
    shared_stack_warning: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceUnsafeClaimInput:
    """Caller-supplied unsafe-claim record."""

    claim_id: str
    related: str = ""
    claim_text: str = ""
    blocked: bool = True
    warning_text: str = "Unsafe claims are not accepted by persistence."


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceEvidenceInput:
    """Caller-supplied evidence/history state."""

    stack_id: str = ""
    deactivation_history_state: str = ""
    deactivation_history_retained: bool = True
    reactivation_history_state: str = ""
    reactivation_history_retained: bool = True
    historical_evidence_state: str = ""
    historical_validation_evidence_retained: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceActionState:
    """Display-only action state for future persistence surfaces."""

    action: OptionalSolverPluginManifestPersistenceAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSummaryViewModel:
    """Summary header values for the persistence view-model."""

    state_scope: str
    schema_version_display: str
    readiness: str
    persistence_state: str
    candidate_count: int
    source_count: int
    acknowledgement_count: int
    acknowledgement_required_count: int
    diagnostic_count: int
    warning_count: int
    error_count: int
    conflict_count: int
    unsafe_claim_count: int
    stale_source_count: int
    redaction_required_count: int
    migration_required_count: int
    evidence_retained_count: int
    history_retained_count: int
    persistence_ready_count: int
    persistence_blocked_count: int
    status_text: str
    persistence_performed: bool = False
    file_write_performed: bool = False
    settings_file_created: bool = False
    project_schema_mutation_performed: bool = False
    automatic_activation_performed: bool = False
    trust_restoration_performed: bool = False
    dependency_installation_performed: bool = False
    dependency_uninstall_performed: bool = False
    solver_execution_performed: bool = False
    issue_mutation_performed: bool = False
    release_mutation_performed: bool = False
    certification_claimed: bool = False
    file_restore_performed: bool = False
    file_rewrite_performed: bool = False
    file_deletion_performed: bool = False
    solver_uninstall_performed: bool = False
    discovery_execution_performed: bool = False
    validation_execution_performed: bool = False
    plugin_package_import_performed: bool = False
    directory_scan_performed: bool = False
    network_fetch_performed: bool = False
    export_performed: bool = False
    reload_performed: bool = False
    reloadable_bundle_created: bool = False
    issue_closure_claimed: bool = False
    tag_mutation_performed: bool = False
    asset_mutation_performed: bool = False
    version_bump_performed: bool = False
    validation_pass_claimed: bool = False
    validation_fail_claimed: bool = False
    not_validation_evidence: bool = True
    third_party_manifests_trusted_by_default: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistedCandidateRowViewModel:
    """Candidate row for future persistence review."""

    stack_id: str
    display_name: str
    source_type: str
    source_label: str
    source_reference_display: str
    trust_label: str
    activation_state: str
    deactivation_state: str
    reactivation_state: str
    discovery_refresh_state: str
    persistence_state: str
    readiness: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    required_acknowledgements: tuple[str, ...]
    diagnostics: tuple[str, ...]
    built_in_relationship: str
    shared_stack_indicators: tuple[str, ...]
    stale_source_state: str
    repreview_required: bool
    deactivation_history_state: str
    reactivation_history_state: str
    historical_evidence_state: str
    redaction_status: str
    redacted_source_reference: bool
    deactivation_history_retained: bool
    reactivation_history_retained: bool
    historical_evidence_retained: bool
    is_untrusted: bool
    not_validation_evidence_text: str = PERSISTENCE_NOT_VALIDATION_TEXT
    not_trust_restoration_text: str = PERSISTENCE_NOT_TRUST_RESTORE_TEXT
    not_automatic_activation_text: str = PERSISTENCE_NOT_AUTOMATIC_ACTIVATION_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSourceRowViewModel:
    """Source/provenance row."""

    source_id: str
    source_type: str
    source_label: str
    source_reference_display: str
    trust_label: str
    persistence_source_kind: str
    redaction_status: str
    raw_path_blocked: bool
    source_fingerprint_display: str
    stale_source_state: str
    repreview_required: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    redacted_source_reference: bool


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel:
    """Acknowledgement row and expiry policy."""

    acknowledgement_id: str
    label: str
    required: bool
    satisfied: bool
    persisted: bool
    expires_on_reload: bool
    expires_on_source_change: bool
    expires_on_schema_change: bool
    expires_on_unsafe_claim: bool
    blocking: bool
    reason: str
    related: str
    warning_text: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceDiagnosticViewModel:
    """Persistence diagnostic row."""

    severity: str
    category: str
    code: str
    message: str
    source_reference_display: str = ""
    stack_id: str = ""
    suggested_fix: str = ""
    blocker: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceRedactionRowViewModel:
    """Redaction/privacy row."""

    raw_reference_supplied: bool
    display_reference: str
    redaction_status: str
    unredacted_path_blocked: bool
    redaction_reviewed: bool
    secret_like_content_blocked: bool
    privacy_warning_text: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaMigrationRowViewModel:
    """Schema/migration row."""

    schema_version_display: str
    schema_version_present: bool
    migration_required: bool
    migration_status: str
    migration_notes_display: str
    blocker_text: str
    warning_text: str
    this_gate_creates_no_schema_file: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel:
    """Stale-source/re-preview row."""

    stale_source_state: str
    repreview_required: bool
    source_reference_display: str
    redacted_source_reference: bool
    missing_moved_changed_not_silently_trusted: str = (
        "A missing/moved/changed source is not silently trusted."
    )
    file_io_performed: bool = False
    file_restoration_performed: bool = False
    file_rewrite_performed: bool = False
    file_deletion_performed: bool = False
    future_policy_required_if_source_cannot_be_repreviewed: str = (
        "A future policy is required if the source cannot be re-previewed."
    )


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceConflictRowViewModel:
    """Shared-stack/conflict row."""

    stack_id: str
    built_in_source: str
    user_plugin_source: str
    activation_state: str
    deactivation_state: str
    reactivation_state: str
    persistence_state: str
    built_ins_win_default: bool
    persisted_user_plugin_state_does_not_override_built_ins_silently: str
    conflicts_remain_visible_after_reload: str
    required_future_policy: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel:
    """Unsafe-claim row."""

    claim_id: str
    related: str
    claim_text: str
    blocked: bool
    warning_text: str
    unsafe_claims_not_accepted_by_persistence: str = (
        "Unsafe claims are not accepted by persistence."
    )


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceEvidenceHistoryRowViewModel:
    """Evidence/history row."""

    stack_id: str
    deactivation_history_state: str
    deactivation_history_retained: bool
    reactivation_history_state: str
    reactivation_history_retained: bool
    historical_evidence_state: str
    historical_validation_evidence_retained: bool
    persisted_state_not_validation_success: str = (
        "Persisted state is not validation success."
    )
    persisted_state_not_validation_failure: str = (
        "Persisted state is not validation failure."
    )
    skipped_missing_remains_text: str = (
        "Skipped-missing optional validation remains skipped-missing."
    )
    issue_closure_not_implied_text: str = (
        "Persistence does not close issues or imply issue closure."
    )
    evidence_not_deleted_or_rewritten_text: str = (
        "Evidence is not deleted or rewritten."
    )


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceTrustBadgeViewModel:
    """Trust/provenance badge."""

    source_type: str
    trust_label: str
    source_label: str
    activation_state: str
    deactivation_state: str
    reactivation_state: str
    discovery_refresh_state: str
    persistence_state: str
    warning_text: str
    trust_label_is_not_certification: str = TRUST_NOT_CERTIFICATION_TEXT
    persisted_state_is_not_validation_evidence: str = PERSISTENCE_NOT_VALIDATION_TEXT
    user_plugin_manifests_untrusted_by_default: str = (
        "User/plugin manifests remain untrusted by default."
    )


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceViewModel:
    """Complete pure persistence view-model."""

    summary: OptionalSolverPluginManifestPersistenceSummaryViewModel
    candidate_rows: tuple[
        OptionalSolverPluginManifestPersistedCandidateRowViewModel, ...
    ]
    source_rows: tuple[OptionalSolverPluginManifestPersistenceSourceRowViewModel, ...]
    acknowledgement_rows: tuple[
        OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel, ...
    ]
    diagnostics: tuple[OptionalSolverPluginManifestPersistenceDiagnosticViewModel, ...]
    redaction_rows: tuple[
        OptionalSolverPluginManifestPersistenceRedactionRowViewModel, ...
    ]
    schema_migration_rows: tuple[
        OptionalSolverPluginManifestPersistenceSchemaMigrationRowViewModel, ...
    ]
    stale_source_rows: tuple[
        OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel, ...
    ]
    conflict_rows: tuple[OptionalSolverPluginManifestPersistenceConflictRowViewModel, ...]
    unsafe_claim_rows: tuple[
        OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel, ...
    ]
    evidence_history_rows: tuple[
        OptionalSolverPluginManifestPersistenceEvidenceHistoryRowViewModel, ...
    ]
    trust_badges: tuple[OptionalSolverPluginManifestPersistenceTrustBadgeViewModel, ...]
    actions: tuple[OptionalSolverPluginManifestPersistenceActionState, ...]
    guidance_text: tuple[str, ...]
    safety_text: tuple[str, ...]
    blocked_transitions: tuple[str, ...] = PERSISTENCE_BLOCKED_TRANSITIONS
    reserved_diagnostic_codes: tuple[str, ...] = OSPMG_PERSISTENCE_DIAGNOSTIC_CODES
    not_validation_evidence: bool = True

    @classmethod
    def from_candidates(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
        *,
        sources: Sequence[OptionalSolverPluginManifestPersistenceSourceInput] = (),
        acknowledgements: Mapping[str, bool] | None = None,
        persisted_acknowledgements: Mapping[str, bool] | None = None,
        persistence_requested: bool = False,
        schema: OptionalSolverPluginManifestPersistenceSchemaInput | None = None,
        conflicts: Sequence[OptionalSolverPluginManifestPersistenceConflictInput] = (),
        unsafe_claims: Sequence[
            OptionalSolverPluginManifestPersistenceUnsafeClaimInput
        ] = (),
        evidence_history: Sequence[
            OptionalSolverPluginManifestPersistenceEvidenceInput
        ] = (),
        state_scope: str = "session_only",
        future_write_required: bool = False,
        schema_review_required: bool = False,
    ) -> OptionalSolverPluginManifestPersistenceViewModel:
        return build_optional_solver_plugin_manifest_persistence_viewmodel(
            candidates,
            sources=sources,
            acknowledgements=acknowledgements,
            persisted_acknowledgements=persisted_acknowledgements,
            persistence_requested=persistence_requested,
            schema=schema,
            conflicts=conflicts,
            unsafe_claims=unsafe_claims,
            evidence_history=evidence_history,
            state_scope=state_scope,
            future_write_required=future_write_required,
            schema_review_required=schema_review_required,
        )

    @classmethod
    def from_activation_viewmodel(
        cls,
        activation_view_model: object,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
        persistence_requested: bool = False,
        schema: OptionalSolverPluginManifestPersistenceSchemaInput | None = None,
    ) -> OptionalSolverPluginManifestPersistenceViewModel:
        return build_optional_solver_plugin_manifest_persistence_viewmodel(
            _candidates_from_activation_view_model(activation_view_model),
            acknowledgements=acknowledgements,
            persistence_requested=persistence_requested,
            schema=schema,
        )

    @classmethod
    def from_deactivation_viewmodel(
        cls,
        deactivation_view_model: object,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
        persistence_requested: bool = False,
        schema: OptionalSolverPluginManifestPersistenceSchemaInput | None = None,
    ) -> OptionalSolverPluginManifestPersistenceViewModel:
        return build_optional_solver_plugin_manifest_persistence_viewmodel(
            _candidates_from_deactivation_view_model(deactivation_view_model),
            acknowledgements=acknowledgements,
            persistence_requested=persistence_requested,
            schema=schema,
        )

    @classmethod
    def from_reactivation_viewmodel(
        cls,
        reactivation_view_model: object,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
        persistence_requested: bool = False,
        schema: OptionalSolverPluginManifestPersistenceSchemaInput | None = None,
    ) -> OptionalSolverPluginManifestPersistenceViewModel:
        return build_optional_solver_plugin_manifest_persistence_viewmodel(
            _candidates_from_reactivation_view_model(reactivation_view_model),
            acknowledgements=acknowledgements,
            persistence_requested=persistence_requested,
            schema=schema,
        )

    @classmethod
    def from_discovery_refresh_viewmodel(
        cls,
        discovery_refresh_view_model: object,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
        persistence_requested: bool = False,
        schema: OptionalSolverPluginManifestPersistenceSchemaInput | None = None,
    ) -> OptionalSolverPluginManifestPersistenceViewModel:
        sources = _sources_from_discovery_refresh_view_model(
            discovery_refresh_view_model
        )
        return build_optional_solver_plugin_manifest_persistence_viewmodel(
            (),
            sources=sources,
            acknowledgements=acknowledgements,
            persistence_requested=persistence_requested,
            schema=schema,
        )

    @classmethod
    def unavailable(cls) -> OptionalSolverPluginManifestPersistenceViewModel:
        return build_optional_solver_plugin_manifest_persistence_viewmodel(())

    @classmethod
    def all_blocked(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    ) -> OptionalSolverPluginManifestPersistenceViewModel:
        return build_optional_solver_plugin_manifest_persistence_viewmodel(
            candidates,
            acknowledgements={},
            persistence_requested=True,
            schema=OptionalSolverPluginManifestPersistenceSchemaInput(
                schema_version_display="osw-exp-092-preview",
                schema_version_present=True,
            ),
        )

    @classmethod
    def redaction_required(
        cls,
        candidate: OptionalSolverPluginManifestPersistenceCandidateInput,
    ) -> OptionalSolverPluginManifestPersistenceViewModel:
        updated = OptionalSolverPluginManifestPersistenceCandidateInput(
            **{
                **_candidate_input_dict(candidate),
                "redaction_required": True,
                "redaction_status": "review_required",
            }
        )
        return build_optional_solver_plugin_manifest_persistence_viewmodel(
            (updated,),
            persistence_requested=True,
            schema=OptionalSolverPluginManifestPersistenceSchemaInput(
                schema_version_display="osw-exp-092-preview",
                schema_version_present=True,
            ),
        )

    @classmethod
    def schema_review_required(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    ) -> OptionalSolverPluginManifestPersistenceViewModel:
        return build_optional_solver_plugin_manifest_persistence_viewmodel(
            candidates,
            acknowledgements={ack: True for ack in PERSISTENCE_REQUIRED_ACKS},
            persistence_requested=True,
            schema=OptionalSolverPluginManifestPersistenceSchemaInput(
                schema_version_display="future schema review",
                schema_version_present=True,
                warning_text="Future schema review is required before writes.",
            ),
            schema_review_required=True,
        )


def build_optional_solver_plugin_manifest_persistence_viewmodel(
    candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    *,
    sources: Sequence[OptionalSolverPluginManifestPersistenceSourceInput] = (),
    acknowledgements: Mapping[str, bool] | None = None,
    persisted_acknowledgements: Mapping[str, bool] | None = None,
    persistence_requested: bool = False,
    schema: OptionalSolverPluginManifestPersistenceSchemaInput | None = None,
    conflicts: Sequence[OptionalSolverPluginManifestPersistenceConflictInput] = (),
    unsafe_claims: Sequence[OptionalSolverPluginManifestPersistenceUnsafeClaimInput] = (),
    evidence_history: Sequence[OptionalSolverPluginManifestPersistenceEvidenceInput] = (),
    state_scope: str = "session_only",
    future_write_required: bool = False,
    schema_review_required: bool = False,
) -> OptionalSolverPluginManifestPersistenceViewModel:
    """Build the persistence view-model from supplied state only."""

    candidate_inputs = tuple(candidates)
    schema_input = schema or OptionalSolverPluginManifestPersistenceSchemaInput()
    acks = {str(k): bool(v) for k, v in (acknowledgements or {}).items()}
    persisted_acks = {
        str(k): bool(v) for k, v in (persisted_acknowledgements or {}).items()
    }
    explicit_request = persistence_requested or any(
        c.persistence_requested for c in candidate_inputs
    )

    all_sources = tuple(sources) or _sources_from_candidates(candidate_inputs)
    redaction_rows = _redaction_rows(candidate_inputs, all_sources)
    schema_rows = (_schema_row(schema_input),)
    conflict_rows = _conflict_rows(candidate_inputs, conflicts)
    unsafe_rows = _unsafe_claim_rows(candidate_inputs, unsafe_claims)
    stale_rows = _stale_source_rows(candidate_inputs, all_sources)
    evidence_rows = _evidence_rows(candidate_inputs, evidence_history)

    acknowledgement_rows = _acknowledgement_rows(acks, persisted_acks)
    acks_satisfied = all(
        row.satisfied for row in acknowledgement_rows if row.required
    )
    readiness = _readiness(
        candidate_inputs=candidate_inputs,
        sources=all_sources,
        explicit_request=explicit_request,
        schema=schema_input,
        acknowledgement_rows=acknowledgement_rows,
        conflict_rows=conflict_rows,
        unsafe_rows=unsafe_rows,
        stale_rows=stale_rows,
        future_write_required=future_write_required,
        schema_review_required=schema_review_required,
    )
    persistence_state = _state_for_readiness(readiness)

    candidate_rows = tuple(
        _candidate_row(
            candidate,
            readiness=_candidate_readiness(
                candidate,
                explicit_request=explicit_request,
                schema=schema_input,
                acks_satisfied=acks_satisfied,
            ),
        )
        for candidate in sorted(candidate_inputs, key=lambda c: (c.stack_id, c.source_type))
    )
    source_rows = tuple(
        _source_row(source)
        for source in sorted(all_sources, key=lambda s: (s.source_id, s.source_type))
    )
    diagnostics = _diagnostics(
        readiness=readiness,
        candidate_rows=candidate_rows,
        source_rows=source_rows,
        schema=schema_input,
        acknowledgement_rows=acknowledgement_rows,
        redaction_rows=redaction_rows,
        conflict_rows=conflict_rows,
        unsafe_rows=unsafe_rows,
        stale_rows=stale_rows,
        evidence_rows=evidence_rows,
    )
    trust_badges = _trust_badges(candidate_rows, source_rows)
    summary = _summary(
        state_scope=state_scope,
        schema=schema_input,
        readiness=readiness,
        persistence_state=persistence_state,
        candidate_rows=candidate_rows,
        source_rows=source_rows,
        acknowledgement_rows=acknowledgement_rows,
        diagnostics=diagnostics,
        conflict_rows=conflict_rows,
        unsafe_rows=unsafe_rows,
        stale_rows=stale_rows,
        redaction_rows=redaction_rows,
        evidence_rows=evidence_rows,
    )
    return OptionalSolverPluginManifestPersistenceViewModel(
        summary=summary,
        candidate_rows=candidate_rows,
        source_rows=source_rows,
        acknowledgement_rows=acknowledgement_rows,
        diagnostics=diagnostics,
        redaction_rows=redaction_rows,
        schema_migration_rows=schema_rows,
        stale_source_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_claim_rows=unsafe_rows,
        evidence_history_rows=evidence_rows,
        trust_badges=trust_badges,
        actions=_action_states(),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
    )


def redact_optional_solver_plugin_manifest_persistence_source_reference(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool]:
    """Return a safe display reference and a redaction flag."""

    return _redact_source_reference(reference, provided_label=provided_label)


def render_optional_solver_plugin_manifest_persistence_summary(
    view_model: OptionalSolverPluginManifestPersistenceViewModel,
) -> dict[str, object]:
    """Return an in-memory, redacted, JSON-ready summary."""

    summary = view_model.summary
    return {
        "state_scope": summary.state_scope,
        "schema_version_display": summary.schema_version_display,
        "readiness": summary.readiness,
        "persistence_state": summary.persistence_state,
        "candidate_count": summary.candidate_count,
        "source_count": summary.source_count,
        "persistence_ready_count": summary.persistence_ready_count,
        "persistence_blocked_count": summary.persistence_blocked_count,
        "persistence_performed": False,
        "file_write_performed": False,
        "settings_file_created": False,
        "project_schema_mutation_performed": False,
        "automatic_activation_performed": False,
        "trust_restoration_performed": False,
        "dependency_installation_performed": False,
        "dependency_uninstall_performed": False,
        "solver_execution_performed": False,
        "discovery_execution_performed": False,
        "validation_execution_performed": False,
        "plugin_package_import_performed": False,
        "directory_scan_performed": False,
        "network_fetch_performed": False,
        "export_performed": False,
        "reload_performed": False,
        "reloadable_bundle_created": False,
        "file_restore_performed": False,
        "file_rewrite_performed": False,
        "file_deletion_performed": False,
        "solver_uninstall_performed": False,
        "issue_mutation_performed": False,
        "issue_closure_claimed": False,
        "release_mutation_performed": False,
        "tag_mutation_performed": False,
        "asset_mutation_performed": False,
        "version_bump_performed": False,
        "validation_pass_claimed": False,
        "validation_fail_claimed": False,
        "certification_claimed": False,
        "not_validation_evidence": True,
        "third_party_manifests_trusted_by_default": False,
        "candidates": [
            {
                "stack_id": row.stack_id,
                "source_type": row.source_type,
                "source_reference_display": row.source_reference_display,
                "trust_label": row.trust_label,
                "persistence_state": row.persistence_state,
                "readiness": row.readiness,
                "redacted_source_reference": row.redacted_source_reference,
            }
            for row in view_model.candidate_rows
        ],
        "sources": [
            {
                "source_id": row.source_id,
                "source_type": row.source_type,
                "source_reference_display": row.source_reference_display,
                "trust_label": row.trust_label,
                "redacted_source_reference": row.redacted_source_reference,
            }
            for row in view_model.source_rows
        ],
        "diagnostics": [
            {"code": d.code, "severity": d.severity, "stack_id": d.stack_id}
            for d in view_model.diagnostics
        ],
    }


def summarize_optional_solver_plugin_manifest_persistence_viewmodel(
    view_model: OptionalSolverPluginManifestPersistenceViewModel,
) -> str:
    """Return a concise persistence summary."""

    s = view_model.summary
    return (
        "Optional solver plugin manifest persistence: "
        f"readiness={s.readiness}; state={s.persistence_state}; "
        f"candidates={s.candidate_count}; sources={s.source_count}; "
        f"ready={s.persistence_ready_count}; blocked={s.persistence_blocked_count}. "
        f"{PERSISTENCE_NOT_IMPLEMENTED_TEXT}"
    )


def explain_optional_solver_plugin_manifest_persistence_viewmodel(
    view_model: OptionalSolverPluginManifestPersistenceViewModel,
) -> str:
    """Explain the safety boundary of the persistence view-model."""

    disabled = ", ".join(
        action.action.value for action in view_model.actions if not action.enabled
    )
    return (
        summarize_optional_solver_plugin_manifest_persistence_viewmodel(view_model)
        + " The view-model transforms supplied manifest UX state only; it does "
        "not persist state, write files, create settings files, mutate "
        "ProjectSchema, implement GUI or CLI behavior, reload, export, import "
        "plugin packages, scan directories, fetch network manifests, run "
        "discovery, run validation, execute solvers, install or uninstall "
        "dependencies, mutate issues, or mutate releases. "
        f"Disabled or future-only actions: {disabled}."
    )


def _redact_source_reference(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool]:
    label = str(provided_label or "").strip()
    if label:
        return label, False
    text = str(reference or "")
    if not text:
        return "", False
    normalized = text.replace("\\", "/")
    if "/" in normalized:
        base = normalized.rsplit("/", 1)[-1] or normalized
        if base and base != text:
            return base, True
    return text, False


def _candidate_input_dict(
    candidate: OptionalSolverPluginManifestPersistenceCandidateInput,
) -> dict[str, object]:
    return {
        field: getattr(candidate, field)
        for field in OptionalSolverPluginManifestPersistenceCandidateInput.__slots__
    }


def _source_display(
    reference: str,
    display: str,
    label: str,
) -> tuple[str, bool]:
    if display:
        return display, False
    redacted_display, redacted = _redact_source_reference(reference)
    if not redacted_display and label:
        return label, False
    return redacted_display, redacted


def _candidate_readiness(
    candidate: OptionalSolverPluginManifestPersistenceCandidateInput,
    *,
    explicit_request: bool,
    schema: OptionalSolverPluginManifestPersistenceSchemaInput,
    acks_satisfied: bool,
) -> OptionalSolverPluginManifestPersistenceReadiness:
    Readiness = OptionalSolverPluginManifestPersistenceReadiness
    if candidate.has_error:
        return Readiness.ERROR
    if not explicit_request and not candidate.persistence_requested:
        return Readiness.UNAVAILABLE_NO_EXPLICIT_REQUEST
    if candidate.unredacted_path_supplied:
        return Readiness.BLOCKED_UNREDACTED_PATH
    if candidate.redaction_required and not candidate.redaction_reviewed:
        return Readiness.BLOCKED_REDACTION_REVIEW
    if not schema.schema_version_present and not schema.placeholder_schema_version_accepted:
        return Readiness.BLOCKED_SCHEMA_VERSION
    if schema.migration_required:
        return Readiness.BLOCKED_SCHEMA_MIGRATION
    if (candidate.stale_source or candidate.repreview_required) and not (
        candidate.stale_source_resolved
    ):
        return Readiness.BLOCKED_STALE_SOURCE_REPREVIEW
    if candidate.has_conflict and not candidate.conflict_resolved:
        return Readiness.BLOCKED_CONFLICT
    if candidate.has_shared_stack and not candidate.shared_stack_reviewed:
        return Readiness.BLOCKED_SHARED_STACK_WARNING
    if candidate.has_unsafe_claim and not candidate.unsafe_claim_handled:
        return Readiness.BLOCKED_UNSAFE_CLAIM
    if not acks_satisfied:
        return Readiness.BLOCKED_ACKNOWLEDGEMENT
    return Readiness.READY_PREVIEW_ONLY


def _candidate_row(
    candidate: OptionalSolverPluginManifestPersistenceCandidateInput,
    *,
    readiness: OptionalSolverPluginManifestPersistenceReadiness,
) -> OptionalSolverPluginManifestPersistedCandidateRowViewModel:
    display, redacted = _source_display(
        candidate.source_reference,
        candidate.source_reference_display,
        candidate.source_label,
    )
    state = candidate.persistence_state or _state_for_readiness(readiness).value
    diagnostics = _diagnostic_codes_for_candidate(candidate, readiness)
    warnings = list(candidate.warnings)
    if candidate.is_untrusted:
        warnings.append("Untrusted source; untrusted by default.")
    warnings.append(TRUST_NOT_CERTIFICATION_TEXT)
    warnings.append(PERSISTENCE_NOT_VALIDATION_TEXT)
    return OptionalSolverPluginManifestPersistedCandidateRowViewModel(
        stack_id=candidate.stack_id,
        display_name=candidate.display_name or candidate.stack_id,
        source_type=candidate.source_type,
        source_label=candidate.source_label,
        source_reference_display=display,
        trust_label=candidate.trust_label,
        activation_state=candidate.activation_state,
        deactivation_state=candidate.deactivation_state,
        reactivation_state=candidate.reactivation_state,
        discovery_refresh_state=candidate.discovery_refresh_state,
        persistence_state=state,
        readiness=readiness.value,
        blockers=_blockers_for_readiness(readiness),
        warnings=tuple(dict.fromkeys(warnings)),
        required_acknowledgements=PERSISTENCE_REQUIRED_ACKS,
        diagnostics=diagnostics,
        built_in_relationship=candidate.built_in_relationship,
        shared_stack_indicators=tuple(candidate.shared_stack_indicators),
        stale_source_state=(
            candidate.stale_source_state or ("stale" if candidate.stale_source else "fresh")
        ),
        repreview_required=candidate.repreview_required or candidate.stale_source,
        deactivation_history_state=candidate.deactivation_history_state or "none",
        reactivation_history_state=candidate.reactivation_history_state or "none",
        historical_evidence_state=candidate.historical_evidence_state or "none",
        redaction_status=candidate.redaction_status,
        redacted_source_reference=redacted or candidate.redaction_status == "redacted",
        deactivation_history_retained=candidate.deactivation_history_retained,
        reactivation_history_retained=candidate.reactivation_history_retained,
        historical_evidence_retained=candidate.evidence_retained,
        is_untrusted=candidate.is_untrusted,
    )


def _source_row(
    source: OptionalSolverPluginManifestPersistenceSourceInput,
) -> OptionalSolverPluginManifestPersistenceSourceRowViewModel:
    display, redacted = _source_display(
        source.source_reference,
        source.source_reference_display,
        source.source_label,
    )
    warnings = list(source.warnings)
    warnings.append(TRUST_NOT_CERTIFICATION_TEXT)
    if source.trust_label not in {"built_in", "reviewed_builtin"}:
        warnings.append("Source remains untrusted unless a separate trust gate exists.")
    return OptionalSolverPluginManifestPersistenceSourceRowViewModel(
        source_id=source.source_id,
        source_type=source.source_type,
        source_label=source.source_label,
        source_reference_display=display,
        trust_label=source.trust_label,
        persistence_source_kind=source.persistence_source_kind,
        redaction_status=source.redaction_status,
        raw_path_blocked=source.raw_path_blocked,
        source_fingerprint_display=source.source_fingerprint_display,
        stale_source_state=source.stale_source_state,
        repreview_required=source.repreview_required,
        blockers=source.blockers,
        warnings=tuple(dict.fromkeys(warnings)),
        redacted_source_reference=redacted or source.redaction_status == "redacted",
    )


def _readiness(
    *,
    candidate_inputs: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    sources: Sequence[OptionalSolverPluginManifestPersistenceSourceInput],
    explicit_request: bool,
    schema: OptionalSolverPluginManifestPersistenceSchemaInput,
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel
    ],
    conflict_rows: Sequence[OptionalSolverPluginManifestPersistenceConflictRowViewModel],
    unsafe_rows: Sequence[OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel],
    stale_rows: Sequence[OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel],
    future_write_required: bool,
    schema_review_required: bool,
) -> OptionalSolverPluginManifestPersistenceReadiness:
    Readiness = OptionalSolverPluginManifestPersistenceReadiness
    state_supplied = bool(candidate_inputs or sources)
    if any(c.has_error for c in candidate_inputs):
        return Readiness.ERROR
    if not state_supplied:
        return Readiness.UNAVAILABLE_NO_STATE
    if not explicit_request:
        return Readiness.UNAVAILABLE_NO_EXPLICIT_REQUEST
    if any(c.unredacted_path_supplied for c in candidate_inputs) or any(
        s.raw_path_blocked for s in sources
    ):
        return Readiness.BLOCKED_UNREDACTED_PATH
    local_redaction_ack = _ack_satisfied(
        acknowledgement_rows, ACK_LOCAL_PATH_REDACTION_REVIEWED
    )
    if _redaction_required(candidate_inputs, sources) and not local_redaction_ack:
        return Readiness.BLOCKED_REDACTION_REVIEW
    if not schema.schema_version_present and not schema.placeholder_schema_version_accepted:
        return Readiness.BLOCKED_SCHEMA_VERSION
    if schema.migration_required:
        return Readiness.BLOCKED_SCHEMA_MIGRATION
    stale_ack = _ack_satisfied(acknowledgement_rows, ACK_STALE_SOURCE_REQUIRES_REPREVIEW)
    if stale_rows and not stale_ack:
        return Readiness.BLOCKED_STALE_SOURCE_REPREVIEW
    if any("conflict" in row.persistence_state for row in conflict_rows):
        return Readiness.BLOCKED_CONFLICT
    if any("shared_stack" in row.persistence_state for row in conflict_rows):
        return Readiness.BLOCKED_SHARED_STACK_WARNING
    if any(row.blocked for row in unsafe_rows):
        return Readiness.BLOCKED_UNSAFE_CLAIM
    if any(row.required and not row.satisfied for row in acknowledgement_rows):
        return Readiness.BLOCKED_ACKNOWLEDGEMENT
    if schema_review_required:
        return Readiness.SCHEMA_REVIEW_REQUIRED
    if future_write_required:
        return Readiness.FUTURE_WRITE_REQUIRED
    return Readiness.READY_PREVIEW_ONLY


def _state_for_readiness(
    readiness: OptionalSolverPluginManifestPersistenceReadiness,
) -> OptionalSolverPluginManifestPersistenceState:
    State = OptionalSolverPluginManifestPersistenceState
    Readiness = OptionalSolverPluginManifestPersistenceReadiness
    if readiness == Readiness.ERROR:
        return State.PERSISTENCE_ERROR
    if readiness in {
        Readiness.UNAVAILABLE_NO_STATE,
        Readiness.UNAVAILABLE_NO_EXPLICIT_REQUEST,
    }:
        return State.PERSISTENCE_UNAVAILABLE
    if readiness == Readiness.READY_PREVIEW_ONLY:
        return State.PERSISTENCE_READY_PREVIEW
    if readiness == Readiness.FUTURE_WRITE_REQUIRED:
        return State.PERSISTENCE_FUTURE_WRITE_REQUIRED
    if readiness == Readiness.SCHEMA_REVIEW_REQUIRED:
        return State.PERSISTENCE_SCHEMA_REVIEW_REQUIRED
    if readiness == Readiness.BLOCKED_REDACTION_REVIEW:
        return State.PERSISTENCE_REDACTION_REVIEW_REQUIRED
    if readiness == Readiness.BLOCKED_STALE_SOURCE_REPREVIEW:
        return State.PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED
    return State.PERSISTENCE_BLOCKED


def _ack_satisfied(
    rows: Sequence[OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel],
    ack_id: str,
) -> bool:
    return any(row.acknowledgement_id == ack_id and row.satisfied for row in rows)


def _redaction_required(
    candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    sources: Sequence[OptionalSolverPluginManifestPersistenceSourceInput],
) -> bool:
    return any(c.redaction_required for c in candidates) or any(
        s.redaction_required for s in sources
    )


def _blockers_for_readiness(
    readiness: OptionalSolverPluginManifestPersistenceReadiness,
) -> tuple[str, ...]:
    return {
        OptionalSolverPluginManifestPersistenceReadiness.UNAVAILABLE_NO_STATE: (
            "No candidate or source state was supplied.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.UNAVAILABLE_NO_EXPLICIT_REQUEST: (
            "Persistence requires an explicit caller-supplied request.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.BLOCKED_ACKNOWLEDGEMENT: (
            "Required acknowledgements are missing.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.BLOCKED_REDACTION_REVIEW: (
            "Local path redaction review acknowledgement is missing.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.BLOCKED_UNREDACTED_PATH: (
            "Unredacted path display is blocked.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.BLOCKED_STALE_SOURCE_REPREVIEW: (
            "Stale source requires re-preview.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.BLOCKED_SCHEMA_VERSION: (
            "Schema version display is required.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.BLOCKED_SCHEMA_MIGRATION: (
            "Schema migration review is required.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.BLOCKED_CONFLICT: (
            "Built-ins win by default; conflict must be resolved.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.BLOCKED_SHARED_STACK_WARNING: (
            "Shared-stack warning must be reviewed.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.BLOCKED_UNSAFE_CLAIM: (
            "Unsafe claims are not accepted by persistence.",
        ),
        OptionalSolverPluginManifestPersistenceReadiness.ERROR: (
            "Supplied persistence state is an error.",
        ),
    }.get(readiness, ())


def _diagnostic_codes_for_candidate(
    candidate: OptionalSolverPluginManifestPersistenceCandidateInput,
    readiness: OptionalSolverPluginManifestPersistenceReadiness,
) -> tuple[str, ...]:
    Readiness = OptionalSolverPluginManifestPersistenceReadiness
    codes: list[str] = []
    if readiness == Readiness.BLOCKED_ACKNOWLEDGEMENT:
        codes.append(OSPMG_PERSISTENCE_ACK_REQUIRED)
    if readiness == Readiness.BLOCKED_REDACTION_REVIEW:
        codes.append(OSPMG_PERSISTENCE_REDACTION_REQUIRED)
    if readiness == Readiness.BLOCKED_UNREDACTED_PATH:
        codes.append(OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED)
    if readiness == Readiness.BLOCKED_STALE_SOURCE_REPREVIEW:
        codes.append(OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED)
    if readiness == Readiness.BLOCKED_SCHEMA_VERSION:
        codes.append(OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED)
    if readiness == Readiness.BLOCKED_SCHEMA_MIGRATION:
        codes.append(OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED)
    if readiness == Readiness.BLOCKED_CONFLICT:
        codes.append(OSPMG_PERSISTENCE_CONFLICT_BLOCKED)
    if readiness == Readiness.BLOCKED_UNSAFE_CLAIM:
        codes.append(OSPMG_PERSISTENCE_UNSAFE_CLAIM)
    if candidate.is_untrusted:
        codes.append(OSPMG_PERSISTENCE_UNTRUSTED_SOURCE)
    if candidate.evidence_retained:
        codes.append(OSPMG_PERSISTENCE_EVIDENCE_RETAINED)
    if candidate.deactivation_history_retained or candidate.reactivation_history_retained:
        codes.append(OSPMG_PERSISTENCE_HISTORY_RETAINED)
    return tuple(dict.fromkeys(codes))


def _sources_from_candidates(
    candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
) -> tuple[OptionalSolverPluginManifestPersistenceSourceInput, ...]:
    return tuple(
        OptionalSolverPluginManifestPersistenceSourceInput(
            source_id=c.source_id or c.stack_id,
            source_type=c.source_type,
            source_label=c.source_label or c.display_name or c.stack_id,
            source_reference=c.source_reference,
            source_reference_display=c.source_reference_display,
            trust_label=c.trust_label,
            persistence_source_kind=c.persistence_source_kind,
            stale_source_state=c.stale_source_state or ("stale" if c.stale_source else ""),
            repreview_required=c.repreview_required or c.stale_source,
            redaction_status=c.redaction_status,
            redaction_required=c.redaction_required,
            redaction_reviewed=c.redaction_reviewed,
            raw_reference_supplied=c.raw_reference_supplied or bool(c.source_reference),
            raw_path_blocked=c.unredacted_path_supplied,
            secret_like_content_blocked=c.secret_like_content_blocked,
        )
        for c in candidates
    )


def _redaction_rows(
    candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    sources: Sequence[OptionalSolverPluginManifestPersistenceSourceInput],
) -> tuple[OptionalSolverPluginManifestPersistenceRedactionRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestPersistenceRedactionRowViewModel] = []
    for c in candidates:
        display, _ = _source_display(
            c.source_reference, c.source_reference_display, c.source_label
        )
        if c.source_reference or c.redaction_required or c.unredacted_path_supplied:
            rows.append(
                OptionalSolverPluginManifestPersistenceRedactionRowViewModel(
                    raw_reference_supplied=c.raw_reference_supplied
                    or bool(c.source_reference),
                    display_reference=display,
                    redaction_status=c.redaction_status,
                    unredacted_path_blocked=c.unredacted_path_supplied,
                    redaction_reviewed=c.redaction_reviewed,
                    secret_like_content_blocked=c.secret_like_content_blocked,
                    privacy_warning_text=(
                        "Raw local paths and secret-like content are blocked or "
                        "redacted before any future persistence."
                    ),
                )
            )
    for s in sources:
        display, _ = _source_display(
            s.source_reference, s.source_reference_display, s.source_label
        )
        if s.source_reference or s.redaction_required or s.raw_path_blocked:
            rows.append(
                OptionalSolverPluginManifestPersistenceRedactionRowViewModel(
                    raw_reference_supplied=s.raw_reference_supplied
                    or bool(s.source_reference),
                    display_reference=display,
                    redaction_status=s.redaction_status,
                    unredacted_path_blocked=s.raw_path_blocked,
                    redaction_reviewed=s.redaction_reviewed,
                    secret_like_content_blocked=s.secret_like_content_blocked,
                    privacy_warning_text=(
                        "Source references are redacted by default; full local "
                        "paths are not persisted by this view-model."
                    ),
                )
            )
    return tuple(rows)


def _schema_row(
    schema: OptionalSolverPluginManifestPersistenceSchemaInput,
) -> OptionalSolverPluginManifestPersistenceSchemaMigrationRowViewModel:
    return OptionalSolverPluginManifestPersistenceSchemaMigrationRowViewModel(
        schema_version_display=schema.schema_version_display,
        schema_version_present=schema.schema_version_present,
        migration_required=schema.migration_required,
        migration_status=schema.migration_status,
        migration_notes_display=schema.migration_notes_display,
        blocker_text=schema.blocker_text
        or (
            "Schema version display is required."
            if not schema.schema_version_present
            and not schema.placeholder_schema_version_accepted
            else ""
        ),
        warning_text=schema.warning_text,
    )


def _conflict_rows(
    candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    conflicts: Sequence[OptionalSolverPluginManifestPersistenceConflictInput],
) -> tuple[OptionalSolverPluginManifestPersistenceConflictRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestPersistenceConflictRowViewModel] = []
    for c in candidates:
        if not ((c.has_conflict and not c.conflict_resolved) or c.has_shared_stack):
            continue
        display, _ = _source_display(
            c.source_reference, c.source_reference_display, c.source_label
        )
        row_state = "conflict_blocked" if c.has_conflict else "shared_stack_warning"
        rows.append(
            OptionalSolverPluginManifestPersistenceConflictRowViewModel(
                stack_id=c.stack_id,
                built_in_source=f"builtin:{c.stack_id}",
                user_plugin_source=display or c.source_label or c.source_type,
                activation_state=c.activation_state,
                deactivation_state=c.deactivation_state,
                reactivation_state=c.reactivation_state,
                persistence_state=row_state,
                built_ins_win_default=True,
                persisted_user_plugin_state_does_not_override_built_ins_silently=(
                    "Persisted user/plugin state does not override built-ins silently."
                ),
                conflicts_remain_visible_after_reload=(
                    "Conflicts remain visible after reload."
                ),
                required_future_policy=(
                    "An explicit future policy is required to resolve this shared "
                    "stack or conflict."
                ),
            )
        )
    for c in conflicts:
        if not c.unresolved and not c.shared_stack_warning:
            continue
        rows.append(
            OptionalSolverPluginManifestPersistenceConflictRowViewModel(
                stack_id=c.stack_id,
                built_in_source=c.built_in_source or f"builtin:{c.stack_id}",
                user_plugin_source=c.user_plugin_source,
                activation_state=c.activation_state,
                deactivation_state=c.deactivation_state,
                reactivation_state=c.reactivation_state,
                persistence_state=c.persistence_state
                or ("conflict_blocked" if c.unresolved else "shared_stack_warning"),
                built_ins_win_default=True,
                persisted_user_plugin_state_does_not_override_built_ins_silently=(
                    "Persisted user/plugin state does not override built-ins silently."
                ),
                conflicts_remain_visible_after_reload=(
                    "Conflicts remain visible after reload."
                ),
                required_future_policy="A future conflict policy is required.",
            )
        )
    return tuple(rows)


def _unsafe_claim_rows(
    candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    unsafe_claims: Sequence[OptionalSolverPluginManifestPersistenceUnsafeClaimInput],
) -> tuple[OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel] = []
    for c in candidates:
        if not c.has_unsafe_claim:
            continue
        indicators = c.unsafe_claim_indicators or ("unsafe claim",)
        for index, claim in enumerate(indicators):
            rows.append(
                OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel(
                    claim_id=f"{c.stack_id}:{index}",
                    related=c.stack_id,
                    claim_text=claim,
                    blocked=not c.unsafe_claim_handled,
                    warning_text="Unsafe claims are not accepted by persistence.",
                )
            )
    for claim in unsafe_claims:
        rows.append(
            OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel(
                claim_id=claim.claim_id,
                related=claim.related,
                claim_text=claim.claim_text,
                blocked=claim.blocked,
                warning_text=claim.warning_text,
            )
        )
    return tuple(rows)


def _stale_source_rows(
    candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    sources: Sequence[OptionalSolverPluginManifestPersistenceSourceInput],
) -> tuple[OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel] = []
    for c in candidates:
        if not (c.stale_source or c.repreview_required):
            continue
        display, redacted = _source_display(
            c.source_reference, c.source_reference_display, c.source_label
        )
        rows.append(
            OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel(
                stale_source_state=c.stale_source_state or "stale",
                repreview_required=True,
                source_reference_display=display,
                redacted_source_reference=redacted or c.redaction_status == "redacted",
            )
        )
    for s in sources:
        if not (s.stale_source_state or s.repreview_required):
            continue
        display, redacted = _source_display(
            s.source_reference, s.source_reference_display, s.source_label
        )
        rows.append(
            OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel(
                stale_source_state=s.stale_source_state or "stale",
                repreview_required=s.repreview_required,
                source_reference_display=display,
                redacted_source_reference=redacted or s.redaction_status == "redacted",
            )
        )
    return tuple(rows)


def _evidence_rows(
    candidates: Sequence[OptionalSolverPluginManifestPersistenceCandidateInput],
    evidence_history: Sequence[OptionalSolverPluginManifestPersistenceEvidenceInput],
) -> tuple[OptionalSolverPluginManifestPersistenceEvidenceHistoryRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestPersistenceEvidenceHistoryRowViewModel] = []
    for c in candidates:
        if not (
            c.deactivation_history_state
            or c.reactivation_history_state
            or c.historical_evidence_state
            or c.deactivation_history_retained
            or c.reactivation_history_retained
            or c.evidence_retained
        ):
            continue
        rows.append(
            OptionalSolverPluginManifestPersistenceEvidenceHistoryRowViewModel(
                stack_id=c.stack_id,
                deactivation_history_state=c.deactivation_history_state or "none",
                deactivation_history_retained=c.deactivation_history_retained,
                reactivation_history_state=c.reactivation_history_state or "none",
                reactivation_history_retained=c.reactivation_history_retained,
                historical_evidence_state=c.historical_evidence_state or "none",
                historical_validation_evidence_retained=c.evidence_retained,
            )
        )
    for e in evidence_history:
        rows.append(
            OptionalSolverPluginManifestPersistenceEvidenceHistoryRowViewModel(
                stack_id=e.stack_id,
                deactivation_history_state=e.deactivation_history_state or "none",
                deactivation_history_retained=e.deactivation_history_retained,
                reactivation_history_state=e.reactivation_history_state or "none",
                reactivation_history_retained=e.reactivation_history_retained,
                historical_evidence_state=e.historical_evidence_state or "none",
                historical_validation_evidence_retained=(
                    e.historical_validation_evidence_retained
                ),
            )
        )
    return tuple(rows)


def _acknowledgement_rows(
    acks: Mapping[str, bool],
    persisted_acks: Mapping[str, bool],
) -> tuple[OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel] = []
    for ack_id in PERSISTENCE_REQUIRED_ACKS:
        satisfied = bool(acks.get(ack_id, False))
        persisted = bool(persisted_acks.get(ack_id, False))
        rows.append(
            OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel(
                acknowledgement_id=ack_id,
                label=_ACK_LABELS[ack_id],
                required=True,
                satisfied=satisfied,
                persisted=persisted,
                expires_on_reload=ack_id
                in {
                    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
                    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
                    ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD,
                },
                expires_on_source_change=ack_id
                in {
                    ACK_LOCAL_PATH_REDACTION_REVIEWED,
                    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
                    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
                    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
                },
                expires_on_schema_change=ack_id
                in {
                    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
                    ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD,
                },
                expires_on_unsafe_claim=ack_id
                in {
                    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
                    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
                    ACK_TRUST_LABEL_NOT_CERTIFICATION,
                },
                blocking=not satisfied,
                reason=(
                    "Required acknowledgement is satisfied."
                    if satisfied
                    else "Required acknowledgement is missing; persistence is blocked."
                ),
                related="persistence",
                warning_text=_ACK_LABELS[ack_id],
            )
        )
    return tuple(rows)


def _diagnostics(
    *,
    readiness: OptionalSolverPluginManifestPersistenceReadiness,
    candidate_rows: Sequence[OptionalSolverPluginManifestPersistedCandidateRowViewModel],
    source_rows: Sequence[OptionalSolverPluginManifestPersistenceSourceRowViewModel],
    schema: OptionalSolverPluginManifestPersistenceSchemaInput,
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel
    ],
    redaction_rows: Sequence[OptionalSolverPluginManifestPersistenceRedactionRowViewModel],
    conflict_rows: Sequence[OptionalSolverPluginManifestPersistenceConflictRowViewModel],
    unsafe_rows: Sequence[OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel],
    stale_rows: Sequence[OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel],
    evidence_rows: Sequence[
        OptionalSolverPluginManifestPersistenceEvidenceHistoryRowViewModel
    ],
) -> tuple[OptionalSolverPluginManifestPersistenceDiagnosticViewModel, ...]:
    items: list[OptionalSolverPluginManifestPersistenceDiagnosticViewModel] = []

    def add(
        code: str,
        severity: str,
        *,
        blocker: bool = False,
        stack_id: str = "",
        source_reference_display: str = "",
    ) -> None:
        items.append(
            OptionalSolverPluginManifestPersistenceDiagnosticViewModel(
                severity=severity,
                category="persistence",
                code=code,
                message=_diagnostic_message(code),
                source_reference_display=source_reference_display,
                stack_id=stack_id,
                suggested_fix=_diagnostic_fix(code),
                blocker=blocker,
            )
        )

    if readiness == OptionalSolverPluginManifestPersistenceReadiness.UNAVAILABLE_NO_STATE:
        add(OSPMG_PERSISTENCE_NOT_IMPLEMENTED, "info", blocker=False)
    if any(row.required and not row.satisfied for row in acknowledgement_rows):
        add(OSPMG_PERSISTENCE_ACK_REQUIRED, "warning", blocker=True)
    if any(
        row.redaction_status in {"required", "review_required"}
        or row.unredacted_path_blocked
        or row.secret_like_content_blocked
        for row in redaction_rows
    ):
        add(OSPMG_PERSISTENCE_REDACTION_REQUIRED, "warning", blocker=True)
    if any(row.unredacted_path_blocked for row in redaction_rows):
        add(OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED, "error", blocker=True)
    if stale_rows:
        add(OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED, "warning", blocker=True)
    if not schema.schema_version_present and not schema.placeholder_schema_version_accepted:
        add(OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED, "warning", blocker=True)
    if schema.migration_required:
        add(OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED, "warning", blocker=True)
    if any("conflict" in row.persistence_state for row in conflict_rows):
        add(OSPMG_PERSISTENCE_CONFLICT_BLOCKED, "warning", blocker=True)
    if any(row.blocked for row in unsafe_rows):
        add(OSPMG_PERSISTENCE_UNSAFE_CLAIM, "error", blocker=True)
    if any(row.is_untrusted for row in candidate_rows) or any(
        row.trust_label not in {"built_in", "reviewed_builtin"} for row in source_rows
    ):
        add(OSPMG_PERSISTENCE_UNTRUSTED_SOURCE, "warning")
    if evidence_rows:
        add(OSPMG_PERSISTENCE_EVIDENCE_RETAINED, "info")
        add(OSPMG_PERSISTENCE_HISTORY_RETAINED, "info")

    for row in candidate_rows:
        for code in row.diagnostics:
            if code in {
                OSPMG_PERSISTENCE_UNTRUSTED_SOURCE,
                OSPMG_PERSISTENCE_EVIDENCE_RETAINED,
                OSPMG_PERSISTENCE_HISTORY_RETAINED,
            }:
                continue
            add(
                code,
                "error"
                if code
                in {
                    OSPMG_PERSISTENCE_UNSAFE_CLAIM,
                    OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED,
                }
                else "warning",
                blocker=code
                not in {
                    OSPMG_PERSISTENCE_UNTRUSTED_SOURCE,
                    OSPMG_PERSISTENCE_EVIDENCE_RETAINED,
                    OSPMG_PERSISTENCE_HISTORY_RETAINED,
                },
                stack_id=row.stack_id,
                source_reference_display=row.source_reference_display,
            )

    for code in (
        OSPMG_PERSISTENCE_NOT_IMPLEMENTED,
        OSPMG_PERSISTENCE_NOT_VALIDATION,
        OSPMG_PERSISTENCE_NOT_TRUST_RESTORE,
        OSPMG_PERSISTENCE_NO_INSTALL,
        OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION,
        OSPMG_PERSISTENCE_NOT_ISSUE_CLOSURE,
        OSPMG_PERSISTENCE_NOT_RELEASE_MUTATION,
        OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION,
        OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT,
        OSPMG_PERSISTENCE_FUTURE_GATE,
    ):
        add(code, "info")
    return _dedupe_diagnostics(items)


def _dedupe_diagnostics(
    items: Sequence[OptionalSolverPluginManifestPersistenceDiagnosticViewModel],
) -> tuple[OptionalSolverPluginManifestPersistenceDiagnosticViewModel, ...]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[OptionalSolverPluginManifestPersistenceDiagnosticViewModel] = []
    for item in items:
        key = (item.code, item.stack_id, item.source_reference_display)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return tuple(deduped)


def _diagnostic_message(code: str) -> str:
    return {
        OSPMG_PERSISTENCE_NOT_IMPLEMENTED: PERSISTENCE_NOT_IMPLEMENTED_TEXT,
        OSPMG_PERSISTENCE_ACK_REQUIRED: "Required acknowledgements are missing.",
        OSPMG_PERSISTENCE_NOT_VALIDATION: "Persistence is not validation evidence.",
        OSPMG_PERSISTENCE_NOT_TRUST_RESTORE: "Persistence does not restore trust.",
        OSPMG_PERSISTENCE_NO_INSTALL: "Persistence does not install dependencies.",
        OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION: "Persistence does not execute solvers.",
        OSPMG_PERSISTENCE_NOT_ISSUE_CLOSURE: "Persistence does not close issues.",
        OSPMG_PERSISTENCE_NOT_RELEASE_MUTATION: "Persistence does not mutate releases.",
        OSPMG_PERSISTENCE_REDACTION_REQUIRED: "Redaction review is required.",
        OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED: "Unredacted paths are blocked.",
        OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED: (
            "Stale sources require re-preview."
        ),
        OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED: "Schema version display is required.",
        OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED: "Schema migration is required.",
        OSPMG_PERSISTENCE_UNTRUSTED_SOURCE: "Source is untrusted by default.",
        OSPMG_PERSISTENCE_CONFLICT_BLOCKED: "Built-ins win; conflict remains blocked.",
        OSPMG_PERSISTENCE_UNSAFE_CLAIM: (
            "Unsafe claims are not accepted by persistence."
        ),
        OSPMG_PERSISTENCE_EVIDENCE_RETAINED: "Historical evidence is retained.",
        OSPMG_PERSISTENCE_HISTORY_RETAINED: (
            "Deactivation/reactivation history is retained."
        ),
        OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION: (
            "Persistence does not run discovery."
        ),
        OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT: (
            "Persistence does not import plugin packages."
        ),
        OSPMG_PERSISTENCE_FUTURE_GATE: (
            "File persistence, reload, schema, GUI, CLI, and export remain future gates."
        ),
    }.get(code, code)


def _diagnostic_fix(code: str) -> str:
    return {
        OSPMG_PERSISTENCE_ACK_REQUIRED: "Satisfy required acknowledgements.",
        OSPMG_PERSISTENCE_REDACTION_REQUIRED: "Review redacted local path display.",
        OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED: "Use a redacted display reference.",
        OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED: (
            "Re-preview the source through a future explicit review gate."
        ),
        OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED: "Supply schema version metadata.",
        OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED: "Run a future schema migration gate.",
        OSPMG_PERSISTENCE_CONFLICT_BLOCKED: "Resolve duplicate stack ids; built-ins win.",
        OSPMG_PERSISTENCE_UNSAFE_CLAIM: "Remove unsafe manifest claims.",
    }.get(code, "")


def _trust_badges(
    candidates: Sequence[OptionalSolverPluginManifestPersistedCandidateRowViewModel],
    sources: Sequence[OptionalSolverPluginManifestPersistenceSourceRowViewModel],
) -> tuple[OptionalSolverPluginManifestPersistenceTrustBadgeViewModel, ...]:
    seen: dict[tuple[str, str], OptionalSolverPluginManifestPersistenceTrustBadgeViewModel] = {}
    for row in candidates:
        key = (row.source_type, row.trust_label)
        if key in seen:
            continue
        seen[key] = OptionalSolverPluginManifestPersistenceTrustBadgeViewModel(
            source_type=row.source_type,
            trust_label=row.trust_label,
            source_label=row.source_label,
            activation_state=row.activation_state,
            deactivation_state=row.deactivation_state,
            reactivation_state=row.reactivation_state,
            discovery_refresh_state=row.discovery_refresh_state,
            persistence_state=row.persistence_state,
            warning_text=(
                "Untrusted source; untrusted by default."
                if row.is_untrusted
                else "Built-in/reviewed source; trust label is not certification."
            ),
        )
    for row in sources:
        key = (row.source_type, row.trust_label)
        if key in seen:
            continue
        seen[key] = OptionalSolverPluginManifestPersistenceTrustBadgeViewModel(
            source_type=row.source_type,
            trust_label=row.trust_label,
            source_label=row.source_label,
            activation_state="",
            deactivation_state="",
            reactivation_state="",
            discovery_refresh_state="",
            persistence_state="source_provenance_only",
            warning_text=(
                "Untrusted source; untrusted by default."
                if row.trust_label not in {"built_in", "reviewed_builtin"}
                else "Built-in/reviewed source; trust label is not certification."
            ),
        )
    return tuple(seen[key] for key in sorted(seen))


def _summary(
    *,
    state_scope: str,
    schema: OptionalSolverPluginManifestPersistenceSchemaInput,
    readiness: OptionalSolverPluginManifestPersistenceReadiness,
    persistence_state: OptionalSolverPluginManifestPersistenceState,
    candidate_rows: Sequence[OptionalSolverPluginManifestPersistedCandidateRowViewModel],
    source_rows: Sequence[OptionalSolverPluginManifestPersistenceSourceRowViewModel],
    acknowledgement_rows: Sequence[
        OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel
    ],
    diagnostics: Sequence[OptionalSolverPluginManifestPersistenceDiagnosticViewModel],
    conflict_rows: Sequence[OptionalSolverPluginManifestPersistenceConflictRowViewModel],
    unsafe_rows: Sequence[OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel],
    stale_rows: Sequence[OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel],
    redaction_rows: Sequence[OptionalSolverPluginManifestPersistenceRedactionRowViewModel],
    evidence_rows: Sequence[
        OptionalSolverPluginManifestPersistenceEvidenceHistoryRowViewModel
    ],
) -> OptionalSolverPluginManifestPersistenceSummaryViewModel:
    ready = sum(
        1
        for row in candidate_rows
        if row.readiness
        == OptionalSolverPluginManifestPersistenceReadiness.READY_PREVIEW_ONLY.value
    )
    blocked = sum(1 for row in candidate_rows if row.readiness.startswith("blocked_"))
    warnings = sum(1 for d in diagnostics if d.severity == "warning")
    errors = sum(1 for d in diagnostics if d.severity in {"error", "blocker"})
    history_retained = sum(
        1
        for row in evidence_rows
        if row.deactivation_history_retained or row.reactivation_history_retained
    )
    evidence_retained = sum(
        1 for row in evidence_rows if row.historical_validation_evidence_retained
    )
    status = (
        f"Persistence ({readiness.value}): {len(candidate_rows)} candidate(s), "
        f"{len(source_rows)} source(s), {ready} ready-preview, {blocked} blocked. "
        "Persistence is not implemented and is not validation evidence."
    )
    return OptionalSolverPluginManifestPersistenceSummaryViewModel(
        state_scope=state_scope,
        schema_version_display=schema.schema_version_display,
        readiness=readiness.value,
        persistence_state=persistence_state.value,
        candidate_count=len(candidate_rows),
        source_count=len(source_rows),
        acknowledgement_count=len(acknowledgement_rows),
        acknowledgement_required_count=sum(
            1 for row in acknowledgement_rows if row.required
        ),
        diagnostic_count=len(diagnostics),
        warning_count=warnings,
        error_count=errors,
        conflict_count=len(conflict_rows),
        unsafe_claim_count=len(unsafe_rows),
        stale_source_count=len(stale_rows),
        redaction_required_count=sum(
            1
            for row in redaction_rows
            if row.redaction_status in {"required", "review_required"}
            or row.unredacted_path_blocked
            or row.secret_like_content_blocked
        ),
        migration_required_count=1 if schema.migration_required else 0,
        evidence_retained_count=evidence_retained,
        history_retained_count=history_retained,
        persistence_ready_count=ready,
        persistence_blocked_count=blocked,
        status_text=status,
    )


def _action_states() -> tuple[OptionalSolverPluginManifestPersistenceActionState, ...]:
    states: list[OptionalSolverPluginManifestPersistenceActionState] = []
    for action in OptionalSolverPluginManifestPersistenceAction:
        unsafe = action.value in _UNSAFE_ACTIONS
        states.append(
            OptionalSolverPluginManifestPersistenceActionState(
                action=action,
                label=action.value.replace("_", " ").title(),
                enabled=False,
                available=not unsafe,
                reason=_action_reason(action),
                future_action=True,
            )
        )
    return tuple(states)


def _action_reason(action: OptionalSolverPluginManifestPersistenceAction) -> str:
    if action.value in _UNSAFE_ACTIONS:
        return {
            OptionalSolverPluginManifestPersistenceAction.SAVE_STATE.value: (
                "File persistence is a future gate; this view-model writes no files."
            ),
            OptionalSolverPluginManifestPersistenceAction.CREATE_SETTINGS_FILE.value: (
                "Settings file creation is unavailable in this gate."
            ),
            OptionalSolverPluginManifestPersistenceAction.MUTATE_PROJECT_SCHEMA.value: (
                "ProjectSchema mutation is unavailable."
            ),
            OptionalSolverPluginManifestPersistenceAction.RELOAD_STATE.value: (
                "Reload behavior is a future gate."
            ),
            OptionalSolverPluginManifestPersistenceAction.EXPORT_SUMMARY.value: (
                "Export behavior is a future gate."
            ),
            OptionalSolverPluginManifestPersistenceAction.CREATE_RELOADABLE_BUNDLE.value: (
                "Reloadable bundles require a future gate."
            ),
            OptionalSolverPluginManifestPersistenceAction.AUTOMATIC_ACTIVATION.value: (
                "Automatic activation is unavailable."
            ),
            OptionalSolverPluginManifestPersistenceAction.TRUST_RESTORATION.value: (
                "Trust restoration is unavailable."
            ),
            OptionalSolverPluginManifestPersistenceAction.RUN_DISCOVERY.value: (
                "Discovery execution is unavailable from this view-model."
            ),
            OptionalSolverPluginManifestPersistenceAction.RUN_VALIDATION.value: (
                "Validation requires a separate validation gate."
            ),
            OptionalSolverPluginManifestPersistenceAction.INSTALL_DEPENDENCY.value: (
                "Dependency installation is unavailable."
            ),
            OptionalSolverPluginManifestPersistenceAction.UNINSTALL_DEPENDENCY.value: (
                "Dependency uninstall is unavailable."
            ),
            OptionalSolverPluginManifestPersistenceAction.UNINSTALL_SOLVER.value: (
                "Solver uninstall is unavailable."
            ),
            OptionalSolverPluginManifestPersistenceAction.EXECUTE_SOLVER.value: (
                "Solver execution is unavailable."
            ),
            OptionalSolverPluginManifestPersistenceAction.CLOSE_ISSUE.value: (
                "Issue closure requires a separate validation and closure gate."
            ),
            OptionalSolverPluginManifestPersistenceAction.MUTATE_RELEASE.value: (
                "Release mutation is unavailable."
            ),
        }[action.value]
    return (
        "Future GUI/CLI acknowledgement or review action; this view-model "
        "persists nothing and mutates nothing."
    )


def _guidance_text() -> tuple[str, ...]:
    return (
        "Persistence readiness is data-only.",
        PERSISTENCE_NOT_IMPLEMENTED_TEXT,
        PERSISTENCE_NOT_VALIDATION_TEXT,
        PERSISTENCE_NOT_TRUST_RESTORE_TEXT,
        PERSISTENCE_NOT_AUTOMATIC_ACTIVATION_TEXT,
        TRUST_NOT_CERTIFICATION_TEXT,
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Built-ins win by default; persisted state does not override them silently.",
        "Stale or missing sources require re-preview through a future explicit gate.",
        "Deactivation/reactivation history and historical validation evidence are retained.",
        "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
        "bounded, issue-specific evidence; skipped-missing remains historical "
        "non-pass evidence.",
    )


def _safety_text() -> tuple[str, ...]:
    return (
        "No runtime persistence behavior.",
        "No file writes.",
        "No settings file creation.",
        "No ProjectSchema mutation.",
        "No GUI behavior.",
        "No CLI behavior.",
        "No reload behavior.",
        "No export behavior.",
        "No automatic activation.",
        "No trust restoration.",
        "No file restoration.",
        "No file rewrite.",
        "No file deletion.",
        "No dependency installation.",
        "No dependency uninstall.",
        "No solver uninstall.",
        "No plugin package import.",
        "No directory scan.",
        "No network fetch.",
        "No discovery execution.",
        "No validation execution.",
        "No solver execution.",
        "No issue mutation.",
        "No release mutation.",
        "No tag mutation.",
        "No asset mutation.",
        "No version bump.",
        "No validation-pass claim.",
        "No validation-fail claim.",
        "No issue-closure claim.",
        "No certification claim.",
    )


def _candidates_from_activation_view_model(
    activation_view_model: object,
) -> tuple[OptionalSolverPluginManifestPersistenceCandidateInput, ...]:
    conflict_stack_ids = {
        getattr(row, "stack_id", "") for row in getattr(activation_view_model, "conflict_rows", ())
    }
    candidates: list[OptionalSolverPluginManifestPersistenceCandidateInput] = []
    for row in getattr(activation_view_model, "candidate_rows", ()):
        candidates.append(
            OptionalSolverPluginManifestPersistenceCandidateInput(
                stack_id=getattr(row, "stack_id", ""),
                display_name=getattr(row, "display_name", ""),
                source_type=getattr(row, "source_type", "user_selected_json_file"),
                source_label=getattr(row, "source_label", ""),
                source_reference=getattr(row, "source_reference_display", ""),
                trust_label=getattr(row, "trust_label", "untrusted_user_file"),
                is_untrusted=getattr(row, "is_untrusted", True),
                activation_state=getattr(row, "activation_state", ""),
                has_conflict=getattr(row, "stack_id", "") in conflict_stack_ids,
                has_unsafe_claim=bool(getattr(row, "unsafe_claim_indicators", ())),
                unsafe_claim_indicators=tuple(
                    getattr(row, "unsafe_claim_indicators", ())
                ),
                built_in_relationship=getattr(row, "built_in_relationship", ""),
            )
        )
    return tuple(candidates)


def _candidates_from_deactivation_view_model(
    deactivation_view_model: object,
) -> tuple[OptionalSolverPluginManifestPersistenceCandidateInput, ...]:
    shared_stack_ids = {
        getattr(row, "stack_id", "")
        for row in getattr(deactivation_view_model, "shared_stack_rows", ())
    }
    candidates: list[OptionalSolverPluginManifestPersistenceCandidateInput] = []
    for row in getattr(deactivation_view_model, "candidate_rows", ()):
        candidates.append(
            OptionalSolverPluginManifestPersistenceCandidateInput(
                stack_id=getattr(row, "stack_id", ""),
                display_name=getattr(row, "display_name", ""),
                source_type=getattr(row, "source_type", "user_selected_json_file"),
                source_label=getattr(row, "source_label", ""),
                source_reference=getattr(row, "source_reference_display", ""),
                trust_label=getattr(row, "trust_label", "untrusted_user_file"),
                is_untrusted=getattr(row, "is_untrusted", True),
                activation_state=getattr(row, "activation_state", ""),
                deactivation_state=getattr(row, "deactivation_state", ""),
                built_in_relationship=getattr(row, "built_in_relationship", ""),
                has_shared_stack=getattr(row, "stack_id", "") in shared_stack_ids,
                shared_stack_indicators=tuple(
                    getattr(row, "shared_stack_indicators", ())
                ),
                deactivation_history_state="deactivation_state_supplied",
                historical_evidence_state=getattr(row, "historical_evidence_state", ""),
                evidence_retained=getattr(row, "evidence_retained", True),
            )
        )
    return tuple(candidates)


def _candidates_from_reactivation_view_model(
    reactivation_view_model: object,
) -> tuple[OptionalSolverPluginManifestPersistenceCandidateInput, ...]:
    shared_stack_ids = {
        getattr(row, "stack_id", "")
        for row in getattr(reactivation_view_model, "shared_stack_rows", ())
    }
    candidates: list[OptionalSolverPluginManifestPersistenceCandidateInput] = []
    for row in getattr(reactivation_view_model, "candidate_rows", ()):
        candidates.append(
            OptionalSolverPluginManifestPersistenceCandidateInput(
                stack_id=getattr(row, "stack_id", ""),
                display_name=getattr(row, "display_name", ""),
                source_type=getattr(row, "source_type", "user_selected_json_file"),
                source_label=getattr(row, "source_label", ""),
                source_reference=getattr(row, "source_reference_display", ""),
                trust_label=getattr(row, "trust_label", "untrusted_user_file"),
                is_untrusted=getattr(row, "is_untrusted", True),
                activation_state=getattr(row, "activation_state", ""),
                deactivation_state=getattr(row, "deactivation_state", ""),
                reactivation_state=getattr(row, "reactivation_state", ""),
                built_in_relationship=getattr(row, "built_in_relationship", ""),
                has_shared_stack=getattr(row, "stack_id", "") in shared_stack_ids,
                shared_stack_indicators=tuple(
                    getattr(row, "shared_stack_indicators", ())
                ),
                stale_source=getattr(row, "repreview_required", False),
                stale_source_state=getattr(row, "stale_source_state", ""),
                repreview_required=getattr(row, "repreview_required", False),
                deactivation_history_state=getattr(
                    row, "deactivation_history_state", ""
                ),
                historical_evidence_state=getattr(row, "historical_evidence_state", ""),
            )
        )
    return tuple(candidates)


def _sources_from_discovery_refresh_view_model(
    discovery_refresh_view_model: object,
) -> tuple[OptionalSolverPluginManifestPersistenceSourceInput, ...]:
    sources: list[OptionalSolverPluginManifestPersistenceSourceInput] = []
    for row in getattr(discovery_refresh_view_model, "source_rows", ()):
        sources.append(
            OptionalSolverPluginManifestPersistenceSourceInput(
                source_id=getattr(row, "stack_id", ""),
                source_type=getattr(row, "source_type", "user_selected_json_file"),
                source_label=getattr(row, "source_label", ""),
                source_reference=getattr(row, "source_reference_display", ""),
                trust_label=getattr(row, "trust_label", "untrusted_user_file"),
                persistence_source_kind="discovery_refresh_supplied_state",
                redaction_status="redacted"
                if getattr(row, "redacted_source_reference", False)
                else "not_required",
            )
        )
    return tuple(sources)


__all__ = [
    "ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD",
    "ACK_LOCAL_PATH_REDACTION_REVIEWED",
    "ACK_NO_DISCOVERY_EXECUTION",
    "ACK_NO_PLUGIN_PACKAGE_IMPORT",
    "ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE",
    "ACK_PERSISTENCE_NOT_INSTALL",
    "ACK_PERSISTENCE_NOT_ISSUE_CLOSURE",
    "ACK_PERSISTENCE_NOT_RELEASE_MUTATION",
    "ACK_PERSISTENCE_NOT_TRUST_RESTORATION",
    "ACK_PERSISTENCE_NOT_VALIDATION",
    "ACK_PERSISTENCE_NO_SOLVER_EXECUTION",
    "ACK_STALE_SOURCE_REQUIRES_REPREVIEW",
    "ACK_TRUST_LABEL_NOT_CERTIFICATION",
    "ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED",
    "OSPMG_PERSISTENCE_ACK_REQUIRED",
    "OSPMG_PERSISTENCE_CONFLICT_BLOCKED",
    "OSPMG_PERSISTENCE_DIAGNOSTIC_CODES",
    "OSPMG_PERSISTENCE_EVIDENCE_RETAINED",
    "OSPMG_PERSISTENCE_FUTURE_GATE",
    "OSPMG_PERSISTENCE_HISTORY_RETAINED",
    "OSPMG_PERSISTENCE_NOT_IMPLEMENTED",
    "OSPMG_PERSISTENCE_NOT_ISSUE_CLOSURE",
    "OSPMG_PERSISTENCE_NOT_RELEASE_MUTATION",
    "OSPMG_PERSISTENCE_NOT_TRUST_RESTORE",
    "OSPMG_PERSISTENCE_NOT_VALIDATION",
    "OSPMG_PERSISTENCE_NO_DISCOVERY_EXECUTION",
    "OSPMG_PERSISTENCE_NO_INSTALL",
    "OSPMG_PERSISTENCE_NO_PLUGIN_IMPORT",
    "OSPMG_PERSISTENCE_NO_SOLVER_EXECUTION",
    "OSPMG_PERSISTENCE_REDACTION_REQUIRED",
    "OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED",
    "OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED",
    "OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED",
    "OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED",
    "OSPMG_PERSISTENCE_UNSAFE_CLAIM",
    "OSPMG_PERSISTENCE_UNTRUSTED_SOURCE",
    "PERSISTENCE_BLOCKED_TRANSITIONS",
    "PERSISTENCE_REQUIRED_ACKS",
    "OptionalSolverPluginManifestPersistedCandidateRowViewModel",
    "OptionalSolverPluginManifestPersistenceAcknowledgementRowViewModel",
    "OptionalSolverPluginManifestPersistenceAction",
    "OptionalSolverPluginManifestPersistenceActionState",
    "OptionalSolverPluginManifestPersistenceCandidateInput",
    "OptionalSolverPluginManifestPersistenceConflictInput",
    "OptionalSolverPluginManifestPersistenceConflictRowViewModel",
    "OptionalSolverPluginManifestPersistenceDiagnosticViewModel",
    "OptionalSolverPluginManifestPersistenceEvidenceHistoryRowViewModel",
    "OptionalSolverPluginManifestPersistenceEvidenceInput",
    "OptionalSolverPluginManifestPersistenceReadiness",
    "OptionalSolverPluginManifestPersistenceRedactionRowViewModel",
    "OptionalSolverPluginManifestPersistenceSchemaInput",
    "OptionalSolverPluginManifestPersistenceSchemaMigrationRowViewModel",
    "OptionalSolverPluginManifestPersistenceSourceInput",
    "OptionalSolverPluginManifestPersistenceSourceRowViewModel",
    "OptionalSolverPluginManifestPersistenceStaleSourceRowViewModel",
    "OptionalSolverPluginManifestPersistenceState",
    "OptionalSolverPluginManifestPersistenceSummaryViewModel",
    "OptionalSolverPluginManifestPersistenceTrustBadgeViewModel",
    "OptionalSolverPluginManifestPersistenceUnsafeClaimInput",
    "OptionalSolverPluginManifestPersistenceUnsafeClaimRowViewModel",
    "OptionalSolverPluginManifestPersistenceViewModel",
    "build_optional_solver_plugin_manifest_persistence_viewmodel",
    "explain_optional_solver_plugin_manifest_persistence_viewmodel",
    "redact_optional_solver_plugin_manifest_persistence_source_reference",
    "render_optional_solver_plugin_manifest_persistence_summary",
    "summarize_optional_solver_plugin_manifest_persistence_viewmodel",
]
