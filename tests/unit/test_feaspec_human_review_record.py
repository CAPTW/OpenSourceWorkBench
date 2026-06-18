from __future__ import annotations

from osw.experimental import feaspec
from osw.experimental.feaspec import (
    AcceptedWarning,
    DiagnosticDecision,
    FEASpecHumanReviewRecord,
    HumanReviewAction,
    HumanReviewState,
    ReviewDiagnosticReference,
    create_human_review_record,
    explain_human_review_record,
    summarize_human_review_record,
    validate_human_review_record,
)


def _validator_summary(*, blockers: bool = False, errors: bool = False) -> dict[str, object]:
    return {"has_blockers": blockers, "has_errors": errors, "diagnostics": []}


def _approved_record() -> FEASpecHumanReviewRecord:
    return create_human_review_record(
        source_feaspec_id="cantilever-approved",
        reviewer="reviewer@example.test",
        reviewed_at="2026-06-18T00:00:00Z",
        action=HumanReviewAction.APPROVE_NO_RUN_EXPORT,
        notes=("reviewed geometry and loads",),
        validator_report_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
        bridge_summary={"status": "ready"},
        case_plan_summary={"status": "ready_for_writer"},
        export_preview_summary={"status": "ready"},
        export_write_summary={"status": "not_written"},
        provenance={"source": "unit-test"},
    )


def test_module_imports_and_public_api_exports() -> None:
    assert feaspec.FEASpecHumanReviewRecord is FEASpecHumanReviewRecord
    assert feaspec.HumanReviewState is HumanReviewState
    assert feaspec.HumanReviewAction is HumanReviewAction
    assert feaspec.create_human_review_record is create_human_review_record
    assert feaspec.validate_human_review_record is validate_human_review_record
    assert feaspec.summarize_human_review_record is summarize_human_review_record
    assert feaspec.explain_human_review_record is explain_human_review_record


def test_review_states_include_required_values() -> None:
    assert {state.value for state in HumanReviewState} >= {
        "unreviewed",
        "needs_changes",
        "rejected",
        "approved_for_no_run_export",
        "approved_for_installed_only_run_request",
    }


def test_review_actions_include_required_values() -> None:
    assert {action.value for action in HumanReviewAction} >= {
        "mark_needs_changes",
        "reject",
        "approve_no_run_export",
        "request_installed_only_run",
        "accept_warning",
        "reject_diagnostic",
        "add_note",
    }


def test_minimal_needs_changes_record_validates() -> None:
    record = create_human_review_record(
        source_feaspec_id="candidate",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="mark_needs_changes",
        validator_report_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
    )

    assert record.state is HumanReviewState.NEEDS_CHANGES
    assert validate_human_review_record(record).is_valid


def test_rejected_record_validates() -> None:
    record = create_human_review_record(
        source_feaspec_id="candidate",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="reject",
        validator_report_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
    )

    assert record.state is HumanReviewState.REJECTED
    assert validate_human_review_record(record).is_valid


def test_approved_no_run_export_record_validates_without_blockers() -> None:
    record = _approved_record()

    result = validate_human_review_record(record)

    assert result.is_valid
    assert record.solver_execution_performed is False


def test_approved_no_run_export_record_fails_with_validator_blockers() -> None:
    record = create_human_review_record(
        source_feaspec_id="candidate",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="approve_no_run_export",
        validator_report_summary=_validator_summary(blockers=True),
        validator_report_hash="sha256:validator",
    )

    result = validate_human_review_record(record)

    assert not result.is_valid
    assert any("blocker" in error.lower() for error in result.errors)


def test_accepted_warning_requires_reason() -> None:
    record = create_human_review_record(
        source_feaspec_id="candidate",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="mark_needs_changes",
        validator_report_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
        accepted_warnings=(
            AcceptedWarning(
                diagnostic=ReviewDiagnosticReference(
                    "FS_CONFIDENCE_LOW",
                    severity="warning",
                ),
                reason="",
            ),
        ),
    )

    result = validate_human_review_record(record)

    assert not result.is_valid
    assert any("requires reason" in error for error in result.errors)


