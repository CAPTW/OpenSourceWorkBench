"""3D-workspace report screenshot GUI capture handoff tests.

These tests validate the explicit mesh-viewer capture action and the transient
candidate handoff into report export. They use fake scene adapters and explicit
path providers so no live PyVista/VTK render, solver execution, or project
auto-save is required.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.scene_model import SceneScreenshotRecord

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
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


class RecordingSceneAdapter:
    """Fake adapter that records export calls and optionally writes a dummy file."""

    def __init__(self, write_image: bool = False) -> None:
        self.write_image = write_image
        self.export_calls: list[str] = []

    def load_mesh(
        self,
        mesh: MeshData,
        scene_input: Any,
        scene_state: Any,
    ) -> object:
        return None

    def set_view_state(self, scene_state: Any) -> None:
        return None

    def export_screenshot_record(
        self,
        path: str,
        *,
        record_id: str,
        scene_state: Any,
        mesh: MeshData,
        mesh_ref: str | None = None,
        selection_ids: Sequence[str] = (),
        caption: str | None = None,
        created_by: str | None = None,
    ) -> SceneScreenshotRecord:
        self.export_calls.append(str(path))
        if self.write_image:
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n")
        return SceneScreenshotRecord(
            id=record_id,
            path=str(path),
            scene_state=scene_state,
            mesh_ref=mesh_ref,
            selection_ids=tuple(selection_ids),
            caption=caption,
            created_by=created_by,
        )


class MissingPyVistaAdapter:
    def load_mesh(self, mesh: MeshData, scene_input: Any, scene_state: Any) -> object:
        return None

    def set_view_state(self, scene_state: Any) -> None:
        return None

    def export_screenshot_record(self, path: str, **_kwargs: object) -> object:
        from osw.post.pyvista_scene import PyVistaUnavailableError

        raise PyVistaUnavailableError("PyVista is not installed.")


def _window(*, app: object, adapter: object) -> object:
    from osw.gui.main_window import MainWindow

    return MainWindow(mesh_scene_adapter_factory=lambda: adapter)


def test_capture_button_stages_scene_screenshot_for_report_export(
    app: object, tmp_path: Path
) -> None:
    adapter = RecordingSceneAdapter()
    window = _window(app=app, adapter=adapter)
    before = window.current_project.to_dict()

    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    shot_path = tmp_path / "scene.png"
    window._pick_scene_screenshot_target_path = lambda: str(shot_path)

    assert window.scene_screenshot_candidates() == ()
    window.mesh_viewer.capture_button.click()

    assert len(window.scene_screenshot_candidates()) == 1
    assert adapter.export_calls == [str(shot_path)]
    record = window.scene_screenshot_candidates()[0]
    assert record is not None
    assert record.mesh_ref == "mesh-1"
    assert (
        "captured scene screenshot" in window.mesh_viewer.status_label.text().lower()
    )

    output = window.export_current_report(output_path=tmp_path / "report.html")
    html = output.read_text(encoding="utf-8")

    assert "3D Scene Screenshots" in html
    assert "scene.png" in html
    assert "Scene screenshot image missing" in html
    assert window.current_project.to_dict() == before


def test_capture_without_mesh_does_not_stage_candidate(
    app: object, tmp_path: Path
) -> None:
    adapter = RecordingSceneAdapter()
    window = _window(app=app, adapter=adapter)
    window.open_mesh_viewer()

    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    window.mesh_viewer.capture_button.click()

    assert window.scene_screenshot_candidates() == ()
    status_text = window.mesh_viewer.status_label.text()
    assert "No mesh loaded" in status_text or "No active mesh is loaded" in status_text


def test_capture_failure_uses_friendly_diagnostics_and_no_crash(
    app: object, tmp_path: Path
) -> None:
    adapter = MissingPyVistaAdapter()
    window = _window(app=app, adapter=adapter)
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "missing-scene.png")

    window.mesh_viewer.capture_button.click()

    assert window.scene_screenshot_candidates() == ()
    assert "PyVista unavailable" in window.mesh_viewer.status_label.text()


def test_capture_candidates_can_be_cleared_before_export(app: object, tmp_path: Path) -> None:
    adapter = RecordingSceneAdapter()
    window = _window(app=app, adapter=adapter)

    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    paths = [tmp_path / "one.png", tmp_path / "two.png"]

    def _next_path() -> str:
        if not paths:
            return str(tmp_path / "unused.png")
        return str(paths.pop(0))

    window._pick_scene_screenshot_target_path = _next_path
    window.mesh_viewer.capture_button.click()
    window.mesh_viewer.capture_button.click()

    assert len(window.scene_screenshot_candidates()) == 2
    window.clear_scene_screenshot_candidates()
    assert window.scene_screenshot_candidates() == ()

    output = window.export_current_report(output_path=tmp_path / "report.html")
    html = output.read_text(encoding="utf-8")
    assert "3D Scene Screenshots" not in html
