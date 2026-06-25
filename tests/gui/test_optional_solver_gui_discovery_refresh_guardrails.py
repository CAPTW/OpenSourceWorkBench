from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path

import pytest
from tests.gui.test_optional_solver_gui_discovery_refresh import (
    _manifests,
    _report,
    _stack,
    _view_model,
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


def test_refresh_source_imports_no_optional_solver_packages() -> None:
    tree = ast.parse(PANEL_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES


def test_refresh_source_has_no_solver_subprocess_or_mutation_actions() -> None:
    text = PANEL_SOURCE.read_text(encoding="utf-8")

    for forbidden in (
        "import subprocess",
        "subprocess.",
        "os.system",
        "QProcess",
        "QThread",
        "threading",
        "run_active_smoke",
        "smoke_runner",
        "solver execution path",
        "dependency install command",
        "gh issue",
        "gh release",
        "QDesktopServices",
        "webbrowser",
        "os.startfile",
        ".clipboard(",
    ):
        assert forbidden not in text
    assert "discover_builtin_optional_solvers" in text


def test_default_refresh_runner_is_not_called_on_construction(monkeypatch, app: object) -> None:
    from osw.gui.dialogs import optional_solver_health_panel
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    calls = []

    def passive_runner(*_args, **_kwargs):
        calls.append("called")
        return _report(_stack("gmsh", "discovered", 6))

    monkeypatch.setattr(
        optional_solver_health_panel.discovery_service,
        "discover_builtin_optional_solvers",
        passive_runner,
    )

    panel = OptionalSolverHealthPanel(_view_model())

    assert calls == []
    assert panel.refresh_runner_call_count() == 0


def test_default_refresh_runner_uses_passive_discovery_only(monkeypatch, app: object) -> None:
    from osw.gui.dialogs import optional_solver_health_panel
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    calls = []

    def passive_runner(*_args, **_kwargs):
        calls.append("called")
        return _report(_stack("gmsh", "discovered", 6))

    monkeypatch.setattr(
        optional_solver_health_panel.discovery_service,
        "discover_builtin_optional_solvers",
        passive_runner,
    )
    panel = OptionalSolverHealthPanel(_view_model())

    panel.trigger_refresh_for_test()

    assert calls == ["called"]
    assert panel.refresh_runner_call_count() == 1
    assert "not validation evidence" in panel.refresh_status_text().lower()


def test_refresh_safety_text_states_passive_boundaries(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(
        _view_model(),
        refresh_runner=lambda _request: _report(_stack("alpha", "discovered", 6)),
        refresh_manifests=_manifests(),
    )

    text = panel.safety_text()

    assert "No automatic startup refresh." in text
    assert "passive presence checks only after an explicit user action" in text
    assert "Refresh output is not validation evidence." in text
    assert "No active smoke validation." in text
    assert "No solver execution." in text
    assert "No solver or dependency installation." in text
    assert "No issue closure action." in text
