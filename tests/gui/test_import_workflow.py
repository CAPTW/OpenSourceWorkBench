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


def test_gui_mesh_import_attaches_mesh_metadata(
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
    before = len(window.current_project.meshes)

    imported = window.import_mesh_file(mesh_path)

    # The mesh import is metadata-only (meshio bridge); it attaches one mesh
    # reference to the current project without running external tools.
    assert imported is True
    assert len(window.current_project.meshes) == before + 1

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
    before = len(window.current_project.script_refs)

    script_imported = window.preview_script_file(script_path)
    mat_imported = window.preview_mat_file(mat_path)

    # Preview-first contract: the script and MAT imports record metadata only.
    assert script_imported is True
    assert mat_imported is True

    # The `.m` script is previewed as text and is never executed, so its
    # side-effect marker file must not exist.
    assert marker_path.exists() is False

    # Both previews attach reference metadata to the current project.
    script_names = [getattr(ref, "name", "") for ref in window.current_project.script_refs]
    assert "plot_preview.m" in script_names
    assert "sample.mat" in script_names
    assert len(window.current_project.script_refs) == before + 2

    # The previews are surfaced in the project tree without running code.
    assert _find_tree_item(window, "plot_preview.m") is not None
    assert _find_tree_item(window, "sample.mat") is not None

    del app


def _find_tree_item(window: object, label: str) -> object | None:
    assert QtCore is not None
    matches = window.project_tree.findItems(
        label,
        QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive,
    )
    return matches[0] if matches else None
