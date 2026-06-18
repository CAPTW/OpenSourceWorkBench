"""UI-agnostic FEASpec human review dialog view-model.

The view-model converts existing human-review evidence into deterministic
state objects that a future GUI can bind to. It does not implement GUI widgets,
write files, call solvers, or perform external command execution.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .human_review import (
    AcceptedWarning,
    DiagnosticDecision,
    FEASpecHumanReviewRecord,
    HumanReviewAction,
    ReviewDiagnosticReference,
    create_human_review_record,
    summarize_human_review_record,
    validate_human_review_record,
)

_BLOCKING_SEVERITIES = {"blocker", "error"}


class HumanReviewDialogPanel(str, Enum):
    """Stable future dialog panel identifiers."""

    SOURCE_EVIDENCE = "source_evidence"
    DIAGNOSTICS = "diagnostics"
    ENGINEERING_SUMMARY = "engineering_summary"
    EXPORT_PREVIEW = "export_preview"
    REVIEW_ACTIONS = "review_actions"
    SAFETY_LIMITATIONS = "safety_limitations"
    RECORD_PREVIEW = "record_preview"


class HumanReviewDialogAction(str, Enum):
    """Stable future dialog action identifiers."""

    MARK_NEEDS_CHANGES = "mark_needs_changes"
    REJECT = "reject"
    APPROVE_NO_RUN_EXPORT = "approve_no_run_export"
    REQUEST_INSTALLED_ONLY_RUN = "request_installed_only_run"
    ACCEPT_WARNING = "accept_warning"
    REJECT_DIAGNOSTIC = "reject_diagnostic"
    PREVIEW_RECORD = "preview_record"
    SAVE_RECORD = "save_record"


@dataclass(frozen=True, slots=True)
class HumanReviewActionAvailability:
    """Enablement state and disabled reasons for one future dialog action."""

    action: HumanReviewDialogAction
    enabled: bool
    disabled_reasons: tuple[str, ...] = ()

    @property
    def disabled_reason(self) -> str:
        return "; ".join(self.disabled_reasons)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "enabled": self.enabled,
            "disabled_reasons": list(self.disabled_reasons),
        }


@dataclass(frozen=True, slots=True)
class HumanReviewDialogDiagnosticRow:
    """Flattened diagnostic row for a future GUI table."""

    source: str
    severity: str
    code: str
    message: str = ""
    target_ref: str = ""
    blocks_approval: bool = False
    blocks_solver_handoff: bool = False
    accept_away_eligible: bool = False

    @property
    def is_blocker(self) -> bool:
        return (
            self.severity.casefold() in _BLOCKING_SEVERITIES
            or self.blocks_approval
            or self.blocks_solver_handoff
        )

    @property
    def is_warning(self) -> bool:
        return self.severity.casefold() == "warning"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "target_ref": self.target_ref,
            "blocks_approval": self.blocks_approval,
            "blocks_solver_handoff": self.blocks_solver_handoff,
            "accept_away_eligible": self.accept_away_eligible,
        }


@dataclass(frozen=True, slots=True)
class HumanReviewDialogWarningRow:
    """Warning acceptance state for one non-blocking diagnostic."""

    diagnostic: HumanReviewDialogDiagnosticRow
    reason: str = ""
    accepted: bool = False
    acceptance_required: bool = True

    @property
    def requires_reason(self) -> bool:
        return self.acceptance_required and not self.reason.strip()

    @property
    def can_accept(self) -> bool:
        return self.diagnostic.accept_away_eligible and bool(self.reason.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagnostic": self.diagnostic.to_dict(),
            "reason": self.reason,
            "accepted": self.accepted,
            "acceptance_required": self.acceptance_required,
            "requires_reason": self.requires_reason,
            "can_accept": self.can_accept,
        }


@dataclass(frozen=True, slots=True)
class HumanReviewRecordPreview:
    """In-memory preview of the record the future dialog would save."""

    state: str
    action: str
    source_feaspec_id: str
    reviewer: str
    reviewed_at: str
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    summary: dict[str, Any] = field(default_factory=dict)
    json_payload: dict[str, Any] = field(default_factory=dict)
    solver_execution_performed: bool = False
    solver_execution_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "action": self.action,
            "source_feaspec_id": self.source_feaspec_id,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "summary": dict(self.summary),
            "json_payload": dict(self.json_payload),
            "solver_execution_performed": self.solver_execution_performed,
            "solver_execution_authorized": self.solver_execution_authorized,
        }


@dataclass(frozen=True, slots=True)
class HumanReviewSavePlan:
    """Path analysis for a future explicit save action.

    This is path analysis only. It never creates directories and never writes
    review records.
    """

    path: str = ""
    safe_path: bool = False
    parent_missing: bool = False
    overwrite_required: bool = False
    can_save: bool = False
    disabled_reasons: tuple[str, ...] = ()

    @property
    def disabled_reason(self) -> str:
        return "; ".join(self.disabled_reasons)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "safe_path": self.safe_path,
            "parent_missing": self.parent_missing,
            "overwrite_required": self.overwrite_required,
            "can_save": self.can_save,
            "disabled_reasons": list(self.disabled_reasons),
        }


@dataclass(frozen=True, slots=True)
class HumanReviewDialogState:
    """Complete UI-agnostic state for a future human-review dialog."""

    source_feaspec_id: str = ""
    reviewer: str = ""
    reviewed_at: str = ""
    desired_action: HumanReviewDialogAction = HumanReviewDialogAction.MARK_NEEDS_CHANGES
    panels: tuple[HumanReviewDialogPanel, ...] = ()
    diagnostics: tuple[HumanReviewDialogDiagnosticRow, ...] = ()
    warnings: tuple[HumanReviewDialogWarningRow, ...] = ()
    actions: tuple[HumanReviewActionAvailability, ...] = ()
    record_preview: HumanReviewRecordPreview | None = None
    save_plan: HumanReviewSavePlan = field(default_factory=HumanReviewSavePlan)
    notes: tuple[str, ...] = ()
    validator_summary: dict[str, Any] = field(default_factory=dict)
    validator_report_hash: str = ""
    bridge_summary: dict[str, Any] = field(default_factory=dict)
    case_plan_summary: dict[str, Any] = field(default_factory=dict)
    export_preview_summary: dict[str, Any] = field(default_factory=dict)
    export_write_summary: dict[str, Any] = field(default_factory=dict)
    limitations_acknowledged: bool = False
    no_run_export_review_acknowledged: bool = False
    run_gate_separation_acknowledged: bool = False

    def availability_for(
        self,
        action: HumanReviewDialogAction | str,
    ) -> HumanReviewActionAvailability:
        dialog_action = _dialog_action(action)
        for availability in self.actions:
            if availability.action is dialog_action:
                return availability
        return HumanReviewActionAvailability(
            dialog_action,
            enabled=False,
            disabled_reasons=("action is not present in dialog state",),
        )


def build_human_review_dialog_state(
    record: FEASpecHumanReviewRecord | Mapping[str, Any] | None = None,
    *,
    source_feaspec_id: str = "",
    reviewer: str = "",
    reviewed_at: str = "",
    desired_action: HumanReviewDialogAction | HumanReviewAction | str = (
        HumanReviewDialogAction.MARK_NEEDS_CHANGES
    ),
    notes: Sequence[str] = (),
    validator_summary: Mapping[str, Any] | None = None,
    validator_report_hash: str = "",
    bridge_summary: Mapping[str, Any] | None = None,
    case_plan_summary: Mapping[str, Any] | None = None,
    export_preview_summary: Mapping[str, Any] | None = None,
    export_write_summary: Mapping[str, Any] | None = None,
    accepted_warnings: Sequence[AcceptedWarning | Mapping[str, Any]] = (),
    diagnostic_decisions: Sequence[DiagnosticDecision | Mapping[str, Any]] = (),
    limitations_acknowledged: bool = False,
    no_run_export_review_acknowledged: bool = False,
    run_gate_separation_acknowledged: bool = False,
    save_path: str | Path | None = None,
    overwrite: bool = False,
) -> HumanReviewDialogState:
    """Build deterministic UI-agnostic human-review dialog state."""

    record_obj = _record_or_none(record)
    if record_obj is not None:
        source_feaspec_id = source_feaspec_id or record_obj.source_feaspec_id
        reviewer = reviewer or record_obj.reviewer
        reviewed_at = reviewed_at or record_obj.reviewed_at
        notes = tuple(notes) or record_obj.notes
        validator_summary = validator_summary or record_obj.validator_report_summary
        validator_report_hash = validator_report_hash or record_obj.validator_report_hash
        bridge_summary = bridge_summary or record_obj.bridge_summary
        case_plan_summary = case_plan_summary or record_obj.case_plan_summary
        export_preview_summary = export_preview_summary or record_obj.export_preview_summary
        export_write_summary = export_write_summary or record_obj.export_write_summary
        accepted_warnings = tuple(accepted_warnings) or record_obj.accepted_warnings
        diagnostic_decisions = (
            tuple(diagnostic_decisions) or record_obj.diagnostic_decisions
        )
        limitations_acknowledged = (
            limitations_acknowledged or record_obj.limitations_acknowledged
        )
        no_run_export_review_acknowledged = (
            no_run_export_review_acknowledged
            or record_obj.no_run_export_review_acknowledged
        )
        run_gate_separation_acknowledged = (
            run_gate_separation_acknowledged
            or record_obj.run_gate_separation_acknowledged
        )

    normalized_validator_summary = dict(validator_summary or {})
    normalized_bridge_summary = dict(bridge_summary or {})
    normalized_case_plan_summary = dict(case_plan_summary or {})
    normalized_export_preview_summary = dict(export_preview_summary or {})
    normalized_export_write_summary = dict(export_write_summary or {})
    normalized_action = _dialog_action(desired_action)
    normalized_accepted_warnings = tuple(
        _accepted_warning(item) for item in accepted_warnings
    )
    normalized_diagnostic_decisions = tuple(
        _diagnostic_decision(item) for item in diagnostic_decisions
    )

    diagnostics = _collect_diagnostics(
        validator_summary=normalized_validator_summary,
        bridge_summary=normalized_bridge_summary,
        case_plan_summary=normalized_case_plan_summary,
        export_preview_summary=normalized_export_preview_summary,
        export_write_summary=normalized_export_write_summary,
    )
    warnings = _build_warning_rows(diagnostics, normalized_accepted_warnings)
    save_plan = build_human_review_save_plan(save_path, overwrite=overwrite)
    preview = build_human_review_record_preview(
        source_feaspec_id=source_feaspec_id,
        reviewer=reviewer,
        reviewed_at=reviewed_at,
        desired_action=normalized_action,
        notes=notes,
        accepted_warnings=normalized_accepted_warnings,
        diagnostic_decisions=normalized_diagnostic_decisions,
        validator_summary=normalized_validator_summary,
        validator_report_hash=validator_report_hash,
        bridge_summary=normalized_bridge_summary,
        case_plan_summary=normalized_case_plan_summary,
        export_preview_summary=normalized_export_preview_summary,
        export_write_summary=normalized_export_write_summary,
        limitations_acknowledged=limitations_acknowledged,
        no_run_export_review_acknowledged=no_run_export_review_acknowledged,
        run_gate_separation_acknowledged=run_gate_separation_acknowledged,
    )

    state_without_actions = HumanReviewDialogState(
        source_feaspec_id=source_feaspec_id,
        reviewer=reviewer,
        reviewed_at=reviewed_at,
        desired_action=normalized_action,
        panels=tuple(HumanReviewDialogPanel),
        diagnostics=diagnostics,
        warnings=warnings,
        actions=(),
        record_preview=preview,
        save_plan=save_plan,
        notes=tuple(str(note) for note in notes),
        validator_summary=normalized_validator_summary,
        validator_report_hash=validator_report_hash,
        bridge_summary=normalized_bridge_summary,
        case_plan_summary=normalized_case_plan_summary,
        export_preview_summary=normalized_export_preview_summary,
        export_write_summary=normalized_export_write_summary,
        limitations_acknowledged=limitations_acknowledged,
        no_run_export_review_acknowledged=no_run_export_review_acknowledged,
        run_gate_separation_acknowledged=run_gate_separation_acknowledged,
    )
    return _replace_actions(
        state_without_actions,
        evaluate_human_review_actions(state_without_actions),
    )


def evaluate_human_review_actions(
    state_or_inputs: HumanReviewDialogState | Mapping[str, Any],
) -> tuple[HumanReviewActionAvailability, ...]:
    """Evaluate deterministic action availability for a dialog state."""

    state = (
        state_or_inputs
        if isinstance(state_or_inputs, HumanReviewDialogState)
        else build_human_review_dialog_state(**dict(state_or_inputs))
    )
    common_reasons = _required_identity_reasons(state)
    approval_reasons = (
        common_reasons
        + _validator_evidence_reasons(state)
        + _blocking_reasons(state)
        + _unresolved_warning_reasons(state)
    )
    needs_changes_reasons = common_reasons + _notes_required_reasons(state)
    reject_reasons = common_reasons + _notes_required_reasons(state)
    run_request_reasons = approval_reasons + _run_request_ack_reasons(state)
    accept_warning_reasons = _accept_warning_reasons(state)
    reject_diagnostic_reasons = (
        () if state.diagnostics else ("diagnostic rows are required",)
    )
    preview_reasons = ()
    save_reasons = state.save_plan.disabled_reasons + _record_preview_invalid_reasons(
        state
    )

    return (
        _availability(HumanReviewDialogAction.MARK_NEEDS_CHANGES, needs_changes_reasons),
        _availability(HumanReviewDialogAction.REJECT, reject_reasons),
        _availability(HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT, approval_reasons),
        _availability(
            HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN,
            run_request_reasons,
        ),
        _availability(HumanReviewDialogAction.ACCEPT_WARNING, accept_warning_reasons),
        _availability(HumanReviewDialogAction.REJECT_DIAGNOSTIC, reject_diagnostic_reasons),
        _availability(HumanReviewDialogAction.PREVIEW_RECORD, preview_reasons),
        _availability(HumanReviewDialogAction.SAVE_RECORD, save_reasons),
    )


def build_human_review_record_preview(
    record: FEASpecHumanReviewRecord | Mapping[str, Any] | None = None,
    *,
    source_feaspec_id: str = "",
    reviewer: str = "",
    reviewed_at: str = "",
    desired_action: HumanReviewDialogAction | HumanReviewAction | str = (
        HumanReviewDialogAction.MARK_NEEDS_CHANGES
    ),
    notes: Sequence[str] = (),
    accepted_warnings: Sequence[AcceptedWarning | Mapping[str, Any]] = (),
    diagnostic_decisions: Sequence[DiagnosticDecision | Mapping[str, Any]] = (),
    validator_summary: Mapping[str, Any] | None = None,
    validator_report_hash: str = "",
    bridge_summary: Mapping[str, Any] | None = None,
    case_plan_summary: Mapping[str, Any] | None = None,
    export_preview_summary: Mapping[str, Any] | None = None,
    export_write_summary: Mapping[str, Any] | None = None,
    limitations_acknowledged: bool = False,
    no_run_export_review_acknowledged: bool = False,
    run_gate_separation_acknowledged: bool = False,
) -> HumanReviewRecordPreview:
    """Build an in-memory preview of the review record."""

    record_obj = _record_or_none(record)
    if record_obj is not None:
        source_feaspec_id = source_feaspec_id or record_obj.source_feaspec_id
        reviewer = reviewer or record_obj.reviewer
        reviewed_at = reviewed_at or record_obj.reviewed_at
        desired_action = _dialog_action(record_obj.action)
        notes = tuple(notes) or record_obj.notes
        accepted_warnings = tuple(accepted_warnings) or record_obj.accepted_warnings
        diagnostic_decisions = (
            tuple(diagnostic_decisions) or record_obj.diagnostic_decisions
        )
        validator_summary = validator_summary or record_obj.validator_report_summary
        validator_report_hash = validator_report_hash or record_obj.validator_report_hash
        bridge_summary = bridge_summary or record_obj.bridge_summary
        case_plan_summary = case_plan_summary or record_obj.case_plan_summary
        export_preview_summary = export_preview_summary or record_obj.export_preview_summary
        export_write_summary = export_write_summary or record_obj.export_write_summary
        limitations_acknowledged = (
            limitations_acknowledged or record_obj.limitations_acknowledged
        )
        no_run_export_review_acknowledged = (
            no_run_export_review_acknowledged
            or record_obj.no_run_export_review_acknowledged
        )
        run_gate_separation_acknowledged = (
            run_gate_separation_acknowledged
            or record_obj.run_gate_separation_acknowledged
        )

    review_action = _review_action_for_dialog_action(desired_action)
    preview_record = create_human_review_record(
        source_feaspec_id=source_feaspec_id,
        reviewer=reviewer,
        reviewed_at=reviewed_at,
        action=review_action,
        notes=tuple(str(note) for note in notes),
        accepted_warnings=tuple(_accepted_warning(item) for item in accepted_warnings),
        diagnostic_decisions=tuple(
            _diagnostic_decision(item) for item in diagnostic_decisions
        ),
        validator_report_summary=dict(validator_summary or {}),
        validator_report_hash=validator_report_hash,
        bridge_summary=dict(bridge_summary or {}),
        case_plan_summary=dict(case_plan_summary or {}),
        export_preview_summary=dict(export_preview_summary or {}),
        export_write_summary=dict(export_write_summary or {}),
        limitations_acknowledged=limitations_acknowledged,
        no_run_export_review_acknowledged=no_run_export_review_acknowledged,
        run_gate_separation_acknowledged=run_gate_separation_acknowledged,
    )
    validation = validate_human_review_record(preview_record)
    summary = summarize_human_review_record(preview_record)
    return HumanReviewRecordPreview(
        state=_enum_value(preview_record.state),
        action=_enum_value(preview_record.action),
        source_feaspec_id=preview_record.source_feaspec_id,
        reviewer=preview_record.reviewer,
        reviewed_at=preview_record.reviewed_at,
        valid=validation.is_valid,
        errors=validation.errors,
        warnings=validation.warnings,
        summary=summary.to_dict(),
        json_payload=preview_record.to_dict(),
        solver_execution_performed=preview_record.solver_execution_performed,
        solver_execution_authorized=preview_record.solver_execution_authorized,
    )


def build_human_review_save_plan(
    path: str | Path | None = None,
    *,
    overwrite: bool = False,
) -> HumanReviewSavePlan:
    """Analyze a future save path without writing files."""

    if path in (None, ""):
        return HumanReviewSavePlan(
            path="",
            safe_path=False,
            can_save=False,
            disabled_reasons=("save path is required",),
        )
    review_path = Path(path)
    parent_missing = not review_path.parent.exists()
    overwrite_required = review_path.exists() and not overwrite
    disabled_reasons: list[str] = []
    if review_path.suffix.casefold() != ".json":
        disabled_reasons.append("human review records must use a .json path")
    if parent_missing:
        disabled_reasons.append("parent directory does not exist")
    if overwrite_required:
        disabled_reasons.append("path exists and overwrite was not acknowledged")
    safe_path = not parent_missing and review_path.suffix.casefold() == ".json"
    return HumanReviewSavePlan(
        path=str(review_path),
        safe_path=safe_path,
        parent_missing=parent_missing,
        overwrite_required=overwrite_required,
        can_save=not disabled_reasons,
        disabled_reasons=tuple(disabled_reasons),
    )


def explain_human_review_action_state(
    availability: HumanReviewActionAvailability | HumanReviewDialogState,
) -> list[str]:
    """Return concise user-facing explanations for action state."""

    if isinstance(availability, HumanReviewDialogState):
        return [
            f"{item.action.value}: {'enabled' if item.enabled else item.disabled_reason}"
            for item in availability.actions
        ]
    if availability.enabled:
        return [f"{availability.action.value}: enabled"]
    return [
        f"{availability.action.value}: disabled",
        *availability.disabled_reasons,
    ]


def _collect_diagnostics(
    *,
    validator_summary: Mapping[str, Any],
    bridge_summary: Mapping[str, Any],
    case_plan_summary: Mapping[str, Any],
    export_preview_summary: Mapping[str, Any],
    export_write_summary: Mapping[str, Any],
) -> tuple[HumanReviewDialogDiagnosticRow, ...]:
    rows = [
        *_diagnostic_rows_from_summary(validator_summary, source="validator"),
        *_diagnostic_rows_from_summary(bridge_summary, source="bridge"),
        *_diagnostic_rows_from_summary(case_plan_summary, source="case_plan"),
        *_diagnostic_rows_from_summary(export_preview_summary, source="export_preview"),
        *_diagnostic_rows_from_summary(export_write_summary, source="export_write"),
    ]
    return tuple(rows)


def _diagnostic_rows_from_summary(
    summary: Mapping[str, Any],
    *,
    source: str,
) -> tuple[HumanReviewDialogDiagnosticRow, ...]:
    diagnostics = summary.get("diagnostics", ())
    if isinstance(diagnostics, str | bytes) or not isinstance(diagnostics, Sequence):
        return ()
    rows: list[HumanReviewDialogDiagnosticRow] = []
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, Mapping):
            continue
        reference = ReviewDiagnosticReference.from_dict(diagnostic)
        severity = reference.severity or str(diagnostic.get("level", ""))
        is_blocker = (
            severity.casefold() in _BLOCKING_SEVERITIES
            or reference.blocks_approval
            or reference.blocks_solver_handoff
        )
        accept_away_eligible = severity.casefold() == "warning" and not is_blocker
        rows.append(
            HumanReviewDialogDiagnosticRow(
                source=reference.source or source,
                severity=severity,
                code=reference.code,
                message=reference.message,
                target_ref=reference.target_ref,
                blocks_approval=reference.blocks_approval,
                blocks_solver_handoff=reference.blocks_solver_handoff,
                accept_away_eligible=accept_away_eligible,
            )
        )
    return tuple(rows)


def _build_warning_rows(
    diagnostics: Sequence[HumanReviewDialogDiagnosticRow],
    accepted_warnings: Sequence[AcceptedWarning],
) -> tuple[HumanReviewDialogWarningRow, ...]:
    reasons_by_code = {
        accepted_warning.diagnostic.code: accepted_warning.reason
        for accepted_warning in accepted_warnings
    }
    rows = []
    for diagnostic in diagnostics:
        if not diagnostic.is_warning:
            continue
        reason = reasons_by_code.get(diagnostic.code, "")
        rows.append(
            HumanReviewDialogWarningRow(
                diagnostic=diagnostic,
                reason=reason,
                accepted=bool(reason.strip()) and diagnostic.accept_away_eligible,
                acceptance_required=diagnostic.accept_away_eligible,
            )
        )
    return tuple(rows)


def _required_identity_reasons(state: HumanReviewDialogState) -> tuple[str, ...]:
    reasons = []
    if not state.reviewer.strip():
        reasons.append("missing reviewer")
    if not state.reviewed_at.strip():
        reasons.append("missing timestamp")
    if not state.source_feaspec_id.strip():
        reasons.append("missing source id")
    return tuple(reasons)


def _notes_required_reasons(state: HumanReviewDialogState) -> tuple[str, ...]:
    if any(note.strip() for note in state.notes):
        return ()
    return ("review notes are required",)


def _validator_evidence_reasons(state: HumanReviewDialogState) -> tuple[str, ...]:
    reasons = []
    if not state.validator_summary:
        reasons.append("missing validator summary")
    if not state.validator_report_hash.strip():
        reasons.append("missing validator hash")
    return tuple(reasons)


def _blocking_reasons(state: HumanReviewDialogState) -> tuple[str, ...]:
    reasons: list[str] = []
    if _summary_has_blockers(state.validator_summary):
        reasons.append("validator blockers/errors exist")
    if any(row.is_blocker for row in state.diagnostics):
        reasons.append("blocker diagnostics exist")
    return tuple(dict.fromkeys(reasons))


def _unresolved_warning_reasons(state: HumanReviewDialogState) -> tuple[str, ...]:
    if any(row.requires_reason for row in state.warnings):
        return ("unresolved warning reasons exist",)
    return ()


def _run_request_ack_reasons(state: HumanReviewDialogState) -> tuple[str, ...]:
    reasons = []
    if not state.no_run_export_review_acknowledged:
        reasons.append("missing no-run export acknowledgement")
    if not state.limitations_acknowledged:
        reasons.append("missing README/limitations acknowledgement")
    if not state.run_gate_separation_acknowledged:
        reasons.append("missing run-gate-separate acknowledgement")
    return tuple(reasons)


def _record_preview_invalid_reasons(
    state: HumanReviewDialogState,
) -> tuple[str, ...]:
    if state.record_preview is None:
        return ("record preview is required",)
    if state.record_preview.valid:
        return ()
    if state.record_preview.errors:
        return tuple(
            f"record preview invalid: {error}" for error in state.record_preview.errors
        )
    return ("record preview invalid",)


def _accept_warning_reasons(state: HumanReviewDialogState) -> tuple[str, ...]:
    if not state.warnings:
        return ("warning rows are required",)
    if not any(row.diagnostic.accept_away_eligible for row in state.warnings):
        return ("no accept-away eligible warnings",)
    if not any(row.requires_reason for row in state.warnings):
        return ("no unresolved warnings require acceptance",)
    return ()


def _availability(
    action: HumanReviewDialogAction,
    disabled_reasons: Sequence[str],
) -> HumanReviewActionAvailability:
    reasons = tuple(reason for reason in disabled_reasons if reason)
    return HumanReviewActionAvailability(
        action=action,
        enabled=not reasons,
        disabled_reasons=reasons,
    )


def _summary_has_blockers(summary: Mapping[str, Any]) -> bool:
    if bool(summary.get("has_blockers")) or bool(summary.get("has_errors")):
        return True
    for key in ("blocker_count", "error_count"):
        try:
            if int(summary.get(key, 0)) > 0:
                return True
        except (TypeError, ValueError):
            return True
    return False


def _replace_actions(
    state: HumanReviewDialogState,
    actions: Sequence[HumanReviewActionAvailability],
) -> HumanReviewDialogState:
    return HumanReviewDialogState(
        source_feaspec_id=state.source_feaspec_id,
        reviewer=state.reviewer,
        reviewed_at=state.reviewed_at,
        desired_action=state.desired_action,
        panels=state.panels,
        diagnostics=state.diagnostics,
        warnings=state.warnings,
        actions=tuple(actions),
        record_preview=state.record_preview,
        save_plan=state.save_plan,
        notes=state.notes,
        validator_summary=state.validator_summary,
        validator_report_hash=state.validator_report_hash,
        bridge_summary=state.bridge_summary,
        case_plan_summary=state.case_plan_summary,
        export_preview_summary=state.export_preview_summary,
        export_write_summary=state.export_write_summary,
        limitations_acknowledged=state.limitations_acknowledged,
        no_run_export_review_acknowledged=state.no_run_export_review_acknowledged,
        run_gate_separation_acknowledged=state.run_gate_separation_acknowledged,
    )


def _review_action_for_dialog_action(
    action: HumanReviewDialogAction | HumanReviewAction | str,
) -> HumanReviewAction:
    dialog_action = _dialog_action(action)
    if dialog_action is HumanReviewDialogAction.REJECT:
        return HumanReviewAction.REJECT
    if dialog_action is HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT:
        return HumanReviewAction.APPROVE_NO_RUN_EXPORT
    if dialog_action is HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN:
        return HumanReviewAction.REQUEST_INSTALLED_ONLY_RUN
    return HumanReviewAction.MARK_NEEDS_CHANGES


def _dialog_action(
    action: HumanReviewDialogAction | HumanReviewAction | str,
) -> HumanReviewDialogAction:
    if isinstance(action, HumanReviewDialogAction):
        return action
    if isinstance(action, HumanReviewAction):
        mapping = {
            HumanReviewAction.MARK_NEEDS_CHANGES: (
                HumanReviewDialogAction.MARK_NEEDS_CHANGES
            ),
            HumanReviewAction.REJECT: HumanReviewDialogAction.REJECT,
            HumanReviewAction.APPROVE_NO_RUN_EXPORT: (
                HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT
            ),
            HumanReviewAction.REQUEST_INSTALLED_ONLY_RUN: (
                HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN
            ),
            HumanReviewAction.ACCEPT_WARNING: HumanReviewDialogAction.ACCEPT_WARNING,
            HumanReviewAction.REJECT_DIAGNOSTIC: (
                HumanReviewDialogAction.REJECT_DIAGNOSTIC
            ),
        }
        return mapping.get(action, HumanReviewDialogAction.MARK_NEEDS_CHANGES)
    value = str(action).strip()
    try:
        return HumanReviewDialogAction(value)
    except ValueError:
        return HumanReviewDialogAction.MARK_NEEDS_CHANGES


def _accepted_warning(item: AcceptedWarning | Mapping[str, Any]) -> AcceptedWarning:
    if isinstance(item, AcceptedWarning):
        return item
    return AcceptedWarning.from_dict(item)


def _diagnostic_decision(item: DiagnosticDecision | Mapping[str, Any]) -> DiagnosticDecision:
    if isinstance(item, DiagnosticDecision):
        return item
    return DiagnosticDecision.from_dict(item)


def _record_or_none(
    record: FEASpecHumanReviewRecord | Mapping[str, Any] | None,
) -> FEASpecHumanReviewRecord | None:
    if record is None:
        return None
    if isinstance(record, FEASpecHumanReviewRecord):
        return record
    return FEASpecHumanReviewRecord.from_dict(record)


def _enum_value(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else str(value)
