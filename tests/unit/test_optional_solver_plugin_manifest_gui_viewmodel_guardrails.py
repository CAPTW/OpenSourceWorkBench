from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_gui_viewmodel.py"
)


def _source() -> str:
    return MODULE.read_text(encoding="utf-8")


def test_viewmodel_source_has_no_file_loading_or_json_parsing() -> None:
    source = _source()

    forbidden = (
        "Path(",
        ".read_text(",
        "open(",
        "json.",
        "load_optional_solver_plugin_manifest_json(",
        "load_optional_solver_plugin_manifest_dict(",
        "load_optional_solver_plugin_manifest_documents(",
    )
    for phrase in forbidden:
        assert phrase not in source


def test_viewmodel_source_has_no_pyside_qt_subprocess_or_plugin_package_imports() -> None:
    tree = ast.parse(_source())
    imported_names = "\n".join(
        (
            node.module
            if isinstance(node, ast.ImportFrom)
            else " ".join(alias.name for alias in node.names)
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom | ast.Import)
    ).lower()

    for phrase in (
        "pyside",
        "qt",
        "subprocess",
        "importlib",
        "pkg_resources",
        "entry_points",
        "gmsh",
        "cantera",
        "pyvista",
        "meshio",
        "coolprop",
    ):
        assert phrase not in imported_names


def test_viewmodel_imports_only_allowed_optional_solver_modules() -> None:
    tree = ast.parse(_source())
    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom | ast.Import)
    ]

    imported_text = "\n".join(ast.get_source_segment(_source(), node) or "" for node in imports)
    assert ".plugin_manifest_loader" in imported_text
    assert ".gui" not in imported_text
    assert "src.osw.gui" not in imported_text
