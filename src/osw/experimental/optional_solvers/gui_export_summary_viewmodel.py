"""Pure export summary view-models for optional solver GUI health data.

This module consumes an already-built optional solver health panel view-model
and prepares redacted export payloads. It does not write files, open dialogs,
touch clipboards, open shells or browsers, execute discovery, run solvers, or
install dependencies.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .gui_health_viewmodel import (
    OptionalSolverDiagnosticRowViewModel,
    OptionalSolverGuidanceRowViewModel,
    OptionalSolverHealthPanelViewModel,
    OptionalSolverStackCardViewModel,
    OptionalSolverValidationHistoryRowViewModel,
)


class OptionalSolverExportSummaryFormat(str, Enum):
    """Supported future export summary formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    TEXT = "text"

    @classmethod
    def from_value(cls, value: object) -> OptionalSolverExportSummaryFormat:
        if isinstance(value, cls):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"md", ".md"}:
            return cls.MARKDOWN
        if normalized in {"txt", ".txt"}:
            return cls.TEXT
        if normalized in {"json", ".json"}:
            return cls.JSON
        return cls(normalized)


@dataclass(frozen=True, slots=True)
class OptionalSolverExportSummaryOptions:
    """Options for building a redacted optional solver export summary."""

    export_format: OptionalSolverExportSummaryFormat = (
        OptionalSolverExportSummaryFormat.JSON
    )
    app_name: str = "OpenSolver Workbench"
    tool_name: str = "Optional solver GUI health panel"
    package_version: str = ""
    generated_at: str = ""
    source_context: str = "optional_solver_gui_health_panel"
    include_full_paths: bool = False
    full_paths_acknowledged: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverExportSummaryDiagnostic:
    """Diagnostic for payload or save-plan analysis."""

    severity: str
    code: str
    message: str
    field: str = ""
    suggested_fix: str = ""

    def to_dict(self) -> dict[str, str]:
        return _drop_empty(
            {
                "severity": self.severity,
                "code": self.code,
                "message": self.message,
                "field": self.field,
                "suggested_fix": self.suggested_fix,
            }
        )


@dataclass(frozen=True, slots=True)
class OptionalSolverExportSummaryPrivacyWarning:
    """Privacy warning attached to an export summary payload."""

    code: str
    message: str
    acknowledgement_required: bool = True
    acknowledged: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "acknowledgement_required": self.acknowledgement_required,
            "acknowledged": self.acknowledged,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverExportSummaryPayload:
    """Serializable optional solver export summary payload."""

    app_name: str
    tool_name: str
    package_version: str
    generated_at: str
    source_context: str
    export_format: str
    summary: Mapping[str, object]
    stacks: tuple[Mapping[str, object], ...]
    diagnostics: tuple[Mapping[str, object], ...]
    guidance: tuple[Mapping[str, object], ...]
    validation_history: tuple[Mapping[str, object], ...]
    issue_references: tuple[str, ...]
    safety_notes: tuple[str, ...]
    privacy_notes: tuple[str, ...]
    privacy_warnings: tuple[OptionalSolverExportSummaryPrivacyWarning, ...]
    redaction_state: Mapping[str, object]
    non_bundled_solver_disclaimer: str
    not_validation_evidence: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "app_name": self.app_name,
            "tool_name": self.tool_name,
            "package_version": self.package_version,
            "generated_at": self.generated_at,
            "source_context": self.source_context,
            "export_format": self.export_format,
            "summary": dict(self.summary),
            "stacks": [dict(item) for item in self.stacks],
            "diagnostics": [dict(item) for item in self.diagnostics],
            "guidance": [dict(item) for item in self.guidance],
            "validation_history": [dict(item) for item in self.validation_history],
            "issue_references": list(self.issue_references),
            "safety_notes": list(self.safety_notes),
            "privacy_notes": list(self.privacy_notes),
            "privacy_warnings": [
                warning.to_dict() for warning in self.privacy_warnings
            ],
            "redaction_state": dict(self.redaction_state),
            "non_bundled_solver_disclaimer": self.non_bundled_solver_disclaimer,
            "not_validation_evidence": self.not_validation_evidence,
        }


