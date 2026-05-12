from __future__ import annotations

from pathlib import Path

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.pyvista_scene import (
    PyVistaScene,
    PyVistaSceneConfig,
    PyVistaUnavailableError,
    build_scene_state,
    mesh_data_to_polydata,
)


class FakePolyData:
    def __init__(self, points: object, faces: object) -> None:
        self.points = points
        self.faces = faces


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


def sample_mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 2.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        point_data={"temperature": (300.0, 310.0, 305.0)},
    )


def test_scene_state_summarizes_mesh_and_placeholders() -> None:
    config = PyVistaSceneConfig(
        show_surface=True,
        show_edges=True,
        show_axes=True,
        show_grid=True,
        scalar_field="temperature",
    )

    state = build_scene_state(sample_mesh(), config=config)

    assert state.mesh_info.nodes == 3
    assert state.mesh_info.elements == 1
    assert state.bounding_box.maximum == (1.0, 1.0, 2.0)
    assert state.scalar_field == "temperature"
    assert state.show_edges is True
    assert state.show_axes is True
    assert state.show_grid is True
    assert state.warnings == ()


def test_missing_scalar_field_is_reported_as_warning() -> None:
    state = build_scene_state(
        sample_mesh(),
        config=PyVistaSceneConfig(scalar_field="pressure"),
    )

    assert state.scalar_field == "pressure"
    assert state.warnings == ("Scalar field 'pressure' is not present on the mesh.",)


def test_missing_pyvista_error_is_user_friendly() -> None:
    scene = PyVistaScene(pyvista_module=None, loader=lambda: None)

    with pytest.raises(PyVistaUnavailableError, match="PyVista is not installed"):
        scene.add_mesh(sample_mesh())


def test_fake_pyvista_scene_accepts_simple_mesh() -> None:
    fake_pyvista = FakePyVista()
    scene = PyVistaScene(
        config=PyVistaSceneConfig(show_edges=True, show_axes=True, show_grid=True),
        pyvista_module=fake_pyvista,
    )

    state = scene.add_mesh(sample_mesh())

    assert state.rendered is True
    assert len(fake_pyvista.plotters) == 1
    plotter = fake_pyvista.plotters[0]
    assert plotter.off_screen is True
    assert plotter.axes_added is True
    assert plotter.grid_shown is True
    assert plotter.mesh_calls[0]["show_edges"] is True
    assert isinstance(plotter.mesh_calls[0]["dataset"], FakePolyData)


def test_mesh_data_to_polydata_builds_triangle_faces() -> None:
    fake_pyvista = FakePyVista()

    dataset = mesh_data_to_polydata(sample_mesh(), pyvista_module=fake_pyvista)

    assert dataset.points == [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 2.0]]
    assert dataset.faces == [3, 0, 1, 2]


def test_screenshot_export_uses_optional_plotter(tmp_path: Path) -> None:
    fake_pyvista = FakePyVista()
    scene = PyVistaScene(pyvista_module=fake_pyvista)
    screenshot_path = tmp_path / "scene.png"

    exported = scene.export_screenshot(sample_mesh(), screenshot_path)

    assert exported == screenshot_path
    assert screenshot_path.read_text(encoding="utf-8") == "fake screenshot"
    assert fake_pyvista.plotters[0].screenshots == [str(screenshot_path)]
