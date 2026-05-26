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

FIXTURES = Path(__file__).parents[1] / "fixtures" / "plugins"


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_plugins_section_uses_demo_rows_without_registry(app: object) -> None:
    from osw.gui.widgets.plugins_section import PluginsSection

    section = PluginsSection()

    rows = section.plugin_rows()
    assert rows[0]["name"] == "Octave / MATLAB Interface"
    assert section.manage_report_button.text() == "Manage Report..."
    assert section.status_labels["Report Generator"].text() == "Enabled"

    del app


def test_plugins_section_displays_registry_rows(app: object) -> None:
    from osw.gui.widgets.plugins_section import PluginsSection
    from osw.plugins.discovery import discover_local_plugin_manifests
    from osw.plugins.health import build_plugin_health_record

    result = discover_local_plugin_manifests(FIXTURES / "valid_calculix")
    registry = result.to_registry()
    health = {
        manifest.id: build_plugin_health_record(manifest)
        for manifest in registry.values()
    }
    section = PluginsSection()

    section.set_plugin_registry(registry)
    section.set_plugin_health_map(health)

    rows = section.plugin_rows()
    assert rows == [
        {
            "name": "CalculiX Adapter",
            "plugin_id": "osw.calculix",
            "enabled": True,
            "status": "warning",
        }
    ]
    assert "CalculiX Adapter" in section.status_labels
    assert "Enabled" in section.status_labels["CalculiX Adapter"].text()

    del app


def test_manage_plugins_button_emits_safe_signal(app: object) -> None:
    from osw.gui.widgets.plugins_section import PluginsSection

    section = PluginsSection()
    requested: list[bool] = []
    section.manage_plugins_requested.connect(lambda: requested.append(True))

    section.manage_report_button.click()

    assert section.last_manage_report_request == "plugin-manager"
    assert requested == [True]

    del app