@dataclass(frozen=True, slots=True)
class OptionalSolverExportSummaryRenderResult:
    """Rendered export summary content."""

    export_format: OptionalSolverExportSummaryFormat
    content: str
    media_type: str
    file_extension: str
    diagnostics: tuple[OptionalSolverExportSummaryDiagnostic, ...] = field(
        default_factory=tuple
    )


@dataclass(frozen=True, slots=True)
class OptionalSolverExportSummarySavePlan:
    """Side-effect-free save-path analysis for a future export implementation."""

    requested_path: str
    normalized_path: str
    export_format: OptionalSolverExportSummaryFormat | None
    file_extension: str
    parent_directory: str
    parent_exists: bool
    target_exists: bool
    overwrite_allowed: bool
    can_save: bool
    diagnostics: tuple[OptionalSolverExportSummaryDiagnostic, ...]
    would_write_file: bool = False


@dataclass(frozen=True, slots=True)
class OptionalSolverExportSummaryViewModel:
    """Pure export summary view-model."""

    options: OptionalSolverExportSummaryOptions
    payload: OptionalSolverExportSummaryPayload
    render_results: tuple[OptionalSolverExportSummaryRenderResult, ...]
    diagnostics: tuple[OptionalSolverExportSummaryDiagnostic, ...]
    privacy_warnings: tuple[OptionalSolverExportSummaryPrivacyWarning, ...]


def build_optional_solver_export_summary_viewmodel(
    panel: OptionalSolverHealthPanelViewModel,
    options: OptionalSolverExportSummaryOptions | None = None,
) -> OptionalSolverExportSummaryViewModel:
    """Build a pure export summary view-model from a health panel view-model."""

    active_options = options or OptionalSolverExportSummaryOptions()
    payload = build_optional_solver_export_summary_payload(panel, active_options)
    render_results = (
        render_optional_solver_export_summary_json(payload),
        render_optional_solver_export_summary_markdown(payload),
        render_optional_solver_export_summary_text(payload),
    )
    diagnostics = _payload_diagnostics(active_options)
    return OptionalSolverExportSummaryViewModel(
        options=active_options,
        payload=payload,
        render_results=render_results,
        diagnostics=diagnostics,
        privacy_warnings=payload.privacy_warnings,
    )


def build_optional_solver_export_summary_payload(
    panel: OptionalSolverHealthPanelViewModel,
    options: OptionalSolverExportSummaryOptions | None = None,
) -> OptionalSolverExportSummaryPayload:
    """Build a JSON-compatible redacted export payload."""

    active_options = options or OptionalSolverExportSummaryOptions()
    allow_full_paths = (
        active_options.include_full_paths and active_options.full_paths_acknowledged
    )
    privacy_warnings = _privacy_warnings(active_options)
    return OptionalSolverExportSummaryPayload(
        app_name=_sanitize_text(active_options.app_name, allow_full_paths),
        tool_name=_sanitize_text(active_options.tool_name, allow_full_paths),
        package_version=_sanitize_text(
            active_options.package_version,
            allow_full_paths,
        ),
        generated_at=_sanitize_text(active_options.generated_at, allow_full_paths),
        source_context=_sanitize_text(
            active_options.source_context,
            allow_full_paths,
        ),
        export_format=active_options.export_format.value,
        summary=_summary_payload(panel),
        stacks=tuple(_stack_payload(card, allow_full_paths) for card in panel.cards),
        diagnostics=tuple(
            _diagnostic_payload(row, allow_full_paths) for row in panel.diagnostics
        ),
        guidance=tuple(
            _guidance_payload(row, allow_full_paths) for row in panel.guidance
        ),
        validation_history=tuple(
            _validation_history_payload(row, allow_full_paths)
            for row in panel.validation_history
        ),
        issue_references=_issue_references(panel),
        safety_notes=_safety_notes(panel, allow_full_paths),
        privacy_notes=_privacy_notes(active_options),
        privacy_warnings=privacy_warnings,
        redaction_state=_redaction_state(active_options),
        non_bundled_solver_disclaimer=(
            "External solvers and optional science packages are not bundled by "
            "OpenSolver Workbench."
        ),
        not_validation_evidence=True,
    )


