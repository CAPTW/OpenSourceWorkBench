from __future__ import annotations

import json
from pathlib import Path

from osw.experimental.feaspec import (
    FEASpecCalculiXResultWriteAcknowledgementState,
    FEASpecCalculiXResultWriteAction,
    FEASpecCalculiXResultWriteActionState,
    FEASpecCalculiXResultWritePanel,
    FEASpecCalculiXResultWriteSavePlan,
    FEASpecCalculiXResultWriteViewModel,
    FEASpecCalculiXResultWriteViewModelInput,
    build_calculix_result_dataset_draft_mapping,
    build_calculix_result_dataset_schema_payload,
    build_calculix_result_write_viewmodel,
    explain_calculix_result_write_viewmodel,
    plan_calculix_result_dataset_write,
    plan_calculix_result_import,
    preview_calculix_result_write_record,
)


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
            "source_feaspec_id": "write_viewmodel_feaspec",
            "case_id": "write_viewmodel_case",
            "osw_version": "0.1.4rc1",
        },
    )
    _write_json(
        root / "write_viewmodel_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "write_viewmodel_feaspec",
            "case_id": "write_viewmodel_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "write_viewmodel_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "write_viewmodel_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "write_viewmodel_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "write_viewmodel_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    (root / "write_viewmodel_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\n"
        "max displacement = 2.5 mm\n"
        "DISPLACEMENTS\n"
        "node | ux\n"
        "units | - | mm\n"
        "1 | 0.1\n",
        encoding="utf-8",
    )
    (root / "write_viewmodel_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    return root


def _viewmodel_inputs(
    tmp_path: Path,
    *,
    output_dir: Path | None = None,
    acknowledge_limitations: bool = True,
    overwrite: bool = False,
    create_dir: bool = False,
):
    import_plan = plan_calculix_result_import(
        _write_result_dir(tmp_path / "result")
    )
    mapping = build_calculix_result_dataset_draft_mapping(import_plan)
    write_plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=output_dir or (tmp_path / "dataset"),
        overwrite=overwrite,
        create_dir=create_dir,
        acknowledge_limitations=acknowledge_limitations,
    )
    schema = build_calculix_result_dataset_schema_payload(mapping, write_plan)
    return import_plan, mapping, write_plan, schema


def test_write_viewmodel_module_imports_and_exports_required_api() -> None:
    assert build_calculix_result_write_viewmodel
    assert preview_calculix_result_write_record
    assert explain_calculix_result_write_viewmodel
    assert FEASpecCalculiXResultWriteViewModel
    assert FEASpecCalculiXResultWriteViewModelInput
    assert FEASpecCalculiXResultWriteSavePlan
    assert FEASpecCalculiXResultWriteAcknowledgementState
    assert FEASpecCalculiXResultWritePanel.SOURCE_RESULT_DIRECTORY
    assert FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET


def test_ready_write_stack_builds_pure_viewmodel(tmp_path: Path) -> None:
    import_plan, mapping, write_plan, schema = _viewmodel_inputs(tmp_path)
    output_dir = tmp_path / "dataset"

    viewmodel = build_calculix_result_write_viewmodel(
        import_plan,
        draft_mapping=mapping,
        write_plan=write_plan,
        schema_payload=schema,
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
        ),
    )

    assert viewmodel.result_dir == str(tmp_path / "result")
    assert viewmodel.output_dir == str(output_dir)
    assert output_dir.exists() is False
    assert FEASpecCalculiXResultWritePanel.WRITE_ACTIONS in viewmodel.panels
    assert viewmodel.rows_for(FEASpecCalculiXResultWritePanel.WRITE_PLAN)
    assert viewmodel.writer_invoked_by_viewmodel is False
    assert viewmodel.files_written is False
    assert viewmodel.solver_execution_performed is False
    assert viewmodel.file_dialog_implemented is False
    assert viewmodel.gui_dialog_implemented is False
    assert viewmodel.action_for(
        FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
    ).state is FEASpecCalculiXResultWriteActionState.ENABLED


def test_preview_record_is_json_serializable_and_no_write(tmp_path: Path) -> None:
    import_plan, mapping, write_plan, schema = _viewmodel_inputs(tmp_path)
    viewmodel = build_calculix_result_write_viewmodel(
        import_plan,
        draft_mapping=mapping,
        write_plan=write_plan,
        schema_payload=schema,
        acknowledgements={"limitations": True, "review_required": True},
    )

    preview = preview_calculix_result_write_record(viewmodel)

    assert preview["viewmodel_only"] is True
    assert preview["writes_files"] is False
    assert preview["writer_invoked_by_viewmodel"] is False
    assert preview["solver_execution_performed"] is False
    json.dumps(preview, sort_keys=True)
    assert (tmp_path / "dataset").exists() is False


def test_writer_result_summary_marks_completion_without_invoking_writer(
    tmp_path: Path,
) -> None:
    import_plan, mapping, write_plan, schema = _viewmodel_inputs(tmp_path)

    viewmodel = build_calculix_result_write_viewmodel(
        import_plan,
        draft_mapping=mapping,
        write_plan=write_plan,
        schema_payload=schema,
        writer_result_summary={
            "status": "written",
            "target_dir": str(tmp_path / "dataset"),
            "written_files": [{"relative_path": "result_dataset.json"}],
        },
        acknowledgements={"limitations": True, "review_required": True},
    )

    assert viewmodel.files_written is True
    assert viewmodel.writer_invoked_by_viewmodel is False
    assert viewmodel.action_for(
        FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
    ).state is FEASpecCalculiXResultWriteActionState.COMPLETED
    assert viewmodel.action_for(
        FEASpecCalculiXResultWriteAction.OPEN_WRITTEN_OUTPUT
    ).state is FEASpecCalculiXResultWriteActionState.ENABLED


def test_explain_viewmodel_is_reviewer_readable(tmp_path: Path) -> None:
    import_plan, mapping, write_plan, schema = _viewmodel_inputs(tmp_path)
    viewmodel = build_calculix_result_write_viewmodel(
        import_plan,
        draft_mapping=mapping,
        write_plan=write_plan,
        schema_payload=schema,
        acknowledgements={"limitations": True, "review_required": True},
    )

    lines = explain_calculix_result_write_viewmodel(viewmodel)

    assert any("write view-model" in line.lower() for line in lines)
    assert any("writer invoked by view-model: false" in line.lower() for line in lines)
    assert any("solver execution performed: false" in line.lower() for line in lines)
