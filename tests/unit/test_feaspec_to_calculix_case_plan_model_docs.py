from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_DOC = REPO_ROOT / "docs" / "experimental" / "feaspec_to_calculix_case_plan_model.md"


def _read() -> str:
    return MODEL_DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_case_plan_model_doc_exists() -> None:
    assert MODEL_DOC.exists()


def test_case_plan_model_doc_states_experimental_status_and_scope() -> None:
    text = _normalized()

    assert "experimental case-plan model" in text
    assert "not a `.inp` writer" in text
    assert "not a solver adapter" in text
    assert "not a runner" in text
    assert "no solver execution" in text


def test_case_plan_model_doc_defines_public_api_and_statuses() -> None:
    text = _read()

    for symbol in (
        "plan_calculix_case_from_feaspec",
        "plan_calculix_case_from_bridge",
        "explain_calculix_case_plan",
        "FEASpecCalculiXCasePlan",
        "CalculiXCaseStatus",
        "blocked",
        "plan-ready",
        "plan-ready-with-warnings",
    ):
        assert symbol in text


def test_case_plan_model_doc_defines_plan_record_areas() -> None:
    text = _read()

    for symbol in (
        "CalculiXCaseNodePlan",
        "CalculiXCaseElementPlan",
        "CalculiXCaseMaterialPlan",
        "CalculiXCaseSectionPlan",
        "CalculiXCaseBoundaryConditionPlan",
        "CalculiXCaseLoadPlan",
        "CalculiXCaseStepPlan",
        "CalculiXCaseOutputRequestPlan",
    ):
        assert symbol in text


def test_case_plan_model_doc_includes_required_diagnostics() -> None:
    text = _read()

    for code in (
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
    ):
        assert code in text


def test_case_plan_model_doc_records_readiness_boundaries() -> None:
    text = _normalized()

    assert "ready_for_inp_writer" in text
    assert "ready_for_solver_execution" in text
    assert "always `false`" in text
    assert "explicit mesh or element topology" in text
    assert "geometry graph remains provenance" in text


def test_case_plan_model_doc_does_not_claim_forbidden_maturity() -> None:
    text = _read().lower()
    forbidden_claims = (
        "solver execution exists",
        "ccx execution exists",
        "inp writer exists",
        "calculix export exists",
        "abaqus is mandatory",
        "industrial certification is provided",
        "native commercial cad import exists",
        "vfea implementation is complete",
    )
    for claim in forbidden_claims:
        assert claim not in text
