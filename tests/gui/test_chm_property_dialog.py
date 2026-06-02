from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class FakePropertyAdapter:
    def __init__(self, *, missing: bool = False) -> None:
        self.missing = missing

    def calculate_properties(self, request: object) -> object:
        from osw.core.diagnostics import DiagnosticReport
        from osw.solvers.coolprop.model import (
            CoolPropPropertyResult,
            CoolPropPropertyValue,
        )

        diagnostics = DiagnosticReport()
        if self.missing:
            diagnostics.add_error("dependency-unavailable", "CoolProp is not installed.")
            return CoolPropPropertyResult("dependency_missing", request, diagnostics=diagnostics)
        return CoolPropPropertyResult(
            "ok",
            request,
            values=(CoolPropPropertyValue("density", 997.0, "kg/m^3"),),
        )

    def sweep_properties(self, request: object) -> object:
        from osw.solvers.coolprop.model import CoolPropSweepResult

        return CoolPropSweepResult(
            "ok",
            request,
            columns=("T [K]", "density [kg/m^3]"),
            rows=((280.0, 999.0), (300.0, 997.0)),
            series={"density": (999.0, 997.0)},
        )


def test_chm_property_dialog_instantiates(app: object) -> None:
    from osw.gui.dialogs.chm_property_dialog import ChmPropertyDialog

    dialog = ChmPropertyDialog(adapter=FakePropertyAdapter())

    assert dialog.objectName() == "oswChmPropertyDialog"
    assert dialog.fluid_combo.objectName() == "oswCoolPropFluidCombo"
    assert dialog.calculate_button.objectName() == "oswCoolPropCalculateButton"
    assert dialog.sweep_button.objectName() == "oswCoolPropSweepButton"
    assert dialog.results_table.objectName() == "oswCoolPropResultsTable"
    assert dialog.diagnostics_list.objectName() == "oswCoolPropDiagnosticsList"
    del app


def test_chm_property_dialog_calculate_and_missing_dependency(app: object) -> None:
    from osw.gui.dialogs.chm_property_dialog import ChmPropertyDialog

    dialog = ChmPropertyDialog(adapter=FakePropertyAdapter())
    result = dialog.calculate_properties()

    assert result.status == "ok"
    assert dialog.results_table.rowCount() == 1

    missing = ChmPropertyDialog(adapter=FakePropertyAdapter(missing=True))
    missing_result = missing.calculate_properties()
    diagnostics = [
        missing.diagnostics_list.item(index).text()
        for index in range(missing.diagnostics_list.count())
    ]

    assert missing_result.status == "dependency_missing"
    assert any("CoolProp is not installed" in item for item in diagnostics)
    del app


def test_chm_property_dialog_sweep_and_theme(app: object) -> None:
    from osw.gui.dialogs.chm_property_dialog import ChmPropertyDialog
    from osw.gui.theme_tokens import get_theme_tokens

    dialog = ChmPropertyDialog(adapter=FakePropertyAdapter())
    result = dialog.calculate_sweep()
    dialog.set_theme_tokens(get_theme_tokens("dark"))
    dialog.set_theme_tokens(get_theme_tokens("light"))

    assert result.status == "ok"
    assert dialog.results_table.columnCount() == 2
    assert dialog.styleSheet()
    del app

