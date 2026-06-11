from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    BridgeDiagnosticCode,
    BridgeSeverity,
    BridgeStatus,
    plan_project_from_feaspec,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "feaspec"


def _codes(name: str) -> set[BridgeDiagnosticCode]:
    return plan_project_from_feaspec(EXAMPLES / name).diagnostic_codes


def test_candidate_example_is_blocked_with_approval_required() -> None:
    plan = plan_project_from_feaspec(EXAMPLES / "cantilever_beam_candidate.json")

    assert plan.status is BridgeStatus.BLOCKED
    assert plan.project_draft is None
    assert BridgeDiagnosticCode.FB_APPROVAL_REQUIRED in plan.diagnostic_codes
    assert BridgeDiagnosticCode.FB_VALIDATION_BLOCKED in plan.diagnostic_codes


def test_invalid_missing_units_is_blocked_with_units_diagnostic() -> None:
    plan = plan_project_from_feaspec(EXAMPLES / "invalid_missing_units.json")

    assert plan.status is BridgeStatus.BLOCKED
    assert BridgeDiagnosticCode.FB_UNITS_UNSUPPORTED in plan.diagnostic_codes


def test_invalid_load_target_is_blocked_or_reports_invalid_load_target() -> None:
    codes = _codes("invalid_load_target.json")

    assert BridgeDiagnosticCode.FB_INVALID_LOAD_TARGET in codes


def test_unknown_target_solver_is_blocked_with_solver_target_diagnostic() -> None:
    plan = plan_project_from_feaspec(
        EXAMPLES / "cantilever_beam_approved.json",
        target_solver="unknown_solver",
    )

    assert plan.status is BridgeStatus.BLOCKED
    assert BridgeDiagnosticCode.FB_SOLVER_TARGET_UNSUPPORTED in plan.diagnostic_codes


def test_explicit_abaqus_target_is_optional_non_default_warning() -> None:
    default_plan = plan_project_from_feaspec(EXAMPLES / "cantilever_beam_approved.json")
    abaqus_plan = plan_project_from_feaspec(
        EXAMPLES / "cantilever_beam_approved.json",
        target_solver="abaqus",
    )

    assert default_plan.solver_target == "calculix"
    assert abaqus_plan.solver_target == "abaqus"
    assert abaqus_plan.status is BridgeStatus.DRAFT_READY_WITH_WARNINGS
    diagnostic = next(
        item
        for item in abaqus_plan.diagnostics
        if item.code is BridgeDiagnosticCode.FB_SOLVER_TARGET_UNSUPPORTED
    )
    assert diagnostic.severity is BridgeSeverity.WARNING
    assert diagnostic.blocks_bridge is False
    assert diagnostic.blocks_solver_handoff is True
