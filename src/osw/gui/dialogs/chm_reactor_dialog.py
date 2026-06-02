"""Theme-aware CHM Cantera reactor dialog."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class ChmReactorDialog(_BaseDialog):
    """Run bounded in-process Cantera reactor calculations after user action."""

    if QtCore is not None:
        reactorRunCompleted = QtCore.Signal(object)
        resultDatasetReady = QtCore.Signal(object)

    def __init__(
        self,
        parent: object | None = None,
        *,
        adapter: object | None = None,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswChmReactorDialog")
        self.setWindowTitle("Cantera 0D Reactor")
        self.resize(820, 600)
        self.adapter = adapter
        self._tokens = theme_tokens or DARK_TOKENS
        self.last_result: object | None = None

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        self.mechanism_edit = QtWidgets.QLineEdit("gri30.yaml", self)
        self.mechanism_edit.setObjectName("oswCanteraMechanismEdit")
        form.addRow("Mechanism", self.mechanism_edit)

        self.composition_edit = QtWidgets.QLineEdit("CH4:1,O2:2,N2:7.52", self)
        self.composition_edit.setObjectName("oswCanteraCompositionEdit")
        form.addRow("Composition", self.composition_edit)

        self.temperature_edit = QtWidgets.QLineEdit("1000", self)
        self.temperature_edit.setObjectName("oswCanteraTemperatureEdit")
        form.addRow("Temperature [K]", self.temperature_edit)

        self.pressure_edit = QtWidgets.QLineEdit("101325", self)
        self.pressure_edit.setObjectName("oswCanteraPressureEdit")
        form.addRow("Pressure [Pa]", self.pressure_edit)

        self.end_time_edit = QtWidgets.QLineEdit("0.001", self)
        self.end_time_edit.setObjectName("oswCanteraEndTimeEdit")
        form.addRow("End time [s]", self.end_time_edit)

        self.results_table = QtWidgets.QTableWidget(self)
        self.results_table.setObjectName("oswCanteraResultsTable")
        layout.addWidget(self.results_table, 1)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswCanteraDiagnosticsList")
        layout.addWidget(self.diagnostics_list)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.run_button = QtWidgets.QPushButton("Run Reactor", self)
        self.run_button.setObjectName("oswCanteraRunButton")
        buttons.addWidget(self.run_button)
        layout.addLayout(buttons)

        self.run_button.clicked.connect(self.run_reactor)
        self.set_theme_tokens(self._tokens)

    def current_request(self) -> object:
        model = import_module("osw.solvers.cantera.model")
        return model.CanteraReactorRequest(
            mixture=model.CanteraMixtureSpec(
                mechanism=self.mechanism_edit.text(),
                composition=self.composition_edit.text(),
                temperature=float(self.temperature_edit.text()),
                pressure=float(self.pressure_edit.text()),
            ),
            end_time=float(self.end_time_edit.text()),
            time_step=min(float(self.end_time_edit.text()), 0.00025),
            tracked_species=("CH4", "O2", "CO2", "H2O"),
        )

    def run_reactor(self) -> object:
        adapter = self.adapter or import_module("osw.solvers.cantera.reactor_adapter")
        results = import_module("osw.solvers.cantera.results")
        result = adapter.run_zero_d_reactor(self.current_request())
        self.last_result = result
        self._show_result(result)
        self._show_diagnostics(getattr(result, "diagnostics", None))
        if getattr(result, "status", "") in {"ok", "warning"}:
            self.resultDatasetReady.emit(results.cantera_result_to_result_dataset(result))
        self.reactorRunCompleted.emit(result)
        return result

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswChmReactorDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLineEdit, QTableWidget, QListWidget {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "}"
            "QPushButton {"
            f"background-color: {tokens.accent};"
            f"color: {tokens.bg_app};"
            f"border: 1px solid {tokens.primary_hover};"
            "padding: 6px 12px;"
            "}"
        )

    def _show_result(self, result: object) -> None:
        table = dict(getattr(result, "table", {}) or {})
        columns = tuple(table.get("columns", ()) or ())
        rows = tuple(table.get("rows", ()) or ())
        self.results_table.setColumnCount(len(columns))
        self.results_table.setHorizontalHeaderLabels(list(columns))
        self.results_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, cell in enumerate(row):
                self.results_table.setItem(
                    row_index,
                    column_index,
                    QtWidgets.QTableWidgetItem(str(cell)),
                )
        self.results_table.resizeColumnsToContents()

    def _show_diagnostics(self, diagnostics: object | None) -> None:
        self.diagnostics_list.clear()
        messages = getattr(diagnostics, "messages", ()) if diagnostics is not None else ()
        for message in messages:
            severity = str(getattr(getattr(message, "severity", ""), "value", ""))
            code = str(getattr(message, "code", ""))
            text = str(getattr(message, "message", ""))
            self.diagnostics_list.addItem(f"{severity.upper()} {code}: {text}")
        if not messages:
            self.diagnostics_list.addItem("No diagnostics.")


__all__ = ["ChmReactorDialog"]

