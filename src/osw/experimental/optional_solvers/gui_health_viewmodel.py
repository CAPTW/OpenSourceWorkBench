"""Pure view-models for a future optional solver GUI health panel.

This module prepares GUI-ready display data from declarative manifests and
already-supplied passive discovery reports. It does not import Qt/PySide,
execute discovery, run solver commands, import optional solver packages, or
install dependencies.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum

from .builtin_manifests import builtin_optional_solver_manifests
from .discovery_models import (
    OptionalSolverDiscoveryDiagnostic,
    OptionalSolverDiscoveryReport,
    OptionalSolverEnvironmentHintDiscovery,
    OptionalSolverExecutableDiscovery,
    OptionalSolverPythonPackageDiscovery,
    OptionalSolverStackDiscovery,
)
from .manifest_models import (
    OptionalSolverHealthState,
    OptionalSolverManifest,
    OptionalSolverRequirement,
)


class OptionalSolverHealthPanelAction(str, Enum):
    """Display-only action identifiers for the future GUI panel."""

    REFRESH_PASSIVE_DISCOVERY = "refresh_passive_discovery"
    RUN_VALIDATION_GATE = "run_validation_gate"
    INSTALL_SOLVER = "install_solver"
    CLOSE_ISSUE = "close_issue"
    COPY_SUMMARY = "copy_summary"
    OPEN_DOCS = "open_docs"


@dataclass(frozen=True, slots=True)
class OptionalSolverHealthPanelActionState:
    """GUI-ready action state.

    These records are display data only. Selecting them is a future GUI concern.
    """

    action: OptionalSolverHealthPanelAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverRequirementRowViewModel:
    """GUI-ready row for an executable, package, or environment hint."""

    requirement_type: str
    identifier: str
    display_name: str
    required: bool
    found: bool | None
    status_text: str
    detail_text: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class OptionalSolverDiagnosticRowViewModel:
    """GUI-ready diagnostic row for a stack."""

    stack_id: str
    severity: str
    code: str
    message: str
    path: str = ""
    suggested_fix: str = ""
    redaction_notice: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverGuidanceRowViewModel:
    """GUI-ready guidance row for the panel or selected stack."""

    category: str
    text: str
    severity: str = "info"


@dataclass(frozen=True, slots=True)
class OptionalSolverValidationHistoryRowViewModel:
    """Display row for prior validation evidence."""

    source: str
    status: str
    summary: str
    timestamp: str = ""
    related_issue: int | None = None
    is_pass_evidence: bool = False
    closure_review_required: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverStackCardViewModel:
    """GUI-ready card summary for one optional solver stack."""

    stack_id: str
    display_name: str
    related_issue: int | None
    issue_reference: str
    health_state: str
    support_status: str
    short_status_text: str
    missing_requirements_count: int
    diagnostics_count: int
    has_non_bundled_disclaimer: bool
    selected: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverStackDetailsViewModel:
    """GUI-ready details data for one optional solver stack."""

    stack_id: str
    display_name: str
    capabilities: tuple[str, ...]
    executable_requirements: tuple[OptionalSolverRequirementRowViewModel, ...]
    python_package_requirements: tuple[OptionalSolverRequirementRowViewModel, ...]
    environment_hints: tuple[OptionalSolverRequirementRowViewModel, ...]
    version_probe_text: str = ""
    help_probe_text: str = ""
    prepared_machine_notes: tuple[str, ...] = field(default_factory=tuple)
    safety_notes: tuple[str, ...] = field(default_factory=tuple)
    documentation_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class OptionalSolverHealthSummaryViewModel:
    """Aggregate summary for visible panel stacks."""

    total_stacks: int
    counts_by_health_state: dict[str, int]
    missing_count: int
    partial_count: int
    discovered_count: int
    open_issue_count: int
    validation_warning_count: int


@dataclass(frozen=True, slots=True)
class OptionalSolverHealthPanelViewModel:
    """Complete GUI-ready optional solver health panel view-model."""

    summary: OptionalSolverHealthSummaryViewModel
    cards: tuple[OptionalSolverStackCardViewModel, ...]
    details: OptionalSolverStackDetailsViewModel | None
    diagnostics: tuple[OptionalSolverDiagnosticRowViewModel, ...]
    guidance: tuple[OptionalSolverGuidanceRowViewModel, ...]
    validation_history: tuple[OptionalSolverValidationHistoryRowViewModel, ...]
    actions: tuple[OptionalSolverHealthPanelActionState, ...]
    selected_stack_id: str = ""
    filter_text: str = ""
    health_state_filters: tuple[str, ...] = field(default_factory=tuple)


def build_optional_solver_stack_card_viewmodel(
    manifest: OptionalSolverManifest,
    discovery: OptionalSolverStackDiscovery | None = None,
    *,
    selected: bool = False,
) -> OptionalSolverStackCardViewModel:
    """Build a card view-model for one manifest and optional discovery stack."""

    health_state = (
        discovery.health_state.value
        if discovery is not None
        else OptionalSolverHealthState.UNKNOWN.value
    )
    return OptionalSolverStackCardViewModel(
        stack_id=manifest.stack_id,
        display_name=manifest.display_name,
        related_issue=manifest.related_issue,
        issue_reference=_issue_reference(manifest.related_issue),
        health_state=health_state,
        support_status=manifest.support_status.value,
        short_status_text=_short_status_text(health_state),
        missing_requirements_count=_missing_requirement_count(discovery),
        diagnostics_count=len(discovery.diagnostics) if discovery is not None else 0,
        has_non_bundled_disclaimer=bool(manifest.non_bundled_disclaimer),
        selected=selected,
    )


def build_optional_solver_health_panel_viewmodel(
    *,
    manifests: Sequence[OptionalSolverManifest] | None = None,
    discovery_reports: (
        OptionalSolverDiscoveryReport
        | OptionalSolverStackDiscovery
        | Sequence[OptionalSolverDiscoveryReport | OptionalSolverStackDiscovery]
        | None
    ) = None,
    validation_history: Sequence[
        OptionalSolverValidationHistoryRowViewModel | Mapping[str, object]
    ]
    | None = None,
    selected_stack_id: str | None = None,
    filter_text: str = "",
    health_state_filters: Sequence[str] | None = None,
) -> OptionalSolverHealthPanelViewModel:
    """Build a deterministic GUI-ready health panel view-model.

    The builder uses only supplied data. When discovery reports are absent it
    renders manifest stacks as ``unknown`` instead of performing discovery.
    """

    active_manifests = (
        builtin_optional_solver_manifests() if manifests is None else tuple(manifests)
    )
    discovery_by_stack = _discovery_by_stack(discovery_reports)
    active_filter_text = filter_text.strip().lower()
    active_health_filters = tuple(
        _health_state_value(item) for item in (health_state_filters or ())
    )

    cards = tuple(
        build_optional_solver_stack_card_viewmodel(
            manifest,
            discovery_by_stack.get(manifest.stack_id),
            selected=manifest.stack_id == (selected_stack_id or ""),
        )
        for manifest in sorted(active_manifests, key=lambda item: item.stack_id)
    )
    visible_cards = tuple(
        card
        for card in cards
        if _matches_filter(card, active_filter_text, active_health_filters)
    )
    selected_id = _selected_stack_id(visible_cards, selected_stack_id)
    visible_cards = tuple(
        _replace_card_selection(card, card.stack_id == selected_id)
        for card in visible_cards
    )
    selected_manifest = next(
        (manifest for manifest in active_manifests if manifest.stack_id == selected_id),
        None,
    )
    selected_discovery = discovery_by_stack.get(selected_id)
    details = (
        _details_viewmodel(selected_manifest, selected_discovery)
        if selected_manifest is not None
        else None
    )
    diagnostics = _diagnostic_rows(visible_cards, discovery_by_stack)
    guidance = _guidance_rows(selected_manifest)
    history_rows = _validation_history_rows(validation_history)
    return OptionalSolverHealthPanelViewModel(
        summary=_summary_viewmodel(visible_cards, diagnostics),
        cards=visible_cards,
        details=details,
        diagnostics=diagnostics,
        guidance=guidance,
        validation_history=history_rows,
        actions=_action_states(),
        selected_stack_id=selected_id,
        filter_text=filter_text,
        health_state_filters=active_health_filters,
    )


def summarize_optional_solver_health_panel(
    panel: OptionalSolverHealthPanelViewModel,
) -> OptionalSolverHealthSummaryViewModel:
    """Return the summary block from a health panel view-model."""

    return panel.summary


def explain_optional_solver_health_panel(
    panel: OptionalSolverHealthPanelViewModel,
) -> str:
    """Return a concise human-readable panel summary."""

    return (
        f"Optional solver health panel prepared {panel.summary.total_stacks} "
        f"visible stacks: missing={panel.summary.missing_count}, "
        f"partial={panel.summary.partial_count}, "
        f"discovered={panel.summary.discovered_count}. The view-model is "
        "display-only and does not run discovery, solvers, installers, or issue "
        "closure actions."
    )


def _discovery_by_stack(
    reports: (
        OptionalSolverDiscoveryReport
        | OptionalSolverStackDiscovery
        | Sequence[OptionalSolverDiscoveryReport | OptionalSolverStackDiscovery]
        | None
    ),
) -> dict[str, OptionalSolverStackDiscovery]:
    if reports is None:
        return {}
    items: Sequence[OptionalSolverDiscoveryReport | OptionalSolverStackDiscovery]
    if isinstance(reports, (OptionalSolverDiscoveryReport, OptionalSolverStackDiscovery)):
        items = (reports,)
    else:
        items = tuple(reports)
    stacks: dict[str, OptionalSolverStackDiscovery] = {}
    for item in items:
        if isinstance(item, OptionalSolverStackDiscovery):
            stacks[item.stack_id] = item
        else:
            for stack in item.stacks:
                stacks[stack.stack_id] = stack
    return stacks


def _matches_filter(
    card: OptionalSolverStackCardViewModel,
    filter_text: str,
    health_state_filters: tuple[str, ...],
) -> bool:
    if health_state_filters and card.health_state not in health_state_filters:
        return False
    if not filter_text:
        return True
    haystack = " ".join(
        (
            card.stack_id,
            card.display_name,
            card.issue_reference,
            card.health_state,
            card.support_status,
        )
    ).lower()
    return filter_text in haystack


def _selected_stack_id(
    cards: tuple[OptionalSolverStackCardViewModel, ...],
    selected_stack_id: str | None,
) -> str:
    if selected_stack_id and any(card.stack_id == selected_stack_id for card in cards):
        return selected_stack_id
    return cards[0].stack_id if cards else ""


def _replace_card_selection(
    card: OptionalSolverStackCardViewModel,
    selected: bool,
) -> OptionalSolverStackCardViewModel:
    return OptionalSolverStackCardViewModel(
        stack_id=card.stack_id,
        display_name=card.display_name,
        related_issue=card.related_issue,
        issue_reference=card.issue_reference,
        health_state=card.health_state,
        support_status=card.support_status,
        short_status_text=card.short_status_text,
        missing_requirements_count=card.missing_requirements_count,
        diagnostics_count=card.diagnostics_count,
        has_non_bundled_disclaimer=card.has_non_bundled_disclaimer,
        selected=selected,
    )


def _summary_viewmodel(
    cards: tuple[OptionalSolverStackCardViewModel, ...],
    diagnostics: tuple[OptionalSolverDiagnosticRowViewModel, ...],
) -> OptionalSolverHealthSummaryViewModel:
    counts: dict[str, int] = {}
    for card in cards:
        counts[card.health_state] = counts.get(card.health_state, 0) + 1
    warning_count = sum(
        1
        for diagnostic in diagnostics
        if diagnostic.severity in {"warning", "error", "blocker"}
    )
    return OptionalSolverHealthSummaryViewModel(
        total_stacks=len(cards),
        counts_by_health_state=dict(sorted(counts.items())),
        missing_count=counts.get(OptionalSolverHealthState.MISSING.value, 0),
        partial_count=counts.get(
            OptionalSolverHealthState.PARTIALLY_INSTALLED.value,
            0,
        ),
        discovered_count=counts.get(OptionalSolverHealthState.DISCOVERED.value, 0),
        open_issue_count=sum(1 for card in cards if card.related_issue is not None),
        validation_warning_count=warning_count,
    )


def _details_viewmodel(
    manifest: OptionalSolverManifest,
    discovery: OptionalSolverStackDiscovery | None,
) -> OptionalSolverStackDetailsViewModel:
    exe_by_id = {
        item.identifier: item for item in discovery.executables
    } if discovery is not None else {}
    pkg_by_id = {
        item.identifier: item for item in discovery.python_packages
    } if discovery is not None else {}
    env_by_name = {
        item.name: item for item in discovery.environment_hints
    } if discovery is not None else {}
    return OptionalSolverStackDetailsViewModel(
        stack_id=manifest.stack_id,
        display_name=manifest.display_name,
        capabilities=tuple(
            f"{item.capability_id}: {item.description}".rstrip(": ")
            for item in manifest.capabilities
        ),
        executable_requirements=tuple(
            _executable_row(item, exe_by_id.get(item.identifier))
            for item in manifest.executable_requirements
        ),
        python_package_requirements=tuple(
            _python_package_row(item, pkg_by_id.get(item.identifier))
            for item in manifest.python_package_requirements
        ),
        environment_hints=tuple(
            _environment_row(name, env_by_name.get(name))
            for name in manifest.environment_variable_hints
        ),
        version_probe_text=_probe_text(manifest.version_probe),
        help_probe_text=_probe_text(manifest.help_probe),
        prepared_machine_notes=manifest.prepared_machine_notes,
        safety_notes=manifest.safety_notes,
        documentation_refs=manifest.documentation_refs,
    )


def _executable_row(
    requirement: OptionalSolverRequirement,
    discovery: OptionalSolverExecutableDiscovery | None,
) -> OptionalSolverRequirementRowViewModel:
    if discovery is None:
        return _requirement_row("executable", requirement, None, "not checked")
    detail = _redacted_executable_detail(discovery)
    status = "found" if discovery.found else "missing"
    return _requirement_row(
        "executable",
        requirement,
        discovery.found,
        status,
        detail,
        discovery.notes or requirement.notes,
    )


def _python_package_row(
    requirement: OptionalSolverRequirement,
    discovery: OptionalSolverPythonPackageDiscovery | None,
) -> OptionalSolverRequirementRowViewModel:
    if discovery is None:
        return _requirement_row("python_package", requirement, None, "not checked")
    detail = f"version {discovery.version}" if discovery.version else ""
    status = "found" if discovery.found else "missing"
    return _requirement_row(
        "python_package",
        requirement,
        discovery.found,
        status,
        detail,
        discovery.notes or requirement.notes,
    )


def _environment_row(
    name: str,
    discovery: OptionalSolverEnvironmentHintDiscovery | None,
) -> OptionalSolverRequirementRowViewModel:
    if discovery is None:
        return OptionalSolverRequirementRowViewModel(
            requirement_type="environment_hint",
            identifier=name,
            display_name=name,
            required=False,
            found=None,
            status_text="not checked",
        )
    detail = "<redacted>" if discovery.present else ""
    return OptionalSolverRequirementRowViewModel(
        requirement_type="environment_hint",
        identifier=name,
        display_name=name,
        required=False,
        found=discovery.present,
        status_text="present" if discovery.present else "missing",
        detail_text=detail,
    )


def _requirement_row(
    requirement_type: str,
    requirement: OptionalSolverRequirement,
    found: bool | None,
    status_text: str,
    detail_text: str = "",
    notes: tuple[str, ...] = (),
) -> OptionalSolverRequirementRowViewModel:
    return OptionalSolverRequirementRowViewModel(
        requirement_type=requirement_type,
        identifier=requirement.identifier,
        display_name=requirement.display_name or requirement.identifier,
        required=requirement.required,
        found=found,
        status_text=status_text,
        detail_text=detail_text,
        notes=notes,
    )


def _redacted_executable_detail(discovery: OptionalSolverExecutableDiscovery) -> str:
    if not discovery.found:
        return ""
    if discovery.redacted_path:
        return discovery.redacted_path
    if discovery.path:
        return "<redacted>"
    return ""


def _diagnostic_rows(
    cards: tuple[OptionalSolverStackCardViewModel, ...],
    discovery_by_stack: Mapping[str, OptionalSolverStackDiscovery],
) -> tuple[OptionalSolverDiagnosticRowViewModel, ...]:
    visible_ids = {card.stack_id for card in cards}
    rows: list[OptionalSolverDiagnosticRowViewModel] = []
    for stack_id in sorted(visible_ids):
        stack = discovery_by_stack.get(stack_id)
        if stack is None:
            continue
        rows.extend(_diagnostic_row(stack_id, item) for item in stack.diagnostics)
    return tuple(rows)


def _diagnostic_row(
    stack_id: str,
    diagnostic: OptionalSolverDiscoveryDiagnostic,
) -> OptionalSolverDiagnosticRowViewModel:
    return OptionalSolverDiagnosticRowViewModel(
        stack_id=stack_id,
        severity=diagnostic.severity.value,
        code=diagnostic.code,
        message=diagnostic.message,
        path=diagnostic.path,
        suggested_fix=diagnostic.suggested_fix,
        redaction_notice=_redaction_notice(diagnostic),
    )


def _guidance_rows(
    manifest: OptionalSolverManifest | None,
) -> tuple[OptionalSolverGuidanceRowViewModel, ...]:
    rows = [
        OptionalSolverGuidanceRowViewModel(
            category="non_bundled_solver",
            text=(
                "External solvers and optional science packages are not bundled "
                "by OpenSolver Workbench."
            ),
        ),
        OptionalSolverGuidanceRowViewModel(
            category="validation_gate",
            text=(
                "Use an explicit OSW-VALID prepared-machine gate for active "
                "smoke validation."
            ),
        ),
        OptionalSolverGuidanceRowViewModel(
            category="issue_closure",
            text=(
                "Issue closure remains unavailable from the panel and requires "
                "a separate closure-review gate."
            ),
            severity="warning",
        ),
    ]
    if manifest is not None:
        rows.extend(
            OptionalSolverGuidanceRowViewModel(
                category="prepared_machine",
                text=note,
            )
            for note in manifest.prepared_machine_notes
        )
        rows.extend(
            OptionalSolverGuidanceRowViewModel(
                category="safety",
                text=note,
            )
            for note in manifest.safety_notes
        )
    return tuple(rows)


def _validation_history_rows(
    rows: Sequence[OptionalSolverValidationHistoryRowViewModel | Mapping[str, object]]
    | None,
) -> tuple[OptionalSolverValidationHistoryRowViewModel, ...]:
    if not rows:
        return (
            OptionalSolverValidationHistoryRowViewModel(
                source="not_supplied",
                status="not_supplied",
                summary="No validation history supplied to the view-model.",
                is_pass_evidence=False,
            ),
        )
    return tuple(_validation_history_row(row) for row in rows)


def _validation_history_row(
    row: OptionalSolverValidationHistoryRowViewModel | Mapping[str, object],
) -> OptionalSolverValidationHistoryRowViewModel:
    if isinstance(row, OptionalSolverValidationHistoryRowViewModel):
        return row
    if is_dataclass(row) and not isinstance(row, type):
        return _validation_history_row(asdict(row))
    status = str(row.get("status") or row.get("classification") or "")
    return OptionalSolverValidationHistoryRowViewModel(
        source=str(row.get("source", "")),
        status=status,
        summary=str(row.get("summary", "")),
        timestamp=str(row.get("timestamp", "")),
        related_issue=_optional_int(row.get("related_issue")),
        is_pass_evidence=status == "passed-installed",
        closure_review_required=True,
    )


def _action_states() -> tuple[OptionalSolverHealthPanelActionState, ...]:
    return (
        OptionalSolverHealthPanelActionState(
            action=OptionalSolverHealthPanelAction.REFRESH_PASSIVE_DISCOVERY,
            label="Refresh passive discovery",
            enabled=True,
            available=True,
            reason="Future GUI may request a passive refresh explicitly.",
        ),
        OptionalSolverHealthPanelActionState(
            action=OptionalSolverHealthPanelAction.RUN_VALIDATION_GATE,
            label="Run validation",
            enabled=False,
            available=False,
            reason="Active validation requires an explicit OSW-VALID gate.",
        ),
        OptionalSolverHealthPanelActionState(
            action=OptionalSolverHealthPanelAction.INSTALL_SOLVER,
            label="Install solver",
            enabled=False,
            available=False,
            reason="Solver installation is out of scope.",
        ),
        OptionalSolverHealthPanelActionState(
            action=OptionalSolverHealthPanelAction.CLOSE_ISSUE,
            label="Close issue",
            enabled=False,
            available=False,
            reason="Issue closure requires a separate closure-review gate.",
        ),
        OptionalSolverHealthPanelActionState(
            action=OptionalSolverHealthPanelAction.COPY_SUMMARY,
            label="Copy summary",
            enabled=False,
            available=True,
            reason="Future placeholder only; this view-model does not use a clipboard.",
        ),
        OptionalSolverHealthPanelActionState(
            action=OptionalSolverHealthPanelAction.OPEN_DOCS,
            label="Open docs",
            enabled=False,
            available=True,
            reason="Future placeholder only; this view-model does not open browsers.",
        ),
    )


def _missing_requirement_count(
    discovery: OptionalSolverStackDiscovery | None,
) -> int:
    if discovery is None:
        return 0
    requirements = (
        *(item for item in discovery.executables if item.required),
        *(item for item in discovery.python_packages if item.required),
    )
    return sum(1 for item in requirements if not item.found)


def _short_status_text(health_state: str) -> str:
    if health_state == OptionalSolverHealthState.MISSING.value:
        return "Missing required optional components"
    if health_state == OptionalSolverHealthState.PARTIALLY_INSTALLED.value:
        return "Partially installed optional stack"
    if health_state == OptionalSolverHealthState.DISCOVERED.value:
        return "Discovered by passive checks"
    if health_state == OptionalSolverHealthState.UNSUPPORTED_PLATFORM.value:
        return "Unsupported on this platform"
    if health_state == OptionalSolverHealthState.BLOCKED_NO_SAFE_CASE.value:
        return "Blocked until a safe validation case exists"
    if health_state in {
        OptionalSolverHealthState.SMOKE_PASSED.value,
        OptionalSolverHealthState.SMOKE_FAILED.value,
    }:
        return "Active validation state from explicit validation evidence"
    return "No passive discovery report supplied"


def _redaction_notice(diagnostic: OptionalSolverDiscoveryDiagnostic) -> str:
    if "REDACTED" in diagnostic.code or "<redacted" in diagnostic.message.lower():
        return "Local paths or environment values were redacted for display."
    return ""


def _health_state_value(value: object) -> str:
    if isinstance(value, OptionalSolverHealthState):
        return value.value
    return str(value)


def _probe_text(probe: object) -> str:
    if probe is None:
        return ""
    command = " ".join(getattr(probe, "command", ()) or ())
    name = str(getattr(probe, "name", ""))
    description = str(getattr(probe, "description", ""))
    parts = [part for part in (name, command, description, "not executed") if part]
    return " - ".join(parts)


def _issue_reference(issue: int | None) -> str:
    return f"#{issue}" if issue is not None else ""


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
