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


def test_calculix_deck_dialog_object_names(app: object) -> None:
    from osw.gui.dialogs.calculix_deck_dialog import CalculixDeckDialog
    from osw.solvers.calculix.adapter import create_calculix_deck

    dialog = CalculixDeckDialog(result=create_calculix_deck(options={"demo": "cantilever"}))

    assert dialog.objectName() == "oswCalculixDeckDialog"
    assert dialog.deck_preview.objectName() == "oswCalculixDeckPreview"
    assert dialog.diagnostics_list.objectName() == "oswCalculixReadinessDiagnostics"
    assert dialog.write_deck_button.objectName() == "oswCalculixWriteDeckButton"
    assert dialog.run_button.objectName() == "oswCalculixRunButton"
    assert dialog.run_status_label.objectName() == "oswCalculixRunStatusLabel"
    assert dialog.case_dir_label.objectName() == "oswCalculixCaseDirLabel"
    assert dialog.run_log_preview.objectName() == "oswCalculixRunLogPreview"
    assert dialog.run_artifacts_list.objectName() == "oswCalculixRunArtifactsList"
    assert dialog.run_diagnostics_list.objectName() == "oswCalculixRunDiagnosticsList"
    assert dialog.close_button.objectName() == "oswCalculixCloseButton"
    assert "*HEADING" in dialog.deck_preview.toPlainText()


def test_calculix_deck_dialog_writes_deck_without_ccx(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.calculix_deck_dialog import CalculixDeckDialog
    from osw.solvers.calculix.adapter import create_calculix_deck

    output_path = tmp_path / "cantilever.inp"
    dialog = CalculixDeckDialog(
        result=create_calculix_deck(options={"demo": "cantilever"}),
        output_path=output_path,
    )
    written = dialog.write_deck()

    assert written == output_path
    assert output_path.exists()
    assert "*CLOAD" in output_path.read_text(encoding="utf-8")


def test_calculix_deck_dialog_run_hook_uses_injected_runner(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.core.artifacts import RunArtifact
    from osw.core.diagnostics import DiagnosticReport
    from osw.gui.dialogs.calculix_deck_dialog import CalculixDeckDialog
    from osw.solvers.calculix.adapter import create_calculix_deck
    from osw.solvers.calculix.runner import CalculiXRunResult, CalculiXRunStatus

    class FakeRunner:
        def __init__(self) -> None:
            self.called = False

        def run_input_deck(self, path: Path, **kwargs: object) -> CalculiXRunResult:
            del kwargs
            self.called = True
            assert Path(path).exists()
            report = DiagnosticReport()
            report.add_info("ccx-run-completed", "CalculiX ccx run completed.")
            return CalculiXRunResult(
                run_id="fake",
                status=CalculiXRunStatus.COMPLETED,
                input_deck_path=Path(path),
                case_dir=tmp_path / "case",
                job_name="cantilever",
                command=("fake-ccx", "cantilever"),
                return_code=0,
                stdout="fake stdout",
                stderr="",
                combined_log="fake stdout",
                artifacts=(
                    RunArtifact(
                        tmp_path / "case" / "cantilever.inp",
                        "input_deck",
                        "Input deck.",
                        exists=True,
                    ),
                ),
                diagnostics=report,
            )

    runner = FakeRunner()
    dialog = CalculixDeckDialog(
        result=create_calculix_deck(options={"demo": "cantilever"}),
        output_path=tmp_path / "cantilever.inp",
        runner=runner,
    )

    result = dialog.run_calculix()

    assert runner.called
    assert result is not None
    assert "completed" in dialog.run_status_label.text()
    assert "fake stdout" in dialog.run_log_preview.toPlainText()
    assert dialog.run_artifacts_list.count() == 1
    assert dialog.run_diagnostics_list.count() == 1


def test_calculix_deck_dialog_theme_switching(app: object) -> None:
    from osw.gui.dialogs.calculix_deck_dialog import CalculixDeckDialog
    from osw.gui.theme_tokens import get_theme_tokens
    from osw.solvers.calculix.adapter import create_calculix_deck

    dialog = CalculixDeckDialog(result=create_calculix_deck(options={"demo": "cantilever"}))

    dialog.set_theme_tokens(get_theme_tokens("dark"))
    dialog.set_theme_tokens(get_theme_tokens("light"))
    assert dialog.styleSheet()
