"""Offscreen interactive-result binding, fallback, and dirty-state contracts."""

from __future__ import annotations

import os
import subprocess
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6 import QtWidgets

from osw.core.project_schema import Project, ProjectMetadata, ResultRef
from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.mesh.mesh_model import MeshCellBlock, MeshData


@pytest.fixture(scope="module")
def app() -> QtWidgets.QApplication:
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _api() -> tuple[object, object]:
    try:
        return (
            import_module("osw.gui.interactive_results_view_model"),
            import_module("osw.post.result_probe"),
        )
    except ModuleNotFoundError:
        pytest.fail("interactive-results GUI dependencies are missing", pytrace=False)


def _mesh(*, changed: bool = False) -> MeshData:
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (2.0 if changed else 1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        ),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )


def _dataset() -> ResultDataset:
    return ResultDataset(
        dataset_id="rd-1",
        source="memory",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                name="temperature",
                location="node",
                components=("value",),
                rows=(
                    ResultRow(0, {"value": 1.0}),
                    ResultRow(1, {"value": 2.0}),
                    ResultRow(2, {"value": 3.0}),
                ),
                unit="K",
            ),
            ResultField(
                name="displacement",
                location="node",
                components=("ux", "uy", "uz"),
                rows=(
                    ResultRow(0, {"ux": 1.0, "uy": 0.0, "uz": 0.0}),
                    ResultRow(1, {"ux": 0.0, "uy": 1.0, "uz": 0.0}),
                    ResultRow(2, {"ux": 0.0, "uy": 0.0, "uz": 1.0}),
                ),
                unit="mm",
            ),
        ),
        metadata={
            "title": "Interactive fixture",
            "mesh_length_unit": "mm",
            "field_semantics": {
                "displacement": {
                    "semantic_role": "displacement",
                    "quantity_dimension": "length",
                    "coordinate_system": "global_cartesian",
                }
            },
        },
    )


class ResultGuiSession:
    backend_kind = "fake-result-gui"
    capabilities = frozenset(
        {
            "mesh-preview",
            "semantic-actors",
            "semantic-visibility",
            "hosted-widget",
            "picking",
            "selection-overlays",
            "setup-overlays",
            "mesh-quality-overlays",
            "result-overlays",
        }
    )

    def __init__(self) -> None:
        self.widget = QtWidgets.QWidget()
        self.actors: dict[str, object] = {}
        self.visibility: dict[str, bool] = {}

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
        self.actors[semantic_id] = (payload, generation)
        return SimpleNamespace(rendered=True, diagnostics=())

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)

    def request_render(self) -> None:
        return None

    def set_representation(self, _mode: str) -> None:
        return None

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.visibility[semantic_id] = visible

    def set_pick_mode(self, _mode: str, _callback: object) -> None:
        return None

    def disable_picking(self) -> None:
        return None

    def clear_hover(self) -> None:
        return None

    def clear_current_selection(self) -> None:
        return None

    def close(self) -> None:
        self.actors.clear()


class ResultGuiFactory:
    backend_kind = ResultGuiSession.backend_kind
    capabilities = ResultGuiSession.capabilities

    def __init__(self) -> None:
        self.session = ResultGuiSession()

    def set_host_parent(self, _parent: object) -> None:
        return None

    def create_session(self) -> ResultGuiSession:
        return self.session


def _window(
    *,
    factory: object,
    confirmation: object,
    project_saver: object,
) -> object:
    from osw.gui.main_window import MainWindow

    project = Project(
        metadata=ProjectMetadata(name="Interactive Results"),
        results=[
            ResultRef(
                id="rd-1",
                name="Result dataset",
                metadata={"result_dataset_id": "rd-1"},
            )
        ],
    )
    window = MainWindow(
        project=project,
        scene_renderer_factory=factory,
        result_mesh_binding_confirmation=confirmation,
        project_saver=project_saver,
    )
    window.last_result_datasets = [_dataset()]
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window.mesh_viewer.set_result_dataset(_dataset())
    window.mesh_viewer.scalar_selector.setCurrentText("result: temperature")
    return window


