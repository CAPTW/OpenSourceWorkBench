from __future__ import annotations

import hashlib
import json
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
    CalculiXExportDiagnosticCode,
    FEASpecCalculiXCasePlan,
    explain_calculix_export_result,
    export_calculix_case,
    export_calculix_case_from_bridge,
    export_calculix_case_from_feaspec,
    plan_calculix_case_from_feaspec,
    plan_project_from_feaspec,
    render_calculix_inp,
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
            "Human review: synthetic ready case approved for exporter unit tests.",
            "Source FEASpec: synthetic_ready.",
        ),
        ready_for_inp_writer=True,
        ready_for_solver_execution=False,
        inp_writer_performed=False,
        solver_execution_performed=False,
    )


def _codes(result: object) -> set[CalculiXExportDiagnosticCode]:
    diagnostics = result.diagnostics
    return {diagnostic.code for diagnostic in diagnostics}


def test_exporter_module_imports_and_public_api_exports() -> None:
    assert callable(export_calculix_case)
    assert callable(export_calculix_case_from_feaspec)
    assert callable(export_calculix_case_from_bridge)
    assert callable(explain_calculix_export_result)


def test_export_blocks_when_renderer_blocks_and_writes_nothing(tmp_path: Path) -> None:
    plan = replace(_synthetic_ready_case_plan(), ready_for_inp_writer=False)

    result = export_calculix_case(plan, tmp_path, basename="blocked")

    assert result.status == "blocked"
    assert CalculiXExportDiagnosticCode.FX_RENDER_BLOCKED in _codes(result)
    assert result.ready_for_solver_execution is False
    assert result.solver_execution_performed is False
    assert list(tmp_path.iterdir()) == []


def test_export_blocks_approved_examples_until_explicit_mesh_topology_exists(
    tmp_path: Path,
) -> None:
    for filename in ("cantilever_beam_approved.json", "truss_2d_approved.json"):
        plan = plan_calculix_case_from_feaspec(EXAMPLES / filename)
        target = tmp_path / filename.removesuffix(".json")
        target.mkdir()

        result = export_calculix_case(plan, target)

        assert result.status == "blocked"
        assert CalculiXExportDiagnosticCode.FX_RENDER_BLOCKED in _codes(result)
        assert list(target.iterdir()) == []


def test_candidate_and_invalid_examples_remain_blocked(tmp_path: Path) -> None:
    for filename in ("cantilever_beam_candidate.json", "invalid_load_target.json"):
        target = tmp_path / filename.removesuffix(".json")
        target.mkdir()

        result = export_calculix_case_from_feaspec(EXAMPLES / filename, target)

        assert result.status == "blocked"
        assert CalculiXExportDiagnosticCode.FX_RENDER_BLOCKED in _codes(result)
        assert list(target.iterdir()) == []


def test_export_synthetic_ready_case_writes_exact_no_run_bundle(
    tmp_path: Path,
) -> None:
    plan = _synthetic_ready_case_plan()

    result = export_calculix_case(plan, tmp_path, basename="ready_case")

    assert result.status == "exported"
    assert result.ready_for_solver_execution is False
    assert result.solver_execution_performed is False
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "README_RUN_FIRST.txt",
        "ready_case.diagnostics.json",
        "ready_case.inp",
        "ready_case.manifest.json",
    ]
    assert {item.filename for item in result.files} == {
        "ready_case.inp",
        "ready_case.manifest.json",
        "ready_case.diagnostics.json",
        "README_RUN_FIRST.txt",
    }


def test_export_manifest_parses_and_records_checksums(tmp_path: Path) -> None:
    result = export_calculix_case(
        _synthetic_ready_case_plan(),
        tmp_path,
        basename="ready_case",
    )
    manifest = json.loads((tmp_path / "ready_case.manifest.json").read_text())

    assert manifest["exporter_module"] == "osw.experimental.feaspec.calculix_exporter"
    assert manifest["osw_version"] == "0.1.5rc3"
    assert manifest["release_tag"] == "v0.1.5-rc3"
    assert manifest["target_solver"] == "calculix"
    assert manifest["source_feaspec_id"] == "synthetic_ready"
    assert manifest["solver_execution_performed"] is False
    assert manifest["ready_for_solver_execution"] is False
    assert len(manifest["files"]) == 3
    for item in manifest["files"]:
        payload = (tmp_path / item["filename"]).read_bytes()
        assert item["sha256"] == hashlib.sha256(payload).hexdigest()
        assert item["size_bytes"] == len(payload)
    assert result.manifest is not None
    assert result.manifest.to_dict()["solver_execution_performed"] is False


