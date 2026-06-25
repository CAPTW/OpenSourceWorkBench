from __future__ import annotations

import importlib.util
import os

import pytest
from tests.unit.test_optional_solver_plugin_manifest_gui_viewmodel import (
    duplicate_stack_report,
    invalid_bundled_report,
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


def test_accepted_rows_render_stack_source_trust_and_notice(app: object) -> None:
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report()
    )
    panel = OptionalSolverPluginManifestPanel(view_model)
    text = panel.accepted_rows_text()

    assert "project_local_stack" in text
    assert "Project Local Stack" in text
    assert "project_local" in text
    assert "reviewed_project" in text
    assert "#6" in text
    assert "project_guidance" in text
    assert "not validation evidence" in text.lower()


def test_rejected_rows_render_reason_and_suggested_fix(app: object) -> None:
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        invalid_bundled_report()
    )
    panel = OptionalSolverPluginManifestPanel(view_model)
    text = panel.rejected_rows_text()

    assert "bundled_claim_stack" in text
    assert "invalid" in text
    assert "claims a solver is bundled" in text
    assert "OSPL_BUNDLED_SOLVER_CLAIM" in text
    assert "external-solver bundling claim" in text
    assert "State that external solvers are not bundled." in text


def test_conflict_rows_render_builtin_wins_and_override_disabled(app: object) -> None:
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        duplicate_stack_report()
    )
    panel = OptionalSolverPluginManifestPanel(view_model)
    text = panel.conflict_rows_text()

    assert "gmsh" in text
    assert "builtin" in text
    assert "plugin_package" in text
    assert "Built-in manifests win by default." in text
    assert "Plugin override is disabled by default." in text
