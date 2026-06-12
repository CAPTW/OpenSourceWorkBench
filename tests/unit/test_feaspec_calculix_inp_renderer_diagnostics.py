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
    CalculiXInpSeverity,
    FEASpecCalculiXCasePlan,
    FEASpecCalculiXInpDiagnostic,
    render_calculix_inp,
    write_calculix_inp,
)

REQUIRED_FW_CODES = {
    "FW_PLAN_NOT_READY",
    "FW_MESH_REQUIRED",
    "FW_UNSUPPORTED_ELEMENT_TYPE",
    "FW_NODE_MISSING",
    "FW_ELEMENT_MISSING",
    "FW_MATERIAL_MISSING",
    "FW_SECTION_MISSING",
    "FW_BC_INVALID_TARGET",
    "FW_LOAD_INVALID_TARGET",
    "FW_LOAD_UNSUPPORTED_TYPE",
    "FW_STEP_UNSUPPORTED",
    "FW_OUTPUT_UNSUPPORTED",
    "FW_WRITE_PATH_EXISTS",
    "FW_PROVENANCE_INCOMPLETE",
}


def _ready_plan() -> FEASpecCalculiXCasePlan:
    return FEASpecCalculiXCasePlan(
        status=CalculiXCaseStatus.PLAN_READY,
        case_id="diagnostic-ready-case",
        source_feaspec_id="diagnostic_ready",
        unit_context={"name": "SI", "length": "m", "force": "N"},
        nodes=(
            CalculiXCaseNodePlan("1", (0.0, 0.0, 0.0)),
            CalculiXCaseNodePlan("2", (1.0, 0.0, 0.0)),
        ),
        elements=(
            CalculiXCaseElementPlan(
                "1",
                "T3D2",
                ("1", "2"),
                metadata={"element_set": "EALL"},
            ),
        ),
        materials=(
            CalculiXCaseMaterialPlan(
                "mat",
                "Steel",
                "isotropic_linear_elastic",
                properties={"young_modulus": 200_000_000_000.0, "poisson_ratio": 0.29},
            ),
        ),
        sections=(CalculiXCaseSectionPlan("sec", "mat", ("EALL",), "truss"),),
        boundary_conditions=(
            CalculiXCaseBoundaryConditionPlan("bc", "fixed", ("1",), ("ux",), (0.0,)),
        ),
        loads=(CalculiXCaseLoadPlan("load", "point_force", ("2",), vector=(10.0, 0.0, 0.0)),),
        steps=(CalculiXCaseStepPlan("linear_static", "static"),),
        output_requests=(CalculiXCaseOutputRequestPlan("out", variables=("U", "S")),),
        provenance_comments=("Human review: diagnostic test case.",),
        ready_for_inp_writer=True,
        ready_for_solver_execution=False,
    )


def _codes(plan: FEASpecCalculiXCasePlan) -> set[CalculiXInpDiagnosticCode]:
    return {diagnostic.code for diagnostic in render_calculix_inp(plan).diagnostics}


def test_required_inp_diagnostic_codes_are_defined() -> None:
    assert {code.value for code in CalculiXInpDiagnosticCode} == REQUIRED_FW_CODES


def test_inp_diagnostic_defaults_block_error_and_blocker_severity() -> None:
    warning = FEASpecCalculiXInpDiagnostic.make(
        CalculiXInpDiagnosticCode.FW_PROVENANCE_INCOMPLETE,
        CalculiXInpSeverity.WARNING,
        "Provenance is incomplete.",
    )
    blocker = FEASpecCalculiXInpDiagnostic.make(
        CalculiXInpDiagnosticCode.FW_MESH_REQUIRED,
        CalculiXInpSeverity.BLOCKER,
        "Mesh is required.",
    )

    assert warning.blocks_render is False
    assert warning.blocks_write is False
    assert blocker.blocks_render is True
    assert blocker.blocks_write is True


