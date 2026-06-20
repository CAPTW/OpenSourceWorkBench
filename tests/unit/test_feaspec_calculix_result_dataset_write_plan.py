from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from osw.experimental.feaspec import (
    CalculiXResultDatasetWriteDiagnosticCode,
    FEASpecCalculiXResultDatasetArtifactReferencePlan,
    FEASpecCalculiXResultDatasetAtomicWritePlan,
    FEASpecCalculiXResultDatasetPlannedFile,
    FEASpecCalculiXResultDatasetWritePlan,
    FEASpecCalculiXResultDatasetWritePlanValidation,
    FEASpecCalculiXResultDatasetWriteStatus,
    FEASpecCalculiXResultDatasetWriteTarget,
    build_calculix_result_dataset_draft_mapping,
    explain_calculix_result_dataset_write_plan,
    plan_calculix_result_dataset_write,
    plan_calculix_result_import,
    validate_calculix_result_dataset_write_plan,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_result_dir(root: Path) -> Path:
    root.mkdir()
    _write_json(
        root / "run_metadata.json",
        {
            "status": "ran",
            "solver_execution_performed": True,
            "exit_code": 0,
            "timed_out": False,
            "source_feaspec_id": "write_plan_feaspec",
            "case_id": "write_plan_case",
            "osw_version": "0.1.4rc1",
            "scalar_summaries": {"metadata_only": "preserved"},
        },
    )
    _write_json(
        root / "write_plan_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "write_plan_feaspec",
            "case_id": "write_plan_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "write_plan_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "write_plan_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "write_plan_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "write_plan_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    (root / "write_plan_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\n"
        "max displacement = 2.5 mm\n"
        "DISPLACEMENTS\n"
        "node | ux\n"
        "units | - | mm\n"
        "1 | 0.1\n",
        encoding="utf-8",
    )
    (root / "write_plan_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    return root


def _mapping(root: Path):
    return build_calculix_result_dataset_draft_mapping(
        plan_calculix_result_import(root)
    )


def _codes(plan: FEASpecCalculiXResultDatasetWritePlan) -> set[str]:
    return {diagnostic.code.value for diagnostic in plan.diagnostics}


def test_write_plan_module_imports_and_exports_required_api() -> None:
    assert plan_calculix_result_dataset_write
    assert validate_calculix_result_dataset_write_plan
    assert explain_calculix_result_dataset_write_plan
    assert FEASpecCalculiXResultDatasetWritePlan
    assert FEASpecCalculiXResultDatasetWritePlanValidation
    assert FEASpecCalculiXResultDatasetWriteTarget
    assert FEASpecCalculiXResultDatasetPlannedFile
    assert FEASpecCalculiXResultDatasetArtifactReferencePlan
    assert FEASpecCalculiXResultDatasetAtomicWritePlan
    assert FEASpecCalculiXResultDatasetWriteStatus


def test_all_write_diagnostic_codes_are_available() -> None:
    required = {
        "FDW_WRITE_NOT_IMPLEMENTED",
        "FDW_OUTPUT_PATH_REQUIRED",
        "FDW_OUTPUT_DIRECTORY_REQUIRED",
        "FDW_PARENT_MISSING",
        "FDW_CREATE_DIR_REQUIRED",
        "FDW_OUTPUT_EXISTS",
        "FDW_OUTPUT_NOT_EMPTY",
        "FDW_UNSAFE_PATH",
        "FDW_PATH_TRAVERSAL_REJECTED",
        "FDW_DRAFT_BLOCKED",
        "FDW_SCHEMA_VERSION_MISSING",
        "FDW_PROVENANCE_INCOMPLETE",
        "FDW_ARTIFACT_REFERENCE_MISSING",
        "FDW_ARTIFACT_HASH_MISMATCH",
        "FDW_DIAGNOSTICS_UNREVIEWED",
        "FDW_LIMITATIONS_NOT_ACKNOWLEDGED",
        "FDW_ATOMIC_WRITE_PLANNED_ONLY",
        "FDW_ATOMIC_WRITE_NOT_IMPLEMENTED",
        "FDW_ARTIFACT_COPY_NOT_IMPLEMENTED",
        "FDW_RESULTDATASET_PERSISTENCE_FORBIDDEN",
        "FDW_WRITE_COMPLETED",
        "FDW_WRITE_FAILED",
        "FDW_TEMP_WRITE_FAILED",
        "FDW_TARGET_REPLACE_FAILED",
        "FDW_UNPLANNED_FILE_COLLISION",
        "FDW_WRITTEN_FILE_HASH_FAILED",
        "FDW_ARTIFACT_COPY_FORBIDDEN",
    }

    assert required <= {item.value for item in CalculiXResultDatasetWriteDiagnosticCode}


def test_ready_mapping_produces_in_memory_plan_with_standard_files(
    tmp_path: Path,
) -> None:
    mapping = _mapping(_write_result_dir(tmp_path / "result"))
    output_dir = tmp_path / "dataset"

    plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=output_dir,
        acknowledge_limitations=True,
    )
    validation = validate_calculix_result_dataset_write_plan(plan)

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.PLANNED_WITH_WARNINGS
    assert validation.has_blockers is False
    assert plan.target.output_dir == str(output_dir)
    assert [item.relative_path for item in plan.planned_files] == [
        "result_dataset.json",
        "result_dataset_manifest.json",
        "diagnostics.json",
        "provenance.json",
        "README_REVIEW_FIRST.txt",
    ]
    assert plan.atomic_write_plan.planned_only is True
    assert plan.writes_files is False
    assert plan.result_dataset_persistence is False
    assert plan.solver_execution_performed is False
    assert output_dir.exists() is False


def test_limitations_must_be_acknowledged_before_plan_is_non_blocked(
    tmp_path: Path,
) -> None:
    mapping = _mapping(_write_result_dir(tmp_path / "result"))

    plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=tmp_path / "dataset",
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert "FDW_LIMITATIONS_NOT_ACKNOWLEDGED" in _codes(plan)


def test_blocked_draft_mapping_blocks_write_planning(tmp_path: Path) -> None:
    mapping = SimpleNamespace(
        status="blocked",
        artifacts=(),
        provenance={"case_id": "blocked"},
        diagnostics=(),
        limitations=(),
        schema_version="0.1",
    )

    plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=tmp_path / "dataset",
        acknowledge_limitations=True,
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert "FDW_DRAFT_BLOCKED" in _codes(plan)


def test_schema_version_and_provenance_are_required(tmp_path: Path) -> None:
    mapping = SimpleNamespace(
        status="draft-ready",
        artifacts=(),
        provenance={},
        diagnostics=(),
        limitations=(),
        schema_version="",
    )

    plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=tmp_path / "dataset",
        acknowledge_limitations=True,
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert "FDW_SCHEMA_VERSION_MISSING" in _codes(plan)
    assert "FDW_PROVENANCE_INCOMPLETE" in _codes(plan)


def test_artifact_references_include_path_hash_size_and_copy_is_future_only(
    tmp_path: Path,
) -> None:
    mapping = _mapping(_write_result_dir(tmp_path / "result"))

    plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=tmp_path / "dataset",
        acknowledge_limitations=True,
        copy_artifacts=True,
    )

    assert plan.artifact_references
    assert all(item.source_path for item in plan.artifact_references)
    assert all(item.sha256 for item in plan.artifact_references)
    assert all(item.size_bytes > 0 for item in plan.artifact_references)
    assert all(item.copy_requested for item in plan.artifact_references)
    assert all(item.copy_planned is False for item in plan.artifact_references)
    assert "FDW_ARTIFACT_COPY_NOT_IMPLEMENTED" in _codes(plan)


