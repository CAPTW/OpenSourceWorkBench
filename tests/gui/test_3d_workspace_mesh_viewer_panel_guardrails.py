"""Import/runner guardrails for the 3D workspace mesh viewer GUI slice.

Mirrors the optional-solver GUI guardrail tests: it reads the panel and
view-model source with ``ast`` and asserts they import no rendering package or
solver runner at import time, run no subprocess, and expose no direct
backend-execution control. These checks need no PySide6, so they run everywhere.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PANEL_SOURCE = REPO_ROOT / "src" / "osw" / "gui" / "widgets" / "mesh_viewer_panel.py"
VIEW_MODEL_SOURCE = REPO_ROOT / "src" / "osw" / "gui" / "workspace_scene_view_model.py"

FORBIDDEN_IMPORT_ROOTS = {
    "subprocess",
    "pyvista",
    "vtk",
    "meshio",
    "gmsh",
    "ccx",
    "openfoam",
    "octave",
}

FORBIDDEN_SUBSTRINGS = (
    "import subprocess",
    "subprocess.",
    "os.system",
    "QProcess",
    "Popen",
    "ExternalCommandRunner",
    "RunManager",
    "CalculiXRunner",
    "OpenFOAMRunner",
    "OctaveRunner",
    "run_case",
    "run_input_deck",
    "run_command",
)


def _imported_roots(source: Path) -> set[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_panel_imports_no_forbidden_roots() -> None:
    assert _imported_roots(PANEL_SOURCE).isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_view_model_imports_no_forbidden_roots() -> None:
    assert _imported_roots(VIEW_MODEL_SOURCE).isdisjoint(FORBIDDEN_IMPORT_ROOTS)


def test_sources_use_no_subprocess_qprocess_or_runners() -> None:
    for source in (PANEL_SOURCE, VIEW_MODEL_SOURCE):
        text = source.read_text(encoding="utf-8")
        for needle in FORBIDDEN_SUBSTRINGS:
            assert needle not in text, f"{source.name} must not contain {needle!r}"


def test_panel_exposes_no_run_solver_control() -> None:
    text = PANEL_SOURCE.read_text(encoding="utf-8")
    assert "Run Solver" not in text
    assert "run_solver" not in text


def test_view_model_does_not_import_pyside6() -> None:
    # Keeps the helpers unit-testable without the optional GUI extra. A docstring
    # may mention PySide6; only an actual import is forbidden.
    assert "PySide6" not in _imported_roots(VIEW_MODEL_SOURCE)
    text = VIEW_MODEL_SOURCE.read_text(encoding="utf-8")
    assert "import PySide6" not in text
    assert "from PySide6" not in text
