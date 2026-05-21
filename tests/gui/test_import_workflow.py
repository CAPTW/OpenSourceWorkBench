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
    from PySide6 import QtCore, QtWidgets
else:
    QtCore = None
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_gui_mesh_import_updates_tree_properties_and_table(
    app: object,
    tmp_path: Path,
) -> None:
    pytest.importorskip("meshio")
    pytest.importorskip("numpy")
    import meshio
    import numpy as np

    from osw.gui.main_window import MainWindow

    mesh_path = tmp_path / "triangle.vtu"
    mesh = meshio.Mesh(
        points=np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
            ]
        ),
        cells=[("triangle", np.array([[0, 1, 2]]))],
    )
    mesh.write(mesh_path)

    window = MainWindow(artifact_dir=tmp_path, report_directory=tmp_path)
    operation = window.import_file(mesh_path)
    mesh_item = _find_tree_item(window, "Mesh: triangle.vtu")

    assert operation.status == "Imported"
    assert mesh_item is not None
    assert window.workflow_session.project.meshes[0].path == str(mesh_path)
    assert window.properties_panel.row_value("Type") == "Mesh (vtu)"
    assert window.properties_panel.row_value("Status") == "Imported"
    assert window.table_viewer.table.rowCount() >= 1
    assert "Mesh preview" in window.table_viewer.summary_label.text()

    del app


def test_gui_script_and_mat_import_are_preview_first(
    app: object,
    tmp_path: Path,
) -> None:
    pytest.importorskip("scipy.io")
    import scipy.io

    from osw.gui.main_window import MainWindow

    marker_path = tmp_path / "should_not_exist.txt"
    script_path = tmp_path / "plot_preview.m"
    script_path.write_text(
        "\n".join(
            [
                "x = 1:3;",
                "plot(x, x);",
                f"fid = fopen('{marker_path.as_posix()}', 'w');",
                "fprintf(fid, 'ran');",
                "fclose(fid);",
            ]
        ),
        encoding="utf-8",
    )
    mat_path = tmp_path / "sample.mat"
    scipy.io.savemat(mat_path, {"temperature": [[300.0, 301.0, 302.0]]})

    window = MainWindow(artifact_dir=tmp_path, report_directory=tmp_path)
    script_operation = window.import_file(script_path)
    mat_operation = window.import_file(mat_path)

    assert script_operation.status == "Previewed with findings"
    assert marker_path.exists() is False
    assert _find_tree_item(window, "M-script preview: plot_preview.m") is not None
    assert _find_tree_item(window, "MAT data preview: sample.mat") is not None
    assert len(window.workflow_session.project.scripts) == 1
    assert len(window.workflow_session.project.results) == 1
    assert mat_operation.status == "Previewed"
    assert "temperature" in window.table_viewer.summary_label.text()

    del app


def _find_tree_item(window: object, label: str) -> object | None:
    assert QtCore is not None
    matches = window.project_tree.findItems(
        label,
        QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive,
    )
    return matches[0] if matches else None
