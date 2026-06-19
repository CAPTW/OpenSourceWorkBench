from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from osw.experimental.feaspec import (
    FEASpecCalculiXResultDatasetWriteStatus,
    plan_calculix_result_dataset_write,
)


def _mapping() -> SimpleNamespace:
    return SimpleNamespace(
        status="draft-ready",
        artifacts=(),
        provenance={"case_id": "path-policy"},
        diagnostics=(),
        limitations=(),
        schema_version="0.1",
    )


def _codes(plan) -> set[str]:
    return {diagnostic.code.value for diagnostic in plan.diagnostics}


def test_missing_output_path_blocks_write_plan() -> None:
    plan = plan_calculix_result_dataset_write(_mapping())

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert plan.target.mode == "missing"
    assert "FDW_OUTPUT_PATH_REQUIRED" in _codes(plan)


def test_single_file_output_path_is_unsupported(tmp_path: Path) -> None:
    plan = plan_calculix_result_dataset_write(
        _mapping(),
        output_path=tmp_path / "result_dataset.json",
        acknowledge_limitations=True,
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.UNSUPPORTED
    assert plan.target.mode == "single-file-unsupported"
    assert "FDW_OUTPUT_DIRECTORY_REQUIRED" in _codes(plan)
    assert plan.planned_files == ()


def test_parent_directory_missing_blocks_without_create_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "missing-parent" / "dataset"

    plan = plan_calculix_result_dataset_write(
        _mapping(),
        output_dir=output_dir,
        acknowledge_limitations=True,
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert "FDW_PARENT_MISSING" in _codes(plan)
    assert output_dir.exists() is False


def test_create_dir_flag_plans_directory_without_creating_it(tmp_path: Path) -> None:
    output_dir = tmp_path / "missing-parent" / "dataset"

    plan = plan_calculix_result_dataset_write(
        _mapping(),
        output_dir=output_dir,
        create_dir=True,
        acknowledge_limitations=True,
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.PLANNED
    assert plan.target.create_dir_requested is True
    assert plan.target.create_dir_planned is True
    assert "FDW_CREATE_DIR_REQUIRED" in _codes(plan)
    assert output_dir.exists() is False


def test_existing_file_output_blocks_unless_overwrite_is_explicit(
    tmp_path: Path,
) -> None:
    target = tmp_path / "dataset"
    target.write_text("not a directory\n", encoding="utf-8")

    blocked = plan_calculix_result_dataset_write(
        _mapping(),
        output_dir=target,
        acknowledge_limitations=True,
    )
    reviewed = plan_calculix_result_dataset_write(
        _mapping(),
        output_dir=target,
        overwrite=True,
        acknowledge_limitations=True,
    )

    assert blocked.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert "FDW_OUTPUT_EXISTS" in _codes(blocked)
    assert reviewed.status is FEASpecCalculiXResultDatasetWriteStatus.PLANNED_WITH_WARNINGS
    assert reviewed.target.overwrite_requested is True
    assert target.read_text(encoding="utf-8") == "not a directory\n"


def test_existing_nonempty_directory_blocks_unless_overwrite_is_explicit(
    tmp_path: Path,
) -> None:
    target = tmp_path / "dataset"
    target.mkdir()
    (target / "existing.txt").write_text("review first\n", encoding="utf-8")

    blocked = plan_calculix_result_dataset_write(
        _mapping(),
        output_dir=target,
        acknowledge_limitations=True,
    )
    reviewed = plan_calculix_result_dataset_write(
        _mapping(),
        output_dir=target,
        overwrite=True,
        acknowledge_limitations=True,
    )

    assert blocked.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert "FDW_OUTPUT_NOT_EMPTY" in _codes(blocked)
    assert reviewed.status is FEASpecCalculiXResultDatasetWriteStatus.PLANNED_WITH_WARNINGS
    assert "FDW_OUTPUT_NOT_EMPTY" in _codes(reviewed)
    assert (target / "existing.txt").exists()


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    output_dir = tmp_path / ".." / "outside"

    plan = plan_calculix_result_dataset_write(
        _mapping(),
        output_dir=output_dir,
        acknowledge_limitations=True,
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert plan.target.traversal_rejected is True
    assert "FDW_PATH_TRAVERSAL_REJECTED" in _codes(plan)


def test_forbidden_repository_paths_are_rejected(tmp_path: Path) -> None:
    output_dir = tmp_path / ".git" / "result-dataset"

    plan = plan_calculix_result_dataset_write(
        _mapping(),
        output_dir=output_dir,
        acknowledge_limitations=True,
    )

    assert plan.status is FEASpecCalculiXResultDatasetWriteStatus.BLOCKED
    assert plan.target.unsafe_path is True
    assert "FDW_UNSAFE_PATH" in _codes(plan)
