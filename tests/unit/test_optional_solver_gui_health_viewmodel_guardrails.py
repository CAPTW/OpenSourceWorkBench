from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = REPO_ROOT / "src" / "osw" / "experimental" / "optional_solvers"
VIEWMODEL = PACKAGE / "gui_health_viewmodel.py"
OPTIONAL_IMPORT_NAMES = {
    "gmsh",
    "meshio",
    "pyvista",
    "vtk",
    "CoolProp",
    "cantera",
}
FORBIDDEN_IMPORT_ROOTS = {
    "PySide6",
    "PyQt6",
    "QtCore",
    "QtGui",
    "QtWidgets",
}


def test_viewmodel_source_imports_no_qt_or_pyside() -> None:
    tree = ast.parse(VIEWMODEL.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(FORBIDDEN_IMPORT_ROOTS)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in FORBIDDEN_IMPORT_ROOTS


def test_viewmodel_source_imports_no_optional_solver_packages() -> None:
    tree = ast.parse(VIEWMODEL.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES


def test_viewmodel_source_uses_no_subprocess_or_discovery_execution() -> None:
    text = VIEWMODEL.read_text(encoding="utf-8")

    assert "subprocess" not in text
    assert "shutil.which" not in text
    assert "discover_optional_solver" not in text
    assert "discover_builtin_optional_solvers" not in text


def test_viewmodel_source_has_no_install_or_run_smoke_actions() -> None:
    text = VIEWMODEL.read_text(encoding="utf-8").lower()

    assert "--install" not in text
    assert "--run-smoke" not in text
    assert "pip install" not in text
    assert "conda install" not in text
