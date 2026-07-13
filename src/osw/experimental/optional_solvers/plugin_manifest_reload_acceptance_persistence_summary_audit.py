"""Supplied-record summary audit for reload acceptance persistence.

This OSW-EXP-136 module renders a deterministic, non-authoritative audit over
already-built in-memory records from the reload acceptance persistence chain.
It performs no file IO, invokes no writer or reader, imports no CLI or GUI
code, uses no process bridge, does not mutate ProjectSchema, and never creates
runtime acceptance, validation evidence, activation, trust restoration, or
release/issue claims.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from enum import Enum

RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_VERSION = "osw-exp-136"
RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_SCHEMA_ID = (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit"
)
RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_SCHEMA_VERSION = (
    "osw-exp-136-summary-audit-1"
)
RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_PAYLOAD_KIND = (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit"
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

RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS: tuple[str, ...] = (
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

RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRY_REASONS: tuple[str, ...] = (
    "reload",
    "target_change",
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
    "persistence_cli_policy_change",
    "persistence_gui_policy_change",
    "writer_policy_change",
    "summary_audit_policy_change",
)

OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNAVAILABLE = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNAVAILABLE"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_INPUT_MISSING = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_INPUT_MISSING"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CHAIN_INCOMPLETE = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CHAIN_INCOMPLETE"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_WRITE_RECORD_MISSING = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_WRITE_RECORD_MISSING"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ACK_REQUIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ACK_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_STALE_SOURCE = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_STALE_SOURCE"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CONFLICT_VISIBLE = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CONFLICT_VISIBLE"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNSAFE_CLAIM_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNSAFE_CLAIM_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_VALIDATION_CLAIM = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_VALIDATION_CLAIM"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_PROJECT_SCHEMA_MUTATION = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_PROJECT_SCHEMA_MUTATION"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_READY_FOR_PREPARED_MACHINE_REVIEW = (  # noqa: E501
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_READY_FOR_PREPARED_MACHINE_REVIEW"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ERROR = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ERROR"
)

OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_DIAGNOSTIC_CODES: tuple[
    str, ...
] = (
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNAVAILABLE,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_INPUT_MISSING,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CHAIN_INCOMPLETE,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_WRITE_RECORD_MISSING,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ACK_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_STALE_SOURCE,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CONFLICT_VISIBLE,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNSAFE_CLAIM_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_VALIDATION_CLAIM,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_PROJECT_SCHEMA_MUTATION,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_READY_FOR_PREPARED_MACHINE_REVIEW,  # noqa: E501
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ERROR,
)


class ReloadAcceptancePersistenceSummaryAuditState(str, Enum):
    """Top-level supplied-record summary audit state."""

    UNAVAILABLE = "unavailable"
    NO_RECORDS_SUPPLIED = "no_records_supplied"
    CHAIN_INCOMPLETE = "chain_incomplete"
    RECORDS_SUPPLIED = "records_supplied"
    RECORDS_WITH_BLOCKERS = "records_with_blockers"
    READY_FOR_SUMMARY_REVIEW = "ready_for_summary_review"
    READY_FOR_PREPARED_MACHINE_REVIEW = "ready_for_prepared_machine_review"
    ERROR = "error"


class ReloadAcceptancePersistenceSummaryAuditReadiness(str, Enum):
    """Review-only readiness vocabulary."""

    UNAVAILABLE = "unavailable"
    NO_RECORDS_SUPPLIED = "no_records_supplied"
    CHAIN_INCOMPLETE = "chain_incomplete"
    RECORDS_SUPPLIED = "records_supplied"
    RECORDS_WITH_BLOCKERS = "records_with_blockers"
    READY_FOR_SUMMARY_REVIEW = "ready_for_summary_review"
    READY_FOR_PREPARED_MACHINE_REVIEW = "ready_for_prepared_machine_review"
    ERROR = "error"


class ReloadAcceptancePersistenceSummaryAuditAction(str, Enum):
    """Disabled or future-only actions visible in the audit."""

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
class ReloadAcceptancePersistenceSummaryAuditDiagnostic:
    """One summary audit diagnostic row."""

    code: str
    severity: str
    message: str
    section: str = "summary_audit"
    blocker: bool = False
    supplied_only: bool = False
    not_truth_claim: bool = True
    suggested_fix: str = ""

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceSummaryAuditRow:
    """Generic deterministic audit row."""

    row_id: str
    label: str
    value: object = ""
    status: str = "review_only"
    guidance: str = ""
    non_authoritative: bool = True

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceSummaryAuditSection:
    """Named summary audit section."""

    section_id: str
    title: str
    rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceSummaryAuditGateRecord:
    """Expected or supplied chain gate record."""

    gate_id: str
    title: str
    artifact_type: str
    implementation_status: str
    evidence_type: str
    safety_summary: str
    non_authoritative_caveat: str
    future_gate: str = ""
    supplied: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceSummaryAuditWriteSummary:
    """Non-authoritative summary of one supplied writer/CLI/GUI write record."""

    source_surface: str
    supplied: bool
    status: str = "not_supplied"
    target_display: str = ""
    dry_run_sha256: str = ""
    final_write_sha256: str = ""
    payload_kind: str = ""
    payload_schema_version: str = ""
    bytes_count: int = 0
    persistence_write_performed: bool = False
    acknowledgement_state: str = "not_supplied"
    replace_policy: str = "not_supplied"
    cleanup_state: str = "not_supplied"
    diagnostics: tuple[Mapping[str, object], ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    local_review_record_only: bool = True
    write_implies_runtime_acceptance: bool = False
    write_implies_validation_evidence: bool = False
    write_implies_validation_failure: bool = False
    write_implies_project_schema_mutation: bool = False
    write_implies_trust_restoration: bool = False
    write_implies_activation: bool = False
    write_implies_issue_closure: bool = False
    write_implies_release_mutation: bool = False
    write_implies_certification: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceSummaryAuditActionRow:
    """Disabled/future-only action row."""

    action: ReloadAcceptancePersistenceSummaryAuditAction
    enabled: bool = False
    future_only: bool = True
    reason: str = "Requires a separate future gate."

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceSummaryAuditNonActionFlags:
    """False flags for behavior this audit never performs."""

    file_writing_performed: bool = False
    file_reading_performed: bool = False
    file_parsing_performed: bool = False
    input_state_file_reading_performed: bool = False
    input_state_file_parsing_performed: bool = False
    writer_invoked: bool = False
    reload_file_reader_invoked: bool = False
    state_writer_invoked: bool = False
    cli_called: bool = False
    gui_called: bool = False
    subprocess_used: bool = False
    runtime_reload_acceptance_performed: bool = False
    active_acceptance_mutation_performed: bool = False
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
class ReloadAcceptancePersistenceSummaryAuditSummary:
    """Top-level review summary."""

    state: ReloadAcceptancePersistenceSummaryAuditState
    readiness: ReloadAcceptancePersistenceSummaryAuditReadiness
    records_supplied: bool
    chain_complete: bool
    chain_gate_count: int
    missing_gate_ids: tuple[str, ...] = ()
    persistence_viewmodel_supplied: bool = False
    writer_record_supplied: bool = False
    cli_write_record_supplied: bool = False
    gui_write_record_supplied: bool = False
    issue_snapshot_supplied: bool = False
    prepared_machine_validation_supplied: bool = False
    non_authoritative: bool = True
    supplied_record_only: bool = True
    local_review_state_only: bool = True
    summary_is_runtime_acceptance: bool = False
    summary_is_validation_evidence: bool = False
    summary_is_validation_failure: bool = False
    summary_is_project_schema_state: bool = False
    summary_restores_trust: bool = False
    summary_activates_candidate: bool = False
    summary_closes_issue: bool = False
    summary_mutates_release: bool = False
    summary_certifies_manifest: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
    """Pure supplied-record summary/audit model."""

    summary: ReloadAcceptancePersistenceSummaryAuditSummary
    chain_gate_records: tuple[
        ReloadAcceptancePersistenceSummaryAuditGateRecord, ...
    ]
    persistence_viewmodel_summary: Mapping[str, object]
    writer_summary: ReloadAcceptancePersistenceSummaryAuditWriteSummary
    cli_write_summary: ReloadAcceptancePersistenceSummaryAuditWriteSummary
    gui_write_summary: ReloadAcceptancePersistenceSummaryAuditWriteSummary
    acknowledgement_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]
    expiry_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]
    target_storage_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]
    schema_migration_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]
    redaction_privacy_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]
    provenance_trust_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]
    stale_source_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]
    conflict_shared_stack_rows: tuple[
        ReloadAcceptancePersistenceSummaryAuditRow, ...
    ]
    unsafe_claim_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]
    evidence_history_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]
    lower_level_diagnostics: tuple[Mapping[str, object], ...]
    diagnostics: tuple[ReloadAcceptancePersistenceSummaryAuditDiagnostic, ...]
    non_action_flags: ReloadAcceptancePersistenceSummaryAuditNonActionFlags
    disabled_future_actions: tuple[
        ReloadAcceptancePersistenceSummaryAuditActionRow, ...
    ]
    issue_state_rows: tuple[Mapping[str, object], ...]
    prepared_machine_validation: Mapping[str, object]
    limitations: tuple[str, ...]
    safety_text: tuple[str, ...]

    @classmethod
    def unavailable(
        cls,
        reason: str = "Summary audit records are unavailable.",
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
        """Return a deterministic unavailable audit."""

        return cls.from_records(unavailable_reason=reason)

    @classmethod
    def from_records(
        cls,
        *,
        persistence_viewmodel_mapping: object | None = None,
        writer_result_mapping: object | None = None,
        cli_write_result_mapping: object | None = None,
        gui_write_result_mapping: object | None = None,
        chain_gate_records: object | None = None,
        issue_state_snapshot: object | None = None,
        prepared_machine_validation_snapshot: object | None = None,
        limitations: Sequence[str] = (),
        diagnostics: object | None = None,
        unavailable_reason: str = "",
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
        """Build a review-only summary from supplied in-memory records."""

        return build_optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit(
            persistence_viewmodel_mapping=persistence_viewmodel_mapping,
            writer_result_mapping=writer_result_mapping,
            cli_write_result_mapping=cli_write_result_mapping,
            gui_write_result_mapping=gui_write_result_mapping,
            chain_gate_records=chain_gate_records,
            issue_state_snapshot=issue_state_snapshot,
            prepared_machine_validation_snapshot=(
                prepared_machine_validation_snapshot
            ),
            limitations=limitations,
            diagnostics=diagnostics,
            unavailable_reason=unavailable_reason,
        )

    @classmethod
    def from_mappings(
        cls,
        *,
        persistence_viewmodel_mapping: Mapping[str, object] | None = None,
        writer_result_mapping: Mapping[str, object] | None = None,
        cli_write_result_mapping: Mapping[str, object] | None = None,
        gui_write_result_mapping: Mapping[str, object] | None = None,
        chain_gate_records: Sequence[Mapping[str, object]] | None = None,
        issue_state_snapshot: Mapping[str, object] | None = None,
        prepared_machine_validation_snapshot: Mapping[str, object] | None = None,
        limitations: Sequence[str] = (),
        diagnostics: Sequence[Mapping[str, object]] = (),
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
        """Build from safe already-built mappings."""

        return cls.from_records(
            persistence_viewmodel_mapping=persistence_viewmodel_mapping,
            writer_result_mapping=writer_result_mapping,
            cli_write_result_mapping=cli_write_result_mapping,
            gui_write_result_mapping=gui_write_result_mapping,
            chain_gate_records=chain_gate_records,
            issue_state_snapshot=issue_state_snapshot,
            prepared_machine_validation_snapshot=(
                prepared_machine_validation_snapshot
            ),
            limitations=limitations,
            diagnostics=diagnostics,
        )

    @classmethod
    def sample(cls) -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
        """Return deterministic supplied sample records for tests and docs."""

        persistence = {
            "summary": {
                "state": "persistence_ready_future_only",
                "readiness": "writer_future_only",
                "ready_for_future_write_plan": True,
                "persistence_readiness_is_validation_evidence": False,
                "persistence_readiness_is_validation_failure": False,
                "persistence_readiness_mutates_project_schema": False,
            },
            "acknowledgements": [
                {"acknowledgement_id": ack, "satisfied": True, "expired": False}
                for ack in RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS
            ],
            "diagnostics": [
                {
                    "severity": "info",
                    "code": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_READY",
                    "message": "Supplied persistence view-model is ready.",
                    "section": "persistence",
                    "blocker": False,
                }
            ],
            "non_action_flags": (
                ReloadAcceptancePersistenceSummaryAuditNonActionFlags().to_mapping()
            ),
            "safety_text": list(_safety_text()),
        }
        writer = _sample_write_record("writer")
        cli = {
            "status": "completed",
            "source_surface": "CLI",
            "target_display": "reload-acceptance-state.json",
            "dry_run_plan": _sample_write_record("cli_dry_run", dry_run=True),
            "writer_result": _sample_write_record("cli", completed=True),
            "diagnostics": [
                {
                    "severity": "info",
                    "code": (
                        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_"
                        "COMPLETED_LOCAL_ONLY"
                    ),
                    "message": "CLI write completed local review-record only.",
                    "section": "cli_write",
                    "blocker": False,
                }
            ],
            "persistence_write_performed": True,
        }
        gui = _sample_write_record("gui", completed=True)
        return cls.from_records(
            persistence_viewmodel_mapping=persistence,
            writer_result_mapping=writer,
            cli_write_result_mapping=cli,
            gui_write_result_mapping=gui,
            chain_gate_records=[row.to_mapping() for row in _expected_gate_records()],
            issue_state_snapshot={str(issue): "open" for issue in range(6, 12)},
            limitations=("Summary audit is supplied-record-only.",),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""

        return {
            "payload_kind": RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_PAYLOAD_KIND,
            "payload_schema_version": (
                RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_SCHEMA_VERSION
            ),
            "summary_audit_version": (
                RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_VERSION
            ),
            "summary": self.summary.to_mapping(),
            "chain_coverage": [
                row.to_mapping() for row in self.chain_gate_records
            ],
            "persistence_viewmodel_summary": dict(
                self.persistence_viewmodel_summary
            ),
            "writer_summary": self.writer_summary.to_mapping(),
            "cli_write_summary": self.cli_write_summary.to_mapping(),
            "gui_write_summary": self.gui_write_summary.to_mapping(),
            "acknowledgements": [
                row.to_mapping() for row in self.acknowledgement_rows
            ],
            "expiry": [row.to_mapping() for row in self.expiry_rows],
            "target_storage_policy": [
                row.to_mapping() for row in self.target_storage_rows
            ],
            "schema_migration": [
                row.to_mapping() for row in self.schema_migration_rows
            ],
            "redaction_privacy": [
                row.to_mapping() for row in self.redaction_privacy_rows
            ],
            "provenance_trust": [
                row.to_mapping() for row in self.provenance_trust_rows
            ],
            "stale_source_repreview": [
                row.to_mapping() for row in self.stale_source_rows
            ],
            "conflict_shared_stack": [
                row.to_mapping() for row in self.conflict_shared_stack_rows
            ],
            "unsafe_claims": [
                row.to_mapping() for row in self.unsafe_claim_rows
            ],
            "evidence_history": [
                row.to_mapping() for row in self.evidence_history_rows
            ],
            "lower_level_diagnostics": [
                dict(row) for row in self.lower_level_diagnostics
            ],
            "diagnostics": [row.to_mapping() for row in self.diagnostics],
            "non_action_flags": self.non_action_flags.to_mapping(),
            "disabled_future_actions": [
                row.to_mapping() for row in self.disabled_future_actions
            ],
            "issue_state_separation": [dict(row) for row in self.issue_state_rows],
            "prepared_machine_validation": dict(
                self.prepared_machine_validation
            ),
            "limitations": list(self.limitations),
            "safety_text": list(self.safety_text),
            "reserved_diagnostic_codes": list(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_DIAGNOSTIC_CODES
            ),
            "required_acknowledgements": list(
                RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS
            ),
            "expiry_reasons": list(
                RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRY_REASONS
            ),
        }

    def to_text_lines(self) -> tuple[str, ...]:
        """Render stable plain-text audit lines."""

        lines = [
            (
                "Optional Solver Plugin Manifest Reload Acceptance "
                "Persistence Summary Audit"
            ),
            f"state: {self.summary.state.value}",
            f"readiness: {self.summary.readiness.value}",
            f"records_supplied: {self.summary.records_supplied}",
            f"chain_complete: {self.summary.chain_complete}",
            (
                "policy: supplied-record-only, pure in-memory, "
                "non-authoritative, local review-state only"
            ),
            (
                "safety: summary audit is not runtime reload acceptance, "
                "not validation evidence, and not validation failure"
            ),
            (
                "safety: summary audit does not mutate ProjectSchema, restore "
                "trust, activate candidates, close issues, mutate releases, "
                "or certify manifests"
            ),
            (
                "target/storage: explicit target records only; no default "
                "target, no background write, no directory scan"
            ),
            (
                "schema: persistence schema is separate from ProjectSchema and "
                "mismatch is not validation failure"
            ),
            "evidence/history: skipped-missing remains skipped-missing",
        ]
        for gate in self.chain_gate_records:
            lines.append(
                "chain: "
                f"{gate.gate_id} status={gate.implementation_status} "
                f"supplied={gate.supplied}"
            )
        for write_summary in (
            self.writer_summary,
            self.cli_write_summary,
            self.gui_write_summary,
        ):
            lines.append(
                "write-summary: "
                f"{write_summary.source_surface} supplied={write_summary.supplied} "
                f"status={write_summary.status} "
                f"target={write_summary.target_display or 'not_supplied'} "
                "local-review-record-only=True"
            )
        for row in self.acknowledgement_rows:
            lines.append(
                f"acknowledgement: {row.row_id} value={row.value} "
                f"status={row.status}"
            )
        for row in self.expiry_rows:
            lines.append(f"expiry: {row.row_id} status={row.status}")
        for row in self.target_storage_rows:
            lines.append(f"target-storage: {row.row_id} value={row.value}")
        for row in self.schema_migration_rows:
            lines.append(f"schema-migration: {row.row_id} value={row.value}")
        for row in self.redaction_privacy_rows:
            lines.append(f"redaction-privacy: {row.row_id} value={row.value}")
        for row in self.provenance_trust_rows:
            lines.append(f"provenance-trust: {row.row_id} value={row.value}")
        for row in self.stale_source_rows:
            lines.append(f"stale-source: {row.row_id} value={row.value}")
        for row in self.conflict_shared_stack_rows:
            lines.append(f"conflict: {row.row_id} value={row.value}")
        for row in self.unsafe_claim_rows:
            lines.append(f"unsafe-claim: {row.row_id} value={row.value}")
        for row in self.evidence_history_rows:
            lines.append(f"evidence-history: {row.row_id} value={row.value}")
        for diagnostic in self.diagnostics:
            lines.append(f"diagnostic: {diagnostic.severity} {diagnostic.code}")
        for row in self.lower_level_diagnostics:
            lines.append(
                "lower-level-diagnostic: "
                f"{row.get('source', '')} {row.get('severity', '')} "
                f"{row.get('code', '')} supplied-only"
            )
        for action in self.disabled_future_actions:
            lines.append(f"action: {action.action.value} enabled={action.enabled}")
        for issue in self.issue_state_rows:
            lines.append(
                f"issue: #{issue.get('issue_number')} "
                f"state={issue.get('state')} mutation_performed=False"
            )
        lines.append(
            "prepared-machine-validation: "
            f"status={self.prepared_machine_validation.get('status')} "
            "supplied-only future separate gate"
        )
        return tuple(lines)


def unavailable(
    reason: str = "Summary audit records are unavailable.",
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
    """Return an unavailable summary audit."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit.unavailable(
        reason
    )