def test_export_diagnostics_json_and_readme_record_no_run_boundary(
    tmp_path: Path,
) -> None:
    export_calculix_case(_synthetic_ready_case_plan(), tmp_path, basename="ready_case")
    diagnostics = json.loads((tmp_path / "ready_case.diagnostics.json").read_text())
    readme = (tmp_path / "README_RUN_FIRST.txt").read_text(encoding="utf-8").lower()

    assert diagnostics["status"] == "exported"
    assert diagnostics["solver_execution_performed"] is False
    assert diagnostics["ready_for_solver_execution"] is False
    assert any(
        item["code"] == "FX_SOLVER_RUN_FORBIDDEN"
        for item in diagnostics["export_diagnostics"]
    )
    assert "no solver execution was performed" in readme
    assert "inspect" in readme
    assert "calculix is not bundled" in readme
    assert "experimental" in readme
    assert "no industrial certification" in readme
    assert "issue #8" in readme


def test_exported_inp_text_matches_renderer_output(tmp_path: Path) -> None:
    plan = _synthetic_ready_case_plan()
    expected = render_calculix_inp(plan).text

    export_calculix_case(plan, tmp_path, basename="ready_case")

    assert (tmp_path / "ready_case.inp").read_text(encoding="utf-8") == expected


def test_export_from_bridge_blocks_without_explicit_mesh(tmp_path: Path) -> None:
    bridge_plan = plan_project_from_feaspec(EXAMPLES / "cantilever_beam_approved.json")

    result = export_calculix_case_from_bridge(bridge_plan, tmp_path)

    assert result.status == "blocked"
    assert CalculiXExportDiagnosticCode.FX_RENDER_BLOCKED in _codes(result)
    assert list(tmp_path.iterdir()) == []


def test_export_refuses_missing_output_dir_unless_create_dir(tmp_path: Path) -> None:
    missing = tmp_path / "bundle"

    blocked = export_calculix_case(_synthetic_ready_case_plan(), missing)
    created = export_calculix_case(
        _synthetic_ready_case_plan(),
        missing,
        create_dir=True,
    )

    assert blocked.status == "blocked"
    assert CalculiXExportDiagnosticCode.FX_OUTPUT_DIR_MISSING in _codes(blocked)
    assert created.status == "exported"
    assert missing.is_dir()


def test_export_refuses_output_path_that_is_not_directory(tmp_path: Path) -> None:
    target = tmp_path / "not-a-dir"
    target.write_text("file", encoding="utf-8")

    result = export_calculix_case(_synthetic_ready_case_plan(), target)

    assert result.status == "blocked"
    assert CalculiXExportDiagnosticCode.FX_OUTPUT_DIR_NOT_DIRECTORY in _codes(result)


def test_export_refuses_unsafe_basenames(tmp_path: Path) -> None:
    for basename in ("nested/case", "../case", r"..\case", "C:case", "bad*case"):
        result = export_calculix_case(
            _synthetic_ready_case_plan(),
            tmp_path,
            basename=basename,
        )

        assert result.status == "blocked"
        assert CalculiXExportDiagnosticCode.FX_UNSAFE_BASENAME in _codes(result)


def test_export_refuses_nonempty_output_dir_by_default(tmp_path: Path) -> None:
    (tmp_path / "unrelated.txt").write_text("keep me", encoding="utf-8")

    result = export_calculix_case(_synthetic_ready_case_plan(), tmp_path)

    assert result.status == "blocked"
    assert CalculiXExportDiagnosticCode.FX_OUTPUT_DIR_NOT_EMPTY in _codes(result)


def test_export_refuses_existing_target_files_without_overwrite(tmp_path: Path) -> None:
    export_calculix_case(_synthetic_ready_case_plan(), tmp_path, basename="ready_case")

    result = export_calculix_case(
        _synthetic_ready_case_plan(),
        tmp_path,
        basename="ready_case",
    )

    assert result.status == "blocked"
    assert CalculiXExportDiagnosticCode.FX_OUTPUT_EXISTS in _codes(result)


def test_export_overwrites_only_known_target_files(tmp_path: Path) -> None:
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("keep me", encoding="utf-8")
    stale = tmp_path / "ready_case.inp"
    stale.write_text("stale", encoding="utf-8")

    result = export_calculix_case(
        _synthetic_ready_case_plan(),
        tmp_path,
        basename="ready_case",
        overwrite=True,
    )

    assert result.status == "exported"
    assert unrelated.read_text(encoding="utf-8") == "keep me"
    assert stale.read_text(encoding="utf-8") != "stale"
    assert (tmp_path / "ready_case.manifest.json").is_file()
    assert (tmp_path / "ready_case.diagnostics.json").is_file()
    assert (tmp_path / "README_RUN_FIRST.txt").is_file()


def test_explain_calculix_export_result_returns_user_readable_lines(
    tmp_path: Path,
) -> None:
    result = export_calculix_case(
        _synthetic_ready_case_plan(),
        tmp_path,
        basename="ready_case",
    )

    lines = explain_calculix_export_result(result)

    assert any("CalculiX export status: exported." in line for line in lines)
    assert any("Ready for solver execution: false." in line for line in lines)
    assert any("Solver execution performed: false." in line for line in lines)
    assert any("ready_case.inp" in line for line in lines)
    assert any("No CalculiX solver execution was performed." in line for line in lines)