def test_confirm_rebind_persists_v2_then_transient_controls_do_not_dirty_or_write(
    app: QtWidgets.QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _api()
    save_calls: list[object] = []
    process_calls: list[object] = []
    factory = ResultGuiFactory()
    window = _window(
        factory=factory,
        confirmation=lambda _message: True,
        project_saver=lambda *_args: save_calls.append(object()),
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: process_calls.append(object()),
    )
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *_args, **_kwargs: process_calls.append(object()),
    )
    prior_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        assert window.persist_mesh_viewer_result_binding() is True
        payload = window.current_project.results[0].metadata["mesh_binding"]
        assert payload["schema"] == "osw.result_mesh_binding.v2"
        assert len(payload["mesh_fingerprint"]) == 64
        assert window.project_dirty is True
        assert save_calls == []

        window._project_dirty = False
        panel = window.mesh_viewer
        assert panel.binding_schema_label.text() == "osw.result_mesh_binding.v2"
        assert panel.binding_state_label.text() == "RESOLVED"
        panel.scalar_component_selector.setCurrentText("value")
        panel.apply_scalar_button.click()
        panel.range_mode_selector.setCurrentText("MANUAL")
        panel.manual_min_input.setValue(0.0)
        panel.manual_max_input.setValue(5.0)
        panel.colorbar_toggle.setChecked(True)
        panel.apply_scalar_button.click()
        panel.vector_selector.setCurrentText("result vector: displacement")
        panel.glyph_toggle.setChecked(True)
        panel.glyph_max_count_input.setValue(2)
        panel.apply_vector_button.click()
        probe = panel.probe_result_entity("point", 1)
        table = panel.set_selected_result_entities("point", (2, 0))

        assert "result:scalar" in factory.session.actors
        assert "result:vector" in factory.session.actors
        assert "result:probe" in factory.session.actors
        assert "result:colorbar" in factory.session.actors
        assert panel.data_range_label.text() == "1 / 3"
        assert panel.applied_range_label.text() == "0 / 5"
        assert panel.vector_count_label.text().startswith("3 / 2 / 1 / 0")
        assert probe is not None and probe.value == 2.0
        assert table is not None and table.total_count == 2
        assert panel.selected_result_table.rowCount() == 2
        assert "point 1: 2 K" == panel.result_probe_label.text()
        assert window.project_dirty is False
        assert save_calls == []
        assert process_calls == []
        assert list(tmp_path.iterdir()) == []

        window.load_mesh_into_viewer(_mesh(changed=True), mesh_ref="mesh-1")
        assert not any(key.startswith("result:") for key in factory.session.actors)
        assert panel.binding_state_label.text() == "STALE"
        assert window.persist_mesh_viewer_result_binding() is False
        panel.rebind_result_button.click()
        assert panel.binding_state_label.text() == "RESOLVED"
        assert (
            window.current_project.results[0].metadata["mesh_binding"]["mesh_fingerprint"]
            != payload["mesh_fingerprint"]
        )
    finally:
        os.chdir(prior_cwd)
        window.close()
    del app


class FailingFactory:
    backend_kind = "pyvistaqt"
    capabilities = frozenset({"mesh-preview", "semantic-actors"})

    def set_host_parent(self, _parent: object) -> None:
        return None

    def create_session(self) -> object:
        from osw.gui.workspace_scene_controller import (
            SceneRendererInitializationError,
        )

        raise SceneRendererInitializationError("renderer backend unavailable")


def test_renderer_fallback_keeps_mapping_probe_and_table_but_disables_rendering(
    app: QtWidgets.QApplication,
) -> None:
    _api()
    window = _window(
        factory=FailingFactory(),
        confirmation=lambda _message: True,
        project_saver=lambda *_args: None,
    )
    try:
        assert window.persist_mesh_viewer_result_binding() is True
        panel = window.mesh_viewer
        panel.scalar_component_selector.setCurrentText("value")
        panel.apply_scalar_button.click()

        assert panel.binding_state_label.text() == "RESOLVED"
        assert panel.data_range_label.text() == "1 / 3"
        assert panel.apply_scalar_button.isEnabled() is False
        assert panel.apply_vector_button.isEnabled() is False
        assert "unavailable" in panel.result_status_label.text().lower()
        assert not any(
            key.startswith("result:") for key in window.active_scene_controller.actor_records
        )
    finally:
        window.close()
    del app