def test_blocker_diagnostic_cannot_be_accepted_away() -> None:
    record = create_human_review_record(
        source_feaspec_id="candidate",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="mark_needs_changes",
        validator_report_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
        accepted_warnings=(
            AcceptedWarning(
                diagnostic=ReviewDiagnosticReference(
                    "FS_REVIEW_MISSING",
                    severity="blocker",
                    blocks_approval=True,
                ),
                reason="accepted anyway",
            ),
        ),
    )

    result = validate_human_review_record(record)

    assert not result.is_valid
    assert "blocker diagnostics cannot be accepted away" in result.errors


def test_installed_only_run_request_does_not_set_solver_execution_performed() -> None:
    record = create_human_review_record(
        source_feaspec_id="approved",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="request_installed_only_run",
        validator_report_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
        limitations_acknowledged=True,
        no_run_export_review_acknowledged=True,
        run_gate_separation_acknowledged=True,
    )

    assert record.state is HumanReviewState.APPROVED_FOR_INSTALLED_ONLY_RUN_REQUEST
    assert record.solver_execution_authorized is True
    assert record.solver_execution_performed is False
    assert validate_human_review_record(record).is_valid


def test_installed_only_run_request_requires_export_and_limitations_acknowledgement() -> None:
    record = create_human_review_record(
        source_feaspec_id="approved",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="request_installed_only_run",
        validator_report_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
    )

    result = validate_human_review_record(record)

    assert not result.is_valid
    assert any("no-run export review" in error for error in result.errors)
    assert any("limitations" in error for error in result.errors)
    assert any("actual run gate is separate" in error for error in result.errors)


def test_solver_flags_default_false() -> None:
    record = FEASpecHumanReviewRecord()

    assert record.solver_execution_performed is False
    assert record.solver_execution_authorized is False


def test_solver_execution_authorized_defaults_false_unless_explicit_request_state() -> None:
    no_run_record = _approved_record()
    run_request = create_human_review_record(
        source_feaspec_id="approved",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="request_installed_only_run",
        validator_report_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
        limitations_acknowledged=True,
        no_run_export_review_acknowledged=True,
        run_gate_separation_acknowledged=True,
    )

    assert no_run_record.solver_execution_authorized is False
    assert run_request.solver_execution_authorized is True


def test_record_preserves_source_hash_and_summaries() -> None:
    record = _approved_record()

    assert record.source_feaspec_id == "cantilever-approved"
    assert record.validator_report_hash == "sha256:validator"
    assert record.bridge_summary == {"status": "ready"}
    assert record.case_plan_summary == {"status": "ready_for_writer"}
    assert record.export_preview_summary == {"status": "ready"}
    assert record.export_write_summary == {"status": "not_written"}


def test_summary_returns_state_action_and_source() -> None:
    summary = summarize_human_review_record(_approved_record())

    assert summary.state == "approved_for_no_run_export"
    assert summary.action == "approve_no_run_export"
    assert summary.source_feaspec_id == "cantilever-approved"
    assert summary.is_valid is True


def test_explain_returns_user_readable_strings() -> None:
    explanations = explain_human_review_record(_approved_record())

    assert explanations
    assert any("Human review" in line for line in explanations)
    assert any("Source FEASpec" in line for line in explanations)
    assert any("Solver execution performed: false" in line for line in explanations)


def test_record_round_trips_through_dict() -> None:
    record = _approved_record()
    restored = FEASpecHumanReviewRecord.from_dict(record.to_dict())

    assert restored.to_dict() == record.to_dict()


def test_validation_reports_missing_required_fields() -> None:
    result = validate_human_review_record(FEASpecHumanReviewRecord())

    assert not result.is_valid
    assert any("reviewer" in error for error in result.errors)
    assert any("reviewed_at" in error for error in result.errors)
    assert any("source_feaspec_id" in error for error in result.errors)
    assert any("action" in error for error in result.errors)


def test_diagnostic_decision_records_rejected_diagnostic() -> None:
    record = create_human_review_record(
        source_feaspec_id="candidate",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="mark_needs_changes",
        validator_report_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
        diagnostic_decisions=(
            DiagnosticDecision(
                diagnostic=ReviewDiagnosticReference(
                    "FS_LOAD_INVALID_TARGET",
                    severity="error",
                    blocks_approval=True,
                ),
                action=HumanReviewAction.REJECT_DIAGNOSTIC,
                reason="load target must be repaired before approval",
            ),
        ),
    )

    assert record.diagnostic_decisions[0].action is HumanReviewAction.REJECT_DIAGNOSTIC
    assert validate_human_review_record(record).is_valid
