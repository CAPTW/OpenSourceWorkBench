"""Offscreen GUI tests for entity picking and NamedSelection management."""

from __future__ import annotations

import importlib.util
import os
from importlib import import_module
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


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
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

    def close(self) -> None:
        self.close_calls += 1

    def emit_pick(self, event: dict[str, object]) -> object:
        assert callable(self.callback)
        return self.callback(event)


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
    assert panel.face_mode_button.text() == "Face (deferred)"
    assert panel.edge_mode_button.text() == "Edge (deferred)"
    assert not panel.face_mode_button.isEnabled()
    assert not panel.edge_mode_button.isEnabled()
    assert "not supported" in panel.face_mode_button.toolTip().lower()
    assert panel.selected_count_label.text() == "Selected: 0"
    assert panel.clear_button.isEnabled()
    assert panel.create_button.text() == "Create"
    assert panel.rename_button.text() == "Rename"
    assert panel.replace_button.text() == "Replace Targets"
    assert panel.delete_button.text() == "Delete"

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

    panel.name_input.setText("Picked Nodes")
    panel.create_button.click()
    assert len(window.current_project.selections) == 1
    created = window.current_project.selections[0]
    stable_id = created.id
    assert stable_id.startswith("selection-")
    assert created.name == "Picked Nodes"
    assert any(call[0] == "named" for call in factory.session.calls)

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

    panel.selection_list.setCurrentRow(0)
    panel.delete_button.click()
    assert window.current_project.selections == []
    assert "Deleted" in panel.status_label.text()

    window.close()
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
