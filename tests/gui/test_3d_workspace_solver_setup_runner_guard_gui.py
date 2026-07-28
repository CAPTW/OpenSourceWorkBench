from __future__ import annotations

import ast
from importlib import import_module
from pathlib import Path

import pytest

GUI_FILES = (
    Path("src/osw/gui/setup_overlay_view_model.py"),
    Path("src/osw/gui/widgets/setup_overlay_panel.py"),
    Path("src/osw/gui/workspace_scene_controller.py"),
    Path("src/osw/gui/workspace_scene_pyvistaqt.py"),
    Path("src/osw/gui/main_window.py"),
)


def test_gui_setup_paths_have_no_solver_runner_or_subprocess_imports() -> None:
    try:
        import_module("osw.gui.setup_overlay_view_model")
        import_module("osw.gui.widgets.setup_overlay_panel")
    except ModuleNotFoundError:
        pytest.fail("GUI setup overlay modules are missing", pytrace=False)

    forbidden_names = {"subprocess", "ExternalCommandRunner", "RunManager"}
    for path in GUI_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: set[str] = set()
        solver_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
                solver_imports.extend(
                    alias.name
                    for alias in node.names
                    if alias.name == "osw.solvers"
                    or alias.name.startswith("osw.solvers.")
                )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imported.add(module)
                imported.update(alias.name for alias in node.names)
                if module == "osw.solvers" or module.startswith("osw.solvers."):
                    solver_imports.append(module)
        assert forbidden_names.isdisjoint(imported)
        assert solver_imports == []


def test_setup_contracts_expose_no_execution_or_native_backend_fields() -> None:
    try:
        api = import_module("osw.core.solver_setup")
        view_model = import_module("osw.gui.setup_overlay_view_model")
    except ModuleNotFoundError:
        pytest.fail("setup contracts are missing", pytrace=False)

    forbidden = {
        "command",
        "executable",
        "process",
        "runner",
        "native_actor",
        "vtk_actor",
    }
    for contract in (
        api.MaterialAssignmentRecord,
        api.FixedSupportRecord,
        api.ForceLoadRecord,
        view_model.SetupOverlaySpec,
    ):
        assert forbidden.isdisjoint(contract.__dataclass_fields__)
