"""Offscreen GUI tests for entity picking and NamedSelection management."""

from __future__ import annotations

import importlib.util
import os
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest

from osw.gui.workspace_scene_controller import ActiveSceneController
from osw.mesh.mesh_model import MeshCellBlock, MeshData

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


def _mesh(*, moved: bool = False) -> MeshData:
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 2.0 if moved else 1.0, 0.0),
        ),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )


class GuiPickingSession:
    backend_kind = "fake-gui-picking"
    capabilities = frozenset(
        {
            "interactive",
            "hosted-widget",
            "mesh-preview",
            "semantic-actors",
            "picking",
            "selection-overlays",
        }
    )

    def __init__(self) -> None:
        assert QtWidgets is not None
        self.widget = QtWidgets.QWidget()
        self.callback: object | None = None
        self.selection_operation = "replace"
        self.actors: dict[str, object] = {}
        self.calls: list[tuple[object, ...]] = []
        self.close_calls = 0

    @property
    def hosted_widget(self) -> object:
        return self.widget

    def clear(self) -> None:
        self.actors.clear()

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        self.actors[semantic_id] = (payload, generation)
        return SimpleNamespace(warnings=(), rendered=True)

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)

    def request_render(self) -> None:
        return None

    def set_pick_mode(self, mode: str, callback: object) -> None:
        self.callback = callback
        self.calls.append(("mode", mode))

    def set_selection_operation(self, operation: str) -> None:
        self.selection_operation = operation
        self.calls.append(("operation", operation))

    def disable_picking(self) -> None:
        self.callback = None

    def set_hover_entities(
        self, kind: str, indices: tuple[int, ...], generation: int
    ) -> None:
        self.calls.append(("hover", kind, indices, generation))

    def clear_hover(self) -> None:
        self.calls.append(("clear_hover",))

    def set_current_selection(
        self, kind: str, indices: tuple[int, ...], generation: int
    ) -> None:
        self.calls.append(("current", kind, indices, generation))

    def clear_current_selection(self) -> None:
        self.calls.append(("clear_current",))

    def set_named_selection_overlay(
        self,
        selection_id: str,
        kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(("named", selection_id, kind, indices, generation))

    def remove_named_selection_overlay(self, selection_id: str) -> None:
        self.calls.append(("remove_named", selection_id))

    def set_active_named_selection_overlay(
        self,
        selection_id: str,
        kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(("active_named", selection_id, kind, indices, generation))

    def remove_active_named_selection_overlay(self, selection_id: str) -> None:
        self.calls.append(("remove_active_named", selection_id))

    def close(self) -> None:
        self.close_calls += 1

    def emit_pick(self, event: dict[str, object]) -> object:
        assert callable(self.callback)
        payload = dict(event)
        payload.setdefault("intent", self.selection_operation)
        return self.callback(payload)


class GuiPickingFactory:
    backend_kind = GuiPickingSession.backend_kind
    capabilities = GuiPickingSession.capabilities

    def __init__(self) -> None:
        self.session = GuiPickingSession()

    def set_host_parent(self, _parent: object) -> None:
        return None

    def create_session(self) -> GuiPickingSession:
        return self.session


def test_named_selection_panel_exposes_accessible_bounded_controls(app: object) -> None:
    panel_module = import_module("osw.gui.widgets.named_selection_panel")
    panel = panel_module.NamedSelectionPanel()

    assert panel.mode_selector.itemText(0) == "Node"
    assert panel.mode_selector.itemText(1) == "Cell"
    assert [
        panel.operation_selector.itemText(index)
        for index in range(panel.operation_selector.count())
    ] == ["Replace", "Add", "Toggle", "Subtract"]
    assert panel.face_mode_button.text() == "Face (deferred)"
    assert panel.edge_mode_button.text() == "Edge (deferred)"
    assert not panel.face_mode_button.isEnabled()
    assert not panel.edge_mode_button.isEnabled()
    assert "not supported" in panel.face_mode_button.toolTip().lower()
    assert panel.selected_count_label.text() == "Selected: 0"
    assert panel.clear_button.isEnabled()
    assert panel.invert_button.text() == "Invert"
    assert panel.create_button.text() == "Create"
    assert panel.rename_button.text() == "Rename"
    assert panel.replace_button.text() == "Replace Targets"
    assert panel.delete_button.text() == "Delete"
    panel.set_current_selection(
        count=2,
        resolution_state="RESOLVED",
        status="Two nodes selected.",
        metadata={
            "entity_kind": "node",
            "entity_ids": (0, 2),
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": "a" * 64,
        },
    )
    assert "node" in panel.metadata_label.text()
    assert "0, 2" in panel.metadata_label.text()
    assert "mesh-1" in panel.metadata_label.toolTip()
    assert "a" * 64 in panel.metadata_label.toolTip()

    panel.set_backend_available(False, "Interactive picking is unavailable.")
    assert "unavailable" in panel.status_label.text().lower()
    assert not panel.create_button.isEnabled()
    del app


def test_main_window_routes_pick_create_rename_replace_and_delete(app: object) -> None:
    from osw.gui.main_window import MainWindow

    factory = GuiPickingFactory()
    window = MainWindow(scene_renderer_factory=factory)
    panel = window.named_selection_panel
    controller: ActiveSceneController = window.active_scene_controller

    window._store_imported_mesh_for_viewer(_mesh(), mesh_ref="mesh-1")
    panel.mode_selector.setCurrentText("Node")
    fingerprint = controller.current_mesh_fingerprint
    assert fingerprint is not None
    factory.session.emit_pick(
        {
            "generation": controller.generation,
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": fingerprint.digest,
            "entity_kind": "node",
            "backend_index": 1,
            "intent": "replace",
        }
    )

    assert panel.selected_count_label.text() == "Selected: 1"
    assert "RESOLVED" in panel.current_resolution_label.text()

    panel.operation_selector.setCurrentText("Add")
    factory.session.emit_pick(
        {
            "generation": controller.generation,
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": fingerprint.digest,
            "entity_kind": "node",
            "backend_index": 2,
        }
    )
    assert panel.selected_count_label.text() == "Selected: 2"
    assert "1, 2" in panel.metadata_label.text()

    panel.name_input.setText("Picked Nodes")
    panel.create_button.click()
    assert len(window.current_project.selections) == 1
    created = window.current_project.selections[0]
    stable_id = created.id
    assert stable_id.startswith("selection-")
    assert created.name == "Picked Nodes"
    assert created.targets[0].locator is not None
    assert created.targets[0].locator.entity_ids == (1, 2)
    assert any(call[0] == "named" for call in factory.session.calls)
    tree_item = window.project_tree_panel.named_selection_item(stable_id)
    assert tree_item is not None
    assert (
        window.project_tree_panel.item_payload(tree_item)["selection_id"] == stable_id
    )
    window.project_tree.setCurrentItem(tree_item)
    assert controller.active_named_selection_ids == (stable_id,)
    assert any(call[0] == "active_named" for call in factory.session.calls)

    panel.selection_list.setCurrentRow(0)
    panel.name_input.setText("Renamed Nodes")
    panel.rename_button.click()
    assert window.current_project.selections[0].id == stable_id
    assert window.current_project.selections[0].name == "Renamed Nodes"

    factory.session.emit_pick(
        {
            "generation": controller.generation,
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": fingerprint.digest,
            "entity_kind": "node",
            "backend_index": 2,
            "intent": "replace",
        }
    )
    panel.selection_list.setCurrentRow(0)
    panel.replace_button.click()
    assert window.current_project.selections[0].id == stable_id
    assert window.current_project.selections[0].targets[0].locator.entity_ids == (2,)
    controller.set_active_named_selection_ids(())
    panel.clear_named_selection(emit=False)
    window.project_tree_panel.clear_named_selection(emit=False)
    factory.session.emit_pick(
        {
            "generation": controller.generation,
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": fingerprint.digest,
            "entity_kind": "node",
            "backend_index": 2,
            "intent": "replace",
        }
    )
    assert controller.active_named_selection_ids == (stable_id,)
    assert window.project_tree_panel.current_named_selection_id() == stable_id

    panel.selection_list.setCurrentRow(0)
    panel.delete_button.click()
    assert window.current_project.selections == []
    assert "Deleted" in panel.status_label.text()

    window.close()
    del app


def test_named_selection_save_reopen_exact_restore_and_stale_replacement(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.core.project_io import load_project
    from osw.core.selection_resolution import ResolutionState
    from osw.gui.main_window import MainWindow

    project_path = tmp_path / "named-selection.osw.json"
    first_factory = GuiPickingFactory()
    window = MainWindow(
        scene_renderer_factory=first_factory,
        project_save_path_picker=lambda: str(project_path),
    )
    window._store_imported_mesh_for_viewer(_mesh(), mesh_ref="mesh-1")
    controller: ActiveSceneController = window.active_scene_controller
    fingerprint = controller.current_mesh_fingerprint
    assert fingerprint is not None
    controller.set_pick_mode("node")
    for backend_index, intent in ((0, "replace"), (2, "add")):
        first_factory.session.emit_pick(
            {
                "generation": controller.generation,
                "mesh_ref": "mesh-1",
                "mesh_fingerprint": fingerprint.digest,
                "entity_kind": "node",
                "backend_index": backend_index,
                "intent": intent,
            }
        )
    window._on_create_named_selection("Persisted Nodes", "exact mesh only")
    selection_id = window.current_project.selections[0].id
    window._on_named_selection_activated(selection_id)

    assert window.save_project_as()
    assert project_path.is_file()
    window.close()

    reopened_project = load_project(project_path)
    second_factory = GuiPickingFactory()
    reopened = MainWindow(
        project=reopened_project, scene_renderer_factory=second_factory
    )
    reopened._store_imported_mesh_for_viewer(_mesh(), mesh_ref="mesh-1")
    reopened_controller: ActiveSceneController = reopened.active_scene_controller

    assert reopened_controller.named_selection_resolutions[selection_id].state is (
        ResolutionState.RESOLVED
    )
    assert reopened_controller.active_named_selection_ids == (selection_id,)
    assert any(call[0] == "active_named" for call in second_factory.session.calls)
    tree_item = reopened.project_tree_panel.named_selection_item(selection_id)
    assert tree_item is not None
    assert tree_item.text(1) == "RESOLVED"

    reopened.central_viewport_panel.set_mesh(_mesh(), mesh_ref="mesh-1")
    assert reopened_controller.named_selection_resolutions[selection_id].state is (
        ResolutionState.RESOLVED
    )
    assert any(
        call[0] == "active_named" and call[-1] == reopened_controller.generation
        for call in second_factory.session.calls
    )

    reopened.central_viewport_panel.set_mesh(_mesh(moved=True), mesh_ref="mesh-1")
    assert reopened_controller.named_selection_resolutions[selection_id].state is (
        ResolutionState.STALE
    )
    assert reopened_controller.named_selection_resolutions[
        selection_id
    ].reason_code == ("MESH_FINGERPRINT_MISMATCH")
    assert reopened_controller.active_named_selection_ids == (selection_id,)
    assert (
        reopened.project_tree_panel.named_selection_item(selection_id).text(1)
        == "STALE"
    )
    assert ("remove_active_named", selection_id) in second_factory.session.calls

    reopened.close()
    del app


def test_escape_clear_keeps_hover_and_committed_state_distinct(app: object) -> None:
    panel_module = import_module("osw.gui.widgets.named_selection_panel")
    panel = panel_module.NamedSelectionPanel()
    clear_calls: list[bool] = []
    panel.clearRequested.connect(lambda: clear_calls.append(True))

    panel.set_current_selection(
        count=2,
        resolution_state="RESOLVED",
        status="Two nodes selected.",
    )
    panel.clear_button.click()

    assert clear_calls == [True]
    assert "Hover" in panel.hover_semantics_label.text()
    assert "Current" in panel.hover_semantics_label.text()
    del app
