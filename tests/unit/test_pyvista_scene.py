from __future__ import annotations

from pathlib import Path

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData, mesh_data_to_model
from osw.post.field_dataset import FieldRenderRequest
from osw.post.field_view_model import field_view_model_from_mesh_model
from osw.post.pyvista_scene import (
    PyVistaScene,
    PyVistaSceneConfig,
    PyVistaUnavailableError,
    build_scene_state,
    export_screenshot_record,
    mesh_data_to_polydata,
    render_field_view,
)


class FakePolyData:
    def __init__(self, points: object, faces: object) -> None:
        self.points = points
        self.faces = faces
        self.point_data: dict[str, object] = {}


class FakePlotter:
    def __init__(self, *, off_screen: bool = False, fail_add_mesh: bool = False) -> None:
        self.off_screen = off_screen
        self.fail_add_mesh = fail_add_mesh
        self.mesh_calls: list[dict[str, object]] = []
        self.axes_added = False
        self.grid_shown = False
        self.screenshots: list[str] = []
        self.close_calls = 0

    def add_mesh(self, dataset: object, **kwargs: object) -> None:
        if self.fail_add_mesh:
            raise RuntimeError("forced add_mesh failure")
        self.mesh_calls.append({"dataset": dataset, **kwargs})

    def add_axes(self) -> None:
        self.axes_added = True

    def show_grid(self) -> None:
        self.grid_shown = True

    def screenshot(self, path: str) -> None:
        self.screenshots.append(path)
        Path(path).write_text("fake screenshot", encoding="utf-8")

    def close(self) -> None:
        self.close_calls += 1


class FakePyVista:
    PolyData = FakePolyData

    def __init__(self, *, fail_add_mesh: bool = False) -> None:
        self.fail_add_mesh = fail_add_mesh
        self.plotters: list[FakePlotter] = []

    def Plotter(self, *, off_screen: bool = False) -> FakePlotter:
        plotter = FakePlotter(
            off_screen=off_screen,
            fail_add_mesh=self.fail_add_mesh,
        )
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


def test_add_mesh_closes_replaced_plotter_and_close_is_idempotent() -> None:
    fake_pyvista = FakePyVista()
    scene = PyVistaScene(pyvista_module=fake_pyvista)

    scene.add_mesh(sample_mesh())
    first = fake_pyvista.plotters[0]
    scene.add_mesh(sample_mesh())
    second = fake_pyvista.plotters[1]

    assert first.close_calls == 1
    assert second.close_calls == 0

    scene.close()
    scene.close()

    assert second.close_calls == 1


def test_add_mesh_closes_partially_initialized_plotter_on_failure() -> None:
    fake_pyvista = FakePyVista(fail_add_mesh=True)
    scene = PyVistaScene(pyvista_module=fake_pyvista)

    with pytest.raises(RuntimeError, match="forced add_mesh failure"):
        scene.add_mesh(sample_mesh())

    assert fake_pyvista.plotters[0].close_calls == 1


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
    assert fake_pyvista.plotters[0].close_calls == 1


def test_screenshot_record_export_closes_plotter(tmp_path: Path) -> None:
    fake_pyvista = FakePyVista()

    record = export_screenshot_record(
        sample_mesh(),
        tmp_path / "record.png",
        record_id="record-1",
        pyvista_module=fake_pyvista,
    )

    assert record.id == "record-1"
    assert fake_pyvista.plotters[0].close_calls == 1


def test_field_render_missing_pyvista_returns_dependency_diagnostic() -> None:
    model = field_view_model_from_mesh_model(
        mesh_data_to_model(sample_mesh(), source="mesh.vtk", mesh_format="vtk")
    )

    result = render_field_view(
        model,
        FieldRenderRequest(dataset_id=model.dataset_id, scalar_field="temperature"),
        loader=lambda: None,
    )

    assert result.status == "dependency_missing"
    assert not result.rendered
    assert "PyVista is not installed" in result.message


def test_field_render_fake_pyvista_uses_scalar_field() -> None:
    fake_pyvista = FakePyVista()
    model = field_view_model_from_mesh_model(
        mesh_data_to_model(sample_mesh(), source="mesh.vtk", mesh_format="vtk")
    )

    result = render_field_view(
        model,
        FieldRenderRequest(dataset_id=model.dataset_id, scalar_field="temperature"),
        pyvista_module=fake_pyvista,
    )

    assert result.status == "rendered"
    assert result.rendered
    assert fake_pyvista.plotters[0].mesh_calls[0]["scalars"] == "temperature"
    dataset = fake_pyvista.plotters[0].mesh_calls[0]["dataset"]
    assert dataset.point_data["temperature"] == (300.0, 310.0, 305.0)
    assert fake_pyvista.plotters[0].close_calls == 1


def test_vector_field_rendering_is_deferred_placeholder() -> None:
    fake_pyvista = FakePyVista()
    model = field_view_model_from_mesh_model(
        mesh_data_to_model(sample_mesh(), source="mesh.vtk", mesh_format="vtk")
    )

    result = render_field_view(
        model,
        FieldRenderRequest(dataset_id=model.dataset_id, vector_field="velocity", mode="vector"),
        pyvista_module=fake_pyvista,
    )

    assert result.status == "placeholder"
    assert "Vector field glyph rendering is deferred" in result.message
    assert fake_pyvista.plotters == []
