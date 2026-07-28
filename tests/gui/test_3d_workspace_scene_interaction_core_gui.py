"""Offscreen GUI tests for the central interactive 3D workspace host."""

from __future__ import annotations

import importlib.util
import os
from types import SimpleNamespace

import pytest

from osw.gui.workspace_scene_controller import (
    ActiveSceneController,
    SceneRendererInitializationError,
)
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


def _mesh(*, x_offset: float = 0.0) -> MeshData:
    return MeshData(
        points=(
            (x_offset, 0.0, 0.0),
            (x_offset + 1.0, 0.0, 0.0),
            (x_offset, 1.0, 0.0),
        ),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


class HostedRecordingSession:
    backend_kind = "fake-interactive"
    capabilities = frozenset(
        {
            "interactive",
            "hosted-widget",
            "camera",
            "representation",
            "semantic-visibility",
            "axes",
            "clipping",
        }
    )

    def __init__(self) -> None:
        assert QtWidgets is not None
        self.widget = QtWidgets.QWidget()
        self.widget.setObjectName("fakeQtInteractor")
        self.calls: list[tuple[object, ...]] = []
        self.actors: dict[str, object] = {}
        self.close_calls = 0

    @property
    def hosted_widget(self) -> object:
        return self.widget

    def clear(self) -> None:
        self.calls.append(("clear",))
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
        self.calls.append(("request_render",))

    def fit_to_scene(self) -> None:
        self.calls.append(("fit",))

    def set_camera_preset(self, preset: str) -> None:
        self.calls.append(("camera", preset))

    def set_interaction_mode(self, mode: str) -> None:
        self.calls.append(("interaction", mode))

    def set_axes_visible(self, visible: bool) -> None:
        self.calls.append(("axes", visible))

    def set_representation(self, mode: str) -> None:
        self.calls.append(("representation", mode))

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.calls.append(("visible", semantic_id, visible))

    def isolate_actor(self, semantic_id: str) -> None:
        self.calls.append(("isolate", semantic_id))

    def show_all_actors(self) -> None:
        self.calls.append(("show_all",))

    def enable_clipping(self, axis: str, origin: float) -> None:
        self.calls.append(("clip_enable", axis, origin))

    def update_clipping(self, axis: str, origin: float) -> None:
        self.calls.append(("clip_update", axis, origin))

    def clear_clipping(self) -> None:
        self.calls.append(("clip_clear",))

    def close(self) -> None:
        self.close_calls += 1


class HostedRecordingFactory:
    backend_kind = HostedRecordingSession.backend_kind
    capabilities = HostedRecordingSession.capabilities

    def __init__(self) -> None:
        self.host_parent: object | None = None
        self.sessions: list[HostedRecordingSession] = []

    def set_host_parent(self, parent: object) -> None:
        self.host_parent = parent

    def create_session(self) -> HostedRecordingSession:
        session = HostedRecordingSession()
        self.sessions.append(session)
        return session


def test_central_panel_hosts_session_widget_and_routes_toolbar_controls(
    app: object,
) -> None:
    from osw.gui.widgets.viewport_placeholder import CentralViewportPanel

    factory = HostedRecordingFactory()
    controller = ActiveSceneController(factory)
    panel = CentralViewportPanel(scene_controller=controller)
    session = factory.sessions[0]

    assert panel.interactive_available is True
    assert panel.hosted_widget is session.widget
    assert session.widget.parent() is panel.renderer_host
    assert panel.diagnostic_label.isHidden()

    panel.set_mesh(_mesh(), mesh_ref="mesh-1")
    panel.toolbar.tool_buttons["Fit"].click()
    panel.toolbar.camera_selector.setCurrentText("Front")
    panel.toolbar.representation_selector.setCurrentText("Wireframe")
    panel.toolbar.axes_button.click()
    panel.toolbar.actor_selector.setCurrentText("Wireframe")
    panel.toolbar.actor_visibility_button.click()
    panel.toolbar.isolate_button.click()
    panel.toolbar.show_all_button.click()
    panel.toolbar.clip_axis_selector.setCurrentText("Z")
    panel.toolbar.clip_origin_input.setValue(0.5)
    panel.toolbar.tool_buttons["Section"].click()
    panel.toolbar.clip_origin_input.setValue(0.75)
    panel.toolbar.tool_buttons["Section"].click()

    assert ("fit",) in session.calls
    assert ("camera", "front") in session.calls
    assert ("representation", "wireframe") in session.calls
    assert ("axes", False) in session.calls
    assert ("visible", "wireframe", False) in session.calls
    assert ("isolate", "wireframe") in session.calls
    assert ("show_all",) in session.calls
    assert ("clip_enable", "z", 0.5) in session.calls
    assert ("clip_update", "z", 0.75) in session.calls
    assert ("clip_clear",) in session.calls
    del app


class FailingFactory:
    backend_kind = "pyvistaqt"
    capabilities = HostedRecordingFactory.capabilities

    def set_host_parent(self, _parent: object) -> None:
        return None

    def create_session(self) -> HostedRecordingSession:
        raise SceneRendererInitializationError("PyVistaQt initialization failed.")


def test_central_panel_shows_explicit_fallback_and_disables_controls(
    app: object,
) -> None:
    from osw.gui.widgets.viewport_placeholder import CentralViewportPanel

    controller = ActiveSceneController(FailingFactory())
    panel = CentralViewportPanel(scene_controller=controller)

    assert panel.interactive_available is False
    assert panel.hosted_widget is None
    assert panel.viewport.isVisibleTo(panel)
    assert "Interactive 3D unavailable" in panel.diagnostic_label.text()
    assert "PyVistaQt initialization failed" in panel.diagnostic_label.text()
    assert all(
        not widget.isEnabled()
        for widget in panel.toolbar.interactive_control_widgets()
    )
    del app


def test_main_window_central_surface_and_legacy_dialog_share_one_session(
    app: object,
) -> None:
    from osw.gui.main_window import MainWindow

    factory = HostedRecordingFactory()
    window = MainWindow(scene_renderer_factory=factory)

    window._store_imported_mesh_for_viewer(_mesh(), mesh_ref="mesh-1")
    assert len(factory.sessions) == 1
    assert set(factory.sessions[0].actors) == {"base_mesh", "wireframe"}

    window.open_mesh_viewer()
    assert window.mesh_viewer is not None
    assert window.mesh_viewer._adapter is window.active_scene_controller
    window.mesh_viewer.load_mesh_preview()

    assert len(factory.sessions) == 1
    assert set(factory.sessions[0].actors) == {"base_mesh", "wireframe"}

    window._store_imported_mesh_for_viewer(
        _mesh(x_offset=2.0),
        mesh_ref="mesh-2",
    )
    assert len(factory.sessions) == 1
    assert set(factory.sessions[0].actors) == {"base_mesh", "wireframe"}
    assert factory.sessions[0].calls.count(("clear",)) == 2

    window.close()
    assert factory.sessions[0].close_calls == 1
    del app
