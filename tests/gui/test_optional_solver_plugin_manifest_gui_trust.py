from __future__ import annotations

import importlib.util
import os

import pytest
from tests.unit.test_optional_solver_plugin_manifest_gui_viewmodel import (
    third_party_report,
    valid_project_report,
)

from osw.experimental.optional_solvers import (
    build_optional_solver_plugin_manifest_gui_viewmodel,
)

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


def test_trust_panel_renders_third_party_warning(app: object) -> None:
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(third_party_report())
    panel = OptionalSolverPluginManifestPanel(view_model)
    text = panel.trust_text()

    assert "third_party_plugin" in text
    assert "Third-party/plugin manifests are not trusted by default." in text
    assert "Trust label is not certification." in text


def test_safety_panel_renders_policy_boundaries(app: object) -> None:
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report()
    )
    panel = OptionalSolverPluginManifestPanel(view_model)
    text = panel.safety_text()

    assert "Plugin manifest preview is not validation evidence." in text
    assert "No file dialog." in text
    assert "No file loading." in text
    assert "No plugin code execution." in text
    assert "No plugin package import." in text
    assert "No directory scan." in text
    assert "No network fetch." in text
    assert "No discovery execution." in text
    assert "No solver execution." in text
    assert "No dependency installation." in text
    assert "No install action." in text
    assert "No issue closure action." in text
    assert "External solvers are not bundled." in text
