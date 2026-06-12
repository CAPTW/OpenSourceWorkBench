from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXCaseBoundaryConditionPlan,
    CalculiXCaseElementPlan,
    CalculiXCaseLoadPlan,
    CalculiXCaseMaterialPlan,
    CalculiXCaseNodePlan,
    CalculiXCaseOutputRequestPlan,
    CalculiXCaseSectionPlan,
    CalculiXCaseStatus,
    CalculiXCaseStepPlan,
    CalculiXInpDiagnosticCode,
    FEASpecCalculiXCasePlan,
    explain_inp_render_result,
    plan_calculix_case_from_feaspec,
    render_calculix_inp,
    write_calculix_inp,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "feaspec"


def _synthetic_ready_case_plan() -> FEASpecCalculiXCasePlan:
    nodes = (
        CalculiXCaseNodePlan("1", (0.0, 0.0, 0.0), source_ref="node_left_bottom"),
        CalculiXCaseNodePlan("2", (1.0, 0.0, 0.0), source_ref="node_right_bottom"),
        CalculiXCaseNodePlan("3", (1.0, 1.0, 0.0), source_ref="node_right_top"),
        CalculiXCaseNodePlan("4", (0.0, 1.0, 0.0), source_ref="node_left_top"),
        CalculiXCaseNodePlan("5", (0.0, 0.0, 1.0), source_ref="node_left_bottom_back"),
        CalculiXCaseNodePlan("6", (1.0, 0.0, 1.0), source_ref="node_right_bottom_back"),
        CalculiXCaseNodePlan("7", (1.0, 1.0, 1.0), source_ref="node_right_top_back"),
        CalculiXCaseNodePlan("8", (0.0, 1.0, 1.0), source_ref="node_left_top_back"),
    )
    return FEASpecCalculiXCasePlan(
        status=CalculiXCaseStatus.PLAN_READY,
        case_id="synthetic-ready-calculix-case-plan",
        source_feaspec_id="synthetic_ready",
        unit_context={"force": "N", "length": "m", "name": "SI", "stress": "Pa"},
        nodes=nodes,
        elements=(
            CalculiXCaseElementPlan(
                "1",
                "C3D8",
                tuple(node.node_id for node in nodes),
                source_ref="element_solid_1",
                metadata={"element_set": "EALL"},
            ),
        ),
        materials=(
            CalculiXCaseMaterialPlan(
                "mat_steel",
                "Steel",
                "isotropic_linear_elastic",
                properties={
                    "density": {"value": 7850.0, "units": "kg/m^3"},
                    "poisson_ratio": 0.3,
                    "young_modulus": {"value": 210_000_000_000.0, "units": "Pa"},
                },
                units={"stress": "Pa"},
                source_ref="material_steel",
            ),
        ),
        sections=(
            CalculiXCaseSectionPlan(
                "sec_solid",
                "mat_steel",
                ("EALL",),
                "solid",
                source_ref="section_solid",
            ),
        ),
        boundary_conditions=(
            CalculiXCaseBoundaryConditionPlan(
                "bc_fixed_left",
                "fixed",
                ("1",),
                ("ux", "uy", "uz"),
                (0.0, 0.0, 0.0),
                source_ref="bc_fixed_left",
            ),
        ),
        loads=(
            CalculiXCaseLoadPlan(
                "load_tip",
                "point_force",
                ("2",),
                vector=(0.0, -100.0, 0.0),
                units={"magnitude": "N"},
                source_ref="load_tip",
            ),
        ),
        steps=(CalculiXCaseStepPlan("linear_static", "static"),),
        output_requests=(
            CalculiXCaseOutputRequestPlan(
                "default_displacement_stress",
                "field",
                "all",
                ("U", "S"),
            ),
        ),
        provenance_comments=(
            "Human review: synthetic ready case approved for renderer unit tests.",
            "Source FEASpec: synthetic_ready.",
        ),
        ready_for_inp_writer=True,
        ready_for_solver_execution=False,
        inp_writer_performed=False,
        solver_execution_performed=False,
    )


def test_renderer_module_imports_and_public_api_exports() -> None:
    assert callable(render_calculix_inp)
    assert callable(write_calculix_inp)
    assert callable(explain_inp_render_result)


def test_render_blocks_if_case_plan_is_not_ready_for_writer() -> None:
    plan = replace(_synthetic_ready_case_plan(), ready_for_inp_writer=False)

    result = render_calculix_inp(plan)

    assert result.status == "blocked"
    assert result.text == ""
    assert CalculiXInpDiagnosticCode.FW_PLAN_NOT_READY in {
        diagnostic.code for diagnostic in result.diagnostics
    }
    assert result.ready_for_solver_execution is False


