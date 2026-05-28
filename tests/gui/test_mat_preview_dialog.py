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


def _sample_result() -> object:
    from osw.scripts.mscript.mat_model import (
        MatFileSummary,
        MatFileVersion,
        MatReadResult,
        MatReadStatus,
        MatVariableSummary,
    )

    variable = MatVariableSummary(
        "x",
        shape=(3,),
        dtype="float64",
        is_numeric=True,
        kind="numeric",
        preview="[0, 1, 2]",
    )
    summary = MatFileSummary(
        source_path=Path("numeric_arrays.mat"),
        version=MatFileVersion.V4,
        variables=(variable,),
    )
    return MatReadResult(MatReadStatus.OK, summary, values={"x": [0.0, 1.0, 2.0]})


def test_mat_preview_dialog_object_names(app: object) -> None:
    from osw.gui.dialogs.mat_preview_dialog import MatPreviewDialog

    dialog = MatPreviewDialog(_sample_result())

    assert dialog.objectName() == "oswMatPreviewDialog"
    assert dialog.preview_panel.objectName() == "oswMatPreviewPanel"
    assert dialog.preview_panel.source_path_label.objectName() == "oswMatPreviewSourcePath"
    assert dialog.preview_panel.version_label.objectName() == "oswMatPreviewVersionLabel"
    assert dialog.preview_panel.variables_table.objectName() == "oswMatVariablesTable"
    assert dialog.preview_panel.variable_preview_table.objectName() == (
        "oswMatVariablePreviewTable"
    )
    assert dialog.preview_panel.diagnostics_list.objectName() == "oswMatDiagnosticsList"
    assert dialog.preview_panel.export_csv_button.objectName() == "oswMatExportCsvButton"
    assert dialog.preview_panel.import_button.objectName() == "oswMatImportButton"
    assert dialog.preview_panel.cancel_button.objectName() == "oswMatCancelButton"


def test_mat_preview_dialog_displays_variables_and_no_run_button(app: object) -> None:
    from osw.gui.dialogs.mat_preview_dialog import MatPreviewDialog

    dialog = MatPreviewDialog(_sample_result())

    assert dialog.preview_panel.variables_table.rowCount() == 1
    assert dialog.preview_panel.variable_preview_table.rowCount() == 3
    assert dialog.findChild(QtWidgets.QPushButton, "oswScriptRunWithOctaveButton") is None


def test_mat_preview_dialog_theme_switching(app: object) -> None:
    from osw.gui.dialogs.mat_preview_dialog import MatPreviewDialog
    from osw.gui.theme_tokens import get_theme_tokens

    dialog = MatPreviewDialog(_sample_result())

    dialog.set_theme_tokens(get_theme_tokens("dark"))
    dialog.set_theme_tokens(get_theme_tokens("light"))
