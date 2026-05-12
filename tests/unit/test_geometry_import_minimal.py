from __future__ import annotations

from pathlib import Path

import pytest

from osw.geometry.cad_importer_base import (
    GeometryImportError,
    detect_geometry_format,
    preview_geometry,
)


def test_ascii_stl_preview_returns_bounds_and_body_metadata(tmp_path: Path) -> None:
    stl_path = tmp_path / "triangle.stl"
    stl_path.write_text(
        "\n".join(
            [
                "solid triangle",
                "facet normal 0 0 1",
                "outer loop",
                "vertex 0 0 0",
                "vertex 2 0 0",
                "vertex 0 3 1",
                "endloop",
                "endfacet",
                "endsolid triangle",
            ]
        ),
        encoding="utf-8",
    )

    model = preview_geometry(stl_path)

    assert model.source == str(stl_path)
    assert model.format == "stl"
    assert model.body_count == 1
    assert model.bounding_box.minimum == (0.0, 0.0, 0.0)
    assert model.bounding_box.maximum == (2.0, 3.0, 1.0)
    assert model.bodies[0].metadata["triangles"] == 1


def test_obj_preview_returns_bounds_vertices_and_faces(tmp_path: Path) -> None:
    obj_path = tmp_path / "quad.obj"
    obj_path.write_text(
        "\n".join(
            [
                "o quad",
                "v -1 0 0",
                "v 1 0 0",
                "v 1 2 0",
                "v -1 2 0",
                "f 1 2 3 4",
            ]
        ),
        encoding="utf-8",
    )

    model = preview_geometry(obj_path)

    assert model.format == "obj"
    assert model.body_count == 1
    assert model.bounding_box.minimum == (-1.0, 0.0, 0.0)
    assert model.bounding_box.maximum == (1.0, 2.0, 0.0)
    assert model.bodies[0].metadata["vertices"] == 4
    assert model.bodies[0].metadata["faces"] == 1


def test_step_preview_stub_does_not_crash_without_optional_kernel(tmp_path: Path) -> None:
    step_path = tmp_path / "bracket.step"
    step_path.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")

    model = preview_geometry(step_path)

    assert model.format == "step"
    assert model.body_count == 1
    assert model.bodies[0].kind == "cad-placeholder"
    assert model.warnings
    assert "optional CAD bridge" in model.warnings[0]


def test_detect_geometry_format_supports_standard_export_extensions() -> None:
    assert detect_geometry_format("part.stl") == "stl"
    assert detect_geometry_format("part.obj") == "obj"
    assert detect_geometry_format("part.step") == "step"
    assert detect_geometry_format("part.stp") == "step"
    assert detect_geometry_format("part.iges") == "iges"
    assert detect_geometry_format("part.igs") == "iges"
    assert detect_geometry_format("part.brep") == "brep"


def test_native_commercial_cad_reports_v01_out_of_scope() -> None:
    with pytest.raises(GeometryImportError) as exc_info:
        detect_geometry_format("assembly.sldprt")

    message = str(exc_info.value)
    assert "v0.1 does not support native commercial CAD" in message
    assert "export STEP or STL" in message


def test_unsupported_geometry_extension_is_friendly() -> None:
    with pytest.raises(GeometryImportError, match="Unsupported geometry format"):
        detect_geometry_format("part.unknown")


def test_missing_geometry_file_reports_friendly_error(tmp_path: Path) -> None:
    with pytest.raises(GeometryImportError, match="Geometry file does not exist"):
        preview_geometry(tmp_path / "missing.stl")
