"""3D-workspace preview/export parity tests for staged scene screenshots.

These tests validate that the right-panel report preview summary includes staged
scene screenshot artifacts in parity with exported report output while preserving
transient MainWindow ownership and no-project mutation.
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
    if QtWidgets is None:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


class RecordingSceneAdapter:
    """Fake adapter that optionally writes a dummy screenshot file."""

    def __init__(self, write_image: bool = False) -> None:
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


def _summary_section_titles(summary: object) -> tuple[str, ...]:
    return tuple(
        str(getattr(section, "title", "")) for section in getattr(summary, "sections", ())
    )


def _scene_screenshot_section(summary: object) -> Any | None:
    for section in getattr(summary, "sections", ()):
        if getattr(section, "section_id", "") == "scene-screenshots":
            return section
    return None


def test_preview_without_staged_screenshots_keeps_summary_unchanged(app: object) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    summary = window.generate_report_preview()

    assert "3D Scene Screenshots" not in _summary_section_titles(summary)
    assert (
        "3D Scene Screenshots"
        not in window.properties_panel.report_preview_panel.report_sections()
    )


def test_preview_includes_staged_scene_screenshot_section(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    window.mesh_viewer.capture_button.click()

    preview_summary = window.generate_report_preview()

    assert "3D Scene Screenshots" in _summary_section_titles(preview_summary)
    panel_sections = window.properties_panel.report_preview_panel.report_sections()
    assert "3D Scene Screenshots" in panel_sections

    section = _scene_screenshot_section(preview_summary)
    assert section is not None
    assert any("Image path: " in block for block in getattr(section, "content_blocks", ()))


def test_preview_screenshot_missing_image_warns_like_export(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "missing.png")
    window.mesh_viewer.capture_button.click()
    before_project = window.current_project.to_dict()

    preview_summary = window.generate_report_preview()
    section = _scene_screenshot_section(preview_summary)
    assert section is not None
    assert any("Scene screenshot image missing" in block for block in section.content_blocks)

    output = window.export_current_report(output_path=tmp_path / "report.html")
    html = output.read_text(encoding="utf-8")
    assert "3D Scene Screenshots" in html
    assert "Scene screenshot not available" in html
    assert window.current_project.to_dict() == before_project


def test_preview_handles_non_image_screenshot_artifact(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.tif")
    window.mesh_viewer.capture_button.click()
    preview_summary = window.generate_report_preview()

    section = _scene_screenshot_section(preview_summary)
    assert section is not None
    assert any(
        "scene screenshot artifact (tif)" in block.lower()
        for block in section.content_blocks
    )


def test_preview_does_not_add_scene_screenshots_to_summary_figures(
    app: object, tmp_path: Path
) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    baseline_summary = window.build_current_report_summary()
    baseline_figure_count = len(baseline_summary.figures)

    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    window.mesh_viewer.capture_button.click()
    preview_summary = window.generate_report_preview()

    assert len(preview_summary.figures) == baseline_figure_count
    assert not any(
        getattr(figure, "metadata", {}).get("kind") == "scene_screenshot"
        for figure in preview_summary.figures
    )