def test_missing_nodes_and_elements_block_rendering() -> None:
    plan = replace(_ready_plan(), nodes=(), elements=())
    codes = _codes(plan)

    assert CalculiXInpDiagnosticCode.FW_NODE_MISSING in codes
    assert CalculiXInpDiagnosticCode.FW_MESH_REQUIRED in codes
    assert CalculiXInpDiagnosticCode.FW_ELEMENT_MISSING in codes


def test_unsupported_element_type_blocks_rendering() -> None:
    plan = replace(
        _ready_plan(),
        elements=(CalculiXCaseElementPlan("1", "UNKNOWN", ("1", "2")),),
    )

    assert CalculiXInpDiagnosticCode.FW_UNSUPPORTED_ELEMENT_TYPE in _codes(plan)


def test_missing_material_or_section_blocks_rendering() -> None:
    no_material = replace(_ready_plan(), materials=())
    no_section = replace(_ready_plan(), sections=())

    assert CalculiXInpDiagnosticCode.FW_MATERIAL_MISSING in _codes(no_material)
    assert CalculiXInpDiagnosticCode.FW_SECTION_MISSING in _codes(no_section)


def test_invalid_boundary_or_load_targets_block_rendering() -> None:
    bad_bc = replace(
        _ready_plan(),
        boundary_conditions=(
            CalculiXCaseBoundaryConditionPlan("bc", "fixed", ("missing",), ("ux",), (0.0,)),
        ),
    )
    bad_load = replace(
        _ready_plan(),
        loads=(CalculiXCaseLoadPlan("load", "point_force", ("missing",), vector=(1.0, 0.0, 0.0)),),
    )

    assert CalculiXInpDiagnosticCode.FW_BC_INVALID_TARGET in _codes(bad_bc)
    assert CalculiXInpDiagnosticCode.FW_LOAD_INVALID_TARGET in _codes(bad_load)


def test_empty_boundary_or_load_records_block_rendering() -> None:
    assert CalculiXInpDiagnosticCode.FW_BC_INVALID_TARGET in _codes(
        replace(_ready_plan(), boundary_conditions=())
    )
    assert CalculiXInpDiagnosticCode.FW_LOAD_INVALID_TARGET in _codes(
        replace(_ready_plan(), loads=())
    )


def test_unsupported_load_step_or_output_blocks_rendering() -> None:
    unsupported_load = replace(
        _ready_plan(),
        loads=(CalculiXCaseLoadPlan("load", "thermal_load", ("2",), magnitude={"value": 1.0}),),
    )
    unsupported_step = replace(
        _ready_plan(),
        steps=(CalculiXCaseStepPlan("nonlinear", "dynamic", nonlinear=True),),
    )
    unsupported_output = replace(
        _ready_plan(),
        output_requests=(CalculiXCaseOutputRequestPlan("out", variables=("RF",)),),
    )

    assert CalculiXInpDiagnosticCode.FW_LOAD_UNSUPPORTED_TYPE in _codes(unsupported_load)
    assert CalculiXInpDiagnosticCode.FW_STEP_UNSUPPORTED in _codes(unsupported_step)
    assert CalculiXInpDiagnosticCode.FW_OUTPUT_UNSUPPORTED in _codes(unsupported_output)


def test_missing_provenance_warns_without_blocking() -> None:
    result = render_calculix_inp(replace(_ready_plan(), provenance_comments=()))

    assert result.status == "rendered-with-warnings"
    assert CalculiXInpDiagnosticCode.FW_PROVENANCE_INCOMPLETE in {
        diagnostic.code for diagnostic in result.diagnostics
    }
    assert all(not diagnostic.blocks_render for diagnostic in result.diagnostics)


def test_write_path_exists_diagnostic_blocks_write_only(tmp_path: Path) -> None:
    target = tmp_path / "case.inp"
    target.write_text("already here", encoding="utf-8")

    result = write_calculix_inp(_ready_plan(), target)

    path_exists = [
        diagnostic
        for diagnostic in result.diagnostics
        if diagnostic.code is CalculiXInpDiagnosticCode.FW_WRITE_PATH_EXISTS
    ][0]
    assert result.status == "blocked"
    assert path_exists.blocks_render is False
    assert path_exists.blocks_write is True
