"""Pure reload acceptance view-model for optional solver plugin manifest UX state.

This module consumes already-built reload preview/review records supplied by a
caller. It performs no file IO, invokes no reader, imports no GUI or CLI code,
and never accepts runtime reload state, writes persistence, mutates
ProjectSchema, runs discovery/validation/solver execution, activates
candidates, restores trust, or mutates issues/releases/tags/assets.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from enum import Enum

from .plugin_manifest_reload_viewmodel import (
    OptionalSolverPluginManifestReloadViewModel,
)

RELOAD_ACCEPTANCE_VIEWMODEL_VERSION = "osw-exp-119"

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

RELOAD_ACCEPTANCE_REQUIRED_ACKS: tuple[str, ...] = (
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

RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS: tuple[str, ...] = (
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
)

OSPMG_RELOAD_ACCEPTANCE_NOT_REQUESTED = "OSPMG_RELOAD_ACCEPTANCE_NOT_REQUESTED"
OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING = (
    "OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING"
)
OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED = (
    "OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED"
)
OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED = (
    "OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED"
)
OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED = (
    "OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED"
)
OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED = "OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED"
OSPMG_RELOAD_ACCEPTANCE_READY = "OSPMG_RELOAD_ACCEPTANCE_READY"
OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW = (
    "OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW"
)
OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_ERROR = "OSPMG_RELOAD_ACCEPTANCE_ERROR"

OSPMG_RELOAD_ACCEPTANCE_DIAGNOSTIC_CODES: tuple[str, ...] = (
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
    OSPMG_RELOAD_ACCEPTANCE_READY,
    OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW,
    OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_ERROR,
)

_READY_RELOAD_READINESS = {
    "ready_review_only",
    "future_activation_review_required",
    "future_discovery_refresh_required",
}

_RELOAD_CODE_TO_ACCEPTANCE_CODE = {
    "OSPMG_RELOAD_ACK_REQUIRED": OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED,
    "OSPMG_RELOAD_ACK_EXPIRED": OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED,
    "OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED": (
        OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED
    ),
    "OSPMG_RELOAD_CONFLICT_VISIBLE": (
        OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED
    ),
    "OSPMG_RELOAD_SHARED_STACK_VISIBLE": (
        OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED
    ),
    "OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED": (
        OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED
    ),
    "OSPMG_RELOAD_SCHEMA_UNSUPPORTED": (
        OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED
    ),
    "OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED": (
        OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED
    ),
    "OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED": (
        OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED
    ),
    "OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED": (
        OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED
    ),
    "OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED": (
        OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED
    ),
}


class ReloadAcceptanceState(str, Enum):
    """Top-level reload acceptance state vocabulary."""

    NO_PREVIEW = "no_preview"
    NOT_REQUESTED = "not_requested"
    BLOCKED = "blocked"
    READY_FOR_FUTURE_ACCEPTANCE = "ready_for_future_acceptance"
    ACCEPTED_FOR_SESSION_REVIEW = "accepted_for_session_review"
    FUTURE_REVIEW_REQUIRED = "future_review_required"
    ERROR = "error"


class ReloadAcceptanceReadiness(str, Enum):
    """Reload acceptance readiness vocabulary."""

    UNAVAILABLE_NO_PREVIEW = "unavailable_no_preview"
    NOT_REQUESTED = "not_requested"
    BLOCKED_READER = "blocked_reader"
    BLOCKED_VIEWMODEL = "blocked_viewmodel"
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
    READY_FUTURE_ONLY = "ready_future_only"
    ACCEPTED_FOR_SESSION_REVIEW = "accepted_for_session_review"
    FUTURE_REVIEW_REQUIRED = "future_review_required"
    ERROR = "error"


class ReloadAcceptanceAction(str, Enum):
    """Disabled/future-only acceptance and runtime actions."""

    REQUEST_ACCEPTANCE = "request_acceptance"
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
    PERSIST_STATE = "persist_state"
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
class ReloadAcceptanceInput:
    """Caller-supplied in-memory input for acceptance review."""

    reload_viewmodel: object | None = None
    requested: bool = False
    acknowledged: tuple[str, ...] = ()
    accepted_for_session_review: bool = False
    policy_flags: Mapping[str, object] | None = None
    expired_acknowledgements: tuple[str, ...] = ()
    reader_diagnostics: tuple[str, ...] = ()
    error_message: str = ""


@dataclass(frozen=True, slots=True)
class ReloadAcceptanceDiagnostic:
    """One reload acceptance diagnostic row."""

    severity: str
    code: str
    message: str
    blocker: bool = False
    related: str = ""
    suggested_fix: str = ""

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptanceAcknowledgementRow:
    """Visible non-persisted acknowledgement row."""

    acknowledgement_id: str
    label: str
    required: bool = True
    satisfied: bool = False
    expired: bool = False
    blocker: bool = False
    expiry_reasons: tuple[str, ...] = RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS
    not_validation_evidence: bool = True
    not_trust_restoration: bool = True
    persisted_by_this_module: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptanceBlockerRow:
    """Acceptance blocker row."""

    blocker_id: str
    diagnostic_code: str
    label: str
    required_action: str
    severity: str = "error"
    blocks_acceptance: bool = True

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptanceActionState:
    """Disabled or future-only action state."""

    action: ReloadAcceptanceAction
    enabled: bool = False
    future_only: bool = True
    reason: str = "Requires a separate future gate."

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptanceAcceptedStateRow:
    """Representation-only accepted-for-session review state."""

    state_id: str = "accepted-for-session-review"
    accepted_for_session_review: bool = False
    scope: str = "session_review_only"
    untrusted_by_default: bool = True
    persisted_state: bool = False
    project_schema_state: bool = False
    validation_evidence: bool = False
    validation_failure: bool = False
    automatic_activation: bool = False
    trust_restoration: bool = False
    discovery_success: bool = False
    dependency_installation: bool = False
    solver_execution: bool = False
    issue_closure: bool = False
    release_mutation: bool = False
    certification: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptanceSourceProvenanceRow:
    """Preview source/provenance row carried from supplied review records."""

    source_id: str
    source_display: str
    source_reference_redacted: bool = True
    provenance_label: str = "supplied_reload_viewmodel"
    trust_label: str = "untrusted_user_source"
    source_fingerprint_changed: bool = False
    user_plugin_sources_untrusted_by_default: bool = True
    built_ins_authoritative_by_default: bool = False
    trust_label_is_certification: bool = False
    accepted_state_not_trust_restoration: bool = True

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptanceEvidenceHistoryRow:
    """Evidence/history row retained as reference only."""

    evidence_id: str
    candidate_id: str = ""
    evidence_type: str = "history"
    retained_reference_only: bool = True
    not_validation_evidence: bool = True
    not_validation_failure: bool = True
    issue_closure_implied: bool = False
    release_mutation_implied: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptanceTrustBadge:
    """Trust label row that is explicitly not certification."""

    source_id: str
    trust_label: str = "untrusted_user_source"
    trust_restored: bool = False
    trust_label_is_certification: bool = False
    certification_claimed: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptanceNonActionFlags:
    """Honesty flags for actions this view-model never performs."""

    implemented_reload_acceptance: bool = False
    runtime_reload_acceptance_performed: bool = False
    persistence_write_performed: bool = False
    project_schema_mutated: bool = False
    default_reload_path_used: bool = False
    background_reload_performed: bool = False
    directory_scan_performed: bool = False
    network_fetch_performed: bool = False
    plugin_package_imported: bool = False
    cli_subprocess_used: bool = False
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
class ReloadAcceptanceSummary:
    """Top-level reload acceptance summary."""

    state: ReloadAcceptanceState
    readiness: ReloadAcceptanceReadiness
    requested: bool = False
    preview_available: bool = False
    accepted_for_session_review: bool = False
    ready_for_future_acceptance: bool = False
    accepted_state_scope: str = "session_review_only"
    source_count: int = 0
    acknowledgement_count: int = 0
    missing_acknowledgement_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    diagnostic_count: int = 0
    future_activation_review_required: bool = False
    future_discovery_refresh_required: bool = False
    untrusted_by_default: bool = True
    accepted_state_is_validation_evidence: bool = False
    accepted_state_is_validation_failure: bool = False
    accepted_state_restores_trust: bool = False
    accepted_state_automatically_activates: bool = False
    accepted_state_runs_discovery: bool = False
    accepted_state_imports_plugin_package: bool = False
    accepted_state_runs_validation: bool = False
    accepted_state_executes_solver: bool = False
    accepted_state_mutates_project_schema: bool = False
    accepted_state_is_persistence_write: bool = False
    accepted_state_closes_issue: bool = False
    accepted_state_mutates_release: bool = False
    accepted_state_certifies_manifest: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadAcceptanceViewModel:
    """Pure in-memory reload acceptance view-model."""

    summary: ReloadAcceptanceSummary
    acknowledgement_rows: tuple[ReloadAcceptanceAcknowledgementRow, ...] = ()
    blocker_rows: tuple[ReloadAcceptanceBlockerRow, ...] = ()
    diagnostics: tuple[ReloadAcceptanceDiagnostic, ...] = ()
    action_states: tuple[ReloadAcceptanceActionState, ...] = ()
    accepted_state_rows: tuple[ReloadAcceptanceAcceptedStateRow, ...] = ()
    source_provenance_rows: tuple[ReloadAcceptanceSourceProvenanceRow, ...] = ()
    evidence_history_rows: tuple[ReloadAcceptanceEvidenceHistoryRow, ...] = ()
    trust_badges: tuple[ReloadAcceptanceTrustBadge, ...] = ()
    non_action_flags: ReloadAcceptanceNonActionFlags = (
        ReloadAcceptanceNonActionFlags()
    )
    safety_text: tuple[str, ...] = ()

    @classmethod
    def unavailable(
        cls,
        reason: str = "No reload preview was supplied.",
    ) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
        """Return a no-preview state."""

        return _build_acceptance_viewmodel(
            ReloadAcceptanceInput(
                reload_viewmodel=None,
                requested=False,
                policy_flags={"missing_preview_reason": reason},
            )
        )

    @classmethod
    def from_reload_viewmodel(
        cls,
        reload_viewmodel: object,
        *,
        requested: bool = False,
        acknowledged: Sequence[str] = (),
        policy_flags: Mapping[str, object] | None = None,
        accepted_for_session_review: bool = False,
        expired_acknowledgements: Sequence[str] = (),
        reader_diagnostics: Sequence[str] = (),
        error_message: str = "",
    ) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
        """Build acceptance readiness from supplied reload view-model records."""

        return _build_acceptance_viewmodel(
            ReloadAcceptanceInput(
                reload_viewmodel=reload_viewmodel,
                requested=requested,
                acknowledged=tuple(str(item) for item in acknowledged),
                accepted_for_session_review=accepted_for_session_review,
                policy_flags=policy_flags,
                expired_acknowledgements=tuple(
                    str(item) for item in expired_acknowledgements
                ),
                reader_diagnostics=tuple(str(item) for item in reader_diagnostics),
                error_message=error_message,
            )
        )

    @classmethod
    def from_preview_mapping(
        cls,
        mapping: Mapping[str, object],
        *,
        requested: bool = False,
        acknowledged: Sequence[str] = (),
        policy_flags: Mapping[str, object] | None = None,
        accepted_for_session_review: bool = False,
    ) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
        """Build from an already-built reload preview mapping."""

        return cls.from_reload_viewmodel(
            mapping,
            requested=requested,
            acknowledged=acknowledged,
            policy_flags=policy_flags,
            accepted_for_session_review=accepted_for_session_review,
        )

    @classmethod
    def ready_for_future_acceptance(
        cls,
        reload_viewmodel: object,
    ) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
        """Return a ready/future-only state for a supplied preview."""

        return cls.from_reload_viewmodel(
            reload_viewmodel,
            requested=True,
            acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
        )

    @classmethod
    def accepted_for_session_review(
        cls,
        reload_viewmodel: object,
    ) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
        """Represent an already-supplied accepted-for-session review state."""

        return cls.from_reload_viewmodel(
            reload_viewmodel,
            requested=True,
            acknowledged=RELOAD_ACCEPTANCE_REQUIRED_ACKS,
            accepted_for_session_review=True,
        )

    @classmethod
    def error(
        cls,
        message: str,
    ) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
        """Return a deterministic error state without raising."""

        return _build_acceptance_viewmodel(
            ReloadAcceptanceInput(error_message=message)
        )

    def to_mapping(self) -> dict[str, object]:
        """Return deterministic JSON-compatible mapping."""

        return {
            "summary": self.summary.to_mapping(),
            "acknowledgements": [
                row.to_mapping() for row in self.acknowledgement_rows
            ],
            "blockers": [row.to_mapping() for row in self.blocker_rows],
            "diagnostics": [row.to_mapping() for row in self.diagnostics],
            "actions": [row.to_mapping() for row in self.action_states],
            "accepted_state": [
                row.to_mapping() for row in self.accepted_state_rows
            ],
            "source_provenance": [
                row.to_mapping() for row in self.source_provenance_rows
            ],
            "evidence_history": [
                row.to_mapping() for row in self.evidence_history_rows
            ],
            "trust_badges": [row.to_mapping() for row in self.trust_badges],
            "non_action_flags": self.non_action_flags.to_mapping(),
            "safety_text": list(self.safety_text),
            "acknowledgement_expiry_reasons": list(
                RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS
            ),
            "reserved_diagnostic_codes": list(
                OSPMG_RELOAD_ACCEPTANCE_DIAGNOSTIC_CODES
            ),
            "view_model_version": RELOAD_ACCEPTANCE_VIEWMODEL_VERSION,
        }

    def to_text_lines(self) -> tuple[str, ...]:
        """Render stable plain-text review lines."""

        lines = [
            "Optional Solver Plugin Manifest Reload Acceptance View-Model",
            f"state: {self.summary.state.value}",
            f"readiness: {self.summary.readiness.value}",
            f"requested: {self.summary.requested}",
            f"preview_available: {self.summary.preview_available}",
            f"accepted_for_session_review: {self.summary.accepted_for_session_review}",
            (
                "safety: accepted reload UX state is session/review scoped, "
                "untrusted by default, and not persistence"
            ),
            (
                "safety: accepted reload UX state is not validation evidence "
                "and is not validation failure"
            ),
            (
                "safety: acceptance does not restore trust, activate candidates, "
                "run discovery, run validation, or execute solvers"
            ),
            (
                "safety: acceptance does not mutate ProjectSchema, close issues, "
                "mutate releases, write state, or certify manifests"
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
        for diagnostic in self.diagnostics:
            lines.append(f"diagnostic: {diagnostic.severity} {diagnostic.code}")
        for action in self.action_states:
            lines.append(f"action: {action.action.value} enabled={action.enabled}")
        return tuple(lines)


def unavailable(
    reason: str = "No reload preview was supplied.",
) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    """Return a no-preview acceptance view-model."""

    return OptionalSolverPluginManifestReloadAcceptanceViewModel.unavailable(reason)


def from_reload_viewmodel(
    reload_viewmodel: object,
    *,
    requested: bool = False,
    acknowledged: Sequence[str] = (),
    policy_flags: Mapping[str, object] | None = None,
    accepted_for_session_review: bool = False,
    expired_acknowledgements: Sequence[str] = (),
    reader_diagnostics: Sequence[str] = (),
    error_message: str = "",
) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    """Build acceptance readiness from supplied reload view-model records."""

    return OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        reload_viewmodel,
        requested=requested,
        acknowledged=acknowledged,
        policy_flags=policy_flags,
        accepted_for_session_review=accepted_for_session_review,
        expired_acknowledgements=expired_acknowledgements,
        reader_diagnostics=reader_diagnostics,
        error_message=error_message,
    )


def build_optional_solver_plugin_manifest_reload_acceptance_viewmodel(
    input_value: ReloadAcceptanceInput | object | None,
    *,
    requested: bool = False,
    acknowledged: Sequence[str] = (),
    policy_flags: Mapping[str, object] | None = None,
    accepted_for_session_review: bool = False,
) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    """Build the pure acceptance view-model from supplied in-memory data."""

    if isinstance(input_value, ReloadAcceptanceInput):
        return _build_acceptance_viewmodel(input_value)
    if input_value is None:
        return OptionalSolverPluginManifestReloadAcceptanceViewModel.unavailable()
    return OptionalSolverPluginManifestReloadAcceptanceViewModel.from_reload_viewmodel(
        input_value,
        requested=requested,
        acknowledged=acknowledged,
        policy_flags=policy_flags,
        accepted_for_session_review=accepted_for_session_review,
    )


def render_optional_solver_plugin_manifest_reload_acceptance_viewmodel(
    view_model: OptionalSolverPluginManifestReloadAcceptanceViewModel,
) -> tuple[str, ...]:
    """Render stable plain text lines from the acceptance view-model."""

    return view_model.to_text_lines()


def all_reload_acceptance_acknowledgements() -> tuple[str, ...]:
    """Return the deterministic required acknowledgement ids."""

    return RELOAD_ACCEPTANCE_REQUIRED_ACKS


def _build_acceptance_viewmodel(
    input_value: ReloadAcceptanceInput,
) -> OptionalSolverPluginManifestReloadAcceptanceViewModel:
    mapping = _reload_mapping(input_value.reload_viewmodel)
    flags = _mapping(input_value.policy_flags)
    preview_available = _preview_available(mapping)
    acknowledged = set(input_value.acknowledged)
    expired = set(input_value.expired_acknowledgements)
    requested = bool(input_value.requested)
    accepted = bool(input_value.accepted_for_session_review)

    ack_rows = _acknowledgement_rows(
        requested=requested or accepted,
        acknowledged=acknowledged,
        expired=expired,
    )
    source_rows = _source_provenance_rows(mapping, flags)
    evidence_rows = _evidence_history_rows(mapping)
    trust_badges = _trust_badges(source_rows)

    condition_codes = _condition_codes(
        mapping=mapping,
        flags=flags,
        reader_diagnostics=input_value.reader_diagnostics,
        error_message=input_value.error_message,
    )
    if not preview_available and not input_value.error_message:
        condition_codes.append(OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING)
    if preview_available and not requested and not accepted:
        condition_codes.append(OSPMG_RELOAD_ACCEPTANCE_NOT_REQUESTED)
    if accepted:
        condition_codes.append(OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW)
    if (requested or accepted) and any(row.blocker for row in ack_rows):
        condition_codes.append(OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED)
    condition_codes.extend(_future_review_codes(mapping, flags))
    condition_codes = _dedupe(condition_codes)

    readiness = _readiness(condition_codes, requested=requested, accepted=accepted)
    state = _state(readiness, accepted=accepted)
    ready = readiness == ReloadAcceptanceReadiness.READY_FUTURE_ONLY

    diagnostics = _diagnostics(condition_codes, flags)
    blockers = tuple(row for row in diagnostics if row.blocker)
    blocker_rows = tuple(_blocker_row(row) for row in blockers)
    warnings = tuple(row for row in diagnostics if row.severity == "warning")
    accepted_rows = (
        (ReloadAcceptanceAcceptedStateRow(accepted_for_session_review=True),)
        if accepted
        else (ReloadAcceptanceAcceptedStateRow(accepted_for_session_review=False),)
    )
    summary = ReloadAcceptanceSummary(
        state=state,
        readiness=readiness,
        requested=requested,
        preview_available=preview_available,
        accepted_for_session_review=accepted,
        ready_for_future_acceptance=ready,
        source_count=len(source_rows),
        acknowledgement_count=len(ack_rows),
        missing_acknowledgement_count=sum(
            1 for row in ack_rows if row.required and not row.satisfied
        ),
        blocker_count=len(blockers),
        warning_count=len(warnings),
        diagnostic_count=len(diagnostics),
        future_activation_review_required=(
            OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED
            in condition_codes
        ),
        future_discovery_refresh_required=(
            OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED
            in condition_codes
        ),
    )
    return OptionalSolverPluginManifestReloadAcceptanceViewModel(
        summary=summary,
        acknowledgement_rows=ack_rows,
        blocker_rows=blocker_rows,
        diagnostics=diagnostics,
        action_states=_action_states(),
        accepted_state_rows=accepted_rows,
        source_provenance_rows=source_rows,
        evidence_history_rows=evidence_rows,
        trust_badges=trust_badges,
        non_action_flags=ReloadAcceptanceNonActionFlags(),
        safety_text=_safety_text(),
    )


def _reload_mapping(value: object | None) -> Mapping[str, object]:
    if value is None:
        return {}
    if isinstance(value, OptionalSolverPluginManifestReloadViewModel):
        return value.to_mapping()
    if isinstance(value, Mapping):
        return value
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            return mapped
    return {}


def _preview_available(mapping: Mapping[str, object]) -> bool:
    if not mapping:
        return False
    summary = _mapping(mapping.get("summary"))
    readiness = _text(summary.get("readiness")).lower()
    state = _text(summary.get("state")).lower()
    if "unavailable" in readiness or "no_reload_request" in state:
        return False
    return True


def _condition_codes(
    *,
    mapping: Mapping[str, object],
    flags: Mapping[str, object],
    reader_diagnostics: Sequence[str],
    error_message: str,
) -> list[str]:
    codes: list[str] = []
    if error_message:
        codes.append(OSPMG_RELOAD_ACCEPTANCE_ERROR)
    if _flag(flags, "reader_blocked") or reader_diagnostics:
        codes.append(OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED)

    reload_codes = set(_reload_diagnostic_codes(mapping))
    for reload_code, acceptance_code in _RELOAD_CODE_TO_ACCEPTANCE_CODE.items():
        if reload_code in reload_codes:
            codes.append(acceptance_code)

    summary = _mapping(mapping.get("summary"))
    readiness = _text(summary.get("readiness")).lower()
    state = _text(summary.get("state")).lower()
    if _reload_viewmodel_blocked(mapping, readiness, state):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED)
    if "stale" in readiness or _flag(flags, "stale_source_requires_repreview"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED)
    if "conflict" in readiness or _flag(flags, "conflict_review_required"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED)
    if "shared_stack" in readiness or _flag(flags, "shared_stack_review_required"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED)
    if "unsafe_claim" in readiness or _flag(flags, "unsafe_claim_blocked"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED)
    if "schema_unsupported" in readiness or _flag(flags, "unsupported_schema"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED)
    if "migration_required" in readiness or _flag(flags, "migration_required"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED)
    if "unredacted_path" in readiness or _flag(flags, "unredacted_path_blocked"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED)
    if "secret_like" in readiness or _flag(flags, "secret_like_value_blocked"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED)
    if _flag(flags, "trust_policy_changed"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED)
    if _flag(flags, "source_fingerprint_changed"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED)
    if _flag(flags, "policy_changed") or _flag(flags, "acceptance_policy_changed"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED)
    return codes


def _future_review_codes(
    mapping: Mapping[str, object],
    flags: Mapping[str, object],
) -> tuple[str, ...]:
    codes = []
    if _flag(flags, "future_activation_review_required"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED)
    if _flag(flags, "future_discovery_refresh_required"):
        codes.append(OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED)
    for candidate in _iter_mappings(mapping.get("candidates")):
        if bool(candidate.get("requires_future_activation_review", False)):
            codes.append(OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED)
        if bool(candidate.get("requires_future_discovery_refresh", False)):
            codes.append(OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED)
        review = _text(candidate.get("reload_review_state")).lower()
        if "activation" in review:
            codes.append(OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED)
        if "discovery" in review:
            codes.append(OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED)
    return tuple(_dedupe(codes))


def _reload_diagnostic_codes(mapping: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(
        _text(row.get("code"))
        for row in _iter_mappings(mapping.get("diagnostics"))
        if _text(row.get("code"))
    )


def _reload_viewmodel_blocked(
    mapping: Mapping[str, object],
    readiness: str,
    state: str,
) -> bool:
    if readiness in _READY_RELOAD_READINESS:
        return False
    if readiness.startswith("blocked_") or readiness == "error":
        return True
    if "blocked" in state or state.endswith("_error"):
        return True
    for row in _iter_mappings(mapping.get("diagnostics")):
        if bool(row.get("blocker", False)):
            return True
    return False


def _acknowledgement_rows(
    *,
    requested: bool,
    acknowledged: set[str],
    expired: set[str],
) -> tuple[ReloadAcceptanceAcknowledgementRow, ...]:
    rows = []
    for ack_id in RELOAD_ACCEPTANCE_REQUIRED_ACKS:
        is_satisfied = ack_id in acknowledged and ack_id not in expired
        is_expired = ack_id in expired
        rows.append(
            ReloadAcceptanceAcknowledgementRow(
                acknowledgement_id=ack_id,
                label=ack_id.replace("_", " "),
                satisfied=is_satisfied,
                expired=is_expired,
                blocker=bool(requested and (not is_satisfied or is_expired)),
            )
        )
    return tuple(rows)


def _source_provenance_rows(
    mapping: Mapping[str, object],
    flags: Mapping[str, object],
) -> tuple[ReloadAcceptanceSourceProvenanceRow, ...]:
    rows = []
    for index, row in enumerate(_iter_mappings(mapping.get("sources")), start=1):
        trust_label = _text(row.get("trust_label"), "untrusted_user_source")
        built_in = bool(row.get("built_ins_authoritative_by_default", False))
        source_id = _text(row.get("source_id"), f"source-{index}")
        rows.append(
            ReloadAcceptanceSourceProvenanceRow(
                source_id=source_id,
                source_display=_text(row.get("source_display"), source_id),
                source_reference_redacted=bool(
                    row.get("source_reference_redacted", True)
                ),
                provenance_label=_text(
                    row.get("provenance_label"), "supplied_reload_viewmodel"
                ),
                trust_label=trust_label,
                source_fingerprint_changed=_flag(
                    flags,
                    "source_fingerprint_changed",
                ),
                user_plugin_sources_untrusted_by_default=bool(
                    row.get(
                        "user_plugin_sources_untrusted_by_default",
                        not built_in,
                    )
                ),
                built_ins_authoritative_by_default=built_in,
                trust_label_is_certification=bool(
                    row.get("trust_label_is_certification", False)
                ),
            )
        )
    if not rows:
        rows.append(
            ReloadAcceptanceSourceProvenanceRow(
                source_id="supplied-preview",
                source_display="supplied reload preview",
                source_fingerprint_changed=_flag(
                    flags,
                    "source_fingerprint_changed",
                ),
            )
        )
    return tuple(rows)


def _evidence_history_rows(
    mapping: Mapping[str, object],
) -> tuple[ReloadAcceptanceEvidenceHistoryRow, ...]:
    rows = []
    for index, row in enumerate(_iter_mappings(mapping.get("evidence_history")), start=1):
        rows.append(
            ReloadAcceptanceEvidenceHistoryRow(
                evidence_id=_text(row.get("evidence_id"), f"evidence-{index}"),
                candidate_id=_text(row.get("candidate_id")),
                evidence_type=_text(row.get("evidence_type"), "history"),
            )
        )
    return tuple(rows)


def _trust_badges(
    sources: Sequence[ReloadAcceptanceSourceProvenanceRow],
) -> tuple[ReloadAcceptanceTrustBadge, ...]:
    return tuple(
        ReloadAcceptanceTrustBadge(
            source_id=row.source_id,
            trust_label=row.trust_label,
            trust_label_is_certification=row.trust_label_is_certification,
        )
        for row in sources
    )


def _readiness(
    codes: Sequence[str],
    *,
    requested: bool,
    accepted: bool,
) -> ReloadAcceptanceReadiness:
    code_set = set(codes)
    if OSPMG_RELOAD_ACCEPTANCE_ERROR in code_set:
        return ReloadAcceptanceReadiness.ERROR
    if OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING in code_set:
        return ReloadAcceptanceReadiness.UNAVAILABLE_NO_PREVIEW
    if OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_READER
    if OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_SCHEMA_UNSUPPORTED
    if OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_MIGRATION_REQUIRED
    if OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_UNREDACTED_PATH
    if OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_SECRET_LIKE_VALUE
    if OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_UNSAFE_CLAIM
    if OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_STALE_SOURCE_REPREVIEW
    if OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_CONFLICT_REVIEW
    if OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_SHARED_STACK_REVIEW
    if {
        OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED,
        OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED,
        OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED,
    } & code_set:
        return ReloadAcceptanceReadiness.BLOCKED_POLICY_CHANGE
    if OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_VIEWMODEL
    if OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED in code_set:
        return ReloadAcceptanceReadiness.BLOCKED_ACKNOWLEDGEMENT
    if accepted:
        return ReloadAcceptanceReadiness.ACCEPTED_FOR_SESSION_REVIEW
    if not requested:
        return ReloadAcceptanceReadiness.NOT_REQUESTED
    return ReloadAcceptanceReadiness.READY_FUTURE_ONLY


def _state(
    readiness: ReloadAcceptanceReadiness,
    *,
    accepted: bool,
) -> ReloadAcceptanceState:
    if readiness == ReloadAcceptanceReadiness.ERROR:
        return ReloadAcceptanceState.ERROR
    if readiness == ReloadAcceptanceReadiness.UNAVAILABLE_NO_PREVIEW:
        return ReloadAcceptanceState.NO_PREVIEW
    if readiness == ReloadAcceptanceReadiness.NOT_REQUESTED:
        return ReloadAcceptanceState.NOT_REQUESTED
    if readiness == ReloadAcceptanceReadiness.ACCEPTED_FOR_SESSION_REVIEW or accepted:
        return ReloadAcceptanceState.ACCEPTED_FOR_SESSION_REVIEW
    if readiness == ReloadAcceptanceReadiness.READY_FUTURE_ONLY:
        return ReloadAcceptanceState.READY_FOR_FUTURE_ACCEPTANCE
    return ReloadAcceptanceState.BLOCKED


def _diagnostics(
    codes: Sequence[str],
    flags: Mapping[str, object],
) -> tuple[ReloadAcceptanceDiagnostic, ...]:
    rows = []
    for code in codes:
        severity = "info"
        blocker = False
        if code in {
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
            OSPMG_RELOAD_ACCEPTANCE_ERROR,
        }:
            severity = "error"
            blocker = True
        elif code in {
            OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED,
            OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED,
        }:
            severity = "warning"
        rows.append(
            ReloadAcceptanceDiagnostic(
                severity=severity,
                code=code,
                message=_diagnostic_message(code, flags),
                blocker=blocker,
                suggested_fix=_suggested_fix(code),
            )
        )
    if OSPMG_RELOAD_ACCEPTANCE_READY not in codes and not any(
        row.blocker for row in rows
    ):
        rows.append(
            ReloadAcceptanceDiagnostic(
                severity="info",
                code=OSPMG_RELOAD_ACCEPTANCE_READY,
                message=_diagnostic_message(OSPMG_RELOAD_ACCEPTANCE_READY, flags),
            )
        )
    return tuple(rows)


def _blocker_row(row: ReloadAcceptanceDiagnostic) -> ReloadAcceptanceBlockerRow:
    return ReloadAcceptanceBlockerRow(
        blocker_id=row.code.lower().replace("ospmg_reload_acceptance_", ""),
        diagnostic_code=row.code,
        label=row.message,
        required_action=row.suggested_fix or "Resolve the blocker in a future gate.",
        severity=row.severity,
    )


def _action_states() -> tuple[ReloadAcceptanceActionState, ...]:
    return tuple(
        ReloadAcceptanceActionState(
            action=action,
            reason=_action_reason(action),
        )
        for action in ReloadAcceptanceAction
    )


def _diagnostic_message(code: str, flags: Mapping[str, object]) -> str:
    reason = _text(flags.get("missing_preview_reason"))
    return {
        OSPMG_RELOAD_ACCEPTANCE_NOT_REQUESTED: (
            "Acceptance was not requested; reload preview remains review-only."
        ),
        OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING: (
            reason or "No reload preview is available for acceptance review."
        ),
        OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED: (
            "Reader diagnostics block acceptance; no reader is invoked here."
        ),
        OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED: (
            "Reload view-model blockers must be resolved before acceptance."
        ),
        OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED: (
            "Required acceptance acknowledgements are missing or expired."
        ),
        OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED: (
            "Source changed or is stale; re-preview is required before acceptance."
        ),
        OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED: (
            "Conflict review is required; built-ins remain authoritative by default."
        ),
        OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED: (
            "Shared-stack review is required before future activation review."
        ),
        OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED: (
            "Unsafe validation, issue, release, trust, install, or "
            "certification claims are blocked."
        ),
        OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED: (
            "Unsupported reload schema blocks acceptance."
        ),
        OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED: (
            "Schema migration is required and remains future-gated."
        ),
        OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED: (
            "Unredacted path disclosure blocks acceptance."
        ),
        OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED: (
            "Secret-like content blocks acceptance."
        ),
        OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED: (
            "Trust policy changed; acknowledgements must be revisited."
        ),
        OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED: (
            "Source fingerprint changed; re-preview is required."
        ),
        OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED: (
            "Acceptance policy changed; acknowledgements must be revisited."
        ),
        OSPMG_RELOAD_ACCEPTANCE_READY: (
            "Acceptance is ready for a future explicit gate only; no state is written or mutated."
        ),
        OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW: (
            "Accepted-for-session-review is supplied state only, untrusted by "
            "default, and not persistence."
        ),
        OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED: (
            "Future activation review remains required after acceptance."
        ),
        OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED: (
            "Future discovery refresh remains required after acceptance."
        ),
        OSPMG_RELOAD_ACCEPTANCE_ERROR: (
            "Acceptance view-model entered an error state without side effects."
        ),
    }.get(code, code)


def _suggested_fix(code: str) -> str:
    return {
        OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING: (
            "Supply an already-built reload preview."
        ),
        OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED: (
            "Re-run explicit preview after resolving reader diagnostics."
        ),
        OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED: (
            "Resolve reload view-model blockers."
        ),
        OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED: (
            "Show and satisfy required acknowledgements."
        ),
        OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED: (
            "Re-preview the source."
        ),
        OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED: (
            "Resolve or acknowledge conflict review in a future gate."
        ),
        OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED: (
            "Review shared-stack warnings in a future gate."
        ),
        OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED: "Remove unsafe claims.",
        OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED: "Use a supported schema.",
        OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED: "Run a future migration gate.",
        OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED: "Redact raw path values.",
        OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED: "Remove secret-like values.",
        OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED: "Repeat trust/source policy review.",
        OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED: "Repeat reload preview.",
        OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED: "Repeat acceptance policy review.",
        OSPMG_RELOAD_ACCEPTANCE_ERROR: "Inspect supplied acceptance input.",
    }.get(code, "")


def _action_reason(action: ReloadAcceptanceAction) -> str:
    return {
        ReloadAcceptanceAction.REQUEST_ACCEPTANCE: (
            "Acceptance request handling requires a future GUI/CLI gate."
        ),
        ReloadAcceptanceAction.ACCEPT_FOR_SESSION_REVIEW: (
            "Session acceptance mutation is future-gated; this module can only "
            "represent supplied state."
        ),
        ReloadAcceptanceAction.ACCEPT_AS_TRUSTED: (
            "Reload acceptance is not trust restoration."
        ),
        ReloadAcceptanceAction.ACTIVATE_RELOADED_CANDIDATE: (
            "Activation requires a future activation review gate."
        ),
        ReloadAcceptanceAction.REFRESH_DISCOVERY: (
            "Discovery refresh is a separate future gate."
        ),
        ReloadAcceptanceAction.VALIDATE_SOLVER: "Validation execution is out of scope.",
        ReloadAcceptanceAction.EXECUTE_SOLVER: "Solver execution is out of scope.",
        ReloadAcceptanceAction.INSTALL_DEPENDENCY: (
            "Dependency installation is out of scope."
        ),
        ReloadAcceptanceAction.UNINSTALL_DEPENDENCY: (
            "Dependency uninstall is out of scope."
        ),
        ReloadAcceptanceAction.UNINSTALL_SOLVER: "Solver uninstall is out of scope.",
        ReloadAcceptanceAction.MUTATE_PROJECT_SCHEMA: (
            "ProjectSchema mutation requires a separate gate."
        ),
        ReloadAcceptanceAction.PERSIST_STATE: "Persistence writes are out of scope.",
        ReloadAcceptanceAction.CREATE_EXPORT_SUMMARY: (
            "Export summary creation remains future-gated."
        ),
        ReloadAcceptanceAction.CREATE_REPORT_FILE: (
            "Report file creation remains future-gated."
        ),
        ReloadAcceptanceAction.CREATE_RELOADABLE_BUNDLE: (
            "Reloadable bundle creation remains future-gated."
        ),
        ReloadAcceptanceAction.COPY_TO_CLIPBOARD: "Clipboard behavior is out of scope.",
        ReloadAcceptanceAction.ATTACH_TO_REPORT: (
            "Report attachment behavior is out of scope."
        ),
        ReloadAcceptanceAction.OPEN_OUTPUT_FOLDER: (
            "Open-output-folder behavior is out of scope."
        ),
        ReloadAcceptanceAction.CLOSE_ISSUE: (
            "Issue closure requires a separate validation/issue gate."
        ),
        ReloadAcceptanceAction.MUTATE_RELEASE: (
            "Release mutation requires a release gate."
        ),
        ReloadAcceptanceAction.PUSH_TAG: "Tag mutation requires a release gate.",
        ReloadAcceptanceAction.UPLOAD_ASSET: (
            "Asset mutation requires a release gate."
        ),
        ReloadAcceptanceAction.CLAIM_VALIDATION_SUCCESS: (
            "Reload acceptance never claims validation success."
        ),
        ReloadAcceptanceAction.CLAIM_VALIDATION_FAILURE: (
            "Reload acceptance never claims validation failure."
        ),
        ReloadAcceptanceAction.CLAIM_CERTIFICATION: (
            "Trust labels are not certification."
        ),
    }[action]


def _safety_text() -> tuple[str, ...]:
    return (
        "Accepted reload UX state is session/review scoped only.",
        "Accepted reload UX state remains untrusted by default.",
        "Accepted reload UX state is not persistence.",
        "Accepted reload UX state is not ProjectSchema state.",
        "Accepted reload UX state is not validation evidence.",
        "Accepted reload UX state is not validation failure.",
        "Acceptance does not restore trust.",
        "Acceptance does not automatically activate candidates.",
        "Acceptance does not run discovery.",
        "Acceptance does not import plugin packages.",
        "Acceptance does not run validation.",
        "Acceptance does not execute solvers.",
        "Acceptance does not install, uninstall, or remove dependencies or solvers.",
        "Acceptance does not close issues or mutate releases, tags, or assets.",
        "Acceptance does not certify manifests.",
        "Issues #6 through #11 remain live optional validation issues.",
    )


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


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _iter_mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(item for item in value if isinstance(item, Mapping))
    return ()


def _text(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _flag(flags: Mapping[str, object], key: str) -> bool:
    return bool(flags.get(key, False))


def _dedupe(values: Sequence[str]) -> list[str]:
    seen = set()
    rows = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            rows.append(value)
    return rows


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
    "OSPMG_RELOAD_ACCEPTANCE_ACKNOWLEDGEMENT_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_ACCEPTED_FOR_SESSION_REVIEW",
    "OSPMG_RELOAD_ACCEPTANCE_CONFLICT_REVIEW_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_DIAGNOSTIC_CODES",
    "OSPMG_RELOAD_ACCEPTANCE_ERROR",
    "OSPMG_RELOAD_ACCEPTANCE_FUTURE_ACTIVATION_REVIEW_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_FUTURE_DISCOVERY_REFRESH_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_NOT_REQUESTED",
    "OSPMG_RELOAD_ACCEPTANCE_POLICY_CHANGED",
    "OSPMG_RELOAD_ACCEPTANCE_PREVIEW_MISSING",
    "OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_READY",
    "OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED",
    "OSPMG_RELOAD_ACCEPTANCE_SECRET_LIKE_VALUE_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_SHARED_STACK_REVIEW_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_SOURCE_FINGERPRINT_CHANGED",
    "OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_TRUST_POLICY_CHANGED",
    "OSPMG_RELOAD_ACCEPTANCE_UNREDACTED_PATH_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED",
    "RELOAD_ACCEPTANCE_ACK_EXPIRY_REASONS",
    "RELOAD_ACCEPTANCE_REQUIRED_ACKS",
    "RELOAD_ACCEPTANCE_VIEWMODEL_VERSION",
    "ReloadAcceptanceAcknowledgementRow",
    "ReloadAcceptanceAcceptedStateRow",
    "ReloadAcceptanceAction",
    "ReloadAcceptanceActionState",
    "ReloadAcceptanceBlockerRow",
    "ReloadAcceptanceDiagnostic",
    "ReloadAcceptanceEvidenceHistoryRow",
    "ReloadAcceptanceInput",
    "ReloadAcceptanceNonActionFlags",
    "ReloadAcceptanceReadiness",
    "ReloadAcceptanceSourceProvenanceRow",
    "ReloadAcceptanceState",
    "ReloadAcceptanceSummary",
    "ReloadAcceptanceTrustBadge",
    "OptionalSolverPluginManifestReloadAcceptanceViewModel",
    "all_reload_acceptance_acknowledgements",
    "build_optional_solver_plugin_manifest_reload_acceptance_viewmodel",
    "from_reload_viewmodel",
    "render_optional_solver_plugin_manifest_reload_acceptance_viewmodel",
    "unavailable",
]
