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


def test_plugin_health_dashboard_displays_status_lines(app: object) -> None:
    from osw.gui.plugin_manager_dialog import PluginManagerDialog, PluginManagerEntry

    dialog = PluginManagerDialog(
        entries=[
            PluginManagerEntry(
                plugin_id="demo.solver",
                display_name="Demo Solver",
                version="0.1.0",
                plugin_type="solver_adapter",
                domain="solver",
                enabled=True,
                valid=True,
                health_status="warning",
                health_messages=("Optional dependency is missing: meshio",),
                missing_executable_warnings=("Executable not configured or found: ccx.",),
                sample_project_reference="examples/04_calculix_cantilever",
                last_health_check_status="checked",
                last_run_status="not-run",
                manifest_text='{"id": "demo.solver"}',
            )
        ]
    )

    text = dialog.health_dashboard.toPlainText()

    assert dialog.health_dashboard.objectName() == "pluginHealthDashboard"
    assert "Plugin status: warning" in text
    assert "Optional dependency is missing: meshio" in text
    assert "Executable not configured or found: ccx." in text
    assert "examples/04_calculix_cantilever" in text
    assert "Last run: not-run" in text

    del app