def from_records(
    **kwargs: object,
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
    """Build a summary audit from supplied records."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit.from_records(
        **kwargs
    )


def from_mappings(
    **kwargs: object,
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
    """Build a summary audit from supplied mappings."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit.from_mappings(
        **kwargs
    )


def sample() -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
    """Return a deterministic sample summary audit."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit.sample()


def build_optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit(
    *,
    persistence_viewmodel_mapping: object | None = None,
    writer_result_mapping: object | None = None,
    cli_write_result_mapping: object | None = None,
    gui_write_result_mapping: object | None = None,
    chain_gate_records: object | None = None,
    issue_state_snapshot: object | None = None,
    prepared_machine_validation_snapshot: object | None = None,
    limitations: Sequence[str] = (),
    diagnostics: object | None = None,
    unavailable_reason: str = "",
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit:
    """Build the pure supplied-record summary audit without side effects."""

    persistence = _object_to_mapping(persistence_viewmodel_mapping)
    writer = _object_to_mapping(writer_result_mapping)
    cli = _object_to_mapping(cli_write_result_mapping)
    gui = _object_to_mapping(gui_write_result_mapping)
    chain_rows = _chain_gate_records(chain_gate_records)
    missing_gate_ids = tuple(row.gate_id for row in chain_rows if not row.supplied)
    chain_complete = not missing_gate_ids
    issues = _issue_rows(issue_state_snapshot)
    prepared = _prepared_machine_validation(prepared_machine_validation_snapshot)
    supplied_diagnostics = _diagnostic_rows(diagnostics, source="supplied")
    lower_diagnostics = (
        _diagnostic_rows(persistence, source="persistence_viewmodel")
        + _diagnostic_rows(writer, source="writer")
        + _diagnostic_rows(cli, source="cli_write")
        + _diagnostic_rows(gui, source="gui_write")
        + supplied_diagnostics
    )
    acknowledgement_rows = _acknowledgement_rows(persistence)
    expiry_rows = _expiry_rows()
    writer_summary = _write_summary("writer", writer)
    cli_summary = _write_summary("cli", cli)
    gui_summary = _write_summary("gui", gui)
    records_supplied = any(
        (
            bool(persistence),
            bool(writer),
            bool(cli),
            bool(gui),
            any(row.supplied for row in chain_rows),
            _object_to_mapping(issue_state_snapshot) != {},
            _object_to_mapping(prepared_machine_validation_snapshot) != {},
            bool(supplied_diagnostics),
            bool(limitations),
        )
    )
    audit_diagnostics = _summary_diagnostics(
        unavailable_reason=unavailable_reason,
        records_supplied=records_supplied,
        chain_complete=chain_complete,
        missing_gate_ids=missing_gate_ids,
        writer_supplied=bool(writer),
        cli_supplied=bool(cli),
        gui_supplied=bool(gui),
        acknowledgement_rows=acknowledgement_rows,
        lower_level_diagnostics=lower_diagnostics,
        prepared_machine_validation_supplied=prepared["supplied"],
    )
    state, readiness = _state_and_readiness(
        unavailable=bool(unavailable_reason),
        records_supplied=records_supplied,
        chain_complete=chain_complete,
        diagnostics=audit_diagnostics,
        prepared_machine_validation_supplied=prepared["supplied"],
    )
    summary = ReloadAcceptancePersistenceSummaryAuditSummary(
        state=state,
        readiness=readiness,
        records_supplied=records_supplied,
        chain_complete=chain_complete,
        chain_gate_count=len(chain_rows),
        missing_gate_ids=missing_gate_ids,
        persistence_viewmodel_supplied=bool(persistence),
        writer_record_supplied=bool(writer),
        cli_write_record_supplied=bool(cli),
        gui_write_record_supplied=bool(gui),
        issue_snapshot_supplied=_object_to_mapping(issue_state_snapshot) != {},
        prepared_machine_validation_supplied=prepared["supplied"],
    )
    safe_limitations = tuple(_safe_string(item) for item in limitations)
    return OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit(
        summary=summary,
        chain_gate_records=chain_rows,
        persistence_viewmodel_summary=_persistence_summary(persistence),
        writer_summary=writer_summary,
        cli_write_summary=cli_summary,
        gui_write_summary=gui_summary,
        acknowledgement_rows=acknowledgement_rows,
        expiry_rows=expiry_rows,
        target_storage_rows=_target_storage_rows(writer_summary, cli_summary, gui_summary),
        schema_migration_rows=_schema_migration_rows(persistence),
        redaction_privacy_rows=_redaction_privacy_rows(),
        provenance_trust_rows=_provenance_trust_rows(persistence),
        stale_source_rows=_stale_source_rows(),
        conflict_shared_stack_rows=_conflict_shared_stack_rows(),
        unsafe_claim_rows=_unsafe_claim_rows(),
        evidence_history_rows=_evidence_history_rows(persistence),
        lower_level_diagnostics=lower_diagnostics,
        diagnostics=audit_diagnostics,
        non_action_flags=ReloadAcceptancePersistenceSummaryAuditNonActionFlags(),
        disabled_future_actions=_action_rows(),
        issue_state_rows=issues,
        prepared_machine_validation=prepared,
        limitations=safe_limitations,
        safety_text=_safety_text(),
    )


def render_optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit(
    audit: OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit,
) -> tuple[str, ...]:
    """Render stable summary audit text."""

    return audit.to_text_lines()


def all_reload_acceptance_persistence_summary_audit_acknowledgements() -> tuple[
    str, ...
]:
    """Return required acknowledgement ids for the audit surface."""

    return RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS


def _expected_gate_records() -> tuple[
    ReloadAcceptancePersistenceSummaryAuditGateRecord, ...
]:
    rows = (
        ("OSW-EXP-124", "Reload acceptance persistence design", "design"),
        ("OSW-EXP-125", "Reload acceptance persistence view-model", "view-model"),
        ("OSW-EXP-126", "Reload acceptance persistence writer", "writer"),
        ("OSW-EXP-127", "Reload acceptance persistence CLI design", "design"),
        ("OSW-EXP-128", "Reload acceptance persistence CLI review", "CLI review"),
        ("OSW-EXP-129", "Reload acceptance persistence GUI review design", "design"),
        ("OSW-EXP-130", "Reload acceptance persistence GUI review", "GUI review"),
        ("OSW-EXP-131", "Reload acceptance persistence GUI write design", "design"),
        ("OSW-EXP-132", "Reload acceptance persistence GUI write", "GUI write"),
        ("OSW-EXP-133", "Reload acceptance persistence CLI write design", "design"),
        ("OSW-EXP-134", "Reload acceptance persistence CLI write", "CLI write"),
        ("OSW-EXP-135", "Persistence summary audit design", "design"),
        ("OSW-EXP-136", "Persistence summary audit implementation", "summary audit"),
    )
    design_gate_ids = {
        "OSW-EXP-124",
        "OSW-EXP-127",
        "OSW-EXP-129",
        "OSW-EXP-131",
        "OSW-EXP-133",
        "OSW-EXP-135",
    }
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditGateRecord(
            gate_id=gate_id,
            title=title,
            artifact_type=artifact_type,
            implementation_status=(
                "design" if gate_id in design_gate_ids else "implemented"
            ),
            evidence_type="supplied-record review slot",
            safety_summary=(
                "Non-authoritative chain context only; no runtime acceptance, "
                "validation, ProjectSchema, issue/release, or certification claim."
            ),
            non_authoritative_caveat=(
                "Chain coverage is review context, not validation evidence."
            ),
            future_gate=(
                "OSW-EXP-137" if gate_id == "OSW-EXP-136" else ""
            ),
        )
        for gate_id, title, artifact_type in rows
    )


def _chain_gate_records(
    supplied: object | None,
) -> tuple[ReloadAcceptancePersistenceSummaryAuditGateRecord, ...]:
    expected = _expected_gate_records()
    supplied_rows = {
        str(row.get("gate_id", "") or row.get("id", "")): row
        for row in _iter_mappings(supplied)
    }
    rows: list[ReloadAcceptancePersistenceSummaryAuditGateRecord] = []
    for expected_row in expected:
        row = supplied_rows.get(expected_row.gate_id)
        if row:
            rows.append(
                ReloadAcceptancePersistenceSummaryAuditGateRecord(
                    gate_id=expected_row.gate_id,
                    title=_safe_string(row.get("title", expected_row.title)),
                    artifact_type=_safe_string(
                        row.get("artifact_type", expected_row.artifact_type)
                    ),
                    implementation_status=_safe_string(
                        row.get(
                            "implementation_status",
                            expected_row.implementation_status,
                        )
                    ),
                    evidence_type=_safe_string(
                        row.get("evidence_type", expected_row.evidence_type)
                    ),
                    safety_summary=_safe_string(
                        row.get("safety_summary", expected_row.safety_summary)
                    ),
                    non_authoritative_caveat=_safe_string(
                        row.get(
                            "non_authoritative_caveat",
                            expected_row.non_authoritative_caveat,
                        )
                    ),
                    future_gate=_safe_string(
                        row.get("future_gate", expected_row.future_gate)
                    ),
                    supplied=True,
                )
            )
        else:
            rows.append(expected_row)
    return tuple(rows)


def _summary_diagnostics(
    *,
    unavailable_reason: str,
    records_supplied: bool,
    chain_complete: bool,
    missing_gate_ids: tuple[str, ...],
    writer_supplied: bool,
    cli_supplied: bool,
    gui_supplied: bool,
    acknowledgement_rows: tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...],
    lower_level_diagnostics: tuple[Mapping[str, object], ...],
    prepared_machine_validation_supplied: bool,
) -> tuple[ReloadAcceptancePersistenceSummaryAuditDiagnostic, ...]:
    rows: list[ReloadAcceptancePersistenceSummaryAuditDiagnostic] = []
    if unavailable_reason:
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNAVAILABLE,
                "error",
                _safe_string(unavailable_reason),
                blocker=True,
                suggested_fix="Supply in-memory records for summary review.",
            )
        )
    if not records_supplied:
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_INPUT_MISSING,
                "warning",
                "No supplied summary/audit records are available.",
                suggested_fix="Supply persistence, writer, CLI, or GUI records.",
            )
        )
    if not chain_complete:
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CHAIN_INCOMPLETE,
                "warning",
                "Chain gate records are incomplete: "
                + ", ".join(missing_gate_ids),
                suggested_fix="Supply chain records for OSW-EXP-124 through OSW-EXP-136.",
            )
        )
    if records_supplied and not any((writer_supplied, cli_supplied, gui_supplied)):
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_WRITE_RECORD_MISSING,
                "info",
                "No supplied writer, CLI write, or GUI write records are present.",
                suggested_fix="Supply write records if local review writes need review.",
            )
        )
    if any(row.status == "blocking" for row in acknowledgement_rows):
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ACK_REQUIRED,
                "warning",
                "Supplied acknowledgement rows include missing or expired items.",
                suggested_fix="Repeat acknowledgement review in a future gate.",
            )
        )
    if any(row.status == "expired" for row in acknowledgement_rows):
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRED,
                "warning",
                "Supplied acknowledgement expiry is visible.",
                suggested_fix="Re-review expired acknowledgements.",
            )
        )
    if any("STALE" in str(row.get("code", "")) for row in lower_level_diagnostics):
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_STALE_SOURCE,
                "warning",
                "Supplied lower-level diagnostics include stale-source state.",
                suggested_fix="Re-preview in a future gate.",
            )
        )
    if any("CONFLICT" in str(row.get("code", "")) for row in lower_level_diagnostics):
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CONFLICT_VISIBLE,
                "warning",
                "Supplied lower-level diagnostics include conflict state.",
                suggested_fix="Review conflicts; built-ins win by default.",
            )
        )
    if any("UNSAFE" in str(row.get("code", "")) for row in lower_level_diagnostics):
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNSAFE_CLAIM_BLOCKED,
                "error",
                "Supplied lower-level diagnostics include unsafe claims.",
                blocker=True,
                suggested_fix="Remove unsafe claims before future reliance.",
            )
        )
    rows.append(
        _diagnostic(
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_VALIDATION_CLAIM,
            "info",
            "Summary audit output makes no validation-pass or validation-fail claim.",
        )
    )
    rows.append(
        _diagnostic(
            OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_PROJECT_SCHEMA_MUTATION,
            "info",
            "Summary audit output performs no ProjectSchema mutation.",
        )
    )
    if prepared_machine_validation_supplied:
        rows.append(
            _diagnostic(
                OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_READY_FOR_PREPARED_MACHINE_REVIEW,
                "info",
                "Prepared-machine validation snapshot is supplied-only and separate.",
            )
        )
    return tuple(rows)


def _diagnostic(
    code: str,
    severity: str,
    message: str,
    *,
    blocker: bool = False,
    supplied_only: bool = False,
    suggested_fix: str = "",
) -> ReloadAcceptancePersistenceSummaryAuditDiagnostic:
    return ReloadAcceptancePersistenceSummaryAuditDiagnostic(
        code=code,
        severity=severity,
        message=message,
        blocker=blocker,
        supplied_only=supplied_only,
        suggested_fix=suggested_fix,
    )


def _state_and_readiness(
    *,
    unavailable: bool,
    records_supplied: bool,
    chain_complete: bool,
    diagnostics: tuple[ReloadAcceptancePersistenceSummaryAuditDiagnostic, ...],
    prepared_machine_validation_supplied: bool,
) -> tuple[
    ReloadAcceptancePersistenceSummaryAuditState,
    ReloadAcceptancePersistenceSummaryAuditReadiness,
]:
    if unavailable:
        return (
            ReloadAcceptancePersistenceSummaryAuditState.UNAVAILABLE,
            ReloadAcceptancePersistenceSummaryAuditReadiness.UNAVAILABLE,
        )
    if not records_supplied:
        return (
            ReloadAcceptancePersistenceSummaryAuditState.NO_RECORDS_SUPPLIED,
            ReloadAcceptancePersistenceSummaryAuditReadiness.NO_RECORDS_SUPPLIED,
        )
    if not chain_complete:
        return (
            ReloadAcceptancePersistenceSummaryAuditState.CHAIN_INCOMPLETE,
            ReloadAcceptancePersistenceSummaryAuditReadiness.CHAIN_INCOMPLETE,
        )
    if any(row.blocker for row in diagnostics):
        return (
            ReloadAcceptancePersistenceSummaryAuditState.RECORDS_WITH_BLOCKERS,
            ReloadAcceptancePersistenceSummaryAuditReadiness.RECORDS_WITH_BLOCKERS,
        )
    if prepared_machine_validation_supplied:
        return (
            ReloadAcceptancePersistenceSummaryAuditState.READY_FOR_PREPARED_MACHINE_REVIEW,
            ReloadAcceptancePersistenceSummaryAuditReadiness.READY_FOR_PREPARED_MACHINE_REVIEW,
        )
    return (
        ReloadAcceptancePersistenceSummaryAuditState.READY_FOR_SUMMARY_REVIEW,
        ReloadAcceptancePersistenceSummaryAuditReadiness.READY_FOR_SUMMARY_REVIEW,
    )


def _persistence_summary(mapping: Mapping[str, object]) -> dict[str, object]:
    summary = _mapping(mapping.get("summary"))
    return {
        "supplied": bool(mapping),
        "state": _safe_string(summary.get("state", "not_supplied")),
        "readiness": _safe_string(summary.get("readiness", "not_supplied")),
        "ready_for_future_write_plan": bool(
            summary.get("ready_for_future_write_plan", False)
        ),
        "local_review_state_only": True,
        "not_runtime_reload_acceptance": True,
        "not_validation_evidence": True,
        "not_validation_failure": True,
        "not_project_schema_state": True,
        "not_trust_restoration": True,
        "not_activation": True,
        "not_issue_closure": True,
        "not_release_mutation": True,
        "not_certification": True,
    }


def _write_summary(
    source_surface: str,
    mapping: Mapping[str, object],
) -> ReloadAcceptancePersistenceSummaryAuditWriteSummary:
    if not mapping:
        return ReloadAcceptancePersistenceSummaryAuditWriteSummary(
            source_surface=source_surface,
            supplied=False,
        )
    writer_result = _mapping(mapping.get("writer_result")) or mapping
    dry_run_plan = _mapping(mapping.get("dry_run_plan"))
    diagnostics = _diagnostic_rows(mapping, source=source_surface) + _diagnostic_rows(
        writer_result,
        source=f"{source_surface}_writer_result",
    )
    return ReloadAcceptancePersistenceSummaryAuditWriteSummary(
        source_surface=source_surface,
        supplied=True,
        status=_safe_string(mapping.get("status", writer_result.get("status", ""))),
        target_display=_safe_string(
            writer_result.get("target_display", mapping.get("target_display", ""))
        ),
        dry_run_sha256=_safe_string(
            dry_run_plan.get("sha256", mapping.get("dry_run_sha256", ""))
        ),
        final_write_sha256=_safe_string(
            writer_result.get("sha256", mapping.get("sha256", ""))
        ),
        payload_kind=_safe_string(
            writer_result.get("payload_kind", mapping.get("payload_kind", ""))
        ),
        payload_schema_version=_safe_string(
            writer_result.get(
                "payload_schema_version",
                mapping.get("payload_schema_version", ""),
            )
        ),
        bytes_count=_int_value(
            writer_result.get("bytes_count", mapping.get("bytes_count", 0))
        ),
        persistence_write_performed=bool(
            writer_result.get(
                "persistence_write_performed",
                mapping.get("persistence_write_performed", False),
            )
        ),
        acknowledgement_state=_acknowledgement_state(mapping),
        replace_policy=_replace_policy(mapping),
        cleanup_state=_cleanup_state(writer_result),
        diagnostics=diagnostics,
        blockers=tuple(_safe_string(item) for item in _sequence(writer_result.get("blockers"))),
        warnings=tuple(_safe_string(item) for item in _sequence(writer_result.get("warnings"))),
    )


def _acknowledgement_state(mapping: Mapping[str, object]) -> str:
    if bool(mapping.get("caller_acknowledged_persistence_write")):
        return "caller_acknowledged_persistence_write"
    if bool(mapping.get("acknowledged")):
        return "acknowledged"
    if bool(mapping.get("confirm_persistence_write")):
        return "confirmed"
    return _safe_string(mapping.get("acknowledgement_state", "not_supplied"))


def _replace_policy(mapping: Mapping[str, object]) -> str:
    if "allow_replace" in mapping:
        return "allow_replace" if bool(mapping.get("allow_replace")) else "block_replace"
    return _safe_string(mapping.get("replace_policy", "not_supplied"))


def _cleanup_state(mapping: Mapping[str, object]) -> str:
    if bool(mapping.get("temp_file_left_behind")):
        return "temp_file_left_behind"
    if bool(mapping.get("cleanup_performed")):
        return "cleanup_performed"
    if bool(mapping.get("atomic_replace_performed")):
        return "atomic_replace_performed"
    return _safe_string(mapping.get("cleanup_state", "not_supplied"))


def _acknowledgement_rows(
    persistence: Mapping[str, object],
) -> tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]:
    supplied = {
        str(row.get("acknowledgement_id", "")): row
        for row in _iter_mappings(persistence.get("acknowledgements"))
    }
    rows = []
    for ack in RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS:
        row = supplied.get(ack, {})
        satisfied = bool(row.get("satisfied", False))
        expired = bool(row.get("expired", False))
        status = "satisfied" if satisfied and not expired else "not_supplied"
        if row and expired:
            status = "expired"
        elif row and not satisfied:
            status = "blocking"
        rows.append(
            ReloadAcceptancePersistenceSummaryAuditRow(
                row_id=ack,
                label=ack.replace("_", " "),
                value={
                    "required": True,
                    "satisfied": satisfied,
                    "expired": expired,
                    "acknowledgement_is_validation_evidence": False,
                    "acknowledgement_restores_trust": False,
                },
                status=status,
                guidance=(
                    "Acknowledgements are review-only, not validation evidence "
                    "and not trust restoration."
                ),
            )
        )
    return tuple(rows)


def _expiry_rows() -> tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]:
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id=reason,
            label=reason.replace("_", " "),
            value="re-review-required-if-triggered",
            status="review_only",
            guidance="Expiry requires re-review and is not validation failure.",
        )
        for reason in RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRY_REASONS
    )


def _target_storage_rows(
    writer: ReloadAcceptancePersistenceSummaryAuditWriteSummary,
    cli: ReloadAcceptancePersistenceSummaryAuditWriteSummary,
    gui: ReloadAcceptancePersistenceSummaryAuditWriteSummary,
) -> tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]:
    target_display = next(
        (
            item.target_display
            for item in (writer, cli, gui)
            if item.target_display
        ),
        "",
    )
    rows = (
        ("explicit_target_required", True, "Explicit target records only."),
        ("redacted_target_display", target_display or "not_supplied", "Raw paths hidden."),
        ("default_target_path_used", False, "No default target path is selected."),
        ("background_write_performed", False, "No background write is performed."),
        ("directory_scan_performed", False, "No directory scan is performed."),
        ("summary_audit_creates_parent_directories", False, "No directories are created."),
        ("local_review_record_only", True, "Write records remain local review-state only."),
    )
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=value,
            guidance=guidance,
        )
        for row_id, value, guidance in rows
    )


def _schema_migration_rows(
    persistence: Mapping[str, object],
) -> tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]:
    schema_rows = _iter_mappings(persistence.get("schema"))
    schema = schema_rows[0] if schema_rows else {}
    rows = (
        (
            "payload_kind",
            _safe_string(
                schema.get(
                    "payload_kind",
                    "optional_solver_plugin_manifest_reload_acceptance_persistence",
                )
            ),
            "Payload kind is review metadata only.",
        ),
        (
            "schema_version",
            _safe_string(schema.get("schema_version", "not_supplied")),
            "Schema version is separate from ProjectSchema.",
        ),
        (
            "schema_mismatch_is_validation_failure",
            False,
            "Schema mismatch is not validation failure.",
        ),
        (
            "separate_from_project_schema",
            True,
            "Persistence schema remains separate from ProjectSchema.",
        ),
        (
            "summary_audit_repairs_or_migrates_files",
            False,
            "Summary audit does not repair or migrate files.",
        ),
    )
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=value,
            guidance=guidance,
        )
        for row_id, value, guidance in rows
    )


def _redaction_privacy_rows() -> tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]:
    rows = (
        ("raw_absolute_paths_hidden_by_default", True, "Basename/hash/source-id preferred."),
        ("secret_like_values_redacted", True, "Tokens, API keys, and passwords are redacted."),
        ("diagnostics_use_redacted_context", True, "Diagnostics are redacted."),
        ("fingerprints_are_trust_signals", False, "Fingerprints are not trust signals."),
        ("full_file_contents_included", False, "Full file contents are never included."),
        ("plugin_code_included", False, "Plugin code is never included."),
        ("credentials_included", False, "Credentials are never included."),
    )
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=value,
            guidance=guidance,
        )
        for row_id, value, guidance in rows
    )


def _provenance_trust_rows(
    persistence: Mapping[str, object],
) -> tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]:
    provenance = _iter_mappings(persistence.get("provenance"))
    source_display = (
        _safe_string(provenance[0].get("source_display", "supplied-record"))
        if provenance
        else "not_supplied"
    )
    rows = (
        ("source_display", source_display, "Source display is redacted."),
        ("supplied_records_remain_untrusted", True, "Supplied records are not trust."),
        ("trust_label_not_certification", True, "Trust labels are not certification."),
        ("summary_audit_is_not_trust_restoration", True, "No trust restoration occurs."),
    )
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=value,
            guidance=guidance,
        )
        for row_id, value, guidance in rows
    )


def _stale_source_rows() -> tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]:
    rows = (
        ("old_preview_silently_trusted", False, "Old preview is not silently trusted."),
        (
            "missing_moved_changed_sources",
            "repreview_required",
            "Changed source requires re-preview.",
        ),
        ("summary_audit_inspects_sources", False, "Summary audit inspects no sources."),
        ("stale_source_is_validation_failure", False, "Stale source is not validation failure."),
    )
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=value,
            guidance=guidance,
        )
        for row_id, value, guidance in rows
    )


def _conflict_shared_stack_rows() -> tuple[
    ReloadAcceptancePersistenceSummaryAuditRow, ...
]:
    rows = (
        ("conflicts_visible", True, "Conflicts remain visible."),
        ("built_ins_win_by_default", True, "Built-ins win by default."),
        ("persisted_record_overrides_builtins", False, "Records do not override built-ins."),
        ("summary_audit_resolves_conflicts", False, "Conflict resolution is future policy."),
    )
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=value,
            guidance=guidance,
        )
        for row_id, value, guidance in rows
    )


def _unsafe_claim_rows() -> tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]:
    rows = (
        ("validation_success_claim_blocked", True, "Validation success claims are blocked."),
        ("validation_failure_claim_blocked", True, "Validation failure claims are blocked."),
        ("issue_closure_claim_blocked", True, "Issue closure claims are blocked."),
        ("release_mutation_claim_blocked", True, "Release mutation claims are blocked."),
        ("bundled_solver_claim_blocked", True, "Bundled solver claims are blocked."),
        ("certification_claim_blocked", True, "Certification claims are blocked."),
    )
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=value,
            status="blocked",
            guidance=guidance,
        )
        for row_id, value, guidance in rows
    )


def _evidence_history_rows(
    persistence: Mapping[str, object],
) -> tuple[ReloadAcceptancePersistenceSummaryAuditRow, ...]:
    supplied = _iter_mappings(persistence.get("evidence_history"))
    rows = [
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id="skipped_missing",
            label="skipped missing",
            value="skipped-missing remains skipped-missing",
            guidance="Skipped-missing is not validation success or failure.",
        ),
        ReloadAcceptancePersistenceSummaryAuditRow(
            row_id="reference_only",
            label="reference only",
            value=True,
            guidance="Evidence/history remains reference-only.",
        ),
    ]
    for index, row in enumerate(supplied, start=1):
        rows.append(
            ReloadAcceptancePersistenceSummaryAuditRow(
                row_id=_safe_string(row.get("evidence_id", f"evidence-{index}")),
                label="supplied evidence history",
                value=_safe_string(row.get("evidence_type", "history")),
                guidance="Supplied evidence is not validation evidence.",
            )
        )
    return tuple(rows)


def _diagnostic_rows(
    value: object,
    *,
    source: str,
) -> tuple[Mapping[str, object], ...]:
    mapping = _object_to_mapping(value)
    raw_rows = _iter_mappings(mapping.get("diagnostics"))
    if not raw_rows and isinstance(value, Sequence) and not isinstance(value, str):
        raw_rows = _iter_mappings(value)
    rows = []
    for row in raw_rows:
        rows.append(
            {
                "source": source,
                "severity": _safe_string(row.get("severity", "info")),
                "code": _safe_string(row.get("code", "supplied_diagnostic")),
                "message": _safe_string(row.get("message", "")),
                "section": _safe_string(row.get("section", source)),
                "blocker": bool(row.get("blocker", False)),
                "supplied_only": True,
                "not_truth_claim": True,
            }
        )
    return tuple(rows)


def _issue_rows(snapshot: object | None) -> tuple[Mapping[str, object], ...]:
    supplied = _object_to_mapping(snapshot)
    rows = []
    for issue_number in range(6, 12):
        key = str(issue_number)
        issue = supplied.get(key, supplied.get(f"#{issue_number}", "open"))
        state = (
            _safe_string(_mapping(issue).get("state", "open"))
            if isinstance(issue, Mapping)
            else _safe_string(issue or "open")
        )
        rows.append(
            {
                "issue_number": issue_number,
                "state": state or "open",
                "source": "supplied_snapshot" if supplied else "default_open_separation",
                "separate_from_summary_audit": True,
                "mutation_performed": False,
                "closure_claimed": False,
            }
        )
    return tuple(rows)


def _prepared_machine_validation(snapshot: object | None) -> Mapping[str, object]:
    supplied = _object_to_mapping(snapshot)
    return {
        "supplied": bool(supplied),
        "status": _safe_string(supplied.get("status", "not_supplied_future_only")),
        "source": "supplied_snapshot" if supplied else "not_supplied",
        "summary_audit_executed_validation": False,
        "validation_evidence_claimed": False,
        "future_separate_gate_required": True,
        "snapshot": _redact_value(supplied),
    }


def _action_rows() -> tuple[ReloadAcceptancePersistenceSummaryAuditActionRow, ...]:
    return tuple(
        ReloadAcceptancePersistenceSummaryAuditActionRow(
            action=action,
            reason=_action_reason(action),
        )
        for action in ReloadAcceptancePersistenceSummaryAuditAction
    )


def _action_reason(action: ReloadAcceptancePersistenceSummaryAuditAction) -> str:
    return {
        ReloadAcceptancePersistenceSummaryAuditAction.ACCEPT_FOR_SESSION_REVIEW: (
            "Runtime/session acceptance mutation is not performed here."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.ACCEPT_AS_TRUSTED: (
            "Summary audit is not trust restoration."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.ACTIVATE_RELOADED_CANDIDATE: (
            "Activation requires future activation review."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.REFRESH_DISCOVERY: (
            "Discovery refresh is separate future behavior."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.VALIDATE_SOLVER: (
            "Validation execution is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.EXECUTE_SOLVER: (
            "Solver execution is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.INSTALL_DEPENDENCY: (
            "Dependency installation is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.UNINSTALL_DEPENDENCY: (
            "Dependency uninstall is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.UNINSTALL_SOLVER: (
            "Solver uninstall is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.MUTATE_PROJECT_SCHEMA: (
            "ProjectSchema mutation requires a separate gate."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.CREATE_EXPORT_SUMMARY: (
            "Export summary creation is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.CREATE_REPORT_FILE: (
            "Report file creation is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.CREATE_RELOADABLE_BUNDLE: (
            "Reloadable bundle creation is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.COPY_TO_CLIPBOARD: (
            "Clipboard behavior is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.ATTACH_TO_REPORT: (
            "Report attachment is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.OPEN_OUTPUT_FOLDER: (
            "Opening output folders is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.CLOSE_ISSUE: (
            "Issue mutation is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.MUTATE_RELEASE: (
            "Release mutation is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.PUSH_TAG: (
            "Tag mutation is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.UPLOAD_ASSET: (
            "Asset mutation is out of scope."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.CLAIM_VALIDATION_SUCCESS: (
            "Validation success claims are blocked."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.CLAIM_VALIDATION_FAILURE: (
            "Validation failure claims are blocked."
        ),
        ReloadAcceptancePersistenceSummaryAuditAction.CLAIM_CERTIFICATION: (
            "Certification claims are blocked."
        ),
    }[action]


def _safety_text() -> tuple[str, ...]:
    return (
        "Summary audit output is local review-state only.",
        "Summary audit output is not runtime reload acceptance.",
        "Summary audit output is not validation evidence.",
        "Summary audit output is not validation failure.",
        "Summary audit output is not ProjectSchema state.",
        "Summary audit output is not trust restoration.",
        "Summary audit output is not automatic activation.",
        "Summary audit output is not discovery success.",
        "Summary audit output is not dependency installation.",
        "Summary audit output is not solver execution.",
        "Summary audit output is not issue closure.",
        "Summary audit output is not release mutation.",
        "Summary audit output is not certification.",
        "Persisted review records remain untrusted by default.",
        "Skipped-missing remains skipped-missing.",
        "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
        "bounded, issue-specific evidence.",
        "Prepared-machine validation remains separate and supplied-only.",
    )


def _sample_write_record(
    source: str,
    *,
    dry_run: bool = False,
    completed: bool = False,
) -> dict[str, object]:
    status = "completed" if completed else "planned"
    return {
        "status": status,
        "target_display": "reload-acceptance-state.json",
        "target_redacted": True,
        "dry_run": dry_run,
        "planned": not completed,
        "written": completed,
        "bytes_count": 2048,
        "sha256": f"{source}-sha256",
        "payload_kind": (
            "optional_solver_plugin_manifest_reload_acceptance_persistence_record"
        ),
        "payload_schema_version": "osw-exp-126-reload-acceptance-persistence-writer-1",
        "diagnostics": [
            {
                "severity": "info",
                "code": f"OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_{status.upper()}",
                "message": f"{source} {status} local review-record only.",
                "section": source,
                "blocker": False,
            }
        ],
        "blockers": [],
        "warnings": [],
        "non_action_flags": (
            ReloadAcceptancePersistenceSummaryAuditNonActionFlags().to_mapping()
        ),
        "write_performed": completed,
        "persistence_write_performed": completed,
        "runtime_reload_acceptance_performed": False,
        "project_schema_mutated": False,
        "cleanup_performed": completed,
        "temp_file_left_behind": False,
        "temp_file_used": completed,
        "atomic_replace_performed": completed,
    }


def _object_to_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        normalized = _redact_value(value)
        return normalized if isinstance(normalized, Mapping) else {}
    to_mapping = getattr(value, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            normalized = _redact_value(mapped)
            return normalized if isinstance(normalized, Mapping) else {}
    return {}


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _iter_mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(item for item in value if isinstance(item, Mapping))
    return ()


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(value)
    if value in (None, ""):
        return ()
    return (value,)


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except ValueError:
        return 0


def _redact_value(value: object, key: str = "") -> object:
    if _secret_key(key):
        return "<redacted-secret-like-value>"
    if isinstance(value, Mapping):
        return {
            str(item_key): _redact_value(value[item_key], str(item_key))
            for item_key in sorted(value)
        }
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [_redact_value(item, key) for item in value]
    if isinstance(value, str):
        return _safe_string(value)
    if isinstance(value, bool | int | float) or value is None:
        return value
    return _safe_string(value)


def _safe_string(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if _secret_like(text):
        return "<redacted-secret-like-value>"
    if "://" in text:
        return "<redacted-url-reference>"
    parts = text.split()
    if len(parts) > 1:
        return " ".join(_safe_token(part) for part in parts)
    return _safe_token(text)


def _safe_token(token: str) -> str:
    prefix = ""
    suffix = ""
    core = token
    while core and core[0] in "([{\"'":
        prefix += core[0]
        core = core[1:]
    while core and core[-1] in ".,;:)]}\"'":
        suffix = core[-1] + suffix
        core = core[:-1]
    if _path_like(core):
        normalized = core.replace("\\", "/")
        basename = normalized.rsplit("/", 1)[-1] or "redacted-path"
        return f"{prefix}{basename}{suffix}"
    return token


def _path_like(text: str) -> bool:
    normalized = text.replace("\\", "/")
    if normalized.startswith(("/", "~/", "$env:", "${", "%")):
        return True
    if len(normalized) > 2 and normalized[1] == ":" and normalized[2] == "/":
        return True
    lowered = normalized.lower()
    return any(
        marker in lowered
        for marker in (
            "/users/",
            "/home/",
            "%userprofile%",
            "%appdata%",
            "${home}",
        )
    )


def _secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(
        marker in lowered
        for marker in (
            "token",
            "secret",
            "api_key",
            "apikey",
            "password",
            "passwd",
            "credential",
            "private_key",
            "access_key",
        )
    )


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
            "sk-",
        )
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
    if isinstance(value, Mapping):
        return {str(key): _value_to_mapping(value[key]) for key in sorted(value)}
    if isinstance(value, tuple | list):
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
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ACK_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CHAIN_INCOMPLETE",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_CONFLICT_VISIBLE",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_DIAGNOSTIC_CODES",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_ERROR",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_INPUT_MISSING",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_PROJECT_SCHEMA_MUTATION",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_NO_VALIDATION_CLAIM",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_READY_FOR_PREPARED_MACHINE_REVIEW",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_STALE_SOURCE",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNAVAILABLE",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_UNSAFE_CLAIM_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_WRITE_RECORD_MISSING",
    "RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_EXPIRY_REASONS",
    "RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_PAYLOAD_KIND",
    "RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_REQUIRED_ACKS",
    "RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_SCHEMA_ID",
    "RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_SCHEMA_VERSION",
    "RELOAD_ACCEPTANCE_PERSISTENCE_SUMMARY_AUDIT_VERSION",
    "OptionalSolverPluginManifestReloadAcceptancePersistenceSummaryAudit",
    "ReloadAcceptancePersistenceSummaryAuditAction",
    "ReloadAcceptancePersistenceSummaryAuditActionRow",
    "ReloadAcceptancePersistenceSummaryAuditDiagnostic",
    "ReloadAcceptancePersistenceSummaryAuditGateRecord",
    "ReloadAcceptancePersistenceSummaryAuditNonActionFlags",
    "ReloadAcceptancePersistenceSummaryAuditReadiness",
    "ReloadAcceptancePersistenceSummaryAuditRow",
    "ReloadAcceptancePersistenceSummaryAuditSection",
    "ReloadAcceptancePersistenceSummaryAuditState",
    "ReloadAcceptancePersistenceSummaryAuditSummary",
    "ReloadAcceptancePersistenceSummaryAuditWriteSummary",
    "all_reload_acceptance_persistence_summary_audit_acknowledgements",
    "build_optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit",
    "from_mappings",
    "from_records",
    "render_optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit",
    "sample",
    "unavailable",
]
