from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOADER = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "optional_solvers"
    / "plugin_manifest_loader.py"
)
OPTIONAL_IMPORT_NAMES = {
    "gmsh",
    "meshio",
    "pyvista",
    "vtk",
    "CoolProp",
    "cantera",
}
FORBIDDEN_IMPORT_ROOTS = {
    "subprocess",
    "requests",
    "urllib",
    "socket",
    "importlib",
}
FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
}
FORBIDDEN_TEXT = (
    "discovery_service",
    "discover_optional_solver",
    "discover_builtin_optional_solvers",
    ".glob(",
    ".rglob(",
    ".iterdir(",
    "gh issue",
    "gh release",
)


def _tree() -> ast.AST:
    return ast.parse(LOADER.read_text(encoding="utf-8"))


def test_loader_imports_no_optional_solver_packages() -> None:
    tree = _tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(OPTIONAL_IMPORT_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in OPTIONAL_IMPORT_NAMES


def test_loader_imports_no_plugin_network_or_subprocess_packages() -> None:
    tree = _tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(FORBIDDEN_IMPORT_ROOTS)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in FORBIDDEN_IMPORT_ROOTS


def test_loader_has_no_dynamic_code_execution_calls() -> None:
    tree = _tree()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALLS


def test_loader_source_has_no_scan_discovery_or_issue_release_mutation_text() -> None:
    text = LOADER.read_text(encoding="utf-8")

    for forbidden in FORBIDDEN_TEXT:
        assert forbidden not in text
