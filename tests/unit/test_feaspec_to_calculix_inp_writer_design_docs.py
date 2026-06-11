from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = (
    REPO_ROOT / "docs" / "experimental" / "feaspec_to_calculix_inp_writer_design.md"
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


def _read() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_inp_writer_design_doc_exists() -> None:
    assert DESIGN_DOC.exists()


def test_inp_writer_design_status_and_non_execution_scope() -> None:
    text = _normalized()

    assert "design-only" in text
    assert "no writer implementation" in text
    assert "no generated `.inp` files" in text
    assert "no solver execution" in text
    assert "no calculix export" in text
    assert "no solveradapter handoff" in text
    assert "no runner handoff" in text


def test_inp_writer_design_defines_preconditions() -> None:
    text = _normalized()

    assert "writer preconditions" in text
    assert "feaspeccalculixcaseplan.ready_for_inp_writer == true" in text
    assert "feaspeccalculixcaseplan.ready_for_solver_execution == false" in text
    assert "separate run gate" in text
    assert "explicit node and element topology" in text
    assert "reviewed boundary-condition and load targets" in text


def test_inp_writer_design_defines_proposed_api_and_results() -> None:
    text = _read()

    for symbol in (
        "render_calculix_inp(case_plan) -> CalculiXInpRenderResult",
        "write_calculix_inp(case_plan, path, *, overwrite=False)",
        "explain_inp_render_result(result) -> list[str]",
        "CalculiXInpRenderResult",
        "CalculiXInpWriteResult",
        "CalculiXInpSection",
        "CalculiXInpDiagnostic",
    ):
        assert symbol in text


def test_inp_writer_design_defines_file_section_ordering() -> None:
    text = _read()

    for section in (
        "header/provenance comments",
        "*NODE",
        "*ELEMENT",
        "material cards",
        "boundary cards",
        "load cards",
        "*STEP",
        "*END STEP",
    ):
        assert section in text


def test_inp_writer_design_includes_required_fw_diagnostics() -> None:
    text = _read()

    for code in REQUIRED_FW_CODES:
        assert code in text


def test_inp_writer_design_defines_golden_fixture_strategy() -> None:
    text = _normalized()

    assert "golden fixture strategy" in text
    assert "tests/fixtures/feaspec/calculix_golden/" in text
    assert "compare normalized text" in text
    assert "no solver execution in golden writer tests" in text


def test_inp_writer_design_separates_issue_8_and_certification() -> None:
    text = _normalized()

    assert "issue `#8` is live calculix `ccx` validation" in text
    assert "remains separate" in text
    assert "does not validate a local `ccx` executable" in text
    assert "no industrial certification" in text


def test_inp_writer_design_does_not_claim_forbidden_maturity() -> None:
    text = _read().lower()
    forbidden_claims = (
        "writer implementation exists",
        "solver execution exists",
        "ccx validation passed",
        "abaqus export exists",
        "automatic solver execution is allowed",
        "industrial certification is provided",
    )
    for claim in forbidden_claims:
        assert claim not in text