def render_optional_solver_export_summary_json(
    payload: OptionalSolverExportSummaryPayload,
) -> OptionalSolverExportSummaryRenderResult:
    """Render the export payload as deterministic JSON."""

    return OptionalSolverExportSummaryRenderResult(
        export_format=OptionalSolverExportSummaryFormat.JSON,
        content=json.dumps(payload.to_dict(), indent=2, sort_keys=True),
        media_type="application/json",
        file_extension=".json",
    )


def render_optional_solver_export_summary_markdown(
    payload: OptionalSolverExportSummaryPayload,
) -> OptionalSolverExportSummaryRenderResult:
    """Render the export payload as Markdown."""

    lines = [
        "# Optional Solver Health Summary",
        "",
        f"- App: {payload.app_name}",
        f"- Tool: {payload.tool_name}",
        f"- Package version: {payload.package_version or 'not supplied'}",
        f"- Generated at: {payload.generated_at or 'not supplied'}",
        f"- Source: {payload.source_context}",
        f"- Not validation evidence: {payload.not_validation_evidence}",
        "",
        "## Summary",
        "",
        *_summary_lines(payload.summary),
        "",
        "## Stacks",
        "",
        *_stack_lines(payload.stacks),
        "",
        "## Diagnostics",
        "",
        *_diagnostic_lines(payload.diagnostics),
        "",
        "## Guidance",
        "",
        *_guidance_lines(payload.guidance),
        "",
        "## Validation History",
        "",
        *_history_lines(payload.validation_history),
        "",
        "## Privacy",
        "",
        *[f"- {note}" for note in payload.privacy_notes],
        *[
            "- "
            + warning.code
            + ": "
            + warning.message
            + f" acknowledged={warning.acknowledged}"
            for warning in payload.privacy_warnings
        ],
        "",
        "## Safety",
        "",
        *[f"- {note}" for note in payload.safety_notes],
    ]
    return OptionalSolverExportSummaryRenderResult(
        export_format=OptionalSolverExportSummaryFormat.MARKDOWN,
        content="\n".join(lines).rstrip() + "\n",
        media_type="text/markdown",
        file_extension=".md",
    )


def render_optional_solver_export_summary_text(
    payload: OptionalSolverExportSummaryPayload,
) -> OptionalSolverExportSummaryRenderResult:
    """Render the export payload as plain text."""

    lines = [
        "Optional Solver Health Summary",
        f"App: {payload.app_name}",
        f"Tool: {payload.tool_name}",
        f"Package version: {payload.package_version or 'not supplied'}",
        f"Generated at: {payload.generated_at or 'not supplied'}",
        f"Source: {payload.source_context}",
        f"Not validation evidence: {payload.not_validation_evidence}",
        "",
        "Summary:",
        *_plain_summary_lines(payload.summary),
        "",
        "Stacks:",
        *_plain_stack_lines(payload.stacks),
        "",
        "Diagnostics:",
        *_plain_mapping_lines(payload.diagnostics),
        "",
        "Guidance:",
        *_plain_mapping_lines(payload.guidance),
        "",
        "Validation history:",
        *_plain_mapping_lines(payload.validation_history),
        "",
        "Privacy:",
        *[f"- {note}" for note in payload.privacy_notes],
        *[
            f"- {warning.code}: {warning.message}; acknowledged={warning.acknowledged}"
            for warning in payload.privacy_warnings
        ],
        "",
        "Safety:",
        *[f"- {note}" for note in payload.safety_notes],
    ]
    return OptionalSolverExportSummaryRenderResult(
        export_format=OptionalSolverExportSummaryFormat.TEXT,
        content="\n".join(lines).rstrip() + "\n",
        media_type="text/plain",
        file_extension=".txt",
    )


