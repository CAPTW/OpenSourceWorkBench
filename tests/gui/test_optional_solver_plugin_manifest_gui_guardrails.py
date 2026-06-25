from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path

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

REPO_ROOT = Path(__file__).resolve().parents[2]
PANEL_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "gui"
    / "dialogs"
    / "optional_solver_plugin_manifest_panel.py"
)
OPTIONAL_IMPORT_NAMES = {
    "gmsh",
    "meshio",
    "pyvista",
    "vtk",
    "CoolProp",
    "cantera",
}


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _source() -> str:
    return PANEL_SOURCE.read_text(encoding="utf-8")


def test_panel_construction_does_not_load_manifests_or_run_discovery(
    monkeypatch: pytest.MonkeyPatch,
    app: object,
) -> None:
    import osw.experimental.optional_solvers as optional_solvers
    from osw.experimental.optional_solvers import discovery_service
    from osw.gui.dialogs.optional_solver_plugin_manifest_panel import (
        OptionalSolverPluginManifestPanel,
    )

    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report()
    )

    def fail_call(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("plugin manifest GUI panel must be display-only")

    monkeypatch.setattr(
        optional_solvers,
        "load_optional_solver_plugin_manifest_json",
        fail_call,
    )
    monkeypatch.setattr(
        optional_solvers,
        "load_optional_solver_plugin_manifest_dict",
        fail_call,
    )
    monkeypatch.setattr(
        optional_solvers,
        "load_optional_solver_plugin_manifest_documents",
        fail_call,
    )
    monkeypatch.setattr(
        discovery_service,
        "discover_builtin_optional_solvers",
        fail_call,
    )

    panel = OptionalSolverPluginManifestPanel(view_model)

    assert "accepted=1" in panel.summary_text()


def test_panel_source_has_no_file_dialog_or_file_loading() -> None:
    source = _source()

    for phrase in (
        "QFileDialog",
        "getOpenFileName",
        "getSaveFileName",
        ".read_text(",
        ".write_text(",
        "Path(",
        "open(",
        "json.",
        "load_optional_solver_plugin_manifest_json",
        "load_optional_solver_plugin_manifest_dict",
        "load_optional_solver_plugin_manifest_documents",
    ):
        assert phrase not in source


def test_panel_source_has_no_plugin_activation_or_external_actions() -> None:
    source = _source()

    for phrase in (
        "subprocess",
        "QProcess",
        "os.system",
        "plugin activation()",
        "activate_plugin",
        "discover_builtin_optional_solvers",
        "discover_optional_solver_manifests",
        "QDesktopServices",
        "webbrowser",
        ".clipboard(",
        "requests.",
        "gh issue",
        "gh release",
    ):
        assert phrase not in source


def test_panel_source_imports_no_optional_solver_packages() -> None:
    tree = ast.parse(_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES
