"""Tests for the UI-003 HeatSink_Flow project tree panel."""

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

EXPECTED_GROUPS = (
    "Geometry",
    "Mesh",
    "Physics",
    "Solvers",
    "Scripts",
    "Results",
    "Reports",
)
EXPECTED_LABELS = (
    "HeatSink_Flow",
    "Geometry",
    "heatsink.step",
    "enclosure.stp",
    "fluid_domain.csg",
    "Mesh",
    "mesh.msh",
    "mesh_stats.txt",
    "Physics",
    "heat_transfer.yaml",
    "turbulence.yaml",
    "Solvers",
    "chtSolver",
    "settings.json",
    "Scripts",
    "preprocess.m",
    "run_case.m",
    "postprocess.m",
    "Results",
    "run_0001",
    "fields.ex2",
    "residuals.dat",
    "monitor.log",
    "run_0000 (baseline)",
    "Reports",
    "report.md",
    "report.pdf",
)


def test_demo_tree_data_is_import_safe_and_complete() -> None:
    from osw.gui.widgets.project_tree_panel import (
        DEMO_PROJECT_LABELS,
        MAJOR_GROUP_LABELS,
        project_tree_filter_matches,
    )

    assert tuple(MAJOR_GROUP_LABELS) == EXPECTED_GROUPS
    assert tuple(DEMO_PROJECT_LABELS) == EXPECTED_LABELS
    assert "Mesh" in project_tree_filter_matches("mesh")
    assert "mesh.msh" in project_tree_filter_matches("mesh")
    assert "heatsink.step" not in project_tree_filter_matches("mesh")


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


def _hidden_labels(tree: object) -> list[str]:
    hidden: list[str] = []

    def visit(item: object) -> None:
        if item.isHidden():
            hidden.append(item.text(0))
        for index in range(item.childCount()):
            visit(item.child(index))

    for top_index in range(tree.topLevelItemCount()):
        visit(tree.topLevelItem(top_index))
    return hidden


def test_project_tree_panel_instantiates_with_reference_labels(app: object) -> None:
    from osw.gui.widgets.project_tree_panel import ProjectTreePanel

    panel = ProjectTreePanel()

    assert panel.objectName() == "oswProjectTreePanel"
    assert panel.header_label.text() == "PROJECTS"
    assert panel.tree.objectName() == "oswProjectTree"
    assert panel.filter_frame.objectName() == "oswProjectTreeFilters"
    assert panel.search_field.objectName() == "oswProjectTreeSearch"
    assert panel.search_field.placeholderText() == "Search project tree..."
    assert panel.footer_label.text() == "Active Project: HeatSink_Flow"
    assert _tree_labels(panel.tree) == list(EXPECTED_LABELS)


def test_mesh_completion_indicator_is_present(app: object) -> None:
    from osw.gui.widgets.project_tree_panel import ProjectTreePanel

    panel = ProjectTreePanel()

    assert panel.items_by_label["mesh.msh"].text(1) == "✓"


def test_filtering_for_mesh_hides_unrelated_leaf_nodes(app: object) -> None:
    from osw.gui.widgets.project_tree_panel import ProjectTreePanel

    panel = ProjectTreePanel()
    panel.filter_tree("mesh")

    hidden = _hidden_labels(panel.tree)
    assert "mesh.msh" not in hidden
    assert "mesh_stats.txt" not in hidden
    assert "heatsink.step" in hidden

    panel.filter_tree("")
    assert _hidden_labels(panel.tree) == []


def test_theme_manager_applies_dark_and_light_to_project_tree(app: object) -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.widgets.project_tree_panel import ProjectTreePanel

    panel = ProjectTreePanel()
    manager = ThemeManager(auto_load=False)

    manager.set_mode("dark", save=False)
    panel.set_theme_tokens(manager.current_tokens)
    manager.set_mode("light", save=False)
    panel.set_theme_tokens(manager.current_tokens)

    assert panel.styleSheet()


def test_main_window_still_uses_project_tree_panel(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.project_tree_panel.objectName() == "oswProjectTreePanel"
    assert window.project_tree.objectName() == "oswProjectTree"