def test_approved_examples_block_until_explicit_mesh_topology_exists() -> None:
    for filename in ("cantilever_beam_approved.json", "truss_2d_approved.json"):
        plan = plan_calculix_case_from_feaspec(EXAMPLES / filename)

        result = render_calculix_inp(plan)

        codes = {diagnostic.code for diagnostic in result.diagnostics}
        assert result.status == "blocked"
        assert CalculiXInpDiagnosticCode.FW_PLAN_NOT_READY in codes
        assert CalculiXInpDiagnosticCode.FW_MESH_REQUIRED in codes
        assert result.ready_for_solver_execution is False


def test_candidate_and_invalid_examples_remain_blocked() -> None:
    for filename in ("cantilever_beam_candidate.json", "invalid_load_target.json"):
        plan = plan_calculix_case_from_feaspec(EXAMPLES / filename)

        result = render_calculix_inp(plan)

        assert result.status == "blocked"
        assert result.text == ""
        assert result.ready_for_solver_execution is False


def test_synthetic_ready_case_plan_renders_required_sections() -> None:
    result = render_calculix_inp(_synthetic_ready_case_plan())

    assert result.status == "rendered"
    assert result.ready_for_solver_execution is False
    assert result.text.endswith("\n")
    for expected in (
        "OpenSolver Workbench experimental FEASpec CalculiX INP renderer",
        "Source FEASpec: synthetic_ready",
        "Human review: synthetic ready case approved",
        "No industrial certification",
        "Solver execution was not performed",
        "*NODE",
        "*ELEMENT, TYPE=C3D8, ELSET=EALL",
        "*MATERIAL, NAME=mat_steel",
        "*ELASTIC",
        "*SOLID SECTION, ELSET=EALL, MATERIAL=mat_steel",
        "*BOUNDARY",
        "*CLOAD",
        "*STEP, NAME=linear_static",
        "*STATIC",
        "*NODE PRINT, NSET=NALL",
        "*EL PRINT, ELSET=EALL",
        "*END STEP",
    ):
        assert expected in result.text
    assert [section.name for section in result.sections] == [
        "header/provenance comments",
        "*NODE",
        "*ELEMENT",
        "material cards",
        "section/property cards",
        "boundary cards",
        "load cards",
        "*STEP",
        "output request cards",
        "*END STEP",
    ]


def test_rendered_text_is_deterministic_without_timestamps_or_certification_claim() -> None:
    first = render_calculix_inp(_synthetic_ready_case_plan())
    second = render_calculix_inp(_synthetic_ready_case_plan())
    lowered = first.text.lower()

    assert first.text == second.text
    assert "2026-" not in first.text
    assert "publishedat" not in lowered
    assert "certified" not in lowered
    assert "no industrial certification" in lowered
    assert "accuracy claim" in lowered
    assert "solver execution was not performed" in lowered


def test_write_calculix_inp_uses_caller_path_and_overwrite_guard(tmp_path: Path) -> None:
    plan = _synthetic_ready_case_plan()
    target = tmp_path / "synthetic_ready.inp"

    written = write_calculix_inp(plan, target)
    blocked = write_calculix_inp(plan, target)
    overwritten = write_calculix_inp(plan, target, overwrite=True)

    assert written.status == "written"
    assert written.path == target
    assert written.bytes_written == len(target.read_bytes())
    assert written.ready_for_solver_execution is False
    assert blocked.status == "blocked"
    assert CalculiXInpDiagnosticCode.FW_WRITE_PATH_EXISTS in {
        diagnostic.code for diagnostic in blocked.diagnostics
    }
    assert overwritten.status == "written"
    assert overwritten.ready_for_solver_execution is False


def test_write_calculix_inp_does_not_create_parent_directories(tmp_path: Path) -> None:
    target = tmp_path / "missing-parent" / "synthetic_ready.inp"

    result = write_calculix_inp(_synthetic_ready_case_plan(), target)

    assert result.status == "blocked"
    assert not target.parent.exists()
    assert result.ready_for_solver_execution is False


def test_explain_inp_render_result_returns_reviewer_readable_lines() -> None:
    result = render_calculix_inp(_synthetic_ready_case_plan())

    lines = explain_inp_render_result(result)

    assert any("CalculiX INP render status: rendered." in line for line in lines)
    assert any("Ready for solver execution: false." in line for line in lines)
    assert any("Rendered" in line and "deterministic INP lines" in line for line in lines)
    assert any("No CalculiX solver execution was performed." in line for line in lines)
