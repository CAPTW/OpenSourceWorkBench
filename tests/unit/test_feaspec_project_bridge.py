from __future__ import annotations

from pathlib import Path

from osw.core.project_schema import Project
from osw.experimental.feaspec import (
    BridgeStatus,
    FEASpecProjectBridgePlan,
    explain_bridge_plan,
    plan_project_from_feaspec,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "feaspec"


def _plan(name: str) -> FEASpecProjectBridgePlan:
    return plan_project_from_feaspec(EXAMPLES / name)


def test_project_bridge_module_imports_and_exports_public_api() -> None:
    assert callable(plan_project_from_feaspec)
    assert callable(explain_bridge_plan)


def test_approved_cantilever_example_produces_project_draft_plan() -> None:
    plan = _plan("cantilever_beam_approved.json")

    assert plan.status in {
        BridgeStatus.DRAFT_READY,
        BridgeStatus.DRAFT_READY_WITH_WARNINGS,
    }
    assert plan.project_draft is not None
    assert plan.project_draft.problem_type == "linear_static_2d_beam"
    assert plan.project_draft.units["name"] == "SI"
    assert plan.project_draft.geometry_graph["nodes"]
    assert plan.project_draft.materials
    assert plan.project_draft.sections
    assert plan.project_draft.boundary_conditions
    assert plan.project_draft.loads
    assert plan.project_draft.solver_target == "calculix"
    assert plan.solver_export_performed is False
    assert plan.solver_execution_performed is False


def test_approved_truss_example_produces_project_draft_plan() -> None:
    plan = _plan("truss_2d_approved.json")

    assert plan.status in {
        BridgeStatus.DRAFT_READY,
        BridgeStatus.DRAFT_READY_WITH_WARNINGS,
    }
    assert plan.project_draft is not None
    assert plan.project_draft.problem_type == "linear_static_2d_truss"
    assert len(plan.project_draft.geometry_graph["nodes"]) == 3
    assert len(plan.project_draft.boundary_conditions) == 2
    assert len(plan.project_draft.loads) == 1


def test_bridge_plan_preserves_provenance_review_units_and_solver_metadata() -> None:
    plan = _plan("cantilever_beam_approved.json")

    assert plan.provenance.source["source_id"] == "cantilever_beam_approved"
    assert plan.provenance.evidence
    assert plan.provenance.confidence["overall"] == 1.0
    assert plan.provenance.human_review["action"] == "approved"
    assert plan.provenance.validation_summary["validation_state"] == "approved"
    assert plan.solver_target == "calculix"
    assert plan.project_draft is not None
    assert plan.project_draft.units["force"] == "N"


def test_bridge_plan_records_extension_needs_and_unmapped_fields() -> None:
    plan = _plan("cantilever_beam_approved.json")

    assert plan.extension_needs
    assert plan.unmapped_fields
    assert "geometry.geometry_graph" in plan.unmapped_fields
    assert "evidence/confidence" in plan.unmapped_fields
    assert any(need.source_field == "loads" for need in plan.extension_needs)


def test_bridge_plan_contains_project_schema_compatible_dict() -> None:
    plan = _plan("cantilever_beam_approved.json")

    assert plan.project_draft is not None
    project_dict = plan.project_draft.project_schema_compatible_dict
    assert project_dict["schema_version"] == "0.1"
    assert project_dict["metadata"]["name"].startswith("FEASpec bridge draft")
    assert project_dict["physics"][0]["solver_config"]["execution_mode"] == "prepare_only"
    project = Project.from_dict(project_dict)
    assert not project.validate().has_errors


def test_explain_bridge_plan_returns_user_readable_strings() -> None:
    plan = _plan("cantilever_beam_approved.json")
    lines = explain_bridge_plan(plan)

    assert lines
    assert any("Bridge status:" in line for line in lines)
    assert any("No solver export or solver execution" in line for line in lines)
