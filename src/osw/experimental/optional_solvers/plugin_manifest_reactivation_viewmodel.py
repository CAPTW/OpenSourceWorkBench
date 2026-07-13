"""Pure view-model extension for optional solver plugin manifest reactivation.

This module is the OSW-EXP-088 implementation of the reactivation view-model
extension designed in OSW-EXP-087. It transforms already-supplied deactivation
candidate state (an OSW-EXP-085 deactivation view-model or caller-supplied
reactivation candidate records) plus caller-supplied acknowledgement, stale-source,
and history/evidence state into deterministic reactivation-readiness,
acknowledgement, diagnostic, shared-stack, stale-source/re-preview,
deactivation-history, evidence-retention, trust, and action-state records.

It performs no side effects. It does not reactivate anything, automatically
activate candidates, restore trust, persist activation/deactivation/reactivation
state, read or write files, restore/rewrite/delete files, parse JSON from a path,
import PySide/Qt, import plugin packages, scan directories, fetch URLs, run
discovery, run validation, execute solvers, install or uninstall dependencies,
uninstall solvers, or mutate issues/releases. Reactivation lifecycle inputs and
acknowledgement satisfaction are SUPPLIED by the caller; this layer only
classifies and renders them. Reactivation persistence, GUI behavior, CLI
behavior, source/discovery integration, validation, install/uninstall, solver
execution, issue closure, and release mutation remain future-gated.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum

from .plugin_manifest_activation_viewmodel import (
    OptionalSolverPluginManifestActivationViewModel,
)
from .plugin_manifest_deactivation_viewmodel import (
    OptionalSolverPluginManifestDeactivationViewModel,
)
from .plugin_manifest_explicit_import_gui_viewmodel import (
    redact_optional_solver_plugin_manifest_source_reference,
)

# Design-only OSPMG_REACTIVATION_* diagnostic vocabulary reserved by OSW-EXP-087.
OSPMG_REACTIVATION_DEACTIVATED_REQUIRED = "OSPMG_REACTIVATION_DEACTIVATED_REQUIRED"
OSPMG_REACTIVATION_ACK_REQUIRED = "OSPMG_REACTIVATION_ACK_REQUIRED"
OSPMG_REACTIVATION_UNTRUSTED_SOURCE = "OSPMG_REACTIVATION_UNTRUSTED_SOURCE"
OSPMG_REACTIVATION_NOT_TRUST_RESTORE = "OSPMG_REACTIVATION_NOT_TRUST_RESTORE"
OSPMG_REACTIVATION_NOT_VALIDATION = "OSPMG_REACTIVATION_NOT_VALIDATION"
OSPMG_REACTIVATION_NO_INSTALL = "OSPMG_REACTIVATION_NO_INSTALL"
OSPMG_REACTIVATION_NO_SOLVER_EXECUTION = "OSPMG_REACTIVATION_NO_SOLVER_EXECUTION"
OSPMG_REACTIVATION_NOT_ISSUE_CLOSURE = "OSPMG_REACTIVATION_NOT_ISSUE_CLOSURE"
OSPMG_REACTIVATION_NOT_RELEASE_MUTATION = "OSPMG_REACTIVATION_NOT_RELEASE_MUTATION"
OSPMG_REACTIVATION_NOT_CERTIFICATION = "OSPMG_REACTIVATION_NOT_CERTIFICATION"
OSPMG_REACTIVATION_HISTORY_RETAINED = "OSPMG_REACTIVATION_HISTORY_RETAINED"
OSPMG_REACTIVATION_REVIEW_REQUIRED = "OSPMG_REACTIVATION_REVIEW_REQUIRED"
OSPMG_REACTIVATION_CONFLICT_BLOCKED = "OSPMG_REACTIVATION_CONFLICT_BLOCKED"
OSPMG_REACTIVATION_SHARED_STACK_WARNING = "OSPMG_REACTIVATION_SHARED_STACK_WARNING"
OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED = (
    "OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED"
)
OSPMG_REACTIVATION_UNSAFE_CLAIM = "OSPMG_REACTIVATION_UNSAFE_CLAIM"
OSPMG_REACTIVATION_NO_DISCOVERY_EXECUTION = "OSPMG_REACTIVATION_NO_DISCOVERY_EXECUTION"
OSPMG_REACTIVATION_NO_PLUGIN_IMPORT = "OSPMG_REACTIVATION_NO_PLUGIN_IMPORT"
OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED = (
    "OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED"
)
OSPMG_REACTIVATION_FUTURE_GATE = "OSPMG_REACTIVATION_FUTURE_GATE"

#: All reserved reactivation diagnostic codes, in design order.
OSPMG_REACTIVATION_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_REACTIVATION_DEACTIVATED_REQUIRED,
    OSPMG_REACTIVATION_ACK_REQUIRED,
    OSPMG_REACTIVATION_UNTRUSTED_SOURCE,
    OSPMG_REACTIVATION_NOT_TRUST_RESTORE,
    OSPMG_REACTIVATION_NOT_VALIDATION,
    OSPMG_REACTIVATION_NO_INSTALL,
    OSPMG_REACTIVATION_NO_SOLVER_EXECUTION,
    OSPMG_REACTIVATION_NOT_ISSUE_CLOSURE,
    OSPMG_REACTIVATION_NOT_RELEASE_MUTATION,
    OSPMG_REACTIVATION_NOT_CERTIFICATION,
    OSPMG_REACTIVATION_HISTORY_RETAINED,
    OSPMG_REACTIVATION_REVIEW_REQUIRED,
    OSPMG_REACTIVATION_CONFLICT_BLOCKED,
    OSPMG_REACTIVATION_SHARED_STACK_WARNING,
    OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED,
    OSPMG_REACTIVATION_UNSAFE_CLAIM,
    OSPMG_REACTIVATION_NO_DISCOVERY_EXECUTION,
    OSPMG_REACTIVATION_NO_PLUGIN_IMPORT,
    OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED,
    OSPMG_REACTIVATION_FUTURE_GATE,
)

# Acknowledgement identifiers (OSW-EXP-087).
ACK_REACTIVATION_NOT_VALIDATION = "reactivation_not_validation"
ACK_REACTIVATION_NOT_TRUST_RESTORATION = "reactivation_not_trust_restoration"
ACK_REACTIVATION_NOT_INSTALL = "reactivation_not_install"
ACK_REACTIVATION_NO_SOLVER_EXECUTION = "reactivation_no_solver_execution"
ACK_REACTIVATION_NOT_ISSUE_CLOSURE = "reactivation_not_issue_closure"
ACK_REACTIVATION_NOT_RELEASE_MUTATION = "reactivation_not_release_mutation"
ACK_REACTIVATION_HISTORY_RETAINED = "reactivation_history_retained"
ACK_REACTIVATION_REQUIRES_ACTIVATION_REVIEW = "reactivation_requires_activation_review"
ACK_UNTRUSTED_SOURCE = "untrusted_source"
ACK_CONFLICT_OR_SHARED_STACK_WARNING = "conflict_or_shared_stack_warning"
ACK_STALE_SOURCE_REQUIRES_REPREVIEW = "stale_source_requires_repreview"
ACK_NO_DISCOVERY_EXECUTION = "no_discovery_execution"
ACK_NO_PLUGIN_PACKAGE_IMPORT = "no_plugin_package_import"
ACK_TRUST_LABEL_NOT_CERTIFICATION = "trust_label_not_certification"

#: Acknowledgements always required before reactivation, regardless of context.
REACTIVATION_ALWAYS_REQUIRED_ACKS: tuple[str, ...] = (
    ACK_REACTIVATION_NOT_VALIDATION,
    ACK_REACTIVATION_NOT_TRUST_RESTORATION,
    ACK_REACTIVATION_NOT_INSTALL,
    ACK_REACTIVATION_NO_SOLVER_EXECUTION,
    ACK_REACTIVATION_NOT_ISSUE_CLOSURE,
    ACK_REACTIVATION_NOT_RELEASE_MUTATION,
    ACK_REACTIVATION_HISTORY_RETAINED,
    ACK_REACTIVATION_REQUIRES_ACTIVATION_REVIEW,
    ACK_UNTRUSTED_SOURCE,
    ACK_NO_DISCOVERY_EXECUTION,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
    ACK_TRUST_LABEL_NOT_CERTIFICATION,
)

#: Conditional acknowledgements (required only when the situation exists).
ACK_CONDITIONAL_SHARED = ACK_CONFLICT_OR_SHARED_STACK_WARNING
ACK_CONDITIONAL_STALE = ACK_STALE_SOURCE_REQUIRES_REPREVIEW

#: All reactivation acknowledgements, in design order.
REACTIVATION_REQUIRED_ACKS: tuple[str, ...] = (
    *REACTIVATION_ALWAYS_REQUIRED_ACKS,
    ACK_CONFLICT_OR_SHARED_STACK_WARNING,
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW,
)

_ACK_LABELS: dict[str, str] = {
    ACK_REACTIVATION_NOT_VALIDATION: "I understand reactivation is not validation.",
    ACK_REACTIVATION_NOT_TRUST_RESTORATION: (
        "I understand reactivation does not restore trust."
    ),
    ACK_REACTIVATION_NOT_INSTALL: "I understand reactivation does not install dependencies.",
    ACK_REACTIVATION_NO_SOLVER_EXECUTION: "I understand reactivation does not execute solvers.",
    ACK_REACTIVATION_NOT_ISSUE_CLOSURE: "I understand reactivation does not close issues.",
    ACK_REACTIVATION_NOT_RELEASE_MUTATION: "I understand reactivation does not mutate releases.",
    ACK_REACTIVATION_HISTORY_RETAINED: "I understand deactivation history stays retained.",
    ACK_REACTIVATION_REQUIRES_ACTIVATION_REVIEW: (
        "I understand reactivation routes back through activation review."
    ),
    ACK_UNTRUSTED_SOURCE: "I understand user/plugin manifest sources are untrusted.",
    ACK_CONFLICT_OR_SHARED_STACK_WARNING: (
        "I understand built-ins win and shared-stack conflicts are shown."
    ),
    ACK_STALE_SOURCE_REQUIRES_REPREVIEW: (
        "I understand a stale/missing source requires re-preview."
    ),
    ACK_NO_DISCOVERY_EXECUTION: "I understand reactivation does not run discovery.",
    ACK_NO_PLUGIN_PACKAGE_IMPORT: "I understand reactivation does not import plugin packages.",
    ACK_TRUST_LABEL_NOT_CERTIFICATION: "I understand a trust label is not certification.",
}

TRUST_NOT_CERTIFICATION_TEXT = "A trust label is not certification."
REACTIVATION_NOT_VALIDATION_TEXT = "A reactivation state is not validation evidence."
REACTIVATION_NOT_ACTIVATION_TEXT = "Reactivation is not automatic activation."
REACTIVATION_NOT_TRUST_RESTORE_TEXT = "Reactivation is not trust restoration."
PERSISTENCE_NOT_IMPLEMENTED_TEXT = (
    "Reactivation persistence is a future gate; this view-model performs no "
    "reactivation, automatic activation, trust restoration, persistence, file "
    "restore/rewrite/delete, install/uninstall, discovery, validation, or "
    "execution."
)
FUTURE_GATE_TEXT = (
    "Reactivation routes back through future activation review; activation remains "
    "a future, separate gate."
)


class OptionalSolverPluginManifestReactivationState(str, Enum):
    """Reactivation lifecycle state (OSW-EXP-087 state machine)."""

    DEACTIVATED = "deactivated"
    REACTIVATION_REQUESTED = "reactivation_requested"
    REACTIVATION_BLOCKED = "reactivation_blocked"
    REACTIVATION_READY = "reactivation_ready"
    FUTURE_ACTIVATION_REQUIRED = "future_activation_required"
    ACTIVE_CANDIDATE_FUTURE_GATE = "active_candidate_future_gate"
    REACTIVATION_ERROR = "reactivation_error"


class OptionalSolverPluginManifestReactivationReadiness(str, Enum):
    """Per-view-model reactivation readiness classification."""

    UNAVAILABLE_NO_DEACTIVATION_STATE = "unavailable_no_deactivation_state"
    UNAVAILABLE_NO_DEACTIVATED_CANDIDATES = "unavailable_no_deactivated_candidates"
    BLOCKED_ACKNOWLEDGEMENT = "blocked_acknowledgement"
    BLOCKED_CONFLICT = "blocked_conflict"
    BLOCKED_SHARED_STACK_WARNING = "blocked_shared_stack_warning"
    BLOCKED_STALE_SOURCE_REPREVIEW = "blocked_stale_source_repreview"
    BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_claim"
    READY_NON_PERSISTENT = "ready_non_persistent"
    FUTURE_ACTIVATION_REQUIRED = "future_activation_required"
    ACTIVE_CANDIDATE_FUTURE_GATE = "active_candidate_future_gate"
    ERROR = "error"


class OptionalSolverPluginManifestReactivationAction(str, Enum):
    """Future action identifiers for the reactivation surface."""

    REQUEST_REACTIVATION = "request_reactivation"
    ACKNOWLEDGE_REACTIVATION_NOT_VALIDATION = "acknowledge_reactivation_not_validation"
    ACKNOWLEDGE_REACTIVATION_NOT_TRUST_RESTORATION = (
        "acknowledge_reactivation_not_trust_restoration"
    )
    ACKNOWLEDGE_NO_INSTALL = "acknowledge_no_install"
    ACKNOWLEDGE_NO_SOLVER_EXECUTION = "acknowledge_no_solver_execution"
    ACKNOWLEDGE_NO_ISSUE_CLOSURE = "acknowledge_no_issue_closure"
    ACKNOWLEDGE_NO_RELEASE_MUTATION = "acknowledge_no_release_mutation"
    ACKNOWLEDGE_HISTORY_RETAINED = "acknowledge_history_retained"
    ACKNOWLEDGE_ACTIVATION_REVIEW_REQUIRED = "acknowledge_activation_review_required"
    ACKNOWLEDGE_UNTRUSTED_SOURCE = "acknowledge_untrusted_source"
    ACKNOWLEDGE_CONFLICT_OR_SHARED_STACK_WARNING = (
        "acknowledge_conflict_or_shared_stack_warning"
    )
    ACKNOWLEDGE_STALE_SOURCE_REQUIRES_REPREVIEW = (
        "acknowledge_stale_source_requires_repreview"
    )
    ACKNOWLEDGE_NO_DISCOVERY_EXECUTION = "acknowledge_no_discovery_execution"
    ACKNOWLEDGE_NO_PLUGIN_PACKAGE_IMPORT = "acknowledge_no_plugin_package_import"
    ACKNOWLEDGE_TRUST_LABEL_NOT_CERTIFICATION = (
        "acknowledge_trust_label_not_certification"
    )
    REACTIVATE_CANDIDATE = "reactivate_candidate"
    ROUTE_TO_ACTIVATION_REVIEW = "route_to_activation_review"
    RUN_DISCOVERY = "run_discovery"
    RUN_VALIDATION = "run_validation"
    INSTALL_DEPENDENCY = "install_dependency"
    UNINSTALL_DEPENDENCY = "uninstall_dependency"
    UNINSTALL_SOLVER = "uninstall_solver"
    EXECUTE_SOLVER = "execute_solver"
    CLOSE_ISSUE = "close_issue"
    EXPORT_REDACTED_SUMMARY = "export_redacted_summary"


# Actions that must never be available/enabled in this gate.
_UNSAFE_ACTIONS: frozenset[str] = frozenset(
    {
        OptionalSolverPluginManifestReactivationAction.RUN_DISCOVERY.value,
        OptionalSolverPluginManifestReactivationAction.RUN_VALIDATION.value,
        OptionalSolverPluginManifestReactivationAction.INSTALL_DEPENDENCY.value,
        OptionalSolverPluginManifestReactivationAction.UNINSTALL_DEPENDENCY.value,
        OptionalSolverPluginManifestReactivationAction.UNINSTALL_SOLVER.value,
        OptionalSolverPluginManifestReactivationAction.EXECUTE_SOLVER.value,
        OptionalSolverPluginManifestReactivationAction.CLOSE_ISSUE.value,
    }
)

# Blocked state-machine transitions (OSW-EXP-087), exposed for future gates.
REACTIVATION_BLOCKED_TRANSITIONS: tuple[str, ...] = (
    "inactive_preview directly to reactivated",
    "deactivated directly to active_candidate without review and acknowledgements",
    "reactivation to discovery execution",
    "reactivation to validation execution",
    "reactivation to dependency installation",
    "reactivation to solver execution",
    "reactivation to issue closure",
    "reactivation to release mutation",
    "reactivation to certification claim",
)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationCandidateInput:
    """Caller-supplied reactivation candidate (no file IO performed)."""

    stack_id: str
    display_name: str = ""
    source_type: str = "user_selected_json_file"
    source_label: str = ""
    source_reference: str = ""
    trust_label: str = "untrusted_user_file"
    is_untrusted: bool = True
    activation_state: str = "deactivated"
    deactivated: bool = True
    reactivation_requested: bool = False
    future_activation_required: bool = False
    routed_to_activation_gate: bool = False
    has_conflict: bool = False
    has_shared_stack: bool = False
    shared_stack_indicators: tuple[str, ...] = ()
    has_unsafe_claim: bool = False
    unsafe_claim_indicators: tuple[str, ...] = ()
    stale_source: bool = False
    has_error: bool = False
    built_in: bool = False
    built_in_relationship: str = ""
    deactivation_history_state: str = "deactivated_by_user"
    deactivation_history_retained: bool = True
    historical_evidence_state: str = ""
    evidence_retained: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationActionState:
    """Display-only state for a future reactivation action."""

    action: OptionalSolverPluginManifestReactivationAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationSummaryViewModel:
    """Summary header values for a reactivation view-model."""

    readiness: str
    state: str
    deactivated_candidate_count: int
    reactivation_candidate_count: int
    reactivation_ready_count: int
    reactivation_blocked_count: int
    future_activation_required_count: int
    stale_source_repreview_required_count: int
    shared_stack_count: int
    conflict_count: int
    acknowledgement_required_count: int
    diagnostic_count: int
    warning_count: int
    error_count: int
    deactivation_history_retained_count: int
    evidence_retained_count: int
    status_text: str
    deactivation_history_retained: bool = True
    evidence_retained: bool = True
    reactivation_performed: bool = False
    automatic_activation_performed: bool = False
    trust_restoration_performed: bool = False
    file_restore_performed: bool = False
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
    certification_claimed: bool = False
    not_validation_evidence: bool = True
    third_party_manifests_trusted_by_default: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationCandidateRowViewModel:
    """Reactivation candidate row (not trusted, not activated by default)."""

    stack_id: str
    display_name: str
    source_type: str
    source_label: str
    source_reference_display: str
    trust_label: str
    activation_state: str
    deactivation_state: str
    reactivation_state: str
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
    historical_evidence_state: str
    redacted_source_reference: bool
    is_untrusted: bool
    not_automatic_activation_text: str = REACTIVATION_NOT_ACTIVATION_TEXT
    not_trust_restoration_text: str = REACTIVATION_NOT_TRUST_RESTORE_TEXT
    not_validation_evidence_text: str = REACTIVATION_NOT_VALIDATION_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationAcknowledgementRowViewModel:
    """Acknowledgement row for the reactivation surface."""

    acknowledgement_id: str
    label: str
    required: bool
    satisfied: bool
    blocking: bool
    reason: str
    related: str
    warning_text: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationDiagnosticViewModel:
    """Reactivation (OSPMG_REACTIVATION) level diagnostic record."""

    severity: str
    category: str
    code: str
    message: str
    source_reference_display: str = ""
    stack_id: str = ""
    suggested_fix: str = ""
    blocker: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationSharedStackRowViewModel:
    """Shared-stack / conflict row for the reactivation surface."""

    stack_id: str
    built_in_source: str
    user_plugin_source: str
    active_source_state: str
    deactivated_source_state: str
    reactivation_source_state: str
    built_ins_win_default: bool
    reactivating_user_source_keeps_built_ins: str
    required_future_policy: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationStaleSourceRowViewModel:
    """Stale-source / re-preview row for the reactivation surface."""

    stack_id: str
    stale_source_state: str
    repreview_required: bool
    source_reference_display: str
    redacted_source_reference: bool
    not_silently_trusted_text: str = (
        "A missing/moved/changed source is not silently trusted."
    )
    no_file_io_text: str = "No file IO is performed; reactivation reads no files."
    no_file_restore_text: str = (
        "No file restoration, rewrite, or deletion is performed."
    )
    future_policy_text: str = (
        "Re-preview through the explicit import boundary or a future policy is "
        "required before reactivation."
    )


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationEvidenceRowViewModel:
    """Deactivation-history / evidence-retention row."""

    stack_id: str
    deactivation_history_state: str
    deactivation_history_retained: bool
    historical_evidence_state: str
    evidence_retained: bool
    not_validation_success_text: str = "Reactivation is not validation success."
    not_validation_failure_reversal_text: str = (
        "Reactivation is not validation failure reversal."
    )
    skipped_missing_remains_text: str = (
        "Skipped-missing optional validation remains skipped-missing."
    )
    issue_closure_not_implied_text: str = (
        "Reactivation does not close issues or imply issue closure."
    )
    evidence_not_deleted_text: str = (
        "Deactivation history and validation evidence are not deleted or rewritten."
    )


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationTrustBadgeViewModel:
    """Source/trust/provenance badge for the reactivation surface."""

    source_type: str
    trust_label: str
    source_label: str
    activation_state: str
    deactivation_state: str
    reactivation_state: str
    warning_text: str
    trust_label_is_not_certification: str = TRUST_NOT_CERTIFICATION_TEXT
    reactivation_is_not_validation_evidence: str = REACTIVATION_NOT_VALIDATION_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestReactivationViewModel:
    """Complete pure view-model for the reactivation surface."""

    summary: OptionalSolverPluginManifestReactivationSummaryViewModel
    candidate_rows: tuple[
        OptionalSolverPluginManifestReactivationCandidateRowViewModel, ...
    ]
    acknowledgement_rows: tuple[
        OptionalSolverPluginManifestReactivationAcknowledgementRowViewModel, ...
    ]
    diagnostics: tuple[OptionalSolverPluginManifestReactivationDiagnosticViewModel, ...]
    shared_stack_rows: tuple[
        OptionalSolverPluginManifestReactivationSharedStackRowViewModel, ...
    ]
    stale_source_rows: tuple[
        OptionalSolverPluginManifestReactivationStaleSourceRowViewModel, ...
    ]
    evidence_rows: tuple[
        OptionalSolverPluginManifestReactivationEvidenceRowViewModel, ...
    ]
    trust_badges: tuple[
        OptionalSolverPluginManifestReactivationTrustBadgeViewModel, ...
    ]
    actions: tuple[OptionalSolverPluginManifestReactivationActionState, ...]
    guidance_text: tuple[str, ...]
    safety_text: tuple[str, ...]
    reserved_diagnostic_codes: tuple[str, ...] = OSPMG_REACTIVATION_DIAGNOSTIC_CODES
    blocked_transitions: tuple[str, ...] = REACTIVATION_BLOCKED_TRANSITIONS
    not_validation_evidence: bool = True

    # ------------------------------------------------------------------
    # Convenience constructors (transform supplied data only; no side effects).
    # ------------------------------------------------------------------
    @classmethod
    def from_candidates(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestReactivationCandidateInput],
        *,
        acknowledgements: Mapping[str, bool] | None = None,
    ) -> OptionalSolverPluginManifestReactivationViewModel:
        return build_optional_solver_plugin_manifest_reactivation_viewmodel(
            candidates,
            acknowledgements=acknowledgements,
            deactivation_state_supplied=True,
        )

    @classmethod
    def from_deactivation_viewmodel(
        cls,
        deactivation_view_model: OptionalSolverPluginManifestDeactivationViewModel,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
    ) -> OptionalSolverPluginManifestReactivationViewModel:
        candidates = _candidates_from_deactivation_view_model(deactivation_view_model)
        return build_optional_solver_plugin_manifest_reactivation_viewmodel(
            candidates,
            acknowledgements=acknowledgements,
            deactivation_state_supplied=True,
        )

    @classmethod
    def from_activation_viewmodel(
        cls,
        activation_view_model: OptionalSolverPluginManifestActivationViewModel,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
    ) -> OptionalSolverPluginManifestReactivationViewModel:
        candidates = _candidates_from_activation_view_model(activation_view_model)
        return build_optional_solver_plugin_manifest_reactivation_viewmodel(
            candidates,
            acknowledgements=acknowledgements,
            deactivation_state_supplied=True,
        )

    @classmethod
    def unavailable(cls) -> OptionalSolverPluginManifestReactivationViewModel:
        return build_optional_solver_plugin_manifest_reactivation_viewmodel(
            (), deactivation_state_supplied=False
        )

    @classmethod
    def all_blocked(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestReactivationCandidateInput],
    ) -> OptionalSolverPluginManifestReactivationViewModel:
        return build_optional_solver_plugin_manifest_reactivation_viewmodel(
            candidates, acknowledgements={}, deactivation_state_supplied=True
        )

    @classmethod
    def all_future_activation_required(
        cls,
        candidates: Sequence[OptionalSolverPluginManifestReactivationCandidateInput],
        *,
        acknowledgements: Mapping[str, bool] | None = None,
    ) -> OptionalSolverPluginManifestReactivationViewModel:
        routed = tuple(replace(c, future_activation_required=True) for c in candidates)
        return build_optional_solver_plugin_manifest_reactivation_viewmodel(
            routed,
            acknowledgements=acknowledgements,
            deactivation_state_supplied=True,
        )


def redact_optional_solver_plugin_manifest_reactivation_source_reference(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool]:
    """Return a safe display reference and a redaction flag (no filesystem access)."""

    return redact_optional_solver_plugin_manifest_source_reference(
        reference, provided_label=provided_label
    )


def build_optional_solver_plugin_manifest_reactivation_viewmodel(
    candidates: Sequence[OptionalSolverPluginManifestReactivationCandidateInput],
    *,
    acknowledgements: Mapping[str, bool] | None = None,
    deactivation_state_supplied: bool = True,
) -> OptionalSolverPluginManifestReactivationViewModel:
    """Build the reactivation view-model from supplied candidates and state."""

    acks = {str(k): bool(v) for k, v in (acknowledgements or {}).items()}

    non_built_in = [c for c in candidates if not c.built_in]
    reactivatable = [
        c for c in non_built_in
        if c.deactivated or c.future_activation_required or c.routed_to_activation_gate
    ]
    any_error = any(c.has_error for c in reactivatable)
    any_conflict = any(c.has_conflict for c in reactivatable)
    any_shared = any(c.has_shared_stack for c in reactivatable)
    any_stale = any(c.stale_source for c in reactivatable)
    any_unsafe = any(c.has_unsafe_claim for c in reactivatable)

    shared_ack_required = any_shared or any_conflict
    stale_ack_required = any_stale
    required_acks = _required_acks(shared_ack_required, stale_ack_required)
    acks_satisfied = all(acks.get(ack, False) for ack in required_acks)

    readiness = _readiness(
        deactivation_state_supplied=deactivation_state_supplied,
        candidates=list(candidates),
        reactivatable=reactivatable,
        any_error=any_error,
        any_unsafe=any_unsafe,
        any_conflict=any_conflict,
        any_shared=any_shared,
        shared_ack=acks.get(ACK_CONFLICT_OR_SHARED_STACK_WARNING, False),
        any_stale=any_stale,
        stale_ack=acks.get(ACK_STALE_SOURCE_REQUIRES_REPREVIEW, False),
        acks_satisfied=acks_satisfied,
    )
    state = _state(readiness)

    candidate_rows = tuple(
        _candidate_row(c, acks=acks, acks_satisfied=acks_satisfied)
        for c in sorted(candidates, key=lambda c: (not c.built_in, c.stack_id))
    )
    acknowledgement_rows = _acknowledgement_rows(
        acks, shared_ack_required=shared_ack_required, stale_ack_required=stale_ack_required
    )
    shared_stack_rows = tuple(
        _shared_stack_row(c)
        for c in sorted(non_built_in, key=lambda c: c.stack_id)
        if c.has_shared_stack or c.has_conflict
    )
    stale_source_rows = tuple(
        _stale_source_row(c)
        for c in sorted(non_built_in, key=lambda c: c.stack_id)
        if c.stale_source
    )
    evidence_rows = tuple(
        _evidence_row(c)
        for c in sorted(non_built_in, key=lambda c: c.stack_id)
        if c.deactivation_history_state or c.historical_evidence_state
    )
    diagnostics = _diagnostics(
        readiness=readiness,
        reactivatable=reactivatable,
        any_error=any_error,
        any_unsafe=any_unsafe,
        any_conflict=any_conflict,
        any_shared=any_shared,
        any_stale=any_stale,
        acks_satisfied=acks_satisfied,
        evidence_rows=evidence_rows,
    )
    trust_badges = _trust_badges(candidate_rows)
    summary = _summary(
        readiness=readiness,
        state=state,
        reactivatable=reactivatable,
        non_built_in=non_built_in,
        candidate_rows=candidate_rows,
        stale_source_rows=stale_source_rows,
        evidence_rows=evidence_rows,
        diagnostics=diagnostics,
        required_acks=required_acks,
        any_conflict=any_conflict,
        any_shared=any_shared,
    )
    return OptionalSolverPluginManifestReactivationViewModel(
        summary=summary,
        candidate_rows=candidate_rows,
        acknowledgement_rows=acknowledgement_rows,
        diagnostics=diagnostics,
        shared_stack_rows=shared_stack_rows,
        stale_source_rows=stale_source_rows,
        evidence_rows=evidence_rows,
        trust_badges=trust_badges,
        actions=_action_states(),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
    )


def render_optional_solver_plugin_manifest_reactivation_summary(
    view_model: OptionalSolverPluginManifestReactivationViewModel,
) -> dict[str, object]:
    """Return an in-memory, redacted, JSON-ready summary (writes no files)."""

    summary = view_model.summary
    return {
        "readiness": summary.readiness,
        "state": summary.state,
        "deactivated_candidate_count": summary.deactivated_candidate_count,
        "reactivation_candidate_count": summary.reactivation_candidate_count,
        "reactivation_ready_count": summary.reactivation_ready_count,
        "reactivation_blocked_count": summary.reactivation_blocked_count,
        "future_activation_required_count": summary.future_activation_required_count,
        "deactivation_history_retained": summary.deactivation_history_retained,
        "evidence_retained": summary.evidence_retained,
        "reactivation_performed": summary.reactivation_performed,
        "automatic_activation_performed": False,
        "trust_restoration_performed": False,
        "file_restore_performed": False,
        "file_rewrite_performed": False,
        "file_deletion_performed": False,
        "dependency_installation_performed": False,
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
                "reactivation_state": row.reactivation_state,
                "readiness": row.readiness,
                "repreview_required": row.repreview_required,
                "redacted_source_reference": row.redacted_source_reference,
            }
            for row in view_model.candidate_rows
        ],
        "diagnostics": [
            {"code": d.code, "severity": d.severity, "stack_id": d.stack_id}
            for d in view_model.diagnostics
        ],
    }


def summarize_optional_solver_plugin_manifest_reactivation_viewmodel(
    view_model: OptionalSolverPluginManifestReactivationViewModel,
) -> str:
    """Return a concise reactivation summary."""

    s = view_model.summary
    return (
        "Optional solver plugin manifest reactivation: "
        f"readiness={s.readiness}; state={s.state}; "
        f"deactivated={s.deactivated_candidate_count}; "
        f"reactivation_ready={s.reactivation_ready_count}; "
        f"blocked={s.reactivation_blocked_count}; "
        f"future_activation_required={s.future_activation_required_count}. "
        f"{PERSISTENCE_NOT_IMPLEMENTED_TEXT}"
    )


def explain_optional_solver_plugin_manifest_reactivation_viewmodel(
    view_model: OptionalSolverPluginManifestReactivationViewModel,
) -> str:
    """Explain the safety boundary of the reactivation view-model."""

    disabled = ", ".join(
        action.action.value for action in view_model.actions if not action.enabled
    )
    return (
        summarize_optional_solver_plugin_manifest_reactivation_viewmodel(view_model)
        + " The view-model transforms supplied deactivation/candidate data only; it "
        "does not reactivate anything, automatically activate candidates, restore "
        "trust, persist state, restore/rewrite/delete files, install or uninstall "
        "dependencies, uninstall solvers, import plugin packages, scan directories, "
        "fetch network manifests, run discovery, run validation, execute solvers, "
        "mutate issues, or mutate releases. "
        f"Disabled or future-only actions: {disabled}."
    )


# ----------------------------------------------------------------------
# Internal helpers (pure).
# ----------------------------------------------------------------------
def _required_acks(shared_ack_required: bool, stale_ack_required: bool) -> tuple[str, ...]:
    acks = list(REACTIVATION_ALWAYS_REQUIRED_ACKS)
    if shared_ack_required:
        acks.append(ACK_CONFLICT_OR_SHARED_STACK_WARNING)
    if stale_ack_required:
        acks.append(ACK_STALE_SOURCE_REQUIRES_REPREVIEW)
    return tuple(acks)


def _candidates_from_deactivation_view_model(
    deactivation_view_model: OptionalSolverPluginManifestDeactivationViewModel,
) -> tuple[OptionalSolverPluginManifestReactivationCandidateInput, ...]:
    shared_stack_ids = {row.stack_id for row in deactivation_view_model.shared_stack_rows}
    candidates: list[OptionalSolverPluginManifestReactivationCandidateInput] = []
    for row in deactivation_view_model.candidate_rows:
        if row.deactivation_state != "deactivated":
            continue
        candidates.append(
            OptionalSolverPluginManifestReactivationCandidateInput(
                stack_id=row.stack_id,
                display_name=row.display_name,
                source_type=row.source_type,
                source_label=row.source_label,
                source_reference=row.source_reference_display,
                trust_label=row.trust_label,
                is_untrusted=row.is_untrusted,
                activation_state=row.activation_state,
                deactivated=True,
                has_shared_stack=row.stack_id in shared_stack_ids,
                shared_stack_indicators=tuple(row.shared_stack_indicators),
                built_in_relationship=row.built_in_relationship,
                historical_evidence_state=(
                    "" if row.historical_evidence_state == "none"
                    else row.historical_evidence_state
                ),
            )
        )
    return tuple(candidates)


def _candidates_from_activation_view_model(
    activation_view_model: OptionalSolverPluginManifestActivationViewModel,
) -> tuple[OptionalSolverPluginManifestReactivationCandidateInput, ...]:
    conflict_stack_ids = {row.stack_id for row in activation_view_model.conflict_rows}
    candidates: list[OptionalSolverPluginManifestReactivationCandidateInput] = []
    for row in activation_view_model.candidate_rows:
        if row.activation_state != "deactivated":
            continue
        candidates.append(
            OptionalSolverPluginManifestReactivationCandidateInput(
                stack_id=row.stack_id,
                display_name=row.display_name,
                source_type=row.source_type,
                source_label=row.source_label,
                source_reference=row.source_reference_display,
                trust_label=row.trust_label,
                is_untrusted=row.is_untrusted,
                activation_state=row.activation_state,
                deactivated=True,
                has_shared_stack=row.stack_id in conflict_stack_ids,
                shared_stack_indicators=(
                    ("duplicate stack id",) if row.stack_id in conflict_stack_ids else ()
                ),
                has_unsafe_claim=bool(row.unsafe_claim_indicators),
                unsafe_claim_indicators=tuple(row.unsafe_claim_indicators),
                built_in_relationship=row.built_in_relationship,
            )
        )
    return tuple(candidates)


def _readiness(
    *,
    deactivation_state_supplied: bool,
    candidates: list,
    reactivatable: list,
    any_error: bool,
    any_unsafe: bool,
    any_conflict: bool,
    any_shared: bool,
    shared_ack: bool,
    any_stale: bool,
    stale_ack: bool,
    acks_satisfied: bool,
) -> OptionalSolverPluginManifestReactivationReadiness:
    Readiness = OptionalSolverPluginManifestReactivationReadiness
    if any_error:
        return Readiness.ERROR
    if not deactivation_state_supplied and not candidates:
        return Readiness.UNAVAILABLE_NO_DEACTIVATION_STATE
    if not reactivatable:
        return Readiness.UNAVAILABLE_NO_DEACTIVATED_CANDIDATES
    if any_unsafe:
        return Readiness.BLOCKED_UNSAFE_CLAIM
    if any_conflict:
        return Readiness.BLOCKED_CONFLICT
    if any_shared and not shared_ack:
        return Readiness.BLOCKED_SHARED_STACK_WARNING
    if any_stale and not stale_ack:
        return Readiness.BLOCKED_STALE_SOURCE_REPREVIEW
    if not acks_satisfied:
        return Readiness.BLOCKED_ACKNOWLEDGEMENT
    if reactivatable and all(c.routed_to_activation_gate for c in reactivatable):
        return Readiness.ACTIVE_CANDIDATE_FUTURE_GATE
    if any(c.future_activation_required for c in reactivatable):
        return Readiness.FUTURE_ACTIVATION_REQUIRED
    return Readiness.READY_NON_PERSISTENT


def _state(
    readiness: OptionalSolverPluginManifestReactivationReadiness,
) -> str:
    State = OptionalSolverPluginManifestReactivationState
    Readiness = OptionalSolverPluginManifestReactivationReadiness
    if readiness == Readiness.ERROR:
        return State.REACTIVATION_ERROR.value
    if readiness == Readiness.ACTIVE_CANDIDATE_FUTURE_GATE:
        return State.ACTIVE_CANDIDATE_FUTURE_GATE.value
    if readiness == Readiness.FUTURE_ACTIVATION_REQUIRED:
        return State.FUTURE_ACTIVATION_REQUIRED.value
    if readiness.value.startswith("unavailable"):
        return State.DEACTIVATED.value
    if readiness.value.startswith("blocked"):
        return State.REACTIVATION_BLOCKED.value
    return State.REACTIVATION_READY.value


def _candidate_row(
    candidate: OptionalSolverPluginManifestReactivationCandidateInput,
    *,
    acks: Mapping[str, bool],
    acks_satisfied: bool,
) -> OptionalSolverPluginManifestReactivationCandidateRowViewModel:
    State = OptionalSolverPluginManifestReactivationState
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
    stale_ack = acks.get(ACK_STALE_SOURCE_REQUIRES_REPREVIEW, False)

    if candidate.has_error:
        reactivation_state = State.REACTIVATION_ERROR.value
        readiness = "error"
        blockers.append("A reactivation error must be resolved first.")
    elif candidate.built_in:
        reactivation_state = State.DEACTIVATED.value
        readiness = "built_in_not_reactivatable"
        blockers.append(
            "Built-ins are authoritative; reactivating a user/plugin source does "
            "not override built-ins."
        )
    elif candidate.routed_to_activation_gate:
        reactivation_state = State.ACTIVE_CANDIDATE_FUTURE_GATE.value
        readiness = "active_candidate_future_gate"
    elif not (candidate.deactivated or candidate.future_activation_required):
        reactivation_state = State.REACTIVATION_BLOCKED.value
        readiness = "unavailable_not_deactivated"
        blockers.append("Candidate is not deactivated; reactivation is unavailable.")
    elif candidate.has_unsafe_claim:
        reactivation_state = State.REACTIVATION_BLOCKED.value
        readiness = "blocked_unsafe_claim"
        blockers.append("Unsafe claims block reactivation; resolve before reactivating.")
    elif candidate.has_conflict:
        reactivation_state = State.REACTIVATION_BLOCKED.value
        readiness = "blocked_conflict"
        blockers.append("Built-ins win; a stack-id conflict must be resolved.")
    elif candidate.has_shared_stack and not shared_ack:
        reactivation_state = State.REACTIVATION_BLOCKED.value
        readiness = "blocked_shared_stack_warning"
        blockers.append("Shared-stack warning must be acknowledged before reactivation.")
    elif candidate.stale_source and not stale_ack:
        reactivation_state = State.REACTIVATION_BLOCKED.value
        readiness = "blocked_stale_source_repreview"
        blockers.append("Stale/missing source requires re-preview before reactivation.")
    elif not acks_satisfied:
        reactivation_state = State.REACTIVATION_BLOCKED.value
        readiness = "blocked_acknowledgement"
        blockers.append("Required acknowledgements are missing.")
    elif candidate.future_activation_required:
        reactivation_state = State.FUTURE_ACTIVATION_REQUIRED.value
        readiness = "future_activation_required"
    elif candidate.reactivation_requested:
        reactivation_state = State.REACTIVATION_REQUESTED.value
        readiness = "ready_non_persistent"
    else:
        reactivation_state = State.REACTIVATION_READY.value
        readiness = "ready_non_persistent"

    return OptionalSolverPluginManifestReactivationCandidateRowViewModel(
        stack_id=candidate.stack_id,
        display_name=candidate.display_name or candidate.stack_id,
        source_type=candidate.source_type,
        source_label=candidate.source_label,
        source_reference_display=display,
        trust_label=candidate.trust_label,
        activation_state=candidate.activation_state,
        deactivation_state="deactivated" if candidate.deactivated else "not_deactivated",
        reactivation_state=reactivation_state,
        readiness=readiness,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        required_acknowledgements=_required_acks(
            candidate.has_shared_stack or candidate.has_conflict,
            candidate.stale_source,
        ),
        diagnostics=(),
        built_in_relationship=candidate.built_in_relationship,
        shared_stack_indicators=tuple(candidate.shared_stack_indicators),
        stale_source_state="stale" if candidate.stale_source else "current",
        repreview_required=candidate.stale_source,
        deactivation_history_state=candidate.deactivation_history_state or "none",
        historical_evidence_state=candidate.historical_evidence_state or "none",
        redacted_source_reference=redacted,
        is_untrusted=candidate.is_untrusted,
    )


def _acknowledgement_rows(
    acks: Mapping[str, bool],
    *,
    shared_ack_required: bool,
    stale_ack_required: bool,
) -> tuple[OptionalSolverPluginManifestReactivationAcknowledgementRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestReactivationAcknowledgementRowViewModel] = []
    for ack_id in REACTIVATION_REQUIRED_ACKS:
        if ack_id == ACK_CONFLICT_OR_SHARED_STACK_WARNING:
            required = shared_ack_required
        elif ack_id == ACK_STALE_SOURCE_REQUIRES_REPREVIEW:
            required = stale_ack_required
        else:
            required = True
        satisfied = bool(acks.get(ack_id, False))
        rows.append(
            OptionalSolverPluginManifestReactivationAcknowledgementRowViewModel(
                acknowledgement_id=ack_id,
                label=_ACK_LABELS.get(ack_id, ack_id),
                required=required,
                satisfied=satisfied,
                blocking=required and not satisfied,
                reason=(
                    "Required acknowledgement is satisfied."
                    if satisfied
                    else (
                        "Required acknowledgement is missing; reactivation is blocked."
                        if required
                        else "Acknowledgement is only required when the situation exists."
                    )
                ),
                related="reactivation",
                warning_text=_ACK_LABELS.get(ack_id, ack_id),
            )
        )
    return tuple(rows)


def _diagnostics(
    *,
    readiness: OptionalSolverPluginManifestReactivationReadiness,
    reactivatable: list,
    any_error: bool,
    any_unsafe: bool,
    any_conflict: bool,
    any_shared: bool,
    any_stale: bool,
    acks_satisfied: bool,
    evidence_rows: Sequence,
) -> tuple[OptionalSolverPluginManifestReactivationDiagnosticViewModel, ...]:
    Readiness = OptionalSolverPluginManifestReactivationReadiness
    items: list[OptionalSolverPluginManifestReactivationDiagnosticViewModel] = []

    def add(code: str, severity: str, blocker: bool = False, stack_id: str = "") -> None:
        items.append(
            OptionalSolverPluginManifestReactivationDiagnosticViewModel(
                severity=severity,
                category="reactivation",
                code=code,
                message=_diagnostic_message(code),
                stack_id=stack_id,
                suggested_fix=_diagnostic_fix(code),
                blocker=blocker,
            )
        )

    if readiness in {
        Readiness.UNAVAILABLE_NO_DEACTIVATION_STATE,
        Readiness.UNAVAILABLE_NO_DEACTIVATED_CANDIDATES,
    }:
        add(OSPMG_REACTIVATION_DEACTIVATED_REQUIRED, "warning", blocker=True)
    if any_unsafe:
        add(OSPMG_REACTIVATION_UNSAFE_CLAIM, "error", blocker=True)
    if any_conflict:
        add(OSPMG_REACTIVATION_CONFLICT_BLOCKED, "warning", blocker=True)
    if any_shared:
        add(OSPMG_REACTIVATION_SHARED_STACK_WARNING, "warning", blocker=True)
    if any_stale:
        add(OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED, "warning", blocker=True)
    if reactivatable and not acks_satisfied:
        add(OSPMG_REACTIVATION_ACK_REQUIRED, "warning", blocker=True)
    if any(c.is_untrusted for c in reactivatable):
        add(OSPMG_REACTIVATION_UNTRUSTED_SOURCE, "warning")
    if evidence_rows:
        add(OSPMG_REACTIVATION_HISTORY_RETAINED, "info")
    if readiness in {
        Readiness.READY_NON_PERSISTENT,
        Readiness.FUTURE_ACTIVATION_REQUIRED,
        Readiness.ACTIVE_CANDIDATE_FUTURE_GATE,
    }:
        add(OSPMG_REACTIVATION_REVIEW_REQUIRED, "info")
        add(OSPMG_REACTIVATION_FUTURE_GATE, "info")

    for code in (
        OSPMG_REACTIVATION_NOT_TRUST_RESTORE,
        OSPMG_REACTIVATION_NOT_VALIDATION,
        OSPMG_REACTIVATION_NO_INSTALL,
        OSPMG_REACTIVATION_NO_SOLVER_EXECUTION,
        OSPMG_REACTIVATION_NOT_ISSUE_CLOSURE,
        OSPMG_REACTIVATION_NOT_RELEASE_MUTATION,
        OSPMG_REACTIVATION_NOT_CERTIFICATION,
        OSPMG_REACTIVATION_NO_DISCOVERY_EXECUTION,
        OSPMG_REACTIVATION_NO_PLUGIN_IMPORT,
        OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED,
    ):
        add(code, "info")
    return tuple(items)


def _diagnostic_message(code: str) -> str:
    return {
        OSPMG_REACTIVATION_DEACTIVATED_REQUIRED: (
            "Reactivation requires a supplied deactivated candidate."
        ),
        OSPMG_REACTIVATION_ACK_REQUIRED: "Required acknowledgements are missing.",
        OSPMG_REACTIVATION_UNTRUSTED_SOURCE: "Source is untrusted by default.",
        OSPMG_REACTIVATION_NOT_TRUST_RESTORE: "Reactivation does not restore trust.",
        OSPMG_REACTIVATION_NOT_VALIDATION: "Reactivation is not validation evidence.",
        OSPMG_REACTIVATION_NO_INSTALL: "Reactivation does not install dependencies.",
        OSPMG_REACTIVATION_NO_SOLVER_EXECUTION: "Reactivation does not execute solvers.",
        OSPMG_REACTIVATION_NOT_ISSUE_CLOSURE: "Reactivation does not close issues.",
        OSPMG_REACTIVATION_NOT_RELEASE_MUTATION: "Reactivation does not mutate releases.",
        OSPMG_REACTIVATION_NOT_CERTIFICATION: "A trust label is not certification.",
        OSPMG_REACTIVATION_HISTORY_RETAINED: (
            "Deactivation history and validation evidence are retained."
        ),
        OSPMG_REACTIVATION_REVIEW_REQUIRED: (
            "Reactivation routes back through future activation review."
        ),
        OSPMG_REACTIVATION_CONFLICT_BLOCKED: "A stack-id conflict blocks reactivation.",
        OSPMG_REACTIVATION_SHARED_STACK_WARNING: (
            "A shared stack id requires a warning before reactivation."
        ),
        OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED: (
            "A stale/missing source requires re-preview before reactivation."
        ),
        OSPMG_REACTIVATION_UNSAFE_CLAIM: "Unsafe manifest claims block reactivation.",
        OSPMG_REACTIVATION_NO_DISCOVERY_EXECUTION: "Reactivation does not run discovery.",
        OSPMG_REACTIVATION_NO_PLUGIN_IMPORT: "Reactivation does not import plugins.",
        OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED: PERSISTENCE_NOT_IMPLEMENTED_TEXT,
        OSPMG_REACTIVATION_FUTURE_GATE: FUTURE_GATE_TEXT,
    }.get(code, code)


def _diagnostic_fix(code: str) -> str:
    return {
        OSPMG_REACTIVATION_DEACTIVATED_REQUIRED: "Deactivate a candidate before reactivation.",
        OSPMG_REACTIVATION_ACK_REQUIRED: "Satisfy required acknowledgements.",
        OSPMG_REACTIVATION_CONFLICT_BLOCKED: "Resolve the duplicate stack id; built-ins win.",
        OSPMG_REACTIVATION_SHARED_STACK_WARNING: "Acknowledge the shared-stack warning.",
        OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED: (
            "Re-preview the source through the explicit import boundary."
        ),
        OSPMG_REACTIVATION_UNSAFE_CLAIM: "Remove unsafe claims from the manifest.",
    }.get(code, "")


def _shared_stack_row(
    candidate: OptionalSolverPluginManifestReactivationCandidateInput,
) -> OptionalSolverPluginManifestReactivationSharedStackRowViewModel:
    display, _ = redact_optional_solver_plugin_manifest_source_reference(
        candidate.source_reference
    )
    return OptionalSolverPluginManifestReactivationSharedStackRowViewModel(
        stack_id=candidate.stack_id,
        built_in_source=f"builtin:{candidate.stack_id}",
        user_plugin_source=display or candidate.source_label or candidate.source_type,
        active_source_state="active" if not candidate.deactivated else "inactive",
        deactivated_source_state="deactivated" if candidate.deactivated else "active",
        reactivation_source_state="reactivation_requested"
        if candidate.reactivation_requested
        else "deactivated",
        built_ins_win_default=True,
        reactivating_user_source_keeps_built_ins=(
            "Reactivating a user/plugin source does not override built-ins."
        ),
        required_future_policy=(
            "An explicit future trust/override policy gate is required to change "
            "shared-stack precedence."
        ),
    )


def _stale_source_row(
    candidate: OptionalSolverPluginManifestReactivationCandidateInput,
) -> OptionalSolverPluginManifestReactivationStaleSourceRowViewModel:
    display, redacted = redact_optional_solver_plugin_manifest_source_reference(
        candidate.source_reference
    )
    if not display and candidate.source_label:
        display = candidate.source_label
        redacted = False
    return OptionalSolverPluginManifestReactivationStaleSourceRowViewModel(
        stack_id=candidate.stack_id,
        stale_source_state="stale",
        repreview_required=True,
        source_reference_display=display,
        redacted_source_reference=redacted,
    )


def _evidence_row(
    candidate: OptionalSolverPluginManifestReactivationCandidateInput,
) -> OptionalSolverPluginManifestReactivationEvidenceRowViewModel:
    return OptionalSolverPluginManifestReactivationEvidenceRowViewModel(
        stack_id=candidate.stack_id,
        deactivation_history_state=candidate.deactivation_history_state or "none",
        deactivation_history_retained=candidate.deactivation_history_retained,
        historical_evidence_state=candidate.historical_evidence_state or "none",
        evidence_retained=candidate.evidence_retained,
    )


def _trust_badges(
    candidate_rows: Sequence[OptionalSolverPluginManifestReactivationCandidateRowViewModel],
) -> tuple[OptionalSolverPluginManifestReactivationTrustBadgeViewModel, ...]:
    seen: dict[
        tuple[str, str], OptionalSolverPluginManifestReactivationTrustBadgeViewModel
    ] = {}
    for row in candidate_rows:
        key = (row.source_type, row.trust_label)
        if key in seen:
            continue
        seen[key] = OptionalSolverPluginManifestReactivationTrustBadgeViewModel(
            source_type=row.source_type,
            trust_label=row.trust_label,
            source_label=row.source_label,
            activation_state=row.activation_state,
            deactivation_state=row.deactivation_state,
            reactivation_state=row.reactivation_state,
            warning_text=(
                "Untrusted source; untrusted by default."
                if row.is_untrusted
                else "Built-in/reviewed source; trust label is not certification."
            ),
        )
    return tuple(seen[key] for key in sorted(seen))


def _summary(
    *,
    readiness: OptionalSolverPluginManifestReactivationReadiness,
    state: str,
    reactivatable: list,
    non_built_in: list,
    candidate_rows: Sequence[OptionalSolverPluginManifestReactivationCandidateRowViewModel],
    stale_source_rows: Sequence,
    evidence_rows: Sequence,
    diagnostics: Sequence[OptionalSolverPluginManifestReactivationDiagnosticViewModel],
    required_acks: Sequence[str],
    any_conflict: bool,
    any_shared: bool,
) -> OptionalSolverPluginManifestReactivationSummaryViewModel:
    State = OptionalSolverPluginManifestReactivationState
    deactivated = sum(1 for c in non_built_in if c.deactivated)
    ready = sum(1 for r in candidate_rows if r.readiness == "ready_non_persistent")
    blocked = sum(
        1 for r in candidate_rows
        if r.reactivation_state == State.REACTIVATION_BLOCKED.value
    )
    future_required = sum(
        1 for r in candidate_rows
        if r.reactivation_state == State.FUTURE_ACTIVATION_REQUIRED.value
    )
    warnings = sum(1 for d in diagnostics if d.severity == "warning")
    errors = sum(1 for d in diagnostics if d.severity in {"error", "blocker"})
    history_retained = sum(
        1 for c in non_built_in if c.deactivation_history_retained
    )
    status = (
        f"Reactivation ({readiness.value}): {deactivated} deactivated candidate(s), "
        f"{ready} reactivation-ready, {future_required} future-activation-required. "
        "Reactivation is not automatic activation, trust restoration, or validation."
    )
    return OptionalSolverPluginManifestReactivationSummaryViewModel(
        readiness=readiness.value,
        state=state,
        deactivated_candidate_count=deactivated,
        reactivation_candidate_count=len(non_built_in),
        reactivation_ready_count=ready,
        reactivation_blocked_count=blocked,
        future_activation_required_count=future_required,
        stale_source_repreview_required_count=len(stale_source_rows),
        shared_stack_count=sum(1 for c in non_built_in if c.has_shared_stack),
        conflict_count=sum(1 for c in non_built_in if c.has_conflict),
        acknowledgement_required_count=len(required_acks),
        diagnostic_count=len(diagnostics),
        warning_count=warnings,
        error_count=errors,
        deactivation_history_retained_count=history_retained,
        evidence_retained_count=len(evidence_rows),
        status_text=status,
        reactivation_performed=False,
    )


def _action_states() -> tuple[OptionalSolverPluginManifestReactivationActionState, ...]:
    Action = OptionalSolverPluginManifestReactivationAction
    states: list[OptionalSolverPluginManifestReactivationActionState] = []
    for action in Action:
        unsafe = action.value in _UNSAFE_ACTIONS
        states.append(
            OptionalSolverPluginManifestReactivationActionState(
                action=action,
                label=action.value.replace("_", " ").title(),
                enabled=False,
                available=not unsafe,
                reason=_action_reason(action),
                future_action=True,
            )
        )
    return tuple(states)


def _action_reason(action: OptionalSolverPluginManifestReactivationAction) -> str:
    Action = OptionalSolverPluginManifestReactivationAction
    if action.value in _UNSAFE_ACTIONS:
        return {
            Action.RUN_DISCOVERY.value: "Discovery execution is unavailable from this view-model.",
            Action.RUN_VALIDATION.value: "Validation requires a separate OSW-VALID gate.",
            Action.INSTALL_DEPENDENCY.value: "Dependency installation is unavailable.",
            Action.UNINSTALL_DEPENDENCY.value: "Dependency uninstall is unavailable.",
            Action.UNINSTALL_SOLVER.value: "Solver uninstall is unavailable.",
            Action.EXECUTE_SOLVER.value: "Solver execution is unavailable.",
            Action.CLOSE_ISSUE.value: "Issue closure requires separate validation/closure gates.",
        }[action.value]
    if action == Action.EXPORT_REDACTED_SUMMARY:
        return "Produces an in-memory redacted summary only; it writes no files."
    if action in {Action.REACTIVATE_CANDIDATE, Action.REQUEST_REACTIVATION}:
        return (
            "Reactivation is display/preview-only; reactivation persistence and "
            "automatic activation are future gates and this view-model persists "
            "nothing and activates nothing."
        )
    if action == Action.ROUTE_TO_ACTIVATION_REVIEW:
        return (
            "Routing back to activation review is a future gate; this view-model "
            "activates nothing."
        )
    return (
        "Future GUI/source action; reactivation persistence is a future gate "
        "(OSW-EXP-089) and this view-model runs nothing."
    )


def _guidance_text() -> tuple[str, ...]:
    return (
        "Reactivation preview is data-only.",
        PERSISTENCE_NOT_IMPLEMENTED_TEXT,
        FUTURE_GATE_TEXT,
        REACTIVATION_NOT_ACTIVATION_TEXT,
        REACTIVATION_NOT_TRUST_RESTORE_TEXT,
        REACTIVATION_NOT_VALIDATION_TEXT,
        TRUST_NOT_CERTIFICATION_TEXT,
        "Built-in manifests win by default; reactivating a user/plugin source does "
        "not override built-ins.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "A stale/missing source requires re-preview; reactivation reads no files.",
        "Deactivation history and historical validation evidence are retained.",
        "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
        "bounded, issue-specific evidence; skipped-missing remains historical "
        "non-pass evidence.",
    )


def _safety_text() -> tuple[str, ...]:
    return (
        "No reactivation persistence.",
        "No automatic activation.",
        "No trust restoration.",
        "No GUI behavior.",
        "No CLI behavior.",
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
    )


__all__ = [
    "ACK_CONFLICT_OR_SHARED_STACK_WARNING",
    "ACK_NO_DISCOVERY_EXECUTION",
    "ACK_NO_PLUGIN_PACKAGE_IMPORT",
    "ACK_REACTIVATION_HISTORY_RETAINED",
    "ACK_REACTIVATION_NOT_INSTALL",
    "ACK_REACTIVATION_NOT_ISSUE_CLOSURE",
    "ACK_REACTIVATION_NOT_RELEASE_MUTATION",
    "ACK_REACTIVATION_NOT_TRUST_RESTORATION",
    "ACK_REACTIVATION_NOT_VALIDATION",
    "ACK_REACTIVATION_NO_SOLVER_EXECUTION",
    "ACK_REACTIVATION_REQUIRES_ACTIVATION_REVIEW",
    "ACK_STALE_SOURCE_REQUIRES_REPREVIEW",
    "ACK_TRUST_LABEL_NOT_CERTIFICATION",
    "ACK_UNTRUSTED_SOURCE",
    "OSPMG_REACTIVATION_ACK_REQUIRED",
    "OSPMG_REACTIVATION_CONFLICT_BLOCKED",
    "OSPMG_REACTIVATION_DEACTIVATED_REQUIRED",
    "OSPMG_REACTIVATION_DIAGNOSTIC_CODES",
    "OSPMG_REACTIVATION_FUTURE_GATE",
    "OSPMG_REACTIVATION_HISTORY_RETAINED",
    "OSPMG_REACTIVATION_NOT_CERTIFICATION",
    "OSPMG_REACTIVATION_NOT_ISSUE_CLOSURE",
    "OSPMG_REACTIVATION_NOT_RELEASE_MUTATION",
    "OSPMG_REACTIVATION_NOT_TRUST_RESTORE",
    "OSPMG_REACTIVATION_NOT_VALIDATION",
    "OSPMG_REACTIVATION_NO_DISCOVERY_EXECUTION",
    "OSPMG_REACTIVATION_NO_INSTALL",
    "OSPMG_REACTIVATION_NO_PLUGIN_IMPORT",
    "OSPMG_REACTIVATION_NO_SOLVER_EXECUTION",
    "OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED",
    "OSPMG_REACTIVATION_REVIEW_REQUIRED",
    "OSPMG_REACTIVATION_SHARED_STACK_WARNING",
    "OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED",
    "OSPMG_REACTIVATION_UNSAFE_CLAIM",
    "OSPMG_REACTIVATION_UNTRUSTED_SOURCE",
    "REACTIVATION_ALWAYS_REQUIRED_ACKS",
    "REACTIVATION_BLOCKED_TRANSITIONS",
    "REACTIVATION_REQUIRED_ACKS",
    "OptionalSolverPluginManifestReactivationAcknowledgementRowViewModel",
    "OptionalSolverPluginManifestReactivationAction",
    "OptionalSolverPluginManifestReactivationActionState",
    "OptionalSolverPluginManifestReactivationCandidateInput",
    "OptionalSolverPluginManifestReactivationCandidateRowViewModel",
    "OptionalSolverPluginManifestReactivationDiagnosticViewModel",
    "OptionalSolverPluginManifestReactivationEvidenceRowViewModel",
    "OptionalSolverPluginManifestReactivationReadiness",
    "OptionalSolverPluginManifestReactivationSharedStackRowViewModel",
    "OptionalSolverPluginManifestReactivationStaleSourceRowViewModel",
    "OptionalSolverPluginManifestReactivationState",
    "OptionalSolverPluginManifestReactivationSummaryViewModel",
    "OptionalSolverPluginManifestReactivationTrustBadgeViewModel",
    "OptionalSolverPluginManifestReactivationViewModel",
    "build_optional_solver_plugin_manifest_reactivation_viewmodel",
    "explain_optional_solver_plugin_manifest_reactivation_viewmodel",
    "redact_optional_solver_plugin_manifest_reactivation_source_reference",
    "render_optional_solver_plugin_manifest_reactivation_summary",
    "summarize_optional_solver_plugin_manifest_reactivation_viewmodel",
]
