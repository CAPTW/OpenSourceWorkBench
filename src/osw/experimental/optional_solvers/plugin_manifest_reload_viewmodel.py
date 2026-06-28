"""Pure reload view-model for optional solver plugin manifest UX state.

This module consumes caller-supplied mappings only. It performs no file IO,
adds no runtime reload behavior, imports no GUI or CLI modules, and does not
run discovery, validation, solver execution, dependency changes, ProjectSchema
mutation, issue/release mutation, trust restoration, or automatic activation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from enum import Enum

STATE_WRITER_PAYLOAD_KIND = "optional_solver_plugin_manifest_state_writer_state"
STATE_WRITER_PAYLOAD_SCHEMA_VERSION = "osw-exp-102-state-writer-1"
RELOAD_VIEWMODEL_VERSION = "osw-exp-107"

ACK_RELOAD_NOT_VALIDATION = "reload_not_validation"
ACK_RELOAD_NOT_TRUST_RESTORATION = "reload_not_trust_restoration"
ACK_RELOAD_NOT_AUTOMATIC_ACTIVATION = "reload_not_automatic_activation"
ACK_RELOAD_NOT_DISCOVERY_SUCCESS = "reload_not_discovery_success"
ACK_RELOAD_NOT_DEPENDENCY_INSTALL = "reload_not_dependency_install"
ACK_RELOAD_NO_SOLVER_EXECUTION = "reload_no_solver_execution"
ACK_RELOAD_NOT_ISSUE_CLOSURE = "reload_not_issue_closure"
ACK_RELOAD_NOT_RELEASE_MUTATION = "reload_not_release_mutation"
ACK_RELOAD_NOT_CERTIFICATION = "reload_not_certification"
ACK_REDACTION_REVIEWED = "redaction_reviewed"
ACK_UNREDACTED_PATHS_BLOCKED = "unredacted_paths_blocked"
ACK_STALE_SOURCE_REQUIRES_REPREVIEW = "stale_source_requires_repreview"
ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED = "untrusted_source_remains_untrusted"
ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD = (
    "activation_review_required_after_reload"
)
ACK_NO_DISCOVERY_EXECUTION = "no_discovery_execution"
ACK_NO_PLUGIN_PACKAGE_IMPORT = "no_plugin_package_import"
ACK_NO_VALIDATION_EXECUTION = "no_validation_execution"
ACK_NO_SOLVER_EXECUTION = "no_solver_execution"
ACK_TRUST_LABEL_NOT_CERTIFICATION = "trust_label_not_certification"
ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE = (
    "persisted_acknowledgements_may_expire"
)

RELOAD_REQUIRED_ACKS: tuple[str, ...] = (
    ACK_RELOAD_NOT_VALIDATION,
    ACK_RELOAD_NOT_TRUST_RESTORATION,
    ACK_RELOAD_NOT_AUTOMATIC_ACTIVATION,
    ACK_RELOAD_NOT_DISCOVERY_SUCCESS,
    ACK_RELOAD_NOT_DEPENDENCY_INSTALL,
    ACK_RELOAD_NO_SOLVER_EXECUTION,
    ACK_RELOAD_NOT_ISSUE_CLOSURE,
    ACK_RELOAD_NOT_RELEASE_MUTATION,
    ACK_RELOAD_NOT_CERTIFICATION,
    ACK_REDACTION_REVIEWED,
    ACK_UNREDACTED_PATHS_BLOCKED,
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
    ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED,
    ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_NO_VALIDATION_EXECUTION,
    ACK_NO_SOLVER_EXECUTION,
    ACK_TRUST_LABEL_NOT_CERTIFICATION,
    ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE,
)

RELOAD_ACK_EXPIRY_REASONS: tuple[str, ...] = (
    "reload",
    "source_fingerprint_change",
    "schema_version_change",
    "unsafe_claim_appearance",
    "trust_policy_change",
    "future_discovery_refresh_result",
)

OSPMG_RELOAD_NOT_IMPLEMENTED = "OSPMG_RELOAD_NOT_IMPLEMENTED"
OSPMG_RELOAD_DESIGN_ONLY = "OSPMG_RELOAD_DESIGN_ONLY"
OSPMG_RELOAD_TARGET_REQUIRED = "OSPMG_RELOAD_TARGET_REQUIRED"
OSPMG_RELOAD_TARGET_MISSING = "OSPMG_RELOAD_TARGET_MISSING"
OSPMG_RELOAD_TARGET_IS_DIRECTORY = "OSPMG_RELOAD_TARGET_IS_DIRECTORY"
OSPMG_RELOAD_TARGET_SYMLINK_REVIEW_REQUIRED = (
    "OSPMG_RELOAD_TARGET_SYMLINK_REVIEW_REQUIRED"
)
OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH = "OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH"
OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED = "OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED"
OSPMG_RELOAD_SCHEMA_UNSUPPORTED = "OSPMG_RELOAD_SCHEMA_UNSUPPORTED"
OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED = "OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED"
OSPMG_RELOAD_REDACTION_REQUIRED = "OSPMG_RELOAD_REDACTION_REQUIRED"
OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED = "OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED"
OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED = (
    "OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED"
)
OSPMG_RELOAD_ACK_REQUIRED = "OSPMG_RELOAD_ACK_REQUIRED"
OSPMG_RELOAD_ACK_EXPIRED = "OSPMG_RELOAD_ACK_EXPIRED"
OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED = (
    "OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED"
)
OSPMG_RELOAD_UNTRUSTED_SOURCE = "OSPMG_RELOAD_UNTRUSTED_SOURCE"
OSPMG_RELOAD_CONFLICT_VISIBLE = "OSPMG_RELOAD_CONFLICT_VISIBLE"
OSPMG_RELOAD_SHARED_STACK_VISIBLE = "OSPMG_RELOAD_SHARED_STACK_VISIBLE"
OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED = "OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED"
OSPMG_RELOAD_EVIDENCE_RETAINED = "OSPMG_RELOAD_EVIDENCE_RETAINED"
OSPMG_RELOAD_HISTORY_RETAINED = "OSPMG_RELOAD_HISTORY_RETAINED"
OSPMG_RELOAD_NOT_VALIDATION = "OSPMG_RELOAD_NOT_VALIDATION"
OSPMG_RELOAD_NOT_TRUST_RESTORE = "OSPMG_RELOAD_NOT_TRUST_RESTORE"
OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION = (
    "OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION"
)
OSPMG_RELOAD_NO_DISCOVERY_EXECUTION = "OSPMG_RELOAD_NO_DISCOVERY_EXECUTION"
OSPMG_RELOAD_NO_PLUGIN_IMPORT = "OSPMG_RELOAD_NO_PLUGIN_IMPORT"
OSPMG_RELOAD_NO_VALIDATION_EXECUTION = "OSPMG_RELOAD_NO_VALIDATION_EXECUTION"
OSPMG_RELOAD_NO_SOLVER_EXECUTION = "OSPMG_RELOAD_NO_SOLVER_EXECUTION"
OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED = (
    "OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED"
)
OSPMG_RELOAD_FUTURE_GATE = "OSPMG_RELOAD_FUTURE_GATE"

OSPMG_RELOAD_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_RELOAD_NOT_IMPLEMENTED,
    OSPMG_RELOAD_DESIGN_ONLY,
    OSPMG_RELOAD_TARGET_REQUIRED,
    OSPMG_RELOAD_TARGET_MISSING,
    OSPMG_RELOAD_TARGET_IS_DIRECTORY,
    OSPMG_RELOAD_TARGET_SYMLINK_REVIEW_REQUIRED,
    OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH,
    OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED,
    OSPMG_RELOAD_SCHEMA_UNSUPPORTED,
    OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED,
    OSPMG_RELOAD_REDACTION_REQUIRED,
    OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED,
    OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED,
    OSPMG_RELOAD_ACK_REQUIRED,
    OSPMG_RELOAD_ACK_EXPIRED,
    OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_RELOAD_UNTRUSTED_SOURCE,
    OSPMG_RELOAD_CONFLICT_VISIBLE,
    OSPMG_RELOAD_SHARED_STACK_VISIBLE,
    OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED,
    OSPMG_RELOAD_EVIDENCE_RETAINED,
    OSPMG_RELOAD_HISTORY_RETAINED,
    OSPMG_RELOAD_NOT_VALIDATION,
    OSPMG_RELOAD_NOT_TRUST_RESTORE,
    OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION,
    OSPMG_RELOAD_NO_DISCOVERY_EXECUTION,
    OSPMG_RELOAD_NO_PLUGIN_IMPORT,
    OSPMG_RELOAD_NO_VALIDATION_EXECUTION,
    OSPMG_RELOAD_NO_SOLVER_EXECUTION,
    OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED,
    OSPMG_RELOAD_FUTURE_GATE,
)

_BOUNDARY_DIAGNOSTICS: tuple[str, ...] = (
    OSPMG_RELOAD_NOT_VALIDATION,
    OSPMG_RELOAD_NOT_TRUST_RESTORE,
    OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION,
    OSPMG_RELOAD_NO_DISCOVERY_EXECUTION,
    OSPMG_RELOAD_NO_PLUGIN_IMPORT,
    OSPMG_RELOAD_NO_VALIDATION_EXECUTION,
    OSPMG_RELOAD_NO_SOLVER_EXECUTION,
    OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED,
    OSPMG_RELOAD_FUTURE_GATE,
)

_SECRET_MARKERS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "access_token",
    "secret",
    "password",
    "bearer ",
    "private_key",
    "client_secret",
)


class OptionalSolverPluginManifestReloadState(str, Enum):
    """Reload review state vocabulary."""

    NO_RELOAD_REQUEST = "no_reload_request"
    TARGET_MISSING = "target_missing"
    TARGET_NOT_SELECTED = "target_not_selected"
    SOURCE_REFERENCE_REDACTED = "source_reference_redacted"
    SCHEMA_REVIEW = "schema_review"
    SCHEMA_UNSUPPORTED = "schema_unsupported"
    SCHEMA_MIGRATION_REQUIRED = "schema_migration_required"
    PAYLOAD_KIND_MISMATCH = "payload_kind_mismatch"
    REDACTION_REVIEW_REQUIRED = "redaction_review_required"
    ACKNOWLEDGEMENT_REVIEW_REQUIRED = "acknowledgement_review_required"
    STALE_SOURCE_REPREVIEW_REQUIRED = "stale_source_repreview_required"
    CONFLICT_REVIEW_REQUIRED = "conflict_review_required"
    UNSAFE_CLAIM_BLOCKED = "unsafe_claim_blocked"
    HISTORY_EVIDENCE_REVIEW = "history_evidence_review"
    RELOAD_PREVIEW_READY = "reload_preview_ready"
    RELOAD_BLOCKED = "reload_blocked"
    RELOAD_ERROR = "reload_error"
    FUTURE_ACTIVATION_REVIEW_REQUIRED = "future_activation_review_required"
    FUTURE_DISCOVERY_REFRESH_REQUIRED = "future_discovery_refresh_required"


class OptionalSolverPluginManifestReloadReadiness(str, Enum):
    """Reload readiness vocabulary."""

    UNAVAILABLE_NO_PAYLOAD = "unavailable_no_payload"
    BLOCKED_PAYLOAD_KIND_MISMATCH = "blocked_payload_kind_mismatch"
    BLOCKED_SCHEMA_VERSION_MISSING = "blocked_schema_version_missing"
    BLOCKED_SCHEMA_UNSUPPORTED = "blocked_schema_unsupported"
    BLOCKED_SCHEMA_MIGRATION_REQUIRED = "blocked_schema_migration_required"
    BLOCKED_REDACTION_REVIEW = "blocked_redaction_review"
    BLOCKED_UNREDACTED_PATH = "blocked_unredacted_path"
    BLOCKED_SECRET_LIKE_CONTENT = "blocked_secret_like_content"
    BLOCKED_ACKNOWLEDGEMENT = "blocked_acknowledgement"
    BLOCKED_STALE_SOURCE_REPREVIEW = "blocked_stale_source_repreview"
    BLOCKED_CONFLICT = "blocked_conflict"
    BLOCKED_SHARED_STACK_WARNING = "blocked_shared_stack_warning"
    BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_claim"
    READY_REVIEW_ONLY = "ready_review_only"
    FUTURE_ACTIVATION_REVIEW_REQUIRED = "future_activation_review_required"
    FUTURE_DISCOVERY_REFRESH_REQUIRED = "future_discovery_refresh_required"
    ERROR = "error"


class OptionalSolverPluginManifestReloadAction(str, Enum):
    """Disabled/future-only reload actions."""

    READ_RELOAD_FILE = "read_reload_file"
    PARSE_RELOAD_FILE = "parse_reload_file"
    MIGRATE_SCHEMA = "migrate_schema"
    ACCEPT_RELOAD_AS_TRUSTED = "accept_reload_as_trusted"
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
    CLAIM_VALIDATION_SUCCESS_FAILURE = "claim_validation_success_failure"
    CLAIM_CERTIFICATION = "claim_certification"


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadInput:
    """Caller-supplied reload view-model input."""

    payload_mapping: Mapping[str, object] | None = None
    source_label: str | None = None
    explicit_error: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadDiagnostic:
    """Diagnostic row surfaced by the reload view-model."""

    severity: str
    code: str
    message: str
    blocker: bool = False
    related: str = ""
    suggested_fix: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadSummary:
    """Top-level reload summary."""

    state: OptionalSolverPluginManifestReloadState
    readiness: OptionalSolverPluginManifestReloadReadiness
    payload_kind: str = ""
    payload_schema_version: str = ""
    writer_version: str = ""
    source_display: str = ""
    source_reference_redacted: bool = True
    source_count: int = 0
    candidate_count: int = 0
    acknowledgement_count: int = 0
    diagnostic_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    reload_is_validation_evidence: bool = False
    reload_is_validation_failure: bool = False
    reload_restores_trust: bool = False
    reload_automatically_activates: bool = False
    reload_runs_discovery: bool = False
    reload_imports_plugin_package: bool = False
    reload_runs_validation: bool = False
    reload_executes_solver: bool = False
    reload_mutates_project_schema: bool = False
    reload_closes_issue: bool = False
    reload_mutates_release: bool = False
    reload_certifies_manifest: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadSourceRow:
    """Source/provenance row for review."""

    source_id: str
    source_type: str
    source_display: str
    source_reference_redacted: bool = True
    provenance_label: str = "caller_supplied_payload"
    trust_label: str = "untrusted_user_source"
    trust_label_is_certification: bool = False
    user_plugin_sources_untrusted_by_default: bool = True
    built_ins_authoritative_by_default: bool = False
    fingerprint_not_trust_signal: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadCandidateRow:
    """Candidate lifecycle row for review."""

    candidate_id: str
    display_name: str
    source_id: str = ""
    source_type: str = "user"
    lifecycle_state: str = "inactive"
    reload_review_state: str = "review_only"
    requires_future_activation_review: bool = False
    requires_future_discovery_refresh: bool = False
    no_automatic_activation: bool = True
    no_trust_restoration: bool = True
    skipped_missing_remains_skipped_missing: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadAcknowledgementRow:
    """Acknowledgement row with reload-expiry semantics."""

    acknowledgement_id: str
    label: str
    required: bool = True
    satisfied: bool = False
    expired: bool = False
    blocker: bool = False
    expiry_reasons: tuple[str, ...] = RELOAD_ACK_EXPIRY_REASONS


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadSchemaRow:
    """Payload/schema review row."""

    payload_kind: str
    payload_schema_version: str
    payload_kind_required: bool = True
    payload_schema_version_required: bool = True
    supported_schema: bool = False
    migration_required: bool = False
    blocker: bool = False
    schema_mismatch_not_validation_failure: bool = True
    schema_model_separate_from_project_schema: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadRedactionRow:
    """Redaction/privacy review row."""

    redaction_required: bool = True
    redaction_review_required: bool = False
    raw_paths_hidden_by_default: bool = True
    unredacted_path_blocked: bool = False
    secret_like_content_blocked: bool = False
    fingerprints_not_trust_signals: bool = True
    redaction_review_before_activation_review: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadStaleSourceRow:
    """Stale-source/re-preview row."""

    source_id: str
    stale_source_state: str = ""
    repreview_required: bool = False
    old_preview_not_silently_trusted: bool = True
    no_source_file_io: bool = True
    stale_source_not_validation_failure: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadConflictRow:
    """Conflict/shared-stack row."""

    conflict_id: str
    candidate_id: str = ""
    conflict_type: str = "conflict"
    built_ins_win_by_default: bool = True
    persisted_state_overrides_built_ins: bool = False
    shared_stack_warning_visible: bool = False
    reload_resolves_conflict: bool = False
    blocker: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadUnsafeClaimRow:
    """Unsafe claim row."""

    claim_id: str
    claim_type: str
    claim_text: str
    blocked: bool = True
    not_reloaded_as_truth: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadEvidenceRow:
    """Evidence/history retention row."""

    evidence_id: str
    candidate_id: str = ""
    evidence_type: str = "history"
    deactivation_history_retained: bool = True
    reactivation_history_retained: bool = True
    historical_evidence_reference_only: bool = True
    skipped_missing_remains_skipped_missing: bool = True
    reload_is_not_validation_evidence: bool = True
    evidence_deleted_or_rewritten: bool = False
    issue_closure_implied: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadActionState:
    """Disabled/future action state."""

    action: OptionalSolverPluginManifestReloadAction
    enabled: bool = False
    future_only: bool = True
    reason: str = "Requires a separate future gate."


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadViewModel:
    """Pure in-memory reload view-model."""

    summary: OptionalSolverPluginManifestReloadSummary
    source_rows: tuple[OptionalSolverPluginManifestReloadSourceRow, ...] = ()
    candidate_rows: tuple[OptionalSolverPluginManifestReloadCandidateRow, ...] = ()
    acknowledgement_rows: tuple[
        OptionalSolverPluginManifestReloadAcknowledgementRow, ...
    ] = ()
    schema_rows: tuple[OptionalSolverPluginManifestReloadSchemaRow, ...] = ()
    redaction_rows: tuple[OptionalSolverPluginManifestReloadRedactionRow, ...] = ()
    stale_source_rows: tuple[OptionalSolverPluginManifestReloadStaleSourceRow, ...] = (
        ()
    )
    conflict_rows: tuple[OptionalSolverPluginManifestReloadConflictRow, ...] = ()
    unsafe_claim_rows: tuple[OptionalSolverPluginManifestReloadUnsafeClaimRow, ...] = (
        ()
    )
    evidence_rows: tuple[OptionalSolverPluginManifestReloadEvidenceRow, ...] = ()
    diagnostics: tuple[OptionalSolverPluginManifestReloadDiagnostic, ...] = ()
    action_states: tuple[OptionalSolverPluginManifestReloadActionState, ...] = ()
    safety_text: tuple[str, ...] = ()

    @classmethod
    def from_payload_mapping(
        cls,
        payload: Mapping[str, object],
        *,
        source_label: str | None = None,
    ) -> OptionalSolverPluginManifestReloadViewModel:
        """Build reload review state from a caller-supplied payload mapping."""

        return _build_view_model(
            OptionalSolverPluginManifestReloadInput(
                payload_mapping=payload,
                source_label=source_label,
            )
        )

    @classmethod
    def from_state_writer_payload(
        cls,
        payload: Mapping[str, object],
        *,
        source_label: str | None = None,
    ) -> OptionalSolverPluginManifestReloadViewModel:
        """Alias for state-writer payload mappings."""

        return cls.from_payload_mapping(payload, source_label=source_label)

    @classmethod
    def unavailable(
        cls,
        reason: str = "No persisted UX state payload was supplied.",
    ) -> OptionalSolverPluginManifestReloadViewModel:
        """Return unavailable/no-payload state."""

        diagnostic = _diagnostic(
            "warning",
            OSPMG_RELOAD_TARGET_REQUIRED,
            reason,
            blocker=True,
        )
        return _empty_view_model(
            state=OptionalSolverPluginManifestReloadState.NO_RELOAD_REQUEST,
            readiness=OptionalSolverPluginManifestReloadReadiness.UNAVAILABLE_NO_PAYLOAD,
            diagnostics=(diagnostic,),
        )

    @classmethod
    def empty(cls) -> OptionalSolverPluginManifestReloadViewModel:
        """Return deterministic empty/no-request state."""

        return cls.unavailable("No reload request has been made.")

    @classmethod
    def blocked(
        cls,
        reason: str = "Reload view-model is blocked.",
        diagnostics: Sequence[str] = (),
    ) -> OptionalSolverPluginManifestReloadViewModel:
        """Return deterministic blocked state for test and UI scaffolding."""

        rows = tuple(
            _diagnostic("error", code, reason, blocker=True)
            for code in diagnostics
        ) or (
            _diagnostic(
                "error",
                OSPMG_RELOAD_NOT_IMPLEMENTED,
                reason,
                blocker=True,
            ),
        )
        return _empty_view_model(
            state=OptionalSolverPluginManifestReloadState.RELOAD_BLOCKED,
            readiness=OptionalSolverPluginManifestReloadReadiness.ERROR,
            diagnostics=rows,
        )

    @classmethod
    def sample_ready_for_review(cls) -> OptionalSolverPluginManifestReloadViewModel:
        """Return a deterministic ready sample without external state."""

        return cls.from_payload_mapping(_sample_payload(), source_label="sample.json")

    def to_mapping(self) -> dict[str, object]:
        """Return deterministic JSON-compatible mapping."""

        return {
            "summary": _record_to_mapping(self.summary),
            "sources": [_record_to_mapping(row) for row in self.source_rows],
            "candidates": [_record_to_mapping(row) for row in self.candidate_rows],
            "acknowledgements": [
                _record_to_mapping(row) for row in self.acknowledgement_rows
            ],
            "schema": [_record_to_mapping(row) for row in self.schema_rows],
            "redaction_privacy": [
                _record_to_mapping(row) for row in self.redaction_rows
            ],
            "stale_sources": [
                _record_to_mapping(row) for row in self.stale_source_rows
            ],
            "conflicts": [_record_to_mapping(row) for row in self.conflict_rows],
            "unsafe_claims": [
                _record_to_mapping(row) for row in self.unsafe_claim_rows
            ],
            "evidence_history": [
                _record_to_mapping(row) for row in self.evidence_rows
            ],
            "diagnostics": [_record_to_mapping(row) for row in self.diagnostics],
            "actions": [_record_to_mapping(row) for row in self.action_states],
            "safety_text": list(self.safety_text),
            "reserved_diagnostic_codes": list(OSPMG_RELOAD_DIAGNOSTIC_CODES),
            "view_model_version": RELOAD_VIEWMODEL_VERSION,
        }

    def to_text_lines(self) -> tuple[str, ...]:
        """Render stable plain text review lines."""

        lines = [
            "Optional Solver Plugin Manifest Reload View-Model",
            f"state: {self.summary.state.value}",
            f"readiness: {self.summary.readiness.value}",
            f"payload_kind: {self.summary.payload_kind}",
            f"payload_schema_version: {self.summary.payload_schema_version}",
            f"source: {self.summary.source_display}",
            (
                "safety: reloaded manifest UX state is not validation evidence "
                "and is not validation failure"
            ),
            (
                "safety: reload does not restore trust and does not "
                "automatically activate candidates"
            ),
            (
                "safety: reload does not run discovery, import plugin packages, "
                "run validation, or execute solvers"
            ),
            (
                "safety: reload does not mutate ProjectSchema, close issues, "
                "mutate releases, or certify manifests"
            ),
        ]
        for candidate in self.candidate_rows:
            lines.append(
                "candidate: "
                f"{candidate.candidate_id} lifecycle={candidate.lifecycle_state} "
                f"review={candidate.reload_review_state}"
            )
        for diagnostic in self.diagnostics:
            lines.append(f"diagnostic: {diagnostic.severity} {diagnostic.code}")
        for action in self.action_states:
            lines.append(f"action: {action.action.value} enabled={action.enabled}")
        return tuple(lines)


def from_payload_mapping(
    payload: Mapping[str, object],
    *,
    source_label: str | None = None,
) -> OptionalSolverPluginManifestReloadViewModel:
    """Build reload review state from a caller-supplied payload mapping."""

    return OptionalSolverPluginManifestReloadViewModel.from_payload_mapping(
        payload,
        source_label=source_label,
    )


def from_state_writer_payload(
    payload: Mapping[str, object],
    *,
    source_label: str | None = None,
) -> OptionalSolverPluginManifestReloadViewModel:
    """Build reload review state from a state-writer payload mapping."""

    return OptionalSolverPluginManifestReloadViewModel.from_state_writer_payload(
        payload,
        source_label=source_label,
    )


def build_optional_solver_plugin_manifest_reload_viewmodel(
    input_value: OptionalSolverPluginManifestReloadInput | Mapping[str, object] | None,
    *,
    source_label: str | None = None,
) -> OptionalSolverPluginManifestReloadViewModel:
    """Build the pure reload view-model from caller-supplied in-memory data."""

    if input_value is None:
        return OptionalSolverPluginManifestReloadViewModel.unavailable()
    if isinstance(input_value, OptionalSolverPluginManifestReloadInput):
        return _build_view_model(input_value)
    if isinstance(input_value, Mapping):
        return OptionalSolverPluginManifestReloadViewModel.from_payload_mapping(
            input_value,
            source_label=source_label,
        )
    raise TypeError("Reload view-model requires a mapping input.")


def render_optional_solver_plugin_manifest_reload_viewmodel(
    view_model: OptionalSolverPluginManifestReloadViewModel,
) -> tuple[str, ...]:
    """Render stable plain text lines from the reload view-model."""

    return view_model.to_text_lines()


def unavailable(
    reason: str = "No persisted UX state payload was supplied.",
) -> OptionalSolverPluginManifestReloadViewModel:
    """Return unavailable/no-payload state."""

    return OptionalSolverPluginManifestReloadViewModel.unavailable(reason)


def empty() -> OptionalSolverPluginManifestReloadViewModel:
    """Return deterministic empty/no-request state."""

    return OptionalSolverPluginManifestReloadViewModel.empty()


def blocked(
    reason: str = "Reload view-model is blocked.",
    diagnostics: Sequence[str] = (),
) -> OptionalSolverPluginManifestReloadViewModel:
    """Return deterministic blocked state."""

    return OptionalSolverPluginManifestReloadViewModel.blocked(
        reason,
        diagnostics=diagnostics,
    )


def sample_ready_for_review() -> OptionalSolverPluginManifestReloadViewModel:
    """Return a deterministic ready sample without external state."""

    return OptionalSolverPluginManifestReloadViewModel.sample_ready_for_review()


def _build_view_model(
    input_value: OptionalSolverPluginManifestReloadInput,
) -> OptionalSolverPluginManifestReloadViewModel:
    payload = input_value.payload_mapping
    if payload is None:
        return OptionalSolverPluginManifestReloadViewModel.unavailable()

    source_display, source_redacted = _display_from_label(input_value.source_label)
    payload_kind = _text(payload.get("payload_kind"))
    payload_schema_version = _text(payload.get("payload_schema_version"))
    header = _mapping(payload.get("header"))
    writer_version = _text(payload.get("writer_version", header.get("writer_version")))

    sources = _source_rows(payload, source_display, source_redacted)
    candidates = _candidate_rows(payload)
    acks = _acknowledgement_rows(payload)
    schema_rows = _schema_rows(payload_kind, payload_schema_version, payload)
    redaction_rows = _redaction_rows(payload)
    stale_rows = _stale_source_rows(payload)
    conflict_rows = _conflict_rows(payload)
    unsafe_rows = _unsafe_claim_rows(payload)
    evidence_rows = _evidence_rows(payload)

    readiness, state = _readiness_and_state(
        payload_kind=payload_kind,
        payload_schema_version=payload_schema_version,
        payload=payload,
        redaction_rows=redaction_rows,
        acks=acks,
        stale_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_rows=unsafe_rows,
        candidates=candidates,
        explicit_error=input_value.explicit_error,
    )
    diagnostics = _diagnostics(
        readiness=readiness,
        state=state,
        sources=sources,
        acks=acks,
        stale_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_rows=unsafe_rows,
        evidence_rows=evidence_rows,
        redaction_rows=redaction_rows,
        payload_kind=payload_kind,
        payload_schema_version=payload_schema_version,
        payload=payload,
    )
    warnings = tuple(row for row in diagnostics if row.severity == "warning")
    blockers = tuple(row for row in diagnostics if row.blocker)
    summary = OptionalSolverPluginManifestReloadSummary(
        state=state,
        readiness=readiness,
        payload_kind=payload_kind,
        payload_schema_version=payload_schema_version,
        writer_version=writer_version,
        source_display=source_display,
        source_reference_redacted=source_redacted,
        source_count=len(sources),
        candidate_count=len(candidates),
        acknowledgement_count=len(acks),
        diagnostic_count=len(diagnostics),
        blocker_count=len(blockers),
        warning_count=len(warnings),
    )
    return OptionalSolverPluginManifestReloadViewModel(
        summary=summary,
        source_rows=sources,
        candidate_rows=candidates,
        acknowledgement_rows=acks,
        schema_rows=schema_rows,
        redaction_rows=redaction_rows,
        stale_source_rows=stale_rows,
        conflict_rows=conflict_rows,
        unsafe_claim_rows=unsafe_rows,
        evidence_rows=evidence_rows,
        diagnostics=diagnostics,
        action_states=_action_states(),
        safety_text=_safety_text(),
    )


def _empty_view_model(
    *,
    state: OptionalSolverPluginManifestReloadState,
    readiness: OptionalSolverPluginManifestReloadReadiness,
    diagnostics: Sequence[OptionalSolverPluginManifestReloadDiagnostic] = (),
) -> OptionalSolverPluginManifestReloadViewModel:
    all_diagnostics = tuple(diagnostics) + tuple(
        _diagnostic("info", code, _diagnostic_message(code))
        for code in _BOUNDARY_DIAGNOSTICS
    )
    summary = OptionalSolverPluginManifestReloadSummary(
        state=state,
        readiness=readiness,
        diagnostic_count=len(all_diagnostics),
        blocker_count=sum(1 for row in all_diagnostics if row.blocker),
        warning_count=sum(1 for row in all_diagnostics if row.severity == "warning"),
    )
    return OptionalSolverPluginManifestReloadViewModel(
        summary=summary,
        diagnostics=all_diagnostics,
        action_states=_action_states(),
        safety_text=_safety_text(),
    )


def _source_rows(
    payload: Mapping[str, object],
    source_display: str,
    source_redacted: bool,
) -> tuple[OptionalSolverPluginManifestReloadSourceRow, ...]:
    rows = []
    for index, row in enumerate(_iter_mappings(payload.get("sources")), start=1):
        raw_display = _text(
            row.get(
                "source_reference_display",
                row.get("source_display", row.get("source_label", "")),
            )
        )
        display, redacted = _display_from_label(raw_display)
        if not display:
            display = f"source-{index}"
        source_type = _text(row.get("source_type", "user_selected_state"))
        trust_label = _text(row.get("trust_label", _trust_label(source_type)))
        built_in = _is_built_in(source_type, trust_label)
        rows.append(
            OptionalSolverPluginManifestReloadSourceRow(
                source_id=_text(row.get("source_id", f"source-{index}")),
                source_type=source_type,
                source_display=display,
                source_reference_redacted=bool(
                    row.get("source_reference_redacted", redacted)
                ),
                provenance_label=_text(
                    row.get("provenance_label", "caller_supplied_payload")
                ),
                trust_label=trust_label,
                user_plugin_sources_untrusted_by_default=not built_in,
                built_ins_authoritative_by_default=built_in,
            )
        )
    if not rows:
        rows.append(
            OptionalSolverPluginManifestReloadSourceRow(
                source_id="caller-supplied-payload",
                source_type="caller_supplied_mapping",
                source_display=source_display or "caller-supplied mapping",
                source_reference_redacted=source_redacted,
                trust_label="untrusted_user_source",
            )
        )
    return tuple(rows)


def _candidate_rows(
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestReloadCandidateRow, ...]:
    rows = []
    for index, row in enumerate(_iter_mappings(payload.get("candidates")), start=1):
        lifecycle = _text(
            row.get(
                "lifecycle_state",
                row.get("persisted_lifecycle_state", row.get("state", "inactive")),
            )
        ).lower()
        review, future_activation, future_refresh = _candidate_review_state(lifecycle)
        skipped_missing = bool(
            row.get("skipped_missing_remains_skipped_missing")
            or row.get("skipped_missing")
            or _text(row.get("validation_state")).lower() == "skipped_missing"
        )
        rows.append(
            OptionalSolverPluginManifestReloadCandidateRow(
                candidate_id=_text(
                    row.get(
                        "candidate_id",
                        row.get("stack_id", row.get("id", f"candidate-{index}")),
                    )
                ),
                display_name=_text(
                    row.get("display_name", row.get("name", f"Candidate {index}"))
                ),
                source_id=_text(row.get("source_id", "")),
                source_type=_text(row.get("source_type", "user")),
                lifecycle_state=lifecycle,
                reload_review_state=review,
                requires_future_activation_review=future_activation,
                requires_future_discovery_refresh=future_refresh,
                skipped_missing_remains_skipped_missing=skipped_missing,
            )
        )
    return tuple(rows)


def _acknowledgement_rows(
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestReloadAcknowledgementRow, ...]:
    supplied: dict[str, Mapping[str, object]] = {}
    for row in _iter_mappings(payload.get("acknowledgements")):
        ack_id = _text(
            row.get("acknowledgement_id", row.get("ack_id", row.get("id", "")))
        )
        if ack_id:
            supplied[ack_id] = row
    rows = []
    for ack_id in RELOAD_REQUIRED_ACKS:
        row = supplied.get(ack_id, {})
        satisfied = bool(row.get("satisfied", False))
        expired = bool(row.get("expired", row.get("expires_on_reload", False)))
        blocker = not satisfied or expired
        rows.append(
            OptionalSolverPluginManifestReloadAcknowledgementRow(
                acknowledgement_id=ack_id,
                label=_text(row.get("label", _ack_label(ack_id))),
                required=True,
                satisfied=satisfied,
                expired=expired,
                blocker=blocker,
                expiry_reasons=tuple(
                    _text(item) for item in _sequence(row.get("expiry_reasons"))
                )
                or RELOAD_ACK_EXPIRY_REASONS,
            )
        )
    return tuple(rows)


def _schema_rows(
    payload_kind: str,
    payload_schema_version: str,
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestReloadSchemaRow, ...]:
    migration = _migration_required(payload)
    return (
        OptionalSolverPluginManifestReloadSchemaRow(
            payload_kind=payload_kind,
            payload_schema_version=payload_schema_version,
            supported_schema=payload_schema_version
            == STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
            migration_required=migration,
            blocker=(
                payload_kind != STATE_WRITER_PAYLOAD_KIND
                or not payload_schema_version
                or payload_schema_version != STATE_WRITER_PAYLOAD_SCHEMA_VERSION
                or migration
            ),
        ),
    )


def _redaction_rows(
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestReloadRedactionRow, ...]:
    rows = []
    for row in _iter_mappings(payload.get("redaction_privacy")):
        rows.append(
            OptionalSolverPluginManifestReloadRedactionRow(
                redaction_required=bool(row.get("redaction_required", True)),
                redaction_review_required=bool(
                    row.get("redaction_review_required", False)
                    or row.get("review_required", False)
                ),
                unredacted_path_blocked=bool(
                    row.get("unredacted_path_blocked", False)
                    or row.get("raw_reference_blocked", False)
                ),
                secret_like_content_blocked=bool(
                    row.get("secret_like_content_blocked", False)
                ),
            )
        )
    if not rows:
        rows.append(
            OptionalSolverPluginManifestReloadRedactionRow(
                redaction_review_required=bool(
                    payload.get("redaction_review_required", False)
                ),
                unredacted_path_blocked=bool(
                    payload.get("unredacted_path_blocked", False)
                ),
                secret_like_content_blocked=bool(
                    payload.get("secret_like_content_blocked", False)
                ),
            )
        )
    return tuple(rows)


def _stale_source_rows(
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestReloadStaleSourceRow, ...]:
    rows = []
    for index, row in enumerate(_iter_mappings(payload.get("stale_sources")), start=1):
        rows.append(
            OptionalSolverPluginManifestReloadStaleSourceRow(
                source_id=_text(row.get("source_id", f"source-{index}")),
                stale_source_state=_text(
                    row.get("stale_source_state", row.get("state", "stale"))
                ),
                repreview_required=bool(row.get("repreview_required", True)),
            )
        )
    return tuple(rows)


def _conflict_rows(
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestReloadConflictRow, ...]:
    rows = []
    for index, row in enumerate(_iter_mappings(payload.get("conflicts")), start=1):
        conflict_type = _text(row.get("conflict_type", row.get("kind", "conflict")))
        shared = bool(row.get("shared_stack_warning_visible", False)) or (
            conflict_type == "shared_stack"
        )
        rows.append(
            OptionalSolverPluginManifestReloadConflictRow(
                conflict_id=_text(row.get("conflict_id", f"conflict-{index}")),
                candidate_id=_text(row.get("candidate_id", row.get("stack_id", ""))),
                conflict_type=conflict_type,
                shared_stack_warning_visible=shared,
                blocker=bool(row.get("blocker", True)),
            )
        )
    return tuple(rows)


def _unsafe_claim_rows(
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestReloadUnsafeClaimRow, ...]:
    rows = []
    for index, row in enumerate(_iter_mappings(payload.get("unsafe_claims")), start=1):
        claim_text = _text(row.get("claim_text", row.get("text", "")))
        rows.append(
            OptionalSolverPluginManifestReloadUnsafeClaimRow(
                claim_id=_text(row.get("claim_id", f"unsafe-claim-{index}")),
                claim_type=_text(row.get("claim_type", _classify_claim(claim_text))),
                claim_text=claim_text,
                blocked=bool(row.get("blocked", True)),
            )
        )
    return tuple(rows)


def _evidence_rows(
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestReloadEvidenceRow, ...]:
    rows = []
    for index, row in enumerate(
        _iter_mappings(payload.get("evidence_history")), start=1
    ):
        rows.append(
            OptionalSolverPluginManifestReloadEvidenceRow(
                evidence_id=_text(row.get("evidence_id", f"evidence-{index}")),
                candidate_id=_text(row.get("candidate_id", row.get("stack_id", ""))),
                evidence_type=_text(row.get("evidence_type", "history")),
                deactivation_history_retained=bool(
                    row.get("deactivation_history_retained", True)
                ),
                reactivation_history_retained=bool(
                    row.get("reactivation_history_retained", True)
                ),
                historical_evidence_reference_only=bool(
                    row.get("historical_evidence_reference_only", True)
                ),
                skipped_missing_remains_skipped_missing=bool(
                    row.get("skipped_missing_remains_skipped_missing", True)
                ),
            )
        )
    return tuple(rows)


def _readiness_and_state(
    *,
    payload_kind: str,
    payload_schema_version: str,
    payload: Mapping[str, object],
    redaction_rows: Sequence[OptionalSolverPluginManifestReloadRedactionRow],
    acks: Sequence[OptionalSolverPluginManifestReloadAcknowledgementRow],
    stale_rows: Sequence[OptionalSolverPluginManifestReloadStaleSourceRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestReloadConflictRow],
    unsafe_rows: Sequence[OptionalSolverPluginManifestReloadUnsafeClaimRow],
    candidates: Sequence[OptionalSolverPluginManifestReloadCandidateRow],
    explicit_error: str = "",
) -> tuple[
    OptionalSolverPluginManifestReloadReadiness,
    OptionalSolverPluginManifestReloadState,
]:
    if payload_kind != STATE_WRITER_PAYLOAD_KIND:
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_PAYLOAD_KIND_MISMATCH,
            OptionalSolverPluginManifestReloadState.PAYLOAD_KIND_MISMATCH,
        )
    if not payload_schema_version:
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_SCHEMA_VERSION_MISSING,
            OptionalSolverPluginManifestReloadState.SCHEMA_REVIEW,
        )
    if _migration_required(payload):
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_SCHEMA_MIGRATION_REQUIRED,
            OptionalSolverPluginManifestReloadState.SCHEMA_MIGRATION_REQUIRED,
        )
    if payload_schema_version != STATE_WRITER_PAYLOAD_SCHEMA_VERSION:
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_SCHEMA_UNSUPPORTED,
            OptionalSolverPluginManifestReloadState.SCHEMA_UNSUPPORTED,
        )
    if any(row.secret_like_content_blocked for row in redaction_rows):
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_SECRET_LIKE_CONTENT,
            OptionalSolverPluginManifestReloadState.REDACTION_REVIEW_REQUIRED,
        )
    if any(row.unredacted_path_blocked for row in redaction_rows):
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_UNREDACTED_PATH,
            OptionalSolverPluginManifestReloadState.REDACTION_REVIEW_REQUIRED,
        )
    if any(row.redaction_review_required for row in redaction_rows):
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_REDACTION_REVIEW,
            OptionalSolverPluginManifestReloadState.REDACTION_REVIEW_REQUIRED,
        )
    if any(row.blocked for row in unsafe_rows):
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_UNSAFE_CLAIM,
            OptionalSolverPluginManifestReloadState.UNSAFE_CLAIM_BLOCKED,
        )
    if any(row.repreview_required for row in stale_rows):
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_STALE_SOURCE_REPREVIEW,
            OptionalSolverPluginManifestReloadState.STALE_SOURCE_REPREVIEW_REQUIRED,
        )
    if any(row.blocker for row in conflict_rows):
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_CONFLICT,
            OptionalSolverPluginManifestReloadState.CONFLICT_REVIEW_REQUIRED,
        )
    if any(row.shared_stack_warning_visible for row in conflict_rows):
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_SHARED_STACK_WARNING,
            OptionalSolverPluginManifestReloadState.CONFLICT_REVIEW_REQUIRED,
        )
    if any(row.blocker for row in acks):
        return (
            OptionalSolverPluginManifestReloadReadiness.BLOCKED_ACKNOWLEDGEMENT,
            OptionalSolverPluginManifestReloadState.ACKNOWLEDGEMENT_REVIEW_REQUIRED,
        )
    if any(row.requires_future_activation_review for row in candidates):
        return (
            OptionalSolverPluginManifestReloadReadiness.FUTURE_ACTIVATION_REVIEW_REQUIRED,
            OptionalSolverPluginManifestReloadState.FUTURE_ACTIVATION_REVIEW_REQUIRED,
        )
    if any(row.requires_future_discovery_refresh for row in candidates):
        return (
            OptionalSolverPluginManifestReloadReadiness.FUTURE_DISCOVERY_REFRESH_REQUIRED,
            OptionalSolverPluginManifestReloadState.FUTURE_DISCOVERY_REFRESH_REQUIRED,
        )
    if explicit_error:
        return (
            OptionalSolverPluginManifestReloadReadiness.ERROR,
            OptionalSolverPluginManifestReloadState.RELOAD_ERROR,
        )
    return (
        OptionalSolverPluginManifestReloadReadiness.READY_REVIEW_ONLY,
        OptionalSolverPluginManifestReloadState.RELOAD_PREVIEW_READY,
    )


def _diagnostics(
    *,
    readiness: OptionalSolverPluginManifestReloadReadiness,
    state: OptionalSolverPluginManifestReloadState,
    sources: Sequence[OptionalSolverPluginManifestReloadSourceRow],
    acks: Sequence[OptionalSolverPluginManifestReloadAcknowledgementRow],
    stale_rows: Sequence[OptionalSolverPluginManifestReloadStaleSourceRow],
    conflict_rows: Sequence[OptionalSolverPluginManifestReloadConflictRow],
    unsafe_rows: Sequence[OptionalSolverPluginManifestReloadUnsafeClaimRow],
    evidence_rows: Sequence[OptionalSolverPluginManifestReloadEvidenceRow],
    redaction_rows: Sequence[OptionalSolverPluginManifestReloadRedactionRow],
    payload_kind: str,
    payload_schema_version: str,
    payload: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestReloadDiagnostic, ...]:
    rows: list[OptionalSolverPluginManifestReloadDiagnostic] = []
    if readiness == OptionalSolverPluginManifestReloadReadiness.BLOCKED_PAYLOAD_KIND_MISMATCH:
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH,
                f"Unsupported payload kind: {payload_kind}.",
                blocker=True,
            )
        )
    if readiness == OptionalSolverPluginManifestReloadReadiness.BLOCKED_SCHEMA_VERSION_MISSING:
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED,
                "Payload schema version is required before reload review.",
                blocker=True,
            )
        )
    if readiness == OptionalSolverPluginManifestReloadReadiness.BLOCKED_SCHEMA_UNSUPPORTED:
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_SCHEMA_UNSUPPORTED,
                f"Unsupported payload schema version: {payload_schema_version}.",
                blocker=True,
            )
        )
    if readiness == OptionalSolverPluginManifestReloadReadiness.BLOCKED_SCHEMA_MIGRATION_REQUIRED:
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED,
                "Payload requires a separate schema migration gate.",
                blocker=True,
            )
        )
    if any(row.redaction_review_required for row in redaction_rows):
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_REDACTION_REQUIRED,
                "Redaction review is required before reload review can proceed.",
                blocker=True,
            )
        )
    if any(row.unredacted_path_blocked for row in redaction_rows):
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED,
                "Unredacted path references are blocked.",
                blocker=True,
            )
        )
    if any(row.secret_like_content_blocked for row in redaction_rows) or _secret_like(
        payload
    ):
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED,
                "Secret-like content is blocked.",
                blocker=True,
            )
        )
    for row in acks:
        if row.expired:
            rows.append(
                _diagnostic(
                    "error",
                    OSPMG_RELOAD_ACK_EXPIRED,
                    f"Acknowledgement expired: {row.acknowledgement_id}.",
                    blocker=True,
                    related=row.acknowledgement_id,
                )
            )
        elif row.blocker:
            rows.append(
                _diagnostic(
                    "error",
                    OSPMG_RELOAD_ACK_REQUIRED,
                    f"Acknowledgement required: {row.acknowledgement_id}.",
                    blocker=True,
                    related=row.acknowledgement_id,
                )
            )
    if any(row.repreview_required for row in stale_rows):
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED,
                "Stale sources require re-preview; this is not validation failure.",
                blocker=True,
            )
        )
    if any(not row.built_ins_authoritative_by_default for row in sources):
        rows.append(
            _diagnostic(
                "info",
                OSPMG_RELOAD_UNTRUSTED_SOURCE,
                "User/plugin sources remain untrusted by default.",
            )
        )
    if any(row.blocker for row in conflict_rows):
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_CONFLICT_VISIBLE,
                "Conflicts remain visible and unresolved by reload.",
                blocker=True,
            )
        )
    if any(row.shared_stack_warning_visible for row in conflict_rows):
        rows.append(
            _diagnostic(
                "warning",
                OSPMG_RELOAD_SHARED_STACK_VISIBLE,
                "Shared-stack warnings remain visible.",
                blocker=readiness
                == OptionalSolverPluginManifestReloadReadiness.BLOCKED_SHARED_STACK_WARNING,
            )
        )
    if any(row.blocked for row in unsafe_rows):
        rows.append(
            _diagnostic(
                "error",
                OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED,
                "Unsafe claims are visible but blocked from being reloaded as truth.",
                blocker=True,
            )
        )
    if evidence_rows:
        rows.append(
            _diagnostic(
                "info",
                OSPMG_RELOAD_EVIDENCE_RETAINED,
                "Historical evidence is retained as reference only.",
            )
        )
        rows.append(
            _diagnostic(
                "info",
                OSPMG_RELOAD_HISTORY_RETAINED,
                "Deactivation/reactivation history is retained.",
            )
        )
    rows.extend(
        _diagnostic("info", code, _diagnostic_message(code))
        for code in _BOUNDARY_DIAGNOSTICS
    )
    if state == OptionalSolverPluginManifestReloadState.RELOAD_PREVIEW_READY:
        rows.append(
            _diagnostic(
                "info",
                OSPMG_RELOAD_DESIGN_ONLY,
                "Reload view-model is ready for review only.",
            )
        )
    return tuple(rows)


def _action_states() -> tuple[OptionalSolverPluginManifestReloadActionState, ...]:
    return tuple(
        OptionalSolverPluginManifestReloadActionState(
            action=action,
            reason=_action_reason(action),
        )
        for action in OptionalSolverPluginManifestReloadAction
    )


def _candidate_review_state(lifecycle: str) -> tuple[str, bool, bool]:
    if lifecycle in {"active", "persisted_active", "reactivation"}:
        return ("future_activation_review_required", True, False)
    if lifecycle in {"discovery_refresh", "discovery-refresh"}:
        return ("future_discovery_refresh_required", False, True)
    if lifecycle == "deactivated":
        return ("deactivated_review_state", False, False)
    return ("review_only", False, False)


def _display_from_label(source_label: str | None) -> tuple[str, bool]:
    raw = _text(source_label).strip()
    if not raw:
        return ("caller-supplied mapping", True)
    normalized = raw.replace("\\", "/").rstrip("/")
    if "/" in normalized:
        leaf = normalized.rsplit("/", 1)[-1] or "<redacted-source>"
        return (leaf, True)
    if ":" in normalized or "$" in normalized or "%" in normalized:
        return ("<redacted-source>", True)
    return (normalized, False)


def _migration_required(payload: Mapping[str, object]) -> bool:
    if bool(payload.get("schema_migration_required", False)):
        return True
    for row in _iter_mappings(payload.get("schema_migration")):
        if bool(row.get("migration_required", False)):
            return True
    return False


def _trust_label(source_type: str) -> str:
    return "built_in_authoritative" if source_type == "built_in" else "untrusted_user_source"


def _is_built_in(source_type: str, trust_label: str) -> bool:
    return source_type in {"built_in", "builtin"} or "built_in" in trust_label


def _classify_claim(text: str) -> str:
    lowered = text.lower()
    if "validation success" in lowered or "validation pass" in lowered:
        return "validation_success"
    if "validation failure" in lowered or "validation fail" in lowered:
        return "validation_failure"
    if "issue" in lowered and "clos" in lowered:
        return "issue_closure"
    if "release" in lowered:
        return "release_mutation"
    if "bundle" in lowered and "solver" in lowered:
        return "bundled_solver"
    if "install" in lowered:
        return "dependency_installation"
    if "execute" in lowered or "execution" in lowered or "solver run" in lowered:
        return "solver_execution"
    if "trust" in lowered:
        return "trust_restoration"
    if "certif" in lowered:
        return "certification"
    return "unsafe_claim"


def _secret_like(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_secret_like(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_secret_like(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in _SECRET_MARKERS)
    return False


def _iter_mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(item for item in value if isinstance(item, Mapping))
    return ()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(value)
    if value is None:
        return ()
    return (value,)


def _text(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _ack_label(ack_id: str) -> str:
    return ack_id.replace("_", " ")


def _diagnostic(
    severity: str,
    code: str,
    message: str,
    *,
    blocker: bool = False,
    related: str = "",
    suggested_fix: str = "",
) -> OptionalSolverPluginManifestReloadDiagnostic:
    return OptionalSolverPluginManifestReloadDiagnostic(
        severity=severity,
        code=code,
        message=message,
        blocker=blocker,
        related=related,
        suggested_fix=suggested_fix,
    )


def _diagnostic_message(code: str) -> str:
    return {
        OSPMG_RELOAD_NOT_VALIDATION: (
            "Reloaded manifest UX state is not validation evidence or failure."
        ),
        OSPMG_RELOAD_NOT_TRUST_RESTORE: (
            "Reload does not restore trust for user/plugin sources."
        ),
        OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION: (
            "Reload does not automatically activate candidates."
        ),
        OSPMG_RELOAD_NO_DISCOVERY_EXECUTION: (
            "Reload view-model does not run discovery."
        ),
        OSPMG_RELOAD_NO_PLUGIN_IMPORT: (
            "Reload view-model does not import plugin packages."
        ),
        OSPMG_RELOAD_NO_VALIDATION_EXECUTION: (
            "Reload view-model does not run validation."
        ),
        OSPMG_RELOAD_NO_SOLVER_EXECUTION: (
            "Reload view-model does not execute solvers."
        ),
        OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED: (
            "Reload view-model does not mutate ProjectSchema."
        ),
        OSPMG_RELOAD_FUTURE_GATE: (
            "File reader, GUI, CLI, activation, and discovery-refresh behavior "
            "remain future-gated."
        ),
    }.get(code, code)


def _action_reason(action: OptionalSolverPluginManifestReloadAction) -> str:
    return {
        OptionalSolverPluginManifestReloadAction.READ_RELOAD_FILE: (
            "Reading persisted state files requires a future file-reader gate."
        ),
        OptionalSolverPluginManifestReloadAction.PARSE_RELOAD_FILE: (
            "Parsing persisted state files requires a future file-reader gate."
        ),
        OptionalSolverPluginManifestReloadAction.MIGRATE_SCHEMA: (
            "Schema migration requires a separate migration gate."
        ),
        OptionalSolverPluginManifestReloadAction.ACCEPT_RELOAD_AS_TRUSTED: (
            "Reloaded state is not trust restoration."
        ),
        OptionalSolverPluginManifestReloadAction.ACTIVATE_RELOADED_CANDIDATE: (
            "Activation after reload requires a future activation review gate."
        ),
        OptionalSolverPluginManifestReloadAction.REFRESH_DISCOVERY: (
            "Discovery refresh remains a separate future gate."
        ),
        OptionalSolverPluginManifestReloadAction.VALIDATE_SOLVER: (
            "Validation execution remains out of scope."
        ),
        OptionalSolverPluginManifestReloadAction.EXECUTE_SOLVER: (
            "Solver execution remains out of scope."
        ),
        OptionalSolverPluginManifestReloadAction.INSTALL_DEPENDENCY: (
            "Dependency installation remains out of scope."
        ),
        OptionalSolverPluginManifestReloadAction.UNINSTALL_DEPENDENCY: (
            "Dependency uninstall remains out of scope."
        ),
        OptionalSolverPluginManifestReloadAction.UNINSTALL_SOLVER: (
            "Solver uninstall remains out of scope."
        ),
        OptionalSolverPluginManifestReloadAction.MUTATE_PROJECT_SCHEMA: (
            "ProjectSchema mutation requires a separate gate."
        ),
        OptionalSolverPluginManifestReloadAction.CREATE_EXPORT_SUMMARY: (
            "Export-summary creation remains separate from reload."
        ),
        OptionalSolverPluginManifestReloadAction.CREATE_REPORT_FILE: (
            "Report output requires a separate report gate."
        ),
        OptionalSolverPluginManifestReloadAction.CREATE_RELOADABLE_BUNDLE: (
            "Reloadable bundles remain future-gated."
        ),
        OptionalSolverPluginManifestReloadAction.COPY_TO_CLIPBOARD: (
            "Clipboard behavior remains future-gated."
        ),
        OptionalSolverPluginManifestReloadAction.ATTACH_TO_REPORT: (
            "Report attachment remains future-gated."
        ),
        OptionalSolverPluginManifestReloadAction.OPEN_OUTPUT_FOLDER: (
            "Open-output-folder behavior remains future-gated."
        ),
        OptionalSolverPluginManifestReloadAction.CLOSE_ISSUE: (
            "Issue closure requires a separate validation/issue gate."
        ),
        OptionalSolverPluginManifestReloadAction.MUTATE_RELEASE: (
            "Release mutation requires a release gate."
        ),
        OptionalSolverPluginManifestReloadAction.PUSH_TAG: (
            "Tag mutation requires a release gate."
        ),
        OptionalSolverPluginManifestReloadAction.UPLOAD_ASSET: (
            "Asset mutation requires a release gate."
        ),
        OptionalSolverPluginManifestReloadAction.CLAIM_VALIDATION_SUCCESS_FAILURE: (
            "Reload diagnostics do not claim validation success or failure."
        ),
        OptionalSolverPluginManifestReloadAction.CLAIM_CERTIFICATION: (
            "Trust labels are not certification."
        ),
    }[action]


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


def _safety_text() -> tuple[str, ...]:
    return (
        "Reloaded manifest UX state is not validation evidence.",
        "Reloaded manifest UX state is not validation failure.",
        "Reload does not restore trust.",
        "Reload does not automatically activate candidates.",
        "Reload does not run discovery.",
        "Reload does not import plugin packages.",
        "Reload does not run validation.",
        "Reload does not execute solvers.",
        "Reload does not mutate ProjectSchema.",
        "Reload does not close issues or mutate releases.",
        "Reload does not certify manifests.",
        "Issues #6 through #11 remain live optional validation issues.",
    )


def _sample_payload() -> dict[str, object]:
    return {
        "payload_kind": STATE_WRITER_PAYLOAD_KIND,
        "payload_schema_version": STATE_WRITER_PAYLOAD_SCHEMA_VERSION,
        "writer_version": "osw-exp-102",
        "sources": [
            {
                "source_id": "sample-source",
                "source_type": "user_selected_state",
                "source_reference_display": "sample.json",
                "source_reference_redacted": True,
                "trust_label": "untrusted_user_source",
            }
        ],
        "candidates": [
            {
                "candidate_id": "sample-candidate",
                "display_name": "Sample optional solver",
                "lifecycle_state": "inactive",
                "source_type": "user",
            }
        ],
        "acknowledgements": [
            {
                "acknowledgement_id": ack,
                "satisfied": True,
                "expired": False,
                "expiry_reasons": RELOAD_ACK_EXPIRY_REASONS,
            }
            for ack in RELOAD_REQUIRED_ACKS
        ],
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
                "evidence_id": "sample-history",
                "candidate_id": "sample-candidate",
                "evidence_type": "deactivation_history",
                "skipped_missing_remains_skipped_missing": True,
            }
        ],
    }


__all__ = [
    "ACK_ACTIVATION_REVIEW_REQUIRED_AFTER_RELOAD",
    "ACK_NO_DISCOVERY_EXECUTION",
    "ACK_NO_PLUGIN_PACKAGE_IMPORT",
    "ACK_NO_SOLVER_EXECUTION",
    "ACK_NO_VALIDATION_EXECUTION",
    "ACK_PERSISTED_ACKNOWLEDGEMENTS_MAY_EXPIRE",
    "ACK_REDACTION_REVIEWED",
    "ACK_RELOAD_NO_SOLVER_EXECUTION",
    "ACK_RELOAD_NOT_AUTOMATIC_ACTIVATION",
    "ACK_RELOAD_NOT_CERTIFICATION",
    "ACK_RELOAD_NOT_DEPENDENCY_INSTALL",
    "ACK_RELOAD_NOT_DISCOVERY_SUCCESS",
    "ACK_RELOAD_NOT_ISSUE_CLOSURE",
    "ACK_RELOAD_NOT_RELEASE_MUTATION",
    "ACK_RELOAD_NOT_TRUST_RESTORATION",
    "ACK_RELOAD_NOT_VALIDATION",
    "ACK_STALE_SOURCE_REQUIRES_REPREVIEW",
    "ACK_TRUST_LABEL_NOT_CERTIFICATION",
    "ACK_UNREDACTED_PATHS_BLOCKED",
    "ACK_UNTRUSTED_SOURCE_REMAINS_UNTRUSTED",
    "OSPMG_RELOAD_ACK_EXPIRED",
    "OSPMG_RELOAD_ACK_REQUIRED",
    "OSPMG_RELOAD_CONFLICT_VISIBLE",
    "OSPMG_RELOAD_DESIGN_ONLY",
    "OSPMG_RELOAD_DIAGNOSTIC_CODES",
    "OSPMG_RELOAD_EVIDENCE_RETAINED",
    "OSPMG_RELOAD_FUTURE_GATE",
    "OSPMG_RELOAD_HISTORY_RETAINED",
    "OSPMG_RELOAD_NO_DISCOVERY_EXECUTION",
    "OSPMG_RELOAD_NO_PLUGIN_IMPORT",
    "OSPMG_RELOAD_NO_SOLVER_EXECUTION",
    "OSPMG_RELOAD_NO_VALIDATION_EXECUTION",
    "OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION",
    "OSPMG_RELOAD_NOT_IMPLEMENTED",
    "OSPMG_RELOAD_NOT_TRUST_RESTORE",
    "OSPMG_RELOAD_NOT_VALIDATION",
    "OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH",
    "OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED",
    "OSPMG_RELOAD_REDACTION_REQUIRED",
    "OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED",
    "OSPMG_RELOAD_SCHEMA_UNSUPPORTED",
    "OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED",
    "OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED",
    "OSPMG_RELOAD_SHARED_STACK_VISIBLE",
    "OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED",
    "OSPMG_RELOAD_TARGET_IS_DIRECTORY",
    "OSPMG_RELOAD_TARGET_MISSING",
    "OSPMG_RELOAD_TARGET_REQUIRED",
    "OSPMG_RELOAD_TARGET_SYMLINK_REVIEW_REQUIRED",
    "OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED",
    "OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED",
    "OSPMG_RELOAD_UNTRUSTED_SOURCE",
    "RELOAD_ACK_EXPIRY_REASONS",
    "RELOAD_REQUIRED_ACKS",
    "RELOAD_VIEWMODEL_VERSION",
    "STATE_WRITER_PAYLOAD_KIND",
    "STATE_WRITER_PAYLOAD_SCHEMA_VERSION",
    "OptionalSolverPluginManifestReloadAcknowledgementRow",
    "OptionalSolverPluginManifestReloadAction",
    "OptionalSolverPluginManifestReloadActionState",
    "OptionalSolverPluginManifestReloadCandidateRow",
    "OptionalSolverPluginManifestReloadConflictRow",
    "OptionalSolverPluginManifestReloadDiagnostic",
    "OptionalSolverPluginManifestReloadEvidenceRow",
    "OptionalSolverPluginManifestReloadInput",
    "OptionalSolverPluginManifestReloadReadiness",
    "OptionalSolverPluginManifestReloadRedactionRow",
    "OptionalSolverPluginManifestReloadSchemaRow",
    "OptionalSolverPluginManifestReloadSourceRow",
    "OptionalSolverPluginManifestReloadStaleSourceRow",
    "OptionalSolverPluginManifestReloadState",
    "OptionalSolverPluginManifestReloadSummary",
    "OptionalSolverPluginManifestReloadUnsafeClaimRow",
    "OptionalSolverPluginManifestReloadViewModel",
    "blocked",
    "build_optional_solver_plugin_manifest_reload_viewmodel",
    "empty",
    "from_payload_mapping",
    "from_state_writer_payload",
    "render_optional_solver_plugin_manifest_reload_viewmodel",
    "sample_ready_for_review",
    "unavailable",
]
