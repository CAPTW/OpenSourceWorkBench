"""Pure reload acceptance persistence planning view-model.

This OSW-EXP-125 module models a future persistence review/write-plan surface
for already-built reload acceptance view-model records. It performs no file IO,
invokes no writer or reader, imports no CLI or GUI code, uses no process bridge,
does not mutate ProjectSchema, and never creates persisted state, runtime
acceptance, validation evidence, activation, trust restoration, or release/issue
claims.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from enum import Enum

RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_VERSION = "osw-exp-125"
RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_ID = (
    "optional_solver_plugin_manifest_reload_acceptance_persistence"
)
RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION = "osw-exp-125-preview"
RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_KIND = (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_state"
)

ACK_ACCEPTANCE_NOT_VALIDATION = "acceptance_not_validation"
ACK_ACCEPTANCE_NOT_VALIDATION_FAILURE = "acceptance_not_validation_failure"
ACK_ACCEPTANCE_NOT_TRUST_RESTORATION = "acceptance_not_trust_restoration"
ACK_ACCEPTANCE_NOT_AUTOMATIC_ACTIVATION = (
    "acceptance_not_automatic_activation"
)
ACK_ACCEPTANCE_NOT_DISCOVERY_SUCCESS = "acceptance_not_discovery_success"
ACK_ACCEPTANCE_NOT_DEPENDENCY_INSTALL = "acceptance_not_dependency_install"
ACK_ACCEPTANCE_NO_SOLVER_EXECUTION = "acceptance_no_solver_execution"
ACK_ACCEPTANCE_NOT_ISSUE_CLOSURE = "acceptance_not_issue_closure"
ACK_ACCEPTANCE_NOT_RELEASE_MUTATION = "acceptance_not_release_mutation"
ACK_ACCEPTANCE_NOT_CERTIFICATION = "acceptance_not_certification"
ACK_ACCEPTANCE_NOT_PERSISTENCE_WRITE = "acceptance_not_persistence_write"
ACK_ACCEPTANCE_NOT_PROJECT_SCHEMA_MUTATION = (
    "acceptance_not_project_schema_mutation"
)
ACK_REDACTION_REVIEWED = "redaction_reviewed"
ACK_UNREDACTED_PATHS_BLOCKED = "unredacted_paths_blocked"
ACK_STALE_SOURCE_REQUIRES_REPREVIEW = "stale_source_requires_repreview"
ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED = "untrusted_source_remains_untrusted"
ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_ACCEPTANCE = (
    "activation_review_required_after_acceptance"
)
ACK_NO_DISCOVERY_EXECUTION = "no_discovery_execution"
ACK_NO_PLUGIN_PACKAGE_IMPORT = "no_plugin_package_import"
ACK_NO_VALIDATION_EXECUTION = "no_validation_execution"
ACK_NO_SOLVER_EXECUTION = "no_solver_execution"
ACK_TRUST_LABEL_NOT_CERTIFICATION = "trust_label_not_certification"
ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE = (
    "persisted_acknowledgements_may_expire"
)

RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS: tuple[str, ...] = (
    ACK_ACCEPTANCE_NOT_VALIDATION,
    ACK_ACCEPTANCE_NOT_VALIDATION_FAILURE,
    ACK_ACCEPTANCE_NOT_TRUST_RESTORATION,
    ACK_ACCEPTANCE_NOT_AUTOMATIC_ACTIVATION,
    ACK_ACCEPTANCE_NOT_DISCOVERY_SUCCESS,
    ACK_ACCEPTANCE_NOT_DEPENDENCY_INSTALL,
    ACK_ACCEPTANCE_NO_SOLVER_EXECUTION,
    ACK_ACCEPTANCE_NOT_ISSUE_CLOSURE,
    ACK_ACCEPTANCE_NOT_RELEASE_MUTATION,
    ACK_ACCEPTANCE_NOT_CERTIFICATION,
    ACK_ACCEPTANCE_NOT_PERSISTENCE_WRITE,
    ACK_ACCEPTANCE_NOT_PROJECT_SCHEMA_MUTATION,
    ACK_REDACTION_REVIEWED,
    ACK_UNREDACTED_PATHS_BLOCKED,
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
    ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_ACCEPTANCE,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_NO_VALIDATION_EXECUTION,
    ACK_NO_SOLVER_EXECUTION,
    ACK_TRUST_LABEL_NOT_CERTIFICATION,
    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
)

RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS: tuple[str, ...] = (
    "reload",
    "source_fingerprint_change",
    "schema_version_change",
    "unsafe_claim_appearance",
    "trust_policy_change",
    "future_discovery_refresh_result",
    "file_reader_policy_change",
    "gui_file_dialog_policy_change",
    "cli_explicit_path_policy_change",
    "acceptance_policy_change",
    "project_schema_policy_change",
    "validation_issue_state_change",
    "persistence_schema_change",
    "persistence_storage_policy_change",
)

OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNAVAILABLE = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNAVAILABLE"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ERROR = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ERROR"
)

OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNAVAILABLE,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ERROR,
)


class ReloadAcceptancePersistenceState(str, Enum):
    """Top-level future persistence state."""

    PERSISTENCE_UNAVAILABLE = "persistence_unavailable"
    NO_ACCEPTANCE_VIEWMODEL = "no_acceptance_viewmodel"
    ACCEPTANCE_NOT_REQUESTED = "acceptance_not_requested"
    PERSISTENCE_NOT_REQUESTED = "persistence_not_requested"
    PERSISTENCE_REQUESTED = "persistence_requested"
    ACKNOWLEDGEMENT_REQUIRED = "acknowledgement_required"
    PERSISTENCE_BLOCKED = "persistence_blocked"
    STALE_SOURCE_REPREVIEW_REQUIRED = "stale_source_repreview_required"
    CONFLICT_REVIEW_REQUIRED = "conflict_review_required"
    UNSAFE_CLAIM_BLOCKED = "unsafe_claim_blocked"
    PERSISTENCE_READY_FUTURE_ONLY = "persistence_ready_future_only"
    PERSISTED_REVIEW_RECORD_FUTURE_ONLY = "persisted_review_record_future_only"
    RUNTIME_ACCEPTANCE_STILL_REQUIRED = "runtime_acceptance_still_required"
    FUTURE_ACTIVATION_REVIEW_REQUIRED = "future_activation_review_required"
    FUTURE_DISCOVERY_REFRESH_REQUIRED = "future_discovery_refresh_required"
    PERSISTENCE_ERROR = "persistence_error"


class ReloadAcceptancePersistenceReadiness(str, Enum):
    """Readiness vocabulary for future persistence planning."""

    UNAVAILABLE = "unavailable"
    ACCEPTANCE_MISSING = "acceptance_missing"
    ACCEPTANCE_NOT_REQUESTED = "acceptance_not_requested"
    PERSISTENCE_NOT_REQUESTED = "persistence_not_requested"
    BLOCKED_ACKNOWLEDGEMENT = "blocked_acknowledgement"
    BLOCKED_STALE_SOURCE_REPREVIEW = "blocked_stale_source_repreview"
    BLOCKED_CONFLICT_REVIEW = "blocked_conflict_review"
    BLOCKED_SHARED_STACK_REVIEW = "blocked_shared_stack_review"
    BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_claim"
    BLOCKED_SCHEMA_UNSUPPORTED = "blocked_schema_unsupported"
    BLOCKED_MIGRATION_REQUIRED = "blocked_migration_required"
    BLOCKED_UNREDACTED_PATH = "blocked_unredacted_path"
    BLOCKED_SECRET_LIKE_VALUE = "blocked_secret_like_value"
    BLOCKED_POLICY_CHANGE = "blocked_policy_change"
    BLOCKED_STORAGE_POLICY = "blocked_storage_policy"
    BLOCKED_DRY_RUN_REQUIRED = "blocked_dry_run_required"
    READY_FUTURE_ONLY = "ready_future_only"
    WRITER_FUTURE_ONLY = "writer_future_only"
    ERROR = "error"


class ReloadAcceptancePersistenceAction(str, Enum):
    """Disabled or future-only persistence and runtime actions."""

    PERSIST_ACCEPTANCE_RECORD = "persist_acceptance_record"
    WRITE_ACCEPTANCE_STATE = "write_acceptance_state"
    ACCEPT_FOR_SESSION_REVIEW = "accept_for_session_review"
    ACCEPT_AS_TRUSTED = "accept_as_trusted"
    ACTIVATE_RELOADED_CANDIDATE = "activate_reloaded_candidate"
    REFRESH_DISCOVERY = "refresh_discovery"
    VALIDATE_SOLVER = "validate_solver"
    EXECUTE_SOLVER = "execute_solver"
    INSTALL_DEPENDENCY = "install_dependency"
    UNINSTALL_DEPENDENCY = "uninstall_dependency"
    UNINSTALL_SOLVER = "uninstall_solver"
    MUTATE_PROJECT_SCHEMA = "mutate_project_schema"
    CREATE_EXPORT_SUMMARY = "create_export_summary"
    CREATE_REPORT_FILE = "create_report_file"
    CREATE_RELOADABLE_BUNDLE = "create_reloadable_bundle"
    COPY_TO_CLIPBOARD = "copy_to_clipboard"
    ATTACH_TO_REPORT = "attach_to_report"
    OPEN_OUTPUT_FOLDER = "open_output_folder"
    CLOSE_ISSUE = "close_issue"
    MUTATE_RELEASE = "mutate_release"
    PUSH_TAG = "push_tag"
    UPLOAD_ASSET = "upload_asset"
    CLAIM_VALIDATION_SUCCESS = "claim_validation_success"
    CLAIM_VALIDATION_FAILURE = "claim_validation_failure"
    CLAIM_CERTIFICATION = "claim_certification"


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceDiagnostic:
    """One future persistence diagnostic row."""

    code: str
    severity: str
    message: str
    section: str = "persistence"
    blocker: bool = False
    context: str = ""
    suggested_fix: str = ""

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceStorageOption:
    """Conceptual storage option; no option writes in this gate."""

    storage_policy_id: str
    label: str
    target_display: str = ""
    explicit_user_selected: bool = False
    raw_path_hidden: bool = True
    default_path_used: bool = False
    background_write_allowed: bool = False
    allowed_in_this_gate: bool = False
    future_only: bool = True

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceSchemaRow:
    """File-format/schema policy row for future persistence."""

    schema_id: str = RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_ID
    schema_version: str = RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION
    payload_kind: str = RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_KIND
    payload_kind_required: bool = True
    schema_version_required: bool = True
    schema_supported: bool = True
    migration_required: bool = False
    migration_executed: bool = False
    schema_mismatch_is_validation_failure: bool = False
    separate_from_project_schema: bool = True
    repairs_or_migrates_files: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceAcknowledgementRow:
    """Persistence acknowledgement row."""

    acknowledgement_id: str
    label: str
    required: bool = True
    satisfied: bool = False
    expired: bool = False
    blocking: bool = True
    acknowledgement_is_validation_evidence: bool = False
    acknowledgement_restores_trust: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceExpiryRow:
    """Acknowledgement expiry reason row."""

    reason_id: str
    label: str
    active: bool = True
    blocks_when_triggered: bool = True

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceBlockerRow:
    """Visible blocker row."""

    blocker_id: str
    diagnostic_code: str
    label: str
    required_action: str
    severity: str = "error"
    blocks_persistence: bool = True

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceProvenanceRow:
    """Redacted, non-authoritative provenance row."""

    provenance_id: str
    source_display: str
    source_kind: str = "supplied_acceptance_viewmodel"
    preview_identifier: str = ""
    payload_fingerprint: str = ""
    raw_reference_hidden: bool = True
    source_reference_redacted: bool = True
    untrusted_by_default: bool = True
    non_authoritative: bool = True
    trust_label_not_certification: bool = True
    limitations: tuple[str, ...] = (
        "Reference-only provenance; not validation evidence.",
    )

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceEvidenceRow:
    """Evidence/history retained as reference only."""

    evidence_id: str
    evidence_type: str = "history"
    retained_reference_only: bool = True
    not_validation_evidence: bool = True
    not_validation_failure: bool = True
    no_evidence_deleted_or_rewritten: bool = True
    issue_closure_implied: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceWritePlan:
    """Dry-run/future-only write-plan record. It writes nothing."""

    storage_policy_id: str
    storage_display_label: str
    target_display: str
    schema_id: str
    schema_version: str
    expected_payload_kind: str
    source_count: int = 0
    acknowledgement_count: int = 0
    provenance_count: int = 0
    evidence_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    diagnostic_count: int = 0
    dry_run_required: bool = True
    writer_future_only: bool = True
    write_performed: bool = False
    persistence_write_performed: bool = False
    runtime_reload_acceptance_performed: bool = False
    project_schema_mutated: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceNonActionFlags:
    """False flags for behavior this model never performs."""

    runtime_reload_acceptance_performed: bool = False
    persistence_write_performed: bool = False
    project_schema_mutated: bool = False
    default_reload_path_used: bool = False
    background_reload_performed: bool = False
    directory_scan_performed: bool = False
    network_fetch_performed: bool = False
    plugin_package_imported: bool = False
    cli_subprocess_used: bool = False
    gui_subprocess_used: bool = False
    reloadable_bundle_created: bool = False
    export_file_created: bool = False
    report_file_created: bool = False
    clipboard_used: bool = False
    report_attached: bool = False
    output_folder_opened: bool = False
    live_discovery_executed: bool = False
    passive_refresh_executed: bool = False
    validation_executed: bool = False
    solver_executed: bool = False
    dependency_installed: bool = False
    dependency_uninstalled: bool = False
    solver_uninstalled: bool = False
    candidate_activated: bool = False
    trust_restored: bool = False
    issue_mutated: bool = False
    release_mutated: bool = False
    tag_mutated: bool = False
    asset_mutated: bool = False
    version_bumped: bool = False
    validation_pass_claimed: bool = False
    validation_fail_claimed: bool = False
    issue_closure_claimed: bool = False
    bundled_solver_claimed: bool = False
    certification_claimed: bool = False

    def to_mapping(self) -> dict[str, bool]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceActionRow:
    """Disabled/future-only action row."""

    action: ReloadAcceptancePersistenceAction
    enabled: bool = False
    future_only: bool = True
    reason: str = "Requires a separate future gate."

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceSummary:
    """Top-level persistence planning summary."""

    state: ReloadAcceptancePersistenceState
    readiness: ReloadAcceptancePersistenceReadiness
    persistence_requested: bool = False
    acceptance_available: bool = False
    acceptance_requested: bool = False
    accepted_for_session_review: bool = False
    future_writer_only: bool = True
    ready_for_future_write_plan: bool = False
    storage_policy_id: str = ""
    accepted_state_scope: str = "session_review_only"
    untrusted_by_default: bool = True
    acknowledgement_count: int = 0
    missing_acknowledgement_count: int = 0
    expired_acknowledgement_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    diagnostic_count: int = 0
    persistence_readiness_is_validation_evidence: bool = False
    persistence_readiness_is_validation_failure: bool = False
    persistence_readiness_restores_trust: bool = False
    persistence_readiness_activates_candidate: bool = False
    persistence_readiness_mutates_project_schema: bool = False
    persistence_readiness_is_runtime_acceptance: bool = False
    persistence_readiness_closes_issue: bool = False
    persistence_readiness_mutates_release: bool = False
    persistence_readiness_certifies_manifest: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
    """Pure in-memory future persistence planning view-model."""

    summary: ReloadAcceptancePersistenceSummary
    storage_options: tuple[ReloadAcceptancePersistenceStorageOption, ...]
    schema_rows: tuple[ReloadAcceptancePersistenceSchemaRow, ...]
    write_plan: ReloadAcceptancePersistenceWritePlan
    acknowledgement_rows: tuple[ReloadAcceptancePersistenceAcknowledgementRow, ...] = ()
    expiry_rows: tuple[ReloadAcceptancePersistenceExpiryRow, ...] = ()
    blocker_rows: tuple[ReloadAcceptancePersistenceBlockerRow, ...] = ()
    diagnostics: tuple[ReloadAcceptancePersistenceDiagnostic, ...] = ()
    provenance_rows: tuple[ReloadAcceptancePersistenceProvenanceRow, ...] = ()
    evidence_history_rows: tuple[ReloadAcceptancePersistenceEvidenceRow, ...] = ()
    non_action_flags: ReloadAcceptancePersistenceNonActionFlags = (
        ReloadAcceptancePersistenceNonActionFlags()
    )
    action_rows: tuple[ReloadAcceptancePersistenceActionRow, ...] = ()
    safety_text: tuple[str, ...] = ()

    @classmethod
    def unavailable(
        cls,
        reason: str = "Persistence view-model is unavailable.",
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
        """Return a deterministic unavailable state."""

        return build_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel(
            acceptance_mapping=None,
            persistence_requested=False,
            policy_flags={"unavailable_reason": reason},
        )

    @classmethod
    def from_acceptance_viewmodel(
        cls,
        acceptance_viewmodel: object,
        *,
        persistence_requested: bool = False,
        acknowledged: Sequence[str] = (),
        expired_acknowledgements: Sequence[str] = (),
        storage_policy_id: str = "",
        storage_label: str = "",
        target_display: str = "",
        dry_run_confirmed: bool = False,
        policy_flags: Mapping[str, object] | None = None,
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
        """Build from an already-built acceptance view-model object."""

        return cls.from_acceptance_mapping(
            _object_to_mapping(acceptance_viewmodel),
            persistence_requested=persistence_requested,
            acknowledged=acknowledged,
            expired_acknowledgements=expired_acknowledgements,
            storage_policy_id=storage_policy_id,
            storage_label=storage_label,
            target_display=target_display,
            dry_run_confirmed=dry_run_confirmed,
            policy_flags=policy_flags,
        )

    @classmethod
    def from_acceptance_mapping(
        cls,
        mapping: Mapping[str, object] | None,
        *,
        persistence_requested: bool = False,
        acknowledged: Sequence[str] = (),
        expired_acknowledgements: Sequence[str] = (),
        storage_policy_id: str = "",
        storage_label: str = "",
        target_display: str = "",
        dry_run_confirmed: bool = False,
        policy_flags: Mapping[str, object] | None = None,
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
        """Build from a safe, already-built in-memory acceptance mapping."""

        return build_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel(
            acceptance_mapping=mapping,
            persistence_requested=persistence_requested,
            acknowledged=acknowledged,
            expired_acknowledgements=expired_acknowledgements,
            storage_policy_id=storage_policy_id,
            storage_label=storage_label,
            target_display=target_display,
            dry_run_confirmed=dry_run_confirmed,
            policy_flags=policy_flags,
        )

    @classmethod
    def build(
        cls,
        *,
        acceptance_mapping: Mapping[str, object] | None = None,
        persistence_requested: bool = False,
        acknowledged: Sequence[str] = (),
        expired_acknowledgements: Sequence[str] = (),
        storage_policy_id: str = "",
        storage_label: str = "",
        target_display: str = "",
        dry_run_confirmed: bool = False,
        policy_flags: Mapping[str, object] | None = None,
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
        """Build synthetic deterministic records for tests and future callers."""

        return build_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel(
            acceptance_mapping=acceptance_mapping,
            persistence_requested=persistence_requested,
            acknowledged=acknowledged,
            expired_acknowledgements=expired_acknowledgements,
            storage_policy_id=storage_policy_id,
            storage_label=storage_label,
            target_display=target_display,
            dry_run_confirmed=dry_run_confirmed,
            policy_flags=policy_flags,
        )

    @classmethod
    def ready_for_future_writer(
        cls,
        acceptance_viewmodel: object,
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
        """Return a ready/future-writer-only plan from supplied acceptance state."""

        return cls.from_acceptance_viewmodel(
            acceptance_viewmodel,
            persistence_requested=True,
            acknowledged=RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS,
            storage_policy_id="explicit_user_selected_path",
            storage_label="Explicit user-selected local state path",
            target_display="reload-acceptance-state.json",
            dry_run_confirmed=True,
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""

        return {
            "summary": self.summary.to_mapping(),
            "storage_options": [
                row.to_mapping() for row in self.storage_options
            ],
            "schema": [row.to_mapping() for row in self.schema_rows],
            "write_plan": self.write_plan.to_mapping(),
            "acknowledgements": [
                row.to_mapping() for row in self.acknowledgement_rows
            ],
            "acknowledgement_expiry": [
                row.to_mapping() for row in self.expiry_rows
            ],
            "blockers": [row.to_mapping() for row in self.blocker_rows],
            "diagnostics": [row.to_mapping() for row in self.diagnostics],
            "provenance": [row.to_mapping() for row in self.provenance_rows],
            "evidence_history": [
                row.to_mapping() for row in self.evidence_history_rows
            ],
            "non_action_flags": self.non_action_flags.to_mapping(),
            "actions": [row.to_mapping() for row in self.action_rows],
            "safety_text": list(self.safety_text),
            "reserved_diagnostic_codes": list(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DIAGNOSTIC_CODES
            ),
            "required_acknowledgements": list(
                RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS
            ),
            "expiry_reasons": list(
                RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS
            ),
            "view_model_version": RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_VERSION,
        }

    def to_text_lines(self) -> tuple[str, ...]:
        """Render stable plain-text review lines."""

        lines = [
            "Optional Solver Plugin Manifest Reload Acceptance Persistence View-Model",
            f"state: {self.summary.state.value}",
            f"readiness: {self.summary.readiness.value}",
            f"persistence_requested: {self.summary.persistence_requested}",
            f"acceptance_available: {self.summary.acceptance_available}",
            f"accepted_for_session_review: {self.summary.accepted_for_session_review}",
            (
                "write-plan: dry_run_required=True writer_future_only=True "
                "write_performed=False persistence_write_performed=False"
            ),
            (
                "safety: persistence readiness is not runtime reload acceptance, "
                "not validation evidence, and not validation failure"
            ),
            (
                "safety: persistence readiness does not restore trust, activate "
                "candidates, run discovery, run validation, or execute solvers"
            ),
            (
                "safety: persistence readiness does not mutate ProjectSchema, "
                "close issues, mutate releases, write files, or certify manifests"
            ),
            (
                "schema: mismatch is not validation failure and persistence "
                "schema remains separate from ProjectSchema"
            ),
            (
                "candidate lifecycle: no automatic activation and no trust "
                "restoration"
            ),
            (
                "evidence/history: reference-only and not validation evidence"
            ),
        ]
        for blocker in self.blocker_rows:
            lines.append(f"blocker: {blocker.diagnostic_code} {blocker.label}")
        for row in self.acknowledgement_rows:
            lines.append(
                "acknowledgement: "
                f"{row.acknowledgement_id} satisfied={row.satisfied} "
                f"expired={row.expired}"
            )
        for row in self.expiry_rows:
            lines.append(f"expiry: {row.reason_id} active={row.active}")
        for diagnostic in self.diagnostics:
            lines.append(f"diagnostic: {diagnostic.severity} {diagnostic.code}")
        for action in self.action_rows:
            lines.append(f"action: {action.action.value} enabled={action.enabled}")
        return tuple(lines)


def unavailable(
    reason: str = "Persistence view-model is unavailable.",
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
    """Return an unavailable persistence view-model."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.unavailable(
        reason
    )


