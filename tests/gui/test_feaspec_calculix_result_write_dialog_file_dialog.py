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


def _viewmodel(
    tmp_path: Path,
    *,
    parent_exists: bool = True,
    planned_file_exists: bool = False,
    output_dir: Path | None = None,
):
    from osw.experimental.feaspec import (
        FEASpecCalculiXResultWriteAcknowledgementState,
        build_calculix_result_write_viewmodel,
    )

    target_dir = output_dir or tmp_path / "dataset"
    planned_files = [
        {"relative_path": "result_dataset.json", "exists": planned_file_exists},
        {
            "relative_path": "result_dataset_manifest.json",
            "exists": planned_file_exists,
        },
    ]
    return build_calculix_result_write_viewmodel(
        {
            "status": "ready",
            "result_dir": str(tmp_path / "result"),
            "artifacts": [{"path": "case.dat"}],
            "diagnostics": [],
        },
        draft_mapping={
            "status": "ready",
            "dataset_id": "file_dialog_dataset",
            "artifacts": [{"path": "case.dat"}],
            "limitations": ["Review parser limitations."],
            "diagnostics": [],
        },
        write_plan={
            "status": "ready",
            "target": {
                "output_dir": str(target_dir),
                "parent_exists": parent_exists,
                "target_exists": False,
            },
            "planned_files": planned_files,
            "limitations_acknowledged": True,
            "copy_artifacts_requested": False,
            "diagnostics": [],
        },
        schema_payload={
            "status": "ready",
            "schema": {"schema_name": "ResultDataset", "schema_version": "0.1"},
            "dataset": {"dataset_id": "file_dialog_dataset"},
            "planned_files": planned_files,
            "limitations": ["Review before use."],
            "schema_diagnostics": [],
        },
        acknowledgements=FEASpecCalculiXResultWriteAcknowledgementState(
            limitations=True,
            review_required=True,
        ),
    )


def test_dialog_exposes_output_directory_control(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(_viewmodel(tmp_path))

    assert dialog.has_file_dialog_controls() is True
    assert dialog.choose_output_directory_enabled() is True
    assert dialog.output_directory_text() == str(tmp_path / "dataset")
    assert "Selected output directory" in dialog.save_plan_text()


def test_injected_chooser_accepts_directory_and_updates_display(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.experimental.feaspec import FEASpecCalculiXResultWriteAction
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    selected = tmp_path / "selected-dataset"
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path),
        output_directory_chooser=lambda _title, _initial: selected,
    )
    button = dialog.action_button(
        FEASpecCalculiXResultWriteAction.CHOOSE_OUTPUT_DIRECTORY
    )
    assert button is not None

    button.click()

    assert dialog.file_dialog_invocation_count() == 1
    assert dialog.selected_output_directory() == str(selected)
    assert dialog.output_directory_text() == str(selected)
    assert str(selected) in dialog.save_plan_text()
    assert selected.exists() is False
    assert dialog.write_invocation_count() == 0


def test_cancel_is_noop(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    initial = str(tmp_path / "dataset")
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path),
        output_directory_chooser=lambda _title, _initial: "",
    )

    assert dialog.choose_output_directory() is False
    assert dialog.file_dialog_invocation_count() == 1
    assert dialog.selected_output_directory() == initial
    assert dialog.output_directory_text() == initial
    assert dialog.write_invocation_count() == 0


def test_select_output_directory_for_test_updates_without_dialog_count(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    selected = tmp_path / "manual-selection"
    dialog = FEASpecCalculiXResultWriteDialog(_viewmodel(tmp_path))

    assert dialog.select_output_directory_for_test(selected) is True
    assert dialog.file_dialog_invocation_count() == 0
    assert dialog.selected_output_directory() == str(selected)
    assert str(selected) in dialog.output_directory_text()


def test_missing_parent_create_dir_requirement_is_surfaced(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    selected = tmp_path / "missing-parent" / "dataset"
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path, parent_exists=False),
        output_directory_chooser=lambda _title, _initial: selected,
    )

    assert dialog.choose_output_directory() is True
    assert '"create_dir_required": true' in dialog.save_plan_text()
    assert "create_dir_required" in dialog.save_plan_text()
    assert selected.parent.exists() is False


def test_overwrite_requirement_is_surfaced(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path, planned_file_exists=True),
    )

    assert '"overwrite_required": true' in dialog.save_plan_text()
    assert "overwrite_required" in dialog.save_plan_text()


def test_unsafe_path_remains_blocked(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    selected = tmp_path / ".git" / "dataset"
    dialog = FEASpecCalculiXResultWriteDialog(_viewmodel(tmp_path))

    assert dialog.select_output_directory_for_test(selected) is True
    assert '"unsafe_path": true' in dialog.save_plan_text()
    assert "unsafe_path" in dialog.save_plan_text()
    assert selected.exists() is False


def test_file_dialog_selection_writes_no_files_or_directories(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    selected = tmp_path / "new-output"
    sentinel = selected / "result_dataset.json"
    dialog = FEASpecCalculiXResultWriteDialog(
        _viewmodel(tmp_path),
        output_directory_chooser=lambda _title, _initial: selected,
    )

    assert dialog.choose_output_directory() is True
    assert selected.exists() is False
    assert sentinel.exists() is False
    assert dialog.write_invocation_count() == 0
    assert dialog.has_write_enabled() is False


def test_safety_text_keeps_no_run_boundary(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.feaspec_calculix_result_write_dialog import (
        FEASpecCalculiXResultWriteDialog,
    )

    dialog = FEASpecCalculiXResultWriteDialog(_viewmodel(tmp_path))
    text = dialog.safety_text()

    assert "Writer calls require enabled gates" in text
    assert "existing library writer" in text
    assert "No artifact copying." in text
    assert "No directory creation during selection." in text
    assert "No solver execution." in text
    assert (
        "GitHub state verified 2026-07-14: Issue #8 is closed after bounded WSL "
        "CalculiX evidence; this workflow does not broaden that closure."
    ) in text
