"""Fake-PyVista tests for the scene shell screenshot-record seam.

These tests never require real PyVista: they inject a fake pyvista module (the
same pattern as tests/unit/test_pyvista_scene.py) or a null loader.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.pyvista_scene import (
    PyVistaUnavailableError,
    export_screenshot_record,
)
from osw.post.scene_model import (
    SceneRenderOptions,
    SceneScreenshotRecord,
    SceneViewState,
)


class FakePolyData:
    def __init__(self, points: object, faces: object) -> None:
        self.points = points
        self.faces = faces
        self.point_data: dict[str, object] = {}


class FakePlotter:
    def __init__(self, *, off_screen: bool = False) -> None:
        self.off_screen = off_screen
        self.mesh_calls: list[dict[str, object]] = []
        self.axes_added = False
        self.grid_shown = False
        self.screenshots: list[str] = []

    def add_mesh(self, dataset: object, **kwargs: object) -> None:
        self.mesh_calls.append({"dataset": dataset, **kwargs})

    def add_axes(self) -> None:
        self.axes_added = True

    def show_grid(self) -> None:
        self.grid_shown = True

    def screenshot(self, path: str) -> None:
        self.screenshots.append(path)
        Path(path).write_text("fake screenshot", encoding="utf-8")


class FakePyVista:
    PolyData = FakePolyData

    def __init__(self) -> None:
        self.plotters: list[FakePlotter] = []

    def Plotter(self, *, off_screen: bool = False) -> FakePlotter:
        plotter = FakePlotter(off_screen=off_screen)
        self.plotters.append(plotter)
        return plotter


def _sample_mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        point_data={"temperature": (300.0, 310.0, 305.0)},
    )


def test_export_screenshot_record_returns_record_via_fake_pyvista(tmp_path: Path) -> None:
    fake_pyvista = FakePyVista()
    target = tmp_path / "scene.png"
    scene_state = SceneViewState(
        render_options=SceneRenderOptions(show_edges=True, color_by="temperature"),
        selected_selection_ids=["sel-1"],
        scalar_field_id="temperature",
    )

    record = export_screenshot_record(
        _sample_mesh(),
        target,
        record_id="rec-1",
        scene_state=scene_state,
        caption="Iso preview",
        dataset_ref="ds-1",
        mesh_ref="mesh-1",
        selection_ids=["sel-1"],
        pyvista_module=fake_pyvista,
    )

    assert isinstance(record, SceneScreenshotRecord)
    assert record.id == "rec-1"
    assert record.path == str(target)
    # The fake plotter actually received the screenshot path and wrote a file.
    assert len(fake_pyvista.plotters) == 1
    assert fake_pyvista.plotters[0].screenshots == [str(target)]
    assert target.exists() and target.stat().st_size > 0
    # Render options mapped to the plotter (edges on), and scene_state is recorded.
    assert fake_pyvista.plotters[0].mesh_calls[0]["show_edges"] is True
    assert record.scene_state == scene_state
    assert record.dataset_ref == "ds-1"
    assert record.selection_ids == ("sel-1",)
    # The record round-trips.
    assert SceneScreenshotRecord.from_dict(record.to_dict()) == record


def test_export_screenshot_record_without_scene_state_uses_defaults(tmp_path: Path) -> None:
    fake_pyvista = FakePyVista()
    target = tmp_path / "default.png"
    record = export_screenshot_record(
        _sample_mesh(), target, record_id="rec-2", pyvista_module=fake_pyvista
    )
    assert record.scene_state == SceneViewState()
    assert target.exists()


def test_export_screenshot_record_missing_pyvista_is_friendly(tmp_path: Path) -> None:
    target = tmp_path / "missing.png"
    with pytest.raises(PyVistaUnavailableError, match="PyVista is not installed"):
        export_screenshot_record(
            _sample_mesh(), target, record_id="rec-3", loader=lambda: None
        )
    # No screenshot file is written when PyVista is unavailable.
    assert not target.exists()
