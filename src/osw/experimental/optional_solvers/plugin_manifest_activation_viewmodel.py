"""Pure view-model for optional solver plugin manifest activation.

This module is the OSW-EXP-079 implementation of the activation view-model
designed in OSW-EXP-078. It transforms already-supplied preview/import data
(or caller-supplied activation candidates plus acknowledgement/lifecycle state)
into deterministic activation-readiness, acknowledgement, diagnostic, conflict,
trust, and action-state records.

It performs no side effects. It does not activate anything, persist activation
state, read or write files, parse JSON from a path, import PySide/Qt, import
plugin packages, scan directories, fetch URLs, run discovery, run validation,
execute solvers, install dependencies, or mutate issues/releases. Activation
lifecycle inputs (requested / active / deactivated) and acknowledgement
satisfaction are SUPPLIED by the caller; this layer only classifies and renders
them. Activation persistence, GUI behavior, discovery integration, validation,
install, and execution remain future-gated.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

from .plugin_manifest_explicit_import_gui_viewmodel import (
    OptionalSolverPluginManifestExplicitImportGuiViewModel,
    build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel,
    redact_optional_solver_plugin_manifest_source_reference,
)
from .plugin_manifest_loader import OptionalSolverPluginManifestLoadReport

# Design-only OSPMG_ACTIVATION_* diagnostic vocabulary reserved by OSW-EXP-078.
OSPMG_ACTIVATION_PREVIEW_REQUIRED = "OSPMG_ACTIVATION_PREVIEW_REQUIRED"
OSPMG_ACTIVATION_SCHEMA_BLOCKED = "OSPMG_ACTIVATION_SCHEMA_BLOCKED"
OSPMG_ACTIVATION_CONFLICT_BLOCKED = "OSPMG_ACTIVATION_CONFLICT_BLOCKED"
OSPMG_ACTIVATION_UNTRUSTED_SOURCE = "OSPMG_ACTIVATION_UNTRUSTED_SOURCE"
OSPMG_ACTIVATION_UNSAFE_CLAIM = "OSPMG_ACTIVATION_UNSAFE_CLAIM"
OSPMG_ACTIVATION_ACK_REQUIRED = "OSPMG_ACTIVATION_ACK_REQUIRED"
OSPMG_ACTIVATION_NOT_VALIDATION = "OSPMG_ACTIVATION_NOT_VALIDATION"
OSPMG_ACTIVATION_NO_INSTALL = "OSPMG_ACTIVATION_NO_INSTALL"
OSPMG_ACTIVATION_NO_SOLVER_EXECUTION = "OSPMG_ACTIVATION_NO_SOLVER_EXECUTION"
OSPMG_ACTIVATION_NOT_CERTIFICATION = "OSPMG_ACTIVATION_NOT_CERTIFICATION"
OSPMG_ACTIVATION_DEACTIVATED = "OSPMG_ACTIVATION_DEACTIVATED"
OSPMG_ACTIVATION_PREVIEW_ONLY_GATE = "OSPMG_ACTIVATION_PREVIEW_ONLY_GATE"

#: All reserved activation diagnostic codes, in design order.
OSPMG_ACTIVATION_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_ACTIVATION_PREVIEW_REQUIRED,
    OSPMG_ACTIVATION_SCHEMA_BLOCKED,
    OSPMG_ACTIVATION_CONFLICT_BLOCKED,
    OSPMG_ACTIVATION_UNTRUSTED_SOURCE,
    OSPMG_ACTIVATION_UNSAFE_CLAIM,
    OSPMG_ACTIVATION_ACK_REQUIRED,
    OSPMG_ACTIVATION_NOT_VALIDATION,
    OSPMG_ACTIVATION_NO_INSTALL,
    OSPMG_ACTIVATION_NO_SOLVER_EXECUTION,
    OSPMG_ACTIVATION_NOT_CERTIFICATION,
    OSPMG_ACTIVATION_DEACTIVATED,
    OSPMG_ACTIVATION_PREVIEW_ONLY_GATE,
)

# Acknowledgement identifiers (OSW-EXP-078).
ACK_UNTRUSTED_SOURCE = "untrusted_source"
ACK_NO_VALIDATION_PASS = "no_validation_pass"
ACK_NO_DEPENDENCY_INSTALL = "no_dependency_install"
ACK_NO_SOLVER_EXECUTION = "no_solver_execution"
ACK_NO_ISSUE_CLOSURE = "no_issue_closure"
ACK_NO_CERTIFICATION = "no_certification"
ACK_CONFLICT_OR_OVERRIDE = "conflict_or_override"
ACK_UNSAFE_CLAIM = "unsafe_claim"

#: Acknowledgements always required before activation, regardless of candidates.
_ALWAYS_REQUIRED_ACKS: tuple[str, ...] = (
    ACK_NO_VALIDATION_PASS,
    ACK_NO_DEPENDENCY_INSTALL,
    ACK_NO_SOLVER_EXECUTION,
    ACK_NO_ISSUE_CLOSURE,
    ACK_NO_CERTIFICATION,
)

_ACK_LABELS: dict[str, str] = {
    ACK_UNTRUSTED_SOURCE: "I understand this source is untrusted.",
    ACK_NO_VALIDATION_PASS: "I understand activation is not validation success.",
    ACK_NO_DEPENDENCY_INSTALL: "I understand activation does not install dependencies.",
    ACK_NO_SOLVER_EXECUTION: "I understand activation does not execute solvers.",
    ACK_NO_ISSUE_CLOSURE: "I understand activation does not close issues.",
    ACK_NO_CERTIFICATION: "I understand a trust label is not certification.",
    ACK_CONFLICT_OR_OVERRIDE: "I understand built-ins win and overrides are blocked by default.",
    ACK_UNSAFE_CLAIM: "I understand this manifest contains unsafe claims.",
}

#: Loader/explicit-import trust labels treated as untrusted for activation.
_UNTRUSTED_TRUST_LABELS: frozenset[str] = frozenset(
    {"user_provided", "third_party_plugin", "untrusted", "invalid",
     "untrusted_user_file", "untrusted_plugin_manifest"}
)

TRUST_NOT_CERTIFICATION_TEXT = "A trust label is not certification."
ACTIVE_NOT_VALIDATION_TEXT = "An active candidate is not validation evidence."
PREVIEW_ONLY_GATE_TEXT = (
    "Activation is preview-only in this gate; it does not persist, validate, "
    "install, discover, or execute anything."
)


class OptionalSolverPluginManifestActivationState(str, Enum):
    """Activation lifecycle state (OSW-EXP-078 state machine)."""

    INACTIVE_PREVIEW = "inactive_preview"
    ACTIVATION_REQUESTED = "activation_requested"
    ACTIVATION_BLOCKED = "activation_blocked"
    ACTIVATION_READY = "activation_ready"
    ACTIVE_CANDIDATE = "active_candidate"
    DEACTIVATED = "deactivated"
    ACTIVATION_ERROR = "activation_error"


class OptionalSolverPluginManifestActivationReadiness(str, Enum):
    """Per-candidate activation readiness classification."""

    UNAVAILABLE_BEFORE_PREVIEW = "unavailable_before_preview"
    BLOCKED_SCHEMA = "blocked_schema"
    BLOCKED_CONFLICT = "blocked_conflict"
    BLOCKED_ACKNOWLEDGEMENT = "blocked_acknowledgement"
    BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_claim"
    READY = "ready"
    ACTIVE_CANDIDATE = "active_candidate"
    DEACTIVATED = "deactivated"
    ERROR = "error"


class OptionalSolverPluginManifestActivationAction(str, Enum):
    """Future action identifiers for the activation surface."""

    REQUEST_ACTIVATION = "request_activation"
    ACKNOWLEDGE_UNTRUSTED_SOURCE = "acknowledge_untrusted_source"
    ACKNOWLEDGE_NO_VALIDATION_PASS = "acknowledge_no_validation_pass"
    ACKNOWLEDGE_NO_INSTALL = "acknowledge_no_install"
    ACKNOWLEDGE_NO_SOLVER_EXECUTION = "acknowledge_no_solver_execution"
    ACKNOWLEDGE_NO_CERTIFICATION = "acknowledge_no_certification"
    ACTIVATE_CANDIDATE = "activate_candidate"
    DEACTIVATE_CANDIDATE = "deactivate_candidate"
    RUN_DISCOVERY_WITH_ACTIVATED_MANIFESTS = "run_discovery_with_activated_manifests"
    RUN_VALIDATION = "run_validation"
    INSTALL_DEPENDENCY = "install_dependency"
    EXECUTE_SOLVER = "execute_solver"
    CLOSE_ISSUE = "close_issue"
    EXPORT_REDACTED_SUMMARY = "export_redacted_summary"


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActivationCandidateInput:
    """Caller-supplied activation candidate (no file IO performed)."""

    stack_id: str
    display_name: str = ""
    source_type: str = "user_selected_json_file"
    source_label: str = ""
    source_reference: str = ""
    trust_label: str = "untrusted_user_file"
    is_untrusted: bool = True
    has_schema_blocker: bool = False
    has_conflict: bool = False
    has_unsafe_claim: bool = False
    unsafe_claim_indicators: tuple[str, ...] = ()
    built_in_relationship: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActivationActionState:
    """Display-only state for a future activation action."""

    action: OptionalSolverPluginManifestActivationAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActivationSummaryViewModel:
    """Summary header values for an activation view-model."""

    preview_sources_count: int
    activation_candidates_count: int
    activation_ready_count: int
    activation_blocked_count: int
    active_candidate_count: int
    deactivated_count: int
    diagnostic_count: int
    warning_count: int
    error_count: int
    acknowledgement_required_count: int
    preview_required_count: int
    status_text: str
    preview_only: bool = True
    activation_performed: bool = False
    validation_execution_performed: bool = False
    discovery_execution_performed: bool = False
    solver_execution_performed: bool = False
    dependency_installation_performed: bool = False
    issue_mutation_performed: bool = False
    release_mutation_performed: bool = False
    certification_claimed: bool = False
    not_validation_evidence: bool = True
    third_party_manifests_trusted_by_default: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActivationCandidateRowViewModel:
    """GUI/CLI-ready activation candidate row."""

    stack_id: str
    display_name: str
    source_type: str
    source_label: str
    source_reference_display: str
    trust_label: str
    activation_state: str
    readiness: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    required_acknowledgements: tuple[str, ...]
    diagnostics: tuple[str, ...]
    built_in_relationship: str
    unsafe_claim_indicators: tuple[str, ...]
    redacted_source_reference: bool
    is_untrusted: bool
    not_validation_evidence_text: str = ACTIVE_NOT_VALIDATION_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActivationAcknowledgementRowViewModel:
    """Acknowledgement row for the activation surface."""

    acknowledgement_id: str
    label: str
    required: bool
    satisfied: bool
    blocking: bool
    reason: str
    related: str
    warning_text: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActivationDiagnosticViewModel:
    """Activation (OSPMG_ACTIVATION) level diagnostic record."""

    severity: str
    category: str
    code: str
    message: str
    source_reference_display: str = ""
    stack_id: str = ""
    suggested_fix: str = ""
    blocker: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActivationConflictRowViewModel:
    """Activation conflict row."""

    stack_id: str
    built_in_source: str
    user_plugin_source: str
    conflict_policy: str
    built_ins_win_default: bool
    activation_state: str
    required_future_policy: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActivationTrustBadgeViewModel:
    """Source/trust/provenance badge for the activation surface."""

    source_type: str
    trust_label: str
    source_label: str
    activation_state: str
    warning_text: str
    trust_label_is_not_certification: str = TRUST_NOT_CERTIFICATION_TEXT
    active_candidate_is_not_validation_evidence: str = ACTIVE_NOT_VALIDATION_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActivationViewModel:
    """Complete pure view-model for the activation surface."""

    summary: OptionalSolverPluginManifestActivationSummaryViewModel
    candidate_rows: tuple[OptionalSolverPluginManifestActivationCandidateRowViewModel, ...]
    acknowledgement_rows: tuple[
        OptionalSolverPluginManifestActivationAcknowledgementRowViewModel, ...
    ]
    diagnostics: tuple[OptionalSolverPluginManifestActivationDiagnosticViewModel, ...]
    conflict_rows: tuple[OptionalSolverPluginManifestActivationConflictRowViewModel, ...]
    trust_badges: tuple[OptionalSolverPluginManifestActivationTrustBadgeViewModel, ...]
    actions: tuple[OptionalSolverPluginManifestActivationActionState, ...]
    guidance_text: tuple[str, ...]
    safety_text: tuple[str, ...]
    reserved_activation_diagnostic_codes: tuple[str, ...] = OSPMG_ACTIVATION_DIAGNOSTIC_CODES
    preview_available: bool = True
    preview_only: bool = True
    not_validation_evidence: bool = True

    # ------------------------------------------------------------------
    # Convenience constructors (transform supplied data only; no side effects).
    # ------------------------------------------------------------------
    @classmethod
    def from_candidates(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestActivationCandidateInput],
        *,
        acknowledgements: Mapping[str, bool] | None = None,
        requested_stack_ids: Sequence[str] | None = None,
        active_stack_ids: Sequence[str] | None = None,
        deactivated_stack_ids: Sequence[str] | None = None,
    ) -> OptionalSolverPluginManifestActivationViewModel:
        return build_optional_solver_plugin_manifest_activation_viewmodel(
            candidates,
            preview_available=True,
            acknowledgements=acknowledgements,
            requested_stack_ids=requested_stack_ids,
            active_stack_ids=active_stack_ids,
            deactivated_stack_ids=deactivated_stack_ids,
        )

    @classmethod
    def from_explicit_import_viewmodel(
        cls,
        import_view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
        requested_stack_ids: Sequence[str] | None = None,
        active_stack_ids: Sequence[str] | None = None,
        deactivated_stack_ids: Sequence[str] | None = None,
    ) -> OptionalSolverPluginManifestActivationViewModel:
        candidates = _candidates_from_import_view_model(import_view_model)
        return build_optional_solver_plugin_manifest_activation_viewmodel(
            candidates,
            preview_available=_import_has_preview(import_view_model),
            acknowledgements=acknowledgements,
            requested_stack_ids=requested_stack_ids,
            active_stack_ids=active_stack_ids,
            deactivated_stack_ids=deactivated_stack_ids,
        )

    @classmethod
    def from_loader_report(
        cls,
        report: OptionalSolverPluginManifestLoadReport,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
        requested_stack_ids: Sequence[str] | None = None,
        active_stack_ids: Sequence[str] | None = None,
        deactivated_stack_ids: Sequence[str] | None = None,
    ) -> OptionalSolverPluginManifestActivationViewModel:
        import_vm = build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
            report
        )
        return cls.from_explicit_import_viewmodel(
            import_vm,
            acknowledgements=acknowledgements,
            requested_stack_ids=requested_stack_ids,
            active_stack_ids=active_stack_ids,
            deactivated_stack_ids=deactivated_stack_ids,
        )

    @classmethod
    def empty(cls) -> OptionalSolverPluginManifestActivationViewModel:
        return build_optional_solver_plugin_manifest_activation_viewmodel(
            (), preview_available=False
        )

    @classmethod
    def preview_required(cls) -> OptionalSolverPluginManifestActivationViewModel:
        return cls.empty()

    @classmethod
    def all_blocked(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestActivationCandidateInput],
    ) -> OptionalSolverPluginManifestActivationViewModel:
        # No acknowledgements satisfied: every otherwise-ready candidate becomes
        # blocked_acknowledgement, and schema/conflict/unsafe candidates remain
        # blocked on their own grounds.
        return build_optional_solver_plugin_manifest_activation_viewmodel(
            candidates,
            preview_available=True,
            acknowledgements={},
            requested_stack_ids=[c.stack_id for c in candidates],
        )


def build_optional_solver_plugin_manifest_activation_viewmodel(
    candidates: Sequence[OptionalSolverPluginManifestActivationCandidateInput],
    *,
    preview_available: bool = True,
    acknowledgements: Mapping[str, bool] | None = None,
    requested_stack_ids: Sequence[str] | None = None,
    active_stack_ids: Sequence[str] | None = None,
    deactivated_stack_ids: Sequence[str] | None = None,
) -> OptionalSolverPluginManifestActivationViewModel:
    """Build the activation view-model from supplied candidates and state."""

    acks = {str(k): bool(v) for k, v in (acknowledgements or {}).items()}
    requested = {str(s) for s in (requested_stack_ids or ())}
    active = {str(s) for s in (active_stack_ids or ())}
    deactivated = {str(s) for s in (deactivated_stack_ids or ())}

    required_acks = _required_acknowledgements(candidates)
    required_satisfied = all(acks.get(ack, False) for ack in required_acks)

    candidate_rows = tuple(
        _candidate_row(
            cand,
            preview_available=preview_available,
            required_acks=required_acks,
            required_satisfied=required_satisfied,
            requested=cand.stack_id in requested,
            active=cand.stack_id in active,
            deactivated=cand.stack_id in deactivated,
        )
        for cand in sorted(candidates, key=lambda c: (c.stack_id, c.source_type))
    )

    acknowledgement_rows = _acknowledgement_rows(required_acks, acks)
    conflict_rows = tuple(
        _conflict_row(cand) for cand in candidate_rows if cand.readiness ==
        OptionalSolverPluginManifestActivationReadiness.BLOCKED_CONFLICT.value
    )
    diagnostics = _diagnostics(
        candidate_rows,
        preview_available=preview_available,
        required_acks=required_acks,
        required_satisfied=required_satisfied,
    )
    trust_badges = _trust_badges(candidate_rows)
    summary = _summary(
        candidate_rows,
        diagnostics=diagnostics,
        preview_available=preview_available,
        required_acks=required_acks,
        active=active,
    )
    return OptionalSolverPluginManifestActivationViewModel(
        summary=summary,
        candidate_rows=candidate_rows,
        acknowledgement_rows=acknowledgement_rows,
        diagnostics=diagnostics,
        conflict_rows=conflict_rows,
        trust_badges=trust_badges,
        actions=_action_states(candidate_rows, preview_available=preview_available),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
        preview_available=preview_available,
    )


def render_optional_solver_plugin_manifest_activation_summary(
    view_model: OptionalSolverPluginManifestActivationViewModel,
) -> dict[str, object]:
    """Return an in-memory, redacted, JSON-ready activation summary.

    This helper builds an in-memory dictionary only. It writes no files, touches
    no clipboard, and opens no shell, browser, or output folder.
    """

    summary = view_model.summary
    return {
        "preview_available": view_model.preview_available,
        "preview_only": True,
        "activation_candidates_count": summary.activation_candidates_count,
        "activation_ready_count": summary.activation_ready_count,
        "activation_blocked_count": summary.activation_blocked_count,
        "active_candidate_count": summary.active_candidate_count,
        "deactivated_count": summary.deactivated_count,
        "activation_performed": summary.activation_performed,
        "validation_execution_performed": False,
        "discovery_execution_performed": False,
        "solver_execution_performed": False,
        "dependency_installation_performed": False,
        "issue_mutation_performed": False,
        "release_mutation_performed": False,
        "certification_claimed": False,
        "not_validation_evidence": True,
        "candidates": [
            {
                "stack_id": row.stack_id,
                "source_type": row.source_type,
                "source_reference_display": row.source_reference_display,
                "trust_label": row.trust_label,
                "activation_state": row.activation_state,
                "readiness": row.readiness,
                "is_untrusted": row.is_untrusted,
                "redacted_source_reference": row.redacted_source_reference,
            }
            for row in view_model.candidate_rows
        ],
        "diagnostics": [
            {"code": d.code, "severity": d.severity, "stack_id": d.stack_id}
            for d in view_model.diagnostics
        ],
    }


def summarize_optional_solver_plugin_manifest_activation_viewmodel(
    view_model: OptionalSolverPluginManifestActivationViewModel,
) -> str:
    """Return a concise activation summary."""

    summary = view_model.summary
    return (
        "Optional solver plugin manifest activation: "
        f"{summary.activation_candidates_count} candidate(s), "
        f"{summary.activation_ready_count} ready, "
        f"{summary.activation_blocked_count} blocked, "
        f"{summary.active_candidate_count} active, "
        f"{summary.deactivated_count} deactivated. {PREVIEW_ONLY_GATE_TEXT}"
    )


def explain_optional_solver_plugin_manifest_activation_viewmodel(
    view_model: OptionalSolverPluginManifestActivationViewModel,
) -> str:
    """Explain the safety boundary of the activation view-model."""

    disabled = ", ".join(
        action.action.value for action in view_model.actions if not action.enabled
    )
    return (
        summarize_optional_solver_plugin_manifest_activation_viewmodel(view_model)
        + " The view-model transforms supplied preview/candidate data only; it "
        "does not activate, persist activation, load files, import plugin "
        "packages, scan directories, fetch network manifests, run discovery, run "
        "validation, execute solvers, install dependencies, mutate issues, or "
        f"mutate releases. Disabled or future-only actions: {disabled}."
    )


# ----------------------------------------------------------------------
# Internal helpers (pure).
# ----------------------------------------------------------------------
def _candidates_from_import_view_model(
    import_view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
) -> tuple[OptionalSolverPluginManifestActivationCandidateInput, ...]:
    conflict_stack_ids = {row.stack_id for row in import_view_model.conflict_rows if row.stack_id}
    candidates: list[OptionalSolverPluginManifestActivationCandidateInput] = []

    for row in import_view_model.accepted_rows:
        candidates.append(
            OptionalSolverPluginManifestActivationCandidateInput(
                stack_id=row.stack_id,
                display_name=row.display_name,
                source_type=row.source_type,
                source_label=row.source_label,
                source_reference=row.source_ref,
                trust_label=row.trust_label,
                is_untrusted=row.trust_label in _UNTRUSTED_TRUST_LABELS,
                has_schema_blocker=False,
                has_conflict=row.stack_id in conflict_stack_ids,
                has_unsafe_claim=False,
                built_in_relationship=_built_in_relationship(row.trust_label),
            )
        )

    for row in import_view_model.rejected_rows:
        has_unsafe = bool(row.unsafe_claim_indicators)
        has_conflict = row.stack_id in conflict_stack_ids
        # Priority: unsafe > conflict > schema/policy.
        has_schema = not has_unsafe and not has_conflict
        candidates.append(
            OptionalSolverPluginManifestActivationCandidateInput(
                stack_id=row.stack_id,
                display_name=row.stack_id,
                source_type=row.source_type,
                source_label=row.source_label,
                source_reference=row.source_ref,
                trust_label=row.trust_label,
                is_untrusted=row.trust_label in _UNTRUSTED_TRUST_LABELS,
                has_schema_blocker=has_schema,
                has_conflict=has_conflict,
                has_unsafe_claim=has_unsafe,
                unsafe_claim_indicators=tuple(row.unsafe_claim_indicators),
                built_in_relationship=_built_in_relationship(row.trust_label),
            )
        )
    return tuple(candidates)


def _import_has_preview(
    import_view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
) -> bool:
    return bool(
        import_view_model.accepted_rows
        or import_view_model.rejected_rows
        or import_view_model.conflict_rows
    )


def _built_in_relationship(trust_label: str) -> str:
    if trust_label in {"trusted_builtin", "built_in"}:
        return "built-in (authoritative by default)"
    return "non-built-in (built-ins win by default)"


def _required_acknowledgements(
    candidates: Sequence[OptionalSolverPluginManifestActivationCandidateInput],
) -> tuple[str, ...]:
    required = list(_ALWAYS_REQUIRED_ACKS)
    if any(c.is_untrusted for c in candidates):
        required.insert(0, ACK_UNTRUSTED_SOURCE)
    if any(c.has_conflict for c in candidates):
        required.append(ACK_CONFLICT_OR_OVERRIDE)
    if any(c.has_unsafe_claim for c in candidates):
        required.append(ACK_UNSAFE_CLAIM)
    return tuple(required)


def _candidate_row(
    cand: OptionalSolverPluginManifestActivationCandidateInput,
    *,
    preview_available: bool,
    required_acks: tuple[str, ...],
    required_satisfied: bool,
    requested: bool,
    active: bool,
    deactivated: bool,
) -> OptionalSolverPluginManifestActivationCandidateRowViewModel:
    Readiness = OptionalSolverPluginManifestActivationReadiness
    State = OptionalSolverPluginManifestActivationState

    if not preview_available:
        readiness = Readiness.UNAVAILABLE_BEFORE_PREVIEW
    elif deactivated:
        readiness = Readiness.DEACTIVATED
    elif active:
        readiness = Readiness.ACTIVE_CANDIDATE
    elif cand.has_schema_blocker:
        readiness = Readiness.BLOCKED_SCHEMA
    elif cand.has_conflict:
        readiness = Readiness.BLOCKED_CONFLICT
    elif cand.has_unsafe_claim:
        readiness = Readiness.BLOCKED_UNSAFE_CLAIM
    elif not required_satisfied:
        readiness = Readiness.BLOCKED_ACKNOWLEDGEMENT
    else:
        readiness = Readiness.READY

    if readiness == Readiness.UNAVAILABLE_BEFORE_PREVIEW:
        state = State.INACTIVE_PREVIEW
    elif readiness == Readiness.ACTIVE_CANDIDATE:
        state = State.ACTIVE_CANDIDATE
    elif readiness == Readiness.DEACTIVATED:
        state = State.DEACTIVATED
    elif not requested:
        state = State.INACTIVE_PREVIEW
    elif readiness == Readiness.READY:
        state = State.ACTIVATION_READY
    else:
        state = State.ACTIVATION_BLOCKED

    blockers = _candidate_blockers(cand, readiness)
    warnings = _candidate_warnings(cand)
    diagnostics = _candidate_diagnostic_codes(cand, readiness)

    display, redacted = redact_optional_solver_plugin_manifest_source_reference(
        cand.source_reference
    )
    if not display and cand.source_label:
        display = cand.source_label
        redacted = False
    return OptionalSolverPluginManifestActivationCandidateRowViewModel(
        stack_id=cand.stack_id,
        display_name=cand.display_name or cand.stack_id,
        source_type=cand.source_type,
        source_label=cand.source_label,
        source_reference_display=display,
        trust_label=cand.trust_label,
        activation_state=state.value,
        readiness=readiness.value,
        blockers=blockers,
        warnings=warnings,
        required_acknowledgements=required_acks,
        diagnostics=diagnostics,
        built_in_relationship=cand.built_in_relationship,
        unsafe_claim_indicators=tuple(cand.unsafe_claim_indicators),
        redacted_source_reference=redacted,
        is_untrusted=cand.is_untrusted,
    )


def _candidate_blockers(
    cand: OptionalSolverPluginManifestActivationCandidateInput,
    readiness: OptionalSolverPluginManifestActivationReadiness,
) -> tuple[str, ...]:
    Readiness = OptionalSolverPluginManifestActivationReadiness
    blockers: list[str] = []
    if readiness == Readiness.UNAVAILABLE_BEFORE_PREVIEW:
        blockers.append("Preview the manifest before activation.")
    if readiness == Readiness.BLOCKED_SCHEMA:
        blockers.append("Manifest has schema blockers; activation is blocked.")
    if readiness == Readiness.BLOCKED_CONFLICT:
        blockers.append("Built-ins win by default; conflict must be resolved.")
    if readiness == Readiness.BLOCKED_UNSAFE_CLAIM:
        blockers.append("Manifest contains unsafe claims; activation is blocked.")
    if readiness == Readiness.BLOCKED_ACKNOWLEDGEMENT:
        blockers.append("Required acknowledgements are missing.")
    return tuple(blockers)


def _candidate_warnings(
    cand: OptionalSolverPluginManifestActivationCandidateInput,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if cand.is_untrusted:
        warnings.append("Untrusted source; untrusted by default.")
    warnings.append(TRUST_NOT_CERTIFICATION_TEXT)
    return tuple(warnings)


def _candidate_diagnostic_codes(
    cand: OptionalSolverPluginManifestActivationCandidateInput,
    readiness: OptionalSolverPluginManifestActivationReadiness,
) -> tuple[str, ...]:
    Readiness = OptionalSolverPluginManifestActivationReadiness
    codes: list[str] = []
    if readiness == Readiness.UNAVAILABLE_BEFORE_PREVIEW:
        codes.append(OSPMG_ACTIVATION_PREVIEW_REQUIRED)
    if readiness == Readiness.BLOCKED_SCHEMA:
        codes.append(OSPMG_ACTIVATION_SCHEMA_BLOCKED)
    if readiness == Readiness.BLOCKED_CONFLICT:
        codes.append(OSPMG_ACTIVATION_CONFLICT_BLOCKED)
    if readiness == Readiness.BLOCKED_UNSAFE_CLAIM:
        codes.append(OSPMG_ACTIVATION_UNSAFE_CLAIM)
    if readiness == Readiness.BLOCKED_ACKNOWLEDGEMENT:
        codes.append(OSPMG_ACTIVATION_ACK_REQUIRED)
    if readiness == Readiness.DEACTIVATED:
        codes.append(OSPMG_ACTIVATION_DEACTIVATED)
    if cand.is_untrusted:
        codes.append(OSPMG_ACTIVATION_UNTRUSTED_SOURCE)
    return tuple(codes)


def _acknowledgement_rows(
    required_acks: tuple[str, ...],
    acks: Mapping[str, bool],
) -> tuple[OptionalSolverPluginManifestActivationAcknowledgementRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestActivationAcknowledgementRowViewModel] = []
    for ack_id in required_acks:
        satisfied = bool(acks.get(ack_id, False))
        rows.append(
            OptionalSolverPluginManifestActivationAcknowledgementRowViewModel(
                acknowledgement_id=ack_id,
                label=_ACK_LABELS.get(ack_id, ack_id),
                required=True,
                satisfied=satisfied,
                blocking=not satisfied,
                reason=(
                    "Required acknowledgement is satisfied."
                    if satisfied
                    else "Required acknowledgement is missing; activation is blocked."
                ),
                related="activation",
                warning_text=_ACK_LABELS.get(ack_id, ack_id),
            )
        )
    return tuple(rows)


def _diagnostics(
    candidate_rows: Sequence[OptionalSolverPluginManifestActivationCandidateRowViewModel],
    *,
    preview_available: bool,
    required_acks: tuple[str, ...],
    required_satisfied: bool,
) -> tuple[OptionalSolverPluginManifestActivationDiagnosticViewModel, ...]:
    Readiness = OptionalSolverPluginManifestActivationReadiness
    items: list[OptionalSolverPluginManifestActivationDiagnosticViewModel] = []

    if not preview_available:
        items.append(
            OptionalSolverPluginManifestActivationDiagnosticViewModel(
                severity="warning",
                category="activation",
                code=OSPMG_ACTIVATION_PREVIEW_REQUIRED,
                message="Preview a manifest before activation is available.",
                blocker=True,
            )
        )

    code_to_severity_blocker = {
        OSPMG_ACTIVATION_SCHEMA_BLOCKED: ("error", True),
        OSPMG_ACTIVATION_CONFLICT_BLOCKED: ("warning", True),
        OSPMG_ACTIVATION_UNSAFE_CLAIM: ("error", True),
        OSPMG_ACTIVATION_ACK_REQUIRED: ("warning", True),
        OSPMG_ACTIVATION_UNTRUSTED_SOURCE: ("warning", False),
        OSPMG_ACTIVATION_DEACTIVATED: ("info", False),
    }
    for row in candidate_rows:
        for code in row.diagnostics:
            severity, blocker = code_to_severity_blocker.get(code, ("info", False))
            items.append(
                OptionalSolverPluginManifestActivationDiagnosticViewModel(
                    severity=severity,
                    category="activation",
                    code=code,
                    message=_diagnostic_message(code),
                    source_reference_display=row.source_reference_display,
                    stack_id=row.stack_id,
                    suggested_fix=_diagnostic_fix(code),
                    blocker=blocker,
                )
            )

    # Persistent informational safety markers (session level).
    for code in (
        OSPMG_ACTIVATION_PREVIEW_ONLY_GATE,
        OSPMG_ACTIVATION_NOT_VALIDATION,
        OSPMG_ACTIVATION_NO_INSTALL,
        OSPMG_ACTIVATION_NO_SOLVER_EXECUTION,
        OSPMG_ACTIVATION_NOT_CERTIFICATION,
    ):
        items.append(
            OptionalSolverPluginManifestActivationDiagnosticViewModel(
                severity="info",
                category="activation",
                code=code,
                message=_diagnostic_message(code),
            )
        )
    if required_acks and not required_satisfied and preview_available:
        # Ensure ack-required is surfaced even when there are no candidate rows.
        if not any(
            row.readiness == Readiness.BLOCKED_ACKNOWLEDGEMENT.value
            for row in candidate_rows
        ):
            items.append(
                OptionalSolverPluginManifestActivationDiagnosticViewModel(
                    severity="warning",
                    category="activation",
                    code=OSPMG_ACTIVATION_ACK_REQUIRED,
                    message=_diagnostic_message(OSPMG_ACTIVATION_ACK_REQUIRED),
                    blocker=True,
                )
            )
    return tuple(items)


def _diagnostic_message(code: str) -> str:
    return {
        OSPMG_ACTIVATION_PREVIEW_REQUIRED: "Activation requires a previewed manifest.",
        OSPMG_ACTIVATION_SCHEMA_BLOCKED: "Activation is blocked by schema diagnostics.",
        OSPMG_ACTIVATION_CONFLICT_BLOCKED: "Activation is blocked by a stack-id conflict.",
        OSPMG_ACTIVATION_UNTRUSTED_SOURCE: "Source is untrusted by default.",
        OSPMG_ACTIVATION_UNSAFE_CLAIM: "Activation is blocked by unsafe manifest claims.",
        OSPMG_ACTIVATION_ACK_REQUIRED: "Required acknowledgements are missing.",
        OSPMG_ACTIVATION_NOT_VALIDATION: "Activation is not validation evidence.",
        OSPMG_ACTIVATION_NO_INSTALL: "Activation does not install dependencies.",
        OSPMG_ACTIVATION_NO_SOLVER_EXECUTION: "Activation does not execute solvers.",
        OSPMG_ACTIVATION_NOT_CERTIFICATION: "A trust label is not certification.",
        OSPMG_ACTIVATION_DEACTIVATED: "Candidate is deactivated.",
        OSPMG_ACTIVATION_PREVIEW_ONLY_GATE: PREVIEW_ONLY_GATE_TEXT,
    }.get(code, code)


def _diagnostic_fix(code: str) -> str:
    return {
        OSPMG_ACTIVATION_SCHEMA_BLOCKED: "Fix manifest schema issues, then re-preview.",
        OSPMG_ACTIVATION_CONFLICT_BLOCKED: "Resolve the duplicate stack id; built-ins win.",
        OSPMG_ACTIVATION_UNSAFE_CLAIM: "Remove unsafe claims from the manifest.",
        OSPMG_ACTIVATION_ACK_REQUIRED: "Satisfy required acknowledgements.",
        OSPMG_ACTIVATION_UNTRUSTED_SOURCE: "Review the untrusted source before activation.",
    }.get(code, "")


def _conflict_row(
    candidate_row: OptionalSolverPluginManifestActivationCandidateRowViewModel,
) -> OptionalSolverPluginManifestActivationConflictRowViewModel:
    return OptionalSolverPluginManifestActivationConflictRowViewModel(
        stack_id=candidate_row.stack_id,
        built_in_source=f"builtin:{candidate_row.stack_id}",
        user_plugin_source=candidate_row.source_reference_display,
        conflict_policy="built-ins win by default; plugin override disabled",
        built_ins_win_default=True,
        activation_state=candidate_row.activation_state,
        required_future_policy=(
            "An explicit future trust/override policy gate is required to activate "
            "a conflicting manifest."
        ),
    )


def _trust_badges(
    candidate_rows: Sequence[OptionalSolverPluginManifestActivationCandidateRowViewModel],
) -> tuple[OptionalSolverPluginManifestActivationTrustBadgeViewModel, ...]:
    seen: dict[tuple[str, str], OptionalSolverPluginManifestActivationTrustBadgeViewModel] = {}
    for row in candidate_rows:
        key = (row.source_type, row.trust_label)
        if key in seen:
            continue
        seen[key] = OptionalSolverPluginManifestActivationTrustBadgeViewModel(
            source_type=row.source_type,
            trust_label=row.trust_label,
            source_label=row.source_label,
            activation_state=row.activation_state,
            warning_text=(
                "Untrusted source; untrusted by default."
                if row.is_untrusted
                else "Built-in/reviewed source; trust label is not certification."
            ),
        )
    return tuple(seen[key] for key in sorted(seen))


def _summary(
    candidate_rows: Sequence[OptionalSolverPluginManifestActivationCandidateRowViewModel],
    *,
    diagnostics: Sequence[OptionalSolverPluginManifestActivationDiagnosticViewModel],
    preview_available: bool,
    required_acks: tuple[str, ...],
    active: set[str],
) -> OptionalSolverPluginManifestActivationSummaryViewModel:
    Readiness = OptionalSolverPluginManifestActivationReadiness
    ready = sum(1 for r in candidate_rows if r.readiness == Readiness.READY.value)
    blocked = sum(1 for r in candidate_rows if r.readiness.startswith("blocked_"))
    active_count = sum(
        1 for r in candidate_rows if r.readiness == Readiness.ACTIVE_CANDIDATE.value
    )
    deactivated_count = sum(
        1 for r in candidate_rows if r.readiness == Readiness.DEACTIVATED.value
    )
    warnings = sum(1 for d in diagnostics if d.severity == "warning")
    errors = sum(1 for d in diagnostics if d.severity in {"error", "blocker"})
    status = (
        "Preview a plugin manifest before activation is available."
        if not preview_available
        else (
            f"Activation preview: {len(candidate_rows)} candidate(s), {ready} ready, "
            f"{blocked} blocked, {active_count} active. Activation is not validation "
            "evidence."
        )
    )
    return OptionalSolverPluginManifestActivationSummaryViewModel(
        preview_sources_count=len(candidate_rows),
        activation_candidates_count=len(candidate_rows),
        activation_ready_count=ready,
        activation_blocked_count=blocked,
        active_candidate_count=active_count,
        deactivated_count=deactivated_count,
        diagnostic_count=len(diagnostics),
        warning_count=warnings,
        error_count=errors,
        acknowledgement_required_count=len(required_acks),
        preview_required_count=0 if preview_available else 1,
        status_text=status,
        activation_performed=bool(active),
    )


def _action_states(
    candidate_rows: Sequence[OptionalSolverPluginManifestActivationCandidateRowViewModel],
    *,
    preview_available: bool,
) -> tuple[OptionalSolverPluginManifestActivationActionState, ...]:
    Action = OptionalSolverPluginManifestActivationAction
    Readiness = OptionalSolverPluginManifestActivationReadiness
    has_candidates = bool(candidate_rows)
    any_ready = any(r.readiness == Readiness.READY.value for r in candidate_rows)
    any_active = any(
        r.readiness == Readiness.ACTIVE_CANDIDATE.value for r in candidate_rows
    )

    def ack_action(action: OptionalSolverPluginManifestActivationAction, label: str):
        return OptionalSolverPluginManifestActivationActionState(
            action=action,
            label=label,
            enabled=preview_available and has_candidates,
            available=True,
            reason="Future GUI acknowledgement toggle; no activation occurs here.",
            future_action=True,
        )

    return (
        OptionalSolverPluginManifestActivationActionState(
            action=Action.REQUEST_ACTIVATION,
            label="Request activation",
            enabled=preview_available and has_candidates,
            available=True,
            reason="Future GUI action; activation implementation is a later gate.",
            future_action=True,
        ),
        ack_action(Action.ACKNOWLEDGE_UNTRUSTED_SOURCE, "Acknowledge untrusted source"),
        ack_action(Action.ACKNOWLEDGE_NO_VALIDATION_PASS, "Acknowledge no validation-pass"),
        ack_action(Action.ACKNOWLEDGE_NO_INSTALL, "Acknowledge no dependency install"),
        ack_action(Action.ACKNOWLEDGE_NO_SOLVER_EXECUTION, "Acknowledge no solver execution"),
        ack_action(Action.ACKNOWLEDGE_NO_CERTIFICATION, "Acknowledge no certification"),
        OptionalSolverPluginManifestActivationActionState(
            action=Action.ACTIVATE_CANDIDATE,
            label="Activate candidate",
            enabled=False,
            available=any_ready,
            reason=(
                "Activation implementation is a future gate "
                "(OSW-EXP-080); no activation occurs in this view-model."
            ),
            future_action=True,
        ),
        OptionalSolverPluginManifestActivationActionState(
            action=Action.DEACTIVATE_CANDIDATE,
            label="Deactivate candidate",
            enabled=False,
            available=any_active,
            reason="Deactivation is a future gate (OSW-EXP-081).",
            future_action=True,
        ),
        OptionalSolverPluginManifestActivationActionState(
            action=Action.RUN_DISCOVERY_WITH_ACTIVATED_MANIFESTS,
            label="Run discovery with activated manifests",
            enabled=False,
            available=False,
            reason="Discovery integration is a future gate (OSW-EXP-082).",
        ),
        OptionalSolverPluginManifestActivationActionState(
            action=Action.RUN_VALIDATION,
            label="Run validation",
            enabled=False,
            available=False,
            reason="Validation requires a separate OSW-VALID gate.",
        ),
        OptionalSolverPluginManifestActivationActionState(
            action=Action.INSTALL_DEPENDENCY,
            label="Install dependency",
            enabled=False,
            available=False,
            reason="Dependency installation is unavailable.",
        ),
        OptionalSolverPluginManifestActivationActionState(
            action=Action.EXECUTE_SOLVER,
            label="Execute solver",
            enabled=False,
            available=False,
            reason="Solver execution is unavailable.",
        ),
        OptionalSolverPluginManifestActivationActionState(
            action=Action.CLOSE_ISSUE,
            label="Close issue",
            enabled=False,
            available=False,
            reason="Issue closure requires a separate validation and closure gate.",
        ),
        OptionalSolverPluginManifestActivationActionState(
            action=Action.EXPORT_REDACTED_SUMMARY,
            label="Export redacted summary",
            enabled=has_candidates,
            available=True,
            reason="Produces an in-memory redacted summary only; it writes no files.",
            future_action=False,
        ),
    )


def _guidance_text() -> tuple[str, ...]:
    return (
        "Activation preview is data-only.",
        PREVIEW_ONLY_GATE_TEXT,
        ACTIVE_NOT_VALIDATION_TEXT,
        TRUST_NOT_CERTIFICATION_TEXT,
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Activation is not validation, installation, discovery, or solver execution.",
        "Built-in manifests win by default; conflicts require an explicit future policy.",
    )


def _safety_text() -> tuple[str, ...]:
    return (
        "No activation persistence.",
        "No GUI activation behavior.",
        "No CLI activation behavior.",
        "No plugin package import.",
        "No directory scan.",
        "No network fetch.",
        "No discovery execution.",
        "No validation execution.",
        "No solver execution.",
        "No dependency installation.",
        "No issue mutation.",
        "No release mutation.",
    )


__all__ = [
    "ACK_CONFLICT_OR_OVERRIDE",
    "ACK_NO_CERTIFICATION",
    "ACK_NO_DEPENDENCY_INSTALL",
    "ACK_NO_ISSUE_CLOSURE",
    "ACK_NO_SOLVER_EXECUTION",
    "ACK_NO_VALIDATION_PASS",
    "ACK_UNSAFE_CLAIM",
    "ACK_UNTRUSTED_SOURCE",
    "OSPMG_ACTIVATION_ACK_REQUIRED",
    "OSPMG_ACTIVATION_CONFLICT_BLOCKED",
    "OSPMG_ACTIVATION_DEACTIVATED",
    "OSPMG_ACTIVATION_DIAGNOSTIC_CODES",
    "OSPMG_ACTIVATION_NO_INSTALL",
    "OSPMG_ACTIVATION_NO_SOLVER_EXECUTION",
    "OSPMG_ACTIVATION_NOT_CERTIFICATION",
    "OSPMG_ACTIVATION_NOT_VALIDATION",
    "OSPMG_ACTIVATION_PREVIEW_ONLY_GATE",
    "OSPMG_ACTIVATION_PREVIEW_REQUIRED",
    "OSPMG_ACTIVATION_SCHEMA_BLOCKED",
    "OSPMG_ACTIVATION_UNSAFE_CLAIM",
    "OSPMG_ACTIVATION_UNTRUSTED_SOURCE",
    "OptionalSolverPluginManifestActivationAcknowledgementRowViewModel",
    "OptionalSolverPluginManifestActivationAction",
    "OptionalSolverPluginManifestActivationActionState",
    "OptionalSolverPluginManifestActivationCandidateInput",
    "OptionalSolverPluginManifestActivationCandidateRowViewModel",
    "OptionalSolverPluginManifestActivationConflictRowViewModel",
    "OptionalSolverPluginManifestActivationDiagnosticViewModel",
    "OptionalSolverPluginManifestActivationReadiness",
    "OptionalSolverPluginManifestActivationState",
    "OptionalSolverPluginManifestActivationSummaryViewModel",
    "OptionalSolverPluginManifestActivationTrustBadgeViewModel",
    "OptionalSolverPluginManifestActivationViewModel",
    "build_optional_solver_plugin_manifest_activation_viewmodel",
    "explain_optional_solver_plugin_manifest_activation_viewmodel",
    "render_optional_solver_plugin_manifest_activation_summary",
    "summarize_optional_solver_plugin_manifest_activation_viewmodel",
]