def test_result_tree_properties_controls_and_deformation_stay_synchronized(
    app: QtWidgets.QApplication,
) -> None:
    _api()
    factory = ResultGuiFactory()
    window = _window(
        factory=factory,
        confirmation=lambda _message: True,
        project_saver=lambda *_args: None,
    )
    try:
        assert window.persist_mesh_viewer_result_binding() is True
        panel = window.mesh_viewer
        tree = window.project_tree_panel

        required_accessible_controls = (
            panel.result_dataset_selector,
            panel.scalar_selector,
            panel.result_association_label,
            panel.scalar_component_selector,
            panel.contour_toggle,
            panel.range_mode_selector,
            panel.manual_min_input,
            panel.manual_max_input,
            panel.colormap_selector,
            panel.colorbar_toggle,
            panel.vector_selector,
            panel.glyph_toggle,
            panel.glyph_max_count_input,
            panel.vector_scale_mode_selector,
            panel.glyph_scale_input,
            panel.result_probe_label,
            panel.selected_result_table,
            panel.deformation_field_selector,
            panel.deformation_mode_selector,
            panel.deformation_scale_mode_selector,
            panel.deformation_scale_input,
            panel.apply_deformation_button,
            panel.reset_result_view_button,
        )
        assert all(widget.accessibleName() for widget in required_accessible_controls)
        assert all(widget.toolTip() for widget in required_accessible_controls)

        result_item = tree.result_item("rd-1")
        assert result_item is not None
        assert result_item.text(1) == "READY"
        assert result_item.childCount() == 2
        assert tree.select_result_field("rd-1", "displacement") is True
        app.processEvents()

        assert panel.selected_result_field_id() == "displacement"
        assert panel.result_association_label.text() == "Association: point"
        assert {"x", "y", "z", "magnitude"}.issubset(
            {
                panel.scalar_component_selector.itemText(index)
                for index in range(panel.scalar_component_selector.count())
            }
        )
        assert "result:scalar" not in factory.session.actors
        rows = window.properties_panel.interactive_result_property_rows()
        assert rows["Result ID"] == "rd-1"
        assert rows["Binding status"] == "READY"
        assert rows["Field ID"] == "displacement"
        assert rows["Association"] == "point"
        assert rows["Components"] == "ux, uy, uz"
        assert rows["Units"] == "mm"
        assert rows["Deformation eligible"] == "yes"
        assert not window.properties_panel.interactive_result_properties_group.isHidden()

        assert panel.deformation_field_selector.currentText() == "displacement"
        panel.deformation_mode_selector.setCurrentText("DEFORMED")
        panel.deformation_scale_mode_selector.setCurrentText("MANUAL")
        panel.deformation_scale_input.setValue(2.0)
        panel.apply_deformation_button.click()
        assert "result:deformed" in factory.session.actors
        assert window.properties_panel.row_value("Deformation mode") == "DEFORMED"
        assert window.properties_panel.row_value("Deformation scale") == "2"

        panel.range_mode_selector.setCurrentText("MANUAL")
        panel.manual_min_input.setValue(5.0)
        panel.manual_max_input.setValue(1.0)
        assert panel.apply_scalar_button.isEnabled() is False
        panel.manual_max_input.setValue(10.0)
        assert panel.apply_scalar_button.isEnabled() is True

        panel.reset_result_view_button.click()
        assert not any(key.startswith("result:") for key in factory.session.actors)

        window.load_mesh_into_viewer(_mesh(changed=True), mesh_ref="mesh-1")
        stale_item = tree.result_item("rd-1")
        assert stale_item is not None
        assert stale_item.text(1) == "STALE_MESH"
        assert panel.apply_scalar_button.isEnabled() is False
        assert panel.apply_vector_button.isEnabled() is False
        assert panel.apply_deformation_button.isEnabled() is False
        assert "MESH_FINGERPRINT_MISMATCH" in panel.result_status_label.text()
    finally:
        window.close()
    del app
