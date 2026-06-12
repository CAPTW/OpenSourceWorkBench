from __future__ import annotations

import ast
import hashlib
import json
import re
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
    FEASpecCalculiXCasePlan,
    render_calculix_inp,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "feaspec" / "calculix_golden"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
README_PATH = FIXTURE_DIR / "README.md"
DOC_PATH = REPO_ROOT / "docs" / "experimental" / "feaspec_to_calculix_inp_golden_fixtures.md"
EXPECTED_FIXTURES = ("cantilever_minimal.inp", "truss_minimal.inp")


def _normalize_inp_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _cantilever_case_plan() -> FEASpecCalculiXCasePlan:
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


def _truss_case_plan() -> FEASpecCalculiXCasePlan:
    nodes = (
        CalculiXCaseNodePlan("1", (0.0, 0.0, 0.0), source_ref="truss_left_support"),
        CalculiXCaseNodePlan("2", (1.0, 0.0, 0.0), source_ref="truss_right_loaded_node"),
    )
    return FEASpecCalculiXCasePlan(
        status=CalculiXCaseStatus.PLAN_READY,
        case_id="synthetic-truss-calculix-case-plan",
        source_feaspec_id="synthetic_truss",
        unit_context={"force": "N", "length": "m", "name": "SI", "stress": "Pa"},
        nodes=nodes,
        elements=(
            CalculiXCaseElementPlan(
                "1",
                "T3D2",
                ("1", "2"),
                source_ref="element_truss_1",
                metadata={"element_set": "EALL"},
            ),
        ),
        materials=(
            CalculiXCaseMaterialPlan(
                "mat_aluminum",
                "Aluminum",
                "isotropic_linear_elastic",
                properties={
                    "density": {"value": 2700.0, "units": "kg/m^3"},
                    "poisson_ratio": 0.33,
                    "young_modulus": {"value": 70_000_000_000.0, "units": "Pa"},
                },
                units={"stress": "Pa"},
                source_ref="material_aluminum",
            ),
        ),
        sections=(
            CalculiXCaseSectionPlan(
                "sec_truss",
                "mat_aluminum",
                ("EALL",),
                "truss",
                properties={"area": {"value": 0.0001, "units": "m^2"}},
                source_ref="section_truss",
            ),
        ),
        boundary_conditions=(
            CalculiXCaseBoundaryConditionPlan(
                "bc_fixed_node_1",
                "fixed",
                ("1",),
                ("ux", "uy", "uz"),
                (0.0, 0.0, 0.0),
                source_ref="bc_fixed_node_1",
            ),
        ),
        loads=(
            CalculiXCaseLoadPlan(
                "load_node_2",
                "point_force",
                ("2",),
                vector=(100.0, 0.0, 0.0),
                units={"magnitude": "N"},
                source_ref="load_node_2",
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
            "Human review: synthetic truss case approved for golden fixture.",
            "Source FEASpec: synthetic_truss.",
        ),
        ready_for_inp_writer=True,
        ready_for_solver_execution=False,
        inp_writer_performed=False,
        solver_execution_performed=False,
    )


def test_golden_fixture_directory_readme_manifest_and_expected_files_exist() -> None:
    assert FIXTURE_DIR.is_dir()
    assert README_PATH.is_file()
    assert MANIFEST_PATH.is_file()
    for filename in EXPECTED_FIXTURES:
        assert (FIXTURE_DIR / filename).is_file()


def test_manifest_parses_and_sha256_matches_files() -> None:
    manifest = _manifest()
    fixtures = manifest["fixtures"]

    assert manifest["renderer_status"] == "no-run"
    assert isinstance(fixtures, list)
    assert {item["filename"] for item in fixtures} == set(EXPECTED_FIXTURES)
    for item in fixtures:
        payload = (FIXTURE_DIR / item["filename"]).read_bytes()
        assert item["sha256"] == hashlib.sha256(payload).hexdigest()
        assert item["note"] == "No solver was run; this is deterministic renderer text only."


def test_readme_records_no_run_fixture_limits() -> None:
    text = README_PATH.read_text(encoding="utf-8").lower()

    assert "no-run golden text fixtures" in text
    assert "not solver outputs" in text
    assert "were not produced by running calculix" in text
    assert "deterministic renderer text" in text
    assert "not evidence of engineering correctness" in text
    assert "not industrial certification" in text
    assert "issue #8" in text


def test_documentation_records_no_run_fixture_boundary() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "# feaspec calculix inp golden fixtures" in text
    assert "no-run golden text fixtures" in text
    assert "not solver outputs" in text
    assert "not validation results" in text
    assert "no `ccx`" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no subprocess" in text
    assert "issue `#8`" in text
    assert "do not close issue `#8`" in text


def test_inp_fixtures_contain_required_calculix_sections() -> None:
    for filename in EXPECTED_FIXTURES:
        text = (FIXTURE_DIR / filename).read_text(encoding="utf-8")
        for expected in (
            "*NODE",
            "*ELEMENT",
            "*MATERIAL",
            "*ELASTIC",
            "*SOLID SECTION",
            "*BOUNDARY",
            "*CLOAD",
            "*STEP",
            "*END STEP",
        ):
            assert expected in text
        assert "*NODE PRINT" in text or "*EL PRINT" in text


def test_inp_fixtures_do_not_contain_timestamps_paths_or_solver_output_markers() -> None:
    timestamp_pattern = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b|T\d{2}:\d{2}:\d{2}")
    local_path_pattern = re.compile(r"[A-Za-z]:[\\/]|/(Users|home|tmp|var|opt)/")
    solver_output_markers = (
        ".frd",
        ".dat",
        ".sta",
        ".cvg",
        ".12d",
        ".out",
        ".err",
        "total time",
        "job finished",
        "calculix solver output",
    )
    forbidden_positive_claims = (
        "industrial certification is provided",
        "certified for production",
        "validated by ccx",
    )

    for filename in EXPECTED_FIXTURES:
        text = (FIXTURE_DIR / filename).read_text(encoding="utf-8")
        lowered = text.lower()
        assert timestamp_pattern.search(text) is None
        assert local_path_pattern.search(text) is None
        assert not any(marker in lowered for marker in solver_output_markers)
        assert "no industrial certification" in lowered
        assert not any(claim in lowered for claim in forbidden_positive_claims)


def test_renderer_output_matches_cantilever_golden_fixture_with_normalization() -> None:
    result = render_calculix_inp(_cantilever_case_plan())
    golden = (FIXTURE_DIR / "cantilever_minimal.inp").read_text(encoding="utf-8")

    assert result.status == "rendered"
    assert result.ready_for_solver_execution is False
    assert _normalize_inp_text(result.text) == _normalize_inp_text(golden)


def test_renderer_output_matches_truss_golden_fixture_with_normalization() -> None:
    result = render_calculix_inp(_truss_case_plan())
    golden = (FIXTURE_DIR / "truss_minimal.inp").read_text(encoding="utf-8")

    assert result.status == "rendered"
    assert result.ready_for_solver_execution is False
    assert _normalize_inp_text(result.text) == _normalize_inp_text(golden)


def test_golden_fixture_tests_do_not_call_external_process_helpers() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    forbidden_import_roots = {"sub" + "process", "os"}
    forbidden_call_names = {"Popen", "system", "spawn", "execv", "run_input_deck"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(alias.name in forbidden_import_roots for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "") not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
