"""Runner-boundary guardrails for the main-window mesh viewer wiring.

Reads `main_window.py` source with `ast`/substring checks and asserts the
wiring introduces no subprocess/runner import or call, adds no "Run Solver"
control, imports `build_mesh_viewer_panel` lazily (not at module top), and
introduces no provider module. These checks need no PySide6.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_WINDOW_SOURCE = REPO_ROOT / "src" / "osw" / "gui" / "main_window.py"
WORKFLOW_SERVICE_SOURCE = REPO_ROOT / "src" / "osw" / "gui" / "workflow_service.py"
PROVIDER_MODULE = REPO_ROOT / "src" / "osw" / "gui" / "mesh_viewer_provider.py"

# Exact runner/subprocess tokens. Note: solver *menu titles* and open_* dialog
# method names (e.g. "Generate OpenFOAM Template Case...") are intentionally not
# in this set -- only direct subprocess/runner usage is forbidden.
FORBIDDEN_SUBSTRINGS = (
    "import subprocess",
    "subprocess.",
    "QProcess",
    "Popen",
    "ExternalCommandRunner",
    "RunManager",
    "CalculiXRunner",
    "OpenFOAMRunner",
    "OctaveRunner",
    "GmshAdapter",
    "Run Solver",
)


def test_main_window_has_no_runner_or_subprocess_refs() -> None:
    text = MAIN_WINDOW_SOURCE.read_text(encoding="utf-8")
    for needle in FORBIDDEN_SUBSTRINGS:
        assert needle not in text, f"main_window.py must not contain {needle!r}"


def test_mesh_viewer_wiring_symbols_present() -> None:
    text = MAIN_WINDOW_SOURCE.read_text(encoding="utf-8")
    assert "open_mesh_viewer" in text
    assert "load_mesh_into_viewer" in text
    assert "oswMeshViewerDialog" in text
    assert "oswActionOpenMeshViewer" in text


def test_build_mesh_viewer_panel_imported_lazily_not_at_module_top() -> None:
    tree = ast.parse(MAIN_WINDOW_SOURCE.read_text(encoding="utf-8"))

    for node in tree.body:  # module-level statements only
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "mesh_viewer_panel" not in node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert "mesh_viewer_panel" not in alias.name

    lazy_import = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and "mesh_viewer_panel" in node.module
            and any(alias.name == "build_mesh_viewer_panel" for alias in node.names)
        ):
            lazy_import = True
    assert lazy_import, "build_mesh_viewer_panel must be imported lazily in main_window.py"


def test_no_mesh_viewer_provider_module_introduced() -> None:
    assert not PROVIDER_MODULE.exists(), "no provider module should be introduced (Option B)"


def test_workflow_service_does_not_import_the_viewer() -> None:
    # MainWindow orchestrates the mesh hand-off; workflow_service stays the mesh
    # producer and must not depend on the viewer widget/view-model.
    text = WORKFLOW_SERVICE_SOURCE.read_text(encoding="utf-8")
    assert "mesh_viewer_panel" not in text
    assert "workspace_scene_view_model" not in text
    assert "MeshViewerPanel" not in text
    assert "build_mesh_viewer_panel" not in text
