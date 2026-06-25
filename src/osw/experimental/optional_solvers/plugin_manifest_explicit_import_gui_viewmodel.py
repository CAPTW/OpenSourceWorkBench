"""Pure view-model for the explicit plugin manifest JSON import/preview GUI.

This module is the OSW-EXP-076 implementation of the explicit-import GUI
view-model designed in OSW-EXP-075. It is an adapter that turns an
already-built optional solver plugin manifest loader report (or a
caller-supplied import state) into deterministic GUI-ready records for a future
explicit-import surface.

It performs no side effects. It does not open files, read files, parse JSON from
a path, call ``QFileDialog``, import PySide/Qt, import plugin packages, scan
directories, fetch URLs, run discovery, run validation, execute solvers, install
dependencies, mutate issues, or mutate releases. File selection, reading, and
parsing belong to a future runner/implementation gate (OSW-EXP-077); the
caller supplies the loader report or import diagnostics, and this view-model only
transforms supplied data.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from .plugin_manifest_gui_viewmodel import (
    NO_BUNDLED_SOLVER_TEXT,
    NOT_VALIDATION_EVIDENCE_TEXT,
    THIRD_PARTY_NOT_TRUSTED_TEXT,
    OptionalSolverPluginManifestAcceptedRowViewModel,
    OptionalSolverPluginManifestConflictRowViewModel,
    OptionalSolverPluginManifestDiagnosticRowViewModel,
    OptionalSolverPluginManifestRejectedRowViewModel,
    OptionalSolverPluginManifestTrustBadgeViewModel,
    build_optional_solver_plugin_manifest_gui_viewmodel,
)
from .plugin_manifest_loader import (
    OptionalSolverManifestSource,
    OptionalSolverManifestTrustLabel,
    OptionalSolverPluginManifestLoadDiagnostic,
    OptionalSolverPluginManifestLoadReport,
)

# Design-only OSPMG_IMPORT_* diagnostic vocabulary reserved by OSW-EXP-075.
OSPMG_IMPORT_CANCELLED = "OSPMG_IMPORT_CANCELLED"
OSPMG_IMPORT_FILE_MISSING = "OSPMG_IMPORT_FILE_MISSING"
OSPMG_IMPORT_UNREADABLE = "OSPMG_IMPORT_UNREADABLE"
OSPMG_IMPORT_UNSUPPORTED_EXTENSION = "OSPMG_IMPORT_UNSUPPORTED_EXTENSION"
OSPMG_IMPORT_FILE_TOO_LARGE = "OSPMG_IMPORT_FILE_TOO_LARGE"
OSPMG_IMPORT_INVALID_JSON = "OSPMG_IMPORT_INVALID_JSON"
OSPMG_IMPORT_SCHEMA_INVALID = "OSPMG_IMPORT_SCHEMA_INVALID"
OSPMG_IMPORT_CONFLICT = "OSPMG_IMPORT_CONFLICT"
OSPMG_IMPORT_UNTRUSTED_SOURCE = "OSPMG_IMPORT_UNTRUSTED_SOURCE"
OSPMG_IMPORT_PREVIEW_ONLY = "OSPMG_IMPORT_PREVIEW_ONLY"

#: All reserved explicit-import diagnostic codes, in design order.
OSPMG_IMPORT_DIAGNOSTIC_CODES: tuple[str, ...] = (
    OSPMG_IMPORT_CANCELLED,
    OSPMG_IMPORT_FILE_MISSING,
    OSPMG_IMPORT_UNREADABLE,
    OSPMG_IMPORT_UNSUPPORTED_EXTENSION,
    OSPMG_IMPORT_FILE_TOO_LARGE,
    OSPMG_IMPORT_INVALID_JSON,
    OSPMG_IMPORT_SCHEMA_INVALID,
    OSPMG_IMPORT_CONFLICT,
    OSPMG_IMPORT_UNTRUSTED_SOURCE,
    OSPMG_IMPORT_PREVIEW_ONLY,
)

PREVIEW_ONLY_TEXT = (
    "Explicit import preview is preview-only data; it does not activate, "
    "validate, install, or execute anything."
)

#: Trust labels treated as untrusted for explicit user/plugin selections.
_UNTRUSTED_TRUST_LABELS: frozenset[str] = frozenset(
    {
        OptionalSolverManifestTrustLabel.USER_PROVIDED.value,
        OptionalSolverManifestTrustLabel.THIRD_PARTY_PLUGIN.value,
        OptionalSolverManifestTrustLabel.UNTRUSTED.value,
        OptionalSolverManifestTrustLabel.INVALID.value,
    }
)


class OptionalSolverPluginManifestExplicitImportState(str, Enum):
    """High-level outcome of an explicit import preview."""

    NO_SOURCES_SELECTED = "no_sources_selected"
    CANCELLED = "cancelled"
    PREVIEWED = "previewed"
    ALL_REJECTED = "all_rejected"
    CONFLICT_ONLY = "conflict_only"
    ERROR = "error"


class OptionalSolverPluginManifestExplicitImportAction(str, Enum):
    """Future action identifiers for the explicit-import GUI surface."""

    CHOOSE_EXPLICIT_JSON_FILES = "choose_explicit_json_files"
    PREVIEW_SELECTED_MANIFEST_JSON = "preview_selected_manifest_json"
    ACTIVATE_MANIFEST = "activate_manifest"
    RUN_DISCOVERY_WITH_PLUGIN_MANIFESTS = "run_discovery_with_plugin_manifests"
    RUN_VALIDATION = "run_validation"
    INSTALL_SOLVER = "install_solver"
    CLOSE_ISSUE = "close_issue"
    EXPORT_REDACTED_SUMMARY = "export_redacted_summary"


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExplicitImportActionState:
    """Display-only state for a future explicit-import action."""

    action: OptionalSolverPluginManifestExplicitImportAction
    label: str
    enabled: bool
    available: bool
    reason: str
    future_action: bool = True


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExplicitImportSummaryViewModel:
    """Summary header values for an explicit-import preview."""

    selected_sources: int
    accepted_count: int
    rejected_count: int
    conflict_count: int
    diagnostic_count: int
    warning_count: int
    error_count: int
    untrusted_source_count: int
    state: str
    status_text: str
    preview_only: bool = True
    activation_performed: bool = False
    discovery_execution_performed: bool = False
    solver_execution_performed: bool = False
    dependency_installation_performed: bool = False
    not_validation_evidence: bool = True
    third_party_manifests_trusted_by_default: bool = False
    external_solvers_bundled: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExplicitImportSourceRowViewModel:
    """Per-source overview row for explicitly selected manifests."""

    source_index: int
    source_type: str
    source_label: str
    source_reference_display: str
    trust_label: str
    status: str
    diagnostics_summary: str
    redacted: bool
    is_untrusted: bool
    warning_text: str


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExplicitImportDiagnosticViewModel:
    """Explicit-import (OSPMG) level diagnostic record."""

    code: str
    severity: str
    message: str
    source_reference_display: str = ""
    redacted: bool = False
    suggested_fix: str = ""


@dataclass(frozen=True, slots=True)
class OptionalSolverPluginManifestExplicitImportGuiViewModel:
    """Complete pure view-model for the explicit-import preview GUI."""

    summary: OptionalSolverPluginManifestExplicitImportSummaryViewModel
    source_rows: tuple[OptionalSolverPluginManifestExplicitImportSourceRowViewModel, ...]
    accepted_rows: tuple[OptionalSolverPluginManifestAcceptedRowViewModel, ...]
    rejected_rows: tuple[OptionalSolverPluginManifestRejectedRowViewModel, ...]
    conflict_rows: tuple[OptionalSolverPluginManifestConflictRowViewModel, ...]
    diagnostic_rows: tuple[OptionalSolverPluginManifestDiagnosticRowViewModel, ...]
    import_diagnostics: tuple[
        OptionalSolverPluginManifestExplicitImportDiagnosticViewModel, ...
    ]
    trust_badges: tuple[OptionalSolverPluginManifestTrustBadgeViewModel, ...]
    actions: tuple[OptionalSolverPluginManifestExplicitImportActionState, ...]
    guidance_text: tuple[str, ...]
    safety_text: tuple[str, ...]
    reserved_import_diagnostic_codes: tuple[str, ...] = OSPMG_IMPORT_DIAGNOSTIC_CODES
    state: str = OptionalSolverPluginManifestExplicitImportState.NO_SOURCES_SELECTED.value
    cancelled: bool = False
    preview_only: bool = True
    not_validation_evidence: bool = True

    # ------------------------------------------------------------------
    # Convenience constructors (transform supplied data only; no file IO).
    # ------------------------------------------------------------------
    @classmethod
    def from_loader_report(
        cls,
        report: OptionalSolverPluginManifestLoadReport,
        *,
        selected_source_count: int | None = None,
        selected_stack_id: str = "",
        filter_text: str = "",
        trust_filters: Sequence[str] | None = None,
        source_filters: Sequence[str] | None = None,
    ) -> OptionalSolverPluginManifestExplicitImportGuiViewModel:
        return build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
            report,
            selected_source_count=selected_source_count,
            selected_stack_id=selected_stack_id,
            filter_text=filter_text,
            trust_filters=trust_filters,
            source_filters=source_filters,
        )

    @classmethod
    def from_cancelled_selection(
        cls,
    ) -> OptionalSolverPluginManifestExplicitImportGuiViewModel:
        return build_optional_solver_plugin_manifest_explicit_import_cancelled_viewmodel()

    @classmethod
    def from_no_selection(
        cls,
    ) -> OptionalSolverPluginManifestExplicitImportGuiViewModel:
        return build_optional_solver_plugin_manifest_explicit_import_empty_viewmodel()

    @classmethod
    def from_import_diagnostics(
        cls,
        diagnostics: Sequence[
            OptionalSolverPluginManifestExplicitImportDiagnosticViewModel
        ],
    ) -> OptionalSolverPluginManifestExplicitImportGuiViewModel:
        return build_optional_solver_plugin_manifest_explicit_import_error_viewmodel(
            diagnostics
        )


def redact_optional_solver_plugin_manifest_source_reference(
    reference: object,
    *,
    provided_label: str = "",
) -> tuple[str, bool]:
    """Return a safe display reference and a redaction flag.

    The helper never inspects the filesystem. It prefers a caller-provided safe
    label, otherwise shortens path-like references to their final segment so
    sensitive absolute paths are not shown by default.
    """

    label = str(provided_label or "").strip()
    if label:
        return label, False
    text = str(reference or "")
    if not text:
        return "", False
    normalized = text.replace("\\", "/")
    if "/" in normalized:
        base = normalized.rsplit("/", 1)[-1] or normalized
        if base and base != text:
            return base, True
    return text, False


def build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
    report: OptionalSolverPluginManifestLoadReport,
    *,
    selected_source_count: int | None = None,
    selected_stack_id: str = "",
    filter_text: str = "",
    trust_filters: Sequence[str] | None = None,
    source_filters: Sequence[str] | None = None,
) -> OptionalSolverPluginManifestExplicitImportGuiViewModel:
    """Build the explicit-import view-model from a supplied loader report."""

    inner = build_optional_solver_plugin_manifest_gui_viewmodel(
        report,
        selected_stack_id=selected_stack_id,
        filter_text=filter_text,
        trust_filters=trust_filters,
        source_filters=source_filters,
    )

    source_rows = _source_rows(report)
    selected_count = (
        selected_source_count if selected_source_count is not None else len(source_rows)
    )
    warning_count = sum(
        1 for item in report.diagnostics if item.severity.value == "warning"
    )
    error_count = sum(
        1 for item in report.diagnostics if item.severity.value in {"error", "blocker"}
    )
    untrusted_count = sum(1 for row in source_rows if row.is_untrusted)
    state = _derive_state(report, selected_count, cancelled=False)
    import_diagnostics = _import_diagnostics(report, cancelled=False)

    summary = OptionalSolverPluginManifestExplicitImportSummaryViewModel(
        selected_sources=selected_count,
        accepted_count=len(report.accepted_manifests),
        rejected_count=len(report.rejected_manifests),
        conflict_count=len(report.conflicts),
        diagnostic_count=len(report.diagnostics),
        warning_count=warning_count,
        error_count=error_count,
        untrusted_source_count=untrusted_count,
        state=state.value,
        status_text=_status_text(report, state, selected_count),
    )

    return OptionalSolverPluginManifestExplicitImportGuiViewModel(
        summary=summary,
        source_rows=source_rows,
        accepted_rows=inner.accepted_rows,
        rejected_rows=inner.rejected_rows,
        conflict_rows=inner.conflict_rows,
        diagnostic_rows=inner.diagnostic_rows,
        import_diagnostics=import_diagnostics,
        trust_badges=inner.trust_badges,
        actions=_action_states(has_preview_data=_has_preview_data(report)),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
        state=state.value,
        cancelled=False,
    )


def build_optional_solver_plugin_manifest_explicit_import_empty_viewmodel() -> (
    OptionalSolverPluginManifestExplicitImportGuiViewModel
):
    """Build the no-sources-selected view-model."""

    state = OptionalSolverPluginManifestExplicitImportState.NO_SOURCES_SELECTED
    summary = _empty_summary(state, status_text="No plugin manifest files selected.")
    return OptionalSolverPluginManifestExplicitImportGuiViewModel(
        summary=summary,
        source_rows=(),
        accepted_rows=(),
        rejected_rows=(),
        conflict_rows=(),
        diagnostic_rows=(),
        import_diagnostics=(_preview_only_diagnostic(),),
        trust_badges=(),
        actions=_action_states(has_preview_data=False),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
        state=state.value,
        cancelled=False,
    )


def build_optional_solver_plugin_manifest_explicit_import_cancelled_viewmodel() -> (
    OptionalSolverPluginManifestExplicitImportGuiViewModel
):
    """Build the cancelled-selection view-model (cancel is a no-op)."""

    state = OptionalSolverPluginManifestExplicitImportState.CANCELLED
    summary = _empty_summary(
        state, status_text="Plugin manifest selection was cancelled."
    )
    cancelled_diagnostic = OptionalSolverPluginManifestExplicitImportDiagnosticViewModel(
        code=OSPMG_IMPORT_CANCELLED,
        severity="info",
        message="Selection was cancelled; no file was opened, read, or parsed.",
    )
    return OptionalSolverPluginManifestExplicitImportGuiViewModel(
        summary=summary,
        source_rows=(),
        accepted_rows=(),
        rejected_rows=(),
        conflict_rows=(),
        diagnostic_rows=(),
        import_diagnostics=(cancelled_diagnostic, _preview_only_diagnostic()),
        trust_badges=(),
        actions=_action_states(has_preview_data=False),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
        state=state.value,
        cancelled=True,
    )


def build_optional_solver_plugin_manifest_explicit_import_error_viewmodel(
    diagnostics: Sequence[
        OptionalSolverPluginManifestExplicitImportDiagnosticViewModel
    ],
) -> OptionalSolverPluginManifestExplicitImportGuiViewModel:
    """Build an error-state view-model from caller-supplied import diagnostics.

    The caller (a future runner) reports import-level failures such as a missing
    file, an unreadable file, invalid JSON, or a schema-invalid manifest. This
    view-model only renders the supplied diagnostics; it performs no file IO.
    """

    supplied = tuple(diagnostics)
    state = OptionalSolverPluginManifestExplicitImportState.ERROR
    error_count = sum(
        1 for item in supplied if item.severity in {"error", "blocker"}
    )
    warning_count = sum(1 for item in supplied if item.severity == "warning")
    summary = OptionalSolverPluginManifestExplicitImportSummaryViewModel(
        selected_sources=0,
        accepted_count=0,
        rejected_count=0,
        conflict_count=0,
        diagnostic_count=len(supplied),
        warning_count=warning_count,
        error_count=error_count,
        untrusted_source_count=0,
        state=state.value,
        status_text="Explicit import could not be previewed; see diagnostics.",
    )
    return OptionalSolverPluginManifestExplicitImportGuiViewModel(
        summary=summary,
        source_rows=(),
        accepted_rows=(),
        rejected_rows=(),
        conflict_rows=(),
        diagnostic_rows=(),
        import_diagnostics=(*supplied, _preview_only_diagnostic()),
        trust_badges=(),
        actions=_action_states(has_preview_data=False),
        guidance_text=_guidance_text(),
        safety_text=_safety_text(),
        state=state.value,
        cancelled=False,
    )


def render_optional_solver_plugin_manifest_explicit_import_summary(
    view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
) -> dict[str, object]:
    """Return an in-memory, redacted, JSON-ready summary.

    This helper builds an in-memory dictionary only. It writes no files, touches
    no clipboard, and opens no shell, browser, or output folder.
    """

    summary = view_model.summary
    return {
        "state": view_model.state,
        "cancelled": view_model.cancelled,
        "preview_only": True,
        "selected_sources": summary.selected_sources,
        "accepted_count": summary.accepted_count,
        "rejected_count": summary.rejected_count,
        "conflict_count": summary.conflict_count,
        "diagnostic_count": summary.diagnostic_count,
        "untrusted_source_count": summary.untrusted_source_count,
        "activation_performed": False,
        "discovery_execution_performed": False,
        "solver_execution_performed": False,
        "dependency_installation_performed": False,
        "plugin_manifest_presence_is_validation_evidence": False,
        "sources": [
            {
                "source_index": row.source_index,
                "source_type": row.source_type,
                "source_label": row.source_label,
                "source_reference_display": row.source_reference_display,
                "trust_label": row.trust_label,
                "status": row.status,
                "redacted": row.redacted,
                "is_untrusted": row.is_untrusted,
            }
            for row in view_model.source_rows
        ],
        "import_diagnostics": [
            {
                "code": item.code,
                "severity": item.severity,
                "message": item.message,
                "source_reference_display": item.source_reference_display,
            }
            for item in view_model.import_diagnostics
        ],
    }


def summarize_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
    view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
) -> str:
    """Return a concise explicit-import preview summary."""

    summary = view_model.summary
    return (
        "Optional solver plugin manifest explicit import preview: "
        f"{summary.selected_sources} selected source(s), "
        f"{summary.accepted_count} accepted, "
        f"{summary.rejected_count} rejected, "
        f"{summary.conflict_count} conflicts, "
        f"{summary.diagnostic_count} diagnostics "
        f"(state={summary.state}). {PREVIEW_ONLY_TEXT}"
    )


def explain_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
    view_model: OptionalSolverPluginManifestExplicitImportGuiViewModel,
) -> str:
    """Explain the safety boundary of the explicit-import view-model."""

    disabled = ", ".join(
        action.action.value for action in view_model.actions if not action.enabled
    )
    return (
        summarize_optional_solver_plugin_manifest_explicit_import_gui_viewmodel(
            view_model
        )
        + " The view-model transforms supplied loader reports or import "
        "diagnostics only; it does not choose, open, read, or parse files, "
        "import plugin packages, scan directories, fetch network manifests, "
        "activate manifests, run discovery, run validation, execute solvers, "
        "install dependencies, mutate issues, or mutate releases. "
        f"Disabled or future-only actions: {disabled}."
    )


# ----------------------------------------------------------------------
# Internal helpers (pure).
# ----------------------------------------------------------------------
def _source_rows(
    report: OptionalSolverPluginManifestLoadReport,
) -> tuple[OptionalSolverPluginManifestExplicitImportSourceRowViewModel, ...]:
    grouped: dict[
        tuple[str, str],
        dict[str, object],
    ] = {}
    for loaded in report.accepted_manifests:
        _accumulate_source(grouped, loaded.source, status="accepted", diagnostics=())
    for rejected in report.rejected_manifests:
        _accumulate_source(
            grouped,
            rejected.source,
            status="rejected",
            diagnostics=rejected.diagnostics,
        )

    rows: list[OptionalSolverPluginManifestExplicitImportSourceRowViewModel] = []
    for index, key in enumerate(sorted(grouped)):
        entry = grouped[key]
        source: OptionalSolverManifestSource = entry["source"]  # type: ignore[assignment]
        status = str(entry["status"])
        diagnostics: tuple[OptionalSolverPluginManifestLoadDiagnostic, ...] = entry[
            "diagnostics"
        ]  # type: ignore[assignment]
        display, redacted = redact_optional_solver_plugin_manifest_source_reference(
            source.reference,
            provided_label="",
        )
        trust_value = source.trust_label.value
        rows.append(
            OptionalSolverPluginManifestExplicitImportSourceRowViewModel(
                source_index=index,
                source_type=source.source_type.value,
                source_label=source.label,
                source_reference_display=display,
                trust_label=trust_value,
                status=status,
                diagnostics_summary=_source_diagnostics_summary(status, diagnostics),
                redacted=redacted,
                is_untrusted=trust_value in _UNTRUSTED_TRUST_LABELS,
                warning_text=_source_warning_text(trust_value),
            )
        )
    return tuple(rows)


def _accumulate_source(
    grouped: dict[tuple[str, str], dict[str, object]],
    source: OptionalSolverManifestSource,
    *,
    status: str,
    diagnostics: tuple[OptionalSolverPluginManifestLoadDiagnostic, ...],
) -> None:
    key = (source.source_type.value, source.reference)
    existing = grouped.get(key)
    if existing is None:
        grouped[key] = {
            "source": source,
            "status": status,
            "diagnostics": diagnostics,
        }
        return
    # Rejection takes precedence over acceptance for the per-source overview.
    if status == "rejected":
        existing["status"] = "rejected"
        existing["source"] = source
        existing["diagnostics"] = diagnostics


def _source_diagnostics_summary(
    status: str,
    diagnostics: Sequence[OptionalSolverPluginManifestLoadDiagnostic],
) -> str:
    if status == "accepted":
        return "Accepted for preview only; not validation evidence."
    for diagnostic in diagnostics:
        if diagnostic.message:
            import_code = _map_loader_code_to_import_code(diagnostic)
            return f"{import_code}: {diagnostic.message}"
    return "Rejected by loader policy."


def _import_diagnostics(
    report: OptionalSolverPluginManifestLoadReport,
    *,
    cancelled: bool,
) -> tuple[OptionalSolverPluginManifestExplicitImportDiagnosticViewModel, ...]:
    items: list[OptionalSolverPluginManifestExplicitImportDiagnosticViewModel] = []
    if cancelled:
        items.append(
            OptionalSolverPluginManifestExplicitImportDiagnosticViewModel(
                code=OSPMG_IMPORT_CANCELLED,
                severity="info",
                message="Selection was cancelled; no file was opened, read, or parsed.",
            )
        )
    for conflict in report.conflicts:
        display, redacted = redact_optional_solver_plugin_manifest_source_reference(
            conflict.rejected_source.reference
        )
        items.append(
            OptionalSolverPluginManifestExplicitImportDiagnosticViewModel(
                code=OSPMG_IMPORT_CONFLICT,
                severity="warning",
                message=conflict.message,
                source_reference_display=display,
                redacted=redacted,
                suggested_fix="Built-ins win by default; resolve the duplicate stack id.",
            )
        )
    for rejected in report.rejected_manifests:
        first = _first_blocking_diagnostic(rejected.diagnostics)
        if first is None:
            continue
        import_code = _map_loader_code_to_import_code(first)
        if import_code == OSPMG_IMPORT_CONFLICT:
            # Conflicts are already surfaced from report.conflicts above.
            continue
        display, redacted = redact_optional_solver_plugin_manifest_source_reference(
            first.source_ref
        )
        items.append(
            OptionalSolverPluginManifestExplicitImportDiagnosticViewModel(
                code=import_code,
                severity=first.severity.value,
                message=first.message,
                source_reference_display=display,
                redacted=redacted,
                suggested_fix=first.suggested_fix,
            )
        )
    if _has_untrusted_source(report):
        items.append(
            OptionalSolverPluginManifestExplicitImportDiagnosticViewModel(
                code=OSPMG_IMPORT_UNTRUSTED_SOURCE,
                severity="warning",
                message=(
                    "User-selected and plugin-provided manifests are untrusted by "
                    "default; a trust label is not certification."
                ),
            )
        )
    items.append(_preview_only_diagnostic())
    return tuple(items)


def _preview_only_diagnostic() -> (
    OptionalSolverPluginManifestExplicitImportDiagnosticViewModel
):
    return OptionalSolverPluginManifestExplicitImportDiagnosticViewModel(
        code=OSPMG_IMPORT_PREVIEW_ONLY,
        severity="info",
        message=PREVIEW_ONLY_TEXT,
    )


def _map_loader_code_to_import_code(
    diagnostic: OptionalSolverPluginManifestLoadDiagnostic,
) -> str:
    code = diagnostic.code.upper()
    category = diagnostic.category.value
    if "EXTENSION" in code:
        return OSPMG_IMPORT_UNSUPPORTED_EXTENSION
    if "JSON_INVALID" in code or "OBJECT_REQUIRED" in code:
        return OSPMG_IMPORT_INVALID_JSON
    if "READ_FAILED" in code or "DIRECTORY_SCAN" in code or "NETWORK_SOURCE" in code:
        return OSPMG_IMPORT_UNREADABLE
    if category == "conflict":
        return OSPMG_IMPORT_CONFLICT
    if category == "trust":
        return OSPMG_IMPORT_UNTRUSTED_SOURCE
    # Schema, safety, source, policy, and remaining IO map to schema-invalid.
    return OSPMG_IMPORT_SCHEMA_INVALID


def _first_blocking_diagnostic(
    diagnostics: Sequence[OptionalSolverPluginManifestLoadDiagnostic],
) -> OptionalSolverPluginManifestLoadDiagnostic | None:
    for diagnostic in diagnostics:
        if diagnostic.is_blocking:
            return diagnostic
    return diagnostics[0] if diagnostics else None


def _has_untrusted_source(report: OptionalSolverPluginManifestLoadReport) -> bool:
    for loaded in report.accepted_manifests:
        if loaded.source.trust_label.value in _UNTRUSTED_TRUST_LABELS:
            return True
    for rejected in report.rejected_manifests:
        if rejected.source.trust_label.value in _UNTRUSTED_TRUST_LABELS:
            return True
    return False


def _has_preview_data(report: OptionalSolverPluginManifestLoadReport) -> bool:
    return bool(
        report.accepted_manifests
        or report.rejected_manifests
        or report.conflicts
        or report.diagnostics
    )


def _derive_state(
    report: OptionalSolverPluginManifestLoadReport,
    selected_count: int,
    *,
    cancelled: bool,
) -> OptionalSolverPluginManifestExplicitImportState:
    if cancelled:
        return OptionalSolverPluginManifestExplicitImportState.CANCELLED
    if not _has_preview_data(report) and selected_count <= 0:
        return OptionalSolverPluginManifestExplicitImportState.NO_SOURCES_SELECTED
    if report.accepted_manifests:
        return OptionalSolverPluginManifestExplicitImportState.PREVIEWED
    if report.rejected_manifests:
        return OptionalSolverPluginManifestExplicitImportState.ALL_REJECTED
    if report.conflicts:
        return OptionalSolverPluginManifestExplicitImportState.CONFLICT_ONLY
    return OptionalSolverPluginManifestExplicitImportState.PREVIEWED


def _status_text(
    report: OptionalSolverPluginManifestLoadReport,
    state: OptionalSolverPluginManifestExplicitImportState,
    selected_count: int,
) -> str:
    return (
        f"Explicit import preview ({state.value}): {selected_count} selected "
        f"source(s), {len(report.accepted_manifests)} accepted, "
        f"{len(report.rejected_manifests)} rejected, "
        f"{len(report.conflicts)} conflicts. This preview is not validation "
        "evidence."
    )


def _empty_summary(
    state: OptionalSolverPluginManifestExplicitImportState,
    *,
    status_text: str,
) -> OptionalSolverPluginManifestExplicitImportSummaryViewModel:
    return OptionalSolverPluginManifestExplicitImportSummaryViewModel(
        selected_sources=0,
        accepted_count=0,
        rejected_count=0,
        conflict_count=0,
        diagnostic_count=0,
        warning_count=0,
        error_count=0,
        untrusted_source_count=0,
        state=state.value,
        status_text=status_text,
    )


def _action_states(
    *,
    has_preview_data: bool,
) -> tuple[OptionalSolverPluginManifestExplicitImportActionState, ...]:
    Action = OptionalSolverPluginManifestExplicitImportAction
    return (
        OptionalSolverPluginManifestExplicitImportActionState(
            action=Action.CHOOSE_EXPLICIT_JSON_FILES,
            label="Choose explicit JSON files",
            enabled=False,
            available=True,
            reason=(
                "File dialog selection is a future implementation gate "
                "(OSW-EXP-077); this view-model performs no file IO."
            ),
            future_action=True,
        ),
        OptionalSolverPluginManifestExplicitImportActionState(
            action=Action.PREVIEW_SELECTED_MANIFEST_JSON,
            label="Preview selected manifest JSON",
            enabled=has_preview_data,
            available=True,
            reason=(
                "Display-only preview of an already-supplied loader report; no "
                "file is opened, read, or parsed here."
            ),
            future_action=False,
        ),
        OptionalSolverPluginManifestExplicitImportActionState(
            action=Action.ACTIVATE_MANIFEST,
            label="Activate manifest",
            enabled=False,
            available=False,
            reason="Plugin manifest activation requires a separate future gate.",
        ),
        OptionalSolverPluginManifestExplicitImportActionState(
            action=Action.RUN_DISCOVERY_WITH_PLUGIN_MANIFESTS,
            label="Run discovery with plugin manifests",
            enabled=False,
            available=False,
            reason=(
                "Discovery with plugin manifests is unavailable until an explicit "
                "activation model exists."
            ),
        ),
        OptionalSolverPluginManifestExplicitImportActionState(
            action=Action.RUN_VALIDATION,
            label="Run validation",
            enabled=False,
            available=False,
            reason="Validation requires a separate OSW-VALID gate.",
        ),
        OptionalSolverPluginManifestExplicitImportActionState(
            action=Action.INSTALL_SOLVER,
            label="Install solver",
            enabled=False,
            available=False,
            reason="Solver installation is unavailable.",
        ),
        OptionalSolverPluginManifestExplicitImportActionState(
            action=Action.CLOSE_ISSUE,
            label="Close issue",
            enabled=False,
            available=False,
            reason="Issue closure requires a separate validation and closure gate.",
        ),
        OptionalSolverPluginManifestExplicitImportActionState(
            action=Action.EXPORT_REDACTED_SUMMARY,
            label="Export redacted summary",
            enabled=has_preview_data,
            available=True,
            reason=(
                "Produces an in-memory redacted summary only; it writes no files "
                "and uses no clipboard, shell, or browser."
            ),
            future_action=False,
        ),
    )


def _guidance_text() -> tuple[str, ...]:
    return (
        "Explicit import preview is data-only.",
        PREVIEW_ONLY_TEXT,
        NOT_VALIDATION_EVIDENCE_TEXT,
        THIRD_PARTY_NOT_TRUSTED_TEXT,
        NO_BUNDLED_SOLVER_TEXT,
        "Preview is not activation, validation, or installation.",
        "Issue closure requires separate validation and closure gates.",
    )


def _safety_text() -> tuple[str, ...]:
    return (
        "No file dialog implementation.",
        "No file loading.",
        "No JSON parsing from a path.",
        "No plugin code execution.",
        "No plugin package import.",
        "No directory scanning.",
        "No network fetch.",
        "No discovery execution.",
        "No solver execution.",
        "No dependency installation.",
        "No issue mutation.",
        "No release mutation.",
    )


def _source_warning_text(trust_value: str) -> str:
    if trust_value == OptionalSolverManifestTrustLabel.TRUSTED_BUILTIN.value:
        return "Built-in trusted source; trust label is not certification."
    if trust_value == OptionalSolverManifestTrustLabel.REVIEWED_PROJECT.value:
        return "Project-reviewed source; review status is not validation evidence."
    if trust_value == OptionalSolverManifestTrustLabel.ORGANIZATION_MANAGED.value:
        return "Organization-managed source; trust label is not certification."
    if trust_value == OptionalSolverManifestTrustLabel.THIRD_PARTY_PLUGIN.value:
        return THIRD_PARTY_NOT_TRUSTED_TEXT
    if trust_value == OptionalSolverManifestTrustLabel.INVALID.value:
        return "Invalid or blocked source; do not activate."
    return "User-provided or untrusted source; untrusted by default."


__all__ = [
    "OSPMG_IMPORT_CANCELLED",
    "OSPMG_IMPORT_CONFLICT",
    "OSPMG_IMPORT_DIAGNOSTIC_CODES",
    "OSPMG_IMPORT_FILE_MISSING",
    "OSPMG_IMPORT_FILE_TOO_LARGE",
    "OSPMG_IMPORT_INVALID_JSON",
    "OSPMG_IMPORT_PREVIEW_ONLY",
    "OSPMG_IMPORT_SCHEMA_INVALID",
    "OSPMG_IMPORT_UNREADABLE",
    "OSPMG_IMPORT_UNSUPPORTED_EXTENSION",
    "OSPMG_IMPORT_UNTRUSTED_SOURCE",
    "OptionalSolverPluginManifestExplicitImportAction",
    "OptionalSolverPluginManifestExplicitImportActionState",
    "OptionalSolverPluginManifestExplicitImportDiagnosticViewModel",
    "OptionalSolverPluginManifestExplicitImportGuiViewModel",
    "OptionalSolverPluginManifestExplicitImportSourceRowViewModel",
    "OptionalSolverPluginManifestExplicitImportState",
    "OptionalSolverPluginManifestExplicitImportSummaryViewModel",
    "build_optional_solver_plugin_manifest_explicit_import_cancelled_viewmodel",
    "build_optional_solver_plugin_manifest_explicit_import_empty_viewmodel",
    "build_optional_solver_plugin_manifest_explicit_import_error_viewmodel",
    "build_optional_solver_plugin_manifest_explicit_import_gui_viewmodel",
    "explain_optional_solver_plugin_manifest_explicit_import_gui_viewmodel",
    "redact_optional_solver_plugin_manifest_source_reference",
    "render_optional_solver_plugin_manifest_explicit_import_summary",
    "summarize_optional_solver_plugin_manifest_explicit_import_gui_viewmodel",
]
