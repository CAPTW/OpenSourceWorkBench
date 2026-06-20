from __future__ import annotations

import json
from pathlib import Path

from osw.experimental.feaspec import (
    FEASpecCalculiXResultWriteAcknowledgementState,
    FEASpecCalculiXResultWriteAction,
    FEASpecCalculiXResultWriteActionState,
    FEASpecCalculiXResultWriteDisabledReason,
    build_calculix_result_dataset_draft_mapping,
    build_calculix_result_dataset_schema_payload,
    build_calculix_result_write_viewmodel,
    plan_calculix_result_dataset_write,
    plan_calculix_result_import,
    plan_calculix_result_write_save_path,
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
            "source_feaspec_id": "write_viewmodel_action_feaspec",
            "case_id": "write_viewmodel_action_case",
            "osw_version": "0.1.4rc1",
        },
    )
    _write_json(
        root / "write_viewmodel_action_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "write_viewmodel_action_feaspec",
            "case_id": "write_viewmodel_action_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(
        root / "write_viewmodel_action_case.diagnostics.json",
        {"status": "exported"},
    )
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "write_viewmodel_action_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "write_viewmodel_action_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "write_viewmodel_action_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    (root / "write_viewmodel_action_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\n"
        "max displacement = 2.5 mm\n"
        "DISPLACEMENTS\n"
        "node | ux\n"
        "units | - | mm\n"
        "1 | 0.1\n",
        encoding="utf-8",
    )
    (root / "write_viewmodel_action_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    return root


def _mapping(tmp_path: Path):
    import_plan = plan_calculix_result_import(
        _write_result_dir(tmp_path / "result")
    )
    return import_plan, build_calculix_result_dataset_draft_mapping(import_plan)


def _viewmodel(
    tmp_path: Path,
    *,
    output_dir: Path | None = None,
    acknowledge_limitations: bool = True,
    acknowledgements: FEASpecCalculiXResultWriteAcknowledgementState | None = None,
    overwrite: bool = False,
    create_dir: bool = False,
    schema_version: str | None = None,
):
    import_plan, mapping = _mapping(tmp_path)
    write_plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=output_dir or (tmp_path / "dataset"),
        overwrite=overwrite,
        create_dir=create_dir,
        acknowledge_limitations=acknowledge_limitations,
    )
    schema = build_calculix_result_dataset_schema_payload(
        mapping,
        write_plan,
        schema_version=schema_version,
    )
    return build_calculix_result_write_viewmodel(
        import_plan,
        draft_mapping=mapping,
        write_plan=write_plan,
        schema_payload=schema,
        acknowledgements=acknowledgements
        or FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
            overwrite=overwrite,
            create_dir=create_dir,
        ),
    )


def test_missing_output_and_objects_disable_write_action() -> None:
    viewmodel = build_calculix_result_write_viewmodel()

    action = viewmodel.action_for(FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET)

    assert action.state is FEASpecCalculiXResultWriteActionState.DISABLED
    assert FEASpecCalculiXResultWriteDisabledReason.MISSING_RESULT_DIR in (
        action.disabled_reasons
    )
    assert FEASpecCalculiXResultWriteDisabledReason.MISSING_OUTPUT_DIR in (
        action.disabled_reasons
    )
    assert FEASpecCalculiXResultWriteDisabledReason.WRITE_NOT_AVAILABLE in (
        action.disabled_reasons
    )


def test_missing_acknowledgements_disable_write_action(tmp_path: Path) -> None:
    viewmodel = _viewmodel(
        tmp_path,
        acknowledge_limitations=False,
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(),
    )

    reasons = viewmodel.action_for(
        FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
    ).disabled_reasons

    assert (
        FEASpecCalculiXResultWriteDisabledReason.MISSING_LIMITATIONS_ACKNOWLEDGEMENT
        in reasons
    )
    assert (
        FEASpecCalculiXResultWriteDisabledReason.MISSING_REVIEW_ACKNOWLEDGEMENT
        in reasons
    )
    assert FEASpecCalculiXResultWriteDisabledReason.WRITE_PLAN_BLOCKED in reasons


def test_overwrite_acknowledgement_gates_nonempty_target(tmp_path: Path) -> None:
    output_dir = tmp_path / "dataset"
    output_dir.mkdir()
    (output_dir / "README_REVIEW_FIRST.txt").write_text("existing\n", encoding="utf-8")

    blocked = _viewmodel(
        tmp_path,
        output_dir=output_dir,
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
        ),
    )

    reasons = blocked.action_for(
        FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
    ).disabled_reasons
    assert FEASpecCalculiXResultWriteDisabledReason.OVERWRITE_REQUIRED in reasons
    assert FEASpecCalculiXResultWriteDisabledReason.WRITE_PLAN_BLOCKED in reasons

    allowed = _viewmodel(
        tmp_path / "allowed",
        output_dir=output_dir,
        overwrite=True,
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
            overwrite=True,
        ),
    )
    assert allowed.save_plan.overwrite_required is True
    assert FEASpecCalculiXResultWriteDisabledReason.OVERWRITE_REQUIRED not in (
        allowed.write_disabled_reasons
    )


def test_create_dir_acknowledgement_gates_missing_parent_plan(tmp_path: Path) -> None:
    output_dir = tmp_path / "missing" / "dataset"

    blocked = _viewmodel(
        tmp_path,
        output_dir=output_dir,
        create_dir=True,
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
        ),
    )

    assert blocked.save_plan.create_dir_required is True
    assert (
        FEASpecCalculiXResultWriteDisabledReason.CREATE_DIR_REQUIRED
        in blocked.write_disabled_reasons
    )

    allowed = _viewmodel(
        tmp_path / "allowed",
        output_dir=output_dir,
        create_dir=True,
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
            create_dir=True,
        ),
    )
    assert (
        FEASpecCalculiXResultWriteDisabledReason.CREATE_DIR_REQUIRED
        not in allowed.write_disabled_reasons
    )


def test_blocked_schema_disables_write_action(tmp_path: Path) -> None:
    viewmodel = _viewmodel(tmp_path, schema_version="")

    reasons = viewmodel.action_for(
        FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
    ).disabled_reasons

    assert FEASpecCalculiXResultWriteDisabledReason.SCHEMA_BLOCKED in reasons


def test_save_path_analysis_rejects_unsafe_path_without_filesystem_touch(
    tmp_path: Path,
) -> None:
    viewmodel = _viewmodel(tmp_path)

    save_plan = plan_calculix_result_write_save_path(
        viewmodel,
        str(tmp_path / ".git" / "dataset"),
    )

    assert save_plan.unsafe_path is True
    assert save_plan.can_write_target is False
    assert FEASpecCalculiXResultWriteDisabledReason.UNSAFE_PATH in (
        save_plan.disabled_reasons
    )
    assert (tmp_path / ".git").exists() is False
