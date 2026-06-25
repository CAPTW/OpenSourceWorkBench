"""Pure view-model helpers for optional solver GUI passive refresh.

This module models refresh state and applies caller-supplied passive discovery
reports to an existing optional solver health panel view-model. It does not
run discovery, create workers, import Qt/PySide, execute solvers, write files,
or install dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from .discovery_models import (
    OptionalSolverDiscoveryReport,
    OptionalSolverStackDiscovery,
)
from .gui_health_viewmodel import (
    OptionalSolverHealthPanelViewModel,
    build_optional_solver_health_panel_viewmodel,
)
from .manifest_models import OptionalSolverManifest


class OptionalSolverRefreshState(str, Enum):
    """Passive refresh lifecycle states for GUI display."""

    IDLE = "idle"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    STALE_IGNORED = "stale_ignored"

    @classmethod
    def from_value(cls, value: object) -> OptionalSolverRefreshState:
        if isinstance(value, cls):
            return value
        return cls(str(value))


class OptionalSolverRefreshAction(str, Enum):
    """Refresh-related action identifiers for future GUI wiring."""

    REFRESH_PASSIVE_DISCOVERY = "refresh_passive_discovery"
    CANCEL_REFRESH = "cancel_refresh"
    RUN_VALIDATION = "run_validation"
    INSTALL_SOLVER = "install_solver"
    CLOSE_ISSUE = "close_issue"


@dataclass(frozen=True, slots=True)
class OptionalSolverRefreshActionState:
    """Display state for a future refresh action."""

    action: OptionalSolverRefreshAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverRefreshDiagnostic:
    """Diagnostic row for refresh state and result handling."""

    severity: str
    code: str
    message: str
    field: str = ""
    suggested_fix: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverRefreshRequest:
    """Caller-owned passive refresh request metadata."""

    request_id: str
    selected_stack_id: str = ""
    filter_text: str = ""
    health_state_filters: tuple[str, ...] = field(default_factory=tuple)
    requested_at: str = ""
    source: str = "optional_solver_gui_refresh"


@dataclass(frozen=True, slots=True)
class OptionalSolverRefreshResult:
    """Caller-supplied passive refresh result metadata.

    The discovery reports are produced outside this module by a future injected
    runner. This module only consumes the supplied reports.
    """

    request_id: str
    state: OptionalSolverRefreshState = OptionalSolverRefreshState.COMPLETED
    discovery_reports: (
        OptionalSolverDiscoveryReport
        | OptionalSolverStackDiscovery
        | Sequence[OptionalSolverDiscoveryReport | OptionalSolverStackDiscovery]
        | None
    ) = None
    generated_at: str = ""
    source: str = "optional_solver_gui_refresh"
    status_text: str = ""
    error_text: str = ""
    diagnostics: tuple[OptionalSolverRefreshDiagnostic, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True, slots=True)
class OptionalSolverRefreshStatusViewModel:
    """GUI-ready passive refresh status display data."""

    state: OptionalSolverRefreshState
    active_request_id: str
    status_text: str
    error_text: str
    last_refresh_timestamp: str = ""
    source: str = ""
    actions: tuple[OptionalSolverRefreshActionState, ...] = field(default_factory=tuple)
    diagnostics: tuple[OptionalSolverRefreshDiagnostic, ...] = field(
        default_factory=tuple
    )
    not_validation_evidence: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverRefreshPlan:
    """Pure refresh plan for future GUI orchestration."""

    current_panel: OptionalSolverHealthPanelViewModel
    state: OptionalSolverRefreshState
    request: OptionalSolverRefreshRequest | None
    status: OptionalSolverRefreshStatusViewModel
    selected_stack_id: str
    filter_text: str
    health_state_filters: tuple[str, ...]
    can_request_refresh: bool
    can_cancel_refresh: bool
    not_validation_evidence: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverRefreshApplyResult:
    """Result of applying or rejecting caller-supplied refresh output."""

    state: OptionalSolverRefreshState
    panel: OptionalSolverHealthPanelViewModel
    applied: bool
    ignored: bool
    active_request_id: str = ""
    result_request_id: str = ""
    status_text: str = ""
    error_text: str = ""
    selected_stack_id: str = ""
    filter_text: str = ""
    health_state_filters: tuple[str, ...] = field(default_factory=tuple)
    last_refresh_timestamp: str = ""
    source: str = ""
    diagnostics: tuple[OptionalSolverRefreshDiagnostic, ...] = field(
        default_factory=tuple
    )
    not_validation_evidence: bool = True


def build_optional_solver_refresh_plan(
    current_panel: OptionalSolverHealthPanelViewModel,
    *,
    state: OptionalSolverRefreshState | str = OptionalSolverRefreshState.IDLE,
    request_id: str = "",
    selected_stack_id: str | None = None,
    filter_text: str | None = None,
    health_state_filters: Sequence[str] | None = None,
    requested_at: str = "",
    source: str = "optional_solver_gui_refresh",
) -> OptionalSolverRefreshPlan:
    """Build a side-effect-free refresh plan for an existing panel."""

    active_state = OptionalSolverRefreshState.from_value(state)
    active_selected = (
        current_panel.selected_stack_id
        if selected_stack_id is None
        else selected_stack_id
    )
    active_filter = current_panel.filter_text if filter_text is None else filter_text
    active_filters = (
        current_panel.health_state_filters
        if health_state_filters is None
        else tuple(str(item) for item in health_state_filters)
    )
    active_request = None
    active_request_id = ""
    if active_state in {
        OptionalSolverRefreshState.PENDING,
        OptionalSolverRefreshState.RUNNING,
    }:
        active_request_id = request_id or _new_request_id()
        active_request = OptionalSolverRefreshRequest(
            request_id=active_request_id,
            selected_stack_id=active_selected,
            filter_text=active_filter,
            health_state_filters=active_filters,
            requested_at=requested_at,
            source=source,
        )

    status = build_optional_solver_refresh_status_viewmodel(
        state=active_state,
        active_request_id=active_request_id,
        timestamp=requested_at,
        source=source,
    )
    return OptionalSolverRefreshPlan(
        current_panel=current_panel,
        state=active_state,
        request=active_request,
        status=status,
        selected_stack_id=active_selected,
        filter_text=active_filter,
        health_state_filters=active_filters,
        can_request_refresh=_can_request_refresh(active_state),
        can_cancel_refresh=_can_cancel_refresh(active_state),
    )


def build_optional_solver_refresh_status_viewmodel(
    *,
    state: OptionalSolverRefreshState | str = OptionalSolverRefreshState.IDLE,
    active_request_id: str = "",
    timestamp: str = "",
    source: str = "",
    status_text: str = "",
    error_text: str = "",
    diagnostics: Sequence[OptionalSolverRefreshDiagnostic] | None = None,
) -> OptionalSolverRefreshStatusViewModel:
    """Build GUI-ready refresh status text and action states."""

    active_state = OptionalSolverRefreshState.from_value(state)
    return OptionalSolverRefreshStatusViewModel(
        state=active_state,
        active_request_id=active_request_id,
        status_text=status_text or _status_text(active_state),
        error_text=error_text,
        last_refresh_timestamp=timestamp,
        source=source,
        actions=_action_states(active_state),
        diagnostics=tuple(diagnostics or ()),
        not_validation_evidence=True,
    )


def apply_optional_solver_refresh_success(
    current_panel: OptionalSolverHealthPanelViewModel,
    *,
    manifests: Sequence[OptionalSolverManifest] | None = None,
    discovery_reports: (
        OptionalSolverDiscoveryReport
        | OptionalSolverStackDiscovery
        | Sequence[OptionalSolverDiscoveryReport | OptionalSolverStackDiscovery]
        | None
    ) = None,
    request: OptionalSolverRefreshRequest | None = None,
    result: OptionalSolverRefreshResult | None = None,
    active_request_id: str = "",
    selected_stack_id: str | None = None,
    filter_text: str | None = None,
    health_state_filters: Sequence[str] | None = None,
    timestamp: str = "",
    source: str = "",
) -> OptionalSolverRefreshApplyResult:
    """Apply caller-supplied passive reports to a new health panel view-model."""

    result_request_id = _result_request_id(result, request)
    if _is_stale(active_request_id, result_request_id):
        return ignore_optional_solver_stale_refresh_result(
            current_panel,
            active_request_id=active_request_id,
            result_request_id=result_request_id,
            timestamp=timestamp or (result.generated_at if result else ""),
            source=source or (result.source if result else ""),
        )

    active_reports = discovery_reports
    if active_reports is None and result is not None:
        active_reports = result.discovery_reports
    selected, filter_value, filters = _preserved_inputs(
        current_panel,
        request=request,
        selected_stack_id=selected_stack_id,
        filter_text=filter_text,
        health_state_filters=health_state_filters,
    )
    panel = build_optional_solver_health_panel_viewmodel(
        manifests=manifests,
        discovery_reports=active_reports,
        validation_history=current_panel.validation_history,
        selected_stack_id=selected,
        filter_text=filter_value,
        health_state_filters=filters,
    )
    applied_timestamp = timestamp or (result.generated_at if result else "")
    applied_source = source or (result.source if result else "")
    return OptionalSolverRefreshApplyResult(
        state=OptionalSolverRefreshState.COMPLETED,
        panel=panel,
        applied=True,
        ignored=False,
        active_request_id=active_request_id,
        result_request_id=result_request_id,
        status_text=(
            "Passive discovery refresh completed. Applied supplied reports to a "
            "new health panel view-model. Refresh output is not validation evidence."
        ),
        error_text="",
        selected_stack_id=panel.selected_stack_id,
        filter_text=panel.filter_text,
        health_state_filters=panel.health_state_filters,
        last_refresh_timestamp=applied_timestamp,
        source=applied_source,
        diagnostics=tuple(result.diagnostics if result else ()),
        not_validation_evidence=True,
    )


def apply_optional_solver_refresh_failure(
    current_panel: OptionalSolverHealthPanelViewModel,
    *,
    request: OptionalSolverRefreshRequest | None = None,
    result: OptionalSolverRefreshResult | None = None,
    active_request_id: str = "",
    error_text: str = "",
    timestamp: str = "",
    source: str = "",
) -> OptionalSolverRefreshApplyResult:
    """Record a failed refresh while preserving the current panel."""

    result_request_id = _result_request_id(result, request)
    if _is_stale(active_request_id, result_request_id):
        return ignore_optional_solver_stale_refresh_result(
            current_panel,
            active_request_id=active_request_id,
            result_request_id=result_request_id,
            timestamp=timestamp or (result.generated_at if result else ""),
            source=source or (result.source if result else ""),
        )
    active_error = error_text or (result.error_text if result else "")
    return _preserved_apply_result(
        current_panel,
        state=OptionalSolverRefreshState.FAILED,
        active_request_id=active_request_id,
        result_request_id=result_request_id,
        status_text="Passive discovery refresh failed. Current health view remains.",
        error_text=active_error or "Refresh failed.",
        timestamp=timestamp or (result.generated_at if result else ""),
        source=source or (result.source if result else ""),
        diagnostics=tuple(result.diagnostics if result else ()),
    )


def apply_optional_solver_refresh_canceled(
    current_panel: OptionalSolverHealthPanelViewModel,
    *,
    request: OptionalSolverRefreshRequest | None = None,
    result: OptionalSolverRefreshResult | None = None,
    active_request_id: str = "",
    timestamp: str = "",
    source: str = "",
) -> OptionalSolverRefreshApplyResult:
    """Record a canceled refresh while preserving the current panel."""

    result_request_id = _result_request_id(result, request)
    if _is_stale(active_request_id, result_request_id):
        return ignore_optional_solver_stale_refresh_result(
            current_panel,
            active_request_id=active_request_id,
            result_request_id=result_request_id,
            timestamp=timestamp or (result.generated_at if result else ""),
            source=source or (result.source if result else ""),
        )
    return _preserved_apply_result(
        current_panel,
        state=OptionalSolverRefreshState.CANCELED,
        active_request_id=active_request_id,
        result_request_id=result_request_id,
        status_text="Passive discovery refresh canceled. Current health view remains.",
        error_text="",
        timestamp=timestamp or (result.generated_at if result else ""),
        source=source or (result.source if result else ""),
        diagnostics=tuple(result.diagnostics if result else ()),
    )


def ignore_optional_solver_stale_refresh_result(
    current_panel: OptionalSolverHealthPanelViewModel,
    *,
    active_request_id: str = "",
    result_request_id: str = "",
    timestamp: str = "",
    source: str = "",
) -> OptionalSolverRefreshApplyResult:
    """Ignore a refresh result that does not match the active request id."""

    return OptionalSolverRefreshApplyResult(
        state=OptionalSolverRefreshState.STALE_IGNORED,
        panel=current_panel,
        applied=False,
        ignored=True,
        active_request_id=active_request_id,
        result_request_id=result_request_id,
        status_text=(
            "Stale passive discovery refresh result ignored. Current health view "
            "remains. Refresh output is not validation evidence."
        ),
        error_text="",
        selected_stack_id=current_panel.selected_stack_id,
        filter_text=current_panel.filter_text,
        health_state_filters=current_panel.health_state_filters,
        last_refresh_timestamp=timestamp,
        source=source,
        diagnostics=(
            OptionalSolverRefreshDiagnostic(
                severity="info",
                code="OSR_STALE_RESULT_IGNORED",
                message="Refresh result request id did not match the active request.",
                field="request_id",
                suggested_fix="Ignore stale results from older refresh requests.",
            ),
        ),
        not_validation_evidence=True,
    )


def explain_optional_solver_refresh(
    value: OptionalSolverRefreshPlan
    | OptionalSolverRefreshStatusViewModel
    | OptionalSolverRefreshApplyResult,
) -> str:
    """Return a concise refresh state explanation."""

    state = value.state.value
    if isinstance(value, OptionalSolverRefreshApplyResult):
        return (
            f"Optional solver passive refresh state is {state}; "
            f"applied={value.applied}, ignored={value.ignored}. Refresh output "
            "is setup evidence only and not validation evidence."
        )
    return (
        f"Optional solver passive refresh state is {state}. The refresh "
        "view-model does not run discovery, execute solvers, create workers, "
        "install dependencies, or mutate issues."
    )


def _preserved_inputs(
    current_panel: OptionalSolverHealthPanelViewModel,
    *,
    request: OptionalSolverRefreshRequest | None,
    selected_stack_id: str | None,
    filter_text: str | None,
    health_state_filters: Sequence[str] | None,
) -> tuple[str, str, tuple[str, ...]]:
    selected = current_panel.selected_stack_id
    filter_value = current_panel.filter_text
    filters = current_panel.health_state_filters
    if request is not None:
        selected = request.selected_stack_id
        filter_value = request.filter_text
        filters = request.health_state_filters
    if selected_stack_id is not None:
        selected = selected_stack_id
    if filter_text is not None:
        filter_value = filter_text
    if health_state_filters is not None:
        filters = tuple(str(item) for item in health_state_filters)
    return selected, filter_value, filters


def _preserved_apply_result(
    current_panel: OptionalSolverHealthPanelViewModel,
    *,
    state: OptionalSolverRefreshState,
    active_request_id: str,
    result_request_id: str,
    status_text: str,
    error_text: str,
    timestamp: str,
    source: str,
    diagnostics: tuple[OptionalSolverRefreshDiagnostic, ...],
) -> OptionalSolverRefreshApplyResult:
    return OptionalSolverRefreshApplyResult(
        state=state,
        panel=current_panel,
        applied=False,
        ignored=False,
        active_request_id=active_request_id,
        result_request_id=result_request_id,
        status_text=status_text + " Refresh output is not validation evidence.",
        error_text=error_text,
        selected_stack_id=current_panel.selected_stack_id,
        filter_text=current_panel.filter_text,
        health_state_filters=current_panel.health_state_filters,
        last_refresh_timestamp=timestamp,
        source=source,
        diagnostics=diagnostics,
        not_validation_evidence=True,
    )


def _result_request_id(
    result: OptionalSolverRefreshResult | None,
    request: OptionalSolverRefreshRequest | None,
) -> str:
    if result is not None:
        return result.request_id
    if request is not None:
        return request.request_id
    return ""


def _is_stale(active_request_id: str, result_request_id: str) -> bool:
    return bool(active_request_id and result_request_id and active_request_id != result_request_id)


def _status_text(state: OptionalSolverRefreshState) -> str:
    messages = {
        OptionalSolverRefreshState.IDLE: "Refresh idle.",
        OptionalSolverRefreshState.PENDING: "Passive discovery refresh pending.",
        OptionalSolverRefreshState.RUNNING: "Passive discovery refresh running.",
        OptionalSolverRefreshState.COMPLETED: (
            "Passive discovery refresh completed. Output is not validation evidence."
        ),
        OptionalSolverRefreshState.FAILED: (
            "Passive discovery refresh failed. Current health view remains."
        ),
        OptionalSolverRefreshState.CANCELED: (
            "Passive discovery refresh canceled. Current health view remains."
        ),
        OptionalSolverRefreshState.STALE_IGNORED: (
            "Stale passive discovery refresh result ignored."
        ),
    }
    return messages[state]


def _action_states(
    state: OptionalSolverRefreshState,
) -> tuple[OptionalSolverRefreshActionState, ...]:
    can_refresh = _can_request_refresh(state)
    can_cancel = _can_cancel_refresh(state)
    return (
        OptionalSolverRefreshActionState(
            action=OptionalSolverRefreshAction.REFRESH_PASSIVE_DISCOVERY,
            label="Refresh passive discovery",
            enabled=can_refresh,
            available=True,
            reason=(
                "Available for future GUI wiring; this view-model does not run "
                "discovery."
                if can_refresh
                else "Refresh request is already pending or running."
            ),
        ),
        OptionalSolverRefreshActionState(
            action=OptionalSolverRefreshAction.CANCEL_REFRESH,
            label="Cancel refresh",
            enabled=can_cancel,
            available=True,
            reason=(
                "Future display-only cancel state for an injected runner."
                if can_cancel
                else "No active refresh request to cancel."
            ),
        ),
        OptionalSolverRefreshActionState(
            action=OptionalSolverRefreshAction.RUN_VALIDATION,
            label="Run validation",
            enabled=False,
            available=False,
            reason="Active validation requires an explicit OSW-VALID gate.",
        ),
        OptionalSolverRefreshActionState(
            action=OptionalSolverRefreshAction.INSTALL_SOLVER,
            label="Install solver",
            enabled=False,
            available=False,
            reason="Solver installation is unavailable.",
        ),
        OptionalSolverRefreshActionState(
            action=OptionalSolverRefreshAction.CLOSE_ISSUE,
            label="Close issue",
            enabled=False,
            available=False,
            reason="Issue closure requires a separate closure-review gate.",
        ),
    )


def _can_request_refresh(state: OptionalSolverRefreshState) -> bool:
    return state not in {
        OptionalSolverRefreshState.PENDING,
        OptionalSolverRefreshState.RUNNING,
    }


def _can_cancel_refresh(state: OptionalSolverRefreshState) -> bool:
    return state in {
        OptionalSolverRefreshState.PENDING,
        OptionalSolverRefreshState.RUNNING,
    }


def _new_request_id() -> str:
    return f"osr-{uuid4().hex}"


__all__ = [
    "OptionalSolverRefreshAction",
    "OptionalSolverRefreshActionState",
    "OptionalSolverRefreshApplyResult",
    "OptionalSolverRefreshDiagnostic",
    "OptionalSolverRefreshPlan",
    "OptionalSolverRefreshRequest",
    "OptionalSolverRefreshResult",
    "OptionalSolverRefreshState",
    "OptionalSolverRefreshStatusViewModel",
    "apply_optional_solver_refresh_canceled",
    "apply_optional_solver_refresh_failure",
    "apply_optional_solver_refresh_success",
    "build_optional_solver_refresh_plan",
    "build_optional_solver_refresh_status_viewmodel",
    "explain_optional_solver_refresh",
    "ignore_optional_solver_stale_refresh_result",
]
