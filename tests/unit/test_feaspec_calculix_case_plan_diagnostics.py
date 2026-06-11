from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXCaseStatus,
    CalculiXPlanDiagnosticCode,
    CalculiXPlanSeverity,
    FEASpecCalculiXPlanDiagnostic,
    plan_calculix_case_from_feaspec,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "feaspec"

REQUIRED_FC_CODES = {
    "FC_APPROVAL_REQUIRED",
    "FC_VALIDATION_BLOCKED",
    "FC_BRIDGE_BLOCKED",
    "FC_MESH_REQUIRED",
    "FC_UNSUPPORTED_GEOMETRY",
    "FC_UNSUPPORTED_ELEMENT_TYPE",
    "FC_MATERIAL_MISSING",
    "FC_SECTION_MISSING",
    "FC_BC_INVALID_TARGET",
    "FC_BC_INSUFFICIENT_CONSTRAINTS",
    "FC_LOAD_INVALID_TARGET",
    "FC_LOAD_UNSUPPORTED_TYPE",
    "FC_UNITS_UNSUPPORTED",
    "FC_STEP_UNSUPPORTED",
    "FC_OUTPUT_UNSUPPORTED",
    "FC_PROVENANCE_INCOMPLETE",
}


def _codes(name: str) -> set[CalculiXPlanDiagnosticCode]:
    return plan_calculix_case_from_feaspec(EXAMPLES / name).diagnostic_codes


def test_required_calculix_case_plan_diagnostic_codes_are_defined() -> None:
    assert {code.value for code in CalculiXPlanDiagnosticCode} == REQUIRED_FC_CODES


def test_calculix_plan_diagnostic_defaults_block_error_and_blocker_severity() -> None:
    warning = FEASpecCalculiXPlanDiagnostic.make(
        CalculiXPlanDiagnosticCode.FC_PROVENANCE_INCOMPLETE,
        CalculiXPlanSeverity.WARNING,
        "Provenance needs review.",
    )
    error = FEASpecCalculiXPlanDiagnostic.make(
        CalculiXPlanDiagnosticCode.FC_MESH_REQUIRED,
        CalculiXPlanSeverity.ERROR,
        "Mesh is required.",
    )

    assert warning.blocks_case_plan is False
    assert warning.blocks_solver_handoff is True
    assert error.blocks_case_plan is True


def test_candidate_example_is_blocked_with_approval_required() -> None:
    plan = plan_calculix_case_from_feaspec(EXAMPLES / "cantilever_beam_candidate.json")

    assert plan.status is CalculiXCaseStatus.BLOCKED
    assert CalculiXPlanDiagnosticCode.FC_APPROVAL_REQUIRED in plan.diagnostic_codes
    assert CalculiXPlanDiagnosticCode.FC_VALIDATION_BLOCKED in plan.diagnostic_codes
    assert CalculiXPlanDiagnosticCode.FC_BRIDGE_BLOCKED in plan.diagnostic_codes
    assert plan.ready_for_inp_writer is False
    assert plan.ready_for_solver_execution is False


def test_invalid_missing_units_is_blocked_with_units_or_validation_diagnostic() -> None:
    codes = _codes("invalid_missing_units.json")

    assert CalculiXPlanDiagnosticCode.FC_UNITS_UNSUPPORTED in codes
    assert CalculiXPlanDiagnosticCode.FC_VALIDATION_BLOCKED in codes


def test_invalid_load_target_is_blocked_with_load_target_diagnostic() -> None:
    codes = _codes("invalid_load_target.json")

    assert CalculiXPlanDiagnosticCode.FC_LOAD_INVALID_TARGET in codes
    assert CalculiXPlanDiagnosticCode.FC_VALIDATION_BLOCKED in codes


def test_invalid_unconnected_graph_is_blocked_by_validation() -> None:
    codes = _codes("invalid_unconnected_graph.json")

    assert CalculiXPlanDiagnosticCode.FC_VALIDATION_BLOCKED in codes
    assert CalculiXPlanDiagnosticCode.FC_BRIDGE_BLOCKED in codes


def test_non_calculix_bridge_target_is_not_silently_accepted() -> None:
    plan = plan_calculix_case_from_feaspec(
        EXAMPLES / "cantilever_beam_approved.json",
        target_solver="abaqus",
    )

    assert plan.status is CalculiXCaseStatus.BLOCKED
    assert CalculiXPlanDiagnosticCode.FC_BRIDGE_BLOCKED in plan.diagnostic_codes
    assert plan.target_solver == "calculix"


def test_approved_examples_without_explicit_mesh_are_blocked_for_writer() -> None:
    for filename in ("cantilever_beam_approved.json", "truss_2d_approved.json"):
        plan = plan_calculix_case_from_feaspec(EXAMPLES / filename)
        assert CalculiXPlanDiagnosticCode.FC_MESH_REQUIRED in plan.diagnostic_codes
        assert plan.ready_for_inp_writer is False
        assert plan.ready_for_solver_execution is False
