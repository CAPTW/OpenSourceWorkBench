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


def test_report_export_dialog_instantiates(app: object) -> None:
    from osw.gui.dialogs.report_export_dialog import ReportExportDialog

    dialog = ReportExportDialog(default_path="artifacts/report/demo.html")

    assert dialog.objectName() == "oswReportExportDialog"
    assert dialog.path_edit.objectName() == "oswReportExportPathEdit"
    assert dialog.format_combo.objectName() == "oswReportExportFormatCombo"
    assert dialog.export_button.objectName() == "oswReportExportConfirmButton"
    assert dialog.cancel_button.objectName() == "oswReportExportCancelButton"
    assert dialog.selected_path().endswith("demo.html")
    assert dialog.selected_format() == "html"


def test_report_export_dialog_applies_themes(app: object) -> None:
    from osw.gui.dialogs.report_export_dialog import ReportExportDialog
    from osw.gui.theme import ThemeManager

    dialog = ReportExportDialog()
    manager = ThemeManager(auto_load=False)

    manager.set_mode("dark", save=False)
    dialog.set_theme_tokens(manager.current_tokens)
    manager.set_mode("light", save=False)
    dialog.set_theme_tokens(manager.current_tokens)

    assert dialog._tokens is manager.current_tokens
