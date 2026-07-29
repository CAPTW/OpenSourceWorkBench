"""3D-workspace staged scene screenshot caption/record management tests.

These tests validate transient caption editing and per-record removal for staged
scene screenshot records, plus the monotonic record-id guard, using fake scene
adapters and explicit path/caption providers. No live PyVista/VTK render, solver
execution, parser execution, mesh generation, or project auto-save is required.
Staged records stay transient and are never serialized to ProjectSchema.
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
    """Fake adapter that optionally writes a dummy screenshot file."""

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


def _capture_ids(window: object) -> list[str]:
    return [record.id for record in window.scene_screenshot_candidates()]


def _scene_section(summary: object) -> Any | None:
    for section in getattr(summary, "sections", ()):
        if getattr(section, "section_id", "") == "scene-screenshots":
            return section
    return None


# -- caption editing --------------------------------------------------------


def test_caption_edit_updates_record_and_preserves_other_fields(
    app: object, tmp_path: Path
) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    panel.capture_button.click()

    before = window.scene_screenshot_candidates()[0]
    panel.staged_screenshots_list.setCurrentRow(0)
    panel._prompt_scene_screenshot_caption = lambda current: "Iso view"
    panel.edit_caption_button.click()

    after = window.scene_screenshot_candidates()[0]
    assert after.caption == "Iso view"
    assert after.id == before.id
    assert after.path == before.path
    assert after.mesh_ref == before.mesh_ref
    assert after.scene_state == before.scene_state
    assert after.created_by == before.created_by
    assert "Updated staged scene screenshot caption." in panel.status_label.text()
    assert any("Iso view" in row for row in _staged_rows(panel))


def test_empty_caption_is_valid(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    panel.capture_button.click()

    panel.staged_screenshots_list.setCurrentRow(0)
    panel._prompt_scene_screenshot_caption = lambda current: ""
    panel.edit_caption_button.click()

    assert window.scene_screenshot_candidates()[0].caption == ""
    assert any("(no caption)" in row for row in _staged_rows(panel))


def test_caption_appears_in_preview_and_export(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    panel.capture_button.click()
    panel.staged_screenshots_list.setCurrentRow(0)
    panel._prompt_scene_screenshot_caption = lambda current: "Iso temperature"
    panel.edit_caption_button.click()
    window._confirm_persist_scene_screenshots = lambda count: True
    assert window.persist_staged_scene_screenshots() == 1

    preview_summary = window.generate_report_preview()
    section = _scene_section(preview_summary)
    assert section is not None
    assert any("Iso temperature" in block for block in section.content_blocks)

    output = window.export_current_report(output_path=tmp_path / "report.html")
    assert "Iso temperature" in output.read_text(encoding="utf-8")


def test_edit_caption_prompt_cancel_leaves_record_unchanged(
    app: object, tmp_path: Path
) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    panel.capture_button.click()

    panel.staged_screenshots_list.setCurrentRow(0)
    panel._prompt_scene_screenshot_caption = lambda current: None  # cancelled
    panel.edit_caption_button.click()

    assert window.scene_screenshot_candidates()[0].caption is None


# -- per-record removal + monotonic ids -------------------------------------


def test_remove_one_keeps_others(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    paths = iter([str(tmp_path / f"s{index}.png") for index in range(3)])
    window._pick_scene_screenshot_target_path = lambda: next(paths)
    panel.capture_button.click()
    panel.capture_button.click()
    panel.capture_button.click()

    assert _capture_ids(window) == [
        "scene-screenshot-1",
        "scene-screenshot-2",
        "scene-screenshot-3",
    ]

    panel.staged_screenshots_list.setCurrentRow(1)
    panel.remove_screenshot_button.click()

    assert _capture_ids(window) == ["scene-screenshot-1", "scene-screenshot-3"]
    assert panel.screenshot_status_label.text() == "Report screenshots staged: 2"
    assert "Removed staged scene screenshot." in panel.status_label.text()


def test_remove_then_capture_does_not_reuse_id(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    paths = iter([str(tmp_path / f"s{index}.png") for index in range(5)])
    window._pick_scene_screenshot_target_path = lambda: next(paths)
    panel.capture_button.click()  # scene-screenshot-1
    panel.capture_button.click()  # scene-screenshot-2

    panel.staged_screenshots_list.setCurrentRow(0)
    panel.remove_screenshot_button.click()  # remove scene-screenshot-1
    panel.capture_button.click()  # must NOT reuse scene-screenshot-2

    ids = _capture_ids(window)
    assert ids == ["scene-screenshot-2", "scene-screenshot-3"]
    assert len(set(ids)) == len(ids)


def test_bulk_clear_still_works(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    paths = iter([str(tmp_path / "a.png"), str(tmp_path / "b.png")])
    window._pick_scene_screenshot_target_path = lambda: next(paths)
    panel.capture_button.click()
    panel.capture_button.click()
    assert len(window.scene_screenshot_candidates()) == 2

    panel.clear_screenshots_button.click()
    assert window.scene_screenshot_candidates() == ()
    assert panel.screenshot_status_label.text() == (
        "No scene screenshots staged for the next report export."
    )


# -- selection / diagnostics / caveat ---------------------------------------


def test_edit_remove_buttons_enable_only_on_selection(
    app: object, tmp_path: Path
) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    panel.capture_button.click()

    assert not panel.edit_caption_button.isEnabled()
    assert not panel.remove_screenshot_button.isEnabled()

    panel.staged_screenshots_list.setCurrentRow(0)
    assert panel.edit_caption_button.isEnabled()
    assert panel.remove_screenshot_button.isEnabled()


def test_edit_and_remove_without_selection_are_friendly(
    app: object, tmp_path: Path
) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    panel.capture_button.click()
    panel.staged_screenshots_list.setCurrentRow(-1)

    panel._on_edit_caption_requested()
    assert "Select a staged scene screenshot first." in panel.status_label.text()
    panel._on_remove_screenshot_requested()
    assert "Select a staged scene screenshot first." in panel.status_label.text()
    # Nothing was mutated by the friendly no-op.
    assert len(window.scene_screenshot_candidates()) == 1


def test_local_artifact_caveat_remains_visible(app: object) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.open_mesh_viewer()
    caveat = window.mesh_viewer.screenshot_caveat_label.text()
    assert "local report artifacts only" in caveat
    assert "not validation evidence" in caveat
    assert "release assets" in caveat


# -- boundaries -------------------------------------------------------------


def test_no_staged_preview_export_unchanged(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")

    preview = window.generate_report_preview()
    assert _scene_section(preview) is None

    output = window.export_current_report(output_path=tmp_path / "report.html")
    assert "3D Scene Screenshots" not in output.read_text(encoding="utf-8")


def test_management_does_not_mutate_project_or_summary_figures(
    app: object, tmp_path: Path
) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    before_project = window.current_project.to_dict()
    baseline_figures = len(window.build_current_report_summary().figures)
    panel = window.mesh_viewer
    paths = iter([str(tmp_path / "a.png"), str(tmp_path / "b.png")])
    window._pick_scene_screenshot_target_path = lambda: next(paths)
    panel.capture_button.click()
    panel.capture_button.click()

    panel.staged_screenshots_list.setCurrentRow(0)
    panel._prompt_scene_screenshot_caption = lambda current: "Cap"
    panel.edit_caption_button.click()
    panel.staged_screenshots_list.setCurrentRow(1)
    panel.remove_screenshot_button.click()

    preview = window.generate_report_preview()

    # No ProjectSchema mutation and no project auto-save through the flow.
    assert window.current_project.to_dict() == before_project
    # Scene screenshots never leak into summary.figures.
    assert len(preview.figures) == baseline_figures
    assert not any(
        getattr(figure, "metadata", {}).get("kind") == "scene_screenshot"
        for figure in preview.figures
    )
