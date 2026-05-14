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


def test_plugin_manager_dialog_shows_entries(app: object) -> None:
    from osw.gui.plugin_manager_dialog import PluginManagerDialog, PluginManagerEntry

    dialog = PluginManagerDialog(
        entries=[
            PluginManagerEntry(
                plugin_id="demo.mesh",
                display_name="Demo Mesh Importer",
                version="0.1.0",
                plugin_type="mesh_importer",
                domain="mesh",
                enabled=True,
                valid=True,
                health_status="ok",
                manifest_text='{"id": "demo.mesh"}',
            )
        ]
    )

    assert dialog.plugin_table.rowCount() == 1
    assert dialog.plugin_table.item(0, 1).text() == "demo.mesh"
    assert "demo.mesh" in dialog.manifest_viewer.toPlainText()
    assert dialog.install_folder_button.objectName() == "pluginInstallFolderButton"
    assert dialog.install_zip_button.objectName() == "pluginInstallZipButton"

    del app
