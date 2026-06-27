"""Pure view-model extension for optional solver plugin manifest deactivation.

This module is the OSW-EXP-085 implementation of the deactivation view-model
extension designed in OSW-EXP-081. It transforms already-supplied activation
candidate state (an OSW-EXP-079 activation view-model or caller-supplied
deactivation candidate records) plus caller-supplied acknowledgement state into
deterministic deactivation-readiness, acknowledgement, diagnostic, shared-stack,
evidence-retention, trust, and action-state records.

It performs no side effects. It does not deactivate anything, persist activation
or deactivation state, read or write files, delete files, parse JSON from a path,
import PySide/Qt, import plugin packages, scan directories, fetch URLs, run
discovery, run validation, execute solvers, install or uninstall dependencies,
uninstall solvers, or mutate issues/releases. Deactivation lifecycle inputs and
acknowledgement satisfaction are SUPPLIED by the caller; this layer only
classifies and renders them. Deactivation persistence, GUI behavior, CLI
behavior, discovery integration, validation, install/uninstall, solver
execution, issue closure, and release mutation remain future-gated.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum

from .plugin_manifest_activation_viewmodel import (
    OptionalSolverPluginManifestActivationViewModel,
)
from .plugin_manifest_explicit_import_gui_viewmodel import (
    redact_optional_solver_plugin_manifest_source_reference,
)

# Design-only OSPMG_DEACTIVATION_* diagnostic vocabulary reserved by OSW-EXP-081.
OSPMG_DEACTIVATION_ACTIVE_REQUIRED = "OSPMG_DEACTIVATION_ACTIVE_REQUIRED"
OSPMG_DEACTIVATION_ACK_REQUIRED = "OSPMG_DEACTIVATION_ACK_REQUIRED"
OSPMG_DEACTIVATION_NOT_FILE_DELETE = "OSPMG_DEACTIVATION_NOT_FILE_DELETE"
OSPMG_DEACTIVATION_NOT_UNINSTALL = "OSPMG_DEACTIVATION_NOT_UNINSTALL"
OSPMG_DEACTIVATION_NOT_VALIDATION = "OSPMG_DEACTIVATION_NOT_VALIDATION"
OSPMG_DEACTIVATION_NO_DISCOVERY_EXECUTION = "OSPMG_DEACTIVATION_NO_DISCOVERY_EXECUTION"
OSPMG_DEACTIVATION_NO_SOLVER_EXECUTION = "OSPMG_DEACTIVATION_NO_SOLVER_EXECUTION"
OSPMG_DEACTIVATION_NOT_ISSUE_CLOSURE = "OSPMG_DEACTIVATION_NOT_ISSUE_CLOSURE"
OSPMG_DEACTIVATION_NOT_RELEASE_MUTATION = "OSPMG_DEACTIVATION_NOT_RELEASE_MUTATION"
OSPMG_DEACTIVATION_EVIDENCE_RETAINED = "OSPMG_DEACTIVATION_EVIDENCE_RETAINED"
OSPMG_DEACTIVATION_SHARED_STACK_WARNING = "OSPMG_DEACTIVATION_SHARED_STACK_WARNING"
OSPMG_DEACTIVATION_STATE_CONFLICT = "OSPMG_DEACTIVATION_STATE_CONFLICT"
OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED = (
    "OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED"
)
OSPMG_DEACTIVATION_DEACTIVATED = "OSPMG_DEACTIVATION_DEACTIVATED"

#: All reserved deactivation diagnostic codes, in design order.
OSPMG_DEACTIVATION_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_DEACTIVATION_ACTIVE_REQUIRED,
    OSPMG_DEACTIVATION_ACK_REQUIRED,
    OSPMG_DEACTIVATION_NOT_FILE_DELETE,
    OSPMG_DEACTIVATION_NOT_UNINSTALL,
    OSPMG_DEACTIVATION_NOT_VALIDATION,
    OSPMG_DEACTIVATION_NO_DISCOVERY_EXECUTION,
    OSPMG_DEACTIVATION_NO_SOLVER_EXECUTION,
    OSPMG_DEACTIVATION_NOT_ISSUE_CLOSURE,
    OSPMG_DEACTIVATION_NOT_RELEASE_MUTATION,
    OSPMG_DEACTIVATION_EVIDENCE_RETAINED,
    OSPMG_DEACTIVATION_SHARED_STACK_WARNING,
    OSPMG_DEACTIVATION_STATE_CONFLICT,
    OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED,
    OSPMG_DEACTIVATION_DEACTIVATED,
)

# Acknowledgement identifiers (OSW-EXP-081).
ACK_NOT_FILE_DELETION = "not_file_deletion"
ACK_NOT_DEPENDENCY_UNINSTALL = "not_dependency_uninstall"
ACK_NOT_SOLVER_UNINSTALL = "not_solver_uninstall"
ACK_NOT_ISSUE_CLOSURE = "not_issue_closure"
ACK_NOT_RELEASE_MUTATION = "not_release_mutation"
ACK_NOT_VALIDATION_EVIDENCE_DELETION = "not_validation_evidence_deletion"
ACK_NO_DISCOVERY_EXECUTION = "no_discovery_execution"
ACK_NO_SOLVER_EXECUTION = "no_solver_execution"
ACK_DEACTIVATION_HISTORY_VISIBLE = "deactivation_history_visible"
ACK_CONFLICT_OR_SHARED_STACK_WARNING = "conflict_or_shared_stack_warning"

#: Acknowledgements always required before deactivation, regardless of conflicts.
DEACTIVATION_ALWAYS_REQUIRED_ACKS: tuple[str, ...] = (
    ACK_NOT_FILE_DELETION,
    ACK_NOT_DEPENDENCY_UNINSTALL,
    ACK_NOT_SOLVER_UNINSTALL,
    ACK_NOT_ISSUE_CLOSURE,
    ACK_NOT_RELEASE_MUTATION,
    ACK_NOT_VALIDATION_EVIDENCE_DELETION,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_SOLVER_EXECUTION,
    ACK_DEACTIVATION_HISTORY_VISIBLE,
)

#: All deactivation acknowledgements, in design order (the last is conditional).
DEACTIVATION_REQUIRED_ACKS: tuple[str, ...] = (
    *DEACTIVATION_ALWAYS_REQUIRED_ACKS,
    ACK_CONFLICT_OR_SHARED_STACK_WARNING,
)

_ACK_LABELS: dict[str, str] = {
    ACK_NOT_FILE_DELETION: "I understand deactivation does not delete the manifest file.",
    ACK_NOT_DEPENDENCY_UNINSTALL: "I understand deactivation does not uninstall dependencies.",
    ACK_NOT_SOLVER_UNINSTALL: "I understand deactivation does not uninstall solvers.",
    ACK_NOT_ISSUE_CLOSURE: "I understand deactivation does not close issues.",
    ACK_NOT_RELEASE_MUTATION: "I understand deactivation does not mutate releases.",
    ACK_NOT_VALIDATION_EVIDENCE_DELETION: (
        "I understand deactivation does not delete validation evidence."
    ),
    ACK_NO_DISCOVERY_EXECUTION: "I understand deactivation does not run discovery.",
    ACK_NO_SOLVER_EXECUTION: "I understand deactivation does not execute solvers.",
    ACK_DEACTIVATION_HISTORY_VISIBLE: "I understand deactivation history stays visible.",
    ACK_CONFLICT_OR_SHARED_STACK_WARNING: (
        "I understand built-ins win and shared-stack conflicts are shown."
    ),
}

TRUST_NOT_CERTIFICATION_TEXT = "A trust label is not certification."
DEACTIVATED_NOT_VALIDATION_TEXT = "A deactivated state is not validation evidence."
DEACTIVATION_NOT_FAILURE_TEXT = "Deactivation is not a validation failure."
DEACTIVATION_NOT_DELETION_TEXT = "Deactivation is not file deletion."
DEACTIVATION_NOT_UNINSTALL_TEXT = "Deactivation is not uninstall."
PERSISTENCE_NOT_IMPLEMENTED_TEXT = (
    "Deactivation persistence is a future gate; this view-model performs no "
    "deactivation, persistence, deletion, uninstall, discovery, validation, or "
    "execution."
)


class OptionalSolverPluginManifestDeactivationState(str, Enum):
    """Deactivation lifecycle state (OSW-EXP-081 state machine)."""

    ACTIVE_CANDIDATE = "active_candidate"
    DEACTIVATION_REQUESTED = "deactivation_requested"
    DEACTIVATION_BLOCKED = "deactivation_blocked"
    DEACTIVATED = "deactivated"
    DEACTIVATION_ERROR = "deactivation_error"
    REACTIVATION_REQUESTED = "reactivation_requested"
    FUTURE_REACTIVATION_REQUIRED = "future_reactivation_required"


class OptionalSolverPluginManifestDeactivationReadiness(str, Enum):
    """Per-view-model deactivation readiness classification."""

    UNAVAILABLE_NO_ACTIVATION_STATE = "unavailable_no_activation_state"
    UNAVAILABLE_NO_ACTIVE_CANDIDATES = "unavailable_no_active_candidates"
    BLOCKED_ACKNOWLEDGEMENT = "blocked_acknowledgement"
    BLOCKED_STATE_CONFLICT = "blocked_state_conflict"
    BLOCKED_SHARED_STACK_WARNING = "blocked_shared_stack_warning"
    READY_NON_PERSISTENT = "ready_non_persistent"
    DEACTIVATED = "deactivated"
    REACTIVATION_FUTURE_GATE = "reactivation_future_gate"
    ERROR = "error"


class OptionalSolverPluginManifestDeactivationAction(str, Enum):
    """Future action identifiers for the deactivation surface."""

    REQUEST_DEACTIVATION = "request_deactivation"
    ACKNOWLEDGE_NOT_FILE_DELETION = "acknowledge_not_file_deletion"
    ACKNOWLEDGE_NOT_DEPENDENCY_UNINSTALL = "acknowledge_not_dependency_uninstall"
    ACKNOWLEDGE_NOT_SOLVER_UNINSTALL = "acknowledge_not_solver_uninstall"
    ACKNOWLEDGE_NOT_ISSUE_CLOSURE = "acknowledge_not_issue_closure"
    ACKNOWLEDGE_NOT_RELEASE_MUTATION = "acknowledge_not_release_mutation"
    ACKNOWLEDGE_NOT_VALIDATION_EVIDENCE_DELETION = (
        "acknowledge_not_validation_evidence_deletion"
    )
    ACKNOWLEDGE_NO_DISCOVERY_EXECUTION = "acknowledge_no_discovery_execution"
    ACKNOWLEDGE_NO_SOLVER_EXECUTION = "acknowledge_no_solver_execution"
    DEACTIVATE_CANDIDATE = "deactivate_candidate"
    REACTIVATE_CANDIDATE = "reactivate_candidate"
    RUN_DISCOVERY = "run_discovery"
    RUN_VALIDATION = "run_validation"
    UNINSTALL_DEPENDENCY = "uninstall_dependency"
    UNINSTALL_SOLVER = "uninstall_solver"
    EXECUTE_SOLVER = "execute_solver"
    CLOSE_ISSUE = "close_issue"
    EXPORT_REDACTED_SUMMARY = "export_redacted_summary"


# Actions that must never be available/enabled in this gate.
_UNSAFE_ACTIONS: frozenset[str] = frozenset(
    {
        OptionalSolverPluginManifestDeactivationAction.RUN_DISCOVERY.value,
        OptionalSolverPluginManifestDeactivationAction.RUN_VALIDATION.value,
        OptionalSolverPluginManifestDeactivationAction.UNINSTALL_DEPENDENCY.value,
        OptionalSolverPluginManifestDeactivationAction.UNINSTALL_SOLVER.value,
        OptionalSolverPluginManifestDeactivationAction.EXECUTE_SOLVER.value,
        OptionalSolverPluginManifestDeactivationAction.CLOSE_ISSUE.value,
    }
)

# Blocked state-machine transitions (OSW-EXP-081), exposed for future gates.
DEACTIVATION_BLOCKED_TRANSITIONS: tuple[str, ...] = (
    "inactive_preview directly to deactivated",
    "deactivation to discovery execution",
    "deactivation to validation execution",
    "deactivation to dependency uninstall",
    "deactivation to solver uninstall",
    "deactivation to solver execution",
    "deactivation to issue closure",
    "deactivation to release mutation",
)

_UNTRUSTED_TRUST_LABELS: frozenset[str] = frozenset(
    {"user_provided", "third_party_plugin", "untrusted", "invalid",
     "untrusted_user_file", "untrusted_plugin_manifest"}
)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationCandidateInput:
    """Caller-supplied deactivation candidate (no file IO performed)."""

    stack_id: str
    display_name: str = ""
    source_type: str = "user_selected_json_file"
    source_label: str = ""
    source_reference: str = ""
    trust_label: str = "untrusted_user_file"
    is_untrusted: bool = True
    activation_state: str = "active_candidate"
    deactivation_requested: bool = False
    deactivated: bool = False
    has_shared_stack: bool = False
    shared_stack_indicators: tuple[str, ...] = ()
    has_state_conflict: bool = False
    built_in: bool = False
    built_in_relationship: str = ""
    historical_evidence_state: str = ""
    evidence_retained: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationActionState:
    """Display-only state for a future deactivation action."""

    action: OptionalSolverPluginManifestDeactivationAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationSummaryViewModel:
    """Summary header values for a deactivation view-model."""

    readiness: str
    state: str
    active_candidate_count: int
    deactivation_candidate_count: int
    deactivation_ready_count: int
    deactivation_blocked_count: int
    deactivated_count: int
    shared_stack_count: int
    state_conflict_count: int
    acknowledgement_required_count: int
    diagnostic_count: int
    warning_count: int
    error_count: int
    evidence_retained_count: int
    status_text: str
    evidence_retained: bool = True
    deactivation_performed: bool = False
    file_deletion_performed: bool = False
    dependency_uninstall_performed: bool = False
    solver_uninstall_performed: bool = False
    discovery_execution_performed: bool = False
    validation_execution_performed: bool = False
    solver_execution_performed: bool = False
    issue_mutation_performed: bool = False
    release_mutation_performed: bool = False
    certification_claimed: bool = False
    not_validation_evidence: bool = True
    third_party_manifests_trusted_by_default: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationCandidateRowViewModel:
    """Deactivation candidate row (not deleted, not trusted by default)."""

    stack_id: str
    display_name: str
    source_type: str
    source_label: str
    source_reference_display: str
    trust_label: str
    activation_state: str
    deactivation_state: str
    readiness: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    required_acknowledgements: tuple[str, ...]
    diagnostics: tuple[str, ...]
    built_in_relationship: str
    shared_stack_indicators: tuple[str, ...]
    historical_evidence_state: str
    evidence_retained: bool
    redacted_source_reference: bool
    is_untrusted: bool
    not_validation_failure_text: str = DEACTIVATION_NOT_FAILURE_TEXT
    not_file_deletion_text: str = DEACTIVATION_NOT_DELETION_TEXT
    not_uninstall_text: str = DEACTIVATION_NOT_UNINSTALL_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationAcknowledgementRowViewModel:
    """Acknowledgement row for the deactivation surface."""

    acknowledgement_id: str
    label: str
    required: bool
    satisfied: bool
    blocking: bool
    reason: str
    related: str
    warning_text: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationDiagnosticViewModel:
    """Deactivation (OSPMG_DEACTIVATION) level diagnostic record."""

    severity: str
    category: str
    code: str
    message: str
    source_reference_display: str = ""
    stack_id: str = ""
    suggested_fix: str = ""
    blocker: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationSharedStackRowViewModel:
    """Shared-stack / conflict row for the deactivation surface."""

    stack_id: str
    built_in_source: str
    user_plugin_source: str
    active_source_state: str
    deactivated_source_state: str
    built_ins_win_default: bool
    deactivating_user_source_keeps_built_ins: str
    required_future_policy: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationEvidenceRowViewModel:
    """Evidence-retention row for the deactivation surface."""

    stack_id: str
    historical_evidence_state: str
    evidence_retained: bool
    not_validation_failure_text: str = DEACTIVATION_NOT_FAILURE_TEXT
    skipped_missing_remains_text: str = (
        "Skipped-missing optional validation remains skipped-missing."
    )
    issue_closure_not_implied_text: str = (
        "Deactivation does not close issues or imply issue closure."
    )
    evidence_not_deleted_text: str = (
        "Historical validation evidence is not deleted or rewritten."
    )


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationTrustBadgeViewModel:
    """Source/trust/provenance badge for the deactivation surface."""

    source_type: str
    trust_label: str
    source_label: str
    activation_state: str
    deactivation_state: str
    warning_text: str
    trust_label_is_not_certification: str = TRUST_NOT_CERTIFICATION_TEXT
    deactivated_is_not_validation_evidence: str = DEACTIVATED_NOT_VALIDATION_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivationViewModel:
    """Complete pure view-model for the deactivation surface."""

    summary: OptionalSolverPluginManifestDeactivationSummaryViewModel
    candidate_rows: tuple[
        OptionalSolverPluginManifestDeactivationCandidateRowViewModel, ...
    ]
    acknowledgement_rows: tuple[
        OptionalSolverPluginManifestDeactivationAcknowledgementRowViewModel, ...
    ]
    diagnostics: tuple[OptionalSolverPluginManifestDeactivationDiagnosticViewModel, ...]
    shared_stack_rows: tuple[
        OptionalSolverPluginManifestDeactivationSharedStackRowViewModel, ...
    ]
    evidence_rows: tuple[
        OptionalSolverPluginManifestDeactivationEvidenceRowViewModel, ...
    ]
    trust_badges: tuple[
        OptionalSolverPluginManifestDeactivationTrustBadgeViewModel, ...
    ]
    actions: tuple[OptionalSolverPluginManifestDeactivationActionState, ...]
    guidance_text: tuple[str, ...]
    safety_text: tuple[str, ...]
    reserved_diagnostic_codes: tuple[str, ...] = OSPMG_DEACTIVATION_DIAGNOSTIC_CODES
    blocked_transitions: tuple[str, ...] = DEACTIVATION_BLOCKED_TRANSITIONS
    not_validation_evidence: bool = True

    # ------------------------------------------------------------------
    # Convenience constructors (transform supplied data only; no side effects).
    # ------------------------------------------------------------------
    @classmethod
    def from_candidates(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestDeactivationCandidateInput],
        *,
        acknowledgements: Mapping[str, bool] | None = None,
    ) -> OptionalSolverPluginManifestDeactivationViewModel:
        return build_optional_solver_plugin_manifest_deactivation_viewmodel(
            candidates, acknowledgements=acknowledgements, activation_state_supplied=True
        )

    @classmethod
    def from_activation_viewmodel(
        cls,
        activation_view_model: OptionalSolverPluginManifestActivationViewModel,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
    ) -> OptionalSolverPluginManifestDeactivationViewModel:
        candidates = _candidates_from_activation_view_model(activation_view_model)
        return build_optional_solver_plugin_manifest_deactivation_viewmodel(
            candidates, acknowledgements=acknowledgements, activation_state_supplied=True
        )

    @classmethod
    def unavailable(cls) -> OptionalSolverPluginManifestDeactivationViewModel:
        return build_optional_solver_plugin_manifest_deactivation_viewmodel(
            (), activation_state_supplied=False
        )

    @classmethod
    def all_deactivated(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestDeactivationCandidateInput],
    ) -> OptionalSolverPluginManifestDeactivationViewModel:
        deactivated = tuple(
            replace(c, deactivated=True, activation_state="deactivated")
            for c in candidates
        )
        return build_optional_solver_plugin_manifest_deactivation_viewmodel(
            deactivated, activation_state_supplied=True
        )

    @classmethod
    def all_blocked(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestDeactivationCandidateInput],
    ) -> OptionalSolverPluginManifestDeactivationViewModel:
        return build_optional_solver_plugin_manifest_deactivation_viewmodel(
            candidates, acknowledgements={}, activation_state_supplied=True
        )


def redact_optional_solver_plugin_manifest_deactivation_source_reference(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool]:
    """Return a safe display reference and a redaction flag (no filesystem access)."""

    return redact_optional_solver_plugin_manifest_source_reference(
        reference, provided_label=provided_label
    )


def build_optional_solver_plugin_manifest_deactivation_viewmodel(
    candidates: Sequence[OptionalSolverPluginManifestDeactivationCandidateInput],
    *,
    acknowledgements: Mapping[str, bool] | None = None,
    activation_state_supplied: bool = True,
) -> OptionalSolverPluginManifestDeactivationViewModel:
    """Build the deactivation view-model from supplied candidates and state."""

    acks = {str(k): bool(v) for k, v in (acknowledgements or {}).items()}

    non_built_in = [c for c in candidates if not c.built_in]
    actives = [
        c for c in non_built_in
        if not c.deactivated and c.activation_state == "active_candidate"
    ]
    deactivated = [c for c in non_built_in if c.deactivated]
    any_conflict = any(c.has_state_conflict for c in actives)
    any_shared = any(c.has_shared_stack for c in actives)

    shared_ack_required = any_shared or any_conflict
    required_acks = _required_acks(shared_ack_required)
    acks_satisfied = all(acks.get(ack, False) for ack in required_acks)

    readiness = _readiness(
        activation_state_supplied=activation_state_supplied,
        candidates=list(candidates),
        actives=actives,
        deactivated=deactivated,
        any_conflict=any_conflict,
        any_shared=any_shared,
        shared_ack=acks.get(ACK_CONFLICT_OR_SHARED_STACK_WARNING, False),
        acks_satisfied=acks_satisfied,
    )
    state = _state(readiness)

    candidate_rows = tuple(
        _candidate_row(c, acks=acks, acks_satisfied=acks_satisfied)
        for c in sorted(candidates, key=lambda c: (not c.built_in, c.stack_id))
    )
    acknowledgement_rows = _acknowledgement_rows(acks, shared_ack_required=shared_ack_required)
    shared_stack_rows = tuple(
        _shared_stack_row(c)
        for c in sorted(non_built_in, key=lambda c: c.stack_id)
        if c.has_shared_stack or c.has_state_conflict
    )
    evidence_rows = tuple(
        _evidence_row(c)
        for c in sorted(non_built_in, key=lambda c: c.stack_id)
        if c.historical_evidence_state
    )
    diagnostics = _diagnostics(
        readiness=readiness,
        actives=actives,
        deactivated=deactivated,
        any_conflict=any_conflict,
        any_shared=any_shared,
        acks_satisfied=acks_satisfied,
        evidence_rows=evidence_rows,
    )
    trust_badges = _trust_badges(candidate_rows)
    summary = _summary(
        readiness=readiness,
        state=state,
        actives=actives,
        deactivated=deactivated,
        non_built_in=non_built_in,
        candidate_rows=candidate_rows,
        shared_stack_rows=shared_stack_rows,
        evidence_rows=evidence_rows,
        diagnostics=diagnostics,
        required_acks=required_acks,
    )
    return OptionalSolverPluginManifestDeactivationViewModel(
        summary=summary,
        candidate_rows=candidate_rows,
        acknowledgement_rows=acknowledgement_rows,
        diagnostics=diagnostics,
        shared_stack_rows=shared_stack_rows,
        evidence_rows=evidence_rows,
        trust_badges=trust_badges,
        actions=_action_states(),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
    )


def render_optional_solver_plugin_manifest_deactivation_summary(
    view_model: OptionalSolverPluginManifestDeactivationViewModel,
) -> dict[str, object]:
    """Return an in-memory, redacted, JSON-ready summary (writes no files)."""

    summary = view_model.summary
    return {
        "readiness": summary.readiness,
        "state": summary.state,
        "active_candidate_count": summary.active_candidate_count,
        "deactivation_candidate_count": summary.deactivation_candidate_count,
        "deactivation_ready_count": summary.deactivation_ready_count,
        "deactivation_blocked_count": summary.deactivation_blocked_count,
        "deactivated_count": summary.deactivated_count,
        "evidence_retained": summary.evidence_retained,
        "deactivation_performed": summary.deactivation_performed,
        "file_deletion_performed": False,
        "dependency_uninstall_performed": False,
        "solver_uninstall_performed": False,
        "discovery_execution_performed": False,
        "validation_execution_performed": False,
        "solver_execution_performed": False,
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
                "deactivation_state": row.deactivation_state,
                "readiness": row.readiness,
                "redacted_source_reference": row.redacted_source_reference,
            }
            for row in view_model.candidate_rows
        ],
        "diagnostics": [
            {"code": d.code, "severity": d.severity, "stack_id": d.stack_id}
            for d in view_model.diagnostics
        ],
    }


def summarize_optional_solver_plugin_manifest_deactivation_viewmodel(
    view_model: OptionalSolverPluginManifestDeactivationViewModel,
) -> str:
    """Return a concise deactivation summary."""

    s = view_model.summary
    return (
        "Optional solver plugin manifest deactivation: "
        f"readiness={s.readiness}; state={s.state}; "
        f"active={s.active_candidate_count}; "
        f"deactivation_ready={s.deactivation_ready_count}; "
        f"blocked={s.deactivation_blocked_count}; "
        f"deactivated={s.deactivated_count}. "
        f"{PERSISTENCE_NOT_IMPLEMENTED_TEXT}"
    )


def explain_optional_solver_plugin_manifest_deactivation_viewmodel(
    view_model: OptionalSolverPluginManifestDeactivationViewModel,
) -> str:
    """Explain the safety boundary of the deactivation view-model."""

    disabled = ", ".join(
        action.action.value for action in view_model.actions if not action.enabled
    )
    return (
        summarize_optional_solver_plugin_manifest_deactivation_viewmodel(view_model)
        + " The view-model transforms supplied activation/candidate data only; it "
        "does not deactivate anything, persist activation or deactivation state, "
        "delete files, uninstall dependencies or solvers, import plugin packages, "
        "scan directories, fetch network manifests, run discovery, run validation, "
        "execute solvers, install dependencies, mutate issues, or mutate releases. "
        f"Disabled or future-only actions: {disabled}."
    )


# ----------------------------------------------------------------------
# Internal helpers (pure).
# ----------------------------------------------------------------------
def _required_acks(shared_ack_required: bool) -> tuple[str, ...]:
    if shared_ack_required:
        return DEACTIVATION_REQUIRED_ACKS
    return DEACTIVATION_ALWAYS_REQUIRED_ACKS


def _candidates_from_activation_view_model(
    activation_view_model: OptionalSolverPluginManifestActivationViewModel,
) -> tuple[OptionalSolverPluginManifestDeactivationCandidateInput, ...]:
    conflict_stack_ids = {row.stack_id for row in activation_view_model.conflict_rows}
    candidates: list[OptionalSolverPluginManifestDeactivationCandidateInput] = []
    for row in activation_view_model.candidate_rows:
        candidates.append(
            OptionalSolverPluginManifestDeactivationCandidateInput(
                stack_id=row.stack_id,
                display_name=row.display_name,
                source_type=row.source_type,
                source_label=row.source_label,
                source_reference=row.source_reference_display,
                trust_label=row.trust_label,
                is_untrusted=row.is_untrusted,
                activation_state=row.activation_state,
                deactivated=row.activation_state == "deactivated",
                has_shared_stack=row.stack_id in conflict_stack_ids,
                shared_stack_indicators=(
                    ("duplicate stack id",) if row.stack_id in conflict_stack_ids else ()
                ),
                built_in=row.source_type == "built_in",
                built_in_relationship=row.built_in_relationship,
            )
        )
    return tuple(candidates)


def _readiness(
    *,
    activation_state_supplied: bool,
    candidates: list,
    actives: list,
    deactivated: list,
    any_conflict: bool,
    any_shared: bool,
    shared_ack: bool,
    acks_satisfied: bool,
) -> OptionalSolverPluginManifestDeactivationReadiness:
    Readiness = OptionalSolverPluginManifestDeactivationReadiness
    if not activation_state_supplied and not candidates:
        return Readiness.UNAVAILABLE_NO_ACTIVATION_STATE
    if not actives:
        if deactivated:
            return Readiness.DEACTIVATED
        return Readiness.UNAVAILABLE_NO_ACTIVE_CANDIDATES
    if any_conflict:
        return Readiness.BLOCKED_STATE_CONFLICT
    if any_shared and not shared_ack:
        return Readiness.BLOCKED_SHARED_STACK_WARNING
    if not acks_satisfied:
        return Readiness.BLOCKED_ACKNOWLEDGEMENT
    return Readiness.READY_NON_PERSISTENT


def _state(
    readiness: OptionalSolverPluginManifestDeactivationReadiness,
) -> str:
    State = OptionalSolverPluginManifestDeactivationState
    Readiness = OptionalSolverPluginManifestDeactivationReadiness
    if readiness == Readiness.DEACTIVATED:
        return State.DEACTIVATED.value
    if readiness == Readiness.ERROR:
        return State.DEACTIVATION_ERROR.value
    if readiness == Readiness.REACTIVATION_FUTURE_GATE:
        return State.FUTURE_REACTIVATION_REQUIRED.value
    if readiness.value.startswith("blocked"):
        return State.DEACTIVATION_BLOCKED.value
    if readiness == Readiness.READY_NON_PERSISTENT:
        return State.DEACTIVATION_REQUESTED.value
    return State.ACTIVE_CANDIDATE.value


def _candidate_row(
    candidate: OptionalSolverPluginManifestDeactivationCandidateInput,
    *,
    acks: Mapping[str, bool],
    acks_satisfied: bool,
) -> OptionalSolverPluginManifestDeactivationCandidateRowViewModel:
    State = OptionalSolverPluginManifestDeactivationState
    display, redacted = redact_optional_solver_plugin_manifest_source_reference(
        candidate.source_reference
    )
    if not display and candidate.source_label:
        display = candidate.source_label
        redacted = False

    blockers: list[str] = []
    warnings: list[str] = []
    if candidate.is_untrusted:
        warnings.append("Untrusted source; untrusted by default.")
    warnings.append(TRUST_NOT_CERTIFICATION_TEXT)
    shared_ack = acks.get(ACK_CONFLICT_OR_SHARED_STACK_WARNING, False)

    if candidate.deactivated:
        deactivation_state = State.DEACTIVATED.value
        readiness = "deactivated"
    elif candidate.built_in:
        deactivation_state = State.ACTIVE_CANDIDATE.value
        readiness = "built_in_protected"
        blockers.append(
            "Built-ins are authoritative; deactivating a user/plugin source does "
            "not deactivate built-ins."
        )
    elif candidate.has_state_conflict:
        deactivation_state = State.DEACTIVATION_BLOCKED.value
        readiness = "blocked_state_conflict"
        blockers.append("A deactivation state conflict must be resolved first.")
    elif candidate.activation_state != "active_candidate":
        deactivation_state = State.DEACTIVATION_BLOCKED.value
        readiness = "unavailable_not_active"
        blockers.append("Candidate is not active; deactivation is unavailable.")
    elif candidate.has_shared_stack and not shared_ack:
        deactivation_state = State.DEACTIVATION_BLOCKED.value
        readiness = "blocked_shared_stack_warning"
        blockers.append("Shared-stack warning must be acknowledged before deactivation.")
    elif not acks_satisfied:
        deactivation_state = State.DEACTIVATION_BLOCKED.value
        readiness = "blocked_acknowledgement"
        blockers.append("Required acknowledgements are missing.")
    elif candidate.deactivation_requested:
        deactivation_state = State.DEACTIVATION_REQUESTED.value
        readiness = "ready_non_persistent"
    else:
        deactivation_state = State.ACTIVE_CANDIDATE.value
        readiness = "ready_non_persistent"

    return OptionalSolverPluginManifestDeactivationCandidateRowViewModel(
        stack_id=candidate.stack_id,
        display_name=candidate.display_name or candidate.stack_id,
        source_type=candidate.source_type,
        source_label=candidate.source_label,
        source_reference_display=display,
        trust_label=candidate.trust_label,
        activation_state=candidate.activation_state,
        deactivation_state=deactivation_state,
        readiness=readiness,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        required_acknowledgements=_required_acks(
            candidate.has_shared_stack or candidate.has_state_conflict
        ),
        diagnostics=(),
        built_in_relationship=candidate.built_in_relationship,
        shared_stack_indicators=tuple(candidate.shared_stack_indicators),
        historical_evidence_state=candidate.historical_evidence_state or "none",
        evidence_retained=candidate.evidence_retained,
        redacted_source_reference=redacted,
        is_untrusted=candidate.is_untrusted,
    )


def _acknowledgement_rows(
    acks: Mapping[str, bool],
    *,
    shared_ack_required: bool,
) -> tuple[OptionalSolverPluginManifestDeactivationAcknowledgementRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestDeactivationAcknowledgementRowViewModel] = []
    for ack_id in DEACTIVATION_REQUIRED_ACKS:
        conditional = ack_id == ACK_CONFLICT_OR_SHARED_STACK_WARNING
        required = (not conditional) or shared_ack_required
        satisfied = bool(acks.get(ack_id, False))
        rows.append(
            OptionalSolverPluginManifestDeactivationAcknowledgementRowViewModel(
                acknowledgement_id=ack_id,
                label=_ACK_LABELS.get(ack_id, ack_id),
                required=required,
                satisfied=satisfied,
                blocking=required and not satisfied,
                reason=(
                    "Required acknowledgement is satisfied."
                    if satisfied
                    else (
                        "Required acknowledgement is missing; deactivation is blocked."
                        if required
                        else "Acknowledgement is only required when shared stacks exist."
                    )
                ),
                related="deactivation",
                warning_text=_ACK_LABELS.get(ack_id, ack_id),
            )
        )
    return tuple(rows)


def _diagnostics(
    *,
    readiness: OptionalSolverPluginManifestDeactivationReadiness,
    actives: list,
    deactivated: list,
    any_conflict: bool,
    any_shared: bool,
    acks_satisfied: bool,
    evidence_rows: Sequence,
) -> tuple[OptionalSolverPluginManifestDeactivationDiagnosticViewModel, ...]:
    Readiness = OptionalSolverPluginManifestDeactivationReadiness
    items: list[OptionalSolverPluginManifestDeactivationDiagnosticViewModel] = []

    def add(code: str, severity: str, blocker: bool = False, stack_id: str = "") -> None:
        items.append(
            OptionalSolverPluginManifestDeactivationDiagnosticViewModel(
                severity=severity,
                category="deactivation",
                code=code,
                message=_diagnostic_message(code),
                stack_id=stack_id,
                suggested_fix=_diagnostic_fix(code),
                blocker=blocker,
            )
        )

    if readiness in {
        Readiness.UNAVAILABLE_NO_ACTIVATION_STATE,
        Readiness.UNAVAILABLE_NO_ACTIVE_CANDIDATES,
    }:
        add(OSPMG_DEACTIVATION_ACTIVE_REQUIRED, "warning", blocker=True)
    if any_conflict:
        add(OSPMG_DEACTIVATION_STATE_CONFLICT, "warning", blocker=True)
    if any_shared:
        add(OSPMG_DEACTIVATION_SHARED_STACK_WARNING, "warning", blocker=True)
    if actives and not acks_satisfied:
        add(OSPMG_DEACTIVATION_ACK_REQUIRED, "warning", blocker=True)
    if deactivated:
        add(OSPMG_DEACTIVATION_DEACTIVATED, "info")
    if evidence_rows:
        add(OSPMG_DEACTIVATION_EVIDENCE_RETAINED, "info")

    for code in (
        OSPMG_DEACTIVATION_NOT_FILE_DELETE,
        OSPMG_DEACTIVATION_NOT_UNINSTALL,
        OSPMG_DEACTIVATION_NOT_VALIDATION,
        OSPMG_DEACTIVATION_NO_DISCOVERY_EXECUTION,
        OSPMG_DEACTIVATION_NO_SOLVER_EXECUTION,
        OSPMG_DEACTIVATION_NOT_ISSUE_CLOSURE,
        OSPMG_DEACTIVATION_NOT_RELEASE_MUTATION,
        OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED,
    ):
        add(code, "info")
    return tuple(items)


def _diagnostic_message(code: str) -> str:
    return {
        OSPMG_DEACTIVATION_ACTIVE_REQUIRED: (
            "Deactivation requires a supplied active candidate."
        ),
        OSPMG_DEACTIVATION_ACK_REQUIRED: "Required acknowledgements are missing.",
        OSPMG_DEACTIVATION_NOT_FILE_DELETE: "Deactivation does not delete the manifest file.",
        OSPMG_DEACTIVATION_NOT_UNINSTALL: "Deactivation does not uninstall dependencies/solvers.",
        OSPMG_DEACTIVATION_NOT_VALIDATION: "Deactivation is not a validation failure.",
        OSPMG_DEACTIVATION_NO_DISCOVERY_EXECUTION: "Deactivation does not run discovery.",
        OSPMG_DEACTIVATION_NO_SOLVER_EXECUTION: "Deactivation does not execute solvers.",
        OSPMG_DEACTIVATION_NOT_ISSUE_CLOSURE: "Deactivation does not close issues.",
        OSPMG_DEACTIVATION_NOT_RELEASE_MUTATION: "Deactivation does not mutate releases.",
        OSPMG_DEACTIVATION_EVIDENCE_RETAINED: "Historical validation evidence is retained.",
        OSPMG_DEACTIVATION_SHARED_STACK_WARNING: (
            "A shared stack id requires a warning before deactivation."
        ),
        OSPMG_DEACTIVATION_STATE_CONFLICT: "A deactivation state conflict blocks deactivation.",
        OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED: PERSISTENCE_NOT_IMPLEMENTED_TEXT,
        OSPMG_DEACTIVATION_DEACTIVATED: "Candidate is deactivated (non-active); evidence retained.",
    }.get(code, code)


def _diagnostic_fix(code: str) -> str:
    return {
        OSPMG_DEACTIVATION_ACTIVE_REQUIRED: "Activate a candidate before deactivation.",
        OSPMG_DEACTIVATION_ACK_REQUIRED: "Satisfy required acknowledgements.",
        OSPMG_DEACTIVATION_SHARED_STACK_WARNING: (
            "Acknowledge the shared-stack/built-ins-win warning."
        ),
        OSPMG_DEACTIVATION_STATE_CONFLICT: "Resolve the conflicting supplied state.",
    }.get(code, "")


def _shared_stack_row(
    candidate: OptionalSolverPluginManifestDeactivationCandidateInput,
) -> OptionalSolverPluginManifestDeactivationSharedStackRowViewModel:
    display, _ = redact_optional_solver_plugin_manifest_source_reference(
        candidate.source_reference
    )
    return OptionalSolverPluginManifestDeactivationSharedStackRowViewModel(
        stack_id=candidate.stack_id,
        built_in_source=f"builtin:{candidate.stack_id}",
        user_plugin_source=display or candidate.source_label or candidate.source_type,
        active_source_state=candidate.activation_state,
        deactivated_source_state="deactivated" if candidate.deactivated else "active",
        built_ins_win_default=True,
        deactivating_user_source_keeps_built_ins=(
            "Deactivating a user/plugin source does not deactivate built-ins."
        ),
        required_future_policy=(
            "An explicit future trust/override policy gate is required to change "
            "shared-stack precedence."
        ),
    )


def _evidence_row(
    candidate: OptionalSolverPluginManifestDeactivationCandidateInput,
) -> OptionalSolverPluginManifestDeactivationEvidenceRowViewModel:
    return OptionalSolverPluginManifestDeactivationEvidenceRowViewModel(
        stack_id=candidate.stack_id,
        historical_evidence_state=candidate.historical_evidence_state,
        evidence_retained=candidate.evidence_retained,
    )


def _trust_badges(
    candidate_rows: Sequence[OptionalSolverPluginManifestDeactivationCandidateRowViewModel],
) -> tuple[OptionalSolverPluginManifestDeactivationTrustBadgeViewModel, ...]:
    seen: dict[
        tuple[str, str], OptionalSolverPluginManifestDeactivationTrustBadgeViewModel
    ] = {}
    for row in candidate_rows:
        key = (row.source_type, row.trust_label)
        if key in seen:
            continue
        seen[key] = OptionalSolverPluginManifestDeactivationTrustBadgeViewModel(
            source_type=row.source_type,
            trust_label=row.trust_label,
            source_label=row.source_label,
            activation_state=row.activation_state,
            deactivation_state=row.deactivation_state,
            warning_text=(
                "Untrusted source; untrusted by default."
                if row.is_untrusted
                else "Built-in/reviewed source; trust label is not certification."
            ),
        )
    return tuple(seen[key] for key in sorted(seen))


def _summary(
    *,
    readiness: OptionalSolverPluginManifestDeactivationReadiness,
    state: str,
    actives: list,
    deactivated: list,
    non_built_in: list,
    candidate_rows: Sequence[OptionalSolverPluginManifestDeactivationCandidateRowViewModel],
    shared_stack_rows: Sequence,
    evidence_rows: Sequence,
    diagnostics: Sequence[OptionalSolverPluginManifestDeactivationDiagnosticViewModel],
    required_acks: Sequence[str],
) -> OptionalSolverPluginManifestDeactivationSummaryViewModel:
    ready = sum(1 for r in candidate_rows if r.readiness == "ready_non_persistent")
    blocked = sum(
        1 for r in candidate_rows
        if r.deactivation_state
        == OptionalSolverPluginManifestDeactivationState.DEACTIVATION_BLOCKED.value
    )
    state_conflicts = sum(1 for c in non_built_in if c.has_state_conflict)
    shared = sum(1 for c in non_built_in if c.has_shared_stack)
    warnings = sum(1 for d in diagnostics if d.severity == "warning")
    errors = sum(1 for d in diagnostics if d.severity in {"error", "blocker"})
    status = (
        f"Deactivation ({readiness.value}): {len(actives)} active candidate(s), "
        f"{ready} deactivation-ready, {len(deactivated)} deactivated. Deactivation "
        "is not deletion, uninstall, validation failure, or issue closure."
    )
    return OptionalSolverPluginManifestDeactivationSummaryViewModel(
        readiness=readiness.value,
        state=state,
        active_candidate_count=len(actives),
        deactivation_candidate_count=len(non_built_in),
        deactivation_ready_count=ready,
        deactivation_blocked_count=blocked,
        deactivated_count=len(deactivated),
        shared_stack_count=shared,
        state_conflict_count=state_conflicts,
        acknowledgement_required_count=len(required_acks),
        diagnostic_count=len(diagnostics),
        warning_count=warnings,
        error_count=errors,
        evidence_retained_count=len(evidence_rows),
        status_text=status,
        deactivation_performed=bool(deactivated),
    )


def _action_states() -> tuple[OptionalSolverPluginManifestDeactivationActionState, ...]:
    Action = OptionalSolverPluginManifestDeactivationAction
    states: list[OptionalSolverPluginManifestDeactivationActionState] = []
    for action in Action:
        unsafe = action.value in _UNSAFE_ACTIONS
        states.append(
            OptionalSolverPluginManifestDeactivationActionState(
                action=action,
                label=action.value.replace("_", " ").title(),
                enabled=False,
                available=not unsafe,
                reason=_action_reason(action),
                future_action=True,
            )
        )
    return tuple(states)


def _action_reason(action: OptionalSolverPluginManifestDeactivationAction) -> str:
    Action = OptionalSolverPluginManifestDeactivationAction
    if action.value in _UNSAFE_ACTIONS:
        return {
            Action.RUN_DISCOVERY.value: "Discovery execution is unavailable from this view-model.",
            Action.RUN_VALIDATION.value: "Validation requires a separate OSW-VALID gate.",
            Action.UNINSTALL_DEPENDENCY.value: "Dependency uninstall is unavailable.",
            Action.UNINSTALL_SOLVER.value: "Solver uninstall is unavailable.",
            Action.EXECUTE_SOLVER.value: "Solver execution is unavailable.",
            Action.CLOSE_ISSUE.value: "Issue closure requires separate validation/closure gates.",
        }[action.value]
    if action == Action.EXPORT_REDACTED_SUMMARY:
        return "Produces an in-memory redacted summary only; it writes no files."
    if action in {Action.DEACTIVATE_CANDIDATE, Action.REQUEST_DEACTIVATION}:
        return (
            "Deactivation is display/preview-only; deactivation persistence is a "
            "future gate and this view-model persists nothing."
        )
    if action == Action.REACTIVATE_CANDIDATE:
        return "Reactivation is a future gate; this view-model reactivates nothing."
    return (
        "Future GUI/source action; deactivation persistence is a future gate "
        "(OSW-EXP-086) and this view-model runs nothing."
    )


def _guidance_text() -> tuple[str, ...]:
    return (
        "Deactivation preview is data-only.",
        PERSISTENCE_NOT_IMPLEMENTED_TEXT,
        DEACTIVATED_NOT_VALIDATION_TEXT,
        DEACTIVATION_NOT_FAILURE_TEXT,
        DEACTIVATION_NOT_DELETION_TEXT,
        DEACTIVATION_NOT_UNINSTALL_TEXT,
        TRUST_NOT_CERTIFICATION_TEXT,
        "Built-in manifests win by default; deactivating a user/plugin source "
        "does not deactivate built-ins.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Historical validation evidence is retained and not rewritten.",
        "Issues #6 through #11 remain open; skipped-missing remains skipped-missing.",
    )


def _safety_text() -> tuple[str, ...]:
    return (
        "No deactivation persistence.",
        "No GUI behavior.",
        "No CLI behavior.",
        "No file deletion.",
        "No dependency uninstall.",
        "No solver uninstall.",
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
    "ACK_CONFLICT_OR_SHARED_STACK_WARNING",
    "ACK_DEACTIVATION_HISTORY_VISIBLE",
    "ACK_NOT_DEPENDENCY_UNINSTALL",
    "ACK_NOT_FILE_DELETION",
    "ACK_NOT_ISSUE_CLOSURE",
    "ACK_NOT_RELEASE_MUTATION",
    "ACK_NOT_SOLVER_UNINSTALL",
    "ACK_NOT_VALIDATION_EVIDENCE_DELETION",
    "ACK_NO_DISCOVERY_EXECUTION",
    "ACK_NO_SOLVER_EXECUTION",
    "DEACTIVATION_ALWAYS_REQUIRED_ACKS",
    "DEACTIVATION_BLOCKED_TRANSITIONS",
    "DEACTIVATION_REQUIRED_ACKS",
    "OSPMG_DEACTIVATION_ACK_REQUIRED",
    "OSPMG_DEACTIVATION_ACTIVE_REQUIRED",
    "OSPMG_DEACTIVATION_DEACTIVATED",
    "OSPMG_DEACTIVATION_DIAGNOSTIC_CODES",
    "OSPMG_DEACTIVATION_EVIDENCE_RETAINED",
    "OSPMG_DEACTIVATION_NOT_FILE_DELETE",
    "OSPMG_DEACTIVATION_NOT_ISSUE_CLOSURE",
    "OSPMG_DEACTIVATION_NOT_RELEASE_MUTATION",
    "OSPMG_DEACTIVATION_NOT_UNINSTALL",
    "OSPMG_DEACTIVATION_NOT_VALIDATION",
    "OSPMG_DEACTIVATION_NO_DISCOVERY_EXECUTION",
    "OSPMG_DEACTIVATION_NO_SOLVER_EXECUTION",
    "OSPMG_DEACTIVATION_PERSISTENCE_NOT_IMPLEMENTED",
    "OSPMG_DEACTIVATION_SHARED_STACK_WARNING",
    "OSPMG_DEACTIVATION_STATE_CONFLICT",
    "OptionalSolverPluginManifestDeactivationAcknowledgementRowViewModel",
    "OptionalSolverPluginManifestDeactivationAction",
    "OptionalSolverPluginManifestDeactivationActionState",
    "OptionalSolverPluginManifestDeactivationCandidateInput",
    "OptionalSolverPluginManifestDeactivationCandidateRowViewModel",
    "OptionalSolverPluginManifestDeactivationDiagnosticViewModel",
    "OptionalSolverPluginManifestDeactivationEvidenceRowViewModel",
    "OptionalSolverPluginManifestDeactivationReadiness",
    "OptionalSolverPluginManifestDeactivationSharedStackRowViewModel",
    "OptionalSolverPluginManifestDeactivationState",
    "OptionalSolverPluginManifestDeactivationSummaryViewModel",
    "OptionalSolverPluginManifestDeactivationTrustBadgeViewModel",
    "OptionalSolverPluginManifestDeactivationViewModel",
    "build_optional_solver_plugin_manifest_deactivation_viewmodel",
    "explain_optional_solver_plugin_manifest_deactivation_viewmodel",
    "redact_optional_solver_plugin_manifest_deactivation_source_reference",
    "render_optional_solver_plugin_manifest_deactivation_summary",
    "summarize_optional_solver_plugin_manifest_deactivation_viewmodel",
]
