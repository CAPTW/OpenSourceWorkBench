"""Pure view-model for optional solver plugin manifest discovery-refresh state.

This module is the OSW-EXP-083 implementation of the discovery-refresh
integration view-model designed in OSW-EXP-082. It transforms already-supplied
activation/deactivation candidate state (or caller-supplied discovery source
records) into deterministic discovery-refresh readiness, source
inclusion/exclusion, acknowledgement, diagnostic, conflict, unsafe-claim, trust,
and action-state records.

It performs no side effects. It does not run discovery, change passive discovery
behavior, persist activation/deactivation state, read or write files, parse JSON
from a path, import PySide/Qt, import plugin packages, scan directories, fetch
URLs, run validation, execute solvers, install dependencies, or mutate
issues/releases. Acknowledgement satisfaction and refresh lifecycle inputs are
SUPPLIED by the caller; this layer only classifies and renders them.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

from .plugin_manifest_activation_viewmodel import (
    OptionalSolverPluginManifestActivationViewModel,
)
from .plugin_manifest_explicit_import_gui_viewmodel import (
    redact_optional_solver_plugin_manifest_source_reference,
)

# Design-only OSPMG_DISCOVERY_REFRESH_* diagnostic vocabulary (OSW-EXP-082).
OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED = (
    "OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED"
)
OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED = (
    "OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED"
)
OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED = "OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED"
OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE = "OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE"
OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED = "OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED"
OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM = "OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM"
OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION = "OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION"
OSPMG_DISCOVERY_REFRESH_NO_INSTALL = "OSPMG_DISCOVERY_REFRESH_NO_INSTALL"
OSPMG_DISCOVERY_REFRESH_NO_SOLVER_EXECUTION = (
    "OSPMG_DISCOVERY_REFRESH_NO_SOLVER_EXECUTION"
)
OSPMG_DISCOVERY_REFRESH_NO_NETWORK_FETCH = "OSPMG_DISCOVERY_REFRESH_NO_NETWORK_FETCH"
OSPMG_DISCOVERY_REFRESH_NO_PLUGIN_IMPORT = "OSPMG_DISCOVERY_REFRESH_NO_PLUGIN_IMPORT"
OSPMG_DISCOVERY_REFRESH_NOT_ISSUE_CLOSURE = "OSPMG_DISCOVERY_REFRESH_NOT_ISSUE_CLOSURE"
OSPMG_DISCOVERY_REFRESH_NOT_CERTIFICATION = "OSPMG_DISCOVERY_REFRESH_NOT_CERTIFICATION"
OSPMG_DISCOVERY_REFRESH_INTEGRATION_NOT_IMPLEMENTED = (
    "OSPMG_DISCOVERY_REFRESH_INTEGRATION_NOT_IMPLEMENTED"
)

#: All reserved discovery-refresh diagnostic codes, in design order.
OSPMG_DISCOVERY_REFRESH_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED,
    OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED,
    OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED,
    OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE,
    OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED,
    OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM,
    OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION,
    OSPMG_DISCOVERY_REFRESH_NO_INSTALL,
    OSPMG_DISCOVERY_REFRESH_NO_SOLVER_EXECUTION,
    OSPMG_DISCOVERY_REFRESH_NO_NETWORK_FETCH,
    OSPMG_DISCOVERY_REFRESH_NO_PLUGIN_IMPORT,
    OSPMG_DISCOVERY_REFRESH_NOT_ISSUE_CLOSURE,
    OSPMG_DISCOVERY_REFRESH_NOT_CERTIFICATION,
    OSPMG_DISCOVERY_REFRESH_INTEGRATION_NOT_IMPLEMENTED,
)

# Acknowledgement identifiers (OSW-EXP-082).
ACK_REFRESH_NOT_VALIDATION = "refresh_not_validation"
ACK_REFRESH_NOT_INSTALL = "refresh_not_install"
ACK_REFRESH_NOT_SOLVER_EXECUTION = "refresh_not_solver_execution"
ACK_REFRESH_NOT_ISSUE_CLOSURE = "refresh_not_issue_closure"
ACK_REFRESH_NOT_CERTIFICATION = "refresh_not_certification"
ACK_UNTRUSTED_MANIFEST_SOURCE = "untrusted_manifest_source"
ACK_CONFLICT_OR_OVERRIDE_VISIBLE = "conflict_or_override_visible"
ACK_DEACTIVATED_CANDIDATES_EXCLUDED = "deactivated_candidates_excluded"
ACK_NO_NETWORK_FETCH = "no_network_fetch"
ACK_NO_PLUGIN_PACKAGE_IMPORT = "no_plugin_package_import"

#: All required discovery-refresh acknowledgements, in design order.
DISCOVERY_REFRESH_REQUIRED_ACKS: tuple[str, ...] = (
    ACK_REFRESH_NOT_VALIDATION,
    ACK_REFRESH_NOT_INSTALL,
    ACK_REFRESH_NOT_SOLVER_EXECUTION,
    ACK_REFRESH_NOT_ISSUE_CLOSURE,
    ACK_REFRESH_NOT_CERTIFICATION,
    ACK_UNTRUSTED_MANIFEST_SOURCE,
    ACK_CONFLICT_OR_OVERRIDE_VISIBLE,
    ACK_DEACTIVATED_CANDIDATES_EXCLUDED,
    ACK_NO_NETWORK_FETCH,
    ACK_NO_PLUGIN_PACKAGE_IMPORT,
)

_ACK_LABELS: dict[str, str] = {
    ACK_REFRESH_NOT_VALIDATION: "I understand discovery refresh is not validation.",
    ACK_REFRESH_NOT_INSTALL: "I understand discovery refresh does not install dependencies.",
    ACK_REFRESH_NOT_SOLVER_EXECUTION: "I understand discovery refresh does not execute solvers.",
    ACK_REFRESH_NOT_ISSUE_CLOSURE: "I understand discovery refresh does not close issues.",
    ACK_REFRESH_NOT_CERTIFICATION: "I understand a trust label is not certification.",
    ACK_UNTRUSTED_MANIFEST_SOURCE: "I understand user/plugin manifest sources are untrusted.",
    ACK_CONFLICT_OR_OVERRIDE_VISIBLE: "I understand built-ins win and conflicts are shown.",
    ACK_DEACTIVATED_CANDIDATES_EXCLUDED: "I understand deactivated candidates are excluded.",
    ACK_NO_NETWORK_FETCH: "I understand discovery refresh does not fetch from the network.",
    ACK_NO_PLUGIN_PACKAGE_IMPORT: "I understand discovery refresh does not import plugin packages.",
}

_UNTRUSTED_TRUST_LABELS: frozenset[str] = frozenset(
    {"user_provided", "third_party_plugin", "untrusted", "invalid",
     "untrusted_user_file", "untrusted_plugin_manifest"}
)

TRUST_NOT_CERTIFICATION_TEXT = "A trust label is not certification."
INCLUSION_NOT_VALIDATION_TEXT = "Discovery inclusion is not validation evidence."
INTEGRATION_NOT_IMPLEMENTED_TEXT = (
    "Discovery-refresh integration is a future gate; this view-model performs no "
    "discovery, validation, install, or execution."
)


class OptionalSolverPluginManifestDiscoveryRefreshMode(str, Enum):
    """Discovery refresh modes (OSW-EXP-082)."""

    BUILT_IN_ONLY_REFRESH = "built_in_only_refresh"
    ACTIVATED_CANDIDATES_PREVIEW_REFRESH = "activated_candidates_preview_refresh"
    ACTIVATED_CANDIDATES_USER_INITIATED_REFRESH = (
        "activated_candidates_user_initiated_refresh"
    )
    DEACTIVATED_CANDIDATES_EXCLUDED = "deactivated_candidates_excluded"
    DEACTIVATED_CANDIDATES_VISIBLE_BUT_INACTIVE = (
        "deactivated_candidates_visible_but_inactive"
    )
    BLOCKED_DUE_TO_UNTRUSTED_OR_CONFLICTING_SOURCES = (
        "blocked_due_to_untrusted_or_conflicting_sources"
    )


class OptionalSolverPluginManifestDiscoveryRefreshState(str, Enum):
    """Discovery refresh lifecycle state (OSW-EXP-082 state machine)."""

    REFRESH_UNAVAILABLE = "refresh_unavailable"
    REFRESH_REQUESTED = "refresh_requested"
    REFRESH_BLOCKED = "refresh_blocked"
    REFRESH_READY = "refresh_ready"
    REFRESH_RUNNING_FUTURE_GATE = "refresh_running_future_gate"
    REFRESH_RESULT_PREVIEW = "refresh_result_preview"
    REFRESH_ERROR = "refresh_error"


class OptionalSolverPluginManifestDiscoveryRefreshReadiness(str, Enum):
    """Per-refresh readiness classification."""

    UNAVAILABLE_NO_ACTIVATION_STATE = "unavailable_no_activation_state"
    UNAVAILABLE_NO_ACTIVE_CANDIDATES = "unavailable_no_active_candidates"
    BUILT_IN_ONLY_READY = "built_in_only_ready"
    BLOCKED_ACKNOWLEDGEMENT = "blocked_acknowledgement"
    BLOCKED_CONFLICT = "blocked_conflict"
    BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_claim"
    READY_PREVIEW_ONLY = "ready_preview_only"
    READY_FUTURE_REFRESH = "ready_future_refresh"
    RESULT_PREVIEW = "result_preview"
    ERROR = "error"


class OptionalSolverPluginManifestDiscoverySourceState(str, Enum):
    """Per-source discovery state."""

    BUILT_IN_ONLY = "built_in_only"
    ACTIVE_CANDIDATE_INCLUDED = "active_candidate_included"
    DEACTIVATED_EXCLUDED = "deactivated_excluded"
    CONFLICT_BLOCKED = "conflict_blocked"
    UNSAFE_CLAIM_BLOCKED = "unsafe_claim_blocked"
    REFRESH_BLOCKED = "refresh_blocked"


class OptionalSolverPluginManifestDiscoveryRefreshAction(str, Enum):
    """Future action identifiers for the discovery-refresh surface."""

    REQUEST_REFRESH = "request_refresh"
    BUILT_IN_ONLY_REFRESH = "built_in_only_refresh"
    INCLUDE_ACTIVATED_CANDIDATES = "include_activated_candidates"
    EXCLUDE_DEACTIVATED_CANDIDATES = "exclude_deactivated_candidates"
    ACKNOWLEDGE_REFRESH_NOT_VALIDATION = "acknowledge_refresh_not_validation"
    ACKNOWLEDGE_NO_INSTALL = "acknowledge_no_install"
    ACKNOWLEDGE_NO_SOLVER_EXECUTION = "acknowledge_no_solver_execution"
    ACKNOWLEDGE_NO_ISSUE_CLOSURE = "acknowledge_no_issue_closure"
    ACKNOWLEDGE_NO_NETWORK_FETCH = "acknowledge_no_network_fetch"
    ACKNOWLEDGE_NO_PLUGIN_IMPORT = "acknowledge_no_plugin_import"
    RUN_DISCOVERY = "run_discovery"
    RUN_VALIDATION = "run_validation"
    INSTALL_DEPENDENCY = "install_dependency"
    EXECUTE_SOLVER = "execute_solver"
    CLOSE_ISSUE = "close_issue"
    EXPORT_REDACTED_SUMMARY = "export_redacted_summary"


# Actions that must never be enabled in this gate.
_UNSAFE_ACTIONS: frozenset[str] = frozenset(
    {
        OptionalSolverPluginManifestDiscoveryRefreshAction.RUN_DISCOVERY.value,
        OptionalSolverPluginManifestDiscoveryRefreshAction.RUN_VALIDATION.value,
        OptionalSolverPluginManifestDiscoveryRefreshAction.INSTALL_DEPENDENCY.value,
        OptionalSolverPluginManifestDiscoveryRefreshAction.EXECUTE_SOLVER.value,
        OptionalSolverPluginManifestDiscoveryRefreshAction.CLOSE_ISSUE.value,
    }
)

# Blocked state-machine transitions (OSW-EXP-082), exposed for the GUI/CLI gate.
DISCOVERY_REFRESH_BLOCKED_TRANSITIONS: tuple[str, ...] = (
    "preview-only directly to discovery execution",
    "inactive/deactivated candidate directly to active discovery source",
    "refresh to validation execution",
    "refresh to dependency installation",
    "refresh to solver execution",
    "refresh to issue closure",
    "refresh to release mutation",
)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoveryRefreshSourceInput:
    """Caller-supplied discovery source (no file IO performed)."""

    stack_id: str
    display_name: str = ""
    source_type: str = "activated_user_selected_json_file"
    source_label: str = ""
    source_reference: str = ""
    trust_label: str = "untrusted_user_file"
    is_untrusted: bool = True
    activation_state: str = "active_candidate"
    has_conflict: bool = False
    has_unsafe_claim: bool = False
    unsafe_claim_indicators: tuple[str, ...] = ()
    built_in: bool = False
    built_in_relationship: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoveryRefreshActionState:
    """Display-only state for a future discovery-refresh action."""

    action: OptionalSolverPluginManifestDiscoveryRefreshAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoveryRefreshSummaryViewModel:
    """Summary header values for a discovery-refresh view-model."""

    refresh_mode: str
    refresh_state: str
    readiness: str
    built_in_source_count: int
    active_candidate_count: int
    included_candidate_count: int
    deactivated_excluded_count: int
    deactivated_visible_count: int
    conflict_blocked_count: int
    unsafe_claim_blocked_count: int
    acknowledgement_required_count: int
    diagnostic_count: int
    warning_count: int
    error_count: int
    refresh_ready: bool
    status_text: str
    discovery_execution_performed: bool = False
    validation_execution_performed: bool = False
    solver_execution_performed: bool = False
    dependency_installation_performed: bool = False
    network_fetch_performed: bool = False
    plugin_package_import_performed: bool = False
    issue_mutation_performed: bool = False
    release_mutation_performed: bool = False
    certification_claimed: bool = False
    not_validation_evidence: bool = True
    third_party_manifests_trusted_by_default: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoverySourceRowViewModel:
    """Discovery input source row."""

    stack_id: str
    display_name: str
    source_type: str
    source_label: str
    source_reference_display: str
    trust_label: str
    discovery_source_state: str
    activation_state: str
    refresh_mode: str
    included: bool
    excluded: bool
    exclusion_reason: str
    readiness: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    required_acknowledgements: tuple[str, ...]
    unsafe_claim_indicators: tuple[str, ...]
    built_in_relationship: str
    redacted_source_reference: bool
    is_untrusted: bool
    not_validation_evidence_text: str = INCLUSION_NOT_VALIDATION_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDeactivatedCandidateRowViewModel:
    """Deactivated candidate row (excluded by default, not a failure)."""

    stack_id: str
    source_label: str
    trust_label: str
    deactivated_state: str
    excluded_by_default: bool
    source_reference_display: str
    redacted_source_reference: bool
    not_validation_failure_text: str = "Deactivated is not a validation failure."
    not_uninstall_text: str = "Deactivated is not uninstall."
    not_file_deletion_text: str = "Deactivated is not file deletion."


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoveryRefreshAcknowledgementRowViewModel:
    """Acknowledgement row for the discovery-refresh surface."""

    acknowledgement_id: str
    label: str
    required: bool
    satisfied: bool
    blocking: bool
    reason: str
    related: str
    warning_text: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoveryRefreshDiagnosticViewModel:
    """Discovery-refresh (OSPMG) level diagnostic record."""

    severity: str
    category: str
    code: str
    message: str
    source_reference_display: str = ""
    stack_id: str = ""
    suggested_fix: str = ""
    blocker: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoveryRefreshConflictRowViewModel:
    """Discovery-refresh conflict row."""

    stack_id: str
    built_in_source: str
    user_plugin_source: str
    conflict_policy: str
    built_ins_win_default: bool
    refresh_state: str
    required_future_policy: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoveryRefreshUnsafeClaimRowViewModel:
    """Discovery-refresh unsafe-claim row."""

    stack_id: str
    source_label: str
    trust_label: str
    unsafe_claim_indicators: tuple[str, ...]
    blocked: bool
    reason: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoveryRefreshTrustBadgeViewModel:
    """Source/trust/provenance badge for the discovery-refresh surface."""

    source_type: str
    trust_label: str
    source_label: str
    discovery_source_state: str
    activation_state: str
    warning_text: str
    trust_label_is_not_certification: str = TRUST_NOT_CERTIFICATION_TEXT
    discovery_inclusion_is_not_validation_evidence: str = INCLUSION_NOT_VALIDATION_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiscoveryRefreshViewModel:
    """Complete pure view-model for the discovery-refresh surface."""

    summary: OptionalSolverPluginManifestDiscoveryRefreshSummaryViewModel
    source_rows: tuple[OptionalSolverPluginManifestDiscoverySourceRowViewModel, ...]
    deactivated_rows: tuple[
        OptionalSolverPluginManifestDeactivatedCandidateRowViewModel, ...
    ]
    acknowledgement_rows: tuple[
        OptionalSolverPluginManifestDiscoveryRefreshAcknowledgementRowViewModel, ...
    ]
    diagnostics: tuple[OptionalSolverPluginManifestDiscoveryRefreshDiagnosticViewModel, ...]
    conflict_rows: tuple[OptionalSolverPluginManifestDiscoveryRefreshConflictRowViewModel, ...]
    unsafe_claim_rows: tuple[
        OptionalSolverPluginManifestDiscoveryRefreshUnsafeClaimRowViewModel, ...
    ]
    trust_badges: tuple[OptionalSolverPluginManifestDiscoveryRefreshTrustBadgeViewModel, ...]
    actions: tuple[OptionalSolverPluginManifestDiscoveryRefreshActionState, ...]
    guidance_text: tuple[str, ...]
    safety_text: tuple[str, ...]
    reserved_diagnostic_codes: tuple[str, ...] = OSPMG_DISCOVERY_REFRESH_DIAGNOSTIC_CODES
    blocked_transitions: tuple[str, ...] = DISCOVERY_REFRESH_BLOCKED_TRANSITIONS
    not_validation_evidence: bool = True

    # ------------------------------------------------------------------
    # Convenience constructors (transform supplied data only; no side effects).
    # ------------------------------------------------------------------
    @classmethod
    def from_sources(
        cls,
        sources: Sequence[OptionalSolverPluginManifestDiscoveryRefreshSourceInput],
        *,
        acknowledgements: Mapping[str, bool] | None = None,
        refresh_requested: bool = False,
        refresh_mode: str | None = None,
    ) -> OptionalSolverPluginManifestDiscoveryRefreshViewModel:
        return build_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
            sources,
            acknowledgements=acknowledgements,
            refresh_requested=refresh_requested,
            refresh_mode=refresh_mode,
            activation_state_supplied=True,
        )

    @classmethod
    def from_activation_viewmodel(
        cls,
        activation_view_model: OptionalSolverPluginManifestActivationViewModel,
        *,
        acknowledgements: Mapping[str, bool] | None = None,
        refresh_requested: bool = False,
        refresh_mode: str | None = None,
        built_in_source_count: int = 0,
    ) -> OptionalSolverPluginManifestDiscoveryRefreshViewModel:
        sources = _sources_from_activation_view_model(
            activation_view_model, built_in_source_count
        )
        return build_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
            sources,
            acknowledgements=acknowledgements,
            refresh_requested=refresh_requested,
            refresh_mode=refresh_mode,
            activation_state_supplied=True,
        )

    @classmethod
    def built_in_only(
        cls, *, built_in_source_count: int = 1
    ) -> OptionalSolverPluginManifestDiscoveryRefreshViewModel:
        sources = tuple(
            OptionalSolverPluginManifestDiscoveryRefreshSourceInput(
                stack_id=f"builtin_{index}",
                display_name=f"Built-in stack {index}",
                source_type="built_in",
                trust_label="built_in",
                is_untrusted=False,
                activation_state="active_candidate",
                built_in=True,
                built_in_relationship="built-in (authoritative by default)",
            )
            for index in range(max(0, built_in_source_count))
        )
        return build_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
            sources,
            refresh_mode=(
                OptionalSolverPluginManifestDiscoveryRefreshMode.BUILT_IN_ONLY_REFRESH.value
            ),
            activation_state_supplied=True,
        )

    @classmethod
    def unavailable(cls) -> OptionalSolverPluginManifestDiscoveryRefreshViewModel:
        return build_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
            (), activation_state_supplied=False
        )

    @classmethod
    def all_blocked(
        cls,
        sources: Sequence[OptionalSolverPluginManifestDiscoveryRefreshSourceInput],
    ) -> OptionalSolverPluginManifestDiscoveryRefreshViewModel:
        return build_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
            sources, acknowledgements={}, refresh_requested=True,
            activation_state_supplied=True,
        )

    @classmethod
    def result_preview(
        cls,
        sources: Sequence[OptionalSolverPluginManifestDiscoveryRefreshSourceInput],
        *,
        acknowledgements: Mapping[str, bool] | None = None,
    ) -> OptionalSolverPluginManifestDiscoveryRefreshViewModel:
        return build_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
            sources, acknowledgements=acknowledgements, refresh_requested=True,
            activation_state_supplied=True, result_preview=True,
        )


def redact_optional_solver_plugin_manifest_discovery_source_reference(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool]:
    """Return a safe display reference and a redaction flag (no filesystem access)."""

    return redact_optional_solver_plugin_manifest_source_reference(
        reference, provided_label=provided_label
    )


def build_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
    sources: Sequence[OptionalSolverPluginManifestDiscoveryRefreshSourceInput],
    *,
    acknowledgements: Mapping[str, bool] | None = None,
    refresh_requested: bool = False,
    refresh_mode: str | None = None,
    activation_state_supplied: bool = True,
    result_preview: bool = False,
) -> OptionalSolverPluginManifestDiscoveryRefreshViewModel:
    """Build the discovery-refresh view-model from supplied sources and state."""

    acks = {str(k): bool(v) for k, v in (acknowledgements or {}).items()}
    acks_satisfied = all(acks.get(ack, False) for ack in DISCOVERY_REFRESH_REQUIRED_ACKS)

    built_ins = [s for s in sources if s.built_in]
    actives = [
        s for s in sources if not s.built_in and s.activation_state == "active_candidate"
    ]
    deactivated = [s for s in sources if not s.built_in and s.activation_state == "deactivated"]

    any_unsafe = any(s.has_unsafe_claim for s in actives)
    any_conflict = any(s.has_conflict for s in actives)
    includable = [s for s in actives if not s.has_unsafe_claim and not s.has_conflict]

    readiness = _readiness(
        activation_state_supplied=activation_state_supplied,
        result_preview=result_preview,
        built_ins=built_ins,
        actives=actives,
        includable=includable,
        any_unsafe=any_unsafe,
        any_conflict=any_conflict,
        acks_satisfied=acks_satisfied,
        refresh_mode=refresh_mode,
    )
    mode = _resolve_mode(refresh_mode, readiness, actives, deactivated, refresh_requested)
    state = _refresh_state(readiness)

    source_rows = tuple(
        _source_row(s, mode=mode, acks_satisfied=acks_satisfied)
        for s in sorted(sources, key=lambda s: (not s.built_in, s.stack_id, s.source_type))
    )
    deactivated_rows = tuple(
        _deactivated_row(s) for s in sorted(deactivated, key=lambda s: s.stack_id)
    )
    acknowledgement_rows = _acknowledgement_rows(acks)
    conflict_rows = tuple(
        _conflict_row(s) for s in sorted(actives, key=lambda s: s.stack_id)
        if s.has_conflict
    )
    unsafe_claim_rows = tuple(
        _unsafe_claim_row(s) for s in sorted(actives, key=lambda s: s.stack_id)
        if s.has_unsafe_claim
    )
    diagnostics = _diagnostics(
        readiness=readiness,
        actives=actives,
        deactivated=deactivated,
        any_unsafe=any_unsafe,
        any_conflict=any_conflict,
        acks_satisfied=acks_satisfied,
    )
    trust_badges = _trust_badges(source_rows)
    summary = _summary(
        mode=mode,
        state=state,
        readiness=readiness,
        built_ins=built_ins,
        actives=actives,
        source_rows=source_rows,
        deactivated=deactivated,
        diagnostics=diagnostics,
    )
    return OptionalSolverPluginManifestDiscoveryRefreshViewModel(
        summary=summary,
        source_rows=source_rows,
        deactivated_rows=deactivated_rows,
        acknowledgement_rows=acknowledgement_rows,
        diagnostics=diagnostics,
        conflict_rows=conflict_rows,
        unsafe_claim_rows=unsafe_claim_rows,
        trust_badges=trust_badges,
        actions=_action_states(),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
    )


def render_optional_solver_plugin_manifest_discovery_refresh_summary(
    view_model: OptionalSolverPluginManifestDiscoveryRefreshViewModel,
) -> dict[str, object]:
    """Return an in-memory, redacted, JSON-ready summary (writes no files)."""

    summary = view_model.summary
    return {
        "refresh_mode": summary.refresh_mode,
        "refresh_state": summary.refresh_state,
        "readiness": summary.readiness,
        "refresh_ready": summary.refresh_ready,
        "built_in_source_count": summary.built_in_source_count,
        "active_candidate_count": summary.active_candidate_count,
        "included_candidate_count": summary.included_candidate_count,
        "deactivated_excluded_count": summary.deactivated_excluded_count,
        "discovery_execution_performed": False,
        "validation_execution_performed": False,
        "solver_execution_performed": False,
        "dependency_installation_performed": False,
        "network_fetch_performed": False,
        "plugin_package_import_performed": False,
        "issue_mutation_performed": False,
        "release_mutation_performed": False,
        "certification_claimed": False,
        "not_validation_evidence": True,
        "sources": [
            {
                "stack_id": row.stack_id,
                "source_type": row.source_type,
                "source_reference_display": row.source_reference_display,
                "trust_label": row.trust_label,
                "discovery_source_state": row.discovery_source_state,
                "included": row.included,
                "redacted_source_reference": row.redacted_source_reference,
            }
            for row in view_model.source_rows
        ],
        "diagnostics": [
            {"code": d.code, "severity": d.severity, "stack_id": d.stack_id}
            for d in view_model.diagnostics
        ],
    }


def summarize_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
    view_model: OptionalSolverPluginManifestDiscoveryRefreshViewModel,
) -> str:
    """Return a concise discovery-refresh summary."""

    s = view_model.summary
    return (
        "Optional solver plugin manifest discovery refresh: "
        f"mode={s.refresh_mode}; state={s.refresh_state}; "
        f"built_in={s.built_in_source_count}; active={s.active_candidate_count}; "
        f"included={s.included_candidate_count}; "
        f"deactivated_excluded={s.deactivated_excluded_count}. "
        f"{INTEGRATION_NOT_IMPLEMENTED_TEXT}"
    )


def explain_optional_solver_plugin_manifest_discovery_refresh_viewmodel(
    view_model: OptionalSolverPluginManifestDiscoveryRefreshViewModel,
) -> str:
    """Explain the safety boundary of the discovery-refresh view-model."""

    disabled = ", ".join(
        action.action.value for action in view_model.actions if not action.enabled
    )
    return (
        summarize_optional_solver_plugin_manifest_discovery_refresh_viewmodel(view_model)
        + " The view-model transforms supplied activation/source data only; it "
        "does not run discovery, change passive discovery, persist activation or "
        "deactivation state, import plugin packages, scan directories, fetch "
        "network manifests, run validation, execute solvers, install "
        "dependencies, mutate issues, or mutate releases. "
        f"Disabled or future-only actions: {disabled}."
    )


# ----------------------------------------------------------------------
# Internal helpers (pure).
# ----------------------------------------------------------------------
def _sources_from_activation_view_model(
    activation_view_model: OptionalSolverPluginManifestActivationViewModel,
    built_in_source_count: int,
) -> tuple[OptionalSolverPluginManifestDiscoveryRefreshSourceInput, ...]:
    conflict_stack_ids = {row.stack_id for row in activation_view_model.conflict_rows}
    sources: list[OptionalSolverPluginManifestDiscoveryRefreshSourceInput] = []
    for index in range(max(0, built_in_source_count)):
        sources.append(
            OptionalSolverPluginManifestDiscoveryRefreshSourceInput(
                stack_id=f"builtin_{index}",
                display_name=f"Built-in stack {index}",
                source_type="built_in",
                trust_label="built_in",
                is_untrusted=False,
                activation_state="active_candidate",
                built_in=True,
                built_in_relationship="built-in (authoritative by default)",
            )
        )
    for row in activation_view_model.candidate_rows:
        if row.activation_state not in {"active_candidate", "deactivated"}:
            continue
        sources.append(
            OptionalSolverPluginManifestDiscoveryRefreshSourceInput(
                stack_id=row.stack_id,
                display_name=row.display_name,
                source_type=row.source_type,
                source_label=row.source_label,
                source_reference=row.source_reference_display,
                trust_label=row.trust_label,
                is_untrusted=row.is_untrusted,
                activation_state=row.activation_state,
                has_conflict=row.stack_id in conflict_stack_ids,
                has_unsafe_claim=bool(row.unsafe_claim_indicators),
                unsafe_claim_indicators=tuple(row.unsafe_claim_indicators),
                built_in=False,
                built_in_relationship=row.built_in_relationship,
            )
        )
    return tuple(sources)


def _readiness(
    *,
    activation_state_supplied: bool,
    result_preview: bool,
    built_ins: list,
    actives: list,
    includable: list,
    any_unsafe: bool,
    any_conflict: bool,
    acks_satisfied: bool,
    refresh_mode: str | None,
) -> OptionalSolverPluginManifestDiscoveryRefreshReadiness:
    Readiness = OptionalSolverPluginManifestDiscoveryRefreshReadiness
    if result_preview:
        return Readiness.RESULT_PREVIEW
    if not activation_state_supplied and not built_ins and not actives:
        return Readiness.UNAVAILABLE_NO_ACTIVATION_STATE
    built_in_only_mode = (
        refresh_mode
        == OptionalSolverPluginManifestDiscoveryRefreshMode.BUILT_IN_ONLY_REFRESH.value
    )
    if not actives:
        if built_ins and (built_in_only_mode or not refresh_mode):
            return Readiness.BUILT_IN_ONLY_READY
        return Readiness.UNAVAILABLE_NO_ACTIVE_CANDIDATES
    if not includable:
        if any_unsafe:
            return Readiness.BLOCKED_UNSAFE_CLAIM
        if any_conflict:
            return Readiness.BLOCKED_CONFLICT
        return Readiness.UNAVAILABLE_NO_ACTIVE_CANDIDATES
    if not acks_satisfied:
        return Readiness.BLOCKED_ACKNOWLEDGEMENT
    return Readiness.READY_PREVIEW_ONLY


def _resolve_mode(
    refresh_mode: str | None,
    readiness: OptionalSolverPluginManifestDiscoveryRefreshReadiness,
    actives: list,
    deactivated: list,
    refresh_requested: bool,
) -> str:
    Mode = OptionalSolverPluginManifestDiscoveryRefreshMode
    Readiness = OptionalSolverPluginManifestDiscoveryRefreshReadiness
    if refresh_mode:
        return refresh_mode
    if readiness in {Readiness.BLOCKED_CONFLICT, Readiness.BLOCKED_UNSAFE_CLAIM}:
        return Mode.BLOCKED_DUE_TO_UNTRUSTED_OR_CONFLICTING_SOURCES.value
    if readiness == Readiness.BUILT_IN_ONLY_READY:
        return Mode.BUILT_IN_ONLY_REFRESH.value
    if actives:
        if refresh_requested:
            return Mode.ACTIVATED_CANDIDATES_USER_INITIATED_REFRESH.value
        return Mode.ACTIVATED_CANDIDATES_PREVIEW_REFRESH.value
    if deactivated:
        return Mode.DEACTIVATED_CANDIDATES_EXCLUDED.value
    return Mode.BUILT_IN_ONLY_REFRESH.value


def _refresh_state(
    readiness: OptionalSolverPluginManifestDiscoveryRefreshReadiness,
) -> str:
    State = OptionalSolverPluginManifestDiscoveryRefreshState
    Readiness = OptionalSolverPluginManifestDiscoveryRefreshReadiness
    if readiness == Readiness.RESULT_PREVIEW:
        return State.REFRESH_RESULT_PREVIEW.value
    if readiness == Readiness.ERROR:
        return State.REFRESH_ERROR.value
    if readiness.value.startswith("unavailable"):
        return State.REFRESH_UNAVAILABLE.value
    if readiness.value.startswith("blocked"):
        return State.REFRESH_BLOCKED.value
    return State.REFRESH_READY.value


def _source_row(
    source: OptionalSolverPluginManifestDiscoveryRefreshSourceInput,
    *,
    mode: str,
    acks_satisfied: bool,
) -> OptionalSolverPluginManifestDiscoverySourceRowViewModel:
    SourceState = OptionalSolverPluginManifestDiscoverySourceState
    display, redacted = redact_optional_solver_plugin_manifest_source_reference(
        source.source_reference
    )
    if not display and source.source_label:
        display = source.source_label
        redacted = False

    blockers: list[str] = []
    warnings: list[str] = []
    if source.is_untrusted:
        warnings.append("Untrusted source; untrusted by default.")
    warnings.append(TRUST_NOT_CERTIFICATION_TEXT)

    if source.built_in:
        state = SourceState.BUILT_IN_ONLY
        included, excluded, reason = True, False, ""
    elif source.activation_state == "deactivated":
        state = SourceState.DEACTIVATED_EXCLUDED
        included, excluded, reason = False, True, "Deactivated candidates are excluded by default."
    elif source.has_unsafe_claim:
        state = SourceState.UNSAFE_CLAIM_BLOCKED
        included, excluded, reason = False, True, "Unsafe claims block discovery inclusion."
        blockers.append("Unsafe claims block discovery inclusion.")
    elif source.has_conflict:
        state = SourceState.CONFLICT_BLOCKED
        included, excluded, reason = False, True, "Built-ins win; conflict must be resolved."
        blockers.append("Built-ins win; conflict must be resolved.")
    elif source.activation_state != "active_candidate":
        state = SourceState.REFRESH_BLOCKED
        included, excluded, reason = False, True, "Source is not an active candidate."
        blockers.append("Activate the candidate before discovery refresh.")
    elif not acks_satisfied:
        state = SourceState.REFRESH_BLOCKED
        included, excluded, reason = False, True, "Required acknowledgements are missing."
        blockers.append("Required acknowledgements are missing.")
    else:
        state = SourceState.ACTIVE_CANDIDATE_INCLUDED
        included, excluded, reason = True, False, ""

    return OptionalSolverPluginManifestDiscoverySourceRowViewModel(
        stack_id=source.stack_id,
        display_name=source.display_name or source.stack_id,
        source_type=source.source_type,
        source_label=source.source_label,
        source_reference_display=display,
        trust_label=source.trust_label,
        discovery_source_state=state.value,
        activation_state=source.activation_state,
        refresh_mode=mode,
        included=included,
        excluded=excluded,
        exclusion_reason=reason,
        readiness="included" if included else "excluded",
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        required_acknowledgements=DISCOVERY_REFRESH_REQUIRED_ACKS,
        unsafe_claim_indicators=tuple(source.unsafe_claim_indicators),
        built_in_relationship=source.built_in_relationship,
        redacted_source_reference=redacted,
        is_untrusted=source.is_untrusted,
    )


def _deactivated_row(
    source: OptionalSolverPluginManifestDiscoveryRefreshSourceInput,
) -> OptionalSolverPluginManifestDeactivatedCandidateRowViewModel:
    display, redacted = redact_optional_solver_plugin_manifest_source_reference(
        source.source_reference
    )
    if not display and source.source_label:
        display = source.source_label
        redacted = False
    return OptionalSolverPluginManifestDeactivatedCandidateRowViewModel(
        stack_id=source.stack_id,
        source_label=source.source_label or source.stack_id,
        trust_label=source.trust_label,
        deactivated_state="deactivated",
        excluded_by_default=True,
        source_reference_display=display,
        redacted_source_reference=redacted,
    )


def _acknowledgement_rows(
    acks: Mapping[str, bool],
) -> tuple[OptionalSolverPluginManifestDiscoveryRefreshAcknowledgementRowViewModel, ...]:
    rows: list[OptionalSolverPluginManifestDiscoveryRefreshAcknowledgementRowViewModel] = []
    for ack_id in DISCOVERY_REFRESH_REQUIRED_ACKS:
        satisfied = bool(acks.get(ack_id, False))
        rows.append(
            OptionalSolverPluginManifestDiscoveryRefreshAcknowledgementRowViewModel(
                acknowledgement_id=ack_id,
                label=_ACK_LABELS.get(ack_id, ack_id),
                required=True,
                satisfied=satisfied,
                blocking=not satisfied,
                reason=(
                    "Required acknowledgement is satisfied."
                    if satisfied
                    else "Required acknowledgement is missing; refresh is blocked."
                ),
                related="discovery_refresh",
                warning_text=_ACK_LABELS.get(ack_id, ack_id),
            )
        )
    return tuple(rows)


def _diagnostics(
    *,
    readiness: OptionalSolverPluginManifestDiscoveryRefreshReadiness,
    actives: list,
    deactivated: list,
    any_unsafe: bool,
    any_conflict: bool,
    acks_satisfied: bool,
) -> tuple[OptionalSolverPluginManifestDiscoveryRefreshDiagnosticViewModel, ...]:
    Readiness = OptionalSolverPluginManifestDiscoveryRefreshReadiness
    items: list[OptionalSolverPluginManifestDiscoveryRefreshDiagnosticViewModel] = []

    def add(code: str, severity: str, blocker: bool = False, stack_id: str = "") -> None:
        items.append(
            OptionalSolverPluginManifestDiscoveryRefreshDiagnosticViewModel(
                severity=severity,
                category="discovery_refresh",
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
        add(OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED, "warning", blocker=True)
    if deactivated:
        add(OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED, "info")
    if any_conflict:
        add(OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED, "warning", blocker=True)
    if any_unsafe:
        add(OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM, "error", blocker=True)
    if actives and not acks_satisfied:
        add(OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED, "warning", blocker=True)
    if any(s.is_untrusted for s in actives):
        add(OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE, "warning")

    for code in (
        OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION,
        OSPMG_DISCOVERY_REFRESH_NO_INSTALL,
        OSPMG_DISCOVERY_REFRESH_NO_SOLVER_EXECUTION,
        OSPMG_DISCOVERY_REFRESH_NO_NETWORK_FETCH,
        OSPMG_DISCOVERY_REFRESH_NO_PLUGIN_IMPORT,
        OSPMG_DISCOVERY_REFRESH_NOT_ISSUE_CLOSURE,
        OSPMG_DISCOVERY_REFRESH_NOT_CERTIFICATION,
        OSPMG_DISCOVERY_REFRESH_INTEGRATION_NOT_IMPLEMENTED,
    ):
        add(code, "info")
    return tuple(items)


def _diagnostic_message(code: str) -> str:
    return {
        OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED: (
            "Discovery refresh requires an active candidate or built-in-only mode."
        ),
        OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED: (
            "Deactivated candidates are excluded from discovery inputs by default."
        ),
        OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED: "Required acknowledgements are missing.",
        OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE: "Source is untrusted by default.",
        OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED: "A stack-id conflict blocks the refresh input.",
        OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM: "Unsafe manifest claims block the refresh input.",
        OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION: "Discovery refresh is not validation evidence.",
        OSPMG_DISCOVERY_REFRESH_NO_INSTALL: "Discovery refresh does not install dependencies.",
        OSPMG_DISCOVERY_REFRESH_NO_SOLVER_EXECUTION: "Discovery refresh does not execute solvers.",
        OSPMG_DISCOVERY_REFRESH_NO_NETWORK_FETCH: "Discovery refresh does not fetch the network.",
        OSPMG_DISCOVERY_REFRESH_NO_PLUGIN_IMPORT: "Discovery refresh does not import plugins.",
        OSPMG_DISCOVERY_REFRESH_NOT_ISSUE_CLOSURE: "Discovery refresh does not close issues.",
        OSPMG_DISCOVERY_REFRESH_NOT_CERTIFICATION: "A trust label is not certification.",
        OSPMG_DISCOVERY_REFRESH_INTEGRATION_NOT_IMPLEMENTED: INTEGRATION_NOT_IMPLEMENTED_TEXT,
    }.get(code, code)


def _diagnostic_fix(code: str) -> str:
    return {
        OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED: (
            "Activate a candidate or use built-in-only refresh."
        ),
        OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED: "Resolve the duplicate stack id; built-ins win.",
        OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM: "Remove unsafe claims from the manifest.",
        OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED: "Satisfy required acknowledgements.",
    }.get(code, "")


def _conflict_row(
    source: OptionalSolverPluginManifestDiscoveryRefreshSourceInput,
) -> OptionalSolverPluginManifestDiscoveryRefreshConflictRowViewModel:
    display, _ = redact_optional_solver_plugin_manifest_source_reference(
        source.source_reference
    )
    return OptionalSolverPluginManifestDiscoveryRefreshConflictRowViewModel(
        stack_id=source.stack_id,
        built_in_source=f"builtin:{source.stack_id}",
        user_plugin_source=display or source.source_label or source.source_type,
        conflict_policy="built-ins win by default; plugin override disabled",
        built_ins_win_default=True,
        refresh_state=OptionalSolverPluginManifestDiscoveryRefreshState.REFRESH_BLOCKED.value,
        required_future_policy=(
            "An explicit future trust/override policy gate is required to include a "
            "conflicting manifest in discovery."
        ),
    )


def _unsafe_claim_row(
    source: OptionalSolverPluginManifestDiscoveryRefreshSourceInput,
) -> OptionalSolverPluginManifestDiscoveryRefreshUnsafeClaimRowViewModel:
    return OptionalSolverPluginManifestDiscoveryRefreshUnsafeClaimRowViewModel(
        stack_id=source.stack_id,
        source_label=source.source_label or source.stack_id,
        trust_label=source.trust_label,
        unsafe_claim_indicators=tuple(source.unsafe_claim_indicators),
        blocked=True,
        reason="Unsafe claims block discovery inclusion; resolve before refresh.",
    )


def _trust_badges(
    source_rows: Sequence[OptionalSolverPluginManifestDiscoverySourceRowViewModel],
) -> tuple[OptionalSolverPluginManifestDiscoveryRefreshTrustBadgeViewModel, ...]:
    seen: dict[
        tuple[str, str], OptionalSolverPluginManifestDiscoveryRefreshTrustBadgeViewModel
    ] = {}
    for row in source_rows:
        key = (row.source_type, row.trust_label)
        if key in seen:
            continue
        seen[key] = OptionalSolverPluginManifestDiscoveryRefreshTrustBadgeViewModel(
            source_type=row.source_type,
            trust_label=row.trust_label,
            source_label=row.source_label,
            discovery_source_state=row.discovery_source_state,
            activation_state=row.activation_state,
            warning_text=(
                "Untrusted source; untrusted by default."
                if row.is_untrusted
                else "Built-in/reviewed source; trust label is not certification."
            ),
        )
    return tuple(seen[key] for key in sorted(seen))


def _summary(
    *,
    mode: str,
    state: str,
    readiness: OptionalSolverPluginManifestDiscoveryRefreshReadiness,
    built_ins: list,
    actives: list,
    source_rows: Sequence[OptionalSolverPluginManifestDiscoverySourceRowViewModel],
    deactivated: list,
    diagnostics: Sequence[OptionalSolverPluginManifestDiscoveryRefreshDiagnosticViewModel],
) -> OptionalSolverPluginManifestDiscoveryRefreshSummaryViewModel:
    SourceState = OptionalSolverPluginManifestDiscoverySourceState
    Readiness = OptionalSolverPluginManifestDiscoveryRefreshReadiness
    included = sum(1 for r in source_rows if r.included and not _is_built_in_row(r))
    conflict_blocked = sum(
        1 for r in source_rows if r.discovery_source_state == SourceState.CONFLICT_BLOCKED.value
    )
    unsafe_blocked = sum(
        1 for r in source_rows
        if r.discovery_source_state == SourceState.UNSAFE_CLAIM_BLOCKED.value
    )
    warnings = sum(1 for d in diagnostics if d.severity == "warning")
    errors = sum(1 for d in diagnostics if d.severity in {"error", "blocker"})
    ready = readiness in {
        Readiness.BUILT_IN_ONLY_READY,
        Readiness.READY_PREVIEW_ONLY,
        Readiness.READY_FUTURE_REFRESH,
    }
    status = (
        f"Discovery refresh ({readiness.value}): {len(built_ins)} built-in, "
        f"{len(actives)} active candidate(s), {included} included, "
        f"{len(deactivated)} deactivated-excluded. Discovery refresh is not "
        "validation evidence."
    )
    return OptionalSolverPluginManifestDiscoveryRefreshSummaryViewModel(
        refresh_mode=mode,
        refresh_state=state,
        readiness=readiness.value,
        built_in_source_count=len(built_ins),
        active_candidate_count=len(actives),
        included_candidate_count=included,
        deactivated_excluded_count=len(deactivated),
        deactivated_visible_count=len(deactivated),
        conflict_blocked_count=conflict_blocked,
        unsafe_claim_blocked_count=unsafe_blocked,
        acknowledgement_required_count=len(DISCOVERY_REFRESH_REQUIRED_ACKS),
        diagnostic_count=len(diagnostics),
        warning_count=warnings,
        error_count=errors,
        refresh_ready=ready,
        status_text=status,
    )


def _is_built_in_row(
    row: OptionalSolverPluginManifestDiscoverySourceRowViewModel,
) -> bool:
    return row.discovery_source_state == (
        OptionalSolverPluginManifestDiscoverySourceState.BUILT_IN_ONLY.value
    )


def _action_states() -> tuple[OptionalSolverPluginManifestDiscoveryRefreshActionState, ...]:
    Action = OptionalSolverPluginManifestDiscoveryRefreshAction
    states: list[OptionalSolverPluginManifestDiscoveryRefreshActionState] = []
    for action in Action:
        unsafe = action.value in _UNSAFE_ACTIONS
        states.append(
            OptionalSolverPluginManifestDiscoveryRefreshActionState(
                action=action,
                label=action.value.replace("_", " ").title(),
                enabled=False,
                available=not unsafe,
                reason=_action_reason(action),
                future_action=True,
            )
        )
    return tuple(states)


def _action_reason(action: OptionalSolverPluginManifestDiscoveryRefreshAction) -> str:
    Action = OptionalSolverPluginManifestDiscoveryRefreshAction
    if action.value in _UNSAFE_ACTIONS:
        return {
            Action.RUN_DISCOVERY.value: "Discovery execution is unavailable from this view-model.",
            Action.RUN_VALIDATION.value: "Validation requires a separate OSW-VALID gate.",
            Action.INSTALL_DEPENDENCY.value: "Dependency installation is unavailable.",
            Action.EXECUTE_SOLVER.value: "Solver execution is unavailable.",
            Action.CLOSE_ISSUE.value: "Issue closure requires separate validation/closure gates.",
        }[action.value]
    if action == Action.EXPORT_REDACTED_SUMMARY:
        return "Produces an in-memory redacted summary only; it writes no files."
    return (
        "Future GUI/source action; discovery-refresh integration is a future gate "
        "(OSW-EXP-084) and this view-model runs nothing."
    )


def _guidance_text() -> tuple[str, ...]:
    return (
        "Discovery-refresh preview is data-only.",
        INTEGRATION_NOT_IMPLEMENTED_TEXT,
        INCLUSION_NOT_VALIDATION_TEXT,
        TRUST_NOT_CERTIFICATION_TEXT,
        "Built-in manifests win by default; conflicts require an explicit future policy.",
        "User-selected and plugin-provided manifests are untrusted by default.",
        "Deactivated candidates are excluded by default and are not validation failures.",
        "Discovery refresh is not validation, installation, or solver execution.",
        "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
        "bounded, issue-specific evidence; skipped-missing remains historical "
        "non-pass evidence.",
    )


def _safety_text() -> tuple[str, ...]:
    return (
        "No runtime discovery integration.",
        "No passive discovery behavior change.",
        "No activation persistence.",
        "No deactivation persistence.",
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
    "ACK_CONFLICT_OR_OVERRIDE_VISIBLE",
    "ACK_DEACTIVATED_CANDIDATES_EXCLUDED",
    "ACK_NO_NETWORK_FETCH",
    "ACK_NO_PLUGIN_PACKAGE_IMPORT",
    "ACK_REFRESH_NOT_CERTIFICATION",
    "ACK_REFRESH_NOT_INSTALL",
    "ACK_REFRESH_NOT_ISSUE_CLOSURE",
    "ACK_REFRESH_NOT_SOLVER_EXECUTION",
    "ACK_REFRESH_NOT_VALIDATION",
    "ACK_UNTRUSTED_MANIFEST_SOURCE",
    "DISCOVERY_REFRESH_BLOCKED_TRANSITIONS",
    "DISCOVERY_REFRESH_REQUIRED_ACKS",
    "OSPMG_DISCOVERY_REFRESH_ACK_REQUIRED",
    "OSPMG_DISCOVERY_REFRESH_ACTIVE_CANDIDATE_REQUIRED",
    "OSPMG_DISCOVERY_REFRESH_CONFLICT_BLOCKED",
    "OSPMG_DISCOVERY_REFRESH_DEACTIVATED_EXCLUDED",
    "OSPMG_DISCOVERY_REFRESH_DIAGNOSTIC_CODES",
    "OSPMG_DISCOVERY_REFRESH_INTEGRATION_NOT_IMPLEMENTED",
    "OSPMG_DISCOVERY_REFRESH_NO_INSTALL",
    "OSPMG_DISCOVERY_REFRESH_NO_NETWORK_FETCH",
    "OSPMG_DISCOVERY_REFRESH_NO_PLUGIN_IMPORT",
    "OSPMG_DISCOVERY_REFRESH_NO_SOLVER_EXECUTION",
    "OSPMG_DISCOVERY_REFRESH_NOT_CERTIFICATION",
    "OSPMG_DISCOVERY_REFRESH_NOT_ISSUE_CLOSURE",
    "OSPMG_DISCOVERY_REFRESH_NOT_VALIDATION",
    "OSPMG_DISCOVERY_REFRESH_UNSAFE_CLAIM",
    "OSPMG_DISCOVERY_REFRESH_UNTRUSTED_SOURCE",
    "OptionalSolverPluginManifestDeactivatedCandidateRowViewModel",
    "OptionalSolverPluginManifestDiscoveryRefreshAcknowledgementRowViewModel",
    "OptionalSolverPluginManifestDiscoveryRefreshAction",
    "OptionalSolverPluginManifestDiscoveryRefreshActionState",
    "OptionalSolverPluginManifestDiscoveryRefreshConflictRowViewModel",
    "OptionalSolverPluginManifestDiscoveryRefreshDiagnosticViewModel",
    "OptionalSolverPluginManifestDiscoveryRefreshMode",
    "OptionalSolverPluginManifestDiscoveryRefreshReadiness",
    "OptionalSolverPluginManifestDiscoveryRefreshSourceInput",
    "OptionalSolverPluginManifestDiscoveryRefreshState",
    "OptionalSolverPluginManifestDiscoveryRefreshSummaryViewModel",
    "OptionalSolverPluginManifestDiscoveryRefreshTrustBadgeViewModel",
    "OptionalSolverPluginManifestDiscoveryRefreshUnsafeClaimRowViewModel",
    "OptionalSolverPluginManifestDiscoveryRefreshViewModel",
    "OptionalSolverPluginManifestDiscoverySourceRowViewModel",
    "OptionalSolverPluginManifestDiscoverySourceState",
    "build_optional_solver_plugin_manifest_discovery_refresh_viewmodel",
    "explain_optional_solver_plugin_manifest_discovery_refresh_viewmodel",
    "redact_optional_solver_plugin_manifest_discovery_source_reference",
    "render_optional_solver_plugin_manifest_discovery_refresh_summary",
    "summarize_optional_solver_plugin_manifest_discovery_refresh_viewmodel",
]
