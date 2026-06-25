from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = REPO_ROOT / "src" / "osw" / "experimental" / "optional_solvers"
EXPORT_VIEWMODEL = PACKAGE / "gui_export_summary_viewmodel.py"
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
FORBIDDEN_TEXT = (
    "subprocess",
    "QFileDialog",
    "QClipboard",
    ".clipboard(",
    "pyperclip",
    "QDesktopServices",
    "webbrowser",
    "os.startfile",
    "open(",
    ".write_text(",
    ".write_bytes(",
    "discover_optional_solver",
    "discover_builtin_optional_solvers",
    "gh issue",
    "gh release",
)


def test_export_viewmodel_source_imports_no_qt_or_pyside() -> None:
    tree = ast.parse(EXPORT_VIEWMODEL.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(FORBIDDEN_IMPORT_ROOTS)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in FORBIDDEN_IMPORT_ROOTS


def test_export_viewmodel_source_imports_no_optional_solver_packages() -> None:
    tree = ast.parse(EXPORT_VIEWMODEL.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES


def test_export_viewmodel_source_has_no_side_effect_apis() -> None:
    text = EXPORT_VIEWMODEL.read_text(encoding="utf-8")

    for forbidden in FORBIDDEN_TEXT:
        assert forbidden not in text
