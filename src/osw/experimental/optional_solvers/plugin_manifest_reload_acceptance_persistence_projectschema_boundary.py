"""ProjectSchema boundary for reload acceptance persistence records.

This OSW-EXP-138 module renders a deterministic, non-authoritative boundary
review over already-supplied in-memory reload acceptance persistence records.
It performs no file IO, invokes no writer or reader, imports no CLI or GUI
code, uses no process bridge, does not import or mutate ProjectSchema, and
never creates runtime acceptance, validation evidence, activation, trust
restoration, release/issue mutation, or certification claims.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from enum import Enum

RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VERSION = "osw-exp-138"
RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SCHEMA_ID = (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary"
)
RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SCHEMA_VERSION = (
    "osw-exp-138-projectschema-boundary-1"
)
RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PAYLOAD_KIND = (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary"
)

OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_UNAVAILABLE = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_UNAVAILABLE"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SEPARATE_SCHEMA = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SEPARATE_SCHEMA"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPORT_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPORT_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_MUTATION_BLOCKED = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_MUTATION_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VALIDATION_EVIDENCE_BLOCKED = (  # noqa: E501
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VALIDATION_EVIDENCE_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_TRUST_RESTORATION_BLOCKED = (  # noqa: E501
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_TRUST_RESTORATION_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ACTIVATION_BLOCKED = (  # noqa: E501
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ACTIVATION_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ISSUE_RELEASE_BLOCKED = (  # noqa: E501
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ISSUE_RELEASE_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_CERTIFICATION_BLOCKED = (  # noqa: E501
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_CERTIFICATION_BLOCKED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PREPARED_MACHINE_REQUIRED = (  # noqa: E501
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PREPARED_MACHINE_REQUIRED"
)
OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ERROR = (
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ERROR"
)

OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_UNAVAILABLE,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SEPARATE_SCHEMA,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPORT_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_MUTATION_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VALIDATION_EVIDENCE_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_TRUST_RESTORATION_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ACTIVATION_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ISSUE_RELEASE_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_CERTIFICATION_BLOCKED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PREPARED_MACHINE_REQUIRED,
    OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ERROR,
)


class ReloadAcceptancePersistenceProjectSchemaBoundaryState(str, Enum):
    """Top-level ProjectSchema boundary state."""

    UNAVAILABLE = "unavailable"
    NO_RECORDS_SUPPLIED = "no_records_supplied"
    RECORDS_SUPPLIED = "records_supplied"
    RECORDS_WITH_BLOCKERS = "records_with_blockers"
    READY_FOR_FUTURE_PROJECTSCHEMA_REVIEW = "ready_for_future_projectschema_review"
    ERROR = "error"


class ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness(str, Enum):
    """Review-only readiness vocabulary."""

    UNAVAILABLE = "unavailable"
    NO_RECORDS_SUPPLIED = "no_records_supplied"
    RECORDS_SUPPLIED = "records_supplied"
    PROJECTSCHEMA_BLOCKED = "projectschema_blocked"
    READY_FOR_FUTURE_REVIEW = "ready_for_future_review"
    ERROR = "error"


class ReloadAcceptancePersistenceProjectSchemaBoundaryAction(str, Enum):
    """Disabled or future-only actions visible in the boundary."""

    IMPORT_PERSISTENCE_RECORD_TO_PROJECT_SCHEMA = "import_persistence_record_to_project_schema"
    IMPORT_SUMMARY_AUDIT_TO_PROJECT_SCHEMA = "import_summary_audit_to_project_schema"
    MUTATE_PROJECT_SCHEMA = "mutate_project_schema"
    MIGRATE_PROJECT_SCHEMA = "migrate_project_schema"
    CREATE_PROJECT_VALIDATION_EVIDENCE = "create_project_validation_evidence"
    ACCEPT_FOR_SESSION_REVIEW = "accept_for_session_review"
    ACCEPT_AS_TRUSTED = "accept_as_trusted"
    ACTIVATE_RELOADED_CANDIDATE = "activate_reloaded_candidate"
    REFRESH_DISCOVERY = "refresh_discovery"
    VALIDATE_SOLVER = "validate_solver"
    EXECUTE_SOLVER = "execute_solver"
    INSTALL_DEPENDENCY = "install_dependency"
    UNINSTALL_DEPENDENCY = "uninstall_dependency"
    UNINSTALL_SOLVER = "uninstall_solver"
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
class ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic:
    """One ProjectSchema boundary diagnostic row."""

    code: str
    severity: str
    message: str
    section: str = "projectschema_boundary"
    blocker: bool = False
    supplied_only: bool = False
    not_truth_claim: bool = True
    suggested_fix: str = ""

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceProjectSchemaBoundaryRow:
    """Generic deterministic boundary row."""

    row_id: str
    label: str
    value: object = ""
    status: str = "review_only"
    guidance: str = ""
    non_authoritative: bool = True

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceProjectSchemaBoundarySourceRecord:
    """Supplied record summary kept separate from ProjectSchema."""

    source_id: str
    label: str
    supplied: bool
    status: str = "not_supplied"
    record: Mapping[str, object] | None = None
    review_only: bool = True
    non_authoritative: bool = True
    not_project_schema_state: bool = True
    not_project_schema_validation_evidence: bool = True
    not_project_schema_validation_failure: bool = True
    not_runtime_reload_acceptance: bool = True
    not_project_schema_mutation: bool = True
    success_does_not_mutate_project_schema: bool = True

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceProjectSchemaBoundaryActionRow:
    """Disabled/future-only action row."""

    action: ReloadAcceptancePersistenceProjectSchemaBoundaryAction
    enabled: bool = False
    future_only: bool = True
    reason: str = "Requires a separate future gate."

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class ReloadAcceptancePersistenceProjectSchemaBoundaryNonActionFlags:
    """False flags for behavior this boundary never performs."""

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
    project_schema_field_added: bool = False
    project_schema_migration_performed: bool = False
    project_schema_validation_evidence_created: bool = False
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
class ReloadAcceptancePersistenceProjectSchemaBoundarySummary:
    """Top-level review summary."""

    state: ReloadAcceptancePersistenceProjectSchemaBoundaryState
    readiness: ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness
    records_supplied: bool
    supplied_record_count: int
    non_authoritative: bool = True
    supplied_record_only: bool = True
    local_review_state_only: bool = True
    boundary_is_project_schema_state: bool = False
    boundary_is_project_schema_validation_evidence: bool = False
    boundary_is_project_schema_validation_failure: bool = False
    boundary_imports_project_schema: bool = False
    boundary_mutates_project_schema: bool = False
    boundary_adds_project_schema_fields: bool = False
    boundary_migrates_project_schema: bool = False
    boundary_restores_trust: bool = False
    boundary_activates_candidate: bool = False
    boundary_closes_issue: bool = False
    boundary_mutates_release: bool = False
    boundary_certifies_manifest: bool = False

    def to_mapping(self) -> dict[str, object]:
        return _record_to_mapping(self)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
    """Pure supplied-record ProjectSchema boundary model."""

    summary: ReloadAcceptancePersistenceProjectSchemaBoundarySummary
    supplied_records: tuple[ReloadAcceptancePersistenceProjectSchemaBoundarySourceRecord, ...]
    schema_separation_rows: tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...]
    prohibited_automatic_flow_rows: tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...]
    future_integration_preconditions: tuple[
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
    ]
    future_permitted_data_candidates: tuple[
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
    ]
    project_schema_mutation_blockers: tuple[
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
    ]
    validation_evidence_boundary: tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...]
    trust_provenance_boundary: tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...]
    candidate_lifecycle_boundary: tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...]
    built_in_shared_stack_boundary: tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...]
    issue_release_certification_boundary: tuple[
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
    ]
    redaction_privacy_boundary: tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...]
    lower_level_diagnostics: tuple[Mapping[str, object], ...]
    diagnostics: tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic, ...]
    non_action_flags: ReloadAcceptancePersistenceProjectSchemaBoundaryNonActionFlags
    disabled_future_actions: tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryActionRow, ...]
    live_optional_validation_issues: tuple[Mapping[str, object], ...]
    prepared_machine_validation: Mapping[str, object]
    limitations: tuple[str, ...]
    safety_text: tuple[str, ...]

    @classmethod
    def unavailable(
        cls,
        reason: str = "ProjectSchema boundary records are unavailable.",
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
        """Return a deterministic unavailable boundary."""

        return cls.from_records(unavailable_reason=reason)

    @classmethod
    def from_records(
        cls,
        *,
        persistence_record_mapping: object | None = None,
        persistence_viewmodel_mapping: object | None = None,
        writer_result_mapping: object | None = None,
        cli_write_result_mapping: object | None = None,
        gui_write_result_mapping: object | None = None,
        summary_audit_mapping: object | None = None,
        issue_state_snapshot: object | None = None,
        prepared_machine_validation_snapshot: object | None = None,
        limitations: Sequence[str] = (),
        diagnostics: object | None = None,
        unavailable_reason: str = "",
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
        """Build a review-only ProjectSchema boundary from supplied records."""

        builder = (
            build_optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary
        )
        return builder(
            persistence_record_mapping=persistence_record_mapping,
            persistence_viewmodel_mapping=persistence_viewmodel_mapping,
            writer_result_mapping=writer_result_mapping,
            cli_write_result_mapping=cli_write_result_mapping,
            gui_write_result_mapping=gui_write_result_mapping,
            summary_audit_mapping=summary_audit_mapping,
            issue_state_snapshot=issue_state_snapshot,
            prepared_machine_validation_snapshot=(prepared_machine_validation_snapshot),
            limitations=limitations,
            diagnostics=diagnostics,
            unavailable_reason=unavailable_reason,
        )

    @classmethod
    def from_mappings(
        cls,
        **kwargs: object,
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
        """Build a boundary from supplied mappings."""

        return cls.from_records(**kwargs)

    @classmethod
    def sample(
        cls,
    ) -> OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
        """Return a deterministic sample boundary."""

        return cls.from_records(
            persistence_record_mapping={
                "payload_kind": (
                    "optional_solver_plugin_manifest_reload_acceptance_persistence_record"
                ),
                "payload_schema_version": ("osw-exp-126-reload-acceptance-persistence-writer-1"),
                "target_display": "reload-acceptance-state.json",
                "diagnostics": [
                    {
                        "severity": "info",
                        "code": "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_SAMPLE",
                        "message": "supplied persistence sample only",
                    }
                ],
            },
            summary_audit_mapping={
                "payload_kind": (
                    "optional_solver_plugin_manifest_reload_acceptance_persistence_summary_audit"
                ),
                "summary": {"state": "ready_for_prepared_machine_review"},
            },
            cli_write_result_mapping={
                "status": "completed",
                "target_display": "cli-state.json",
                "persistence_write_performed": True,
            },
            gui_write_result_mapping={
                "status": "completed",
                "target_display": "gui-state.json",
                "persistence_write_performed": True,
            },
            writer_result_mapping={
                "status": "completed",
                "sha256": "sample-sha256",
                "bytes_count": 512,
            },
            prepared_machine_validation_snapshot={"status": "not_supplied_future_only"},
            limitations=("sample supplied records only",),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible mapping."""

        return {
            "payload_kind": (RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PAYLOAD_KIND),
            "payload_schema_version": (
                RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SCHEMA_VERSION
            ),
            "projectschema_boundary_version": (
                RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VERSION
            ),
            "summary": self.summary.to_mapping(),
            "supplied_records": [record.to_mapping() for record in self.supplied_records],
            "schema_separation": [row.to_mapping() for row in self.schema_separation_rows],
            "prohibited_automatic_flows": [
                row.to_mapping() for row in self.prohibited_automatic_flow_rows
            ],
            "future_integration_preconditions": [
                row.to_mapping() for row in self.future_integration_preconditions
            ],
            "future_permitted_data_candidates": [
                row.to_mapping() for row in self.future_permitted_data_candidates
            ],
            "project_schema_mutation_blockers": [
                row.to_mapping() for row in self.project_schema_mutation_blockers
            ],
            "validation_evidence_boundary": [
                row.to_mapping() for row in self.validation_evidence_boundary
            ],
            "trust_provenance_boundary": [
                row.to_mapping() for row in self.trust_provenance_boundary
            ],
            "candidate_lifecycle_boundary": [
                row.to_mapping() for row in self.candidate_lifecycle_boundary
            ],
            "built_in_shared_stack_boundary": [
                row.to_mapping() for row in self.built_in_shared_stack_boundary
            ],
            "issue_release_certification_boundary": [
                row.to_mapping() for row in self.issue_release_certification_boundary
            ],
            "redaction_privacy_boundary": [
                row.to_mapping() for row in self.redaction_privacy_boundary
            ],
            "lower_level_diagnostics": [dict(row) for row in self.lower_level_diagnostics],
            "diagnostics": [row.to_mapping() for row in self.diagnostics],
            "non_action_flags": self.non_action_flags.to_mapping(),
            "disabled_future_actions": [row.to_mapping() for row in self.disabled_future_actions],
            "live_optional_validation_issues": [
                dict(row) for row in self.live_optional_validation_issues
            ],
            "prepared_machine_validation": dict(self.prepared_machine_validation),
            "limitations": list(self.limitations),
            "safety_text": list(self.safety_text),
        }

    def to_text_lines(self) -> tuple[str, ...]:
        """Render stable plain-text boundary lines."""

        lines = [
            (
                "Optional Solver Plugin Manifest Reload Acceptance "
                "Persistence ProjectSchema Boundary"
            ),
            f"state: {self.summary.state.value}",
            f"readiness: {self.summary.readiness.value}",
            f"records_supplied: {self.summary.records_supplied}",
            (
                "policy: supplied-record-only, pure in-memory, "
                "redaction-first, non-authoritative, non-mutating"
            ),
            (
                "safety: boundary output is not ProjectSchema state, not "
                "ProjectSchema validation evidence, and not validation failure"
            ),
            (
                "safety: boundary output does not mutate ProjectSchema, add "
                "ProjectSchema fields, or migrate ProjectSchema"
            ),
        ]
        if not self.summary.records_supplied:
            lines.append(
                "ProjectSchema boundary unavailable: no supplied reload "
                "acceptance persistence records were provided."
            )
        for record in self.supplied_records:
            if record.supplied:
                lines.append(f"{record.label} is not ProjectSchema state.")
        lines.extend(
            (
                "Supplied persistence record is not ProjectSchema state.",
                "Supplied summary audit is not ProjectSchema state.",
                "CLI write success is not ProjectSchema mutation.",
                "GUI write success is not ProjectSchema mutation.",
                "Persistence schema is separate from ProjectSchema schema.",
                "Summary audit schema is separate from ProjectSchema schema.",
                "Writer schema is separate from ProjectSchema schema.",
            )
        )
        lines.extend(_rows_to_text("schema", self.schema_separation_rows))
        lines.extend(_rows_to_text("prohibited_flow", self.prohibited_automatic_flow_rows))
        lines.extend(_rows_to_text("precondition", self.future_integration_preconditions))
        lines.extend(_rows_to_text("candidate", self.future_permitted_data_candidates))
        lines.extend(_rows_to_text("blocker", self.project_schema_mutation_blockers))
        lines.extend(_rows_to_text("validation", self.validation_evidence_boundary))
        lines.extend(_rows_to_text("trust", self.trust_provenance_boundary))
        lines.extend(_rows_to_text("lifecycle", self.candidate_lifecycle_boundary))
        lines.extend(_rows_to_text("built_in", self.built_in_shared_stack_boundary))
        lines.extend(
            _rows_to_text(
                "issue_release",
                self.issue_release_certification_boundary,
            )
        )
        lines.extend(_rows_to_text("redaction", self.redaction_privacy_boundary))
        for issue in self.live_optional_validation_issues:
            lines.append(
                "live_issue: "
                f"#{issue['issue_number']} state={issue['state']} "
                "separate_from_projectschema=True mutation_performed=False"
            )
        lines.append(
            "prepared_machine_validation: "
            f"status={self.prepared_machine_validation['status']} "
            "future_separate_gate_required=True supplied_only=True"
        )
        for diagnostic in self.diagnostics:
            lines.append(
                "diagnostic: "
                f"{diagnostic.code} severity={diagnostic.severity} "
                f"blocker={diagnostic.blocker} message={diagnostic.message}"
            )
        for diagnostic in self.lower_level_diagnostics:
            lines.append(
                "lower_level_diagnostic: "
                f"{diagnostic['code']} supplied_only=True "
                "not_projectschema_truth=True"
            )
        for action in self.disabled_future_actions:
            lines.append(
                "disabled_future_action: "
                f"{action.action.value} enabled={action.enabled} "
                f"future_only={action.future_only}"
            )
        lines.extend(f"safety: {line}" for line in self.safety_text)
        return tuple(_safe_string(line) for line in lines)


