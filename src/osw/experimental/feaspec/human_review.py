"""Experimental FEASpec human review record model.

The record model captures reviewer decisions and provenance before no-run
export or future installed-only run request gates. It does not implement GUI
approval, result import, runner integration, ProjectSchema mutation, or solver
execution.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .human_review_errors import FEASpecHumanReviewValidationError

HUMAN_REVIEW_SCHEMA_VERSION = "feaspec-human-review-record/v1"
_BLOCKING_SEVERITIES = {"blocker", "error"}


class HumanReviewState(str, Enum):
    """Allowed states for a FEASpec human review record."""

    UNREVIEWED = "unreviewed"
    NEEDS_CHANGES = "needs_changes"
    REJECTED = "rejected"
    APPROVED_FOR_NO_RUN_EXPORT = "approved_for_no_run_export"
    APPROVED_FOR_INSTALLED_ONLY_RUN_REQUEST = "approved_for_installed_only_run_request"

    @classmethod
    def from_value(cls, value: object) -> HumanReviewState:
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value))
        except ValueError as exc:
            msg = f"Unsupported human review state: {value!r}"
            raise FEASpecHumanReviewValidationError(msg) from exc


class HumanReviewAction(str, Enum):
    """Allowed reviewer actions captured by a human review record."""

    MARK_NEEDS_CHANGES = "mark_needs_changes"
    REJECT = "reject"
    APPROVE_NO_RUN_EXPORT = "approve_no_run_export"
    REQUEST_INSTALLED_ONLY_RUN = "request_installed_only_run"
    ACCEPT_WARNING = "accept_warning"
    REJECT_DIAGNOSTIC = "reject_diagnostic"
    ADD_NOTE = "add_note"

    @classmethod
    def from_value(cls, value: object) -> HumanReviewAction:
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value))
        except ValueError as exc:
            msg = f"Unsupported human review action: {value!r}"
            raise FEASpecHumanReviewValidationError(msg) from exc


@dataclass(frozen=True)
class ReviewDiagnosticReference:
    """Stable reference to a diagnostic considered during human review."""

    code: str
    severity: str = ""
    message: str = ""
    target_ref: str = ""
    source: str = ""
    blocks_approval: bool = False
    blocks_solver_handoff: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> ReviewDiagnosticReference:
        payload = _mapping(data, "diagnostic")
        known = {
            "code",
            "severity",
            "message",
            "target_ref",
            "source",
            "blocks_approval",
            "blocks_solver_handoff",
        }
        return cls(
            code=str(payload.get("code", "")),
            severity=str(payload.get("severity", "")),
            message=str(payload.get("message", "")),
            target_ref=str(payload.get("target_ref", "")),
            source=str(payload.get("source", "")),
            blocks_approval=bool(payload.get("blocks_approval", False)),
            blocks_solver_handoff=bool(payload.get("blocks_solver_handoff", False)),
            extra=_extra(payload, known),
        )

    @property
    def is_blocking(self) -> bool:
        return (
            self.severity.lower() in _BLOCKING_SEVERITIES
            or self.blocks_approval
            or self.blocks_solver_handoff
        )

    @property
    def is_warning(self) -> bool:
        return self.severity.lower() == "warning"

    def to_dict(self) -> dict[str, Any]:
        return _drop_empty(
            {
                "code": self.code,
                "severity": self.severity,
                "message": self.message,
                "target_ref": self.target_ref,
                "source": self.source,
                "blocks_approval": self.blocks_approval,
                "blocks_solver_handoff": self.blocks_solver_handoff,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class AcceptedWarning:
    """Reviewer acceptance record for a non-blocking warning diagnostic."""

    diagnostic: ReviewDiagnosticReference
    reason: str
    reviewer: str = ""
    accepted_at: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> AcceptedWarning:
        payload = _mapping(data, "accepted_warning")
        known = {"diagnostic", "reason", "reviewer", "accepted_at"}
        return cls(
            diagnostic=ReviewDiagnosticReference.from_dict(payload.get("diagnostic", {})),
            reason=str(payload.get("reason", "")),
            reviewer=str(payload.get("reviewer", "")),
            accepted_at=str(payload.get("accepted_at", "")),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_empty(
            {
                "diagnostic": self.diagnostic.to_dict(),
                "reason": self.reason,
                "reviewer": self.reviewer,
                "accepted_at": self.accepted_at,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class DiagnosticDecision:
    """Reviewer decision record for a diagnostic."""

    diagnostic: ReviewDiagnosticReference
    action: HumanReviewAction | str
    reason: str = ""
    reviewer: str = ""
    decided_at: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> DiagnosticDecision:
        payload = _mapping(data, "diagnostic_decision")
        known = {"diagnostic", "action", "reason", "reviewer", "decided_at"}
        return cls(
            diagnostic=ReviewDiagnosticReference.from_dict(payload.get("diagnostic", {})),
            action=_coerce_action(payload.get("action", "")),
            reason=str(payload.get("reason", "")),
            reviewer=str(payload.get("reviewer", "")),
            decided_at=str(payload.get("decided_at", "")),
            extra=_extra(payload, known),
        )

    def to_dict(self) -> dict[str, Any]:
        return _drop_empty(
            {
                "diagnostic": self.diagnostic.to_dict(),
                "action": _enum_value(self.action),
                "reason": self.reason,
                "reviewer": self.reviewer,
                "decided_at": self.decided_at,
                **self.extra,
            }
        )


@dataclass(frozen=True)
class HumanReviewSummary:
    """Compact human review summary for previews and reports."""

    state: str
    action: str
    source_feaspec_id: str
    reviewer: str
    reviewed_at: str
    validator_report_hash: str = ""
    accepted_warning_count: int = 0
    diagnostic_decision_count: int = 0
    solver_execution_authorized: bool = False
    solver_execution_performed: bool = False
    is_valid: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "action": self.action,
            "source_feaspec_id": self.source_feaspec_id,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "validator_report_hash": self.validator_report_hash,
            "accepted_warning_count": self.accepted_warning_count,
            "diagnostic_decision_count": self.diagnostic_decision_count,
            "solver_execution_authorized": self.solver_execution_authorized,
            "solver_execution_performed": self.solver_execution_performed,
            "is_valid": self.is_valid,
        }


@dataclass(frozen=True)
class FEASpecHumanReviewValidationResult:
    """Validation result for a human review record."""

    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class FEASpecHumanReviewRecord:
    """Reviewer decision record for a FEASpec preparation workflow."""

    schema_version: str = HUMAN_REVIEW_SCHEMA_VERSION
    record_id: str = ""
    source_feaspec_id: str = ""
    reviewer: str = ""
    reviewed_at: str = ""
    state: HumanReviewState | str = HumanReviewState.UNREVIEWED
    action: HumanReviewAction | str = ""
    notes: tuple[str, ...] = ()
    accepted_warnings: tuple[AcceptedWarning, ...] = ()
    diagnostic_decisions: tuple[DiagnosticDecision, ...] = ()
    validator_report_summary: dict[str, Any] = field(default_factory=dict)
    validator_report_hash: str = ""
    bridge_summary: dict[str, Any] = field(default_factory=dict)
    case_plan_summary: dict[str, Any] = field(default_factory=dict)
    export_preview_summary: dict[str, Any] = field(default_factory=dict)
    export_write_summary: dict[str, Any] = field(default_factory=dict)
    limitations_acknowledged: bool = False
    solver_execution_authorized: bool = False
    solver_execution_performed: bool = False
    no_run_export_review_acknowledged: bool = False
    run_gate_separation_acknowledged: bool = False
    provenance: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> FEASpecHumanReviewRecord:
        payload = _mapping(data, "human_review_record")
        return cls(
            schema_version=str(payload.get("schema_version", HUMAN_REVIEW_SCHEMA_VERSION)),
            record_id=str(payload.get("record_id", "")),
            source_feaspec_id=str(payload.get("source_feaspec_id", "")),
            reviewer=str(payload.get("reviewer", "")),
            reviewed_at=str(payload.get("reviewed_at", "")),
            state=_coerce_state(payload.get("state", HumanReviewState.UNREVIEWED.value)),
            action=_coerce_action(payload.get("action", "")),
            notes=tuple(str(item) for item in _sequence(payload.get("notes", []), "notes")),
            accepted_warnings=tuple(
                AcceptedWarning.from_dict(item)
                for item in _sequence(payload.get("accepted_warnings", []), "accepted_warnings")
            ),
            diagnostic_decisions=tuple(
                DiagnosticDecision.from_dict(item)
                for item in _sequence(
                    payload.get("diagnostic_decisions", []), "diagnostic_decisions"
                )
            ),
            validator_report_summary=_json_mapping(
                payload.get("validator_report_summary", {}), "validator_report_summary"
            ),
            validator_report_hash=str(payload.get("validator_report_hash", "")),
            bridge_summary=_json_mapping(payload.get("bridge_summary", {}), "bridge_summary"),
            case_plan_summary=_json_mapping(
                payload.get("case_plan_summary", {}), "case_plan_summary"
            ),
            export_preview_summary=_json_mapping(
                payload.get("export_preview_summary", {}), "export_preview_summary"
            ),
            export_write_summary=_json_mapping(
                payload.get("export_write_summary", {}), "export_write_summary"
            ),
            limitations_acknowledged=bool(payload.get("limitations_acknowledged", False)),
            solver_execution_authorized=bool(
                payload.get("solver_execution_authorized", False)
            ),
            solver_execution_performed=bool(payload.get("solver_execution_performed", False)),
            no_run_export_review_acknowledged=bool(
                payload.get("no_run_export_review_acknowledged", False)
            ),
            run_gate_separation_acknowledged=bool(
                payload.get("run_gate_separation_acknowledged", False)
            ),
            provenance=_json_mapping(payload.get("provenance", {}), "provenance"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "source_feaspec_id": self.source_feaspec_id,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "state": _enum_value(self.state),
            "action": _enum_value(self.action),
            "notes": list(self.notes),
            "accepted_warnings": [
                accepted_warning.to_dict() for accepted_warning in self.accepted_warnings
            ],
            "diagnostic_decisions": [
                diagnostic_decision.to_dict()
                for diagnostic_decision in self.diagnostic_decisions
            ],
            "validator_report_summary": dict(self.validator_report_summary),
            "validator_report_hash": self.validator_report_hash,
            "bridge_summary": dict(self.bridge_summary),
            "case_plan_summary": dict(self.case_plan_summary),
            "export_preview_summary": dict(self.export_preview_summary),
            "export_write_summary": dict(self.export_write_summary),
            "limitations_acknowledged": self.limitations_acknowledged,
            "solver_execution_authorized": self.solver_execution_authorized,
            "solver_execution_performed": self.solver_execution_performed,
            "no_run_export_review_acknowledged": self.no_run_export_review_acknowledged,
            "run_gate_separation_acknowledged": self.run_gate_separation_acknowledged,
            "provenance": dict(self.provenance),
        }


def create_human_review_record(
    *,
    source_feaspec_id: str,
    reviewer: str,
    reviewed_at: str,
    action: HumanReviewAction | str,
    record_id: str = "",
    state: HumanReviewState | str | None = None,
    notes: Sequence[str] = (),
    accepted_warnings: Sequence[AcceptedWarning | Mapping[str, Any]] = (),
    diagnostic_decisions: Sequence[DiagnosticDecision | Mapping[str, Any]] = (),
    validator_report_summary: Mapping[str, Any] | None = None,
    validator_report_hash: str = "",
    bridge_summary: Mapping[str, Any] | None = None,
    case_plan_summary: Mapping[str, Any] | None = None,
    export_preview_summary: Mapping[str, Any] | None = None,
    export_write_summary: Mapping[str, Any] | None = None,
    limitations_acknowledged: bool = False,
    no_run_export_review_acknowledged: bool = False,
    run_gate_separation_acknowledged: bool = False,
    solver_execution_authorized: bool | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> FEASpecHumanReviewRecord:
    """Create a deterministic human review record.

    The helper does not create timestamps automatically. Callers must supply a
    reviewed timestamp so tests and future review flows remain reproducible.
    """

    review_action = HumanReviewAction.from_value(action)
    review_state = (
        HumanReviewState.from_value(state)
        if state is not None
        else _state_for_action(review_action)
    )
    authorized = (
        review_state is HumanReviewState.APPROVED_FOR_INSTALLED_ONLY_RUN_REQUEST
        if solver_execution_authorized is None
        else solver_execution_authorized
    )
    normalized_record_id = record_id or f"human-review:{source_feaspec_id}"
    return FEASpecHumanReviewRecord(
        record_id=normalized_record_id,
        source_feaspec_id=source_feaspec_id,
        reviewer=reviewer,
        reviewed_at=reviewed_at,
        state=review_state,
        action=review_action,
        notes=tuple(str(note) for note in notes),
        accepted_warnings=tuple(_accepted_warning(item) for item in accepted_warnings),
        diagnostic_decisions=tuple(_diagnostic_decision(item) for item in diagnostic_decisions),
        validator_report_summary=_json_mapping(
            validator_report_summary or {}, "validator_report_summary"
        ),
        validator_report_hash=validator_report_hash,
        bridge_summary=_json_mapping(bridge_summary or {}, "bridge_summary"),
        case_plan_summary=_json_mapping(case_plan_summary or {}, "case_plan_summary"),
        export_preview_summary=_json_mapping(
            export_preview_summary or {}, "export_preview_summary"
        ),
        export_write_summary=_json_mapping(export_write_summary or {}, "export_write_summary"),
        limitations_acknowledged=limitations_acknowledged,
        solver_execution_authorized=authorized,
        solver_execution_performed=False,
        no_run_export_review_acknowledged=no_run_export_review_acknowledged,
        run_gate_separation_acknowledged=run_gate_separation_acknowledged,
        provenance=_json_mapping(provenance or {}, "provenance"),
    )


def validate_human_review_record(
    record: FEASpecHumanReviewRecord | Mapping[str, Any],
) -> FEASpecHumanReviewValidationResult:
    """Validate a human review record without mutating it."""

    review_record = _record(record)
    errors: list[str] = []
    warnings: list[str] = []

    state = _try_state(review_record.state)
    action = _try_action(review_record.action)

    if not review_record.reviewer.strip():
        errors.append("reviewer is required")
    if not review_record.reviewed_at.strip():
        errors.append("reviewed_at timestamp is required")
    if not review_record.source_feaspec_id.strip():
        errors.append("source_feaspec_id is required")
    if action is None:
        errors.append("action is required")
    if state is None:
        errors.append("state is required")
    if not review_record.validator_report_summary:
        errors.append("validator_report_summary is required")
    if not review_record.validator_report_hash.strip():
        errors.append("validator_report_hash is required")
    if review_record.solver_execution_performed:
        errors.append("human review records must not record solver execution as performed")

    if _validator_summary_has_blockers(review_record.validator_report_summary):
        errors.append("validator blocker/error diagnostics prevent approval")
    if _has_blocking_accepted_warning(review_record.accepted_warnings):
        errors.append("blocker diagnostics cannot be accepted away")
    for accepted_warning in review_record.accepted_warnings:
        if not accepted_warning.reason.strip():
            errors.append(
                "accepted warning "
                f"{accepted_warning.diagnostic.code or '<missing>'} requires reason"
            )
    for diagnostic_decision in review_record.diagnostic_decisions:
        if diagnostic_decision.diagnostic.is_blocking and not diagnostic_decision.reason.strip():
            warnings.append(
                f"diagnostic decision {diagnostic_decision.diagnostic.code or '<missing>'} "
                "should include a reason"
            )

    if state is HumanReviewState.APPROVED_FOR_NO_RUN_EXPORT:
        _validate_no_run_export_approval(review_record, errors)
    if state is HumanReviewState.APPROVED_FOR_INSTALLED_ONLY_RUN_REQUEST:
        _validate_installed_only_request(review_record, errors)

    return FEASpecHumanReviewValidationResult(tuple(errors), tuple(warnings))


def summarize_human_review_record(
    record: FEASpecHumanReviewRecord | Mapping[str, Any],
) -> HumanReviewSummary:
    """Return a compact summary of a human review record."""

    review_record = _record(record)
    validation = validate_human_review_record(review_record)
    return HumanReviewSummary(
        state=_enum_value(review_record.state),
        action=_enum_value(review_record.action),
        source_feaspec_id=review_record.source_feaspec_id,
        reviewer=review_record.reviewer,
        reviewed_at=review_record.reviewed_at,
        validator_report_hash=review_record.validator_report_hash,
        accepted_warning_count=len(review_record.accepted_warnings),
        diagnostic_decision_count=len(review_record.diagnostic_decisions),
        solver_execution_authorized=review_record.solver_execution_authorized,
        solver_execution_performed=review_record.solver_execution_performed,
        is_valid=validation.is_valid,
    )


def explain_human_review_record(
    record: FEASpecHumanReviewRecord | Mapping[str, Any],
) -> list[str]:
    """Return concise reviewer-facing human review explanations."""

    review_record = _record(record)
    validation = validate_human_review_record(review_record)
    explanations = [
        f"Human review {review_record.record_id or '<unidentified>'}: "
        f"{_enum_value(review_record.state)} via {_enum_value(review_record.action)}.",
        f"Source FEASpec: {review_record.source_feaspec_id or '<missing>'}.",
        f"Reviewer: {review_record.reviewer or '<missing>'} at "
        f"{review_record.reviewed_at or '<missing>'}.",
        "Solver execution performed: false.",
    ]
    if review_record.solver_execution_authorized:
        explanations.append(
            "Installed-only run request intent is recorded; the actual run gate remains separate."
        )
    if review_record.accepted_warnings:
        explanations.append(f"Accepted warnings: {len(review_record.accepted_warnings)}.")
    if validation.errors:
        explanations.extend(f"ERROR: {error}" for error in validation.errors)
    if validation.warnings:
        explanations.extend(f"WARNING: {warning}" for warning in validation.warnings)
    return explanations


def _validate_no_run_export_approval(
    record: FEASpecHumanReviewRecord,
    errors: list[str],
) -> None:
    if _validator_summary_has_blockers(record.validator_report_summary):
        errors.append("no-run export approval requires no blocker/error diagnostics")


def _validate_installed_only_request(
    record: FEASpecHumanReviewRecord,
    errors: list[str],
) -> None:
    _validate_no_run_export_approval(record, errors)
    if not record.no_run_export_review_acknowledged:
        errors.append(
            "installed-only run request requires no-run export review acknowledgement"
        )
    if not record.limitations_acknowledged:
        errors.append(
            "installed-only run request requires README/export limitations acknowledgement"
        )
    if not record.run_gate_separation_acknowledged:
        errors.append(
            "installed-only run request must acknowledge the actual run gate is separate"
        )
    if not record.solver_execution_authorized:
        errors.append("installed-only run request must explicitly record request intent")
    if record.solver_execution_performed:
        errors.append("installed-only run request must not imply solver execution")


def _state_for_action(action: HumanReviewAction) -> HumanReviewState:
    if action is HumanReviewAction.MARK_NEEDS_CHANGES:
        return HumanReviewState.NEEDS_CHANGES
    if action is HumanReviewAction.REJECT:
        return HumanReviewState.REJECTED
    if action is HumanReviewAction.APPROVE_NO_RUN_EXPORT:
        return HumanReviewState.APPROVED_FOR_NO_RUN_EXPORT
    if action is HumanReviewAction.REQUEST_INSTALLED_ONLY_RUN:
        return HumanReviewState.APPROVED_FOR_INSTALLED_ONLY_RUN_REQUEST
    return HumanReviewState.UNREVIEWED


def _validator_summary_has_blockers(summary: Mapping[str, Any]) -> bool:
    if bool(summary.get("has_blockers")) or bool(summary.get("has_errors")):
        return True
    for key in ("blocker_count", "error_count"):
        try:
            if int(summary.get(key, 0)) > 0:
                return True
        except (TypeError, ValueError):
            return True
    diagnostics = summary.get("diagnostics", ())
    if isinstance(diagnostics, Sequence) and not isinstance(diagnostics, str | bytes):
        for diagnostic in diagnostics:
            try:
                if ReviewDiagnosticReference.from_dict(diagnostic).is_blocking:
                    return True
            except FEASpecHumanReviewValidationError:
                return True
    return False


def _has_blocking_accepted_warning(accepted_warnings: Sequence[AcceptedWarning]) -> bool:
    return any(accepted_warning.diagnostic.is_blocking for accepted_warning in accepted_warnings)


def _record(record: FEASpecHumanReviewRecord | Mapping[str, Any]) -> FEASpecHumanReviewRecord:
    if isinstance(record, FEASpecHumanReviewRecord):
        return record
    return FEASpecHumanReviewRecord.from_dict(record)


def _accepted_warning(item: AcceptedWarning | Mapping[str, Any]) -> AcceptedWarning:
    if isinstance(item, AcceptedWarning):
        return item
    return AcceptedWarning.from_dict(item)


def _diagnostic_decision(item: DiagnosticDecision | Mapping[str, Any]) -> DiagnosticDecision:
    if isinstance(item, DiagnosticDecision):
        return item
    return DiagnosticDecision.from_dict(item)


def _coerce_state(value: object) -> HumanReviewState | str:
    if isinstance(value, HumanReviewState):
        return value
    try:
        return HumanReviewState.from_value(value)
    except FEASpecHumanReviewValidationError:
        return str(value)


def _coerce_action(value: object) -> HumanReviewAction | str:
    if isinstance(value, HumanReviewAction):
        return value
    try:
        return HumanReviewAction.from_value(value)
    except FEASpecHumanReviewValidationError:
        return str(value)


def _try_state(value: HumanReviewState | str) -> HumanReviewState | None:
    try:
        return HumanReviewState.from_value(value)
    except FEASpecHumanReviewValidationError:
        return None


def _try_action(value: HumanReviewAction | str) -> HumanReviewAction | None:
    if str(value).strip() == "":
        return None
    try:
        return HumanReviewAction.from_value(value)
    except FEASpecHumanReviewValidationError:
        return None


def _enum_value(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _mapping(data: object, label: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        msg = f"{label} must be a mapping."
        raise FEASpecHumanReviewValidationError(msg)
    return data


def _json_mapping(data: object, label: str) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        msg = f"{label} must be a mapping."
        raise FEASpecHumanReviewValidationError(msg)
    return dict(data)


def _sequence(data: object, label: str) -> Sequence[object]:
    if data is None:
        return ()
    if isinstance(data, str | bytes) or not isinstance(data, Sequence):
        msg = f"{label} must be a sequence."
        raise FEASpecHumanReviewValidationError(msg)
    return data


def _extra(payload: Mapping[str, Any], known: set[str]) -> dict[str, Any]:
    return {str(key): value for key, value in payload.items() if str(key) not in known}


def _drop_empty(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if value not in ("", None, [], {}, ()) or isinstance(value, bool)
    }
