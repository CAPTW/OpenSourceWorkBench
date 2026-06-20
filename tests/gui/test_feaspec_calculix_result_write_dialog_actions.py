from __future__ import annotations

import importlib.util
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


def _viewmodel(tmp_path: Path, *, missing_output: bool = False):
    from osw.experimental.feaspec import (
        FEASpecCalculiXResultWriteAcknowledgementState,
        build_calculix_result_write_viewmodel,
    )

    target = {} if missing_output else {"output_dir": str(tmp_path / "dataset")}
    return build_calculix_result_write_viewmodel(
        {
            "status": "ready",
            "result_dir": str(tmp_path / "result"),
            "artifacts": [{"path": "case.dat"}],
            "diagnostics": [],
        },
        draft_mapping={
            "status": "ready",
            "dataset_id": "dialog_actions_dataset",
            "artifacts": [{"path": "case.dat"}],
            "limitations": ["Review parser limitations."],
            "diagnostics": [],
        },
        write_plan={
            "status": "ready" if target else "blocked",
            "target": target,
            "planned_files": [{"relative_path": "result_dataset.json"}],
            "limitations_acknowledged": True,
            "copy_artifacts_requested": False,
            "diagnostics": (
                []
                if target
                else [
                    {
                        "code": "FDW_OUTPUT_DIR_MISSING",
                        "message": "Output directory is required.",
                        "blocks_write": True,
                    }
                ]
            ),
        },
        schema_payload={
            "status": "ready",
            "schema": {"schema_name": "ResultDataset", "schema_version": "0.1"},
            "dataset": {"dataset_id": "dialog_actions_dataset"},
            "planned_files": [{"relative_path": "result_dataset.json"}],
            "limitations": ["Review before use."],
            "schema_diagnostics": [],
        },
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
        ),
    )


def test_action_buttons_render_write_disabled_and_file_dialog_enabled(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import FEASpecCalculiXResultWriteAction
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(_viewmodel(tmp_path))

    assert "Choose output directory" in dialog.action_labels()
    assert "Write ResultDataset" in dialog.action_labels()
    assert dialog.has_write_enabled() is False
    assert dialog.has_file_dialog_controls() is True
    assert dialog.choose_output_directory_enabled() is True
    write_button = dialog.action_button(
        FEASpecCalculiXResultWriteAction.WRITE_RESULT_DATASET
    )
    choose_button = dialog.action_button(
        FEASpecCalculiXResultWriteAction.CHOOSE_OUTPUT_DIRECTORY
    )
    assert write_button is not None
    assert choose_button is not None
    assert write_button.isEnabled() is False
    assert choose_button.isEnabled() is True


def test_disabled_reasons_include_viewmodel_and_display_only_gate(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path, missing_output=True)
    )
    text = "\n".join(dialog.disabled_reason_texts())

    assert "missing_output_dir" in text
    assert "write_plan_blocked" in text
    assert "display_only_dialog" in text
    assert "FDW_OUTPUT_DIR_MISSING" in dialog.diagnostics_text()


def test_action_button_clicks_do_not_create_files(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    sentinel = tmp_path / "dataset" / "result_dataset.json"
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path),
        output_directory_chooser=lambda _title, _initial: str(tmp_path / "chosen"),
    )

    for button in dialog.findChildren(QtWidgets.QPushButton):
        if button is dialog.close_button:
            continue
        button.click()

    assert sentinel.exists() is False
    assert (tmp_path / "chosen").exists() is False
    assert dialog.write_invocation_count() == 0
    assert dialog.file_dialog_invocation_count() == 1


def test_close_button_only_closes_dialog(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    sentinel = tmp_path / "dataset" / "result_dataset.json"
    dialog = FEASpecCalculiXResultWriteDialog(_viewmodel(tmp_path))

    dialog.close_button.click()

    assert sentinel.exists() is False
    assert dialog.result() == QtWidgets.QDialog.DialogCode.Rejected
    assert dialog.write_invocation_count() == 0
