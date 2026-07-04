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


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_gui_run_generate_updates_monitor_tree_and_report(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.main_window import MainWindow

    geometry_path = tmp_path / "plate.stl"
    geometry_path.write_text(_ascii_stl(), encoding="utf-8")

    window = MainWindow(artifact_dir=tmp_path / "artifacts", report_directory=tmp_path)
    window.import_file(geometry_path)
    operation = window.run_workflow()
    report_path = window.export_report(tmp_path / "gui_workflow_report.html")

    monitor_text = window.run_monitor.toPlainText()
    report_text = report_path.read_text(encoding="utf-8")

    assert operation.status == "Prepared"
    assert "CalculiX linear static prepare" in _tree_labels(window)
    assert "OpenFOAM cavity prepare" in _tree_labels(window)
    assert "Gmsh plate prepare" in _tree_labels(window)
    assert "M-script explicit run diagnostic" in _tree_labels(window)
    assert "Prepared input deck" in monitor_text
    assert "prepared openfoam cavity template" in monitor_text.lower()
    assert "Prepared Gmsh .geo preview" in monitor_text
    assert window.workflow_session.project.solvers
    assert window.workflow_session.result_tables
    assert (tmp_path / "artifacts" / "gmsh" / "gui_plate.geo").exists()
    assert not (tmp_path / "artifacts" / "gmsh" / "gui_plate.msh").exists()
    assert (tmp_path / "artifacts" / "calculix" / "gui_cantilever.inp").exists()
    assert not (tmp_path / "artifacts" / "calculix" / "gui_cantilever.frd").exists()
    assert (
        tmp_path
        / "artifacts"
        / "openfoam"
        / "gui_cavity"
        / "system"
        / "controlDict"
    ).exists()
    assert not (tmp_path / "artifacts" / "openfoam" / "gui_cavity" / "1").exists()
    assert "plate.stl" in report_text
    assert "CalculiX linear static" in report_text
    assert "M-script execution is explicit" in report_text

    del app


def test_gui_python_modules_do_not_import_subprocess() -> None:
    gui_root = Path(__file__).parents[2] / "src" / "osw" / "gui"

    offenders = [
        path.relative_to(gui_root).as_posix()
        for path in gui_root.glob("*.py")
        if "subprocess" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def _ascii_stl() -> str:
    return "\n".join(
        [
            "solid plate",
            "  facet normal 0 0 1",
            "    outer loop",
            "      vertex 0 0 0",
            "      vertex 1 0 0",
            "      vertex 0 1 0",
            "    endloop",
            "  endfacet",
            "endsolid plate",
            "",
        ]
    )


def _tree_labels(window: object) -> set[str]:
    labels: set[str] = set()
    root = window.project_tree.topLevelItem(0)
    stack = [root]
    while stack:
        item = stack.pop()
        labels.add(item.text(0))
        stack.extend(item.child(index) for index in range(item.childCount()))
    return labels
