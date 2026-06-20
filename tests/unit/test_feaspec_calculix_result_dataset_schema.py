from __future__ import annotations

import json
from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXResultDatasetSchemaDiagnosticCode,
    FEASpecCalculiXResultDatasetDiagnosticsPayload,
    FEASpecCalculiXResultDatasetManifestPayload,
    FEASpecCalculiXResultDatasetProvenancePayload,
    FEASpecCalculiXResultDatasetReviewReadmePayload,
    FEASpecCalculiXResultDatasetSchemaPayload,
    FEASpecCalculiXResultDatasetSchemaStatus,
    FEASpecCalculiXResultDatasetSchemaValidation,
    FEASpecCalculiXResultDatasetSchemaVersion,
    build_calculix_result_dataset_diagnostics_payload,
    build_calculix_result_dataset_draft_mapping,
    build_calculix_result_dataset_manifest_payload,
    build_calculix_result_dataset_provenance_payload,
    build_calculix_result_dataset_review_readme,
    build_calculix_result_dataset_schema_payload,
    explain_calculix_result_dataset_schema_payload,
    plan_calculix_result_dataset_write,
    plan_calculix_result_import,
    validate_calculix_result_dataset_schema_payload,
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
            "source_feaspec_id": "schema_feaspec",
            "case_id": "schema_case",
            "osw_version": "0.1.4rc1",
            "scalar_summaries": {"metadata_only": "preserved"},
        },
    )
    _write_json(
        root / "schema_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "schema_feaspec",
            "case_id": "schema_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "schema_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "schema_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "schema_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "schema_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    (root / "schema_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\n"
        "max displacement = 2.5 mm\n"
        "DISPLACEMENTS\n"
        "node | ux\n"
        "units | - | mm\n"
        "1 | 0.1\n",
        encoding="utf-8",
    )
    (root / "schema_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    return root


def _schema_payload(tmp_path: Path) -> FEASpecCalculiXResultDatasetSchemaPayload:
    mapping = build_calculix_result_dataset_draft_mapping(
        plan_calculix_result_import(_write_result_dir(tmp_path / "result"))
    )
    write_plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=tmp_path / "dataset",
        acknowledge_limitations=True,
    )
    return build_calculix_result_dataset_schema_payload(mapping, write_plan)


def _codes(payload: FEASpecCalculiXResultDatasetSchemaPayload) -> set[str]:
    return {diagnostic.code.value for diagnostic in payload.schema_diagnostics}


def test_schema_model_module_imports_and_exports_required_api() -> None:
    assert build_calculix_result_dataset_schema_payload
    assert validate_calculix_result_dataset_schema_payload
    assert explain_calculix_result_dataset_schema_payload
    assert build_calculix_result_dataset_manifest_payload
    assert build_calculix_result_dataset_diagnostics_payload
    assert build_calculix_result_dataset_provenance_payload
    assert build_calculix_result_dataset_review_readme
    assert FEASpecCalculiXResultDatasetSchemaPayload
    assert FEASpecCalculiXResultDatasetSchemaValidation
    assert FEASpecCalculiXResultDatasetSchemaVersion
    assert FEASpecCalculiXResultDatasetManifestPayload
    assert FEASpecCalculiXResultDatasetDiagnosticsPayload
    assert FEASpecCalculiXResultDatasetProvenancePayload
    assert FEASpecCalculiXResultDatasetReviewReadmePayload
    assert FEASpecCalculiXResultDatasetSchemaStatus


def test_all_schema_diagnostic_codes_are_available() -> None:
    required = {
        "FDS_SCHEMA_MODEL_ONLY",
        "FDS_SCHEMA_NAME_MISSING",
        "FDS_SCHEMA_VERSION_MISSING",
        "FDS_PRODUCER_VERSION_MISSING",
        "FDS_SOURCE_VERSION_MISSING",
        "FDS_DRAFT_MAPPING_MISSING",
        "FDS_WRITE_PLAN_MISSING",
        "FDS_WRITE_PLAN_BLOCKED",
        "FDS_ARTIFACTS_MISSING",
        "FDS_PROVENANCE_MISSING",
        "FDS_DIAGNOSTICS_MISSING",
        "FDS_LIMITATIONS_MISSING",
        "FDS_PAYLOAD_INVALID",
        "FDS_MANIFEST_INVALID",
        "FDS_README_REQUIRED",
        "FDS_FILE_WRITE_FORBIDDEN",
        "FDS_PERSISTENCE_NOT_IMPLEMENTED",
    }

    assert required <= {item.value for item in CalculiXResultDatasetSchemaDiagnosticCode}


