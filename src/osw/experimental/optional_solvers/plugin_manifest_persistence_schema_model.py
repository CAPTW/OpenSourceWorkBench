"""Pure in-memory schema model for optional solver plugin manifest persisted state.

This module is the OSW-EXP-093 implementation of the persistence schema model for
the OSW-EXP-090 persistence design and the OSW-EXP-092 persistence view-model. It
defines versioned, JSON-compatible, in-memory records for future persisted
optional solver plugin manifest UX state and provides deterministic construction,
normalization, dict conversion, and validation diagnostics.

It performs no side effects. It does not persist anything, read or write files,
create settings files, create runtime state files, create schema files, parse JSON
from a path, inspect path existence, import PySide/Qt, import plugin packages, scan
directories, fetch URLs, run discovery, run validation, execute solvers, install or
uninstall dependencies, uninstall solvers, mutate ProjectSchema, or mutate
issues/releases. All inputs are supplied by the caller; this layer only models and
validates them in memory.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .plugin_manifest_persistence_viewmodel import (
    OSPMG_PERSISTENCE_ACK_REQUIRED,
    OSPMG_PERSISTENCE_CONFLICT_BLOCKED,
    OSPMG_PERSISTENCE_DIAGNOSTIC_CODES,
    OSPMG_PERSISTENCE_NOT_IMPLEMENTED,
    OSPMG_PERSISTENCE_REDACTION_REQUIRED,
    OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED,
    OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED,
    OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED,
    OSPMG_PERSISTENCE_UNSAFE_CLAIM,
    OSPMG_PERSISTENCE_UNTRUSTED_SOURCE,
    OptionalSolverPluginManifestPersistenceViewModel,
    redact_optional_solver_plugin_manifest_persistence_source_reference,
)

#: Current supported in-memory schema version for the persistence schema model.
PERSISTENCE_SCHEMA_VERSION = "osw-exp-093-schema-1"

#: In-memory schema versions this model recognizes (current + the 092 preview).
SUPPORTED_PERSISTENCE_SCHEMA_VERSIONS: tuple[str, ...] = (
    PERSISTENCE_SCHEMA_VERSION,
    "osw-exp-092-preview",
)

#: Default redaction policy identifier (redaction-first).
DEFAULT_REDACTION_POLICY_ID = "redaction_first_v1"

REDACTION_FIRST_PRIVACY_WARNING = (
    "Source references are redacted by default; raw absolute paths are blocked "
    "until an explicit future review/allow gate exists."
)
SCHEMA_NOT_WRITTEN_TEXT = (
    "This schema model is in-memory only; it creates no schema file and writes "
    "nothing."
)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaHeader:
    """Versioned header for a persisted-state schema model (in-memory only)."""

    schema_version: str = ""
    schema_version_supported: bool = False
    created_by_osw_version: str = ""
    created_at: str = ""
    state_scope: str = "session_only"
    state_kind: str = "session_summary"
    redaction_policy_id: str = DEFAULT_REDACTION_POLICY_ID
    migration_required: bool = False
    migration_notes: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaSourceRecord:
    """In-memory source/provenance record."""

    source_id: str
    source_type: str = "user_selected_json_file"
    source_label: str = ""
    source_reference_display: str = ""
    source_reference_redacted: bool = True
    trust_label: str = "untrusted_user_file"
    persisted_state_kind: str = "session_only"
    source_fingerprint_display: str = ""
    stale_source_state: str = ""
    repreview_required: bool = False
    raw_reference_blocked: bool = False
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaCandidateRecord:
    """In-memory candidate record."""

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
    readiness: str = ""
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    required_acknowledgements: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    stale_source_state: str = ""
    repreview_required: bool = False
    redaction_status: str = "redacted"
    built_in_relationship: str = ""
    shared_stack_indicators: tuple[str, ...] = ()
    deactivation_history_state: str = ""
    reactivation_history_state: str = ""
    historical_evidence_state: str = ""
    is_untrusted: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord:
    """In-memory acknowledgement record with expiry policy."""

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
class OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord:
    """In-memory diagnostic record."""

    severity: str
    category: str
    code: str
    message: str
    source_reference_display: str = ""
    stack_id: str = ""
    suggested_fix: str = ""
    blocker: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaRedactionPolicyRecord:
    """In-memory redaction/privacy policy record (redaction-first)."""

    redaction_required: bool = True
    raw_absolute_paths_allowed: bool = False
    unredacted_path_blocked: bool = True
    secret_like_content_blocked: bool = True
    display_strategy: str = "basename_or_display_name"
    path_review_required: bool = True
    privacy_warning: str = REDACTION_FIRST_PRIVACY_WARNING


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaMigrationRecord:
    """In-memory schema/migration record."""

    schema_version_present: bool = False
    schema_version_supported: bool = False
    migration_required: bool = False
    migration_status: str = "not_required"
    migration_notes_display: str = ""
    blocker: bool = False
    this_gate_creates_schema_file: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaConflictRecord:
    """In-memory shared-stack/conflict record."""

    stack_id: str
    built_in_source_id: str = ""
    user_or_plugin_source_id: str = ""
    active_source_state: str = ""
    deactivated_source_state: str = ""
    reactivation_source_state: str = ""
    persistence_state: str = ""
    built_ins_win_by_default: bool = True
    conflict_visible: bool = True
    future_policy_required: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord:
    """In-memory unsafe-claim record (never accepted by persistence)."""

    claim_id: str
    related_candidate_id: str = ""
    related_source_id: str = ""
    claim_text: str = ""
    blocked: bool = True
    warning_text: str = "Unsafe claims are not accepted by persistence."
    accepted_by_persistence: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaEvidenceHistoryRecord:
    """In-memory evidence/history retention record."""

    deactivation_history_retained: bool = True
    reactivation_history_retained: bool = True
    historical_validation_evidence_retained: bool = True
    skipped_missing_remains_skipped_missing: bool = True
    issue_closure_implied: bool = False
    validation_success_claimed: bool = False
    validation_failure_claimed: bool = False
    evidence_deleted_or_rewritten: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaNonActionFlags:
    """In-memory non-action flags; all must remain false."""

    persistence_performed: bool = False
    file_write_performed: bool = False
    settings_file_created: bool = False
    runtime_state_file_created: bool = False
    project_schema_mutation_performed: bool = False
    gui_behavior_added: bool = False
    cli_behavior_added: bool = False
    reload_behavior_added: bool = False
    export_behavior_added: bool = False
    automatic_activation_performed: bool = False
    trust_restoration_performed: bool = False
    file_restoration_performed: bool = False
    file_rewrite_performed: bool = False
    file_deletion_performed: bool = False
    dependency_installation_performed: bool = False
    dependency_uninstall_performed: bool = False
    solver_uninstall_performed: bool = False
    discovery_execution_performed: bool = False
    validation_execution_performed: bool = False
    solver_execution_performed: bool = False
    issue_mutation_performed: bool = False
    release_mutation_performed: bool = False
    tag_mutation_performed: bool = False
    asset_mutation_performed: bool = False
    certification_claimed: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaValidationSummary:
    """Deterministic validation summary for a schema model (in-memory)."""

    schema_version_display: str
    record_count: int
    source_count: int
    candidate_count: int
    acknowledgement_count: int
    diagnostic_count: int
    conflict_count: int
    unsafe_claim_count: int
    redaction_issue_count: int
    stale_source_count: int
    migration_required_count: int
    blocker_count: int
    warning_count: int
    error_count: int
    ready_for_future_write: bool = False
    persistence_performed: bool = False
    file_write_performed: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestPersistenceSchemaModel:
    """Complete in-memory persistence schema model (writes nothing)."""

    header: OptionalSolverPluginManifestPersistenceSchemaHeader
    sources: tuple[
        OptionalSolverPluginManifestPersistenceSchemaSourceRecord, ...
    ] = ()
    candidates: tuple[
        OptionalSolverPluginManifestPersistenceSchemaCandidateRecord, ...
    ] = ()
    acknowledgements: tuple[
        OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord, ...
    ] = ()
    diagnostics: tuple[
        OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord, ...
    ] = ()
    conflicts: tuple[
        OptionalSolverPluginManifestPersistenceSchemaConflictRecord, ...
    ] = ()
    unsafe_claims: tuple[
        OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord, ...
    ] = ()
    redaction_policy: OptionalSolverPluginManifestPersistenceSchemaRedactionPolicyRecord = (
        field(
            default_factory=OptionalSolverPluginManifestPersistenceSchemaRedactionPolicyRecord
        )
    )
    schema_migration: OptionalSolverPluginManifestPersistenceSchemaMigrationRecord = field(
        default_factory=OptionalSolverPluginManifestPersistenceSchemaMigrationRecord
    )
    evidence_history: OptionalSolverPluginManifestPersistenceSchemaEvidenceHistoryRecord = (
        field(
            default_factory=OptionalSolverPluginManifestPersistenceSchemaEvidenceHistoryRecord
        )
    )
    non_action_flags: OptionalSolverPluginManifestPersistenceSchemaNonActionFlags = field(
        default_factory=OptionalSolverPluginManifestPersistenceSchemaNonActionFlags
    )
    validation_summary: OptionalSolverPluginManifestPersistenceSchemaValidationSummary | None = (
        None
    )
    reserved_diagnostic_codes: tuple[str, ...] = OSPMG_PERSISTENCE_DIAGNOSTIC_CODES
    this_gate_creates_schema_file: bool = False
    not_validation_evidence: bool = True

    # ------------------------------------------------------------------
    # Convenience constructors (transform supplied data only; no side effects).
    # ------------------------------------------------------------------
    @classmethod
    def empty(
        cls, *, schema_version: str = PERSISTENCE_SCHEMA_VERSION, state_scope: str = "session_only"
    ) -> OptionalSolverPluginManifestPersistenceSchemaModel:
        return build_optional_solver_plugin_manifest_persistence_schema_model(
            schema_version=schema_version, state_scope=state_scope
        )

    @classmethod
    def from_mapping(
        cls, mapping: Mapping[str, object]
    ) -> OptionalSolverPluginManifestPersistenceSchemaModel:
        return _model_from_mapping(mapping)

    def to_mapping(self) -> dict[str, object]:
        return _model_to_mapping(self)

    @classmethod
    def validate_mapping(
        cls, mapping: Mapping[str, object]
    ) -> tuple[OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord, ...]:
        return validate_optional_solver_plugin_manifest_persistence_schema_mapping(mapping)

    @classmethod
    def from_persistence_viewmodel(
        cls,
        view_model: OptionalSolverPluginManifestPersistenceViewModel,
        *,
        schema_version: str = PERSISTENCE_SCHEMA_VERSION,
    ) -> OptionalSolverPluginManifestPersistenceSchemaModel:
        return _model_from_persistence_viewmodel(view_model, schema_version=schema_version)

    @classmethod
    def unsupported_version(
        cls, schema_version: str
    ) -> OptionalSolverPluginManifestPersistenceSchemaModel:
        return build_optional_solver_plugin_manifest_persistence_schema_model(
            schema_version=schema_version
        )

    @classmethod
    def migration_required(
        cls, schema_version: str, *, migration_notes: str = ""
    ) -> OptionalSolverPluginManifestPersistenceSchemaModel:
        return build_optional_solver_plugin_manifest_persistence_schema_model(
            schema_version=schema_version,
            migration_required=True,
            migration_notes=migration_notes or "Schema migration is required before reuse.",
        )

    @classmethod
    def redaction_required(
        cls,
        source: OptionalSolverPluginManifestPersistenceSchemaSourceRecord,
    ) -> OptionalSolverPluginManifestPersistenceSchemaModel:
        blocked = OptionalSolverPluginManifestPersistenceSchemaSourceRecord(
            source_id=source.source_id,
            source_type=source.source_type,
            source_label=source.source_label,
            source_reference_display=source.source_reference_display,
            source_reference_redacted=False,
            trust_label=source.trust_label,
            persisted_state_kind=source.persisted_state_kind,
            stale_source_state=source.stale_source_state,
            repreview_required=source.repreview_required,
            raw_reference_blocked=True,
        )
        return build_optional_solver_plugin_manifest_persistence_schema_model(
            sources=(blocked,)
        )


def build_optional_solver_plugin_manifest_persistence_schema_model(
    *,
    schema_version: str = PERSISTENCE_SCHEMA_VERSION,
    created_by_osw_version: str = "",
    created_at: str = "",
    state_scope: str = "session_only",
    state_kind: str = "session_summary",
    sources: Sequence[OptionalSolverPluginManifestPersistenceSchemaSourceRecord] = (),
    candidates: Sequence[
        OptionalSolverPluginManifestPersistenceSchemaCandidateRecord
    ] = (),
    acknowledgements: Sequence[
        OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord
    ] = (),
    conflicts: Sequence[
        OptionalSolverPluginManifestPersistenceSchemaConflictRecord
    ] = (),
    unsafe_claims: Sequence[
        OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord
    ] = (),
    redaction_policy: OptionalSolverPluginManifestPersistenceSchemaRedactionPolicyRecord
    | None = None,
    evidence_history: OptionalSolverPluginManifestPersistenceSchemaEvidenceHistoryRecord
    | None = None,
    migration_required: bool = False,
    migration_notes: str = "",
) -> OptionalSolverPluginManifestPersistenceSchemaModel:
    """Build a schema model from supplied records only (in-memory; no writes)."""

    version_supported = schema_version in SUPPORTED_PERSISTENCE_SCHEMA_VERSIONS
    version_present = bool(schema_version)
    needs_migration = migration_required or (version_present and not version_supported)
    redaction = redaction_policy or (
        OptionalSolverPluginManifestPersistenceSchemaRedactionPolicyRecord()
    )
    history = evidence_history or (
        OptionalSolverPluginManifestPersistenceSchemaEvidenceHistoryRecord()
    )
    header = OptionalSolverPluginManifestPersistenceSchemaHeader(
        schema_version=schema_version,
        schema_version_supported=version_supported,
        created_by_osw_version=created_by_osw_version,
        created_at=created_at,
        state_scope=state_scope,
        state_kind=state_kind,
        redaction_policy_id=DEFAULT_REDACTION_POLICY_ID,
        migration_required=needs_migration,
        migration_notes=migration_notes,
    )
    schema_migration = OptionalSolverPluginManifestPersistenceSchemaMigrationRecord(
        schema_version_present=version_present,
        schema_version_supported=version_supported,
        migration_required=needs_migration,
        migration_status="required" if needs_migration else "not_required",
        migration_notes_display=migration_notes,
        blocker=needs_migration or not version_present,
    )
    diagnostics = _schema_diagnostics(
        header=header,
        sources=tuple(sources),
        candidates=tuple(candidates),
        acknowledgements=tuple(acknowledgements),
        conflicts=tuple(conflicts),
        unsafe_claims=tuple(unsafe_claims),
        redaction=redaction,
        schema_migration=schema_migration,
    )
    validation_summary = _validation_summary(
        header=header,
        sources=tuple(sources),
        candidates=tuple(candidates),
        acknowledgements=tuple(acknowledgements),
        diagnostics=diagnostics,
        conflicts=tuple(conflicts),
        unsafe_claims=tuple(unsafe_claims),
        schema_migration=schema_migration,
    )
    return OptionalSolverPluginManifestPersistenceSchemaModel(
        header=header,
        sources=tuple(sources),
        candidates=tuple(candidates),
        acknowledgements=tuple(acknowledgements),
        diagnostics=diagnostics,
        conflicts=tuple(conflicts),
        unsafe_claims=tuple(unsafe_claims),
        redaction_policy=redaction,
        schema_migration=schema_migration,
        evidence_history=history,
        non_action_flags=OptionalSolverPluginManifestPersistenceSchemaNonActionFlags(),
        validation_summary=validation_summary,
    )


def validate_optional_solver_plugin_manifest_persistence_schema_mapping(
    mapping: Mapping[str, object],
) -> tuple[OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord, ...]:
    """Validate a supplied in-memory mapping (no file IO, no path checks)."""

    items: list[OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord] = []

    def add(code: str, severity: str, message: str, blocker: bool = False) -> None:
        items.append(
            OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord(
                severity=severity, category="persistence_schema", code=code,
                message=message, blocker=blocker,
            )
        )

    version = str(mapping.get("schema_version") or "")
    if not version:
        add(OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED, "error",
            "A schema_version is required.", blocker=True)
    elif version not in SUPPORTED_PERSISTENCE_SCHEMA_VERSIONS:
        add(OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED, "warning",
            f"Schema version {version!r} is unsupported; migration is required.",
            blocker=True)

    if "redaction_policy" not in mapping:
        add(OSPMG_PERSISTENCE_REDACTION_REQUIRED, "warning",
            "A redaction policy is required (redaction-first).", blocker=True)

    flags = mapping.get("non_action_flags")
    if isinstance(flags, Mapping):
        for key, value in flags.items():
            if bool(value):
                add(OSPMG_PERSISTENCE_NOT_IMPLEMENTED, "error",
                    f"Non-action flag {key!r} must be false in this gate.",
                    blocker=True)

    for source in _iter_mappings(mapping.get("manifest_sources")):
        if source.get("raw_reference_blocked") or source.get("unredacted_path_blocked"):
            add(OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED, "error",
                "An unredacted/raw path is blocked.", blocker=True)
        if source.get("repreview_required") or source.get("stale_source_state") == "stale":
            add(OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED, "warning",
                "A stale source requires re-preview.", blocker=True)
        if str(source.get("trust_label") or "") == "future_trusted_by_user":
            add(OSPMG_PERSISTENCE_UNTRUSTED_SOURCE, "warning",
                "A trusted-by-user source requires a future trust policy gate.")

    for claim in _iter_mappings(mapping.get("unsafe_claims")):
        if bool(claim.get("accepted_by_persistence")):
            add(OSPMG_PERSISTENCE_UNSAFE_CLAIM, "error",
                "Unsafe claims must not be accepted by persistence.", blocker=True)
        else:
            add(OSPMG_PERSISTENCE_UNSAFE_CLAIM, "warning",
                "An unsafe claim is present and blocked.", blocker=True)

    if list(_iter_mappings(mapping.get("conflicts"))):
        add(OSPMG_PERSISTENCE_CONFLICT_BLOCKED, "warning",
            "A conflict/shared-stack record is present; built-ins win by default.",
            blocker=True)

    required_acks = {
        str(a.get("acknowledgement_id"))
        for a in _iter_mappings(mapping.get("acknowledgements"))
        if a.get("required")
    }
    satisfied_acks = {
        str(a.get("acknowledgement_id"))
        for a in _iter_mappings(mapping.get("acknowledgements"))
        if a.get("required") and a.get("satisfied")
    }
    if required_acks - satisfied_acks:
        add(OSPMG_PERSISTENCE_ACK_REQUIRED, "warning",
            "Required acknowledgements are missing.", blocker=True)

    return tuple(items)


def redact_optional_solver_plugin_manifest_persistence_schema_source_reference(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool]:
    """Return a safe display reference and a redaction flag (no filesystem access)."""

    return redact_optional_solver_plugin_manifest_persistence_source_reference(
        reference, provided_label=provided_label
    )


# ----------------------------------------------------------------------
# Internal helpers (pure).
# ----------------------------------------------------------------------
def _iter_mappings(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _schema_diagnostics(
    *,
    header: OptionalSolverPluginManifestPersistenceSchemaHeader,
    sources: tuple[OptionalSolverPluginManifestPersistenceSchemaSourceRecord, ...],
    candidates: tuple[OptionalSolverPluginManifestPersistenceSchemaCandidateRecord, ...],
    acknowledgements: tuple[
        OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord, ...
    ],
    conflicts: tuple[OptionalSolverPluginManifestPersistenceSchemaConflictRecord, ...],
    unsafe_claims: tuple[
        OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord, ...
    ],
    redaction: OptionalSolverPluginManifestPersistenceSchemaRedactionPolicyRecord,
    schema_migration: OptionalSolverPluginManifestPersistenceSchemaMigrationRecord,
) -> tuple[OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord, ...]:
    items: list[OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord] = []

    def add(code: str, severity: str, message: str, blocker: bool = False,
            stack_id: str = "") -> None:
        items.append(
            OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord(
                severity=severity, category="persistence_schema", code=code,
                message=message, blocker=blocker, stack_id=stack_id,
            )
        )

    if not header.schema_version:
        add(OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED, "error",
            "A schema_version is required.", blocker=True)
    elif not header.schema_version_supported:
        add(OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED, "warning",
            "Schema version is unsupported; migration is required.", blocker=True)
    if schema_migration.migration_required:
        add(OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED, "warning",
            "Schema migration is required before reuse.", blocker=True)
    for source in sources:
        if source.raw_reference_blocked:
            add(OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED, "error",
                "An unredacted/raw path is blocked.", blocker=True)
        if source.repreview_required or source.stale_source_state == "stale":
            add(OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED, "warning",
                "A stale source requires re-preview.", blocker=True)
        if source.trust_label == "future_trusted_by_user":
            add(OSPMG_PERSISTENCE_UNTRUSTED_SOURCE, "warning",
                "A trusted-by-user source requires a future trust policy gate.")
    for claim in unsafe_claims:
        add(OSPMG_PERSISTENCE_UNSAFE_CLAIM, "error" if claim.accepted_by_persistence
            else "warning", claim.claim_text or "An unsafe claim is present.",
            blocker=True)
    if conflicts:
        add(OSPMG_PERSISTENCE_CONFLICT_BLOCKED, "warning",
            "A conflict/shared-stack record is present; built-ins win by default.",
            blocker=True)
    required = {a.acknowledgement_id for a in acknowledgements if a.required}
    satisfied = {a.acknowledgement_id for a in acknowledgements if a.required and a.satisfied}
    if required - satisfied:
        add(OSPMG_PERSISTENCE_ACK_REQUIRED, "warning",
            "Required acknowledgements are missing.", blocker=True)
    if redaction.redaction_required:
        add(OSPMG_PERSISTENCE_REDACTION_REQUIRED, "info",
            "Redaction-first policy applies; raw absolute paths are blocked.")
    add(OSPMG_PERSISTENCE_NOT_IMPLEMENTED, "info", PERSISTENCE_NOT_IMPLEMENTED_INFO)
    return tuple(items)


PERSISTENCE_NOT_IMPLEMENTED_INFO = (
    "Persistence schema model is in-memory only; no writes, settings files, schema "
    "files, ProjectSchema mutation, reload, or export occur in this gate."
)


def _validation_summary(
    *,
    header: OptionalSolverPluginManifestPersistenceSchemaHeader,
    sources: tuple,
    candidates: tuple,
    acknowledgements: tuple,
    diagnostics: tuple,
    conflicts: tuple,
    unsafe_claims: tuple,
    schema_migration: OptionalSolverPluginManifestPersistenceSchemaMigrationRecord,
) -> OptionalSolverPluginManifestPersistenceSchemaValidationSummary:
    warnings = sum(1 for d in diagnostics if d.severity == "warning")
    errors = sum(1 for d in diagnostics if d.severity in {"error", "blocker"})
    blockers = sum(1 for d in diagnostics if d.blocker)
    redaction_issues = sum(
        1 for d in diagnostics if d.code == OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED
    )
    stale_count = sum(1 for s in sources if s.repreview_required or s.stale_source_state == "stale")
    record_count = (
        len(sources) + len(candidates) + len(acknowledgements) + len(conflicts)
        + len(unsafe_claims)
    )
    return OptionalSolverPluginManifestPersistenceSchemaValidationSummary(
        schema_version_display=header.schema_version or "not supplied",
        record_count=record_count,
        source_count=len(sources),
        candidate_count=len(candidates),
        acknowledgement_count=len(acknowledgements),
        diagnostic_count=len(diagnostics),
        conflict_count=len(conflicts),
        unsafe_claim_count=len(unsafe_claims),
        redaction_issue_count=redaction_issues,
        stale_source_count=stale_count,
        migration_required_count=1 if schema_migration.migration_required else 0,
        blocker_count=blockers,
        warning_count=warnings,
        error_count=errors,
        ready_for_future_write=False,
        persistence_performed=False,
        file_write_performed=False,
    )


def _model_to_mapping(
    model: OptionalSolverPluginManifestPersistenceSchemaModel,
) -> dict[str, object]:
    return {
        "schema_version": model.header.schema_version,
        "created_by_osw_version": model.header.created_by_osw_version,
        "created_at": model.header.created_at,
        "state_scope": model.header.state_scope,
        "manifest_sources": [
            {
                "source_id": s.source_id,
                "source_type": s.source_type,
                "source_label": s.source_label,
                "source_reference_display": s.source_reference_display,
                "source_reference_redacted": s.source_reference_redacted,
                "trust_label": s.trust_label,
                "persisted_state_kind": s.persisted_state_kind,
                "source_fingerprint_display": s.source_fingerprint_display,
                "stale_source_state": s.stale_source_state,
                "repreview_required": s.repreview_required,
                "raw_reference_blocked": s.raw_reference_blocked,
            }
            for s in model.sources
        ],
        "candidates": [
            {
                "stack_id": c.stack_id,
                "display_name": c.display_name,
                "source_id": c.source_id,
                "source_type": c.source_type,
                "trust_label": c.trust_label,
                "activation_state": c.activation_state,
                "deactivation_state": c.deactivation_state,
                "reactivation_state": c.reactivation_state,
                "discovery_refresh_state": c.discovery_refresh_state,
                "persistence_state": c.persistence_state,
                "readiness": c.readiness,
                "redaction_status": c.redaction_status,
                "repreview_required": c.repreview_required,
                "is_untrusted": c.is_untrusted,
            }
            for c in model.candidates
        ],
        "acknowledgements": [
            {
                "acknowledgement_id": a.acknowledgement_id,
                "required": a.required,
                "satisfied": a.satisfied,
                "persisted": a.persisted,
                "expires_on_reload": a.expires_on_reload,
                "expires_on_source_change": a.expires_on_source_change,
                "expires_on_schema_change": a.expires_on_schema_change,
                "expires_on_unsafe_claim": a.expires_on_unsafe_claim,
                "blocking": a.blocking,
            }
            for a in model.acknowledgements
        ],
        "diagnostics": [
            {"severity": d.severity, "code": d.code, "stack_id": d.stack_id,
             "blocker": d.blocker}
            for d in model.diagnostics
        ],
        "conflicts": [
            {
                "stack_id": c.stack_id,
                "built_in_source_id": c.built_in_source_id,
                "user_or_plugin_source_id": c.user_or_plugin_source_id,
                "built_ins_win_by_default": c.built_ins_win_by_default,
                "conflict_visible": c.conflict_visible,
                "future_policy_required": c.future_policy_required,
            }
            for c in model.conflicts
        ],
        "unsafe_claims": [
            {
                "claim_id": u.claim_id,
                "related_candidate_id": u.related_candidate_id,
                "claim_text": u.claim_text,
                "blocked": u.blocked,
                "accepted_by_persistence": u.accepted_by_persistence,
            }
            for u in model.unsafe_claims
        ],
        "redaction_policy": {
            "redaction_required": model.redaction_policy.redaction_required,
            "raw_absolute_paths_allowed": model.redaction_policy.raw_absolute_paths_allowed,
            "unredacted_path_blocked": model.redaction_policy.unredacted_path_blocked,
            "secret_like_content_blocked": model.redaction_policy.secret_like_content_blocked,
            "display_strategy": model.redaction_policy.display_strategy,
            "path_review_required": model.redaction_policy.path_review_required,
        },
        "evidence_history": {
            "deactivation_history_retained": model.evidence_history.deactivation_history_retained,
            "reactivation_history_retained": model.evidence_history.reactivation_history_retained,
            "historical_validation_evidence_retained": (
                model.evidence_history.historical_validation_evidence_retained
            ),
            "skipped_missing_remains_skipped_missing": (
                model.evidence_history.skipped_missing_remains_skipped_missing
            ),
            "issue_closure_implied": model.evidence_history.issue_closure_implied,
            "validation_success_claimed": model.evidence_history.validation_success_claimed,
            "validation_failure_claimed": model.evidence_history.validation_failure_claimed,
            "evidence_deleted_or_rewritten": (
                model.evidence_history.evidence_deleted_or_rewritten
            ),
        },
        "migration_notes": model.header.migration_notes,
        "non_action_flags": _non_action_flags_to_mapping(model.non_action_flags),
    }


def _non_action_flags_to_mapping(
    flags: OptionalSolverPluginManifestPersistenceSchemaNonActionFlags,
) -> dict[str, bool]:
    return {
        "persistence_performed": flags.persistence_performed,
        "file_write_performed": flags.file_write_performed,
        "settings_file_created": flags.settings_file_created,
        "runtime_state_file_created": flags.runtime_state_file_created,
        "project_schema_mutation_performed": flags.project_schema_mutation_performed,
        "gui_behavior_added": flags.gui_behavior_added,
        "cli_behavior_added": flags.cli_behavior_added,
        "reload_behavior_added": flags.reload_behavior_added,
        "export_behavior_added": flags.export_behavior_added,
        "automatic_activation_performed": flags.automatic_activation_performed,
        "trust_restoration_performed": flags.trust_restoration_performed,
        "file_restoration_performed": flags.file_restoration_performed,
        "file_rewrite_performed": flags.file_rewrite_performed,
        "file_deletion_performed": flags.file_deletion_performed,
        "dependency_installation_performed": flags.dependency_installation_performed,
        "dependency_uninstall_performed": flags.dependency_uninstall_performed,
        "solver_uninstall_performed": flags.solver_uninstall_performed,
        "discovery_execution_performed": flags.discovery_execution_performed,
        "validation_execution_performed": flags.validation_execution_performed,
        "solver_execution_performed": flags.solver_execution_performed,
        "issue_mutation_performed": flags.issue_mutation_performed,
        "release_mutation_performed": flags.release_mutation_performed,
        "tag_mutation_performed": flags.tag_mutation_performed,
        "asset_mutation_performed": flags.asset_mutation_performed,
        "certification_claimed": flags.certification_claimed,
    }


def _model_from_mapping(
    mapping: Mapping[str, object],
) -> OptionalSolverPluginManifestPersistenceSchemaModel:
    sources = tuple(
        OptionalSolverPluginManifestPersistenceSchemaSourceRecord(
            source_id=str(s.get("source_id") or ""),
            source_type=str(s.get("source_type") or "user_selected_json_file"),
            source_label=str(s.get("source_label") or ""),
            source_reference_display=str(s.get("source_reference_display") or ""),
            source_reference_redacted=bool(s.get("source_reference_redacted", True)),
            trust_label=str(s.get("trust_label") or "untrusted_user_file"),
            persisted_state_kind=str(s.get("persisted_state_kind") or "session_only"),
            source_fingerprint_display=str(s.get("source_fingerprint_display") or ""),
            stale_source_state=str(s.get("stale_source_state") or ""),
            repreview_required=bool(s.get("repreview_required", False)),
            raw_reference_blocked=bool(s.get("raw_reference_blocked", False)),
        )
        for s in _iter_mappings(mapping.get("manifest_sources"))
    )
    candidates = tuple(
        OptionalSolverPluginManifestPersistenceSchemaCandidateRecord(
            stack_id=str(c.get("stack_id") or ""),
            display_name=str(c.get("display_name") or ""),
            source_id=str(c.get("source_id") or ""),
            source_type=str(c.get("source_type") or "user_selected_json_file"),
            trust_label=str(c.get("trust_label") or "untrusted_user_file"),
            activation_state=str(c.get("activation_state") or "inactive_preview"),
            deactivation_state=str(c.get("deactivation_state") or ""),
            reactivation_state=str(c.get("reactivation_state") or ""),
            discovery_refresh_state=str(c.get("discovery_refresh_state") or ""),
            persistence_state=str(c.get("persistence_state") or ""),
            readiness=str(c.get("readiness") or ""),
            redaction_status=str(c.get("redaction_status") or "redacted"),
            repreview_required=bool(c.get("repreview_required", False)),
            is_untrusted=bool(c.get("is_untrusted", True)),
        )
        for c in _iter_mappings(mapping.get("candidates"))
    )
    acknowledgements = tuple(
        OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord(
            acknowledgement_id=str(a.get("acknowledgement_id") or ""),
            required=bool(a.get("required", True)),
            satisfied=bool(a.get("satisfied", False)),
            persisted=bool(a.get("persisted", False)),
            expires_on_reload=bool(a.get("expires_on_reload", True)),
            expires_on_source_change=bool(a.get("expires_on_source_change", True)),
            expires_on_schema_change=bool(a.get("expires_on_schema_change", True)),
            expires_on_unsafe_claim=bool(a.get("expires_on_unsafe_claim", True)),
            blocking=bool(a.get("blocking", False)),
        )
        for a in _iter_mappings(mapping.get("acknowledgements"))
    )
    return build_optional_solver_plugin_manifest_persistence_schema_model(
        schema_version=str(mapping.get("schema_version") or ""),
        created_by_osw_version=str(mapping.get("created_by_osw_version") or ""),
        created_at=str(mapping.get("created_at") or ""),
        state_scope=str(mapping.get("state_scope") or "session_only"),
        sources=sources,
        candidates=candidates,
        acknowledgements=acknowledgements,
        migration_notes=str(mapping.get("migration_notes") or ""),
    )


def _model_from_persistence_viewmodel(
    view_model: OptionalSolverPluginManifestPersistenceViewModel,
    *,
    schema_version: str,
) -> OptionalSolverPluginManifestPersistenceSchemaModel:
    sources = tuple(
        OptionalSolverPluginManifestPersistenceSchemaSourceRecord(
            source_id=row.source_id,
            source_type=row.source_type,
            source_label=row.source_label,
            source_reference_display=row.source_reference_display,
            source_reference_redacted=row.redacted_source_reference,
            trust_label=row.trust_label,
            persisted_state_kind=row.persistence_source_kind,
            source_fingerprint_display=row.source_fingerprint_display,
            stale_source_state=row.stale_source_state,
            repreview_required=row.repreview_required,
            raw_reference_blocked=row.raw_path_blocked,
        )
        for row in view_model.source_rows
    )
    candidates = tuple(
        OptionalSolverPluginManifestPersistenceSchemaCandidateRecord(
            stack_id=row.stack_id,
            display_name=row.display_name,
            source_type=row.source_type,
            trust_label=row.trust_label,
            activation_state=row.activation_state,
            deactivation_state=row.deactivation_state,
            reactivation_state=row.reactivation_state,
            discovery_refresh_state=row.discovery_refresh_state,
            persistence_state=row.persistence_state,
            readiness=row.readiness,
            blockers=tuple(row.blockers),
            warnings=tuple(row.warnings),
            required_acknowledgements=tuple(row.required_acknowledgements),
            diagnostics=tuple(row.diagnostics),
            stale_source_state=row.stale_source_state,
            repreview_required=row.repreview_required,
            redaction_status=row.redaction_status,
            built_in_relationship=row.built_in_relationship,
            shared_stack_indicators=tuple(row.shared_stack_indicators),
            deactivation_history_state=row.deactivation_history_state,
            reactivation_history_state=row.reactivation_history_state,
            historical_evidence_state=row.historical_evidence_state,
            is_untrusted=row.is_untrusted,
        )
        for row in view_model.candidate_rows
    )
    acknowledgements = tuple(
        OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord(
            acknowledgement_id=row.acknowledgement_id,
            label=row.label,
            required=row.required,
            satisfied=row.satisfied,
            persisted=row.persisted,
            expires_on_reload=row.expires_on_reload,
            expires_on_source_change=row.expires_on_source_change,
            expires_on_schema_change=row.expires_on_schema_change,
            expires_on_unsafe_claim=row.expires_on_unsafe_claim,
            blocking=row.blocking,
            reason=row.reason,
            warning_text=row.warning_text,
        )
        for row in view_model.acknowledgement_rows
    )
    conflicts = tuple(
        OptionalSolverPluginManifestPersistenceSchemaConflictRecord(
            stack_id=row.stack_id,
            built_in_source_id=row.built_in_source,
            user_or_plugin_source_id=row.user_plugin_source,
            active_source_state=row.activation_state,
            deactivated_source_state=row.deactivation_state,
            reactivation_source_state=row.reactivation_state,
            persistence_state=row.persistence_state,
            built_ins_win_by_default=row.built_ins_win_default,
            conflict_visible=True,
            future_policy_required=True,
        )
        for row in view_model.conflict_rows
    )
    unsafe_claims = tuple(
        OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord(
            claim_id=row.claim_id,
            related_candidate_id=row.related,
            claim_text=row.claim_text,
            blocked=row.blocked,
            warning_text=row.warning_text,
            accepted_by_persistence=False,
        )
        for row in view_model.unsafe_claim_rows
    )
    evidence = OptionalSolverPluginManifestPersistenceSchemaEvidenceHistoryRecord()
    if view_model.evidence_history_rows:
        first = view_model.evidence_history_rows[0]
        evidence = OptionalSolverPluginManifestPersistenceSchemaEvidenceHistoryRecord(
            deactivation_history_retained=first.deactivation_history_retained,
            reactivation_history_retained=first.reactivation_history_retained,
            historical_validation_evidence_retained=(
                first.historical_validation_evidence_retained
            ),
        )
    migration_row = (
        view_model.schema_migration_rows[0] if view_model.schema_migration_rows else None
    )
    return build_optional_solver_plugin_manifest_persistence_schema_model(
        schema_version=schema_version,
        state_scope=view_model.summary.state_scope,
        sources=sources,
        candidates=candidates,
        acknowledgements=acknowledgements,
        conflicts=conflicts,
        unsafe_claims=unsafe_claims,
        evidence_history=evidence,
        migration_required=bool(migration_row.migration_required) if migration_row else False,
        migration_notes=migration_row.migration_notes_display if migration_row else "",
    )


__all__ = [
    "DEFAULT_REDACTION_POLICY_ID",
    "PERSISTENCE_SCHEMA_VERSION",
    "SUPPORTED_PERSISTENCE_SCHEMA_VERSIONS",
    "OptionalSolverPluginManifestPersistenceSchemaAcknowledgementRecord",
    "OptionalSolverPluginManifestPersistenceSchemaCandidateRecord",
    "OptionalSolverPluginManifestPersistenceSchemaConflictRecord",
    "OptionalSolverPluginManifestPersistenceSchemaDiagnosticRecord",
    "OptionalSolverPluginManifestPersistenceSchemaEvidenceHistoryRecord",
    "OptionalSolverPluginManifestPersistenceSchemaHeader",
    "OptionalSolverPluginManifestPersistenceSchemaMigrationRecord",
    "OptionalSolverPluginManifestPersistenceSchemaModel",
    "OptionalSolverPluginManifestPersistenceSchemaNonActionFlags",
    "OptionalSolverPluginManifestPersistenceSchemaRedactionPolicyRecord",
    "OptionalSolverPluginManifestPersistenceSchemaSourceRecord",
    "OptionalSolverPluginManifestPersistenceSchemaUnsafeClaimRecord",
    "OptionalSolverPluginManifestPersistenceSchemaValidationSummary",
    "build_optional_solver_plugin_manifest_persistence_schema_model",
    "redact_optional_solver_plugin_manifest_persistence_schema_source_reference",
    "validate_optional_solver_plugin_manifest_persistence_schema_mapping",
]
