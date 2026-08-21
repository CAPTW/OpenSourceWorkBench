"""Offscreen GUI contracts for transient Mesh Diagnostics."""

from __future__ import annotations

import ast
import os
import subprocess
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6 import QtWidgets

from osw.core.project_schema import Project, ProjectMetadata
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)
from osw.mesh.mesh_model import MeshCellBlock, MeshData


@pytest.fixture(scope="module")
def app() -> QtWidgets.QApplication:
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _api() -> tuple[object, object]:
    try:
        return (
            import_module("osw.gui.mesh_diagnostics_view_model"),
            import_module("osw.gui.widgets.mesh_diagnostics_panel"),
        )
    except ModuleNotFoundError:
        pytest.fail("Mesh Diagnostics GUI modules are missing", pytrace=False)


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )


class _Provider:
    provider_schema = "osw.mesh_quality.provider.gui-fixture.v1"
    provider_version = "1"

    def evaluate(self, _mesh_data: MeshData) -> tuple[float, ...]:
        return (0.25,)


def _analyze(mesh: MeshData, **kwargs: object) -> object:
    from osw.mesh.quality import analyze_mesh_cell_quality

    return analyze_mesh_cell_quality(
        mesh,
        threshold=float(kwargs.get("threshold", 0.0)),
        provider=_Provider(),
    )


class GuiDiagnosticsSession:
    backend_kind = "fake-gui-diagnostics"
    capabilities = frozenset(
        {
            "mesh-preview",
            "semantic-actors",
            "semantic-visibility",
            "hosted-widget",
            "mesh-quality-overlays",
        }
    )

    def __init__(self) -> None:
        self.widget = QtWidgets.QWidget()
        self.actors: dict[str, object] = {}

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

    def set_representation(self, _mode: str) -> None:
        return None

    def set_actor_visible(self, _semantic_id: str, _visible: bool) -> None:
        return None

    def disable_picking(self) -> None:
        return None

    def close(self) -> None:
        self.actors.clear()


class GuiDiagnosticsFactory:
    backend_kind = GuiDiagnosticsSession.backend_kind
    capabilities = GuiDiagnosticsSession.capabilities

    def __init__(self) -> None:
        self.session = GuiDiagnosticsSession()

    def set_host_parent(self, _parent: object) -> None:
        return None

    def create_session(self) -> GuiDiagnosticsSession:
        return self.session


def test_panel_shows_preview_metric_table_and_validates_threshold(
    app: QtWidgets.QApplication,
) -> None:
    view_api, panel_api = _api()
    quality = import_module("osw.mesh.quality")
    analysis = quality.analyze_mesh_cell_quality(_mesh(), provider=_Provider())
    view_model = view_api.build_mesh_diagnostics_view_model(
        analysis,
        threshold=0.3,
        mesh_label="active-mesh",
        renderer_available=True,
    )
    panel = panel_api.MeshDiagnosticsPanel()

    panel.set_view_model(view_model)

    assert panel.objectName() == "oswMeshDiagnosticsPanel"
    assert panel.metric_label.text() == "Scaled Jacobian"
    assert "negative values indicate inverted" in panel.metric_claim_label.text().lower()
    assert "not a universal solver-acceptance standard" in (panel.metric_claim_label.text().lower())
    assert panel.node_count_label.text() == "3"
    assert panel.cell_count_label.text() == "1"
    assert panel.bad_count_label.text() == "1 (100.0%)"
    panel.highlight_check.setChecked(True)
    panel.isolate_check.setChecked(True)
    panel.set_view_model(view_model)
    assert panel.highlight_check.isChecked() is False
    assert panel.isolate_check.isChecked() is False
    assert panel.table.rowCount() == 1
    assert panel.table.item(0, 0).text() == "0:0"
    assert panel.table.item(0, 3).text() == "EVALUATED"
    assert panel.highlight_check.isEnabled()
    assert panel.isolate_check.isEnabled()

    thresholds: list[float] = []
    panel.thresholdChanged.connect(thresholds.append)
    panel.threshold_edit.setText("nan")
    panel.apply_threshold_button.click()
    assert thresholds == []
    assert "finite" in panel.status_label.text().lower()
    panel.threshold_edit.setText("3.5")
    panel.apply_threshold_button.click()
    assert thresholds == []
    assert "within [-1, 1]" in panel.status_label.text()
    panel.threshold_edit.setText("0.4")
    panel.apply_threshold_button.click()
    assert thresholds == [0.4]
    assert "repair" in panel.deferred_scope_label.text().lower()
    del app


