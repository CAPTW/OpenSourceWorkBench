"""3D-workspace report screenshot workflow-UX tests (fake adapters, no render).

These tests validate the staged-screenshot count/list, the Clear action, and the
local-artifact caveat in the mesh viewer panel, plus the transient handoff into
report export. They use fake scene adapters and explicit path providers, so no
live PyVista/VTK render, solver execution, parser execution, mesh generation, or
project auto-save is required. Staged screenshots stay transient and are never
serialized to ProjectSchema.
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

_EMPTY_STATE = "No scene screenshots staged for the next report export."


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

    def __init__(self, write_image: bool = True) -> None:
        self.write_image = write_image
        self.export_calls: list[str] = []

    def load_mesh(self, mesh: MeshData, scene_input: Any, scene_state: Any) -> object:
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


def _window(*, app: object, adapter: object) -> object:
    from osw.gui.main_window import MainWindow

    assert app is not None
    return MainWindow(mesh_scene_adapter_factory=lambda: adapter)


def _staged_rows(panel: object) -> list[str]:
    widget = panel.staged_screenshots_list
    return [widget.item(index).text() for index in range(widget.count())]


# -- pure formatting -------------------------------------------------------


def test_staged_screenshot_rows_formatting() -> None:
    from osw.gui.widgets.mesh_viewer_panel import _staged_screenshot_rows

    assert _staged_screenshot_rows(()) == ()
    rows = _staged_screenshot_rows(
        (
            SceneScreenshotRecord(id="s1", path="/a/b/scene.png", caption="Iso view"),
            SceneScreenshotRecord(id="s2", path=""),
        )
    )
    assert rows[0] == "s1 - Iso view - scene.png"
    assert rows[1] == "s2 - (no caption) - (no image path)"


# -- panel presentation ----------------------------------------------------


def test_empty_state_and_caveat_visible(app: object) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.open_mesh_viewer()
    panel = window.mesh_viewer

    assert panel.screenshot_status_label.text() == _EMPTY_STATE
    caveat = panel.screenshot_caveat_label.text()
    assert "local report artifacts only" in caveat
    assert "not validation evidence" in caveat
    assert "release assets" in caveat
    assert _staged_rows(panel) == []
    assert not panel.clear_screenshots_button.isEnabled()


def test_clear_button_invokes_injected_clear_callback(app: object) -> None:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    assert app is not None
    panel = MeshViewerPanel(scene_adapter=RecordingSceneAdapter())
    records: list[SceneScreenshotRecord] = [SceneScreenshotRecord(id="s1", path="a.png")]
    calls: list[str] = []

    def _clear() -> None:
        calls.append("clear")
        records.clear()

    panel.set_scene_screenshot_candidates_provider(lambda: tuple(records))
    panel.set_clear_scene_screenshots_callback(_clear)

    assert panel.screenshot_status_label.text() == "Report screenshots staged: 1"
    assert panel.clear_screenshots_button.isEnabled()

    panel.clear_screenshots_button.click()

    assert calls == ["clear"]
    assert panel.screenshot_status_label.text() == _EMPTY_STATE
    assert not panel.clear_screenshots_button.isEnabled()


# -- MainWindow-driven workflow --------------------------------------------


def test_capture_updates_staged_count_and_list(app: object, tmp_path: Path) -> None:
    adapter = RecordingSceneAdapter()
    window = _window(app=app, adapter=adapter)
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    shot = tmp_path / "scene.png"
    window._pick_scene_screenshot_target_path = lambda: str(shot)

    assert panel.screenshot_status_label.text() == _EMPTY_STATE
    panel.capture_button.click()

    assert panel.screenshot_status_label.text() == "Report screenshots staged: 1"
    rows = _staged_rows(panel)
    assert len(rows) == 1
    assert "scene-screenshot-1" in rows[0]
    assert "scene.png" in rows[0]
    assert panel.clear_screenshots_button.isEnabled()


def test_clear_action_resets_count_via_main_window(app: object, tmp_path: Path) -> None:
    adapter = RecordingSceneAdapter()
    window = _window(app=app, adapter=adapter)
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    paths = iter([str(tmp_path / "a.png"), str(tmp_path / "b.png")])
    window._pick_scene_screenshot_target_path = lambda: next(paths)

    panel.capture_button.click()
    panel.capture_button.click()
    assert panel.screenshot_status_label.text() == "Report screenshots staged: 2"
    assert len(window.scene_screenshot_candidates()) == 2

    panel.clear_screenshots_button.click()

    # The MainWindow-owned clear callback ran: transient candidates are empty.
    assert window.scene_screenshot_candidates() == ()
    assert panel.screenshot_status_label.text() == _EMPTY_STATE
    assert _staged_rows(panel) == []
    assert not panel.clear_screenshots_button.isEnabled()
    assert "cleared staged scene screenshots" in panel.status_label.text().lower()


def test_passive_viewing_does_not_stage_screenshots(app: object) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer

    panel.load_mesh_preview()

    assert window.scene_screenshot_candidates() == ()
    assert panel.screenshot_status_label.text() == _EMPTY_STATE
    assert _staged_rows(panel) == []


def test_report_export_requires_persisted_and_leaves_project_unchanged(
    app: object, tmp_path: Path
) -> None:
    adapter = RecordingSceneAdapter()
    window = _window(app=app, adapter=adapter)
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    shot = tmp_path / "scene.png"
    window._pick_scene_screenshot_target_path = lambda: str(shot)
    window.mesh_viewer.capture_button.click()

    before = window.export_current_report(output_path=tmp_path / "before.html")
    assert "3D Scene Screenshots" not in before.read_text(encoding="utf-8")

    window._confirm_persist_scene_screenshots = lambda count: True
    assert window.persist_staged_scene_screenshots() == 1
    staged_project = window.current_project.to_dict()
    output = window.export_current_report(output_path=tmp_path / "report.html")
    html = output.read_text(encoding="utf-8")

    assert "3D Scene Screenshots" in html
    assert "scene.png" in html
    assert window.current_project.to_dict() == staged_project


def test_no_staged_records_keeps_report_unchanged(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")

    output = window.export_current_report(output_path=tmp_path / "report.html")
    html = output.read_text(encoding="utf-8")

    assert "3D Scene Screenshots" not in html
