"""Theme-aware BoundaryCurve preview panel."""

from __future__ import annotations

from typing import Any

from osw.core.boundary_curve import BoundaryCurve, BoundaryCurveKind, CurveInterpolation
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class BoundaryCurvePanel(_BaseWidget):
    """Read-only curve metadata, preview, and validation diagnostics surface."""

    if QtCore is not None:
        createRequested = QtCore.Signal(object)
        cancelRequested = QtCore.Signal()

    def __init__(
        self,
        curve: BoundaryCurve | None = None,
        parent: object | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswBoundaryCurvePanel")
        self._tokens = DARK_TOKENS
        self._curve: BoundaryCurve | None = None
        self._build_layout()
        self.set_theme_tokens(self._tokens)
        if curve is not None:
            self.set_curve(curve)

    def current_curve(self) -> BoundaryCurve | None:
        return self._curve

    def set_curve(self, curve: BoundaryCurve) -> None:
        self._curve = curve
        self.name_edit.setText(curve.name)
        self.kind_combo.setCurrentText(curve.kind)
        self.x_unit_edit.setText(curve.x_unit)
        self.y_unit_edit.setText(curve.y_unit)
        self.interpolation_combo.setCurrentText(curve.interpolation)
        self._populate_preview(curve)
        self._populate_diagnostics(curve)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswBoundaryCurvePanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel[oswCurveMeta='true'] {"
            f"color: {tokens.text_secondary};"
            "font-weight: 600;"
            "}"
            "QLineEdit, QComboBox, QTableWidget, QListWidget {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "}"
            "QPushButton {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "padding: 5px 8px;"
            "border-radius: 3px;"
            "}"
        )

    def _build_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        meta_grid = QtWidgets.QGridLayout()
        self.name_edit = QtWidgets.QLineEdit(self)
        self.name_edit.setObjectName("oswBoundaryCurveNameEdit")
        self.kind_combo = QtWidgets.QComboBox(self)
        self.kind_combo.setObjectName("oswBoundaryCurveKindCombo")
        self.kind_combo.addItems([kind.value for kind in BoundaryCurveKind])
        self.x_unit_edit = QtWidgets.QLineEdit(self)
        self.x_unit_edit.setObjectName("oswBoundaryCurveXAxisUnitEdit")
        self.y_unit_edit = QtWidgets.QLineEdit(self)
        self.y_unit_edit.setObjectName("oswBoundaryCurveYAxisUnitEdit")
        self.interpolation_combo = QtWidgets.QComboBox(self)
        self.interpolation_combo.setObjectName("oswBoundaryCurveInterpolationCombo")
        self.interpolation_combo.addItems([item.value for item in CurveInterpolation])
        for row, (label, widget) in enumerate(
            (
                ("Name", self.name_edit),
                ("Kind", self.kind_combo),
                ("X unit", self.x_unit_edit),
                ("Y unit", self.y_unit_edit),
                ("Interpolation", self.interpolation_combo),
            )
        ):
            meta_label = QtWidgets.QLabel(label, self)
            meta_label.setProperty("oswCurveMeta", True)
            meta_grid.addWidget(meta_label, row, 0)
            meta_grid.addWidget(widget, row, 1)
        layout.addLayout(meta_grid)

        self.preview_table = QtWidgets.QTableWidget(self)
        self.preview_table.setObjectName("oswBoundaryCurvePreviewTable")
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["x", "y"])
        self.preview_table.setMinimumHeight(220)
        layout.addWidget(self.preview_table, 1)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswBoundaryCurveDiagnosticsList")
        self.diagnostics_list.setMaximumHeight(120)
        layout.addWidget(self.diagnostics_list)

        button_row = QtWidgets.QHBoxLayout()
        self.create_button = QtWidgets.QPushButton("Create", self)
        self.create_button.setObjectName("oswBoundaryCurveCreateButton")
        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.setObjectName("oswBoundaryCurveCancelButton")
        button_row.addStretch(1)
        button_row.addWidget(self.create_button)
        button_row.addWidget(self.cancel_button)
        layout.addLayout(button_row)
        self.create_button.clicked.connect(lambda: self.createRequested.emit(self._curve))
        self.cancel_button.clicked.connect(self.cancelRequested.emit)

    def _populate_preview(self, curve: BoundaryCurve) -> None:
        rows = curve.preview_rows(max_rows=50)
        self.preview_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.preview_table.setItem(row_index, 0, _readonly_item(row["x"]))
            self.preview_table.setItem(row_index, 1, _readonly_item(row["y"]))
        self.preview_table.resizeColumnsToContents()

    def _populate_diagnostics(self, curve: BoundaryCurve) -> None:
        self.diagnostics_list.clear()
        report = curve.validate()
        for message in report.messages:
            self.diagnostics_list.addItem(
                f"{message.severity.upper()} {message.path}: {message.message}"
            )
        if not report.messages:
            self.diagnostics_list.addItem("No validation messages.")


def _readonly_item(value: object) -> object:
    item = QtWidgets.QTableWidgetItem(str(value))
    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
    return item
