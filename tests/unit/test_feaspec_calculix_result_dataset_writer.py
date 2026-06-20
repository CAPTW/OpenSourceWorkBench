from __future__ import annotations

import hashlib
import json
from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXResultDatasetWriteDiagnosticCode,
    FEASpecCalculiXResultDatasetPreparedWritePayloads,
    FEASpecCalculiXResultDatasetWriteResult,
    FEASpecCalculiXResultDatasetWriteResultStatus,
    FEASpecCalculiXResultDatasetWrittenFile,
    build_calculix_result_dataset_draft_mapping,
    build_calculix_result_dataset_schema_payload,
    explain_calculix_result_dataset_write_result,
    plan_calculix_result_dataset_write,
    plan_calculix_result_import,
    prepare_calculix_result_dataset_write_payloads,
    write_calculix_result_dataset,
)

STANDARD_FILES = [
    "README_REVIEW_FIRST.txt",
    "diagnostics.json",
    "provenance.json",
    "result_dataset.json",
    "result_dataset_manifest.json",
]


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_result_dir(root: Path) -> Path:
    root.mkdir(parents=True)
    _write_json(
        root / "run_metadata.json",
        {
            "status": "ran",
            "solver_execution_performed": True,
            "exit_code": 0,
            "timed_out": False,
            "source_feaspec_id": "writer_feaspec",
            "case_id": "writer_case",
            "osw_version": "0.1.4rc1",
            "scalar_summaries": {"metadata_only": "preserved"},
        },
    )
    _write_json(
        root / "writer_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "writer_feaspec",
            "case_id": "writer_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "writer_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "writer_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "writer_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "writer_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    (root / "writer_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\n"
        "max displacement = 2.5 mm\n"
        "DISPLACEMENTS\n"
        "node | ux\n"
        "units | - | mm\n"
        "1 | 0.1\n",
        encoding="utf-8",
    )
    (root / "writer_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    return root


def _writer_inputs(
    tmp_path: Path,
    *,
    output_dir: Path | None = None,
    overwrite: bool = False,
    create_dir: bool = False,
    acknowledge_limitations: bool = True,
    copy_artifacts: bool = False,
):
    mapping = build_calculix_result_dataset_draft_mapping(
        plan_calculix_result_import(_write_result_dir(tmp_path / "result"))
    )
    write_plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=output_dir or (tmp_path / "dataset"),
        overwrite=overwrite,
        create_dir=create_dir,
        acknowledge_limitations=acknowledge_limitations,
        copy_artifacts=copy_artifacts,
    )
    payload = build_calculix_result_dataset_schema_payload(mapping, write_plan)
    return write_plan, payload


def _codes(result: FEASpecCalculiXResultDatasetWriteResult) -> set[str]:
    return {diagnostic.code.value for diagnostic in result.diagnostics}


def test_writer_module_imports_and_exports_required_public_api() -> None:
    assert callable(write_calculix_result_dataset)
    assert callable(prepare_calculix_result_dataset_write_payloads)
    assert callable(explain_calculix_result_dataset_write_result)
    assert FEASpecCalculiXResultDatasetWriteResult
    assert FEASpecCalculiXResultDatasetWrittenFile
    assert FEASpecCalculiXResultDatasetPreparedWritePayloads
    assert FEASpecCalculiXResultDatasetWriteResultStatus


def test_write_diagnostic_codes_include_writer_additions() -> None:
    required = {
        "FDW_WRITE_COMPLETED",
        "FDW_WRITE_FAILED",
        "FDW_TEMP_WRITE_FAILED",
        "FDW_TARGET_REPLACE_FAILED",
        "FDW_UNPLANNED_FILE_COLLISION",
        "FDW_WRITTEN_FILE_HASH_FAILED",
        "FDW_ARTIFACT_COPY_FORBIDDEN",
    }

    assert required <= {item.value for item in CalculiXResultDatasetWriteDiagnosticCode}


def test_prepare_payloads_is_deterministic_and_writes_no_files(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path)

    prepared = prepare_calculix_result_dataset_write_payloads(write_plan, payload)
    second = prepare_calculix_result_dataset_write_payloads(write_plan, payload)

    assert prepared.has_blockers is False
    assert prepared.writes_files is False
    assert prepared.payloads == second.payloads
    assert [item["relative_path"] for item in prepared.payloads] == [
        "result_dataset.json",
        "result_dataset_manifest.json",
        "diagnostics.json",
        "provenance.json",
        "README_REVIEW_FIRST.txt",
    ]
    assert (tmp_path / "dataset").exists() is False


def test_valid_plan_and_schema_write_exact_standard_files(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path)

    result = write_calculix_result_dataset(write_plan, payload)

    assert result.status in {
        FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN,
        FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN_WITH_WARNINGS,
    }
    assert sorted(path.name for path in (tmp_path / "dataset").iterdir()) == STANDARD_FILES
    assert len(result.written_files) == 5
    assert "FDW_WRITE_COMPLETED" in _codes(result)
    assert result.solver_execution_performed is False
    assert result.artifact_copy_performed is False
    assert result.cli_write_command_added is False
    assert result.gui_write_command_added is False
    assert not (tmp_path / "dataset" / "artifacts").exists()


