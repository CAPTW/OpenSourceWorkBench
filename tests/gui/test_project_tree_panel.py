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


def test_project_tree_named_selection_nodes_use_stable_payload_and_runtime_state(
    app: object,
) -> None:
    from osw.core.project_schema import Project, ProjectMetadata
    from osw.core.selection import (
        EntityKind,
        EntityLocator,
        NamedSelection,
        SelectionTargetRef,
    )
    from osw.core.selection_resolution import ResolutionResult, ResolutionState
    from osw.gui.widgets.project_tree_panel import ProjectTreePanel

    locator = EntityLocator(
        identity_schema="osw.mesh_identity.v1",
        mesh_ref="mesh-1",
        mesh_fingerprint="a" * 64,
        entity_kind=EntityKind.NODE,
        id_namespace="osw.mesh.point_ordinal.v1",
        entity_ids=(0, 2),
    )
    selection = NamedSelection(
        id="selection-stable",
        name="Supports",
        entity_kind=EntityKind.NODE,
        targets=(
            SelectionTargetRef(
                kind=EntityKind.NODE,
                ids=(0, 2),
                mesh_ref="mesh-1",
                locator=locator,
            ),
        ),
        source_mesh_ref="mesh-1",
    )
    panel = ProjectTreePanel()
    panel.set_project(
        Project(
            metadata=ProjectMetadata(name="Selection Tree"),
            selections=(selection,),
        )
    )

    item = panel.named_selection_item(selection.id)
    assert item is not None
    assert item.parent().text(0) == "Named Selections"
    assert panel.item_payload(item) == {
        "selection_id": selection.id,
        "entity_kind": "node",
        "mesh_ref": "mesh-1",
        "mesh_fingerprint": "a" * 64,
    }

    panel.set_named_selection_resolutions(
        {
            selection.id: ResolutionResult(
                state=ResolutionState.STALE,
                reason_code="MESH_FINGERPRINT_MISMATCH",
                message="The loaded mesh identity differs from this selection.",
            )
        },
        active_selection_ids=(selection.id,),
    )
    assert item.text(1) == "STALE"
    assert "loaded mesh identity differs" in item.toolTip(0)
    assert panel.select_named_selection(selection.id, emit=False)
    assert panel.current_named_selection_id() == selection.id


def test_project_tree_groups_typed_setup_records_by_product_role(app: object) -> None:
    from osw.core.project_schema import PhysicsSetup, Project, ProjectMetadata
    from osw.core.solver_setup import (
        FixedSupportRecord,
        ForceLoadRecord,
        HeatFluxRecord,
        MaterialAssignmentRecord,
        PrescribedDisplacementRecord,
        PressureLoadRecord,
        SetupReadiness,
        SetupRecordKind,
        SetupRecordStatus,
        TemperatureRecord,
    )
    from osw.core.units import Quantity
    from osw.gui.widgets.project_tree_panel import ProjectTreePanel

    setup = PhysicsSetup(
        material_assignment_records=[
            MaterialAssignmentRecord("material", "Steel region", "steel", "cells")
        ],
        fixed_support_records=[FixedSupportRecord("fixed", "Clamp", "nodes")],
        prescribed_displacement_records=[
            PrescribedDisplacementRecord(
                "move",
                "Move",
                "nodes",
                ux=Quantity(0.0, "m"),
            )
        ],
        force_load_records=[
            ForceLoadRecord(
                "force",
                "Force",
                "nodes",
                Quantity(1.0, "N"),
                (1.0, 0.0, 0.0),
            )
        ],
        pressure_load_records=[
            PressureLoadRecord("pressure", "Pressure", "surface", Quantity(1.0, "Pa"))
        ],
        temperature_records=[
            TemperatureRecord("temperature", "Temperature", "nodes", Quantity(300.0, "K"))
        ],
        heat_flux_records=[HeatFluxRecord("flux", "Heat Flux", "surface", Quantity(2.0, "W/m^2"))],
    )
    panel = ProjectTreePanel()
    panel.set_project(Project(ProjectMetadata(name="Setups"), physics=setup))

    assert panel.setup_item("material").parent().text(0) == "Materials"
    assert panel.setup_item("fixed").parent().text(0) == "Boundary Conditions"
    assert panel.setup_item("move").parent().text(0) == "Boundary Conditions"
    assert panel.setup_item("force").parent().text(0) == "Loads"
    assert panel.setup_item("pressure").parent().text(0) == "Loads"
    assert panel.setup_item("temperature").parent().text(0) == "Thermal Conditions"
    assert panel.setup_item("flux").parent().text(0) == "Thermal Conditions"
    assert panel.item_payload(panel.setup_item("material"))["material_id"] == "steel"
    status = SetupRecordStatus(
        "force",
        SetupRecordKind.FORCE,
        SetupReadiness.BLOCKED,
        "MESH_FINGERPRINT_MISMATCH",
        "The target is stale.",
    )
    panel.set_setup_statuses({"force": status}, active_setup_id="force")
    summary = panel.setup_item("force").text(1)
    assert "force" in summary
    assert "nodes" in summary
    assert "enabled" in summary
    assert "MESH_FINGERPRINT_MISMATCH" in summary
    assert "stale" in panel.setup_item("force").toolTip(0).lower()
    assert panel.select_setup("force", emit=False)
    assert panel.current_setup_id() == "force"


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
