"""Boundary conditions table section for the right inspector."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

BOUNDARY_CONDITION_COLUMNS = ("Name", "Type", "Value")
DEMO_BOUNDARY_ROWS = (
    ("inlet", "Velocity Inlet", "3.0 m/s"),
    ("outlet", "Pressure Outlet", "0 Pa"),
    ("wall_heatsink", "Wall (No Slip)", "—"),
    ("base_bottom", "Heat Flux", "1.0e5 W/m²"),
    ("symmetry", "Symmetry", "—"),
)


class BoundaryConditionsSection(_BaseWidget):
    """Compact boundary condition table with safe placeholder actions."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswBoundaryConditionsSection")
        self._tokens = DARK_TOKENS
        self.last_action: str | None = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 7, 8, 8)
        layout.setSpacing(6)
        self.header_label = QtWidgets.QLabel("BOUNDARY CONDITIONS", self)
        self.header_label.setObjectName("oswBoundaryConditionsHeader")

        self.table = QtWidgets.QTableWidget(self)
        self.table.setObjectName("oswBoundaryConditionsTable")
        self.table.setColumnCount(len(BOUNDARY_CONDITION_COLUMNS))
        self.table.setHorizontalHeaderLabels(BOUNDARY_CONDITION_COLUMNS)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setMinimumHeight(142)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

        self.add_button = self._action_button("Add", "oswBoundaryAddButton")
        self.edit_button = self._action_button("Edit", "oswBoundaryEditButton")
        self.copy_button = self._action_button("Copy", "oswBoundaryCopyButton")
        self.remove_button = self._action_button("Remove", "oswBoundaryRemoveButton")
        button_row = QtWidgets.QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(5)
        for button in self.action_buttons():
            button_row.addWidget(button)

        layout.addWidget(self.header_label)
        layout.addWidget(self.table)
        layout.addLayout(button_row)
        self.reset_demo_boundaries()
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def column_labels(self) -> list[str]:
        return [
            self.table.horizontalHeaderItem(index).text()
            for index in range(self.table.columnCount())
        ]

    def boundary_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for row_index in range(self.table.rowCount()):
            rows.append(
                {
                    column: self.table.item(row_index, column_index).text()
                    for column_index, column in enumerate(BOUNDARY_CONDITION_COLUMNS)
                }
            )
        return rows

    def action_buttons(self) -> list[object]:
        return [self.add_button, self.edit_button, self.copy_button, self.remove_button]

    def add_boundary_row(self, row: tuple[str, str, str] | dict[str, str]) -> None:
        if isinstance(row, dict):
            values = tuple(row[column] for column in BOUNDARY_CONDITION_COLUMNS)
        else:
            values = row
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        for column_index, value in enumerate(values):
            item = QtWidgets.QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_index, column_index, item)
        self.table.setRowHeight(row_index, 23)

    def remove_selected_boundary_row(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if selected:
            self.table.removeRow(selected[0].row())
        self.last_action = "Remove"

    def reset_demo_boundaries(self) -> None:
        self.table.setRowCount(0)
        for row in DEMO_BOUNDARY_ROWS:
            self.add_boundary_row(row)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswBoundaryConditionsSection {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel#oswBoundaryConditionsHeader {"
            f"color: {tokens.accent};"
            "font-weight: 800;"
            "background: transparent;"
            "border: none;"
            "}"
            "QTableWidget#oswBoundaryConditionsTable {"
            f"background-color: {tokens.bg_panel};"
            f"alternate-background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"gridline-color: {tokens.border};"
            f"border: 1px solid {tokens.border};"
            "font-size: 8pt;"
            "}"
            "QHeaderView::section {"
            f"background-color: {tokens.bg_header};"
            f"color: {tokens.text_secondary};"
            f"border: 1px solid {tokens.border};"
            "padding: 3px 4px;"
            "}"
        )

    def _action_button(self, text: str, object_name: str) -> object:
        button = QtWidgets.QPushButton(text, self)
        button.setObjectName(object_name)
        if text == "Remove":
            button.clicked.connect(self.remove_selected_boundary_row)
        else:
            button.clicked.connect(lambda _checked=False, label=text: self._record_action(label))
        return button

    def _record_action(self, label: str) -> None:
        self.last_action = label