def plan_optional_solver_export_summary_save(
    path: str | Path | None,
    *,
    export_format: OptionalSolverExportSummaryFormat | str | None = None,
    allow_overwrite: bool = False,
) -> OptionalSolverExportSummarySavePlan:
    """Analyze a future save path without writing files."""

    diagnostics: list[OptionalSolverExportSummaryDiagnostic] = []
    requested_path = "" if path is None else str(path)
    if not requested_path.strip():
        diagnostics.append(
            OptionalSolverExportSummaryDiagnostic(
                severity="error",
                code="OSE_PATH_REQUIRED",
                message="An explicit export path is required.",
                field="path",
                suggested_fix="Choose a .json, .md, or .txt export path.",
            )
        )
        return _save_plan(
            requested_path=requested_path,
            path_obj=None,
            export_format=None,
            overwrite_allowed=allow_overwrite,
            diagnostics=diagnostics,
        )

    path_obj = Path(requested_path)
    if _has_unsafe_path_parts(path_obj):
        diagnostics.append(
            OptionalSolverExportSummaryDiagnostic(
                severity="error",
                code="OSE_UNSAFE_PATH",
                message="Export path contains traversal or unsafe characters.",
                field="path",
                suggested_fix="Choose a normal file path without traversal.",
            )
        )

    extension = path_obj.suffix.lower()
    inferred_format = _format_from_extension(extension)
    active_format = (
        OptionalSolverExportSummaryFormat.from_value(export_format)
        if export_format is not None
        else inferred_format
    )
    if extension not in _ALLOWED_EXTENSIONS:
        diagnostics.append(
            OptionalSolverExportSummaryDiagnostic(
                severity="error",
                code="OSE_UNSUPPORTED_EXTENSION",
                message="Export path must end in .json, .md, or .txt.",
                field="path",
                suggested_fix="Use a supported export summary extension.",
            )
        )
    if active_format is not None and extension in _ALLOWED_EXTENSIONS:
        expected_extension = _extension_for_format(active_format)
        if extension != expected_extension:
            diagnostics.append(
                OptionalSolverExportSummaryDiagnostic(
                    severity="error",
                    code="OSE_EXTENSION_FORMAT_MISMATCH",
                    message="Export path extension does not match the format.",
                    field="export_format",
                    suggested_fix=f"Use {expected_extension} for {active_format.value}.",
                )
            )

    parent = path_obj.parent
    if parent and not parent.exists():
        diagnostics.append(
            OptionalSolverExportSummaryDiagnostic(
                severity="error",
                code="OSE_PARENT_MISSING",
                message="Export parent directory does not exist.",
                field="path",
                suggested_fix="Choose an existing directory.",
            )
        )
    if path_obj.exists() and not allow_overwrite:
        diagnostics.append(
            OptionalSolverExportSummaryDiagnostic(
                severity="error",
                code="OSE_OVERWRITE_BLOCKED",
                message="Export target exists and overwrite is not acknowledged.",
                field="path",
                suggested_fix="Choose a new path or explicitly allow overwrite.",
            )
        )
    return _save_plan(
        requested_path=requested_path,
        path_obj=path_obj,
        export_format=active_format,
        overwrite_allowed=allow_overwrite,
        diagnostics=diagnostics,
    )


def explain_optional_solver_export_summary(
    view_model: OptionalSolverExportSummaryViewModel,
) -> str:
    """Return a concise explanation of the export summary view-model."""

    return (
        "Optional solver export summary prepared "
        f"{len(view_model.payload.stacks)} stack summaries in "
        f"{len(view_model.render_results)} text-oriented formats. The payload is "
        "not validation evidence and this layer does not write files, open "
        "dialogs, use clipboards, run discovery, execute solvers, or mutate "
        "issues."
    )


def _summary_payload(panel: OptionalSolverHealthPanelViewModel) -> dict[str, object]:
    summary = panel.summary
    return {
        "total_stacks": summary.total_stacks,
        "counts_by_health_state": dict(sorted(summary.counts_by_health_state.items())),
        "missing_count": summary.missing_count,
        "partial_count": summary.partial_count,
        "discovered_count": summary.discovered_count,
        "open_issue_count": summary.open_issue_count,
        "validation_warning_count": summary.validation_warning_count,
    }


