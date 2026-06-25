from __future__ import annotations

import importlib.util
import os

import pytest
from tests.unit.test_optional_solver_plugin_manifest_gui_viewmodel import (
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


def project_view_model():
    return build_optional_solver_plugin_manifest_gui_viewmodel(valid_project_report())


def test_panel_constructs_with_supplied_view_model(app: object) -> None:
    from osw.gui.dialogs import OptionalSolverPluginManifestPanel as PackagePanel
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    panel = OptionalSolverPluginManifestPanel(project_view_model())

    assert PackagePanel is OptionalSolverPluginManifestPanel
    assert panel.objectName() == "oswOptionalSolverPluginManifestPanel"
    assert panel.windowTitle() == "Optional Solver Plugin Manifest Preview"
    assert panel.tabs.objectName() == "oswOptionalSolverPluginManifestTabs"


def test_summary_renders_counts(app: object) -> None:
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    panel = OptionalSolverPluginManifestPanel(project_view_model())
    text = panel.summary_text()

    assert "accepted=1" in text
    assert "rejected=0" in text
    assert "conflicts=0" in text
    assert "diagnostics=0" in text
    assert "not validation evidence" in text.lower()


def test_action_footer_marks_unsafe_actions_unavailable(app: object) -> None:
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    panel = OptionalSolverPluginManifestPanel(project_view_model())
    actions = panel.action_state_text()
    reasons = panel.disabled_action_reasons()

    assert "choose_explicit_json_files: available; disabled; future" in actions
    assert "activate_manifest: unavailable; disabled; future" in actions
    assert "run_discovery_with_plugin_manifests: unavailable" in actions
    assert "run_validation: unavailable" in actions
    assert "install_solver: unavailable" in actions
    assert "close_issue: unavailable" in actions
    assert "separate future gate" in reasons["activate_manifest"].lower()
    assert "OSW-VALID gate" in reasons["run_validation"]
    assert "closure gate" in reasons["close_issue"].lower()
    assert panel.available_action_names() == ("choose_explicit_json_files",)