def unavailable(
    reason: str = "ProjectSchema boundary records are unavailable.",
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
    """Return an unavailable ProjectSchema boundary."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary.unavailable(
        reason
    )


def from_records(
    **kwargs: object,
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
    """Build a ProjectSchema boundary from supplied records."""

    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary.from_records(
            **kwargs
        )
    )


def from_mappings(
    **kwargs: object,
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
    """Build a ProjectSchema boundary from supplied mappings."""

    return (
        OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary.from_mappings(
            **kwargs
        )
    )


def sample() -> OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
    """Return a deterministic sample ProjectSchema boundary."""

    return OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary.sample()


def build_optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary(
    *,
    persistence_record_mapping: object | None = None,
    persistence_viewmodel_mapping: object | None = None,
    writer_result_mapping: object | None = None,
    cli_write_result_mapping: object | None = None,
    gui_write_result_mapping: object | None = None,
    summary_audit_mapping: object | None = None,
    issue_state_snapshot: object | None = None,
    prepared_machine_validation_snapshot: object | None = None,
    limitations: Sequence[str] = (),
    diagnostics: object | None = None,
    unavailable_reason: str = "",
) -> OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary:
    """Build the pure supplied-record ProjectSchema boundary."""

    supplied = (
        _source_record(
            "persistence_record",
            "Supplied persistence record",
            persistence_record_mapping,
        ),
        _source_record(
            "persistence_viewmodel",
            "Supplied persistence view-model record",
            persistence_viewmodel_mapping,
        ),
        _source_record(
            "writer_result",
            "Supplied writer result",
            writer_result_mapping,
        ),
        _source_record(
            "cli_write_result",
            "Supplied CLI write result",
            cli_write_result_mapping,
        ),
        _source_record(
            "gui_write_result",
            "Supplied GUI write result",
            gui_write_result_mapping,
        ),
        _source_record(
            "summary_audit",
            "Supplied summary audit",
            summary_audit_mapping,
        ),
    )
    supplied_count = sum(1 for record in supplied if record.supplied)
    has_records = supplied_count > 0
    supplied_diagnostics = _lower_level_diagnostics(
        (
            ("persistence_record", persistence_record_mapping),
            ("persistence_viewmodel", persistence_viewmodel_mapping),
            ("writer_result", writer_result_mapping),
            ("cli_write_result", cli_write_result_mapping),
            ("gui_write_result", gui_write_result_mapping),
            ("summary_audit", summary_audit_mapping),
            ("caller", diagnostics),
        )
    )
    diagnostic_rows = _diagnostics(
        has_records=has_records,
        unavailable_reason=unavailable_reason,
    )
    if unavailable_reason:
        state = ReloadAcceptancePersistenceProjectSchemaBoundaryState.UNAVAILABLE
        readiness = ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness.UNAVAILABLE
    elif not has_records:
        state = ReloadAcceptancePersistenceProjectSchemaBoundaryState.NO_RECORDS_SUPPLIED
        readiness = ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness.NO_RECORDS_SUPPLIED
    else:
        state = ReloadAcceptancePersistenceProjectSchemaBoundaryState.RECORDS_WITH_BLOCKERS
        readiness = ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness.PROJECTSCHEMA_BLOCKED
    summary = ReloadAcceptancePersistenceProjectSchemaBoundarySummary(
        state=state,
        readiness=readiness,
        records_supplied=has_records,
        supplied_record_count=supplied_count,
    )
    return OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary(
        summary=summary,
        supplied_records=supplied,
        schema_separation_rows=_schema_separation_rows(),
        prohibited_automatic_flow_rows=_prohibited_automatic_flow_rows(),
        future_integration_preconditions=_future_integration_preconditions(),
        future_permitted_data_candidates=_future_permitted_data_candidates(),
        project_schema_mutation_blockers=_project_schema_mutation_blockers(),
        validation_evidence_boundary=_validation_evidence_boundary_rows(),
        trust_provenance_boundary=_trust_provenance_boundary_rows(),
        candidate_lifecycle_boundary=_candidate_lifecycle_boundary_rows(),
        built_in_shared_stack_boundary=_built_in_shared_stack_boundary_rows(),
        issue_release_certification_boundary=(_issue_release_certification_boundary_rows()),
        redaction_privacy_boundary=_redaction_privacy_boundary_rows(),
        lower_level_diagnostics=supplied_diagnostics,
        diagnostics=diagnostic_rows,
        non_action_flags=(ReloadAcceptancePersistenceProjectSchemaBoundaryNonActionFlags()),
        disabled_future_actions=_action_rows(),
        live_optional_validation_issues=_issue_rows(issue_state_snapshot),
        prepared_machine_validation=_prepared_machine_validation(
            prepared_machine_validation_snapshot
        ),
        limitations=tuple(_safe_string(item) for item in limitations),
        safety_text=_safety_text(),
    )


def render_optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary(
    boundary: OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary,
) -> tuple[str, ...]:
    """Render stable ProjectSchema boundary text."""

    return boundary.to_text_lines()


def _source_record(
    source_id: str,
    label: str,
    value: object | None,
) -> ReloadAcceptancePersistenceProjectSchemaBoundarySourceRecord:
    mapping = _object_to_mapping(value)
    return ReloadAcceptancePersistenceProjectSchemaBoundarySourceRecord(
        source_id=source_id,
        label=label,
        supplied=bool(mapping),
        status="supplied_review_only" if mapping else "not_supplied",
        record=mapping,
    )


def _diagnostics(
    *,
    has_records: bool,
    unavailable_reason: str,
) -> tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic, ...]:
    rows = [
        ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
            code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SEPARATE_SCHEMA,
            severity="info",
            message=(
                "Persistence, writer, CLI, GUI, and summary audit schemas "
                "remain separate from ProjectSchema."
            ),
            section="schema_separation",
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
            code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPORT_BLOCKED,
            severity="warning",
            message="ProjectSchema import is blocked and future-only.",
            section="prohibited_flows",
            blocker=True,
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
            code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_MUTATION_BLOCKED,
            severity="warning",
            message="ProjectSchema mutation is blocked and future-only.",
            section="project_schema_mutation_blockers",
            blocker=True,
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
            code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VALIDATION_EVIDENCE_BLOCKED,
            severity="warning",
            message=("ProjectSchema validation evidence creation is blocked and future-only."),
            section="validation_evidence_boundary",
            blocker=True,
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
            code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_TRUST_RESTORATION_BLOCKED,
            severity="warning",
            message="Trust restoration is blocked and future-only.",
            section="trust_provenance_boundary",
            blocker=True,
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
            code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ACTIVATION_BLOCKED,
            severity="warning",
            message="Candidate activation is blocked and future-only.",
            section="candidate_lifecycle_boundary",
            blocker=True,
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
            code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ISSUE_RELEASE_BLOCKED,
            severity="warning",
            message=("Issue, release, tag, and asset mutation are blocked and future-only."),
            section="issue_release_certification_boundary",
            blocker=True,
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
            code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_CERTIFICATION_BLOCKED,
            severity="warning",
            message="Certification claims are blocked and future-only.",
            section="issue_release_certification_boundary",
            blocker=True,
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
            code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PREPARED_MACHINE_REQUIRED,
            severity="warning",
            message=(
                "Prepared-machine validation is required before any future "
                "ProjectSchema integration."
            ),
            section="future_integration_preconditions",
            blocker=True,
        ),
    ]
    if unavailable_reason or not has_records:
        rows.insert(
            0,
            ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic(
                code=OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_UNAVAILABLE,
                severity="warning",
                message=(
                    _safe_string(unavailable_reason)
                    or ("No supplied reload acceptance persistence records are available.")
                ),
                section="input_policy",
                blocker=False,
            ),
        )
    return tuple(rows)


def _schema_separation_rows() -> tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...]:
    rows = (
        (
            "persistence_schema_separate",
            "Persistence schema",
            "Persistence schema is separate from ProjectSchema schema.",
        ),
        (
            "summary_audit_schema_separate",
            "Summary audit schema",
            "Summary audit schema is separate from ProjectSchema schema.",
        ),
        (
            "writer_schema_separate",
            "Writer schema",
            "Writer schema is separate from ProjectSchema schema.",
        ),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=label,
            value=True,
            guidance=guidance,
        )
        for row_id, label, guidance in rows
    )


def _prohibited_automatic_flow_rows() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        (
            "persistence_record_to_project_schema_import",
            "persistence record -> ProjectSchema import",
        ),
        ("summary_audit_to_project_schema_import", "summary audit -> ProjectSchema import"),
        ("cli_write_to_project_schema_mutation", "CLI write -> ProjectSchema mutation"),
        ("gui_write_to_project_schema_mutation", "GUI write -> ProjectSchema mutation"),
        (
            "reload_acceptance_to_validation_evidence",
            "reload acceptance -> ProjectSchema validation evidence",
        ),
        (
            "trust_label_to_trusted_solver_state",
            "trust label -> ProjectSchema trusted solver state",
        ),
        (
            "persisted_active_to_activated_candidate",
            "persisted active candidate -> ProjectSchema activated candidate",
        ),
        (
            "skipped_missing_to_validation_success",
            "skipped-missing -> ProjectSchema validation success",
        ),
        ("unsafe_claim_to_projectschema_truth", "unsafe claim -> ProjectSchema truth"),
        (
            "issue_release_certification_to_evidence",
            "issue/release/certification claim -> ProjectSchema evidence",
        ),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=label,
            value=False,
            status="blocked_future_only",
            guidance=f"{label} remains blocked until a separate gate.",
        )
        for row_id, label in rows
    )


def _future_integration_preconditions() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        ("separate_projectschema_design", "separate ProjectSchema boundary implementation design"),
        ("prepared_machine_validation_review", "prepared-machine validation review"),
        ("explicit_user_opt_in", "explicit user opt-in"),
        ("project_schema_version_review", "ProjectSchema schema version review"),
        ("persistence_schema_version_review", "persistence schema version review"),
        ("source_provenance_review", "source/provenance review"),
        ("stale_source_repreview", "stale-source re-preview"),
        ("conflict_shared_stack_review", "conflict/shared-stack review"),
        ("unsafe_claim_review", "unsafe-claim review"),
        ("acknowledgement_expiry_review", "acknowledgement expiry review"),
        ("redaction_privacy_review", "redaction/privacy review"),
        ("validation_issue_state_review", "validation issue state review"),
        (
            "issue_release_certification_separation_review",
            "issue/release/certification separation review",
        ),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=label,
            value="required_future_gate",
            status="missing_until_future_gate",
            guidance=(
                f"{label} is required before ProjectSchema mutation or "
                "ProjectSchema validation evidence."
            ),
        )
        for row_id, label in rows
    )


def _future_permitted_data_candidates() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        ("redacted_source_identifiers", "redacted source identifiers"),
        ("payload_kind_schema_version", "persistence payload kind/schema version"),
        ("writer_hash_byte_count", "writer SHA-256 and bytes count"),
        ("cli_gui_surface_identity", "CLI/GUI surface identity"),
        ("summary_audit_gate_coverage", "summary audit gate coverage"),
        ("non_action_flags", "non-action flags"),
        ("diagnostics_references", "diagnostics references"),
        ("limitations", "limitations"),
        (
            "prepared_machine_validation_status",
            "prepared-machine validation status if supplied later",
        ),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=label,
            value="candidate_review_input_only",
            status="non_authoritative_future_candidate",
            guidance=(f"{label} may be considered only as non-authoritative review input."),
        )
        for row_id, label in rows
    )


def _project_schema_mutation_blockers() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        ("runtime_acceptance_missing", "runtime acceptance not separately completed"),
        ("prepared_machine_validation_missing", "prepared-machine validation missing"),
        ("stale_source_present", "stale source present"),
        ("conflict_shared_stack_unresolved", "conflict/shared-stack unresolved"),
        ("unsafe_claim_present", "unsafe claim present"),
        ("trust_provenance_unclear", "trust/provenance unclear"),
        ("schema_migration_required", "schema migration required"),
        ("acknowledgements_expired", "acknowledgements expired"),
        ("raw_paths_unredacted", "raw paths unredacted"),
        ("secrets_tokens_api_keys_present", "secrets/tokens/API keys present"),
        (
            "bounded_optional_validation_closure_not_projectschema_authority",
            "bounded issues #6 through #11 closure does not authorize "
            "ProjectSchema mutation",
        ),
        (
            "issue_release_certification_claims_present",
            "issue/release/certification claims present",
        ),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=label,
            value=True,
            status="blocked_future_only",
            guidance=f"{label} blocks ProjectSchema mutation.",
        )
        for row_id, label in rows
    )


def _validation_evidence_boundary_rows() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        (
            "persistence_writes_not_validation_evidence",
            "Persistence writes are not validation evidence.",
        ),
        ("cli_writes_not_validation_evidence", "CLI writes are not validation evidence."),
        ("gui_writes_not_validation_evidence", "GUI writes are not validation evidence."),
        ("summary_audit_not_validation_evidence", "Summary audit is not validation evidence."),
        ("skipped_missing_remains_skipped_missing", "Skipped-missing remains skipped-missing."),
        ("prepared_machine_validation_separate", "Prepared-machine validation remains separate."),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=True,
            guidance=guidance,
        )
        for row_id, guidance in rows
    )


def _trust_provenance_boundary_rows() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        ("untrusted_by_default", "User/plugin manifests remain untrusted by default."),
        ("trust_label_not_certification", "Trust labels are not certification."),
        ("fingerprints_not_trust_signals", "Fingerprints are not trust signals."),
        ("no_trust_restoration", "ProjectSchema trust state is not restored."),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=True,
            guidance=guidance,
        )
        for row_id, guidance in rows
    )


def _candidate_lifecycle_boundary_rows() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        ("persisted_inactive_review_only", "Persisted inactive remains review-only."),
        (
            "persisted_active_requires_future_activation_review",
            "Persisted active requires future activation review.",
        ),
        (
            "deactivated_remains_deactivated_review_state",
            "Deactivated remains deactivated review state.",
        ),
        ("reactivation_requires_future_review", "Reactivation requires future review."),
        ("discovery_refresh_review_only", "Discovery-refresh state remains review state."),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=True,
            guidance=guidance,
        )
        for row_id, guidance in rows
    )


def _built_in_shared_stack_boundary_rows() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        ("builtins_remain_authoritative", "Built-ins remain authoritative by default."),
        (
            "persisted_records_do_not_override_builtins",
            "Persisted records do not override built-ins.",
        ),
        ("conflicts_remain_visible", "Conflicts remain visible."),
        ("shared_stack_warnings_remain_visible", "Shared-stack warnings remain visible."),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=True,
            guidance=guidance,
        )
        for row_id, guidance in rows
    )


def _issue_release_certification_boundary_rows() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        ("no_issue_closure", "No issue closure is performed or claimed."),
        ("no_release_mutation", "No release mutation is performed or claimed."),
        ("no_tag_mutation", "No tag mutation is performed or claimed."),
        ("no_asset_mutation", "No asset mutation is performed or claimed."),
        ("no_version_bump", "No version bump is performed or claimed."),
        ("no_bundled_solver_claim", "No bundled-solver support is claimed."),
        ("no_certification_claim", "No certification is claimed."),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=True,
            status="blocked_future_only",
            guidance=guidance,
        )
        for row_id, guidance in rows
    )


def _redaction_privacy_boundary_rows() -> tuple[
    ReloadAcceptancePersistenceProjectSchemaBoundaryRow, ...
]:
    rows = (
        ("raw_absolute_paths_hidden_by_default", "Raw absolute paths are hidden by default."),
        ("secret_like_values_redacted", "Secret-like values are redacted."),
        ("no_full_file_content_display", "Full file content is not displayed."),
        ("no_plugin_code_display", "Plugin code is not displayed."),
        ("no_remote_url_authority", "Remote URL references are not authority."),
    )
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryRow(
            row_id=row_id,
            label=row_id.replace("_", " "),
            value=True,
            guidance=guidance,
        )
        for row_id, guidance in rows
    )


def _action_rows() -> tuple[ReloadAcceptancePersistenceProjectSchemaBoundaryActionRow, ...]:
    return tuple(
        ReloadAcceptancePersistenceProjectSchemaBoundaryActionRow(
            action=action,
            reason=_action_reason(action),
        )
        for action in ReloadAcceptancePersistenceProjectSchemaBoundaryAction
    )


def _action_reason(
    action: ReloadAcceptancePersistenceProjectSchemaBoundaryAction,
) -> str:
    return {
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.IMPORT_PERSISTENCE_RECORD_TO_PROJECT_SCHEMA: (  # noqa: E501
            "Persistence record import to ProjectSchema requires a separate gate."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.IMPORT_SUMMARY_AUDIT_TO_PROJECT_SCHEMA: (  # noqa: E501
            "Summary audit import to ProjectSchema requires a separate gate."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.MUTATE_PROJECT_SCHEMA: (
            "ProjectSchema mutation requires a separate gate."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.MIGRATE_PROJECT_SCHEMA: (
            "ProjectSchema migration requires a separate gate."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.CREATE_PROJECT_VALIDATION_EVIDENCE: (
            "ProjectSchema validation evidence requires prepared-machine validation."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.ACCEPT_FOR_SESSION_REVIEW: (
            "Runtime/session acceptance mutation is not performed here."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.ACCEPT_AS_TRUSTED: (
            "Trust restoration is not performed here."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.ACTIVATE_RELOADED_CANDIDATE: (
            "Activation requires future activation review."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.REFRESH_DISCOVERY: (
            "Discovery refresh is separate future behavior."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.VALIDATE_SOLVER: (
            "Validation execution is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.EXECUTE_SOLVER: (
            "Solver execution is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.INSTALL_DEPENDENCY: (
            "Dependency installation is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.UNINSTALL_DEPENDENCY: (
            "Dependency uninstall is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.UNINSTALL_SOLVER: (
            "Solver uninstall is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.CREATE_EXPORT_SUMMARY: (
            "Export summary creation is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.CREATE_REPORT_FILE: (
            "Report file creation is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.CREATE_RELOADABLE_BUNDLE: (
            "Reloadable bundle creation is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.COPY_TO_CLIPBOARD: (
            "Clipboard behavior is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.ATTACH_TO_REPORT: (
            "Report attachment is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.OPEN_OUTPUT_FOLDER: (
            "Opening output folders is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.CLOSE_ISSUE: (
            "Issue mutation is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.MUTATE_RELEASE: (
            "Release mutation is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.PUSH_TAG: (
            "Tag mutation is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.UPLOAD_ASSET: (
            "Asset mutation is out of scope."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.CLAIM_VALIDATION_SUCCESS: (
            "Validation success claims are blocked."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.CLAIM_VALIDATION_FAILURE: (
            "Validation failure claims are blocked."
        ),
        ReloadAcceptancePersistenceProjectSchemaBoundaryAction.CLAIM_CERTIFICATION: (
            "Certification claims are blocked."
        ),
    }[action]


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
                "separate_from_projectschema_boundary": True,
                "separate_from_project_schema": True,
                "mutation_performed": False,
                "closure_claimed": False,
                "release_mutation_claimed": False,
                "certification_claimed": False,
            }
        )
    return tuple(rows)


def _prepared_machine_validation(snapshot: object | None) -> Mapping[str, object]:
    supplied = _object_to_mapping(snapshot)
    return {
        "supplied": bool(supplied),
        "status": _safe_string(supplied.get("status", "not_supplied_future_only")),
        "source": "supplied_snapshot" if supplied else "not_supplied",
        "supplied_only": True,
        "future_separate_gate_required": True,
        "boundary_executed_validation": False,
        "project_schema_validation_evidence_created": False,
        "validation_evidence_claimed": False,
        "snapshot": _redact_value(supplied),
    }


def _lower_level_diagnostics(
    values: Sequence[tuple[str, object | None]],
) -> tuple[Mapping[str, object], ...]:
    rows = []
    for source, value in values:
        mapping = _object_to_mapping(value)
        for row in _iter_mappings(mapping.get("diagnostics")):
            rows.append(_diagnostic_row(row, source))
        for row in _iter_mappings(mapping.get("lower_level_diagnostics")):
            rows.append(_diagnostic_row(row, source))
    return tuple(rows)


def _diagnostic_row(
    row: Mapping[str, object],
    source: str,
) -> Mapping[str, object]:
    return {
        "source": source,
        "severity": _safe_string(row.get("severity", "info")),
        "code": _safe_string(row.get("code", "supplied_diagnostic")),
        "message": _safe_string(row.get("message", "")),
        "section": _safe_string(row.get("section", source)),
        "blocker": bool(row.get("blocker", False)),
        "supplied_only": True,
        "not_truth_claim": True,
        "not_projectschema_truth": True,
        "not_project_schema_state": True,
        "not_validation_evidence": True,
    }


def _safety_text() -> tuple[str, ...]:
    return (
        "Boundary output is local review-state only.",
        "Boundary output is not ProjectSchema state.",
        "Boundary output is not ProjectSchema validation evidence.",
        "Boundary output is not ProjectSchema validation failure.",
        "Boundary output is not runtime reload acceptance.",
        "Boundary output is not trust restoration.",
        "Boundary output is not automatic activation.",
        "Boundary output is not discovery success.",
        "Boundary output is not dependency installation.",
        "Boundary output is not solver execution.",
        "Boundary output is not issue closure.",
        "Boundary output is not release mutation.",
        "Boundary output is not certification.",
        "Persistence writes are not validation evidence.",
        "Skipped-missing remains skipped-missing.",
        "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
        "bounded, issue-specific evidence.",
        "Prepared-machine validation remains separate and supplied-only.",
    )


def _rows_to_text(
    prefix: str,
    rows: Sequence[ReloadAcceptancePersistenceProjectSchemaBoundaryRow],
) -> tuple[str, ...]:
    return tuple(
        f"{prefix}: {row.row_id} value={row.value} status={row.status} guidance={row.guidance}"
        for row in rows
    )


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
    return {field.name: _value_to_mapping(getattr(record, field.name)) for field in fields(record)}


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
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ACTIVATION_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_CERTIFICATION_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_DIAGNOSTIC_CODES",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ERROR",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPORT_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ISSUE_RELEASE_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_MUTATION_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PREPARED_MACHINE_REQUIRED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SEPARATE_SCHEMA",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_TRUST_RESTORATION_BLOCKED",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_UNAVAILABLE",
    "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VALIDATION_EVIDENCE_BLOCKED",
    "RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PAYLOAD_KIND",
    "RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SCHEMA_ID",
    "RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SCHEMA_VERSION",
    "RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VERSION",
    "OptionalSolverPluginManifestReloadAcceptancePersistenceProjectSchemaBoundary",
    "ReloadAcceptancePersistenceProjectSchemaBoundaryAction",
    "ReloadAcceptancePersistenceProjectSchemaBoundaryActionRow",
    "ReloadAcceptancePersistenceProjectSchemaBoundaryDiagnostic",
    "ReloadAcceptancePersistenceProjectSchemaBoundaryNonActionFlags",
    "ReloadAcceptancePersistenceProjectSchemaBoundaryReadiness",
    "ReloadAcceptancePersistenceProjectSchemaBoundaryRow",
    "ReloadAcceptancePersistenceProjectSchemaBoundarySourceRecord",
    "ReloadAcceptancePersistenceProjectSchemaBoundaryState",
    "ReloadAcceptancePersistenceProjectSchemaBoundarySummary",
    "build_optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary",
    "from_mappings",
    "from_records",
    "render_optional_solver_plugin_manifest_reload_acceptance_persistence_projectschema_boundary",
    "sample",
    "unavailable",
]