def test_main_window_routes_transient_actions_without_dirtying_or_writing(
    app: QtWidgets.QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _api()
    from osw.gui.main_window import MainWindow

    save_calls: list[object] = []
    factory = GuiDiagnosticsFactory()
    project = Project(metadata=ProjectMetadata(name="Diagnostics"))
    window = MainWindow(
        project=project,
        scene_renderer_factory=factory,
        project_saver=lambda *_args: save_calls.append(object()),
        mesh_quality_analyzer=_analyze,
        mesh_diagnostics_async=False,
    )
    selections_before = tuple(window.current_project.selections)
    setup_before = window.current_project.primary_physics
    prior_cwd = Path.cwd()
    os.chdir(tmp_path)
    process_calls: list[object] = []
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

    try:
        window.active_scene_controller.load_mesh(
            _mesh(),
            mesh_input_ref("mesh-1"),
            scene_view_state_from_toggles(),
        )
        window.mesh_diagnostics_panel.analyze_button.click()
        assert window.mesh_diagnostics_panel.table.rowCount() == 1
        assert window.project_dirty is False

        window.mesh_diagnostics_panel.threshold_edit.setText("0.3")
        window.mesh_diagnostics_panel.apply_threshold_button.click()
        window.mesh_diagnostics_panel.highlight_check.setChecked(True)
        window.mesh_diagnostics_panel.isolate_check.setChecked(True)
        window.mesh_diagnostics_panel.restore_button.click()
        window.mesh_diagnostics_panel.clear_button.click()

        assert window.current_project.selections == list(selections_before)
        assert window.current_project.primary_physics is setup_before
        assert window.project_dirty is False
        assert save_calls == []
        assert process_calls == []
        assert list(tmp_path.iterdir()) == []

        old_controller = window.active_scene_controller
        window._replace_active_scene_controller()
        assert old_controller is not window.active_scene_controller
        assert window.mesh_diagnostics_panel.analysis_state_label.text() == "Not evaluated."
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


def test_renderer_fallback_keeps_metadata_and_table_with_explicit_diagnostic(
    app: QtWidgets.QApplication,
) -> None:
    _api()
    from osw.gui.main_window import MainWindow

    window = MainWindow(
        project=Project(metadata=ProjectMetadata(name="Fallback")),
        scene_renderer_factory=FailingFactory(),
        mesh_quality_analyzer=_analyze,
        mesh_diagnostics_async=False,
    )
    try:
        window.active_scene_controller.load_mesh(
            _mesh(),
            mesh_input_ref("mesh-1"),
            scene_view_state_from_toggles(),
        )
        window.mesh_diagnostics_panel.analyze_button.click()

        assert window.mesh_diagnostics_panel.table.rowCount() == 1
        assert not window.mesh_diagnostics_panel.highlight_check.isEnabled()
        assert not window.mesh_diagnostics_panel.isolate_check.isEnabled()
        assert "unavailable" in window.mesh_diagnostics_panel.status_label.text().lower()
        assert window.project_dirty is False
    finally:
        window.close()
    del app


def test_mesh_diagnostics_gui_paths_have_no_solver_runner_or_file_output() -> None:
    _api()
    paths = (
        Path("src/osw/gui/mesh_diagnostics_view_model.py"),
        Path("src/osw/gui/widgets/mesh_diagnostics_panel.py"),
    )
    forbidden_imports = {
        "subprocess",
        "osw.solvers",
        "ExternalCommandRunner",
        "RunManager",
    }
    forbidden_calls = {"write_text", "write_bytes", "open"}
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: set[str] = set()
        calls: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
        assert forbidden_imports.isdisjoint(imported)
        assert forbidden_calls.isdisjoint(calls)