def _stack_payload(
    card: OptionalSolverStackCardViewModel,
    allow_full_paths: bool,
) -> dict[str, object]:
    return {
        "stack_id": _sanitize_text(card.stack_id, allow_full_paths),
        "display_name": _sanitize_text(card.display_name, allow_full_paths),
        "related_issue": card.related_issue,
        "issue_reference": _sanitize_text(card.issue_reference, allow_full_paths),
        "health_state": _sanitize_text(card.health_state, allow_full_paths),
        "support_status": _sanitize_text(card.support_status, allow_full_paths),
        "short_status_text": _sanitize_text(card.short_status_text, allow_full_paths),
        "missing_requirements_count": card.missing_requirements_count,
        "diagnostics_count": card.diagnostics_count,
        "has_non_bundled_disclaimer": card.has_non_bundled_disclaimer,
    }


def _diagnostic_payload(
    row: OptionalSolverDiagnosticRowViewModel,
    allow_full_paths: bool,
) -> dict[str, object]:
    return _drop_empty(
        {
            "stack_id": _sanitize_text(row.stack_id, allow_full_paths),
            "severity": _sanitize_text(row.severity, allow_full_paths),
            "code": _sanitize_text(row.code, allow_full_paths),
            "message": _sanitize_text(row.message, allow_full_paths),
            "path": _sanitize_text(row.path, allow_full_paths),
            "suggested_fix": _sanitize_text(row.suggested_fix, allow_full_paths),
            "redaction_notice": _sanitize_text(
                row.redaction_notice,
                allow_full_paths,
            ),
        }
    )


def _guidance_payload(
    row: OptionalSolverGuidanceRowViewModel,
    allow_full_paths: bool,
) -> dict[str, object]:
    return {
        "category": _sanitize_text(row.category, allow_full_paths),
        "severity": _sanitize_text(row.severity, allow_full_paths),
        "text": _sanitize_text(row.text, allow_full_paths),
    }


def _validation_history_payload(
    row: OptionalSolverValidationHistoryRowViewModel,
    allow_full_paths: bool,
) -> dict[str, object]:
    return _drop_empty(
        {
            "source": _sanitize_text(row.source, allow_full_paths),
            "status": _sanitize_text(row.status, allow_full_paths),
            "summary": _sanitize_text(row.summary, allow_full_paths),
            "timestamp": _sanitize_text(row.timestamp, allow_full_paths),
            "related_issue": row.related_issue,
            "issue_reference": (
                f"#{row.related_issue}" if row.related_issue is not None else ""
            ),
            "is_pass_evidence": row.is_pass_evidence,
            "closure_review_required": row.closure_review_required,
        }
    )


def _issue_references(panel: OptionalSolverHealthPanelViewModel) -> tuple[str, ...]:
    refs = {
        card.issue_reference
        for card in panel.cards
        if card.issue_reference
    }
    refs.update(
        f"#{row.related_issue}"
        for row in panel.validation_history
        if row.related_issue is not None
    )
    return tuple(sorted(refs, key=_issue_sort_key))


def _safety_notes(
    panel: OptionalSolverHealthPanelViewModel,
    allow_full_paths: bool,
) -> tuple[str, ...]:
    notes = [
        "Exported summary is not validation evidence.",
        "Skipped-missing is not pass evidence.",
        "Issues #6 through #11 remain separate prepared-machine validation work.",
        "No discovery execution during export.",
        "No solver execution during export.",
        "No file write is performed by this view-model.",
        "No clipboard, shell, or browser action is performed.",
        "External solvers and optional science packages are not bundled.",
        "No certification claim is made.",
    ]
    if panel.details is not None:
        notes.extend(panel.details.safety_notes)
    return tuple(_sanitize_text(note, allow_full_paths) for note in notes)


