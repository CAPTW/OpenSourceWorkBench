"""Theme-aware CHM CoolProp property dialog."""

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


class ChmPropertyDialog(_BaseDialog):
    """Calculate bounded CoolProp property points and sweeps after user action."""

    if QtCore is not None:
        propertyCalculated = QtCore.Signal(object)
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
        self.setObjectName("oswChmPropertyDialog")
        self.setWindowTitle("CoolProp Property Calculator")
        self.resize(760, 560)
        self.adapter = adapter
        self._tokens = theme_tokens or DARK_TOKENS
        self.last_result: object | None = None

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        self.fluid_combo = QtWidgets.QComboBox(self)
        self.fluid_combo.setObjectName("oswCoolPropFluidCombo")
        self.fluid_combo.setEditable(True)
        self.fluid_combo.addItems(["Water", "Nitrogen", "Methane", "Air"])
        form.addRow("Fluid", self.fluid_combo)

        self.temperature_edit = QtWidgets.QLineEdit("300", self)
        self.temperature_edit.setObjectName("oswCoolPropTemperatureEdit")
        form.addRow("Temperature [K]", self.temperature_edit)

        self.pressure_edit = QtWidgets.QLineEdit("101325", self)
        self.pressure_edit.setObjectName("oswCoolPropPressureEdit")
        form.addRow("Pressure [Pa]", self.pressure_edit)

        self.results_table = QtWidgets.QTableWidget(self)
        self.results_table.setObjectName("oswCoolPropResultsTable")
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Property", "Value", "Unit"])
        layout.addWidget(self.results_table, 1)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswCoolPropDiagnosticsList")
        layout.addWidget(self.diagnostics_list)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.calculate_button = QtWidgets.QPushButton("Calculate", self)
        self.calculate_button.setObjectName("oswCoolPropCalculateButton")
        self.sweep_button = QtWidgets.QPushButton("Sweep", self)
        self.sweep_button.setObjectName("oswCoolPropSweepButton")
        buttons.addWidget(self.calculate_button)
        buttons.addWidget(self.sweep_button)
        layout.addLayout(buttons)

        self.calculate_button.clicked.connect(self.calculate_properties)
        self.sweep_button.clicked.connect(self.calculate_sweep)
        self.set_theme_tokens(self._tokens)

    def current_request(self) -> object:
        model = import_module("osw.solvers.coolprop.model")
        return model.CoolPropPropertyRequest(
            fluid=self.fluid_combo.currentText(),
            input_pair=model.PropertyInputPair(
                "T",
                float(self.temperature_edit.text()),
                "P",
                float(self.pressure_edit.text()),
                "K",
                "Pa",
            ),
        )

    def current_sweep_request(self) -> object:
        model = import_module("osw.solvers.coolprop.model")
        base_temperature = float(self.temperature_edit.text())
        return model.CoolPropSweepRequest(
            fluid=self.fluid_combo.currentText(),
            sweep_variable="T",
            sweep_values=(
                base_temperature - 20.0,
                base_temperature - 10.0,
                base_temperature,
                base_temperature + 10.0,
                base_temperature + 20.0,
            ),
            sweep_unit="K",
            fixed_variable="P",
            fixed_value=float(self.pressure_edit.text()),
            fixed_unit="Pa",
            output_properties=("density",),
        )

    def calculate_properties(self) -> object:
        adapter = self.adapter or import_module("osw.solvers.coolprop.property_adapter")
        results = import_module("osw.solvers.coolprop.results")
        result = adapter.calculate_properties(self.current_request())
        self.last_result = result
        self._show_property_result(result)
        self._show_diagnostics(getattr(result, "diagnostics", None))
        if getattr(result, "status", "") in {"ok", "warning"}:
            self.resultDatasetReady.emit(results.coolprop_result_to_result_dataset(result))
        self.propertyCalculated.emit(result)
        return result

    def calculate_sweep(self) -> object:
        adapter = self.adapter or import_module("osw.solvers.coolprop.property_adapter")
        results = import_module("osw.solvers.coolprop.results")
        result = adapter.sweep_properties(self.current_sweep_request())
        self.last_result = result
        self._show_sweep_result(result)
        self._show_diagnostics(getattr(result, "diagnostics", None))
        if getattr(result, "status", "") in {"ok", "warning"}:
            self.resultDatasetReady.emit(results.coolprop_sweep_to_result_dataset(result))
        self.propertyCalculated.emit(result)
        return result

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswChmPropertyDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLineEdit, QComboBox, QTableWidget, QListWidget {"
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

    def _show_property_result(self, result: object) -> None:
        values = tuple(getattr(result, "values", ()) or ())
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Property", "Value", "Unit"])
        self.results_table.setRowCount(len(values))
        for row, value in enumerate(values):
            cells = (
                getattr(value, "name", ""),
                f"{getattr(value, 'value', '')}",
                getattr(value, "unit", ""),
            )
            for column, cell in enumerate(cells):
                self.results_table.setItem(row, column, QtWidgets.QTableWidgetItem(str(cell)))
        self.results_table.resizeColumnsToContents()

    def _show_sweep_result(self, result: object) -> None:
        columns = tuple(getattr(result, "columns", ()) or ())
        rows = tuple(getattr(result, "rows", ()) or ())
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


__all__ = ["ChmPropertyDialog"]

