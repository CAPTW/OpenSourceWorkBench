"""Pure GUI view-model for optional solver plugin manifest load reports.

This module consumes an already-built plugin manifest loader report and turns it
into deterministic display records. It does not load files, parse JSON, import
plugin packages, scan directories, fetch manifests, run discovery, execute
solvers, import Qt/PySide, or install dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, fields
from enum import Enum

from .plugin_manifest_loader import (
    OptionalSolverLoadedManifest,
    OptionalSolverManifestConflict,
    OptionalSolverManifestSource,
    OptionalSolverManifestTrustLabel,
    OptionalSolverPluginManifestLoadDiagnostic,
    OptionalSolverPluginManifestLoadReport,
    OptionalSolverRejectedManifest,
)

NOT_VALIDATION_EVIDENCE_TEXT = (
    "Plugin manifest preview is not validation evidence."
)
THIRD_PARTY_NOT_TRUSTED_TEXT = (
    "Third-party/plugin manifests are not trusted by default."
)
NO_BUNDLED_SOLVER_TEXT = "External solvers are not bundled."


class OptionalSolverPluginManifestAction(str, Enum):
    """Future action identifiers for plugin manifest GUI preview."""

    CHOOSE_EXPLICIT_JSON_FILES = "choose_explicit_json_files"
    ACTIVATE_MANIFEST = "activate_manifest"
    RUN_DISCOVERY_WITH_PLUGIN_MANIFESTS = "run_discovery_with_plugin_manifests"
    RUN_VALIDATION = "run_validation"
    INSTALL_SOLVER = "install_solver"
    CLOSE_ISSUE = "close_issue"


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestActionState:
    """Display-only state for future plugin manifest GUI actions."""

    action: OptionalSolverPluginManifestAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestSummaryViewModel:
    """Summary header values for a plugin manifest preview."""

    accepted_count: int
    rejected_count: int
    conflict_count: int
    diagnostic_count: int
    visible_accepted_count: int
    visible_rejected_count: int
    visible_conflict_count: int
    visible_diagnostic_count: int
    status_text: str
    not_validation_evidence: bool = True
    third_party_manifests_trusted_by_default: bool = False
    external_solvers_bundled: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestAcceptedRowViewModel:
    """GUI-ready accepted manifest table row."""

    stack_id: str
    display_name: str
    source_type: str
    source_label: str
    source_ref: str
    trust_label: str
    trust_text: str
    related_issue: str
    support_status: str
    capabilities_summary: str
    not_validation_evidence_text: str = NOT_VALIDATION_EVIDENCE_TEXT


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestRejectedRowViewModel:
    """GUI-ready rejected manifest table row."""

    stack_id: str
    source_type: str
    source_label: str
    source_ref: str
    trust_label: str
    rejection_reason: str
    diagnostics: tuple[str, ...]
    suggested_fix: str
    unsafe_claim_indicators: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestConflictRowViewModel:
    """GUI-ready duplicate/conflict table row."""

    stack_id: str
    winning_source_type: str
    winning_trust_label: str
    winning_source_ref: str
    rejected_source_type: str
    rejected_trust_label: str
    rejected_source_ref: str
    message: str
    built_in_wins_text: str
    plugin_override_disabled_text: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestDiagnosticRowViewModel:
    """GUI-ready diagnostic table row."""

    severity: str
    category: str
    code: str
    message: str
    source_ref: str = ""
    stack_id: str = ""
    suggested_fix: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestTrustBadgeViewModel:
    """Source/trust badge shown by the future GUI."""

    source_type: str
    trust_label: str
    label: str
    source_ref: str
    warning_text: str
    is_trusted_builtin: bool = False
    is_third_party: bool = False
    is_invalid: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestGuiViewModel:
    """Complete pure GUI view-model for plugin manifest preview."""

    summary: OptionalSolverPluginManifestSummaryViewModel
    accepted_rows: tuple[OptionalSolverPluginManifestAcceptedRowViewModel, ...]
    rejected_rows: tuple[OptionalSolverPluginManifestRejectedRowViewModel, ...]
    conflict_rows: tuple[OptionalSolverPluginManifestConflictRowViewModel, ...]
    diagnostic_rows: tuple[OptionalSolverPluginManifestDiagnosticRowViewModel, ...]
    trust_badges: tuple[OptionalSolverPluginManifestTrustBadgeViewModel, ...]
    actions: tuple[OptionalSolverPluginManifestActionState, ...]
    guidance_text: tuple[str, ...]
    safety_text: tuple[str, ...]
    selected_stack_id: str = ""
    filter_text: str = ""
    trust_filters: tuple[str, ...] = field(default_factory=tuple)
    source_filters: tuple[str, ...] = field(default_factory=tuple)
    selected_stack_present: bool = False
    not_validation_evidence: bool = True


def build_optional_solver_plugin_manifest_gui_viewmodel(
    report: OptionalSolverPluginManifestLoadReport,
    *,
    selected_stack_id: str = "",
    filter_text: str = "",
    trust_filters: Sequence[str] | None = None,
    source_filters: Sequence[str] | None = None,
) -> OptionalSolverPluginManifestGuiViewModel:
    """Build deterministic display data from a plugin manifest load report."""

    trust_filter_values = _normalized_filter_values(trust_filters)
    source_filter_values = _normalized_filter_values(source_filters)
    text_filter = filter_text.strip().lower()
    accepted_all = tuple(
        _accepted_row(item) for item in sorted(report.accepted_manifests, key=_loaded_key)
    )
    rejected_all = tuple(
        _rejected_row(item) for item in sorted(report.rejected_manifests, key=_rejected_key)
    )
    conflict_all = tuple(
        _conflict_row(item) for item in sorted(report.conflicts, key=_conflict_key)
    )
    diagnostic_all = tuple(
        _diagnostic_row(item) for item in sorted(report.diagnostics, key=_diagnostic_key)
    )

    accepted_rows = tuple(
        row
        for row in accepted_all
        if _row_matches_filters(row, text_filter, trust_filter_values, source_filter_values)
    )
    rejected_rows = tuple(
        row
        for row in rejected_all
        if _row_matches_filters(row, text_filter, trust_filter_values, source_filter_values)
    )
    conflict_rows = tuple(
        row
        for row in conflict_all
        if _conflict_matches_filters(
            row,
            text_filter,
            trust_filter_values,
            source_filter_values,
        )
    )
    diagnostic_rows = tuple(
        row
        for row in diagnostic_all
        if _diagnostic_matches_filters(row, text_filter)
    )
    trust_badges = _trust_badges(report)
    selected_present = bool(
        selected_stack_id
        and selected_stack_id
        in {
            row.stack_id
            for row in (
                *accepted_all,
                *rejected_all,
                *conflict_all,
                *diagnostic_all,
            )
            if row.stack_id
        }
    )
    summary = OptionalSolverPluginManifestSummaryViewModel(
        accepted_count=len(report.accepted_manifests),
        rejected_count=len(report.rejected_manifests),
        conflict_count=len(report.conflicts),
        diagnostic_count=len(report.diagnostics),
        visible_accepted_count=len(accepted_rows),
        visible_rejected_count=len(rejected_rows),
        visible_conflict_count=len(conflict_rows),
        visible_diagnostic_count=len(diagnostic_rows),
        status_text=_summary_status_text(report),
    )
    return OptionalSolverPluginManifestGuiViewModel(
        summary=summary,
        accepted_rows=accepted_rows,
        rejected_rows=rejected_rows,
        conflict_rows=conflict_rows,
        diagnostic_rows=diagnostic_rows,
        trust_badges=trust_badges,
        actions=_action_states(),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
        selected_stack_id=selected_stack_id,
        filter_text=filter_text,
        trust_filters=trust_filter_values,
        source_filters=source_filter_values,
        selected_stack_present=selected_present,
        not_validation_evidence=True,
    )


def summarize_optional_solver_plugin_manifest_gui_viewmodel(
    view_model: OptionalSolverPluginManifestGuiViewModel,
) -> str:
    """Return a concise GUI preview summary."""

    return (
        "Optional solver plugin manifest GUI preview view-model: "
        f"{view_model.summary.accepted_count} accepted, "
        f"{view_model.summary.rejected_count} rejected, "
        f"{view_model.summary.conflict_count} conflicts, "
        f"{view_model.summary.diagnostic_count} diagnostics. "
        "Plugin manifest preview is not validation evidence."
    )


def explain_optional_solver_plugin_manifest_gui_viewmodel(
    view_model: OptionalSolverPluginManifestGuiViewModel,
) -> str:
    """Explain the safety boundary of the GUI preview view-model."""

    disabled_actions = ", ".join(
        action.action.value for action in view_model.actions if not action.enabled
    )
    return (
        summarize_optional_solver_plugin_manifest_gui_viewmodel(view_model)
        + " The view-model consumes loader reports only; it does not load files, "
        "parse JSON, import plugin packages, scan directories, fetch network "
        "manifests, run discovery, execute solvers, install dependencies, or "
        f"close issues. Disabled actions: {disabled_actions}."
    )


def _accepted_row(
    loaded: OptionalSolverLoadedManifest,
) -> OptionalSolverPluginManifestAcceptedRowViewModel:
    issue = (
        f"#{loaded.manifest.related_issue}"
        if loaded.manifest.related_issue is not None
        else "none"
    )
    capabilities = ", ".join(
        capability.capability_id for capability in loaded.manifest.capabilities
    )
    return OptionalSolverPluginManifestAcceptedRowViewModel(
        stack_id=loaded.stack_id,
        display_name=loaded.manifest.display_name,
        source_type=loaded.source.source_type.value,
        source_label=loaded.source.label,
        source_ref=loaded.source.reference,
        trust_label=loaded.source.trust_label.value,
        trust_text=_trust_warning_text(loaded.source),
        related_issue=issue,
        support_status=loaded.manifest.support_status.value,
        capabilities_summary=capabilities or "none",
    )


def _rejected_row(
    rejected: OptionalSolverRejectedManifest,
) -> OptionalSolverPluginManifestRejectedRowViewModel:
    diagnostics = tuple(_diagnostic_summary(item) for item in rejected.diagnostics)
    return OptionalSolverPluginManifestRejectedRowViewModel(
        stack_id=rejected.stack_id,
        source_type=rejected.source.source_type.value,
        source_label=rejected.source.label,
        source_ref=rejected.source.reference,
        trust_label=rejected.source.trust_label.value,
        rejection_reason=_first_diagnostic_message(rejected.diagnostics),
        diagnostics=diagnostics,
        suggested_fix=_first_suggested_fix(rejected.diagnostics),
        unsafe_claim_indicators=_unsafe_claim_indicators(rejected.diagnostics),
    )


def _conflict_row(
    conflict: OptionalSolverManifestConflict,
) -> OptionalSolverPluginManifestConflictRowViewModel:
    return OptionalSolverPluginManifestConflictRowViewModel(
        stack_id=conflict.stack_id,
        winning_source_type=conflict.winning_source.source_type.value,
        winning_trust_label=conflict.winning_source.trust_label.value,
        winning_source_ref=conflict.winning_source.reference,
        rejected_source_type=conflict.rejected_source.source_type.value,
        rejected_trust_label=conflict.rejected_source.trust_label.value,
        rejected_source_ref=conflict.rejected_source.reference,
        message=conflict.message,
        built_in_wins_text="Built-in manifests win by default.",
        plugin_override_disabled_text="Plugin override is disabled by default.",
    )


def _diagnostic_row(
    diagnostic: OptionalSolverPluginManifestLoadDiagnostic,
) -> OptionalSolverPluginManifestDiagnosticRowViewModel:
    return OptionalSolverPluginManifestDiagnosticRowViewModel(
        severity=diagnostic.severity.value,
        category=diagnostic.category.value,
        code=diagnostic.code,
        message=diagnostic.message,
        source_ref=diagnostic.source_ref,
        stack_id=diagnostic.stack_id,
        suggested_fix=diagnostic.suggested_fix,
    )


def _trust_badges(
    report: OptionalSolverPluginManifestLoadReport,
) -> tuple[OptionalSolverPluginManifestTrustBadgeViewModel, ...]:
    sources: dict[tuple[str, str, str], OptionalSolverManifestSource] = {}
    for loaded in report.accepted_manifests:
        _add_source(sources, loaded.source)
    for rejected in report.rejected_manifests:
        _add_source(sources, rejected.source)
    for conflict in report.conflicts:
        _add_source(sources, conflict.winning_source)
        _add_source(sources, conflict.rejected_source)
    return tuple(
        _trust_badge(source)
        for source in sorted(
            sources.values(),
            key=lambda item: (
                item.source_type.value,
                item.trust_label.value,
                item.reference,
                item.label,
            ),
        )
    )


def _trust_badge(
    source: OptionalSolverManifestSource,
) -> OptionalSolverPluginManifestTrustBadgeViewModel:
    return OptionalSolverPluginManifestTrustBadgeViewModel(
        source_type=source.source_type.value,
        trust_label=source.trust_label.value,
        label=source.label,
        source_ref=source.reference,
        warning_text=_trust_warning_text(source),
        is_trusted_builtin=(
            source.trust_label == OptionalSolverManifestTrustLabel.TRUSTED_BUILTIN
        ),
        is_third_party=(
            source.trust_label == OptionalSolverManifestTrustLabel.THIRD_PARTY_PLUGIN
        ),
        is_invalid=source.trust_label == OptionalSolverManifestTrustLabel.INVALID,
    )


def _add_source(
    sources: dict[tuple[str, str, str], OptionalSolverManifestSource],
    source: OptionalSolverManifestSource,
) -> None:
    sources[(source.source_type.value, source.trust_label.value, source.reference)] = (
        source
    )


def _action_states() -> tuple[OptionalSolverPluginManifestActionState, ...]:
    return (
        OptionalSolverPluginManifestActionState(
            action=OptionalSolverPluginManifestAction.CHOOSE_EXPLICIT_JSON_FILES,
            label="Choose explicit JSON files",
            enabled=False,
            available=True,
            reason=(
                "Future display-only action; file dialogs are not implemented in "
                "this pure view-model gate."
            ),
            future_action=True,
        ),
        OptionalSolverPluginManifestActionState(
            action=OptionalSolverPluginManifestAction.ACTIVATE_MANIFEST,
            label="Activate manifest",
            enabled=False,
            available=False,
            reason="Plugin manifest activation requires a separate future gate.",
        ),
        OptionalSolverPluginManifestActionState(
            action=OptionalSolverPluginManifestAction.RUN_DISCOVERY_WITH_PLUGIN_MANIFESTS,
            label="Run discovery with plugin manifests",
            enabled=False,
            available=False,
            reason=(
                "Discovery with plugin manifests is unavailable until an explicit "
                "activation model exists."
            ),
        ),
        OptionalSolverPluginManifestActionState(
            action=OptionalSolverPluginManifestAction.RUN_VALIDATION,
            label="Run validation",
            enabled=False,
            available=False,
            reason="Validation requires a separate OSW-VALID gate.",
        ),
        OptionalSolverPluginManifestActionState(
            action=OptionalSolverPluginManifestAction.INSTALL_SOLVER,
            label="Install solver",
            enabled=False,
            available=False,
            reason="Solver installation is unavailable.",
        ),
        OptionalSolverPluginManifestActionState(
            action=OptionalSolverPluginManifestAction.CLOSE_ISSUE,
            label="Close issue",
            enabled=False,
            available=False,
            reason="Issue closure requires a separate validation and closure gate.",
        ),
    )


def _guidance_text() -> tuple[str, ...]:
    return (
        "Plugin preview is data-only.",
        NOT_VALIDATION_EVIDENCE_TEXT,
        THIRD_PARTY_NOT_TRUSTED_TEXT,
        NO_BUNDLED_SOLVER_TEXT,
        "Issue closure requires separate validation and closure gates.",
    )


def _safety_text() -> tuple[str, ...]:
    return (
        "No plugin code execution.",
        "No plugin package import.",
        "No directory scanning.",
        "No network fetch.",
        "No solver execution.",
        "No dependency installation.",
        "No install actions.",
        "No issue closure action.",
    )


def _trust_warning_text(source: OptionalSolverManifestSource) -> str:
    label = source.trust_label
    if label == OptionalSolverManifestTrustLabel.TRUSTED_BUILTIN:
        return "Built-in trusted source; trust label is not certification."
    if label == OptionalSolverManifestTrustLabel.REVIEWED_PROJECT:
        return "Project-reviewed source; review status is not validation evidence."
    if label == OptionalSolverManifestTrustLabel.ORGANIZATION_MANAGED:
        return "Organization-managed source; trust label is not certification."
    if label == OptionalSolverManifestTrustLabel.THIRD_PARTY_PLUGIN:
        return THIRD_PARTY_NOT_TRUSTED_TEXT
    if label == OptionalSolverManifestTrustLabel.INVALID:
        return "Invalid or blocked source; do not activate."
    return "User-provided or untrusted source; review before any future activation."


def _summary_status_text(report: OptionalSolverPluginManifestLoadReport) -> str:
    return (
        "Plugin manifest preview report: "
        f"{len(report.accepted_manifests)} accepted, "
        f"{len(report.rejected_manifests)} rejected, "
        f"{len(report.conflicts)} conflicts, "
        f"{len(report.diagnostics)} diagnostics. "
        "This preview is not validation evidence."
    )


def _diagnostic_summary(
    diagnostic: OptionalSolverPluginManifestLoadDiagnostic,
) -> str:
    return (
        f"{diagnostic.severity.value}/{diagnostic.category.value}: "
        f"{diagnostic.code}: {diagnostic.message}"
    )


def _first_diagnostic_message(
    diagnostics: Sequence[OptionalSolverPluginManifestLoadDiagnostic],
) -> str:
    for diagnostic in diagnostics:
        if diagnostic.message:
            return diagnostic.message
    return "Manifest was rejected by loader policy."


def _first_suggested_fix(
    diagnostics: Sequence[OptionalSolverPluginManifestLoadDiagnostic],
) -> str:
    for diagnostic in diagnostics:
        if diagnostic.suggested_fix:
            return diagnostic.suggested_fix
    return ""


def _unsafe_claim_indicators(
    diagnostics: Sequence[OptionalSolverPluginManifestLoadDiagnostic],
) -> tuple[str, ...]:
    code_map = {
        "OSPL_INSTALLER_COMMAND_PRESENT": "installer command wording",
        "OSPL_EXECUTABLE_CODE_REFERENCE_PRESENT": "executable code reference",
        "OSPL_BUNDLED_SOLVER_CLAIM": "external-solver bundling claim",
        "OSPL_CERTIFICATION_CLAIM": "certification claim",
    }
    return tuple(
        value
        for diagnostic in diagnostics
        for code, value in code_map.items()
        if diagnostic.code == code
    )


def _normalized_filter_values(values: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(str(item).strip().lower() for item in values or () if str(item).strip())


def _row_matches_filters(
    row: OptionalSolverPluginManifestAcceptedRowViewModel
    | OptionalSolverPluginManifestRejectedRowViewModel,
    text_filter: str,
    trust_filters: tuple[str, ...],
    source_filters: tuple[str, ...],
) -> bool:
    if trust_filters and row.trust_label.lower() not in trust_filters:
        return False
    if source_filters and row.source_type.lower() not in source_filters:
        return False
    if not text_filter:
        return True
    searchable = _dataclass_search_text(row)
    return text_filter in searchable


def _conflict_matches_filters(
    row: OptionalSolverPluginManifestConflictRowViewModel,
    text_filter: str,
    trust_filters: tuple[str, ...],
    source_filters: tuple[str, ...],
) -> bool:
    if trust_filters and not {
        row.winning_trust_label.lower(),
        row.rejected_trust_label.lower(),
    }.intersection(trust_filters):
        return False
    if source_filters and not {
        row.winning_source_type.lower(),
        row.rejected_source_type.lower(),
    }.intersection(source_filters):
        return False
    if not text_filter:
        return True
    searchable = _dataclass_search_text(row)
    return text_filter in searchable


def _diagnostic_matches_filters(
    row: OptionalSolverPluginManifestDiagnosticRowViewModel,
    text_filter: str,
) -> bool:
    if not text_filter:
        return True
    searchable = _dataclass_search_text(row)
    return text_filter in searchable


def _loaded_key(loaded: OptionalSolverLoadedManifest) -> tuple[str, str, str]:
    return (loaded.stack_id, loaded.source.source_type.value, loaded.source.reference)


def _rejected_key(rejected: OptionalSolverRejectedManifest) -> tuple[str, str, str]:
    return (rejected.stack_id, rejected.source.source_type.value, rejected.source.reference)


def _conflict_key(conflict: OptionalSolverManifestConflict) -> tuple[str, str]:
    return (conflict.stack_id, conflict.rejected_source.reference)


def _diagnostic_key(
    diagnostic: OptionalSolverPluginManifestLoadDiagnostic,
) -> tuple[str, str, str, str]:
    return (
        diagnostic.stack_id,
        diagnostic.source_ref,
        diagnostic.severity.value,
        diagnostic.code,
    )


def _dataclass_search_text(value: object) -> str:
    return " ".join(str(getattr(value, item.name)) for item in fields(value)).lower()


__all__ = [
    "OptionalSolverPluginManifestAcceptedRowViewModel",
    "OptionalSolverPluginManifestAction",
    "OptionalSolverPluginManifestActionState",
    "OptionalSolverPluginManifestConflictRowViewModel",
    "OptionalSolverPluginManifestDiagnosticRowViewModel",
    "OptionalSolverPluginManifestGuiViewModel",
    "OptionalSolverPluginManifestRejectedRowViewModel",
    "OptionalSolverPluginManifestSummaryViewModel",
    "OptionalSolverPluginManifestTrustBadgeViewModel",
    "build_optional_solver_plugin_manifest_gui_viewmodel",
    "explain_optional_solver_plugin_manifest_gui_viewmodel",
    "summarize_optional_solver_plugin_manifest_gui_viewmodel",
]
