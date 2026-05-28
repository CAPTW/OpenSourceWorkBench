from __future__ import annotations

import importlib.util
import os

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


def _sample_curve() -> object:
    from osw.core.boundary_curve import BoundaryCurveSource, boundary_curve_from_xy

    return boundary_curve_from_xy(
        [0, 1, 2],
        [20, 30, 40],
        "Temperature curve",
        curve_id="temperature-curve",
        x_unit="s",
        y_unit="degC",
        kind="temperature_profile",
        source=BoundaryCurveSource(source_file="curves.csv", variable_names=("time", "temp")),
    )


def test_boundary_curve_dialog_object_names(app: object) -> None:
    from osw.gui.dialogs.boundary_curve_dialog import BoundaryCurveDialog

    dialog = BoundaryCurveDialog(_sample_curve())

    assert dialog.objectName() == "oswBoundaryCurveDialog"
    assert dialog.preview_panel.objectName() == "oswBoundaryCurvePanel"
    assert dialog.preview_panel.name_edit.objectName() == "oswBoundaryCurveNameEdit"
    assert dialog.preview_panel.kind_combo.objectName() == "oswBoundaryCurveKindCombo"
    assert dialog.preview_panel.x_unit_edit.objectName() == "oswBoundaryCurveXAxisUnitEdit"
    assert dialog.preview_panel.y_unit_edit.objectName() == "oswBoundaryCurveYAxisUnitEdit"
    assert dialog.preview_panel.interpolation_combo.objectName() == (
        "oswBoundaryCurveInterpolationCombo"
    )
    assert dialog.preview_panel.preview_table.objectName() == "oswBoundaryCurvePreviewTable"
    assert dialog.preview_panel.diagnostics_list.objectName() == (
        "oswBoundaryCurveDiagnosticsList"
    )
    assert dialog.preview_panel.create_button.objectName() == "oswBoundaryCurveCreateButton"
    assert dialog.preview_panel.cancel_button.objectName() == "oswBoundaryCurveCancelButton"


def test_boundary_curve_dialog_displays_preview_and_diagnostics(app: object) -> None:
    from osw.core.boundary_curve import BoundaryCurve
    from osw.gui.dialogs.boundary_curve_dialog import BoundaryCurveDialog

    invalid_curve = BoundaryCurve(
        curve_id="invalid",
        name="Invalid",
        x_values=[0],
        y_values=[1],
    )
    dialog = BoundaryCurveDialog(invalid_curve)

    assert dialog.preview_panel.preview_table.rowCount() == 1
    assert dialog.preview_panel.diagnostics_list.count() >= 1


def test_boundary_curve_dialog_theme_switching(app: object) -> None:
    from osw.gui.dialogs.boundary_curve_dialog import BoundaryCurveDialog
    from osw.gui.theme_tokens import get_theme_tokens

    dialog = BoundaryCurveDialog(_sample_curve())

    dialog.set_theme_tokens(get_theme_tokens("dark"))
    dialog.set_theme_tokens(get_theme_tokens("light"))
    assert dialog.styleSheet()
