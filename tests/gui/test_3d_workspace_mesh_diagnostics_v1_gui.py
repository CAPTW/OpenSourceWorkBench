"""Offscreen product flow for background mesh diagnostics and Project sync."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6 import QtWidgets

from osw.core.project_io import load_project, save_project
from osw.core.project_schema import Project, ProjectMetadata
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.mesh.quality import MeshDiagnosticsStatus, analyze_mesh_cell_quality


@pytest.fixture(scope="module")
def app() -> QtWidgets.QApplication:
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


class Provider:
    provider_schema = "osw.mesh_quality.provider.gui-fixture.v1"
    provider_version = "1"

    def evaluate(self, _mesh: MeshData) -> tuple[float, ...]:
        return (1.0, -1.0, 0.0)


def _analyze(mesh: MeshData, **kwargs: object) -> object:
    return analyze_mesh_cell_quality(
        mesh,
        threshold=float(kwargs.get("threshold", 0.0)),
        provider=Provider(),
    )


def _mesh(*, changed: bool = False) -> MeshData:
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.2 if changed else 1.0),
            (1.0, 1.0, 0.0),
        ),
        cells=(
            MeshCellBlock(
                "tetra",
                ((0, 1, 2, 3), (0, 2, 1, 3), (0, 1, 2, 4)),
            ),
        ),
    )


class Session:
    backend_kind = "fake-mesh-diagnostics-gui-v1"
    capabilities = frozenset(
        {
            "mesh-preview",
            "semantic-actors",
            "semantic-visibility",
            "hosted-widget",
            "selection-overlays",
            "mesh-quality-overlays",
        }
    )

    def __init__(self) -> None:
        self.widget = QtWidgets.QWidget()
        self.actors: dict[str, object] = {}
        self.visibility: dict[str, bool] = {}
        self.close_calls = 0

    @property
    def hosted_widget(self) -> object:
        return self.widget

    def clear(self) -> None:
        self.actors.clear()
        self.visibility.clear()

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        self.actors[semantic_id] = payload
        self.visibility[semantic_id] = True
        return SimpleNamespace(warnings=(), rendered=True, generation=generation)

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)
        self.visibility.pop(semantic_id, None)

    def request_render(self) -> None:
        return None

    def set_representation(self, _mode: str) -> None:
        return None

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.visibility[semantic_id] = visible

    def set_current_selection(
        self,
        _kind: str,
        _indices: tuple[int, ...],
        _generation: int,
    ) -> None:
        return None

    def clear_current_selection(self) -> None:
        return None

    def clear_hover(self) -> None:
        return None

    def disable_picking(self) -> None:
        return None

    def close(self) -> None:
        self.close_calls += 1
        self.clear()


class Factory:
    backend_kind = Session.backend_kind
    capabilities = Session.capabilities

    def __init__(self) -> None:
        self.sessions: list[Session] = []

    def set_host_parent(self, _parent: object) -> None:
        return None

    def create_session(self) -> Session:
        session = Session()
        self.sessions.append(session)
        return session


def _wait_until(
    app: QtWidgets.QApplication,
    predicate: object,
    *,
    timeout: float = 5.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():  # type: ignore[operator]
            return
        time.sleep(0.01)
    raise AssertionError("Timed out waiting for the GUI condition.")


def test_background_gui_tree_properties_named_selection_save_reopen_and_export(
    app: QtWidgets.QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from osw.gui.main_window import MainWindow

    process_calls: list[object] = []
    monkeypatch.setattr(subprocess, "run", lambda *_a, **_k: process_calls.append(object()))
    monkeypatch.setattr(subprocess, "Popen", lambda *_a, **_k: process_calls.append(object()))
    factory = Factory()
    window = MainWindow(
        project=Project(metadata=ProjectMetadata(name="Diagnostics v1")),
        scene_renderer_factory=factory,
        mesh_quality_analyzer=_analyze,
        mesh_diagnostics_async=True,
    )
    try:
        window.active_scene_controller.load_mesh(
            _mesh(),
            mesh_input_ref("mesh-diagnostics-v1"),
            scene_view_state_from_toggles(),
        )
        window.mesh_diagnostics_panel.analyze_button.click()
        assert window.active_scene_controller.mesh_quality_status is MeshDiagnosticsStatus.RUNNING
        _wait_until(
            app,
            lambda: window._mesh_diagnostics_thread is None
            and window.active_scene_controller.mesh_quality_status is MeshDiagnosticsStatus.READY,
        )

        panel = window.mesh_diagnostics_panel
        assert panel.metric_label.text() == "Scaled Jacobian"
        assert panel.table.rowCount() == 3
        assert panel.bad_count_label.text() == "2 (66.7%)"
        panel.range_mode.setCurrentText("Manual")
        panel.range_min_edit.setText("1")
        panel.range_max_edit.setText("1")
        assert panel.apply_range_button.isEnabled() is False
        panel.range_min_edit.setText("-1")
        assert panel.apply_range_button.isEnabled() is True
        assert window.project_dirty is False
        diagnostics_item = window.project_tree_panel.mesh_diagnostics_item()
        assert diagnostics_item is not None
        window.project_tree_panel.select_mesh_diagnostics()
        assert window.properties_panel.mesh_diagnostics_property_rows()["Bad"] == "2"

        panel.quality_check.setChecked(True)
        panel.highlight_check.setChecked(True)
        panel.filter_combo.setCurrentText("Hide bad")
        session = factory.sessions[-1]
        assert set(session.actors) >= {
            "mesh_quality",
            "mesh_quality_scalar_bar",
            "mesh_bad_elements",
            "mesh_diagnostic_good_elements",
        }
        assert session.visibility["base_mesh"] is False
        panel.filter_combo.setCurrentText("Clear filter")
        panel.select_bad_button.click()
        assert window.active_scene_controller.current_selection_target.locator.entity_ids == (
            "0:1",
            "0:2",
        )

        panel.named_selection_name.setText("Poor tetrahedra")
        panel.create_named_selection_button.click()
        assert window.project_dirty is True
        assert len(window.current_project.selections) == 1
        selection = window.current_project.selections[0]
        assert selection.name == "Poor tetrahedra"
        assert selection.targets[0].locator.entity_ids == ("0:1", "0:2")

        json_path = tmp_path / "mesh-diagnostics.json"
        csv_path = tmp_path / "mesh-diagnostics.csv"
        assert window.export_mesh_diagnostics("json", json_path) == json_path
        assert window.export_mesh_diagnostics("csv", csv_path) == csv_path
        assert json.loads(json_path.read_text(encoding="utf-8"))["schema"] == (
            "osw.mesh_diagnostics_report.v1"
        )
        assert "0:1" in csv_path.read_text(encoding="utf-8")

        project_path = tmp_path / "diagnostics.osw.json"
        saved = window._project_for_explicit_save()
        save_project(saved, project_path)
        reopened_project = load_project(project_path)
        assert reopened_project.selections[0].name == "Poor tetrahedra"
        assert reopened_project.active_scene is not None
        assert reopened_project.active_scene.mesh_quality_state is not None
        assert reopened_project.active_scene.mesh_quality_state.coloring_visible is True

        reopened = MainWindow(
            project=reopened_project,
            scene_renderer_factory=Factory(),
            mesh_quality_analyzer=_analyze,
            mesh_diagnostics_async=False,
        )
        try:
            reopened.active_scene_controller.load_mesh(
                _mesh(),
                mesh_input_ref("mesh-diagnostics-v1"),
                scene_view_state_from_toggles(),
            )
            assert (
                reopened.active_scene_controller.named_selection_resolutions[
                    selection.id
                ].state.value
                == "RESOLVED"
            )
            assert reopened.active_scene_controller.mesh_quality_analysis is not None
            reopened.active_scene_controller.load_mesh(
                _mesh(changed=True),
                mesh_input_ref("mesh-diagnostics-v1"),
                scene_view_state_from_toggles(),
            )
            assert (
                reopened.active_scene_controller.named_selection_resolutions[
                    selection.id
                ].state.value
                == "STALE"
            )
            assert reopened.active_scene_controller.mesh_quality_status is (
                MeshDiagnosticsStatus.STALE
            )
        finally:
            reopened.close()

        assert process_calls == []
    finally:
        window.close()
        _wait_until(app, lambda: window._mesh_diagnostics_thread is None)
    del app


def test_close_waits_for_background_diagnostics_worker_without_late_qt_mutation(
    app: QtWidgets.QApplication,
) -> None:
    from osw.gui.main_window import MainWindow
    from osw.gui.workspace_scene_controller import SceneLifecycleState

    def slow_analyze(mesh: MeshData, **kwargs: object) -> object:
        time.sleep(0.05)
        return _analyze(mesh, **kwargs)

    window = MainWindow(
        project=Project(metadata=ProjectMetadata(name="Diagnostics close")),
        scene_renderer_factory=Factory(),
        mesh_quality_analyzer=slow_analyze,
        mesh_diagnostics_async=True,
    )
    window.active_scene_controller.load_mesh(
        _mesh(),
        mesh_input_ref("mesh-diagnostics-v1"),
        scene_view_state_from_toggles(),
    )
    window.mesh_diagnostics_panel.analyze_button.click()
    assert window.active_scene_controller.mesh_quality_status is MeshDiagnosticsStatus.RUNNING

    assert window.close()
    _wait_until(app, lambda: window._mesh_diagnostics_thread is None)
    assert window.active_scene_controller.state is SceneLifecycleState.CLOSED
    del app
