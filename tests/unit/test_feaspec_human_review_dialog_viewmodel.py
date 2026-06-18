from __future__ import annotations

from osw.experimental import feaspec
from osw.experimental.feaspec import (
    AcceptedWarning,
    HumanReviewActionAvailability,
    HumanReviewDialogAction,
    HumanReviewDialogDiagnosticRow,
    HumanReviewDialogPanel,
    HumanReviewDialogState,
    HumanReviewDialogWarningRow,
    HumanReviewRecordPreview,
    HumanReviewSavePlan,
    ReviewDiagnosticReference,
    build_human_review_dialog_state,
    build_human_review_record_preview,
    build_human_review_save_plan,
    evaluate_human_review_actions,
    explain_human_review_action_state,
)


def _validator_summary(*, diagnostics: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "has_blockers": False,
        "has_errors": False,
        "diagnostics": diagnostics or [],
    }


def test_module_imports() -> None:
    import osw.experimental.feaspec.human_review_viewmodel as viewmodel

    assert viewmodel.HumanReviewDialogState is HumanReviewDialogState


def test_public_api_exports_required_types_and_functions() -> None:
    assert feaspec.HumanReviewDialogPanel is HumanReviewDialogPanel
    assert feaspec.HumanReviewDialogAction is HumanReviewDialogAction
    assert feaspec.HumanReviewActionAvailability is HumanReviewActionAvailability
    assert feaspec.HumanReviewDialogDiagnosticRow is HumanReviewDialogDiagnosticRow
    assert feaspec.HumanReviewDialogWarningRow is HumanReviewDialogWarningRow
    assert feaspec.HumanReviewRecordPreview is HumanReviewRecordPreview
    assert feaspec.HumanReviewSavePlan is HumanReviewSavePlan
    assert feaspec.HumanReviewDialogState is HumanReviewDialogState
    assert feaspec.build_human_review_dialog_state is build_human_review_dialog_state
    assert feaspec.evaluate_human_review_actions is evaluate_human_review_actions
    assert feaspec.build_human_review_record_preview is build_human_review_record_preview
    assert feaspec.build_human_review_save_plan is build_human_review_save_plan
    assert feaspec.explain_human_review_action_state is explain_human_review_action_state


def test_dialog_state_includes_all_required_panels() -> None:
    state = build_human_review_dialog_state()

    assert {panel.value for panel in state.panels} == {
        "source_evidence",
        "diagnostics",
        "engineering_summary",
        "export_preview",
        "review_actions",
        "safety_limitations",
        "record_preview",
    }


def test_diagnostic_rows_preserve_severity_code_and_message() -> None:
    state = build_human_review_dialog_state(
        validator_summary=_validator_summary(
            diagnostics=[
                {
                    "code": "FS_CONFIDENCE_LOW",
                    "severity": "warning",
                    "message": "Review inferred load direction.",
                    "target_ref": "load:L1",
                }
            ]
        )
    )

    assert state.diagnostics == (
        HumanReviewDialogDiagnosticRow(
            source="validator",
            severity="warning",
            code="FS_CONFIDENCE_LOW",
            message="Review inferred load direction.",
            target_ref="load:L1",
            accept_away_eligible=True,
        ),
    )


def test_record_preview_includes_state_action_source_and_reviewer() -> None:
    preview = build_human_review_record_preview(
        source_feaspec_id="cantilever-approved",
        reviewer="reviewer@example.test",
        reviewed_at="2026-06-18T00:00:00Z",
        desired_action=HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT,
        validator_summary=_validator_summary(),
        validator_report_hash="sha256:validator",
    )

    assert preview.state == "approved_for_no_run_export"
    assert preview.action == "approve_no_run_export"
    assert preview.source_feaspec_id == "cantilever-approved"
    assert preview.reviewer == "reviewer@example.test"
    assert preview.solver_execution_performed is False
    assert preview.json_payload["solver_execution_performed"] is False


def test_warning_rows_require_reason_for_acceptance() -> None:
    state = build_human_review_dialog_state(
        validator_summary=_validator_summary(
            diagnostics=[
                {
                    "code": "FS_CONFIDENCE_LOW",
                    "severity": "warning",
                    "message": "Review confidence.",
                }
            ]
        )
    )

    assert state.warnings[0].requires_reason is True
    assert state.warnings[0].can_accept is False


def test_warning_rows_accept_with_reason() -> None:
    state = build_human_review_dialog_state(
        validator_summary=_validator_summary(
            diagnostics=[
                {
                    "code": "FS_CONFIDENCE_LOW",
                    "severity": "warning",
                    "message": "Review confidence.",
                }
            ]
        ),
        accepted_warnings=(
            AcceptedWarning(
                diagnostic=ReviewDiagnosticReference(
                    code="FS_CONFIDENCE_LOW",
                    severity="warning",
                ),
                reason="reviewed source drawing",
            ),
        ),
    )

    assert state.warnings[0].accepted is True
    assert state.warnings[0].requires_reason is False


def test_save_plan_reports_parent_missing_without_creating_directory(tmp_path) -> None:
    missing_parent = tmp_path / "missing" / "review.json"

    plan = build_human_review_save_plan(missing_parent)

    assert plan.parent_missing is True
    assert plan.can_save is False
    assert not missing_parent.parent.exists()


def test_save_plan_reports_overwrite_needed_without_writing_file(tmp_path) -> None:
    review_path = tmp_path / "review.json"
    review_path.write_text("existing", encoding="utf-8")

    plan = build_human_review_save_plan(review_path)

    assert plan.overwrite_required is True
    assert plan.can_save is False
    assert review_path.read_text(encoding="utf-8") == "existing"


def test_viewmodel_output_is_deterministic_for_same_input() -> None:
    kwargs = {
        "source_feaspec_id": "cantilever-approved",
        "reviewer": "reviewer@example.test",
        "reviewed_at": "2026-06-18T00:00:00Z",
        "desired_action": HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT,
        "validator_summary": _validator_summary(),
        "validator_report_hash": "sha256:validator",
    }

    first = build_human_review_dialog_state(**kwargs)
    second = build_human_review_dialog_state(**kwargs)

    assert first == second
