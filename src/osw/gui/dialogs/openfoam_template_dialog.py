"""Theme-aware OpenFOAM template generation and run handoff dialog."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class OpenFOAMTemplateDialog(_BaseDialog):
    """Generate bounded OpenFOAM templates without launching OpenFOAM solvers."""

    if QtCore is not None:
        caseGenerated = QtCore.Signal(object)
        openfoamRunCompleted = QtCore.Signal(object)

    def __init__(
        self,
        parent: object | None = None,
        *,
        runner: object | None = None,
        theme_tokens: ThemeTokens | None = None,
        output_dir: str | Path = Path("artifacts") / "openfoam",
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswOpenFOAMTemplateDialog")
        self.setWindowTitle("Generate OpenFOAM Template Case")
        self.resize(900, 680)
        self._tokens = theme_tokens or DARK_TOKENS
        self.runner = runner
        self.output_dir = Path(output_dir)
        self.case_result: object | None = None
        self.run_result: object | None = None

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        self.template_kind_combo = QtWidgets.QComboBox(self)
        self.template_kind_combo.setObjectName("oswOpenFOAMTemplateKindCombo")
        self.template_kind_combo.addItems(["cavity", "duct"])
        form.addRow("Template", self.template_kind_combo)

        self.solver_combo = QtWidgets.QComboBox(self)
        self.solver_combo.setObjectName("oswOpenFOAMSolverCombo")
        self.solver_combo.addItems(["icoFoam", "simpleFoam"])
        form.addRow("Solver", self.solver_combo)

        self.case_name_edit = QtWidgets.QLineEdit("cavity", self)
        self.case_name_edit.setObjectName("oswOpenFOAMCaseNameEdit")
        form.addRow("Case", self.case_name_edit)

        self.inlet_velocity_edit = QtWidgets.QLineEdit("1.0", self)
        self.inlet_velocity_edit.setObjectName("oswOpenFOAMInletVelocityEdit")
        form.addRow("Inlet Ux", self.inlet_velocity_edit)

        self.outlet_pressure_edit = QtWidgets.QLineEdit("0.0", self)
        self.outlet_pressure_edit.setObjectName("oswOpenFOAMOutletPressureEdit")
        form.addRow("Outlet p", self.outlet_pressure_edit)

        self.case_summary = QtWidgets.QPlainTextEdit(self)
        self.case_summary.setObjectName("oswOpenFOAMCaseSummary")
        self.case_summary.setReadOnly(True)
        layout.addWidget(self.case_summary, 1)

        self.residual_summary = QtWidgets.QPlainTextEdit(self)
        self.residual_summary.setObjectName("oswOpenFOAMResidualSummary")
        self.residual_summary.setReadOnly(True)
        self.residual_summary.setMaximumHeight(120)
        layout.addWidget(self.residual_summary)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswOpenFOAMDiagnosticsList")
        layout.addWidget(self.diagnostics_list)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.generate_case_button = QtWidgets.QPushButton("Generate Case", self)
        self.generate_case_button.setObjectName("oswOpenFOAMGenerateCaseButton")
        self.run_button = QtWidgets.QPushButton("Prepare Run Handoff", self)
        self.run_button.setObjectName("oswOpenFOAMRunButton")
        buttons.addWidget(self.generate_case_button)
        buttons.addWidget(self.run_button)
        layout.addLayout(buttons)

        self.template_kind_combo.currentTextChanged.connect(self._sync_template_defaults)
        self.generate_case_button.clicked.connect(self.generate_case)
        self.run_button.clicked.connect(self.prepare_run_handoff)
        self.set_theme_tokens(self._tokens)
        self._sync_template_defaults(self.template_kind_combo.currentText())

    def current_request(self) -> object:
        case_generator = import_module("osw.solvers.openfoam.case_generator")
        template = self.template_kind_combo.currentText()
        if template == "duct":
            request = case_generator.default_duct_request(
                self.output_dir,
                inlet_velocity=float(self.inlet_velocity_edit.text()),
                outlet_pressure=float(self.outlet_pressure_edit.text()),
            )
        else:
            request = case_generator.default_cavity_request(self.output_dir)
        return request.__class__(
            template_kind=request.template_kind,
            solver=self.solver_combo.currentText(),
            case_name=self.case_name_edit.text() or request.case_name,
            output_dir=request.output_dir,
            dimensions=request.dimensions,
            mesh_settings=request.mesh_settings,
            boundaries=request.boundaries,
            transport=request.transport,
            control=request.control,
            metadata=request.metadata,
        )

    def generate_case(self) -> object:
        case_generator = import_module("osw.solvers.openfoam.case_generator")
        self.diagnostics_list.clear()
        result = case_generator.generate_openfoam_case(self.current_request())
        self.case_result = result
        lines = [
            f"Status: {getattr(result, 'status', '')}",
            f"Case directory: {getattr(result, 'case_dir', '')}",
        ]
        for path in getattr(result, "generated_files", ()) or ():
            try:
                relative = Path(path).relative_to(getattr(result, "case_dir", Path(path).parent))
            except ValueError:
                relative = Path(path)
            lines.append(f"- {relative}")
        self.case_summary.setPlainText("\n".join(lines))
        self._show_diagnostics(getattr(result, "diagnostics", None))
        self.caseGenerated.emit(result)
        return result

    def prepare_run_handoff(self) -> object | None:
        """Prepare an OpenFOAM case handoff without running OpenFOAM commands."""

        if self.case_result is None:
            self.generate_case()
        if self.case_result is None:
            return None
        lines = [
            "OpenFOAM run handoff prepared.",
            f"Case directory: {getattr(self.case_result, 'case_dir', '')}",
            f"Solver preview: {self.solver_combo.currentText()}",
            "GUI did not run blockMesh, icoFoam, simpleFoam, or OpenFOAM wrappers.",
        ]
        self.residual_summary.setPlainText("\n".join(lines))
        self._show_diagnostics(getattr(self.case_result, "diagnostics", None))
        self.diagnostics_list.addItem(
            "INFO runner-boundary: external OpenFOAM execution requires an "
            "explicit backend run gate."
        )
        return self.case_result

    def run_openfoam(self) -> object | None:
        """Compatibility entry point; prepares a handoff and does not run OpenFOAM."""

        return self.prepare_run_handoff()

    def set_run_result(self, result: object) -> None:
        self.run_result = result
        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        summary = getattr(result, "residual_summary", None)
        lines = [f"Run status: {status}"]
        if summary is not None:
            lines.append(f"Iterations: {getattr(summary, 'iteration_count', 0)}")
            for field, value in sorted(dict(getattr(summary, "final_residuals", {})).items()):
                lines.append(f"{field}: {float(value):.6g}")
        self.residual_summary.setPlainText("\n".join(lines))
        self._show_diagnostics(getattr(result, "diagnostics", None))

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswOpenFOAMTemplateDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLineEdit, QComboBox, QPlainTextEdit, QListWidget {"
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

    def _show_diagnostics(self, diagnostics: object | None) -> None:
        self.diagnostics_list.clear()
        messages = getattr(diagnostics, "messages", ()) if diagnostics is not None else ()
        for message in messages:
            severity = str(getattr(getattr(message, "severity", ""), "value", ""))
            code = str(getattr(message, "code", ""))
            text = str(getattr(message, "message", ""))
            self.diagnostics_list.addItem(f"{severity.upper()} {code}: {text}")

    def _sync_template_defaults(self, template: str) -> None:
        if template == "duct":
            self.case_name_edit.setText("duct")
            self.solver_combo.setCurrentText("simpleFoam")
            return
        self.case_name_edit.setText("cavity")
        self.solver_combo.setCurrentText("icoFoam")