def test_artifact_hash_or_size_mismatch_blocks_plan(tmp_path: Path) -> None:
    result_dir = _write_result_dir(tmp_path / "result")
    mapping = _mapping(result_dir)
    artifact = result_dir / "write_plan_case.dat"
    artifact.write_text("changed after mapping\n", encoding="utf-8")

    plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=tmp_path / "dataset",
        acknowledge_limitations=True,
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert "FDW_ARTIFACT_HASH_MISMATCH" in _codes(plan)


def test_missing_artifact_reference_blocks_plan(tmp_path: Path) -> None:
    mapping = SimpleNamespace(
        status="draft-ready",
        artifacts=(
            SimpleNamespace(
                source_path="",
                filename="",
                role="dat",
                suffix=".dat",
                sha256="",
                size_bytes=0,
            ),
        ),
        provenance={"case_id": "missing-artifact"},
        diagnostics=(),
        limitations=(),
        schema_version="0.1",
    )

    plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=tmp_path / "dataset",
        acknowledge_limitations=True,
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert "FDW_ARTIFACT_REFERENCE_MISSING" in _codes(plan)


def test_explain_write_plan_is_reviewer_readable(tmp_path: Path) -> None:
    plan = plan_calculix_result_dataset_write(
        _mapping(_write_result_dir(tmp_path / "result")),
        output_dir=tmp_path / "dataset",
        acknowledge_limitations=True,
    )

    lines = explain_calculix_result_dataset_write_plan(plan)

    assert any("write plan status" in line.lower() for line in lines)
    assert any("resultdataset files written: false" in line.lower() for line in lines)
    assert any("solver execution performed: false" in line.lower() for line in lines)