def from_acceptance_viewmodel(
    acceptance_viewmodel: object,
    *,
    persistence_requested: bool = False,
    acknowledged: Sequence[str] = (),
    expired_acknowledgements: Sequence[str] = (),
    storage_policy_id: str = "",
    storage_label: str = "",
    target_display: str = "",
    dry_run_confirmed: bool = False,
    policy_flags: Mapping[str, object] | None = None,
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
    """Build future persistence readiness from supplied acceptance records."""

    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.from_acceptance_viewmodel(
            acceptance_viewmodel,
            persistence_requested=persistence_requested,
            acknowledged=acknowledged,
            expired_acknowledgements=expired_acknowledgements,
            storage_policy_id=storage_policy_id,
            storage_label=storage_label,
            target_display=target_display,
            dry_run_confirmed=dry_run_confirmed,
            policy_flags=policy_flags,
        )
    )


def from_acceptance_mapping(
    mapping: Mapping[str, object] | None,
    *,
    persistence_requested: bool = False,
    acknowledged: Sequence[str] = (),
    expired_acknowledgements: Sequence[str] = (),
    storage_policy_id: str = "",
    storage_label: str = "",
    target_display: str = "",
    dry_run_confirmed: bool = False,
    policy_flags: Mapping[str, object] | None = None,
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
    """Build future persistence readiness from a safe mapping."""

    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel.from_acceptance_mapping(
            mapping,
            persistence_requested=persistence_requested,
            acknowledged=acknowledged,
            expired_acknowledgements=expired_acknowledgements,
            storage_policy_id=storage_policy_id,
            storage_label=storage_label,
            target_display=target_display,
            dry_run_confirmed=dry_run_confirmed,
            policy_flags=policy_flags,
        )
    )


