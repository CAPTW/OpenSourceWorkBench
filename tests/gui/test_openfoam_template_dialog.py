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


class FakeOpenFOAMRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, str]] = []

    def run_case(self, case_dir: Path, solver: str, policy: object) -> object:
        del policy
        from osw.core.diagnostics import DiagnosticReport
        from osw.solvers.openfoam.model import (
            OpenFOAMResidualSeries,
            OpenFOAMResidualSummary,
            OpenFOAMRunResult,
            OpenFOAMRunStatus,
        )

        self.calls.append((Path(case_dir), solver))
        report = DiagnosticReport()
        report.add_info("openfoam-run-completed", "OpenFOAM solver run completed.")
        return OpenFOAMRunResult(
            run_id="fake",
            status=OpenFOAMRunStatus.COMPLETED,
            case_dir=Path(case_dir),
            solver=solver,
            stdout="fake openfoam stdout",
            residual_summary=OpenFOAMResidualSummary(
                series=(OpenFOAMResidualSeries("Ux", (0.01,), (1,)),),
                final_residuals={"Ux": 0.01},
                initial_residuals={"Ux": 0.1},
                iteration_count=1,
            ),
            diagnostics=report,
        )


def test_openfoam_template_dialog_object_names(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.openfoam_template_dialog import OpenFOAMTemplateDialog

    dialog = OpenFOAMTemplateDialog(runner=FakeOpenFOAMRunner(), output_dir=tmp_path)

    assert dialog.objectName() == "oswOpenFOAMTemplateDialog"
    assert dialog.template_kind_combo.objectName() == "oswOpenFOAMTemplateKindCombo"
    assert dialog.solver_combo.objectName() == "oswOpenFOAMSolverCombo"
    assert dialog.case_name_edit.objectName() == "oswOpenFOAMCaseNameEdit"
    assert dialog.inlet_velocity_edit.objectName() == "oswOpenFOAMInletVelocityEdit"
    assert dialog.outlet_pressure_edit.objectName() == "oswOpenFOAMOutletPressureEdit"
    assert dialog.generate_case_button.objectName() == "oswOpenFOAMGenerateCaseButton"
    assert dialog.run_button.objectName() == "oswOpenFOAMRunButton"
    assert dialog.diagnostics_list.objectName() == "oswOpenFOAMDiagnosticsList"
    assert dialog.case_summary.objectName() == "oswOpenFOAMCaseSummary"
    assert dialog.residual_summary.objectName() == "oswOpenFOAMResidualSummary"


def test_openfoam_template_dialog_generates_case_without_openfoam(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.openfoam_template_dialog import OpenFOAMTemplateDialog

    dialog = OpenFOAMTemplateDialog(runner=FakeOpenFOAMRunner(), output_dir=tmp_path)
    result = dialog.generate_case()

    assert result.status == "ok"
    assert (Path(result.case_dir) / "system" / "controlDict").exists()
    assert "Case directory" in dialog.case_summary.toPlainText()


def test_openfoam_template_dialog_run_uses_injected_runner(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.openfoam_template_dialog import OpenFOAMTemplateDialog

    runner = FakeOpenFOAMRunner()
    dialog = OpenFOAMTemplateDialog(runner=runner, output_dir=tmp_path)

    result = dialog.run_openfoam()

    assert runner.calls
    assert result is not None
    assert "Run status: completed" in dialog.residual_summary.toPlainText()
    assert "Ux: 0.01" in dialog.residual_summary.toPlainText()


def test_openfoam_template_dialog_theme_switching(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.openfoam_template_dialog import OpenFOAMTemplateDialog
    from osw.gui.theme_tokens import get_theme_tokens

    dialog = OpenFOAMTemplateDialog(runner=FakeOpenFOAMRunner(), output_dir=tmp_path)

    dialog.set_theme_tokens(get_theme_tokens("dark"))
    dialog.set_theme_tokens(get_theme_tokens("light"))
    assert dialog.styleSheet()
