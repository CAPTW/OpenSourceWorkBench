from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class _FakeWriter:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result
        self.calls: list[tuple[object, object, bool]] = []

    def __call__(
        self,
        write_plan: object,
        schema_payload: object,
        *,
        overwrite: bool = False,
    ) -> dict[str, object]:
        self.calls.append((write_plan, schema_payload, overwrite))
        return self.result


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
            "source_feaspec_id": "gui_write_feaspec",
            "case_id": "gui_write_case",
            "osw_version": "0.1.4rc1",
        },
    )
    _write_json(
        root / "gui_write_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "gui_write_feaspec",
            "case_id": "gui_write_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "gui_write_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "gui_write_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "gui_write_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "gui_write_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    (root / "gui_write_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\n"
        "max displacement = 2.5 mm\n"
        "DISPLACEMENTS\n"
        "node | ux\n"
        "units | - | mm\n"
        "1 | 0.1\n",
        encoding="utf-8",
    )
    (root / "gui_write_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    return root


def _viewmodel(
    tmp_path: Path,
    *,
    output_dir: Path | None = None,
    acknowledgements: object | None = None,
    overwrite: bool = False,
    create_dir: bool = False,
    acknowledge_limitations: bool = True,
):
    from osw.experimental.feaspec import (
        FEASpecCalculiXResultWriteAcknowledgementState,
        build_calculix_result_dataset_draft_mapping,
        build_calculix_result_dataset_schema_payload,
        build_calculix_result_write_viewmodel,
        plan_calculix_result_dataset_write,
        plan_calculix_result_import,
    )

    import_plan = plan_calculix_result_import(_write_result_dir(tmp_path / "result"))
    mapping = build_calculix_result_dataset_draft_mapping(import_plan)
    write_plan = plan_calculix_result_dataset_write(
        mapping,
        output_dir=output_dir or (tmp_path / "dataset"),
        overwrite=overwrite,
        create_dir=create_dir,
        acknowledge_limitations=acknowledge_limitations,
    )
    schema = build_calculix_result_dataset_schema_payload(mapping, write_plan)
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


def test_write_button_enabled_only_when_gates_are_satisfied(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import FEASpecCalculiXResultWriteAcknowledgementState
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    ready = FEASpecCalculiXResultWriteDialog(_viewmodel(tmp_path))
    missing_ack = FEASpecCalculiXResultWriteDialog(
        _viewmodel(
            tmp_path / "missing_ack",
            acknowledge_limitations=False,
            acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(),
        )
    )

    assert ready.write_button_enabled() is True
    assert missing_ack.write_button_enabled() is False
    assert "missing_limitations_acknowledgement" in "\n".join(
        missing_ack.disabled_reason_texts()
    )


def test_write_requires_confirmation_before_calling_writer(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    writer = _FakeWriter({"status": "written", "written_files": []})
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path),
        result_dataset_writer=writer,
    )

    assert dialog.trigger_write_for_test(confirm=False) is False

    assert writer.calls == []
    assert dialog.write_invocation_count() == 0
    assert "Write FEASpec CalculiX ResultDataset files?" in (
        dialog.write_confirmation_text()
    )


def test_confirmed_write_calls_injected_writer_once(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    result = {
        "status": "written",
        "target_dir": str(tmp_path / "dataset"),
        "written_files": [
            {
                "relative_path": "result_dataset.json",
                "size_bytes": 12,
                "sha256": "abc123",
            }
        ],
    }
    writer = _FakeWriter(result)
    viewmodel = _viewmodel(tmp_path)
    dialog = FEASpecCalculiXResultWriteDialog(
        viewmodel,
        result_dataset_writer=writer,
    )

    assert dialog.trigger_write_for_test(confirm=True) is True

    assert writer.calls == [
        (viewmodel.inputs.write_plan, viewmodel.inputs.schema_payload, False)
    ]
    assert dialog.write_invocation_count() == 1
    assert "result_dataset.json" in dialog.last_writer_result_text()
    assert "abc123" in dialog.written_files_text()
    assert dialog.write_button_enabled() is False


def test_real_library_writer_writes_only_resultdataset_files_under_selected_output(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    output_dir = tmp_path / "dataset"
    dialog = FEASpecCalculiXResultWriteDialog(_viewmodel(tmp_path, output_dir=output_dir))

    assert dialog.trigger_write_for_test(confirm=True) is True

    expected = {
        "README_REVIEW_FIRST.txt",
        "diagnostics.json",
        "provenance.json",
        "result_dataset.json",
        "result_dataset_manifest.json",
    }
    assert {path.name for path in output_dir.iterdir()} == expected
    assert not (output_dir / "gui_write_case.dat").exists()
    assert not (output_dir / "gui_write_case.frd").exists()
    assert "result_dataset_manifest.json" in dialog.last_writer_result_text()
    assert dialog.write_invocation_count() == 1


def test_selected_output_mismatch_blocks_writer_call(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    writer = _FakeWriter({"status": "written", "written_files": []})
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path),
        result_dataset_writer=writer,
    )

    assert dialog.select_output_directory_for_test(tmp_path / "other") is True
    assert dialog.write_button_enabled() is False
    assert dialog.trigger_write_for_test(confirm=True) is False

    assert writer.calls == []
    assert "selected_output_mismatch" in "\n".join(dialog.disabled_reason_texts())


def test_writer_failure_updates_result_panel_without_creating_success_state(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    writer = _FakeWriter(
        {
            "status": "partial-cleanup-failed",
            "diagnostics": [{"code": "FDW_PARTIAL_CLEANUP_FAILED"}],
        }
    )
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path),
        result_dataset_writer=writer,
    )

    assert dialog.trigger_write_for_test(confirm=True) is False

    assert len(writer.calls) == 1
    assert "partial-cleanup-failed" in dialog.last_writer_result_text()
    assert "FDW_PARTIAL_CLEANUP_FAILED" in dialog.last_writer_result_text()
    assert dialog.write_button_enabled() is True


def test_overwrite_and_create_directory_acknowledgements_gate_write(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import FEASpecCalculiXResultWriteAcknowledgementState
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    output_dir = tmp_path / "dataset"
    output_dir.mkdir()
    (output_dir / "result_dataset.json").write_text("existing", encoding="utf-8")
    overwrite_dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(
            tmp_path,
            output_dir=output_dir,
            acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
                limitations=True,
                review_required=True,
            ),
        )
    )
    create_dir_dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(
            tmp_path / "create",
            output_dir=tmp_path / "missing" / "dataset",
            create_dir=True,
            acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
                limitations=True,
                review_required=True,
            ),
        )
    )

    assert overwrite_dialog.write_button_enabled() is False
    assert "overwrite_required" in "\n".join(overwrite_dialog.disabled_reason_texts())
    assert create_dir_dialog.write_button_enabled() is False
    assert "create_dir_required" in "\n".join(
        create_dir_dialog.disabled_reason_texts()
    )


def test_source_has_no_solver_execution_or_artifact_copy_paths() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "osw"
        / "gui"
        / "dialogs"
        / "feaspec_calculix_result_write_dialog.py"
    )
    source = module_path.read_text(encoding="utf-8")
    forbidden = (
        "SolverAdapter",
        "CalculiXRunner",
        "run_calculix",
        "ccx.exe",
        "shutil.copy",
        "copy2",
        "getOpenFileName",
        "getSaveFileName",
    )

    for token in forbidden:
        assert token not in source
    assert "QFileDialog.getExistingDirectory" in source
    assert "write_calculix_result_dataset" in source
