from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    HumanReviewDialogAction,
    build_human_review_dialog_state,
)


def _validator_summary(
    *,
    blockers: bool = False,
    errors: bool = False,
    diagnostics: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "has_blockers": blockers,
        "has_errors": errors,
        "diagnostics": diagnostics or [],
    }


def _ready_state(**overrides: object):
    kwargs = {
        "source_feaspec_id": "cantilever-approved",
        "reviewer": "reviewer@example.test",
        "reviewed_at": "2026-06-18T00:00:00Z",
        "notes": ("reviewed",),
        "desired_action": HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT,
        "validator_summary": _validator_summary(),
        "validator_report_hash": "sha256:validator",
        "bridge_summary": {"status": "ready"},
        "case_plan_summary": {"status": "ready"},
        "export_preview_summary": {"status": "ready"},
    }
    kwargs.update(overrides)
    return build_human_review_dialog_state(**kwargs)


def _availability(state, action: HumanReviewDialogAction):
    return state.availability_for(action)


def test_no_run_export_approval_disabled_when_reviewer_missing() -> None:
    state = _ready_state(reviewer="")

    availability = _availability(state, HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT)

    assert availability.enabled is False
    assert "missing reviewer" in availability.disabled_reasons


def test_no_run_export_approval_disabled_when_timestamp_missing() -> None:
    state = _ready_state(reviewed_at="")

    availability = _availability(state, HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT)

    assert availability.enabled is False
    assert "missing timestamp" in availability.disabled_reasons


def test_no_run_export_approval_disabled_when_source_id_missing() -> None:
    state = _ready_state(source_feaspec_id="")

    availability = _availability(state, HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT)

    assert availability.enabled is False
    assert "missing source id" in availability.disabled_reasons


def test_no_run_export_approval_disabled_when_validator_summary_missing() -> None:
    state = _ready_state(validator_summary={})

    availability = _availability(state, HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT)

    assert availability.enabled is False
    assert "missing validator summary" in availability.disabled_reasons


def test_no_run_export_approval_disabled_when_validator_hash_missing() -> None:
    state = _ready_state(validator_report_hash="")

    availability = _availability(state, HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT)

    assert availability.enabled is False
    assert "missing validator hash" in availability.disabled_reasons


def test_no_run_export_approval_disabled_when_blockers_exist() -> None:
    state = _ready_state(validator_summary=_validator_summary(blockers=True))

    availability = _availability(state, HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT)

    assert availability.enabled is False
    assert "validator blockers/errors exist" in availability.disabled_reasons


def test_no_run_export_approval_disabled_when_errors_exist() -> None:
    state = _ready_state(validator_summary=_validator_summary(errors=True))

    availability = _availability(state, HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT)

    assert availability.enabled is False
    assert "validator blockers/errors exist" in availability.disabled_reasons


def test_no_run_export_approval_disabled_with_unresolved_warning_reason() -> None:
    state = _ready_state(
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

    availability = _availability(state, HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT)

    assert availability.enabled is False
    assert "unresolved warning reasons exist" in availability.disabled_reasons


def test_no_run_export_approval_enabled_when_required_fields_present() -> None:
    state = _ready_state()

    availability = _availability(state, HumanReviewDialogAction.APPROVE_NO_RUN_EXPORT)

    assert availability.enabled is True
    assert availability.disabled_reasons == ()


def test_installed_only_run_request_disabled_without_no_run_export_ack() -> None:
    state = _ready_state(
        limitations_acknowledged=True,
        run_gate_separation_acknowledged=True,
    )

    availability = _availability(
        state,
        HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN,
    )

    assert availability.enabled is False
    assert "missing no-run export acknowledgement" in availability.disabled_reasons


def test_installed_only_run_request_disabled_without_readme_limitations_ack() -> None:
    state = _ready_state(
        no_run_export_review_acknowledged=True,
        run_gate_separation_acknowledged=True,
    )

    availability = _availability(
        state,
        HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN,
    )

    assert availability.enabled is False
    assert "missing README/limitations acknowledgement" in availability.disabled_reasons


def test_installed_only_run_request_disabled_without_run_gate_ack() -> None:
    state = _ready_state(
        no_run_export_review_acknowledged=True,
        limitations_acknowledged=True,
    )

    availability = _availability(
        state,
        HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN,
    )

    assert availability.enabled is False
    assert "missing run-gate-separate acknowledgement" in availability.disabled_reasons


def test_installed_only_run_request_enabled_only_with_acknowledgements() -> None:
    state = _ready_state(
        no_run_export_review_acknowledged=True,
        limitations_acknowledged=True,
        run_gate_separation_acknowledged=True,
    )

    availability = _availability(
        state,
        HumanReviewDialogAction.REQUEST_INSTALLED_ONLY_RUN,
    )

    assert availability.enabled is True


def test_needs_changes_action_can_be_enabled_with_notes() -> None:
    state = _ready_state(desired_action=HumanReviewDialogAction.MARK_NEEDS_CHANGES)

    availability = _availability(state, HumanReviewDialogAction.MARK_NEEDS_CHANGES)

    assert availability.enabled is True


def test_reject_action_can_be_enabled_with_notes() -> None:
    state = _ready_state(desired_action=HumanReviewDialogAction.REJECT)

    availability = _availability(state, HumanReviewDialogAction.REJECT)

    assert availability.enabled is True


def test_save_action_disabled_when_save_path_missing() -> None:
    state = _ready_state(save_path=None)

    availability = _availability(state, HumanReviewDialogAction.SAVE_RECORD)

    assert availability.enabled is False
    assert "save path is required" in availability.disabled_reasons


def test_save_action_enabled_for_safe_new_path(tmp_path: Path) -> None:
    state = _ready_state(save_path=tmp_path / "review.json")

    availability = _availability(state, HumanReviewDialogAction.SAVE_RECORD)

    assert availability.enabled is True
