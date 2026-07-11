"""3D-workspace persisted report screenshot asset tests (opt-in, no auto-save).

These tests validate the explicit opt-in persist flow that copies transient
staged scene screenshots into ``Project.report_screenshots`` (local paths +
provenance only, no image bytes) and confirm persisted assets feed preview/export
through the existing report bridge after a project reload. They use fake scene
adapters and an overridable confirmation seam, so no live PyVista/VTK render,
solver execution, mesh generation, or project auto-save is required.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from osw.core.project_schema import Project, ProjectMetadata, ReportConfig
from osw.core.report_asset import ReportScreenshotAsset
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
    def __init__(self, write_image: bool = False) -> None:
        self.write_image = write_image

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


def _scene_section(summary: object) -> Any | None:
    for section in getattr(summary, "sections", ()):
        if getattr(section, "section_id", "") == "scene-screenshots":
            return section
    return None


def _capture(window: object, tmp_path: Path, *, write_image: bool = True) -> None:
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    window.mesh_viewer.capture_button.click()


# -- explicit opt-in persist ------------------------------------------------


def test_persist_action_stores_report_assets_in_project(
    app: object, tmp_path: Path
) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    _capture(window, tmp_path)
    window._confirm_persist_scene_screenshots = lambda count: True

    window.mesh_viewer.persist_screenshots_button.click()

    assets = window.current_project.report_screenshots
    assert len(assets) == 1
    assert isinstance(assets[0], ReportScreenshotAsset)
    assert assets[0].mesh_ref == "mesh-1"
    assert assets[0].path.endswith("scene.png")
    assert assets[0].metadata["is_release_asset"] is False
    assert assets[0].metadata["is_validation_evidence"] is False
    assert assets[0].path_kind is None
    assert "path_kind" not in assets[0].to_dict()
    assert window.current_project.schema_version == "0.1"
    # Transient staged candidates are preserved.
    assert len(window.scene_screenshot_candidates()) == 1
    assert "persisted 1 scene screenshot" in window.mesh_viewer.status_label.text().lower()


def test_current_persist_action_keeps_loaded_0_2_and_adds_unmarked_legacy_asset(
    app: object,
    tmp_path: Path,
) -> None:
    project = Project.from_dict(
        {"schema_version": "0.2", "metadata": {"name": "Loaded 0.2"}}
    )
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    window.set_project(project)
    _capture(window, tmp_path)
    window._confirm_persist_scene_screenshots = lambda count: True

    window.persist_staged_scene_screenshots()

    assert window.current_project.schema_version == "0.2"
    assert len(window.current_project.report_screenshots) == 1
    asset = window.current_project.report_screenshots[0]
    assert asset.path_kind is None
    assert "path_kind" not in asset.to_dict()


def test_persist_is_friendly_noop_when_no_staged(app: object) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.open_mesh_viewer()
    window._confirm_persist_scene_screenshots = lambda count: True

    result = window.persist_staged_scene_screenshots()

    assert result == 0
    assert window.current_project.report_screenshots == []


def test_persist_declined_is_no_op(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    _capture(window, tmp_path)
    window._confirm_persist_scene_screenshots = lambda count: False

    result = window.persist_staged_scene_screenshots()

    assert result == -1
    assert window.current_project.report_screenshots == []


def test_persist_does_not_auto_save(
    app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import osw.core.project_io as project_io

    saves: list[object] = []
    monkeypatch.setattr(project_io, "save_project", lambda project, path: saves.append(path))

    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    _capture(window, tmp_path)
    window._confirm_persist_scene_screenshots = lambda count: True

    window.persist_staged_scene_screenshots()

    assert saves == []  # no project file was saved
    assert len(window.current_project.report_screenshots) == 1


def test_persist_button_enabled_only_when_staged(app: object, tmp_path: Path) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    panel = window.mesh_viewer

    assert not panel.persist_screenshots_button.isEnabled()

    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    panel.capture_button.click()

    assert panel.persist_screenshots_button.isEnabled()


# -- persisted records feed preview/export ----------------------------------


def test_persisted_assets_feed_preview_and_export_after_reload(
    app: object, tmp_path: Path
) -> None:
    image = tmp_path / "scene.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    asset = ReportScreenshotAsset(
        id="shot-1", path=str(image), caption="Persisted iso", mesh_ref="mesh-1"
    )
    project = Project(
        metadata=ProjectMetadata(name="Reloaded"),
        report_screenshots=[asset],
        report=ReportConfig(title="Reloaded"),
    )
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.set_project(project)

    # No transient candidates: the persisted project asset alone drives the report.
    assert window.scene_screenshot_candidates() == ()

    preview = window.generate_report_preview()
    section = _scene_section(preview)
    assert section is not None
    assert any("Persisted iso" in block for block in section.content_blocks)

    output = window.export_current_report(output_path=tmp_path / "report.html")
    html = output.read_text(encoding="utf-8")
    assert "3D Scene Screenshots" in html
    assert "Persisted iso" in html


def test_persist_preserves_transient_without_summary_figure_duplication(
    app: object, tmp_path: Path
) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter(write_image=True))
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    baseline_figures = len(window.build_current_report_summary().figures)
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    window.mesh_viewer.capture_button.click()
    window._confirm_persist_scene_screenshots = lambda count: True

    window.persist_staged_scene_screenshots()

    # Transient preserved and persisted, but de-duplicated by id in the report.
    assert len(window.scene_screenshot_candidates()) == 1
    assert len(window.current_project.report_screenshots) == 1
    preview = window.generate_report_preview()
    section = _scene_section(preview)
    assert section is not None
    entry_lines = [b for b in section.content_blocks if b.startswith("scene-screenshot-1:")]
    assert len(entry_lines) == 1
    # Scene screenshots never leak into summary.figures.
    assert len(preview.figures) == baseline_figures
    assert not any(
        getattr(figure, "metadata", {}).get("kind") == "scene_screenshot"
        for figure in preview.figures
    )


def test_no_staged_no_persisted_report_has_no_scene_section(
    app: object, tmp_path: Path
) -> None:
    window = _window(app=app, adapter=RecordingSceneAdapter())
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")

    output = window.export_current_report(output_path=tmp_path / "report.html")
    assert "3D Scene Screenshots" not in output.read_text(encoding="utf-8")


def test_project_reconstruction_helpers_preserve_persisted_assets(app: object) -> None:
    # A persisted report screenshot (and named selection) must survive subsequent
    # project mutations such as adding a mesh or script reference.
    from osw.core.project_schema import MeshRef, ProjectMetadata, ScriptRef
    from osw.core.selection import EntityKind, NamedSelection, SelectionTargetRef
    from osw.gui.main_window import _project_with_mesh_ref, _project_with_script_ref

    assert app is not None
    asset = ReportScreenshotAsset(id="shot-1", path="scenes/iso.png", caption="Iso")
    selection = NamedSelection(
        id="sel-1",
        name="Selection",
        entity_kind=EntityKind.NODE,
        targets=(SelectionTargetRef(kind=EntityKind.NODE, ids=(1,), mesh_ref="mesh-1"),),
    )
    project = Project(
        metadata=ProjectMetadata(name="Persisted"),
        report_screenshots=[asset],
        selections=[selection],
    )

    after_mesh = _project_with_mesh_ref(project, MeshRef("mesh-2", "mesh/2.vtu", "vtu"))
    assert after_mesh.report_screenshots == project.report_screenshots
    assert after_mesh.selections == project.selections

    after_script = _project_with_script_ref(project, ScriptRef("s-1", "scripts/p.m", "m"))
    assert after_script.report_screenshots == project.report_screenshots
    assert after_script.selections == project.selections
