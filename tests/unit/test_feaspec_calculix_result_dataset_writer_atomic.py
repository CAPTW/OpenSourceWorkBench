from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.experimental.feaspec import (
    FEASpecCalculiXResultDatasetWriteResultStatus,
    build_calculix_result_dataset_draft_mapping,
    build_calculix_result_dataset_schema_payload,
    plan_calculix_result_dataset_write,
    plan_calculix_result_import,
    write_calculix_result_dataset,
)
from osw.experimental.feaspec import calculix_result_dataset_writer as writer_module


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
            "source_feaspec_id": "atomic_writer_feaspec",
            "case_id": "atomic_writer_case",
            "osw_version": "0.1.4rc1",
        },
    )
    _write_json(
        root / "atomic_writer_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "atomic_writer_feaspec",
            "case_id": "atomic_writer_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "atomic_writer_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "atomic_writer_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "atomic_writer_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\nmax displacement = 2.5 mm\n",
        encoding="utf-8",
    )
    return root


def _writer_inputs(tmp_path: Path, *, output_dir: Path | None = None, create_dir=False):
    mapping = build_calculix_result_dataset_draft_mapping(
        plan_calculix_result_import(_write_result_dir(tmp_path / "result"))
    )
    write_plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=output_dir or (tmp_path / "dataset"),
        create_dir=create_dir,
        acknowledge_limitations=True,
    )
    payload = build_calculix_result_dataset_schema_payload(mapping, write_plan)
    return write_plan, payload


def _codes(result) -> set[str]:
    return {diagnostic.code.value for diagnostic in result.diagnostics}


def test_writer_removes_temp_files_after_success(tmp_path: Path) -> None:
    write_plan, payload = _writer_inputs(tmp_path)

    result = write_calculix_result_dataset(write_plan, payload)

    assert result.status in {
        FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN,
        FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN_WITH_WARNINGS,
    }
    assert not list((tmp_path / "dataset").glob(".osw-*.tmp"))


def test_writer_temp_write_failure_reports_diagnostic_and_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_plan, payload = _writer_inputs(tmp_path)

    def fail_temp_write(path: Path, text: str) -> None:
        path.write_text("partial", encoding="utf-8")
        raise OSError("simulated temp write failure")

    monkeypatch.setattr(writer_module, "_write_text_to_temp", fail_temp_write)

    result = write_calculix_result_dataset(write_plan, payload)

    assert result.status is FEASpecCalculiXResultDatasetWriteResultStatus.FAILED
    assert "FDW_TEMP_WRITE_FAILED" in _codes(result)
    assert not list((tmp_path / "dataset").glob(".osw-*.tmp"))
    assert not any(
        (tmp_path / "dataset" / filename).exists()
        for filename in (
            "result_dataset.json",
            "result_dataset_manifest.json",
            "diagnostics.json",
            "provenance.json",
            "README_REVIEW_FIRST.txt",
        )
    )


def test_writer_replace_failure_reports_diagnostic_and_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_plan, payload = _writer_inputs(tmp_path)

    def fail_replace(temp_path: Path, target_path: Path) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(writer_module, "_replace_temp_file", fail_replace)

    result = write_calculix_result_dataset(write_plan, payload)

    assert result.status is FEASpecCalculiXResultDatasetWriteResultStatus.FAILED
    assert "FDW_TARGET_REPLACE_FAILED" in _codes(result)
    assert not list((tmp_path / "dataset").glob(".osw-*.tmp"))


def test_writer_partial_cleanup_failure_is_classified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_plan, payload = _writer_inputs(tmp_path)

    def fail_temp_write(path: Path, text: str) -> None:
        path.write_text("partial", encoding="utf-8")
        raise OSError("simulated temp write failure")

    monkeypatch.setattr(writer_module, "_write_text_to_temp", fail_temp_write)
    monkeypatch.setattr(writer_module, "_cleanup_temp_paths", lambda paths: False)

    result = write_calculix_result_dataset(write_plan, payload)

    assert result.status is (
        FEASpecCalculiXResultDatasetWriteResultStatus.PARTIAL_CLEANUP_FAILED
    )
    assert "FDW_TEMP_WRITE_FAILED" in _codes(result)
    assert "FDW_WRITE_FAILED" in _codes(result)


def test_writer_refuses_unplanned_file_collision_even_with_overwrite(
    tmp_path: Path,
) -> None:
    write_plan, payload = _writer_inputs(tmp_path)
    target = tmp_path / "dataset"
    target.mkdir()
    (target / "unplanned.txt").write_text("do not touch\n", encoding="utf-8")

    result = write_calculix_result_dataset(write_plan, payload, overwrite=True)

    assert result.status is FEASpecCalculiXResultDatasetWriteResultStatus.BLOCKED
    assert "FDW_UNPLANNED_FILE_COLLISION" in _codes(result)
    assert (target / "unplanned.txt").read_text(encoding="utf-8") == "do not touch\n"


def test_writer_does_not_create_missing_parent_without_plan_permission(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "missing" / "dataset"
    write_plan, payload = _writer_inputs(tmp_path, output_dir=output_dir)

    result = write_calculix_result_dataset(write_plan, payload)

    assert result.status is FEASpecCalculiXResultDatasetWriteResultStatus.BLOCKED
    assert "FDW_DRAFT_BLOCKED" in _codes(result)
    assert output_dir.exists() is False


def test_writer_creates_missing_parent_only_when_plan_allowed(tmp_path: Path) -> None:
    output_dir = tmp_path / "missing" / "dataset"
    write_plan, payload = _writer_inputs(
        tmp_path,
        output_dir=output_dir,
        create_dir=True,
    )

    result = write_calculix_result_dataset(write_plan, payload)

    assert result.status in {
        FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN,
        FEASpecCalculiXResultDatasetWriteResultStatus.WRITTEN_WITH_WARNINGS,
    }
    assert output_dir.is_dir()
    assert (output_dir / "result_dataset.json").is_file()
