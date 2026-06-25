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


def test_export_source_imports_no_optional_solver_packages() -> None:
    tree = ast.parse(PANEL_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES


def test_export_source_has_no_clipboard_shell_browser_or_solver_execution() -> None:
    text = PANEL_SOURCE.read_text(encoding="utf-8")

    for forbidden in (
        "import subprocess",
        "subprocess.",
        "os.system",
        "QProcess",
        "QClipboard",
        ".clipboard(",
        "QDesktopServices",
        "webbrowser",
        "os.startfile",
        "open_output",
        "open output folder",
        "discover_optional_solver",
        "gh issue",
        "gh release",
    ):
        assert forbidden not in text
    assert "discover_builtin_optional_solvers" in text
    assert ".mkdir(" not in text
    assert ".write_text(" in text


def test_export_does_not_call_discovery(monkeypatch, app: object, tmp_path) -> None:
    from osw.experimental.optional_solvers import discovery_service
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    def fail_discovery(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("GUI export must not perform discovery")

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
    target = tmp_path / "summary.json"
    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: target,
    )

    panel.export_summary_button.click()

    assert target.exists()
    assert panel.export_error_text() == ""
    assert "not_validation_evidence" in target.read_text(encoding="utf-8")


def test_export_does_not_create_parent_directories(app: object, tmp_path) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    target = tmp_path / "missing" / "summary.txt"
    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: target,
    )

    panel.export_summary_button.click()

    assert not target.parent.exists()
    assert not target.exists()
    assert "OSE_PARENT_MISSING" in panel.export_error_text()
