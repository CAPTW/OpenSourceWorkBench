from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path

import pytest
from tests.gui.test_optional_solver_gui_health_panel import (
    sample_optional_solver_health_view_model,
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

REPO_ROOT = Path(__file__).resolve().parents[2]
PANEL_SOURCE = (
    REPO_ROOT / "src" / "osw" / "gui" / "dialogs" / "optional_solver_health_panel.py"
)
OPTIONAL_IMPORT_NAMES = {
    "gmsh",
    "meshio",
    "pyvista",
    "vtk",
    "CoolProp",
    "cantera",
}


def test_action_panel_marks_unsafe_actions_unavailable_or_disabled(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    actions = panel.action_state_text()
    reasons = panel.disabled_action_reasons()

    assert "install_solver: unavailable" in actions
    assert "close_issue: unavailable" in actions
    assert "run_validation_gate: unavailable" in actions
    assert "Solver installation is out of scope." in reasons["install_solver"]
    assert "Issue closure requires a separate closure-review gate." in reasons[
        "close_issue"
    ]
    assert "Active validation requires an explicit OSW-VALID gate." in reasons[
        "run_validation_gate"
    ]


def test_future_placeholders_do_not_expose_clipboard_or_browser_actions(
    app: object,
) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    reasons = panel.disabled_action_reasons()

    assert "copy_summary" in panel.available_action_names()
    assert "open_docs" in panel.available_action_names()
    assert "does not access the clipboard" in reasons["copy_summary"]
    assert "does not open shells or browsers" in reasons["open_docs"]
    assert "passive discovery only" in reasons["refresh_passive_discovery"]


def test_widget_construction_does_not_call_discovery(monkeypatch, app: object) -> None:
    from osw.experimental.optional_solvers import discovery_service
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    view_model = sample_optional_solver_health_view_model()

    def fail_discovery(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("GUI panel must not perform discovery")

    monkeypatch.setattr(
        discovery_service,
        "discover_optional_solver_manifests",
        fail_discovery,
    )
    monkeypatch.setattr(
        discovery_service,
        "discover_builtin_optional_solvers",
        fail_discovery,
    )

    panel = OptionalSolverHealthPanel(view_model)

    assert "total=3" in panel.summary_text()


def test_panel_source_imports_no_optional_solver_packages() -> None:
    tree = ast.parse(PANEL_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES


def test_panel_source_uses_no_subprocess_solver_or_external_actions() -> None:
    text = PANEL_SOURCE.read_text(encoding="utf-8")

    assert "import subprocess" not in text
    assert "subprocess." not in text
    assert "os.system" not in text
    assert "QProcess" not in text
    assert "discover_optional_solver_manifests" not in text
    assert "discover_builtin_optional_solvers" in text
    assert "QDesktopServices" not in text
    assert "webbrowser" not in text
    assert ".clipboard(" not in text
    assert "gh issue" not in text
    assert "gh release" not in text


def test_safety_text_states_non_goal_boundaries(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    text = panel.safety_text()

    assert "No automatic startup refresh." in text
    assert "passive presence checks only after an explicit user action" in text
    assert "Refresh output is not validation evidence." in text
    assert "No active smoke validation." in text
    assert "No solver execution." in text
    assert "No subprocess usage." in text
    assert "No solver or dependency installation." in text
    assert "No optional solver package import." in text
    assert "No issue closure action." in text
    assert "External solvers and optional science packages are not bundled." in text
    assert "Skipped-missing validation history is not pass evidence." in text
    assert "No certification claim." in text