def build_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel(
    *,
    acceptance_mapping: Mapping[str, object] | None = None,
    persistence_requested: bool = False,
    acknowledged: Sequence[str] = (),
    expired_acknowledgements: Sequence[str] = (),
    storage_policy_id: str = "",
    storage_label: str = "",
    target_display: str = "",
    dry_run_confirmed: bool = False,
    policy_flags: Mapping[str, object] | None = None,
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel:
    """Build the pure future persistence view-model from supplied data only."""

    flags = _mapping(policy_flags)
    acceptance = _mapping(acceptance_mapping)
    acknowledged_set = {str(item) for item in acknowledged}
    expired_set = {str(item) for item in expired_acknowledgements}
    storage_policy = str(storage_policy_id or "").strip()
    safe_target = _safe_display(target_display)
    safe_storage_label = (
        str(storage_label or "").strip() or "Explicit future storage policy"
    )

    acknowledgement_rows = _acknowledgement_rows(acknowledged_set, expired_set)
    expiry_rows = _expiry_rows()
    provenance_rows = _provenance_rows(acceptance, flags)
    evidence_rows = _evidence_rows(acceptance)
    storage_options = (
        ReloadAcceptancePersistenceStorageOption(
            storage_policy_id=storage_policy or "missing_storage_policy",
            label=safe_storage_label,
            target_display=safe_target,
            explicit_user_selected=bool(storage_policy and safe_target),
        ),
    )
    schema_rows = (
        ReloadAcceptancePersistenceSchemaRow(
            schema_supported=not _flag(flags, "unsupported_schema"),
            migration_required=_flag(flags, "migration_required"),
        ),
    )
    diagnostics = _diagnostics(
        acceptance,
        flags,
        persistence_requested=persistence_requested,
        acknowledged_set=acknowledged_set,
        expired_set=expired_set,
        storage_policy_id=storage_policy,
        dry_run_confirmed=dry_run_confirmed,
    )
    blocker_rows = tuple(
        _blocker_row(row) for row in diagnostics if row.blocker
    )
    readiness = _readiness(diagnostics, persistence_requested=persistence_requested)
    state = _state(readiness, persistence_requested=persistence_requested)
    write_plan = ReloadAcceptancePersistenceWritePlan(
        storage_policy_id=storage_policy or "missing_storage_policy",
        storage_display_label=safe_storage_label,
        target_display=safe_target,
        schema_id=RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_ID,
        schema_version=RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION,
        expected_payload_kind=RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_KIND,
        source_count=len(provenance_rows),
        acknowledgement_count=len(acknowledgement_rows),
        provenance_count=len(provenance_rows),
        evidence_count=len(evidence_rows),
        blocker_count=len(blocker_rows),
        warning_count=sum(1 for row in diagnostics if row.severity == "warning"),
        diagnostic_count=len(diagnostics),
    )
    accepted_summary = _mapping(acceptance.get("summary", {}))
    summary = ReloadAcceptancePersistenceSummary(
        state=state,
        readiness=readiness,
        persistence_requested=persistence_requested,
        acceptance_available=bool(acceptance),
        acceptance_requested=bool(accepted_summary.get("requested", False)),
        accepted_for_session_review=bool(
            accepted_summary.get("accepted_for_session_review", False)
        ),
        ready_for_future_write_plan=readiness
        in {
            ReloadAcceptancePersistenceReadiness.READY_FUTURE_ONLY,
            ReloadAcceptancePersistenceReadiness.WRITER_FUTURE_ONLY,
        },
        storage_policy_id=storage_policy,
        acknowledgement_count=len(acknowledgement_rows),
        missing_acknowledgement_count=sum(
            1 for row in acknowledgement_rows if row.required and not row.satisfied
        ),
        expired_acknowledgement_count=sum(1 for row in acknowledgement_rows if row.expired),
        blocker_count=len(blocker_rows),
        warning_count=sum(1 for row in diagnostics if row.severity == "warning"),
        diagnostic_count=len(diagnostics),
    )
    return OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel(
        summary=summary,
        storage_options=storage_options,
        schema_rows=schema_rows,
        write_plan=write_plan,
        acknowledgement_rows=acknowledgement_rows,
        expiry_rows=expiry_rows,
        blocker_rows=blocker_rows,
        diagnostics=diagnostics,
        provenance_rows=provenance_rows,
        evidence_history_rows=evidence_rows,
        action_rows=_action_rows(),
        safety_text=_safety_text(),
    )


def render_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel(
    view_model: OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel,
) -> tuple[str, ...]:
    """Render stable text lines."""

    return view_model.to_text_lines()


def all_reload_acceptance_persistence_acknowledgements() -> tuple[str, ...]:
    """Return the deterministic required acknowledgement ids."""

    return RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS


def _diagnostics(
    acceptance: Mapping[str, object],
    flags: Mapping[str, object],
    *,
    persistence_requested: bool,
    acknowledged_set: set[str],
    expired_set: set[str],
    storage_policy_id: str,
    dry_run_confirmed: bool,
) -> tuple[ReloadAcceptancePersistenceDiagnostic, ...]:
    rows: list[ReloadAcceptancePersistenceDiagnostic] = []

    def add(
        code: str,
        *,
        severity: str = "warning",
        blocker: bool = False,
        section: str = "persistence",
        context: str = "",
    ) -> None:
        if any(row.code == code for row in rows):
            return
        rows.append(
            ReloadAcceptancePersistenceDiagnostic(
                code=code,
                severity=severity,
                message=_diagnostic_message(code, flags),
                section=section,
                blocker=blocker,
                context=_safe_display(context),
                suggested_fix=_suggested_fix(code),
            )
        )

    if _flag(flags, "error"):
        add(
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ERROR,
            severity="error",
            blocker=True,
        )
    if not acceptance:
        add(
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING,
            severity="error",
            blocker=True,
        )
        add(OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNAVAILABLE)
    if acceptance and not _acceptance_requested(acceptance):
        add(
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED,
            section="acceptance",
        )
    if not persistence_requested:
        add(OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED)
        return tuple(rows)

    missing_ack = set(RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS) - acknowledged_set
    if missing_ack or expired_set:
        add(
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED,
            severity="error",
            blocker=True,
            section="acknowledgements",
        )
    for flag, code in (
        (
            "stale_source_requires_repreview",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED,
        ),
        (
            "conflict_review_required",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED,
        ),
        (
            "shared_stack_review_required",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED,
        ),
        (
            "unsafe_claim_blocked",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED,
        ),
        (
            "unsupported_schema",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED,
        ),
        (
            "migration_required",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED,
        ),
        (
            "unredacted_path_blocked",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED,
        ),
        (
            "secret_like_value_blocked",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED,
        ),
        (
            "trust_policy_changed",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED,
        ),
        (
            "source_fingerprint_changed",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED,
        ),
        ("policy_changed", OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED),
        (
            "acceptance_policy_changed",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED,
        ),
        (
            "persistence_schema_changed",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED,
        ),
        (
            "persistence_storage_policy_changed",
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED,
        ),
    ):
        if _flag(flags, flag):
            add(code, severity="error", blocker=True)

    for code in _acceptance_diagnostic_codes(acceptance):
        mapped = _map_acceptance_diagnostic(code)
        if mapped:
            add(mapped, severity="error", blocker=True)

    if not storage_policy_id:
        add(
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED,
            severity="error",
            blocker=True,
            section="storage",
        )
    if not dry_run_confirmed:
        add(
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED,
            severity="error",
            blocker=True,
            section="write_plan",
        )
    if not any(row.blocker for row in rows):
        add(OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY, severity="info")
    add(
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY,
        severity="info",
        section="write_plan",
    )
    return tuple(rows)


def _readiness(
    diagnostics: Sequence[ReloadAcceptancePersistenceDiagnostic],
    *,
    persistence_requested: bool,
) -> ReloadAcceptancePersistenceReadiness:
    codes = {row.code for row in diagnostics}
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ERROR in codes:
        return ReloadAcceptancePersistenceReadiness.ERROR
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING in codes:
        return ReloadAcceptancePersistenceReadiness.ACCEPTANCE_MISSING
    if not persistence_requested:
        return ReloadAcceptancePersistenceReadiness.PERSISTENCE_NOT_REQUESTED
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_SCHEMA_UNSUPPORTED
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_MIGRATION_REQUIRED
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_UNREDACTED_PATH
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_SECRET_LIKE_VALUE
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_UNSAFE_CLAIM
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_STALE_SOURCE_REPREVIEW
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_CONFLICT_REVIEW
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_SHARED_STACK_REVIEW
    if {
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED,
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED,
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED,
    } & codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_POLICY_CHANGE
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_ACKNOWLEDGEMENT
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_STORAGE_POLICY
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED in codes:
        return ReloadAcceptancePersistenceReadiness.BLOCKED_DRY_RUN_REQUIRED
    if OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY in codes:
        return ReloadAcceptancePersistenceReadiness.WRITER_FUTURE_ONLY
    return ReloadAcceptancePersistenceReadiness.READY_FUTURE_ONLY


def _state(
    readiness: ReloadAcceptancePersistenceReadiness,
    *,
    persistence_requested: bool,
) -> ReloadAcceptancePersistenceState:
    if readiness == ReloadAcceptancePersistenceReadiness.ERROR:
        return ReloadAcceptancePersistenceState.PERSISTENCE_ERROR
    if readiness == ReloadAcceptancePersistenceReadiness.ACCEPTANCE_MISSING:
        return ReloadAcceptancePersistenceState.NO_ACCEPTANCE_VIEWMODEL
    if readiness == ReloadAcceptancePersistenceReadiness.PERSISTENCE_NOT_REQUESTED:
        return ReloadAcceptancePersistenceState.PERSISTENCE_NOT_REQUESTED
    if readiness == ReloadAcceptancePersistenceReadiness.BLOCKED_ACKNOWLEDGEMENT:
        return ReloadAcceptancePersistenceState.ACKNOWLEDGEMENT_REQUIRED
    if readiness == ReloadAcceptancePersistenceReadiness.BLOCKED_STALE_SOURCE_REPREVIEW:
        return ReloadAcceptancePersistenceState.STALE_SOURCE_REPREVIEW_REQUIRED
    if readiness in {
        ReloadAcceptancePersistenceReadiness.BLOCKED_CONFLICT_REVIEW,
        ReloadAcceptancePersistenceReadiness.BLOCKED_SHARED_STACK_REVIEW,
    }:
        return ReloadAcceptancePersistenceState.CONFLICT_REVIEW_REQUIRED
    if readiness == ReloadAcceptancePersistenceReadiness.BLOCKED_UNSAFE_CLAIM:
        return ReloadAcceptancePersistenceState.UNSAFE_CLAIM_BLOCKED
    if readiness in {
        ReloadAcceptancePersistenceReadiness.READY_FUTURE_ONLY,
        ReloadAcceptancePersistenceReadiness.WRITER_FUTURE_ONLY,
    }:
        return ReloadAcceptancePersistenceState.PERSISTENCE_READY_FUTURE_ONLY
    if not persistence_requested:
        return ReloadAcceptancePersistenceState.ACCEPTANCE_NOT_REQUESTED
    return ReloadAcceptancePersistenceState.PERSISTENCE_BLOCKED


def _acknowledgement_rows(
    acknowledged: set[str],
    expired: set[str],
) -> tuple[ReloadAcceptancePersistenceAcknowledgementRow, ...]:
    return tuple(
        ReloadAcceptancePersistenceAcknowledgementRow(
            acknowledgement_id=ack,
            label=ack.replace("_", " "),
            satisfied=ack in acknowledged,
            expired=ack in expired,
            blocking=ack not in acknowledged or ack in expired,
        )
        for ack in RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS
    )


def _expiry_rows() -> tuple[ReloadAcceptancePersistenceExpiryRow, ...]:
    return tuple(
        ReloadAcceptancePersistenceExpiryRow(
            reason_id=reason,
            label=reason.replace("_", " "),
        )
        for reason in RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS
    )


def _provenance_rows(
    acceptance: Mapping[str, object],
    flags: Mapping[str, object],
) -> tuple[ReloadAcceptancePersistenceProvenanceRow, ...]:
    rows = []
    for index, row in enumerate(
        _iter_mappings(acceptance.get("source_provenance")), start=1
    ):
        source_display = _safe_display(
            row.get("source_display") or row.get("source_reference_display")
        )
        rows.append(
            ReloadAcceptancePersistenceProvenanceRow(
                provenance_id=str(row.get("source_id", f"source-{index}")),
                source_display=source_display or f"source-{index}",
                source_kind=str(row.get("source_kind", "supplied_acceptance_viewmodel")),
                preview_identifier=_safe_display(
                    row.get("preview_identifier", flags.get("preview_identifier", ""))
                ),
                payload_fingerprint=_safe_fingerprint(
                    row.get("payload_fingerprint", flags.get("payload_fingerprint", ""))
                ),
            )
        )
    if not rows and acceptance:
        rows.append(
            ReloadAcceptancePersistenceProvenanceRow(
                provenance_id="acceptance-viewmodel",
                source_display="supplied-acceptance-viewmodel",
            )
        )
    return tuple(rows)


def _evidence_rows(
    acceptance: Mapping[str, object],
) -> tuple[ReloadAcceptancePersistenceEvidenceRow, ...]:
    rows = []
    for index, row in enumerate(
        _iter_mappings(acceptance.get("evidence_history")), start=1
    ):
        rows.append(
            ReloadAcceptancePersistenceEvidenceRow(
                evidence_id=str(row.get("evidence_id", f"evidence-{index}")),
                evidence_type=str(row.get("evidence_type", "history")),
            )
        )
    if acceptance and not rows:
        rows.append(ReloadAcceptancePersistenceEvidenceRow(evidence_id="history"))
    return tuple(rows)


def _blocker_row(
    diagnostic: ReloadAcceptancePersistenceDiagnostic,
) -> ReloadAcceptancePersistenceBlockerRow:
    return ReloadAcceptancePersistenceBlockerRow(
        blocker_id=diagnostic.code.lower().replace(
            "ospmg_reload_acceptance_persistence_", ""
        ),
        diagnostic_code=diagnostic.code,
        label=diagnostic.message,
        required_action=diagnostic.suggested_fix,
        severity=diagnostic.severity,
    )


def _action_rows() -> tuple[ReloadAcceptancePersistenceActionRow, ...]:
    return tuple(
        ReloadAcceptancePersistenceActionRow(
            action=action,
            reason=_action_reason(action),
        )
        for action in ReloadAcceptancePersistenceAction
    )


def _diagnostic_message(code: str, flags: Mapping[str, object]) -> str:
    unavailable_reason = str(flags.get("unavailable_reason", "") or "")
    return {
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED: (
            "Persistence was not requested; acceptance review remains in memory."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNAVAILABLE: (
            unavailable_reason or "Persistence planning is unavailable."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING: (
            "No supplied acceptance view-model is available for persistence planning."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED: (
            "Required persistence acknowledgements are missing or expired."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED: (
            "Stale source state requires re-preview before future persistence."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED: (
            "Conflict review is required; built-ins remain authoritative."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED: (
            "Shared-stack warnings require future policy review."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED: (
            "Unsafe validation, issue, release, trust, install, solver, "
            "or certification claims are blocked."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED: (
            "Unsupported persistence schema blocks future writing."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED: (
            "Persistence schema migration is required and remains future-gated."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED: (
            "Unredacted path disclosure blocks persistence planning."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED: (
            "Secret-like values are blocked and must not be persisted."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED: (
            "Trust policy changed; acknowledgements expire."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED: (
            "Source fingerprint changed; re-preview is required."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED: (
            "Acceptance or persistence policy changed; acknowledgements expire."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED: (
            "An explicit future storage policy is required."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED: (
            "A dry-run write plan is required before any future writer gate."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY: (
            "Persistence planning is ready for a future writer gate only."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY: (
            "Writer behavior is disabled and future-only; no write was performed."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ERROR: (
            "Persistence planning entered an error state without side effects."
        ),
    }[code]


def _suggested_fix(code: str) -> str:
    return {
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING: (
            "Supply an already-built reload acceptance view-model."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED: (
            "Review and satisfy required persistence acknowledgements."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED: (
            "Re-preview the source in a future gate."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED: (
            "Resolve or explicitly review conflicts in a future gate."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED: (
            "Review shared-stack warnings in a future gate."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED: (
            "Remove unsafe claims before future persistence."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED: (
            "Use a supported persistence schema."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED: (
            "Run a separate future migration gate."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED: (
            "Use redacted references only."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED: (
            "Remove secret-like values."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED: (
            "Repeat trust policy review."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED: (
            "Repeat preview/review from supplied state."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED: (
            "Repeat acknowledgement review."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED: (
            "Choose an explicit storage policy in a future gate."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED: (
            "Review a dry-run write plan before future writing."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ERROR: (
            "Inspect supplied in-memory records."
        ),
    }.get(code, "Review in a future gate.")


def _action_reason(action: ReloadAcceptancePersistenceAction) -> str:
    return {
        ReloadAcceptancePersistenceAction.PERSIST_ACCEPTANCE_RECORD: (
            "Persisting acceptance records requires OSW-EXP-126 or later."
        ),
        ReloadAcceptancePersistenceAction.WRITE_ACCEPTANCE_STATE: (
            "Writing acceptance state requires a future writer gate."
        ),
        ReloadAcceptancePersistenceAction.ACCEPT_FOR_SESSION_REVIEW: (
            "Runtime/session acceptance mutation is not performed here."
        ),
        ReloadAcceptancePersistenceAction.ACCEPT_AS_TRUSTED: (
            "Persistence is not trust restoration."
        ),
        ReloadAcceptancePersistenceAction.ACTIVATE_RELOADED_CANDIDATE: (
            "Activation requires future activation review."
        ),
        ReloadAcceptancePersistenceAction.REFRESH_DISCOVERY: (
            "Discovery refresh is separate future behavior."
        ),
        ReloadAcceptancePersistenceAction.VALIDATE_SOLVER: (
            "Validation execution is out of scope."
        ),
        ReloadAcceptancePersistenceAction.EXECUTE_SOLVER: (
            "Solver execution is out of scope."
        ),
        ReloadAcceptancePersistenceAction.INSTALL_DEPENDENCY: (
            "Dependency installation is out of scope."
        ),
        ReloadAcceptancePersistenceAction.UNINSTALL_DEPENDENCY: (
            "Dependency uninstall is out of scope."
        ),
        ReloadAcceptancePersistenceAction.UNINSTALL_SOLVER: (
            "Solver uninstall is out of scope."
        ),
        ReloadAcceptancePersistenceAction.MUTATE_PROJECT_SCHEMA: (
            "ProjectSchema mutation is out of scope."
        ),
        ReloadAcceptancePersistenceAction.CREATE_EXPORT_SUMMARY: (
            "Export summary creation is future-gated."
        ),
        ReloadAcceptancePersistenceAction.CREATE_REPORT_FILE: (
            "Report file creation is future-gated."
        ),
        ReloadAcceptancePersistenceAction.CREATE_RELOADABLE_BUNDLE: (
            "Reloadable bundle creation is future-gated."
        ),
        ReloadAcceptancePersistenceAction.COPY_TO_CLIPBOARD: (
            "Clipboard behavior is out of scope."
        ),
        ReloadAcceptancePersistenceAction.ATTACH_TO_REPORT: (
            "Report attachment is out of scope."
        ),
        ReloadAcceptancePersistenceAction.OPEN_OUTPUT_FOLDER: (
            "Open-output-folder behavior is out of scope."
        ),
        ReloadAcceptancePersistenceAction.CLOSE_ISSUE: (
            "Issue closure requires a separate issue gate."
        ),
        ReloadAcceptancePersistenceAction.MUTATE_RELEASE: (
            "Release mutation requires a release gate."
        ),
        ReloadAcceptancePersistenceAction.PUSH_TAG: (
            "Tag mutation requires a release/tag gate."
        ),
        ReloadAcceptancePersistenceAction.UPLOAD_ASSET: (
            "Asset upload requires a release asset gate."
        ),
        ReloadAcceptancePersistenceAction.CLAIM_VALIDATION_SUCCESS: (
            "Persistence never claims validation success."
        ),
        ReloadAcceptancePersistenceAction.CLAIM_VALIDATION_FAILURE: (
            "Persistence never claims validation failure."
        ),
        ReloadAcceptancePersistenceAction.CLAIM_CERTIFICATION: (
            "Trust labels are not certification."
        ),
    }[action]


def _safety_text() -> tuple[str, ...]:
    return (
        "Persistence readiness is not runtime reload acceptance.",
        "Persistence readiness is not a file write.",
        "Persistence readiness is not validation evidence.",
        "Persistence readiness is not validation failure.",
        "Persistence readiness is not trust restoration.",
        "Persistence readiness is not automatic activation.",
        "Persistence readiness is not discovery success.",
        "Persistence readiness is not dependency installation.",
        "Persistence readiness is not solver execution.",
        "Persistence readiness is not ProjectSchema mutation.",
        "Persistence readiness is not issue closure.",
        "Persistence readiness is not release mutation.",
        "Persistence readiness is not certification.",
        "Persisted acceptance records must remain untrusted by default.",
        "Skipped-missing remains skipped-missing.",
        "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
        "bounded, issue-specific evidence.",
    )


def _acceptance_requested(acceptance: Mapping[str, object]) -> bool:
    return bool(_mapping(acceptance.get("summary", {})).get("requested", False))


def _acceptance_diagnostic_codes(acceptance: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(
        str(row.get("code", ""))
        for row in _iter_mappings(acceptance.get("diagnostics"))
        if str(row.get("code", ""))
    )


def _map_acceptance_diagnostic(code: str) -> str:
    lowered = code.lower()
    if any(
        marker in lowered
        for marker in (
            "preview_missing",
            "reader_blocked",
            "viewmodel_blocked",
        )
    ):
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING
    if "acknowledgement_required" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED
    if "stale" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED
    if "shared_stack" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED
    if "conflict" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED
    if "unsafe" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED
    if "schema_unsupported" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED
    if "migration" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED
    if "unredacted_path" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED
    if "secret" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED
    if "trust_policy" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED
    if "fingerprint" in lowered:
        return OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED
    return ""


def _object_to_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            return mapped
    return {}


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _iter_mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(item for item in value if isinstance(item, Mapping))
    return ()


def _safe_display(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if _secret_like(text):
        return "<redacted-secret-like-value>"
    normalized = text.replace("\\", "/")
    if "/" in normalized:
        return normalized.rsplit("/", 1)[-1] or "redacted-reference"
    return text


def _safe_fingerprint(value: object) -> str:
    text = str(value or "").strip()
    if not text or _secret_like(text):
        return ""
    return _safe_display(text)


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


def _flag(flags: Mapping[str, object], key: str) -> bool:
    return bool(flags.get(key, False))


def _record_to_mapping(record: object) -> dict[str, object]:
    return {
        field.name: _value_to_mapping(getattr(record, field.name))
        for field in fields(record)
    }


def _value_to_mapping(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return _record_to_mapping(value)
    if isinstance(value, tuple):
        return [_value_to_mapping(item) for item in value]
    return value


__all__ = [
    "ACK_ACCEPTANCE_NO_SOLVER_EXECUTION",
    "ACK_ACCEPTANCE_NOT_AUTOMATIC_ACTIVATION",
    "ACK_ACCEPTANCE_NOT_CERTIFICATION",
    "ACK_ACCEPTANCE_NOT_DEPENDENCY_INSTALL",
    "ACK_ACCEPTANCE_NOT_DISCOVERY_SUCCESS",
    "ACK_ACCEPTANCE_NOT_ISSUE_CLOSURE",
    "ACK_ACCEPTANCE_NOT_PERSISTENCE_WRITE",
    "ACK_ACCEPTANCE_NOT_PROJECT_SCHEMA_MUTATION",
    "ACK_ACCEPTANCE_NOT_RELEASE_MUTATION",
    "ACK_ACCEPTANCE_NOT_TRUST_RESTORATION",
    "ACK_ACCEPTANCE_NOT_VALIDATION",
    "ACK_ACCEPTANCE_NOT_VALIDATION_FAILURE",
    "ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_ACCEPTANCE",
    "ACK_NO_DISCOVERY_EXECUTION",
    "ACK_NO_PLUGIN_PACKAGE_IMPORT",
    "ACK_NO_SOLVER_EXECUTION",
    "ACK_NO_VALIDATION_EXECUTION",
    "ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE",
    "ACK_REDACTION_REVIEWED",
    "ACK_STALE_SOURCE_REQUIRES_REPREVIEW",
    "ACK_TRUST_LABEL_NOT_CERTIFICATION",
    "ACK_UNREDACTED_PATHS_BLOCKED",
    "ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACCEPTANCE_MISSING",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ACKNOWLEDGEMENT_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CONFLICT_REVIEW_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DIAGNOSTIC_CODES",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_DRY_RUN_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_ERROR",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_MIGRATION_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_POLICY_CHANGED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_UNSUPPORTED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SECRET_LIKE_VALUE_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SHARED_STACK_REVIEW_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SOURCE_FINGERPRINT_CHANGED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_STORAGE_POLICY_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_TRUST_POLICY_CHANGED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNAVAILABLE",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNREDACTED_PATH_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_UNSAFE_CLAIM_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY",
    "RELOAD_ACCEPTANCE_PERSISTENCE_EXPIRY_REASONS",
    "RELOAD_ACCEPTANCE_PERSISTENCE_PAYLOAD_KIND",
    "RELOAD_ACCEPTANCE_PERSISTENCE_REQUIRED_ACKS",
    "RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_ID",
    "RELOAD_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION",
    "RELOAD_ACCEPTANCE_PERSISTENCE_VIEWMODEL_VERSION",
    "ReloadAcceptancePersistenceAcknowledgementRow",
    "ReloadAcceptancePersistenceAction",
    "ReloadAcceptancePersistenceActionRow",
    "ReloadAcceptancePersistenceBlockerRow",
    "ReloadAcceptancePersistenceDiagnostic",
    "ReloadAcceptancePersistenceEvidenceRow",
    "ReloadAcceptancePersistenceExpiryRow",
    "ReloadAcceptancePersistenceNonActionFlags",
    "ReloadAcceptancePersistenceProvenanceRow",
    "ReloadAcceptancePersistenceReadiness",
    "ReloadAcceptancePersistenceSchemaRow",
    "ReloadAcceptancePersistenceState",
    "ReloadAcceptancePersistenceStorageOption",
    "ReloadAcceptancePersistenceSummary",
    "ReloadAcceptancePersistenceWritePlan",
    "OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel",
    "all_reload_acceptance_persistence_acknowledgements",
    "build_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel",
    "from_acceptance_mapping",
    "from_acceptance_viewmodel",
    "render_optional_solver_plugin_manifest_reload_acceptance_persistence_viewmodel",
    "unavailable",
]