def _privacy_notes(
    options: OptionalSolverExportSummaryOptions,
) -> tuple[str, ...]:
    notes = [
        "Redacted by default.",
        "Environment values are never exported.",
        "The export summary contains passive setup evidence only.",
        "No telemetry is collected.",
    ]
    if options.include_full_paths:
        notes.append(
            "Full path export was requested; explicit acknowledgement is required."
        )
    else:
        notes.append("Full paths are omitted by default.")
    return tuple(notes)


def _privacy_warnings(
    options: OptionalSolverExportSummaryOptions,
) -> tuple[OptionalSolverExportSummaryPrivacyWarning, ...]:
    if not options.include_full_paths:
        return ()
    return (
        OptionalSolverExportSummaryPrivacyWarning(
            code="OSE_FULL_PATH_EXPORT_REQUESTED",
            message=(
                "Full path export can reveal private user directories. "
                "Confirm before using an implementation that can include paths."
            ),
            acknowledgement_required=True,
            acknowledged=options.full_paths_acknowledged,
        ),
    )


def _payload_diagnostics(
    options: OptionalSolverExportSummaryOptions,
) -> tuple[OptionalSolverExportSummaryDiagnostic, ...]:
    if options.include_full_paths and not options.full_paths_acknowledged:
        return (
            OptionalSolverExportSummaryDiagnostic(
                severity="warning",
                code="OSE_PRIVACY_ACK_REQUIRED",
                message="Full path export was requested without acknowledgement.",
                field="include_full_paths",
                suggested_fix="Require explicit privacy acknowledgement.",
            ),
        )
    return ()


def _redaction_state(options: OptionalSolverExportSummaryOptions) -> dict[str, object]:
    full_paths_enabled = (
        options.include_full_paths and options.full_paths_acknowledged
    )
    return {
        "redacted_by_default": True,
        "full_path_export_requested": options.include_full_paths,
        "full_path_export_acknowledged": options.full_paths_acknowledged,
        "full_paths_allowed_by_options": full_paths_enabled,
        "environment_values_exported": False,
    }


def _save_plan(
    *,
    requested_path: str,
    path_obj: Path | None,
    export_format: OptionalSolverExportSummaryFormat | None,
    overwrite_allowed: bool,
    diagnostics: Sequence[OptionalSolverExportSummaryDiagnostic],
) -> OptionalSolverExportSummarySavePlan:
    parent = path_obj.parent if path_obj is not None else None
    can_save = not any(item.severity == "error" for item in diagnostics)
    return OptionalSolverExportSummarySavePlan(
        requested_path=requested_path,
        normalized_path=str(path_obj) if path_obj is not None else "",
        export_format=export_format,
        file_extension=path_obj.suffix.lower() if path_obj is not None else "",
        parent_directory=str(parent) if parent is not None else "",
        parent_exists=bool(parent.exists()) if parent is not None else False,
        target_exists=bool(path_obj.exists()) if path_obj is not None else False,
        overwrite_allowed=overwrite_allowed,
        can_save=can_save,
        diagnostics=tuple(diagnostics),
        would_write_file=False,
    )


def _format_from_extension(
    extension: str,
) -> OptionalSolverExportSummaryFormat | None:
    mapping = {
        ".json": OptionalSolverExportSummaryFormat.JSON,
        ".md": OptionalSolverExportSummaryFormat.MARKDOWN,
        ".txt": OptionalSolverExportSummaryFormat.TEXT,
    }
    return mapping.get(extension)


def _extension_for_format(export_format: OptionalSolverExportSummaryFormat) -> str:
    return {
        OptionalSolverExportSummaryFormat.JSON: ".json",
        OptionalSolverExportSummaryFormat.MARKDOWN: ".md",
        OptionalSolverExportSummaryFormat.TEXT: ".txt",
    }[export_format]


def _has_unsafe_path_parts(path: Path) -> bool:
    raw = str(path)
    if "\x00" in raw:
        return True
    if any(part == ".." for part in path.parts):
        return True
    return any(char in raw for char in '<>"|?*')


def _sanitize_text(value: object, allow_full_paths: bool) -> str:
    text = "" if value is None else str(value)
    text = _ENV_ASSIGNMENT_RE.sub(r"\1=<redacted>", text)
    if allow_full_paths:
        return text
    text = _WINDOWS_PATH_RE.sub("<redacted:path>", text)
    text = _POSIX_PRIVATE_PATH_RE.sub("<redacted:path>", text)
    return text


