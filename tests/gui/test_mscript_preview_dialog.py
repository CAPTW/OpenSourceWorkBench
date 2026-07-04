from __future__ import annotations

import importlib.util
import os
from pathlib import Path

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

FIXTURES = Path(__file__).parents[1] / "fixtures" / "mscript"


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_script_preview_dialog_displays_preview_regions(app: object) -> None:
    from osw.gui.dialogs.script_preview_dialog import ScriptPreviewDialog
    from osw.scripts.mscript.importer import preview_mscript

    result = preview_mscript(FIXTURES / "function_basic.m")
    assert result.preview is not None

    dialog = ScriptPreviewDialog(result.preview)

    assert dialog.objectName() == "oswScriptPreviewDialog"
    assert dialog.preview_panel.objectName() == "oswScriptPreviewPanel"
    assert dialog.preview_panel.source_path_label.objectName() == "oswScriptPreviewSourcePath"
    assert dialog.preview_panel.kind_label.objectName() == "oswScriptPreviewKindLabel"
    assert dialog.preview_panel.signature_label.objectName() == "oswScriptPreviewSignatureLabel"
    assert dialog.preview_panel.help_text.objectName() == "oswScriptPreviewHelpText"
    assert dialog.preview_panel.code_text.objectName() == "oswScriptPreviewCodeText"
    assert dialog.preview_panel.safety_table.objectName() == "oswScriptSafetyFindingsTable"
    assert dialog.preview_panel.plot_table.objectName() == "oswScriptPlotHintsTable"
    assert dialog.preview_panel.import_button.objectName() == "oswScriptPreviewImportButton"
    assert dialog.preview_panel.cancel_button.objectName() == "oswScriptPreviewCancelButton"
    assert "function_basic.m" in dialog.preview_panel.source_path_label.text()
    assert dialog.preview_panel.kind_label.text() == "function"
    assert "function y = function_basic(x)" in dialog.preview_panel.signature_label.text()
    assert "Return a doubled value" in dialog.preview_panel.help_text.toPlainText()
    assert "function y = function_basic(x)" in dialog.preview_panel.code_text.toPlainText()
    assert dialog.preview_panel.import_button.isEnabled()
    assert dialog.preview_panel.run_button.objectName() == "oswScriptRunWithOctaveButton"
    assert dialog.preview_panel.run_status_label.objectName() == "oswScriptRunStatusLabel"
    assert dialog.preview_panel.run_log_preview.objectName() == "oswScriptRunLogPreview"
    assert (
        dialog.preview_panel.run_diagnostics_table.objectName()
        == "oswScriptRunDiagnosticsTable"
    )
    assert dialog.preview_panel.run_button.isEnabled()

    del app


def test_script_preview_dialog_surfaces_safety_and_plot_hints(app: object) -> None:
    from osw.gui.dialogs.script_preview_dialog import ScriptPreviewDialog
    from osw.scripts.mscript.importer import preview_mscript

    dangerous = preview_mscript(FIXTURES / "dangerous_system.m").preview
    plot = preview_mscript(FIXTURES / "simple_plot.m").preview
    assert dangerous is not None
    assert plot is not None

    safety_dialog = ScriptPreviewDialog(dangerous)
    plot_dialog = ScriptPreviewDialog(plot)

    assert safety_dialog.preview_panel.safety_table.rowCount() >= 4
    assert safety_dialog.preview_panel.safety_table.item(0, 0).text() == "high"
    assert not safety_dialog.preview_panel.run_button.isEnabled()
    assert "run handoff blocked" in safety_dialog.preview_panel.run_status_label.text().lower()
    assert plot_dialog.preview_panel.plot_table.rowCount() >= 4
    commands = {
        plot_dialog.preview_panel.plot_table.item(row, 0).text()
        for row in range(plot_dialog.preview_panel.plot_table.rowCount())
    }
    assert {"figure", "plot", "title"}.issubset(commands)

    del app


def test_script_preview_dialog_prepares_octave_handoff_without_runner(app: object) -> None:
    from osw.gui.dialogs.script_preview_dialog import ScriptPreviewDialog
    from osw.scripts.mscript.importer import preview_mscript

    class FakeRunner:
        def __init__(self) -> None:
            self.called = False

        def run(self, request: object) -> object:
            del request
            self.called = True
            return object()

    result = preview_mscript(FIXTURES / "simple_plot.m")
    assert result.preview is not None
    dialog = ScriptPreviewDialog(result.preview)
    runner = FakeRunner()
    dialog.set_octave_runner(runner)

    run_result = dialog.run_previewed_script_with_octave()

    assert runner.called is False
    assert run_result is result.preview
    assert "did not run GNU Octave" in dialog.preview_panel.run_status_label.text()
    assert "explicit backend/service run gate" in dialog.preview_panel.run_log_preview.toPlainText()
    assert dialog.current_figure_dataset() is None
    assert dialog.preview_panel.open_figures_button.objectName() == "oswOpenFigureDatasetButton"
    del app


def test_script_preview_dialog_accepts_theme_updates(app: object) -> None:
    from osw.gui.dialogs.script_preview_dialog import ScriptPreviewDialog
    from osw.gui.theme_tokens import get_theme_tokens
    from osw.scripts.mscript.importer import preview_mscript

    result = preview_mscript(FIXTURES / "simple_plot.m")
    assert result.preview is not None
    dialog = ScriptPreviewDialog(result.preview)

    dialog.set_theme_tokens(get_theme_tokens("dark"))
    dialog.set_theme_tokens(get_theme_tokens("light"))

    assert dialog.current_preview() is result.preview
    del app
