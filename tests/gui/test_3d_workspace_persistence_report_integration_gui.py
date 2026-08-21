"""Focused GUI routing tests for active-scene save/reopen/report integration."""

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


def _mesh(*, offset: float = 0.0) -> MeshData:
    return MeshData(
        points=(
            (offset, 0.0, 0.0),
            (offset + 1.0, 0.0, 0.0),
            (offset, 1.0, 0.0),
        ),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


class CaptureAdapter:
    def __init__(self, *, capture_available: bool = True) -> None:
        self.capture_available = capture_available
        self.load_calls = 0
        self.capture_calls = 0

    def load_mesh(self, mesh: MeshData, scene_input: Any, scene_state: Any) -> object:
        self.load_calls += 1
        return None

    def set_view_state(self, scene_state: Any) -> None:
        return None

    def clear(self) -> None:
        return None

    def close(self) -> None:
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
        from osw.post.pyvista_scene import PyVistaUnavailableError

        self.capture_calls += 1
        if not self.capture_available:
            raise PyVistaUnavailableError("renderer backend unavailable")
        Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + b"captured")
        return SceneScreenshotRecord(
            id=record_id,
            path=path,
            scene_state=scene_state,
            mesh_ref=mesh_ref,
            selection_ids=tuple(selection_ids),
            caption=caption,
            created_by=created_by,
        )


def _window(app: object, adapter: CaptureAdapter, **kwargs: object) -> object:
    from osw.gui.main_window import MainWindow

    assert app is not None
    return MainWindow(mesh_scene_adapter_factory=lambda: adapter, **kwargs)


def test_explicit_save_captures_active_scene_and_transient_controls_stay_clean(
    app: object,
    tmp_path: Path,
) -> None:
    saves: list[tuple[object, str]] = []
    target = tmp_path / "project.osw.json"
    window = _window(
        app,
        CaptureAdapter(),
        project_save_path_picker=lambda: str(target),
        project_saver=lambda project, path: saves.append((project, path)),
    )
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window._project_dirty = False

    window.mesh_viewer.surface_toggle.setChecked(False)
    window.mesh_viewer.edge_toggle.setChecked(True)
    window.mesh_viewer.axis_toggle.setChecked(False)
    window.mesh_viewer.load_mesh_preview()
    assert window.project_dirty is False

    assert window.save_project_as() is True
    assert len(saves) == 1
    saved_project, saved_path = saves[0]
    assert saved_path == str(target)
    assert saved_project.active_scene is not None
    assert saved_project.active_scene.mesh_ref == "mesh-1"
    assert saved_project.schema_version == "0.3"
    assert window.current_project.active_scene == saved_project.active_scene
    assert window.project_dirty is False


def test_reopen_is_pending_metadata_only_until_explicit_exact_mesh_reload(
    app: object,
) -> None:
    from osw.core.project_schema import Project, ProjectMetadata
    from osw.core.workspace_3d import ActiveSceneRestoreStatus, ActiveSceneState
    from osw.mesh.identity import compute_mesh_fingerprint

    mesh = _mesh()
    project = Project(
        metadata=ProjectMetadata(name="Saved"),
        active_scene=ActiveSceneState(
            mesh_ref="mesh-1",
            mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
            representation="wireframe",
        ),
    )
    adapter = CaptureAdapter()
    window = _window(
        app,
        adapter,
        project_open_path_picker=lambda: "saved.osw.json",
        project_loader=lambda path: project,
    )

    assert window.open_project() is True
    assert adapter.load_calls == 0
    assert window.last_imported_mesh_data is None
    assert window.active_scene_controller.active_scene_restore_result.status is (
        ActiveSceneRestoreStatus.PENDING
    )
    assert window.project_dirty is False

    window.load_mesh_into_viewer(mesh, mesh_ref="mesh-1")

    assert window.active_scene_controller.active_scene_restore_result.status in {
        ActiveSceneRestoreStatus.RESTORED,
        ActiveSceneRestoreStatus.PARTIAL,
    }
    assert window.project_dirty is False


def test_explicit_clear_saved_scene_marks_dirty_and_preserves_report_assets(
    app: object,
) -> None:
    from osw.core.project_schema import Project, ProjectMetadata
    from osw.core.report_asset import ReportScreenshotAsset
    from osw.core.workspace_3d import ActiveSceneState

    asset = ReportScreenshotAsset(id="shot-1", path="scene.png")
    project = Project(
        metadata=ProjectMetadata(name="Saved"),
        active_scene=ActiveSceneState(
            mesh_ref="mesh-1",
            mesh_fingerprint="a" * 64,
        ),
        report_screenshots=(asset,),
    )
    window = _window(app, CaptureAdapter(), project=project)
    window._project_dirty = False

    assert window.clear_saved_active_scene_state() is True

    assert window.current_project.active_scene is None
    assert window.current_project.report_screenshots == [asset]
    assert window.project_dirty is True


def test_capture_is_dirty_neutral_confirmation_staging_is_dirty_and_no_auto_save(
    app: object,
    tmp_path: Path,
) -> None:
    saves: list[object] = []
    adapter = CaptureAdapter()
    window = _window(
        app,
        adapter,
        project_saver=lambda project, path: saves.append((project, path)),
    )
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window._project_dirty = False
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")

    record = window.capture_scene_screenshot_to_report_candidates()

    assert record is not None
    assert record.metadata["osw.active_scene.provenance"]["active_scene_digest"]
    assert window.project_dirty is False
    assert window.current_project.report_screenshots == []
    assert saves == []

    window._confirm_persist_scene_screenshots = lambda count: True
    assert window.persist_staged_scene_screenshots() == 1
    assert window.project_dirty is True
    assert len(window.current_project.report_screenshots) == 1
    assert saves == []


