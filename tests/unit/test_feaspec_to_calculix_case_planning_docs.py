from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLANNING_DOC = (
    REPO_ROOT / "docs" / "experimental" / "feaspec_to_calculix_case_planning.md"
)

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


def _read() -> str:
    return PLANNING_DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_feaspec_to_calculix_case_planning_doc_exists() -> None:
    assert PLANNING_DOC.exists()


def test_calculix_case_planning_status_and_non_execution_boundaries() -> None:
    text = _read().lower()

    assert "design-only" in text
    assert "no case generator" in text
    assert "no `.inp` writer" in text
    assert "no solver execution" in text
    assert "no calculix export" in text
    assert "no `ccx` execution" in text


def test_calculix_case_planning_defines_preconditions() -> None:
    text = _read().lower()

    assert "preconditions" in text
    assert "approved feaspec" in text
    assert "validator report has no blockers" in text
    assert "bridge plan status is `draft-ready` or `draft-ready-with-warnings`" in text
    assert "explicit units" in text
    assert "target solver is `calculix`" in text


def test_calculix_case_planning_defines_future_case_plan_object() -> None:
    text = _read()

    assert "FEASpecCalculiXCasePlan" in text
    for field in (
        "case_id",
        "source_feaspec_id",
        "target_solver",
        "unit_context",
        "nodes",
        "elements",
        "materials",
        "sections",
        "boundary_conditions",
        "loads",
        "steps",
        "output_requests",
        "provenance_comments",
        "diagnostics",
        "unmapped_fields",
    ):
        assert field in text


def test_calculix_case_planning_defines_mapping_areas() -> None:
    text = _read().lower()

    assert "geometry and mesh strategy" in text
    assert "node and element strategy" in text
    assert "materials and sections" in text
    assert "boundary conditions" in text
    assert "loads" in text
    assert "steps and output requests" in text
    assert "static linear" in text


def test_calculix_case_planning_mesh_and_geometry_boundaries() -> None:
    text = _normalized()

    assert "there is no meshing in this gate" in text
    assert "geometry graph" in text
    assert "not enough for a solver deck" in text
    assert "future case planning must require an explicit mesh source" in text
    assert "unsupported geometry blocks case generation" in text


def test_calculix_case_planning_includes_required_diagnostic_codes() -> None:
    text = _read()

    for code in REQUIRED_FC_CODES:
        assert code in text


def test_calculix_case_planning_solver_and_issue_boundaries() -> None:
    text = _normalized()

    assert "calculix-first" in text
    assert "issue `#8` is live calculix `ccx` validation" in text
    assert "remains separate" in text
    assert "planning gate" in text
    assert "does not run live optional validation" in text
    assert "abaqus remains optional and non-default" in text
    assert "does not require abaqus" in text


def test_calculix_case_planning_forbids_overtrust_and_certification() -> None:
    text = _read().lower()

    assert "no automatic unreviewed solver execution" in text
    assert "no industrial certification" in text
    assert "no live optional validation" in text


def test_calculix_case_planning_does_not_claim_forbidden_implementation() -> None:
    text = _read().lower()
    forbidden_claims = (
        "case generator implementation exists",
        "calculix case generator exists",
        ".inp writer exists",
        "solver execution exists",
        "ccx validation passed",
        "abaqus export exists",
        "vfea implementation is complete",
        "automatic solver execution is allowed",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text
