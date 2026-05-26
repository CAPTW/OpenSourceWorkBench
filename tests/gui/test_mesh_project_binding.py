from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
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


def test_project_tree_keeps_demo_mesh_rows(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()
    labels = _tree_labels(window.project_tree_panel.tree)

    assert "Mesh" in labels
    assert "mesh.msh" in labels
    assert window.current_project.metadata.name == "HeatSink_Flow"


def test_properties_panel_displays_mesh_summary_rows(app: object) -> None:
    from osw.core.demo_project import create_heatsink_flow_demo_project
    from osw.core.project_schema import MeshRef, Project
    from osw.gui.widgets.properties_panel import PropertiesPanel

    mesh_info = {
        "format": "vtu",
        "node_count": 4,
        "element_count": 1,
        "cell_types": ["tetra"],
        "bounds": {
            "minimum": [0.0, 0.0, 0.0],
            "maximum": [1.0, 1.0, 1.0],
        },
    }
    project = create_heatsink_flow_demo_project()
    project = Project(
        metadata=project.metadata,
        units=project.units,
        materials=project.materials,
        geometry=project.geometry,
        meshes=[
            *project.mesh_refs,
            MeshRef(
                "imported-tiny",
                "mesh/tiny.vtu",
                "vtu",
                name="tiny.vtu",
                status="imported",
                cell_count=1,
                node_count=4,
                quality_summary="4 nodes, 1 elements, cell types: tetra",
                mesh_info=mesh_info,
            ),
        ],
        scripts=project.scripts,
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
    panel.set_node_selection("tiny.vtu")

    assert panel.row_value("Nodes") == "4"
    assert panel.row_value("Elements") == "1"
    assert panel.row_value("Cell types") == "tetra"
    assert panel.row_value("Bounds") == "[0.0, 0.0, 0.0] -> [1.0, 1.0, 1.0]"


def test_main_window_can_attach_imported_mesh_metadata(app: object) -> None:
    from osw.gui.main_window import MainWindow
    from osw.mesh.mesh_model import MeshCellBlock, MeshModel
    from osw.mesh.meshio_bridge import MeshImportResult, MeshImportStatus

    window = MainWindow()
    mesh = MeshModel(
        id="tiny",
        name="tiny.vtu",
        source_path="mesh/tiny.vtu",
        points=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )

    attached = window.attach_mesh_to_project(MeshImportResult(MeshImportStatus.OK, mesh=mesh))
    labels = _tree_labels(window.project_tree_panel.tree)

    assert attached is True
    assert any(mesh_ref.name == "tiny.vtu" for mesh_ref in window.current_project.mesh_refs)
    assert "tiny.vtu" in labels
    assert window.properties_panel.current_project() is window.current_project


def test_theme_switching_still_works_after_mesh_binding(app: object) -> None:
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
