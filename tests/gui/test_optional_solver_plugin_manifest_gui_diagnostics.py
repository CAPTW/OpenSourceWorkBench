from __future__ import annotations

import importlib.util
import os

import pytest
from tests.unit.test_optional_solver_plugin_manifest_gui_viewmodel import (
    invalid_bundled_report,
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


def test_diagnostics_render_category_severity_code_and_message(app: object) -> None:
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        invalid_bundled_report()
    )
    panel = OptionalSolverPluginManifestPanel(view_model)
    text = panel.diagnostics_text()

    assert "blocker" in text
    assert "safety" in text
    assert "OSPL_BUNDLED_SOLVER_CLAIM" in text
    assert "claims a solver is bundled" in text
    assert "bundled_claim_stack" in text
    assert "State that external solvers are not bundled." in text
