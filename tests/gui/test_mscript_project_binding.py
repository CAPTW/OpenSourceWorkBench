from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

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

FIXTURES = Path(__file__).parents[1] / "fixtures" / "mscript"


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _tree_labels(tree: object) -> list[str]:
    labels: list[str] = []

    def visit(item: object) -> None:
        labels.append(item.text(0))
        for index in range(item.childCount()):
            visit(item.child(index))

    for top_index in range(tree.topLevelItemCount()):
        visit(tree.topLevelItem(top_index))
    return labels


def test_main_window_keeps_demo_script_rows(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()
    labels = _tree_labels(window.project_tree_panel.tree)

    assert window.current_project.metadata.name == "HeatSink_Flow"
    assert "Scripts" in labels
    assert "preprocess.m" in labels
    assert "run_case.m" in labels
    assert "postprocess.m" in labels
    assert window.project_tree_panel.objectName() == "oswProjectTreePanel"
    assert window.properties_panel.objectName() == "oswPropertiesPanel"

    del app


def test_properties_panel_displays_script_preview_summary(app: object) -> None:
    from osw.core.demo_project import create_heatsink_flow_demo_project
    from osw.core.project_schema import Project
    from osw.gui.widgets.properties_panel import PropertiesPanel
    from osw.scripts.mscript.importer import create_script_ref, preview_mscript

    result = preview_mscript(FIXTURES / "function_multi_output.m")
    assert result.preview is not None
    script_ref = create_script_ref(result.preview)
    project = create_heatsink_flow_demo_project()
    project = Project(
        metadata=project.metadata,
        units=project.units,
        materials=project.materials,
        geometry=project.geometry,
        meshes=project.meshes,
        scripts=[*project.scripts, script_ref],
        boundary_curves=project.boundary_curves,
        physics=project.physics,
        solvers=project.solvers,
        results=project.results,
        report=project.report,
        schema_version=project.schema_version,
        plugins=project.plugins,
        warnings=project.warnings,
    )
    panel = PropertiesPanel()
    panel.set_project(project)
    panel.set_node_selection("function_multi_output.m")

    assert panel.row_value("Kind") == "function"
    assert panel.row_value("Line count") == str(result.preview.line_count)
    assert panel.row_value("Function signature") == "function [a,b] = function_multi_output(x,y)"
    assert panel.row_value("Plot hints") == "0"
    assert "warnings=0" in panel.row_value("Safety summary")

    del app


def test_main_window_can_attach_script_preview_without_running_file(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.main_window import MainWindow

    marker = tmp_path / "should_not_exist.txt"
    script = tmp_path / "preview_only.m"
    script.write_text(
        "\n".join(
            [
                "x = 1:3;",
                f"system('echo unsafe > {marker.as_posix()}');",
                "plot(x, x);",
            ]
        ),
        encoding="utf-8",
    )
    window = MainWindow()

    attached = window.preview_script_file(script)
    labels = _tree_labels(window.project_tree_panel.tree)

    assert attached is True
    assert marker.exists() is False
    assert any(script_ref.name == "preview_only.m" for script_ref in window.current_project.scripts)
    assert "preview_only.m" in labels
    window.properties_panel.set_node_selection("preview_only.m")
    assert "high=" in window.properties_panel.row_value("Safety summary")

    del app


def test_theme_switching_still_works_after_script_binding(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    window.theme_manager.set_mode("dark", save=False)
    window.theme_manager.apply_to_app(app)
    window.theme_manager.set_mode("light", save=False)
    window.theme_manager.apply_to_app(app)
    window.theme_manager.set_mode("system", save=False)
    window.theme_manager.apply_to_app(app)

    assert window.project_tree_panel.objectName() == "oswProjectTreePanel"
    assert window.properties_panel.objectName() == "oswPropertiesPanel"
    del app