def test_ready_mapping_and_write_plan_build_schema_payload(tmp_path: Path) -> None:
    payload = _schema_payload(tmp_path)
    validation = validate_calculix_result_dataset_schema_payload(payload)

    assert payload.status is FEASpecCalculiXResultDatasetSchemaStatus.PAYLOAD_READY
    assert validation.has_blockers is False
    assert payload.schema.schema_name == "osw.feaspec.calculix.resultdataset"
    assert payload.schema.schema_version == "0.1"
    assert payload.schema.producer_version == "0.1.5rc1"
    assert payload.schema.source_version == "0.1.4rc1"
    assert payload.schema.source_release == "v0.1.4-rc1"
    assert payload.dataset["dataset_id"] == "schema_case"
    assert payload.dataset["artifacts"]
    assert payload.dataset["scalar_candidates"]
    assert payload.dataset["table_candidates"]
    assert payload.dataset["field_references"]
    assert payload.writes_files is False
    assert payload.result_dataset_persistence is False
    assert payload.field_values_parsed is False
    assert payload.mesh_reconstructed is False
    assert payload.unit_inference_performed is False
    assert payload.engineering_correctness_claimed is False
    assert "FDS_SCHEMA_MODEL_ONLY" in _codes(payload)
    assert "FDS_FILE_WRITE_FORBIDDEN" in _codes(payload)
    assert "FDS_PERSISTENCE_NOT_IMPLEMENTED" in _codes(payload)


def test_schema_payload_exposes_companion_payloads(tmp_path: Path) -> None:
    payload = _schema_payload(tmp_path)

    manifest = build_calculix_result_dataset_manifest_payload(payload)
    diagnostics = build_calculix_result_dataset_diagnostics_payload(payload)
    provenance = build_calculix_result_dataset_provenance_payload(payload)
    readme = build_calculix_result_dataset_review_readme(payload)

    assert manifest.planned_files
    assert any(
        item["relative_path"] == "result_dataset.json"
        for item in manifest.planned_files
    )
    assert any(
        item["relative_path"] == "README_REVIEW_FIRST.txt"
        for item in manifest.planned_files
    )
    assert manifest.artifact_references
    assert diagnostics.diagnostic_count >= 1
    assert diagnostics.schema_diagnostics
    assert diagnostics.source_diagnostics
    assert diagnostics.write_plan_diagnostics
    assert provenance.provenance["case_id"] == "schema_case"
    assert provenance.artifact_sources
    assert "README_REVIEW_FIRST" in readme.content
    assert "No file writes occur" in readme.content
    assert "No solver execution is performed" in readme.content
    assert "Issue #8 live CalculiX validation remains open" in readme.content
    assert readme.writes_files is False


def test_schema_payload_is_deterministic_json_serializable(tmp_path: Path) -> None:
    payload = _schema_payload(tmp_path)

    first = payload.to_dict()
    second = payload.to_dict()
    first_json = json.dumps(first, sort_keys=True)
    second_json = json.dumps(second, sort_keys=True)

    assert first == second
    assert first_json == second_json
    assert first["writes_files"] is False
    assert first["result_dataset_persistence"] is False


def test_schema_payload_writes_no_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "dataset"

    payload = _schema_payload(tmp_path)

    assert output_dir.exists() is False
    assert payload.writes_files is False
    assert payload.manifest_payload.writes_files is False
    assert payload.diagnostics_payload.writes_files is False
    assert payload.provenance_payload.writes_files is False
    assert payload.readme_payload.writes_files is False


def test_explain_schema_payload_is_reviewer_readable(tmp_path: Path) -> None:
    lines = explain_calculix_result_dataset_schema_payload(
        _schema_payload(tmp_path)
    )

    assert any("schema payload status" in line.lower() for line in lines)
    assert any("resultdataset files written: false" in line.lower() for line in lines)
    assert any("solver execution performed" in line.lower() for line in lines)