def test_cancel_staging_and_renderer_fallback_leave_project_clean(
    app: object,
    tmp_path: Path,
) -> None:
    adapter = CaptureAdapter(capture_available=False)
    window = _window(app, adapter)
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window._project_dirty = False
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")

    record = window.capture_scene_screenshot_to_report_candidates()

    assert record is None
    assert not (tmp_path / "scene.png").exists()
    assert window.scene_screenshot_candidates() == ()
    assert window.current_project.report_screenshots == []
    assert window.project_dirty is False


def test_report_preview_consumes_only_persisted_screenshots(
    app: object,
    tmp_path: Path,
) -> None:
    adapter = CaptureAdapter()
    window = _window(app, adapter)
    window.load_mesh_into_viewer(_mesh(), mesh_ref="mesh-1")
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    assert window.capture_scene_screenshot_to_report_candidates() is not None

    before = window.generate_report_preview(log=False)
    assert all(
        getattr(section, "section_id", "") != "scene-screenshots"
        for section in before.sections
    )

    window._confirm_persist_scene_screenshots = lambda count: True
    window.persist_staged_scene_screenshots()
    after = window.generate_report_preview(log=False)
    section = next(
        section
        for section in after.sections
        if getattr(section, "section_id", "") == "scene-screenshots"
    )
    rendered = "\n".join(section.content_blocks)
    assert "Active scene: osw.active_scene.v1" in rendered
    assert str(tmp_path) not in rendered


def test_capture_embeds_state_and_restore_rejects_changed_fingerprint(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.core.workspace_3d import ActiveSceneRestoreStatus

    adapter = CaptureAdapter()
    window = _window(app, adapter)
    original = _mesh()
    window.load_mesh_into_viewer(original, mesh_ref="mesh-1")
    window.mesh_viewer.surface_toggle.setChecked(False)
    window.mesh_viewer.edge_toggle.setChecked(True)
    window.mesh_viewer.axis_toggle.setChecked(False)
    window.mesh_viewer.load_mesh_preview()
    window._project_dirty = False
    window._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")

    record = window.capture_scene_screenshot_to_report_candidates()

    assert record is not None
    assert record.metadata["osw.active_scene.state"]["representation"]
    assert record.metadata["osw.active_scene.provenance"]["active_scene_digest"]
    assert window.project_dirty is False

    restored = window.restore_scene_from_report_capture(record)
    assert restored.status in {
        ActiveSceneRestoreStatus.RESTORED,
        ActiveSceneRestoreStatus.PARTIAL,
    }

    window.load_mesh_into_viewer(_mesh(offset=4.0), mesh_ref="mesh-1")
    stale = window.restore_scene_from_report_capture(record)
    assert stale.status is ActiveSceneRestoreStatus.STALE
    assert stale.reason_codes == ("MESH_FINGERPRINT_MISMATCH",)
    window.close()
    assert window.active_scene_controller.pending_active_scene_state is None


def test_save_reopen_export_and_restore_persisted_capture(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.core.project_schema import Project
    from osw.core.workspace_3d import ActiveSceneRestoreStatus

    saved: list[object] = []
    target = tmp_path / "project.osw.json"
    first = _window(
        app,
        CaptureAdapter(),
        project_save_path_picker=lambda: str(target),
        project_saver=lambda project, path: saved.append((project, path)),
    )
    mesh = _mesh()
    first.load_mesh_into_viewer(mesh, mesh_ref="mesh-1")
    first.mesh_viewer.surface_toggle.setChecked(False)
    first.mesh_viewer.edge_toggle.setChecked(True)
    first.mesh_viewer.load_mesh_preview()
    first._pick_scene_screenshot_target_path = lambda: str(tmp_path / "scene.png")
    assert first.capture_scene_screenshot_to_report_candidates() is not None
    first._confirm_persist_scene_screenshots = lambda count: True
    assert first.persist_staged_scene_screenshots() == 1
    assert first.save_project_as() is True
    report_path = first.export_report(tmp_path / "report.html")
    assert report_path.is_file()
    assert "Active scene: osw.active_scene.v1" in report_path.read_text(encoding="utf-8")
    saved_project = saved[0][0]
    first.close()

    second = _window(
        app,
        CaptureAdapter(),
        project_open_path_picker=lambda: str(target),
        project_loader=lambda path: Project.from_dict(saved_project.to_dict()),
    )
    assert second.open_project() is True
    assert second.active_scene_controller.active_scene_restore_result.status is (
        ActiveSceneRestoreStatus.PENDING
    )
    second.load_mesh_into_viewer(mesh, mesh_ref="mesh-1")
    assert second.active_scene_controller.active_scene_restore_result.status in {
        ActiveSceneRestoreStatus.RESTORED,
        ActiveSceneRestoreStatus.PARTIAL,
    }
    assert len(second.current_project.report_screenshots) == 1
    restored = second.restore_scene_from_report_capture(
        second.current_project.report_screenshots[0]
    )
    assert restored.status in {
        ActiveSceneRestoreStatus.RESTORED,
        ActiveSceneRestoreStatus.PARTIAL,
    }
    second.load_mesh_into_viewer(_mesh(offset=3.0), mesh_ref="mesh-1")
    stale = second.restore_scene_from_report_capture(
        second.current_project.report_screenshots[0]
    )
    assert stale.status is ActiveSceneRestoreStatus.STALE
    second.close()