def test_written_files_are_valid_json_or_review_readme(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path)

    write_calculix_result_dataset(write_plan, payload)

    dataset = json.loads((tmp_path / "dataset" / "result_dataset.json").read_text())
    manifest = json.loads(
        (tmp_path / "dataset" / "result_dataset_manifest.json").read_text()
    )
    diagnostics = json.loads((tmp_path / "dataset" / "diagnostics.json").read_text())
    provenance = json.loads((tmp_path / "dataset" / "provenance.json").read_text())
    readme = (tmp_path / "dataset" / "README_REVIEW_FIRST.txt").read_text(
        encoding="utf-8"
    )

    assert dataset["dataset_id"] == "writer_case"
    assert manifest["dataset_id"] == "writer_case"
    assert diagnostics["diagnostic_count"] >= 1
    assert provenance["provenance"]["case_id"] == "writer_case"
    assert "README_REVIEW_FIRST" in readme
    assert "Human review" in readme


def test_written_file_metadata_records_size_and_sha256(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path)

    result = write_calculix_result_dataset(write_plan, payload)

    for written_file in result.written_files:
        path = Path(written_file.path)
        data = path.read_bytes()
        assert written_file.size_bytes == len(data)
        assert written_file.sha256 == hashlib.sha256(data).hexdigest()
        assert written_file.payload_kind


def test_json_serialization_is_deterministic_across_writes(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path)

    write_calculix_result_dataset(write_plan, payload)
    first_render = {
        filename: (tmp_path / "dataset" / filename).read_text(encoding="utf-8")
        for filename in STANDARD_FILES
        if not filename.endswith(".txt")
    }
    write_calculix_result_dataset(write_plan, payload, overwrite=True)

    for filename, text in first_render.items():
        assert (tmp_path / "dataset" / filename).read_text(encoding="utf-8") == text


def test_json_serialization_changes_only_when_source_payload_changes(
    tmp_path: Path,
) -> None:
    first_plan, first_payload = _writer_inputs(
        tmp_path,
        output_dir=tmp_path / "dataset_a",
    )
    second_plan, second_payload = _writer_inputs(
        tmp_path / "variant",
        output_dir=tmp_path / "dataset_b",
    )

    write_calculix_result_dataset(first_plan, first_payload)
    write_calculix_result_dataset(second_plan, second_payload)

    assert (
        tmp_path / "dataset_a" / "result_dataset.json"
    ).read_text(encoding="utf-8") != (
        tmp_path / "dataset_b" / "result_dataset.json"
    ).read_text(encoding="utf-8")


def test_writer_refuses_blocked_write_plan_and_writes_no_files(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path, acknowledge_limitations=False)

    result = write_calculix_result_dataset(write_plan, payload)

    assert result.status is FEASpecCalculiXResultDatasetWriteResultStatus.BLOCKED
    assert "FDW_DRAFT_BLOCKED" in _codes(result)
    assert (tmp_path / "dataset").exists() is False


def test_writer_refuses_blocked_schema_payload_and_writes_no_files(
    tmp_path: Path,
) -> None:
    write_plan, payload = _writer_inputs(tmp_path)
    blocked_payload = build_calculix_result_dataset_schema_payload(
        build_calculix_result_dataset_draft_mapping(
            plan_calculix_result_import(_write_result_dir(tmp_path / "other_result"))
        ),
        write_plan,
        schema_version="",
    )

    result = write_calculix_result_dataset(write_plan, blocked_payload)

    assert result.status is FEASpecCalculiXResultDatasetWriteResultStatus.BLOCKED
    assert "FDW_WRITE_FAILED" in _codes(result)
    assert (tmp_path / "dataset").exists() is False


def test_writer_refuses_existing_standard_files_without_overwrite(
    tmp_path: Path,
) -> None:
    write_plan, payload = _writer_inputs(tmp_path)
    write_calculix_result_dataset(write_plan, payload)
    original = (tmp_path / "dataset" / "README_REVIEW_FIRST.txt").read_text(
        encoding="utf-8"
    )

    blocked = write_calculix_result_dataset(write_plan, payload)

    assert blocked.status is FEASpecCalculiXResultDatasetWriteResultStatus.BLOCKED
    assert "FDW_OUTPUT_EXISTS" in _codes(blocked)
    assert (
        tmp_path / "dataset" / "README_REVIEW_FIRST.txt"
    ).read_text(encoding="utf-8") == original


def test_writer_overwrites_standard_files_only_when_explicit(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path)
    write_calculix_result_dataset(write_plan, payload)
    (tmp_path / "dataset" / "README_REVIEW_FIRST.txt").write_text(
        "stale\n",
        encoding="utf-8",
    )

    result = write_calculix_result_dataset(write_plan, payload, overwrite=True)

    assert result.status in {
        FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN,
        FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN_WITH_WARNINGS,
    }
    assert "stale" not in (
        tmp_path / "dataset" / "README_REVIEW_FIRST.txt"
    ).read_text(encoding="utf-8")
    assert sorted(path.name for path in (tmp_path / "dataset").iterdir()) == STANDARD_FILES


def test_writer_refuses_artifact_copy_requests(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path, copy_artifacts=True)

    result = write_calculix_result_dataset(write_plan, payload)

    assert result.status is FEASpecCalculiXResultDatasetWriteResultStatus.BLOCKED
    assert "FDW_ARTIFACT_COPY_FORBIDDEN" in _codes(result)
    assert not (tmp_path / "dataset" / "artifacts").exists()


def test_explain_writer_result_is_reviewer_readable(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path)
    result = write_calculix_result_dataset(write_plan, payload)

    lines = explain_calculix_result_dataset_write_result(result)

    assert any("ResultDataset writer status:" in line for line in lines)
    assert any("Files written: 5." in line for line in lines)
    assert any("Solver execution performed: false." in line for line in lines)
    assert any("CLI write command added: false." in line for line in lines)
