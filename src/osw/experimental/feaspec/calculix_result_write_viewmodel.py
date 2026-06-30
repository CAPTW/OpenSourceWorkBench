"""UI-agnostic FEASpec CalculiX ResultDataset write view-model.

The view-model turns existing result-import, write-plan, schema-payload, and
optional writer-result records into deterministic state objects for a future
GUI. It does not import Qt/PySide, open file dialogs, invoke the writer, write
files, execute solvers, or mutate ProjectSchema records.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import PurePath
from typing import Any


class FEASpecCalculiXResultWritePanel(str, Enum):
    """Stable future ResultDataset write panel identifiers."""

    SOURCE_RESULT_DIRECTORY = "source_result_directory"
    ARTIFACT_SUMMARY = "artifact_summary"
    DIAGNOSTICS = "diagnostics"
    DRAFT_MAPPING = "draft_mapping"
    WRITE_PLAN = "write_plan"
    SCHEMA_MANIFEST = "schema_manifest"
    SAFETY_LIMITATIONS = "safety_limitations"
    WRITE_ACTIONS = "write_actions"
    WRITE_RESULT = "write_result"


class FEASpecCalculiXResultWriteAction(str, Enum):
    """Stable future ResultDataset write action identifiers."""

    PREVIEW_IMPORT = "preview_import"
    PREVIEW_DRAFT_MAPPING = "preview_draft_mapping"
    PREVIEW_WRITE_PLAN = "preview_write_plan"
    PREVIEW_SCHEMA = "preview_schema"
    CHOOSE_OUTPUT_DIRECTORY = "choose_output_directory"
    ACKNOWLEDGE_LIMITATIONS = "acknowledge_limitations"
    ACKNOWLEDGE_REVIEW_REQUIRED = "acknowledge_review_required"
    ACKNOWLEDGE_OVERWRITE = "acknowledge_overwrite"
    ACKNOWLEDGE_CREATE_DIR = "acknowledge_create_dir"
    WRITE_RESULT_DATASET = "write_result_dataset"
    OPEN_WRITTEN_OUTPUT = "open_written_output"


class FEASpecCalculiXResultWriteActionState(str, Enum):
    """Action state values for a future GUI binding."""

    HIDDEN = "hidden"
    DISABLED = "disabled"
    ENABLED = "enabled"
    COMPLETED = "completed"
    FAILED = "failed"


class FEASpecCalculiXResultWriteDisabledReason(str, Enum):
    """Machine-readable reasons an action is not available."""

    MISSING_RESULT_DIR = "missing_result_dir"
    MISSING_OUTPUT_DIR = "missing_output_dir"
    IMPORT_PLAN_BLOCKED = "import_plan_blocked"
    WRITE_PLAN_BLOCKED = "write_plan_blocked"
    SCHEMA_BLOCKED = "schema_blocked"
    MISSING_LIMITATIONS_ACKNOWLEDGEMENT = "missing_limitations_acknowledgement"
    MISSING_REVIEW_ACKNOWLEDGEMENT = "missing_review_acknowledgement"
    OVERWRITE_REQUIRED = "overwrite_required"
    CREATE_DIR_REQUIRED = "create_dir_required"
    UNSAFE_PATH = "unsafe_path"
    WRITER_FAILED = "writer_failed"
    WRITE_NOT_AVAILABLE = "write_not_available"


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultWriteAcknowledgementState:
    """Acknowledgement state for future write enablement."""

    limitations: bool = False
    review_required: bool = False
    overwrite: bool = False
    create_dir: bool = False

    def to_dict(self) -> dict[str, bool]:
        return {
            "limitations": self.limitations,
            "review_required": self.review_required,
            "overwrite": self.overwrite,
            "create_dir": self.create_dir,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultWriteRow:
    """Flattened row for a future GUI table or summary panel."""

    panel: FEASpecCalculiXResultWritePanel
    label: str
    value: str = ""
    severity: str = ""
    details: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "panel": self.panel.value,
            "label": self.label,
            "value": self.value,
            "severity": self.severity,
            "details": list(self.details),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultWriteSafetyMessage:
    """User-visible safety message for a future GUI."""

    code: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultWriteSavePlan:
    """Lexical save-target analysis for the future write action.

    This object performs path-string and existing plan-payload analysis only.
    It never creates directories, checks the filesystem, invokes the writer, or
    writes ResultDataset files.
    """

    path: str = ""
    safe_path: bool = False
    parent_missing: bool = False
    overwrite_required: bool = False
    create_dir_required: bool = False
    unsafe_path: bool = False
    can_select: bool = False
    can_write_target: bool = False
    disabled_reasons: tuple[FEASpecCalculiXResultWriteDisabledReason, ...] = ()
    writes_files: bool = False

    @property
    def disabled_reason(self) -> str:
        return "; ".join(reason.value for reason in self.disabled_reasons)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "safe_path": self.safe_path,
            "parent_missing": self.parent_missing,
            "overwrite_required": self.overwrite_required,
            "create_dir_required": self.create_dir_required,
            "unsafe_path": self.unsafe_path,
            "can_select": self.can_select,
            "can_write_target": self.can_write_target,
            "disabled_reasons": [reason.value for reason in self.disabled_reasons],
            "writes_files": self.writes_files,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultWriteActionAvailability:
    """Enablement state and disabled reasons for one future GUI action."""

    action: FEASpecCalculiXResultWriteAction
    state: FEASpecCalculiXResultWriteActionState
    disabled_reasons: tuple[FEASpecCalculiXResultWriteDisabledReason, ...] = ()
    label: str = ""
    safety_note: str = ""

    @property
    def enabled(self) -> bool:
        return self.state is FEASpecCalculiXResultWriteActionState.ENABLED

    @property
    def disabled_reason(self) -> str:
        return "; ".join(reason.value for reason in self.disabled_reasons)

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action.value,
            "state": self.state.value,
            "enabled": self.enabled,
            "disabled_reasons": [reason.value for reason in self.disabled_reasons],
            "label": self.label,
            "safety_note": self.safety_note,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultWriteViewModelInput:
    """Raw records consumed by the write view-model builder."""

    result_dir: str = ""
    output_dir: str = ""
    result_import_plan: object | None = None
    draft_mapping: object | None = None
    write_plan: object | None = None
    schema_payload: object | None = None
    writer_result_summary: object | None = None
    acknowledgements: FEASpecCalculiXResultWriteAcknowledgementState = field(
        default_factory=FEASpecCalculiXResultWriteAcknowledgementState
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "result_dir": self.result_dir,
            "output_dir": self.output_dir,
            "result_import_plan": _to_mapping(self.result_import_plan),
            "draft_mapping": _to_mapping(self.draft_mapping),
            "write_plan": _to_mapping(self.write_plan),
            "schema_payload": _to_mapping(self.schema_payload),
            "writer_result_summary": _to_mapping(self.writer_result_summary),
            "acknowledgements": self.acknowledgements.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultWriteViewModel:
    """Complete UI-agnostic state for a future ResultDataset write GUI."""

    inputs: FEASpecCalculiXResultWriteViewModelInput
    result_dir: str = ""
    output_dir: str = ""
    import_summary: Mapping[str, Any] = field(default_factory=dict)
    draft_mapping_summary: Mapping[str, Any] = field(default_factory=dict)
    write_plan_summary: Mapping[str, Any] = field(default_factory=dict)
    schema_summary: Mapping[str, Any] = field(default_factory=dict)
    writer_result_summary: Mapping[str, Any] = field(default_factory=dict)
    panels: tuple[FEASpecCalculiXResultWritePanel, ...] = ()
    rows: tuple[FEASpecCalculiXResultWriteRow, ...] = ()
    safety_messages: tuple[FEASpecCalculiXResultWriteSafetyMessage, ...] = ()
    actions: tuple[FEASpecCalculiXResultWriteActionAvailability, ...] = ()
    save_plan: FEASpecCalculiXResultWriteSavePlan = field(
        default_factory=FEASpecCalculiXResultWriteSavePlan
    )
    acknowledgements: FEASpecCalculiXResultWriteAcknowledgementState = field(
        default_factory=FEASpecCalculiXResultWriteAcknowledgementState
    )
    write_disabled_reasons: tuple[FEASpecCalculiXResultWriteDisabledReason, ...] = ()
    files_written: bool = False
    writer_invoked_by_viewmodel: bool = False
    gui_dialog_implemented: bool = False
    file_dialog_implemented: bool = False
    solver_execution_performed: bool = False
    artifact_copy_performed: bool = False
    projectschema_mutation_performed: bool = False

    def action_for(
        self,
        action: FEASpecCalculiXResultWriteAction | str,
    ) -> FEASpecCalculiXResultWriteActionAvailability:
        desired = _write_action(action)
        for availability in self.actions:
            if availability.action is desired:
                return availability
        return FEASpecCalculiXResultWriteActionAvailability(
            action=desired,
            state=FEASpecCalculiXResultWriteActionState.HIDDEN,
            disabled_reasons=(
                FEASpecCalculiXResultWriteDisabledReason.WRITE_NOT_AVAILABLE,
            ),
        )

    def rows_for(
        self,
        panel: FEASpecCalculiXResultWritePanel | str,
    ) -> tuple[FEASpecCalculiXResultWriteRow, ...]:
        desired = _write_panel(panel)
        return tuple(row for row in self.rows if row.panel is desired)

    def to_dict(self) -> dict[str, object]:
        return {
            "result_dir": self.result_dir,
            "output_dir": self.output_dir,
            "import_summary": dict(self.import_summary),
            "draft_mapping_summary": dict(self.draft_mapping_summary),
            "write_plan_summary": dict(self.write_plan_summary),
            "schema_summary": dict(self.schema_summary),
            "writer_result_summary": dict(self.writer_result_summary),
            "panels": [panel.value for panel in self.panels],
            "rows": [row.to_dict() for row in self.rows],
            "safety_messages": [
                message.to_dict() for message in self.safety_messages
            ],
            "actions": [action.to_dict() for action in self.actions],
            "save_plan": self.save_plan.to_dict(),
            "acknowledgements": self.acknowledgements.to_dict(),
            "write_disabled_reasons": [
                reason.value for reason in self.write_disabled_reasons
            ],
            "files_written": self.files_written,
            "writer_invoked_by_viewmodel": self.writer_invoked_by_viewmodel,
            "gui_dialog_implemented": self.gui_dialog_implemented,
            "file_dialog_implemented": self.file_dialog_implemented,
            "solver_execution_performed": self.solver_execution_performed,
            "artifact_copy_performed": self.artifact_copy_performed,
            "projectschema_mutation_performed": self.projectschema_mutation_performed,
        }


def build_calculix_result_write_viewmodel(
    result_import_plan: object | None = None,
    *,
    draft_mapping: object | None = None,
    write_plan: object | None = None,
    schema_payload: object | None = None,
    writer_result_summary: object | None = None,
    result_dir: str = "",
    output_dir: str = "",
    acknowledgements: FEASpecCalculiXResultWriteAcknowledgementState
    | Mapping[str, Any]
    | None = None,
) -> FEASpecCalculiXResultWriteViewModel:
    """Build a pure state model for a future ResultDataset write GUI."""

    ack = _acknowledgement_state(acknowledgements)
    import_summary = _import_summary(result_import_plan)
    draft_summary = _draft_mapping_summary(draft_mapping)
    write_summary = _write_plan_summary(write_plan)
    schema_summary = _schema_payload_summary(schema_payload)
    writer_summary = _writer_result_summary(writer_result_summary)
    resolved_result_dir = result_dir or str(import_summary.get("result_dir", ""))
    resolved_output_dir = output_dir or str(write_summary.get("output_dir", ""))
    save_plan = _save_plan(
        resolved_output_dir,
        write_plan_payload=_to_mapping(write_plan),
        acknowledgements=ack,
    )
    disabled_reasons = _write_disabled_reasons(
        result_dir=resolved_result_dir,
        output_dir=resolved_output_dir,
        import_summary=import_summary,
        write_summary=write_summary,
        schema_summary=schema_summary,
        writer_summary=writer_summary,
        save_plan=save_plan,
        acknowledgements=ack,
    )
    inputs = FEASpecCalculiXResultWriteViewModelInput(
        result_dir=resolved_result_dir,
        output_dir=resolved_output_dir,
        result_import_plan=result_import_plan,
        draft_mapping=draft_mapping,
        write_plan=write_plan,
        schema_payload=schema_payload,
        writer_result_summary=writer_result_summary,
        acknowledgements=ack,
    )
    files_written = _writer_completed(writer_summary)
    viewmodel = FEASpecCalculiXResultWriteViewModel(
        inputs=inputs,
        result_dir=resolved_result_dir,
        output_dir=resolved_output_dir,
        import_summary=import_summary,
        draft_mapping_summary=draft_summary,
        write_plan_summary=write_summary,
        schema_summary=schema_summary,
        writer_result_summary=writer_summary,
        panels=_panels(writer_summary),
        rows=_rows(
            import_summary=import_summary,
            draft_summary=draft_summary,
            write_summary=write_summary,
            schema_summary=schema_summary,
            writer_summary=writer_summary,
        ),
        safety_messages=_safety_messages(draft_summary, schema_summary),
        save_plan=save_plan,
        acknowledgements=ack,
        write_disabled_reasons=disabled_reasons,
        files_written=files_written,
    )
    return replace(
        viewmodel,
        actions=tuple(evaluate_calculix_result_write_actions(viewmodel)),
    )


def evaluate_calculix_result_write_actions(
    viewmodel: FEASpecCalculiXResultWriteViewModel,
) -> list[FEASpecCalculiXResultWriteActionAvailability]:
    """Return future GUI action states without invoking the writer."""

    disabled = viewmodel.write_disabled_reasons
    writer_failed = FEASpecCalculiXResultWriteDisabledReason.WRITER_FAILED in disabled
    write_state = FEASpecCalculiXResultWriteActionState.ENABLED
    if viewmodel.files_written:
        write_state = FEASpecCalculiXResultWriteActionState.COMPLETED
    elif writer_failed:
        write_state = FEASpecCalculiXResultWriteActionState.FAILED
    elif disabled:
        write_state = FEASpecCalculiXResultWriteActionState.DISABLED

    return [
        _action(
            FEASpecCalculiXResultWriteAction.PREVIEW_IMPORT,
            _enabled_if(bool(viewmodel.import_summary)),
            label="Preview import",
        ),
        _action(
            FEASpecCalculiXResultWriteAction.PREVIEW_DRAFT_MAPPING,
            _enabled_if(bool(viewmodel.draft_mapping_summary)),
            label="Preview draft mapping",
        ),
        _action(
            FEASpecCalculiXResultWriteAction.PREVIEW_WRITE_PLAN,
            _enabled_if(bool(viewmodel.write_plan_summary)),
            label="Preview write plan",
        ),
        _action(
            FEASpecCalculiXResultWriteAction.PREVIEW_SCHEMA,
            _enabled_if(bool(viewmodel.schema_summary)),
            label="Preview schema",
        ),
        _action(
            FEASpecCalculiXResultWriteAction.CHOOSE_OUTPUT_DIRECTORY,
            FEASpecCalculiXResultWriteActionState.ENABLED,
            label="Choose output directory",
            safety_note="Path selection updates state only; no files are written.",
        ),
        _ack_action(
            FEASpecCalculiXResultWriteAction.ACKNOWLEDGE_LIMITATIONS,
            viewmodel.acknowledgements.limitations,
        ),
        _ack_action(
            FEASpecCalculiXResultWriteAction.ACKNOWLEDGE_REVIEW_REQUIRED,
            viewmodel.acknowledgements.review_required,
        ),
        _ack_action(
            FEASpecCalculiXResultWriteAction.ACKNOWLEDGE_OVERWRITE,
            viewmodel.acknowledgements.overwrite,
            visible=viewmodel.save_plan.overwrite_required,
        ),
        _ack_action(
            FEASpecCalculiXResultWriteAction.ACKNOWLEDGE_CREATE_DIR,
            viewmodel.acknowledgements.create_dir,
            visible=viewmodel.save_plan.create_dir_required,
        ),
        _action(
            FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET,
            write_state,
            disabled_reasons=disabled,
            label="Write ResultDataset",
            safety_note="The view-model never invokes the writer.",
        ),
        _action(
            FEASpecCalculiXResultWriteAction.OPEN_WRITTEN_OUTPUT,
            (
                FEASpecCalculiXResultWriteActionState.ENABLED
                if viewmodel.files_written
                else FEASpecCalculiXResultWriteActionState.DISABLED
            ),
            disabled_reasons=(
                ()
                if viewmodel.files_written
                else (FEASpecCalculiXResultWriteDisabledReason.WRITE_NOT_AVAILABLE,)
            ),
            label="Open written output",
        ),
    ]


def preview_calculix_result_write_record(
    viewmodel: FEASpecCalculiXResultWriteViewModel,
) -> dict[str, object]:
    """Return a JSON-serializable preview record for the future GUI."""

    payload = viewmodel.to_dict()
    payload["viewmodel_only"] = True
    payload["writes_files"] = False
    payload["writer_invoked_by_viewmodel"] = False
    payload["solver_execution_performed"] = False
    payload["release_mutation_performed"] = False
    payload["issue_mutation_performed"] = False
    payload["tag_mutation_performed"] = False
    return payload


def plan_calculix_result_write_save_path(
    viewmodel: FEASpecCalculiXResultWriteViewModel,
    path: str,
) -> FEASpecCalculiXResultWriteSavePlan:
    """Analyze a pending output path without touching the filesystem."""

    return _save_plan(
        path,
        write_plan_payload=_to_mapping(viewmodel.inputs.write_plan),
        acknowledgements=viewmodel.acknowledgements,
    )


def explain_calculix_result_write_viewmodel(
    viewmodel: FEASpecCalculiXResultWriteViewModel,
) -> list[str]:
    """Return reviewer-readable view-model status and action state."""

    lines = [
        "FEASpec CalculiX ResultDataset write view-model: ready.",
        f"Result directory: {viewmodel.result_dir or '<missing>'}.",
        f"Output directory: {viewmodel.output_dir or '<missing>'}.",
        f"Import status: {viewmodel.import_summary.get('status', '')}.",
        f"Draft mapping status: {viewmodel.draft_mapping_summary.get('status', '')}.",
        f"Write plan status: {viewmodel.write_plan_summary.get('status', '')}.",
        f"Schema status: {viewmodel.schema_summary.get('status', '')}.",
        f"Files written by view-model: {str(viewmodel.files_written).lower()}.",
        "Writer invoked by view-model: false.",
        "Solver execution performed: false.",
    ]
    for action in viewmodel.actions:
        reason = f" ({action.disabled_reason})" if action.disabled_reasons else ""
        lines.append(f"- {action.action.value}: {action.state.value}{reason}")
    for message in viewmodel.safety_messages:
        lines.append(f"{message.severity.upper()} {message.code}: {message.message}")
    return lines


def _panels(
    writer_summary: Mapping[str, Any],
) -> tuple[FEASpecCalculiXResultWritePanel, ...]:
    panels = [
        FEASpecCalculiXResultWritePanel.SOURCE_RESULT_DIRECTORY,
        FEASpecCalculiXResultWritePanel.ARTIFACT_SUMMARY,
        FEASpecCalculiXResultWritePanel.DIAGNOSTICS,
        FEASpecCalculiXResultWritePanel.DRAFT_MAPPING,
        FEASpecCalculiXResultWritePanel.WRITE_PLAN,
        FEASpecCalculiXResultWritePanel.SCHEMA_MANIFEST,
        FEASpecCalculiXResultWritePanel.SAFETY_LIMITATIONS,
        FEASpecCalculiXResultWritePanel.WRITE_ACTIONS,
    ]
    if writer_summary:
        panels.append(FEASpecCalculiXResultWritePanel.WRITE_RESULT)
    return tuple(panels)


def _rows(
    *,
    import_summary: Mapping[str, Any],
    draft_summary: Mapping[str, Any],
    write_summary: Mapping[str, Any],
    schema_summary: Mapping[str, Any],
    writer_summary: Mapping[str, Any],
) -> tuple[FEASpecCalculiXResultWriteRow, ...]:
    rows: list[FEASpecCalculiXResultWriteRow] = [
        FEASpecCalculiXResultWriteRow(
            FEASpecCalculiXResultWritePanel.SOURCE_RESULT_DIRECTORY,
            "result_dir",
            str(import_summary.get("result_dir", "")),
        ),
        FEASpecCalculiXResultWriteRow(
            FEASpecCalculiXResultWritePanel.SOURCE_RESULT_DIRECTORY,
            "import_status",
            str(import_summary.get("status", "")),
        ),
        FEASpecCalculiXResultWriteRow(
            FEASpecCalculiXResultWritePanel.ARTIFACT_SUMMARY,
            "artifact_count",
            str(import_summary.get("artifact_count", 0)),
        ),
        FEASpecCalculiXResultWriteRow(
            FEASpecCalculiXResultWritePanel.DRAFT_MAPPING,
            "dataset_id",
            str(draft_summary.get("dataset_id", "")),
        ),
        FEASpecCalculiXResultWriteRow(
            FEASpecCalculiXResultWritePanel.DRAFT_MAPPING,
            "draft_status",
            str(draft_summary.get("status", "")),
        ),
        FEASpecCalculiXResultWriteRow(
            FEASpecCalculiXResultWritePanel.WRITE_PLAN,
            "output_dir",
            str(write_summary.get("output_dir", "")),
        ),
        FEASpecCalculiXResultWriteRow(
            FEASpecCalculiXResultWritePanel.WRITE_PLAN,
            "planned_files",
            str(write_summary.get("planned_file_count", 0)),
        ),
        FEASpecCalculiXResultWriteRow(
            FEASpecCalculiXResultWritePanel.SCHEMA_MANIFEST,
            "schema",
            str(schema_summary.get("schema", "")),
        ),
        FEASpecCalculiXResultWriteRow(
            FEASpecCalculiXResultWritePanel.SCHEMA_MANIFEST,
            "schema_status",
            str(schema_summary.get("status", "")),
        ),
    ]
    for diagnostic in _all_diagnostics(import_summary, write_summary, schema_summary):
        rows.append(
            FEASpecCalculiXResultWriteRow(
                FEASpecCalculiXResultWritePanel.DIAGNOSTICS,
                str(diagnostic.get("code", "")),
                str(diagnostic.get("message", "")),
                severity=str(diagnostic.get("severity", "")),
                metadata=dict(diagnostic),
            )
        )
    for limitation in draft_summary.get("limitations", ()):
        rows.append(
            FEASpecCalculiXResultWriteRow(
                FEASpecCalculiXResultWritePanel.SAFETY_LIMITATIONS,
                "limitation",
                str(limitation),
            )
        )
    if writer_summary:
        rows.append(
            FEASpecCalculiXResultWriteRow(
                FEASpecCalculiXResultWritePanel.WRITE_RESULT,
                "writer_status",
                str(writer_summary.get("status", "")),
            )
        )
        rows.append(
            FEASpecCalculiXResultWriteRow(
                FEASpecCalculiXResultWritePanel.WRITE_RESULT,
                "written_files",
                str(writer_summary.get("written_file_count", 0)),
            )
        )
    return tuple(rows)


def _safety_messages(
    draft_summary: Mapping[str, Any],
    schema_summary: Mapping[str, Any],
) -> tuple[FEASpecCalculiXResultWriteSafetyMessage, ...]:
    messages = [
        FEASpecCalculiXResultWriteSafetyMessage(
            "FWVM_VIEWMODEL_ONLY",
            "This layer computes GUI state only; it does not call the writer.",
        ),
        FEASpecCalculiXResultWriteSafetyMessage(
            "FWVM_NO_FILE_DIALOG",
            "No PySide, Qt, file chooser, or GUI command is implemented here.",
        ),
        FEASpecCalculiXResultWriteSafetyMessage(
            "FWVM_NO_SOLVER_EXECUTION",
            "No CalculiX execution or external command path exists.",
        ),
        FEASpecCalculiXResultWriteSafetyMessage(
            "FWVM_REVIEW_REQUIRED",
            "Written ResultDataset files require human review first.",
        ),
        FEASpecCalculiXResultWriteSafetyMessage(
            "FWVM_ISSUE_8_OPEN",
            "Issue #8 live CalculiX validation remains separate and open.",
        ),
    ]
    if draft_summary.get("limitations") or schema_summary.get("limitations_count", 0):
        messages.append(
            FEASpecCalculiXResultWriteSafetyMessage(
                "FWVM_LIMITATIONS_ACK_REQUIRED",
                "Parser/import limitations must be acknowledged before writing.",
                severity="warning",
            )
        )
    return tuple(messages)


def _write_disabled_reasons(
    *,
    result_dir: str,
    output_dir: str,
    import_summary: Mapping[str, Any],
    write_summary: Mapping[str, Any],
    schema_summary: Mapping[str, Any],
    writer_summary: Mapping[str, Any],
    save_plan: FEASpecCalculiXResultWriteSavePlan,
    acknowledgements: FEASpecCalculiXResultWriteAcknowledgementState,
) -> tuple[FEASpecCalculiXResultWriteDisabledReason, ...]:
    reasons: list[FEASpecCalculiXResultWriteDisabledReason] = []
    if not result_dir:
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.MISSING_RESULT_DIR)
    if not output_dir:
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.MISSING_OUTPUT_DIR)
    if _blocked_status(import_summary.get("status")) or import_summary.get(
        "has_blockers",
        False,
    ):
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.IMPORT_PLAN_BLOCKED)
    if not write_summary:
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.WRITE_NOT_AVAILABLE)
    elif _blocked_status(write_summary.get("status")) or write_summary.get(
        "has_blockers",
        False,
    ):
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.WRITE_PLAN_BLOCKED)
    if not schema_summary:
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.WRITE_NOT_AVAILABLE)
    elif _blocked_status(schema_summary.get("status")) or schema_summary.get(
        "has_blockers",
        False,
    ):
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.SCHEMA_BLOCKED)
    if not acknowledgements.limitations and _requires_limitations_ack(
        write_summary,
        schema_summary,
    ):
        reasons.append(
            FEASpecCalculiXResultWriteDisabledReason.MISSING_LIMITATIONS_ACKNOWLEDGEMENT
        )
    if not acknowledgements.review_required:
        reasons.append(
            FEASpecCalculiXResultWriteDisabledReason.MISSING_REVIEW_ACKNOWLEDGEMENT
        )
    if (
        save_plan.overwrite_required
        and not acknowledgements.overwrite
        and not _target_overwrite_requested(write_summary)
    ):
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.OVERWRITE_REQUIRED)
    if save_plan.create_dir_required and not acknowledgements.create_dir:
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.CREATE_DIR_REQUIRED)
    if save_plan.unsafe_path:
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.UNSAFE_PATH)
    if _writer_failed(writer_summary):
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.WRITER_FAILED)
    return tuple(_dedupe_reasons(reasons))


def _save_plan(
    path: str,
    *,
    write_plan_payload: Mapping[str, Any],
    acknowledgements: FEASpecCalculiXResultWriteAcknowledgementState,
) -> FEASpecCalculiXResultWriteSavePlan:
    target = _target_payload(write_plan_payload)
    planned_files = _mapping_tuple(write_plan_payload.get("planned_files"))
    selected_path = str(path or target.get("output_dir") or target.get("output_path") or "")
    unsafe = bool(
        target.get("unsafe_path")
        or target.get("traversal_rejected")
        or _path_is_unsafe(selected_path)
    )
    parent_missing = bool(
        selected_path
        and not bool(target.get("target_exists", False))
        and not bool(target.get("parent_exists", True))
    )
    overwrite_required = bool(
        target.get("target_is_file")
        or target.get("target_nonempty")
        or any(item.get("exists") for item in planned_files)
    )
    create_dir_required = bool(target.get("create_dir_planned") or parent_missing)
    reasons: list[FEASpecCalculiXResultWriteDisabledReason] = []
    if not selected_path:
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.MISSING_OUTPUT_DIR)
    if unsafe:
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.UNSAFE_PATH)
    if overwrite_required and not acknowledgements.overwrite and not bool(
        target.get("overwrite_requested", False)
    ):
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.OVERWRITE_REQUIRED)
    if create_dir_required and not acknowledgements.create_dir:
        reasons.append(FEASpecCalculiXResultWriteDisabledReason.CREATE_DIR_REQUIRED)
    safe_path = bool(selected_path) and not unsafe
    return FEASpecCalculiXResultWriteSavePlan(
        path=selected_path,
        safe_path=safe_path,
        parent_missing=parent_missing,
        overwrite_required=overwrite_required,
        create_dir_required=create_dir_required,
        unsafe_path=unsafe,
        can_select=safe_path,
        can_write_target=safe_path and not reasons,
        disabled_reasons=tuple(_dedupe_reasons(reasons)),
    )


def _import_summary(plan: object | None) -> Mapping[str, Any]:
    payload = _to_mapping(plan)
    if not payload:
        return {}
    artifacts = _mapping_tuple(payload.get("artifacts"))
    return {
        "status": str(payload.get("status", "")),
        "result_dir": str(payload.get("result_dir", "")),
        "artifact_count": len(artifacts),
        "diagnostics": _diagnostic_tuple(payload.get("diagnostics")),
        "limitations": _string_tuple(payload.get("limitations")),
        "has_blockers": _has_blockers(payload.get("diagnostics")),
    }


def _draft_mapping_summary(mapping: object | None) -> Mapping[str, Any]:
    payload = _to_mapping(mapping)
    if not payload:
        return {}
    return {
        "status": str(payload.get("status", "")),
        "dataset_id": str(payload.get("dataset_id", "")),
        "source": str(payload.get("source", "")),
        "artifact_count": len(_mapping_tuple(payload.get("artifacts"))),
        "scalar_count": len(_mapping_tuple(payload.get("scalar_candidates"))),
        "table_count": len(_mapping_tuple(payload.get("table_candidates"))),
        "field_reference_count": len(_mapping_tuple(payload.get("field_references"))),
        "diagnostics": _diagnostic_tuple(payload.get("diagnostics")),
        "limitations": _string_tuple(payload.get("limitations")),
    }


def _write_plan_summary(plan: object | None) -> Mapping[str, Any]:
    payload = _to_mapping(plan)
    if not payload:
        return {}
    target = _target_payload(payload)
    diagnostics = _diagnostic_tuple(payload.get("diagnostics"))
    return {
        "status": str(payload.get("status", "")),
        "output_dir": str(target.get("output_dir", "")),
        "target": target,
        "planned_file_count": len(_mapping_tuple(payload.get("planned_files"))),
        "artifact_reference_count": len(
            _mapping_tuple(payload.get("artifact_references"))
        ),
        "limitations_acknowledged": bool(payload.get("limitations_acknowledged")),
        "copy_artifacts_requested": bool(payload.get("copy_artifacts_requested")),
        "diagnostics": diagnostics,
        "has_blockers": _has_blockers(diagnostics),
    }


def _schema_payload_summary(payload_obj: object | None) -> Mapping[str, Any]:
    payload = _to_mapping(payload_obj)
    if not payload:
        return {}
    schema = _to_mapping(payload.get("schema"))
    diagnostics = _diagnostic_tuple(payload.get("schema_diagnostics"))
    return {
        "status": str(payload.get("status", "")),
        "schema": " ".join(
            item
            for item in (
                str(schema.get("schema_name", "")),
                str(schema.get("schema_version", "")),
            )
            if item
        ),
        "dataset_id": str(_to_mapping(payload.get("dataset")).get("dataset_id", "")),
        "planned_file_count": len(_mapping_tuple(payload.get("planned_files"))),
        "limitations_count": len(_mapping_tuple(payload.get("limitations"))),
        "diagnostics": diagnostics,
        "has_blockers": _has_blockers(diagnostics),
        "writes_files": bool(payload.get("writes_files", False)),
        "result_dataset_persistence": bool(
            payload.get("result_dataset_persistence", False)
        ),
    }


def _writer_result_summary(result: object | None) -> Mapping[str, Any]:
    payload = _to_mapping(result)
    if not payload:
        return {}
    written_files = _mapping_tuple(payload.get("written_files"))
    return {
        "status": str(payload.get("status", "")),
        "target_dir": str(payload.get("target_dir", "")),
        "written_file_count": len(written_files),
        "written_files": written_files,
        "diagnostics": _diagnostic_tuple(payload.get("diagnostics")),
        "solver_execution_performed": bool(
            payload.get("solver_execution_performed", False)
        ),
        "artifact_copy_performed": bool(payload.get("artifact_copy_performed", False)),
        "gui_write_command_added": bool(payload.get("gui_write_command_added", False)),
    }


def _target_payload(write_plan_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return _to_mapping(write_plan_payload.get("target"))


def _all_diagnostics(
    *summaries: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    diagnostics: list[Mapping[str, Any]] = []
    for summary in summaries:
        diagnostics.extend(_diagnostic_tuple(summary.get("diagnostics")))
    return tuple(_dedupe_mappings(diagnostics))


def _acknowledgement_state(
    value: FEASpecCalculiXResultWriteAcknowledgementState | Mapping[str, Any] | None,
) -> FEASpecCalculiXResultWriteAcknowledgementState:
    if isinstance(value, FEASpecCalculiXResultWriteAcknowledgementState):
        return value
    if isinstance(value, Mapping):
        return FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=bool(value.get("limitations")),
            review_required=bool(value.get("review_required")),
            overwrite=bool(value.get("overwrite")),
            create_dir=bool(value.get("create_dir")),
        )
    return FEASpecCalculiXResultWriteAcknowledgementState()


def _action(
    action: FEASpecCalculiXResultWriteAction,
    state: FEASpecCalculiXResultWriteActionState,
    *,
    disabled_reasons: Sequence[FEASpecCalculiXResultWriteDisabledReason] = (),
    label: str = "",
    safety_note: str = "",
) -> FEASpecCalculiXResultWriteActionAvailability:
    return FEASpecCalculiXResultWriteActionAvailability(
        action=action,
        state=state,
        disabled_reasons=tuple(disabled_reasons),
        label=label,
        safety_note=safety_note,
    )


def _ack_action(
    action: FEASpecCalculiXResultWriteAction,
    completed: bool,
    *,
    visible: bool = True,
) -> FEASpecCalculiXResultWriteActionAvailability:
    if not visible:
        return _action(action, FEASpecCalculiXResultWriteActionState.HIDDEN)
    return _action(
        action,
        (
            FEASpecCalculiXResultWriteActionState.COMPLETED
            if completed
            else FEASpecCalculiXResultWriteActionState.ENABLED
        ),
    )


def _enabled_if(value: bool) -> FEASpecCalculiXResultWriteActionState:
    return (
        FEASpecCalculiXResultWriteActionState.ENABLED
        if value
        else FEASpecCalculiXResultWriteActionState.DISABLED
    )


def _requires_limitations_ack(
    write_summary: Mapping[str, Any],
    schema_summary: Mapping[str, Any],
) -> bool:
    if bool(write_summary.get("limitations_acknowledged")):
        return False
    return bool(
        schema_summary.get("limitations_count", 0)
        or _has_code(write_summary.get("diagnostics"), "FDW_LIMITATIONS_NOT_ACKNOWLEDGED")
    )


def _blocked_status(value: object) -> bool:
    text = str(getattr(value, "value", value) or "").casefold()
    return text in {"blocked", "unsupported", "failed", "partial-cleanup-failed"}


def _target_overwrite_requested(write_summary: Mapping[str, Any]) -> bool:
    target = _to_mapping(write_summary.get("target"))
    return bool(target.get("overwrite_requested", False))


def _writer_completed(writer_summary: Mapping[str, Any]) -> bool:
    return str(writer_summary.get("status", "")).casefold() in {
        "written",
        "written-with-warnings",
        "completed",
    }


def _writer_failed(writer_summary: Mapping[str, Any]) -> bool:
    return str(writer_summary.get("status", "")).casefold() in {
        "failed",
        "partial-cleanup-failed",
    }


def _path_is_unsafe(path: str) -> bool:
    if not path:
        return False
    parts = {part.casefold() for part in PurePath(path).parts}
    return bool(parts.intersection({".git", ".codex"}) or ".." in parts)


def _has_blockers(value: object) -> bool:
    return any(
        bool(
            item.get("blocks_write")
            or item.get("blocks_payload")
            or item.get("blocks_import")
            or item.get("blocks_mapping")
        )
        for item in _diagnostic_tuple(value)
    )


def _has_code(value: object, code: str) -> bool:
    return any(str(item.get("code", "")) == code for item in _diagnostic_tuple(value))


def _diagnostic_tuple(value: object) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        dict(item)
        for item in _mapping_tuple(value)
        if "code" in item or "message" in item or "severity" in item
    )


def _mapping_tuple(value: object) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, Mapping):
        return (dict(value),)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    records: list[Mapping[str, Any]] = []
    for item in value:
        mapping = _to_mapping(item)
        if mapping:
            records.append(mapping)
    return tuple(records)


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if not isinstance(value, Sequence) or isinstance(value, bytes):
        return ()
    return tuple(str(item) for item in value if str(item))


def _to_mapping(value: object) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    return {}


def _dedupe_reasons(
    reasons: Sequence[FEASpecCalculiXResultWriteDisabledReason],
) -> list[FEASpecCalculiXResultWriteDisabledReason]:
    seen: set[FEASpecCalculiXResultWriteDisabledReason] = set()
    unique: list[FEASpecCalculiXResultWriteDisabledReason] = []
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        unique.append(reason)
    return unique


def _dedupe_mappings(
    records: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[Mapping[str, Any]] = []
    for record in records:
        key = (
            str(record.get("code", "")),
            str(record.get("path", "")),
            str(record.get("message", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(record))
    return unique


def _write_action(
    value: FEASpecCalculiXResultWriteAction | str,
) -> FEASpecCalculiXResultWriteAction:
    if isinstance(value, FEASpecCalculiXResultWriteAction):
        return value
    return FEASpecCalculiXResultWriteAction(str(value))


def _write_panel(
    value: FEASpecCalculiXResultWritePanel | str,
) -> FEASpecCalculiXResultWritePanel:
    if isinstance(value, FEASpecCalculiXResultWritePanel):
        return value
    return FEASpecCalculiXResultWritePanel(str(value))
