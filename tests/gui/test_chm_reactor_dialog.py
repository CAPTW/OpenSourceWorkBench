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


class FakeReactorAdapter:
    def __init__(self, *, missing: bool = False) -> None:
        self.missing = missing

    def run_zero_d_reactor(self, request: object) -> object:
        from osw.core.diagnostics import DiagnosticReport
        from osw.solvers.cantera.model import CanteraReactorResult

        diagnostics = DiagnosticReport()
        if self.missing:
            diagnostics.add_error("dependency-unavailable", "Cantera is not installed.")
            return CanteraReactorResult("dependency_missing", request, diagnostics=diagnostics)
        return CanteraReactorResult(
            "ok",
            request,
            times=(0.0, 0.001),
            temperature_series=(1000.0, 1025.0),
            pressure_series=(101325.0, 101400.0),
            species_series={"CH4": (0.05, 0.03)},
            table={
                "columns": ["time_s", "temperature_K", "pressure_Pa", "CH4"],
                "rows": [["0", "1000", "101325", "0.05"], ["0.001", "1025", "101400", "0.03"]],
            },
        )


def test_chm_reactor_dialog_instantiates(app: object) -> None:
    from osw.gui.dialogs.chm_reactor_dialog import ChmReactorDialog

    dialog = ChmReactorDialog(adapter=FakeReactorAdapter())

    assert dialog.objectName() == "oswChmReactorDialog"
    assert dialog.mechanism_edit.objectName() == "oswCanteraMechanismEdit"
    assert dialog.composition_edit.objectName() == "oswCanteraCompositionEdit"
    assert dialog.temperature_edit.objectName() == "oswCanteraTemperatureEdit"
    assert dialog.pressure_edit.objectName() == "oswCanteraPressureEdit"
    assert dialog.end_time_edit.objectName() == "oswCanteraEndTimeEdit"
    assert dialog.run_button.objectName() == "oswCanteraRunButton"
    assert dialog.results_table.objectName() == "oswCanteraResultsTable"
    assert dialog.diagnostics_list.objectName() == "oswCanteraDiagnosticsList"
    del app


def test_chm_reactor_dialog_run_and_missing_dependency(app: object) -> None:
    from osw.gui.dialogs.chm_reactor_dialog import ChmReactorDialog

    dialog = ChmReactorDialog(adapter=FakeReactorAdapter())
    result = dialog.run_reactor()

    assert result.status == "ok"
    assert dialog.results_table.rowCount() == 2

    missing = ChmReactorDialog(adapter=FakeReactorAdapter(missing=True))
    missing_result = missing.run_reactor()
    diagnostics = [
        missing.diagnostics_list.item(index).text()
        for index in range(missing.diagnostics_list.count())
    ]

    assert missing_result.status == "dependency_missing"
    assert any("Cantera is not installed" in item for item in diagnostics)
    del app


def test_chm_reactor_dialog_theme(app: object) -> None:
    from osw.gui.dialogs.chm_reactor_dialog import ChmReactorDialog
    from osw.gui.theme_tokens import get_theme_tokens

    dialog = ChmReactorDialog(adapter=FakeReactorAdapter())
    dialog.set_theme_tokens(get_theme_tokens("dark"))
    dialog.set_theme_tokens(get_theme_tokens("light"))

    assert dialog.styleSheet()
    del app

