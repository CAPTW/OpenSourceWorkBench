"""Qt-free unit tests for the 3D workspace mesh viewer view-model helpers.

These import no PySide6: they exercise the pure mapping helpers and the default
scene adapter's PyVista-optional behavior without any GUI toolkit or live render.
"""

from __future__ import annotations

import pytest

from osw.gui.workspace_scene_view_model import (
    DefaultSceneAdapter,
    MeshViewerState,
    mesh_input_ref,
    mesh_scalar_field_names,
    mesh_summary_rows,
    mesh_vector_field_names,
    scene_view_state_from_toggles,
    summary_rows_to_text,
)
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.pyvista_scene import PyVistaUnavailableError
from osw.post.scene_model import SceneInputRef, SceneViewState


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _mesh_with_fields() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
        point_data={"temperature": (1.0, 2.0, 3.0), "pressure": (4.0, 5.0, 6.0)},
        cell_data={"region": (7.0,)},
    )


def _mesh_with_vector_field() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
        point_data={
            "temperature": (1.0, 2.0, 3.0),
            "velocity": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        },
        cell_data={"force": ((1.0, 2.0, 3.0),)},
    )


def test_mesh_input_ref_is_mesh_sourced() -> None:
    ref = mesh_input_ref("mesh-1", ("sel-a", "sel-b"))
    assert isinstance(ref, SceneInputRef)
    assert ref.source_kind == "mesh"
    assert ref.mesh_ref == "mesh-1"
    assert ref.selection_ids == ("sel-a", "sel-b")


def test_mesh_input_ref_blank_ref_is_none() -> None:
    ref = mesh_input_ref("")
    assert ref.mesh_ref is None
    assert ref.selection_ids == ()


def test_mesh_summary_rows_reports_counts_types_bounds() -> None:
    rows = dict(mesh_summary_rows(_mesh()))
    assert rows["Nodes"] == "3"
    assert rows["Elements"] == "1"
    assert rows["Cell types"] == "triangle"
    assert rows["Bounds min"] == "(0, 0, 0)"
    assert rows["Bounds max"] == "(1, 1, 0)"


def test_mesh_summary_rows_handles_no_mesh() -> None:
    assert mesh_summary_rows(None) == (("Mesh", "No mesh loaded."),)


def test_scene_view_state_from_toggles_maps_render_options() -> None:
    state = scene_view_state_from_toggles(
        show_surface=True,
        show_edges=True,
        show_axes=False,
        show_grid=True,
        selected_selection_ids=("s1",),
    )
    assert isinstance(state, SceneViewState)
    assert state.render_options.show_surface is True
    assert state.render_options.show_edges is True
    assert state.render_options.show_axes is False
    assert state.render_options.show_grid is True
    assert state.selected_selection_ids == ("s1",)


def test_summary_rows_to_text_joins_rows() -> None:
    text = summary_rows_to_text((("Nodes", "3"), ("Elements", "1")))
    assert text == "Nodes: 3\nElements: 1"


def test_default_adapter_load_mesh_is_pyvista_free() -> None:
    adapter = DefaultSceneAdapter(loader=lambda: None)
    state = adapter.load_mesh(_mesh(), mesh_input_ref("m"), scene_view_state_from_toggles())
    # build_scene_state returns a PyVista-free summary; no live render occurs.
    assert state.mesh_info.node_count == 3
    assert state.rendered is False


def test_default_adapter_export_screenshot_record_missing_pyvista_is_friendly(tmp_path) -> None:
    adapter = DefaultSceneAdapter(loader=lambda: None)
    with pytest.raises(PyVistaUnavailableError):
        adapter.export_screenshot_record(
            str(tmp_path / "shot.png"),
            record_id="r1",
            scene_state=scene_view_state_from_toggles(),
            mesh=_mesh(),
        )
    assert not (tmp_path / "shot.png").exists()


def test_mesh_viewer_state_defaults_are_transient() -> None:
    state = MeshViewerState()
    assert state.mesh is None
    assert state.screenshot_record is None
    assert isinstance(state.scene_state, SceneViewState)


def test_mesh_scalar_field_names_lists_point_then_cell_fields() -> None:
    names = mesh_scalar_field_names(_mesh_with_fields())
    assert names == ("temperature", "pressure", "region")


def test_mesh_scalar_field_names_empty_when_no_fields_or_no_mesh() -> None:
    assert mesh_scalar_field_names(_mesh()) == ()
    assert mesh_scalar_field_names(None) == ()


def test_scene_view_state_from_toggles_binds_color_by() -> None:
    state = scene_view_state_from_toggles(color_by="temperature")
    assert state.render_options.color_by == "temperature"
    assert state.scalar_field_id == "temperature"
    # color_by maps to the scene shell's PyVistaSceneConfig scalar_field.
    assert state.render_options.to_pyvista_config_dict()["scalar_field"] == "temperature"


def test_scene_view_state_from_toggles_no_color_by_is_none() -> None:
    state = scene_view_state_from_toggles(color_by=None)
    assert state.render_options.color_by is None
    assert state.scalar_field_id is None
    state_blank = scene_view_state_from_toggles(color_by="")
    assert state_blank.render_options.color_by is None


def test_mesh_scalar_field_names_excludes_vector_arrays() -> None:
    names = mesh_scalar_field_names(_mesh_with_vector_field())
    assert names == ("temperature",)


def test_mesh_vector_field_names_lists_point_then_cell_vectors() -> None:
    names = mesh_vector_field_names(_mesh_with_vector_field())
    assert names == ("velocity", "force")


def test_scene_view_state_from_toggles_records_glyph_options() -> None:
    state = scene_view_state_from_toggles(
        glyph_enabled=True,
        glyph_vector_field="velocity",
        glyph_scale=1.5,
        glyph_max_count=25,
    )

    assert state.glyph_options.enabled is True
    assert state.glyph_options.vector_field == "velocity"
    assert state.glyph_options.scale == 1.5
    assert state.glyph_options.max_glyph_count == 25