def _summary_lines(summary: Mapping[str, object]) -> list[str]:
    return [
        f"- Total stacks: {summary.get('total_stacks', 0)}",
        f"- Missing: {summary.get('missing_count', 0)}",
        f"- Partial: {summary.get('partial_count', 0)}",
        f"- Discovered: {summary.get('discovered_count', 0)}",
        f"- Open issues: {summary.get('open_issue_count', 0)}",
        f"- Validation warnings: {summary.get('validation_warning_count', 0)}",
    ]


def _stack_lines(stacks: Sequence[Mapping[str, object]]) -> list[str]:
    if not stacks:
        return ["- No stacks included."]
    return [
        "- "
        + str(stack.get("stack_id", ""))
        + ": "
        + str(stack.get("display_name", ""))
        + " | health="
        + str(stack.get("health_state", ""))
        + " | issue="
        + str(stack.get("issue_reference", ""))
        for stack in stacks
    ]


def _diagnostic_lines(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["- No diagnostics."]
    return [
        "- "
        + str(row.get("stack_id", ""))
        + " | "
        + str(row.get("severity", ""))
        + " | "
        + str(row.get("code", ""))
        + " | "
        + str(row.get("message", ""))
        for row in rows
    ]


def _guidance_lines(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["- No guidance."]
    return [
        "- "
        + str(row.get("category", ""))
        + " ["
        + str(row.get("severity", ""))
        + "]: "
        + str(row.get("text", ""))
        for row in rows
    ]


def _history_lines(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["- No validation history."]
    return [
        "- "
        + str(row.get("source", ""))
        + ": "
        + str(row.get("status", ""))
        + " | "
        + str(row.get("issue_reference", ""))
        + " | pass_evidence="
        + str(row.get("is_pass_evidence", False))
        for row in rows
    ]


def _plain_summary_lines(summary: Mapping[str, object]) -> list[str]:
    return [line.replace("- ", "", 1) for line in _summary_lines(summary)]


def _plain_stack_lines(stacks: Sequence[Mapping[str, object]]) -> list[str]:
    return [line.replace("- ", "", 1) for line in _stack_lines(stacks)]


def _plain_mapping_lines(rows: Sequence[Mapping[str, object]]) -> list[str]:
    if not rows:
        return ["- none"]
    return ["- " + "; ".join(f"{key}={value}" for key, value in row.items()) for row in rows]


def _issue_sort_key(issue_reference: str) -> tuple[int, str]:
    try:
        return (int(issue_reference.lstrip("#")), issue_reference)
    except ValueError:
        return (999999, issue_reference)


def _drop_empty(payload: Mapping[str, object]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if value not in ("", None, [], (), {})
    }


_ALLOWED_EXTENSIONS = {".json", ".md", ".txt"}
_WINDOWS_PATH_RE = re.compile(r"\b[A-Za-z]:[\\/][^\s|,;)]*")
_POSIX_PRIVATE_PATH_RE = re.compile(r"(?<!\w)/(?:Users|home)/[^\s|,;)]*")
_ENV_ASSIGNMENT_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})=([^\s,;]+)")


__all__ = [
    "OptionalSolverExportSummaryDiagnostic",
    "OptionalSolverExportSummaryFormat",
    "OptionalSolverExportSummaryOptions",
    "OptionalSolverExportSummaryPayload",
    "OptionalSolverExportSummaryPrivacyWarning",
    "OptionalSolverExportSummaryRenderResult",
    "OptionalSolverExportSummarySavePlan",
    "OptionalSolverExportSummaryViewModel",
    "build_optional_solver_export_summary_payload",
    "build_optional_solver_export_summary_viewmodel",
    "explain_optional_solver_export_summary",
    "plan_optional_solver_export_summary_save",
    "render_optional_solver_export_summary_json",
    "render_optional_solver_export_summary_markdown",
    "render_optional_solver_export_summary_text",
]
