"""Solver settings section for the right properties inspector."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

SOLVER_OPTIONS = ("chtSolver", "simpleFoam", "CalculiX Static", "SU2 CFD")
TIME_SCHEME_OPTIONS = ("Steady-State", "Transient")
LINEAR_SOLVER_OPTIONS = ("GMRES", "BiCGStab", "CG")
PRECONDITIONER_OPTIONS = ("AMG", "ILU", "Jacobi")
DEMO_SOLVER_SETTINGS = {
    "Solver": "chtSolver",
    "Time Scheme": "Steady-State",
    "Linear Solver": "GMRES",
    "Preconditioner": "AMG",
    "Convergence Tol.": "1.0e-06",
    "Advanced Options": "collapsed",
}


class SolverSettingsSection(_BaseWidget):
    """Compact mock solver settings form."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswSolverSettingsSection")
        self._tokens = DARK_TOKENS

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 7, 8, 8)
        layout.setSpacing(6)
        self.header_label = QtWidgets.QLabel("SOLVER SETTINGS", self)
        self.header_label.setObjectName("oswSolverSettingsHeader")

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        self.solver_combo = self._combo("oswSolverCombo", SOLVER_OPTIONS)
        self.time_scheme_combo = self._combo("oswTimeSchemeCombo", TIME_SCHEME_OPTIONS)
        self.linear_solver_combo = self._combo("oswLinearSolverCombo", LINEAR_SOLVER_OPTIONS)
        self.preconditioner_combo = self._combo("oswPreconditionerCombo", PRECONDITIONER_OPTIONS)
        self.tolerance_edit = QtWidgets.QLineEdit(DEMO_SOLVER_SETTINGS["Convergence Tol."], self)
        self.tolerance_edit.setObjectName("oswConvergenceToleranceEdit")
        self.advanced_toggle = QtWidgets.QToolButton(self)
        self.advanced_toggle.setObjectName("oswAdvancedOptionsToggle")
        self.advanced_toggle.setText("Advanced Options collapsed")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.toggled.connect(self._update_advanced_text)

        form.addRow("Solver:", self.solver_combo)
        form.addRow("Time Scheme:", self.time_scheme_combo)
        form.addRow("Linear Solver:", self.linear_solver_combo)
        form.addRow("Preconditioner:", self.preconditioner_combo)
        form.addRow("Convergence Tol.:", self.tolerance_edit)

        layout.addWidget(self.header_label)
        layout.addLayout(form)
        layout.addWidget(self.advanced_toggle)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def solver_settings(self) -> dict[str, str]:
        return {
            "Solver": self.solver_combo.currentText(),
            "Time Scheme": self.time_scheme_combo.currentText(),
            "Linear Solver": self.linear_solver_combo.currentText(),
            "Preconditioner": self.preconditioner_combo.currentText(),
            "Convergence Tol.": self.tolerance_edit.text(),
            "Advanced Options": "expanded" if self.advanced_toggle.isChecked() else "collapsed",
        }

    def set_solver(self, name: str) -> None:
        if self.solver_combo.findText(name) < 0:
            self.solver_combo.addItem(name)
        self.solver_combo.setCurrentText(name)

    def set_time_scheme(self, name: str) -> None:
        if self.time_scheme_combo.findText(name) < 0:
            self.time_scheme_combo.addItem(name)
        self.time_scheme_combo.setCurrentText(name)

    def set_linear_solver(self, name: str) -> None:
        if self.linear_solver_combo.findText(name) < 0:
            self.linear_solver_combo.addItem(name)
        self.linear_solver_combo.setCurrentText(name)

    def set_preconditioner(self, name: str) -> None:
        if self.preconditioner_combo.findText(name) < 0:
            self.preconditioner_combo.addItem(name)
        self.preconditioner_combo.setCurrentText(name)

    def set_convergence_tolerance(self, text: str) -> None:
        self.tolerance_edit.setText(text)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswSolverSettingsSection {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel#oswSolverSettingsHeader {"
            f"color: {tokens.accent};"
            "font-weight: 800;"
            "background: transparent;"
            "border: none;"
            "}"
            "QLabel {"
            f"color: {tokens.text_secondary};"
            "background: transparent;"
            "border: none;"
            "}"
        )

    def _combo(self, object_name: str, options: tuple[str, ...]) -> object:
        combo = QtWidgets.QComboBox(self)
        combo.setObjectName(object_name)
        combo.addItems(options)
        return combo

    def _update_advanced_text(self, expanded: bool) -> None:
        state = "expanded" if expanded else "collapsed"
        self.advanced_toggle.setText(f"Advanced Options {state}")
