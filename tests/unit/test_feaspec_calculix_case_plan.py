from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXCaseStatus,
    CalculiXPlanDiagnosticCode,
    FEASpecCalculiXCasePlan,
    explain_calculix_case_plan,
    plan_calculix_case_from_bridge,
    plan_calculix_case_from_feaspec,
    plan_project_from_feaspec,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "feaspec"


def _plan(name: str) -> FEASpecCalculiXCasePlan:
    return plan_calculix_case_from_feaspec(EXAMPLES / name)


def test_case_plan_module_imports_and_exports_public_api() -> None:
    assert callable(plan_calculix_case_from_feaspec)
    assert callable(plan_calculix_case_from_bridge)
    assert callable(explain_calculix_case_plan)


def test_approved_cantilever_example_returns_planning_object_only() -> None:
    plan = _plan("cantilever_beam_approved.json")

    assert plan.status is CalculiXCaseStatus.BLOCKED
    assert plan.case_id == "cantilever_beam_approved-calculix-case-plan"
    assert plan.source_feaspec_id == "cantilever_beam_approved"
    assert plan.target_solver == "calculix"
    assert plan.unit_context["name"] == "SI"
    assert len(plan.nodes) == 2
    assert len(plan.elements) == 0
    assert plan.materials[0].material_id == "mat_steel"
    assert plan.sections[0].section_id == "sec_rect"
    assert plan.boundary_conditions[0].bc_id == "bc_fixed_left"
    assert plan.loads[0].load_id == "load_tip"
    assert plan.steps[0].analysis_type == "static"
    assert plan.steps[0].metadata["planned_only"] is True
    assert plan.output_requests[0].variables == ("U", "S")
    assert CalculiXPlanDiagnosticCode.FC_MESH_REQUIRED in plan.diagnostic_codes
    assert plan.ready_for_inp_writer is False
    assert plan.ready_for_solver_execution is False
    assert plan.inp_writer_performed is False
    assert plan.solver_execution_performed is False


def test_approved_truss_example_preserves_reviewed_records() -> None:
    plan = _plan("truss_2d_approved.json")

    assert plan.source_feaspec_id == "truss_2d_approved"
    assert len(plan.nodes) == 3
    assert len(plan.boundary_conditions) == 2
    assert len(plan.loads) == 1
    assert plan.sections[0].target_refs == ("e_left", "e_right", "e_bottom")
    assert plan.loads[0].units["magnitude"] == "N"
    assert CalculiXPlanDiagnosticCode.FC_MESH_REQUIRED in plan.diagnostic_codes


def test_case_plan_can_start_from_project_bridge_plan() -> None:
    bridge_plan = plan_project_from_feaspec(EXAMPLES / "cantilever_beam_approved.json")

    plan = plan_calculix_case_from_bridge(bridge_plan)

    assert plan.source_feaspec_id == "cantilever_beam_approved"
    assert plan.bridge_status == bridge_plan.status
    assert plan.validator_report
    assert "geometry.geometry_graph" in plan.unmapped_fields
    assert any(need.source_field == "loads" for need in plan.extension_needs)


def test_case_plan_serializes_to_stable_dict() -> None:
    plan = _plan("cantilever_beam_approved.json")
    payload = plan.to_dict()

    assert payload["status"] == "blocked"
    assert payload["case_id"] == "cantilever_beam_approved-calculix-case-plan"
    assert payload["ready_for_inp_writer"] is False
    assert payload["ready_for_solver_execution"] is False
    assert payload["nodes"]
    assert payload["materials"]
    assert payload["diagnostics"]


def test_explain_calculix_case_plan_returns_reviewer_lines() -> None:
    plan = _plan("cantilever_beam_approved.json")
    lines = explain_calculix_case_plan(plan)

    assert any("CalculiX case-plan status:" in line for line in lines)
    assert any("not ready for a `.inp` writer" in line for line in lines)
    assert any("FC_MESH_REQUIRED" in line for line in lines)
    assert any("No `.inp` writer or solver execution" in line for line in lines)
