from __future__ import annotations

from enum import Enum
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

from osw.experimental.feaspec import (
    FEASpecCalculiXResultDatasetSchemaStatus,
    FEASpecCalculiXResultDatasetWriteStatus,
    build_calculix_result_dataset_schema_payload,
    plan_calculix_result_dataset_write,
    validate_calculix_result_dataset_schema_payload,
)


def _mapping(tmp_path: Path) -> dict[str, object]:
    artifact = tmp_path / "result.dat"
    artifact.write_text("TOTAL ENERGY SUMMARY\nmax displacement = 2.5 mm\n")
    digest = sha256(artifact.read_bytes()).hexdigest()
    return {
        "dataset_id": "schema_validation_case",
        "source": str(tmp_path),
        "solver": "CalculiX",
        "analysis_type": "linear_static",
        "status": "draft-ready",
        "artifacts": [
            {
                "source_path": str(artifact),
                "filename": artifact.name,
                "suffix": ".dat",
                "artifact_kind": "dat",
                "role": "primary-result",
                "sha256": digest,
                "size_bytes": artifact.stat().st_size,
            }
        ],
        "status_summaries": [],
        "scalar_candidates": [],
        "table_candidates": [],
        "field_references": [],
        "provenance": {
            "result_dir": str(tmp_path),
            "case_id": "schema_validation_case",
            "source_feaspec_id": "schema_validation_feaspec",
            "osw_version": "0.1.4rc1",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
        },
        "diagnostics": [
            {
                "code": "FV_SYNTHETIC_DIAGNOSTIC",
                "severity": "info",
                "message": "Synthetic carried diagnostic.",
            }
        ],
        "limitations": [
            {
                "message": "Synthetic review limitation.",
                "source": "test",
                "blocks_mapping": False,
            }
        ],
        "writes_files": False,
        "result_dataset_persistence": False,
        "solver_execution_performed": False,
        "frd_numerical_field_parser": False,
        "mesh_reconstructed": False,
        "units_inferred": False,
        "engineering_correctness_claimed": False,
    }


def _write_plan(mapping: dict[str, object], tmp_path: Path):
    return plan_calculix_result_dataset_write(
        mapping,
        output_dir=tmp_path / "dataset",
        acknowledge_limitations=True,
    )


def _codes(payload) -> set[str]:
    return {diagnostic.code.value for diagnostic in payload.schema_diagnostics}


def test_schema_validation_blocks_missing_write_plan(tmp_path: Path) -> None:
    payload = build_calculix_result_dataset_schema_payload(
        _mapping(tmp_path),
        None,
    )
    validation = validate_calculix_result_dataset_schema_payload(payload)

    assert payload.status is FEASpecCalculiXResultDatasetSchemaStatus.BLOCKED
    assert validation.has_blockers is True
    assert "FDS_WRITE_PLAN_MISSING" in _codes(payload)
    assert "FDS_MANIFEST_INVALID" in _codes(payload)


def test_schema_validation_blocks_write_plan_with_blockers(tmp_path: Path) -> None:
    mapping = _mapping(tmp_path)
    write_plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=tmp_path / "dataset",
    )

    payload = build_calculix_result_dataset_schema_payload(mapping, write_plan)

    assert payload.status is FEASpecCalculiXResultDatasetSchemaStatus.BLOCKED
    assert "FDS_WRITE_PLAN_BLOCKED" in _codes(payload)


def test_schema_validation_blocks_missing_schema_version(tmp_path: Path) -> None:
    mapping = _mapping(tmp_path)
    write_plan = _write_plan(mapping, tmp_path)

    payload = build_calculix_result_dataset_schema_payload(
        mapping,
        write_plan,
        schema_version="",
    )
    validation = validate_calculix_result_dataset_schema_payload(payload)

    assert validation.has_blockers is True
    assert "FDS_SCHEMA_VERSION_MISSING" in _codes(payload)


def test_schema_validation_blocks_missing_provenance(tmp_path: Path) -> None:
    mapping = _mapping(tmp_path)
    mapping["provenance"] = {}
    write_plan = _write_plan(mapping, tmp_path)

    payload = build_calculix_result_dataset_schema_payload(mapping, write_plan)

    assert payload.status is FEASpecCalculiXResultDatasetSchemaStatus.BLOCKED
    assert "FDS_PROVENANCE_MISSING" in _codes(payload)
    assert "FDS_WRITE_PLAN_BLOCKED" in _codes(payload)


def test_schema_validation_blocks_missing_artifacts(tmp_path: Path) -> None:
    mapping = _mapping(tmp_path)
    mapping["artifacts"] = []
    write_plan = _write_plan(mapping, tmp_path)

    payload = build_calculix_result_dataset_schema_payload(mapping, write_plan)

    assert payload.status is FEASpecCalculiXResultDatasetSchemaStatus.BLOCKED
    assert "FDS_ARTIFACTS_MISSING" in _codes(payload)


def test_schema_validation_warns_for_missing_diagnostics_or_limitations(
    tmp_path: Path,
) -> None:
    mapping = _mapping(tmp_path)
    mapping["diagnostics"] = []
    mapping["limitations"] = []
    write_plan = _write_plan(mapping, tmp_path)

    payload = build_calculix_result_dataset_schema_payload(mapping, write_plan)
    validation = validate_calculix_result_dataset_schema_payload(payload)

    assert validation.has_blockers is False
    assert payload.status is (
        FEASpecCalculiXResultDatasetSchemaStatus.PAYLOAD_READY_WITH_WARNINGS
    )
    assert "FDS_DIAGNOSTICS_MISSING" in _codes(payload)
    assert "FDS_LIMITATIONS_MISSING" in _codes(payload)


def test_schema_validation_requires_review_readme_in_manifest(
    tmp_path: Path,
) -> None:
    mapping = _mapping(tmp_path)

    class _Status(str, Enum):
        PLANNED = "planned"

    write_plan = SimpleNamespace(
        status=FEASpecCalculiXResultDatasetWriteStatus.PLANNED,
        diagnostics=(),
        writes_files=False,
        result_dataset_persistence=False,
        to_dict=lambda: {
            "status": _Status.PLANNED.value,
            "planned_files": [
                {
                    "role": "result_dataset",
                    "relative_path": "result_dataset.json",
                    "target_path": "",
                    "temp_path": "",
                    "writes_file": False,
                }
            ],
            "artifact_references": [],
            "diagnostics": [],
            "schema_name": "osw.feaspec.calculix.resultdataset",
            "schema_version": "0.1",
            "producer_version": "0.1.4rc1",
            "source_release": "v0.1.4-rc1",
        },
    )

    payload = build_calculix_result_dataset_schema_payload(mapping, write_plan)

    assert payload.status is FEASpecCalculiXResultDatasetSchemaStatus.BLOCKED
    assert "FDS_README_REQUIRED" in _codes(payload)
