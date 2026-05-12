from __future__ import annotations

from pathlib import Path

import pytest

from osw.mesh.mesh_model import MeshCellBlock, build_mesh_info
from osw.mesh.meshio_bridge import (
    MeshImportError,
    detect_mesh_format,
    export_vtu,
    load_mesh_info,
    mesh_data_from_meshio,
)


class FakeMesh:
    def __init__(self, points: object, cells: object) -> None:
        self.points = points
        self.cells = cells


class FakeMeshio:
    Mesh = FakeMesh

    def __init__(self, mesh: FakeMesh | None = None, error: Exception | None = None) -> None:
        self.mesh = mesh
        self.error = error
        self.writes: list[tuple[str, FakeMesh, str | None]] = []

    def read(self, path: str) -> FakeMesh:
        if self.error is not None:
            raise self.error
        assert self.mesh is not None
        return self.mesh

    def write(self, path: str, mesh: FakeMesh, file_format: str | None = None) -> None:
        self.writes.append((path, mesh, file_format))
        Path(path).write_text("<VTKFile />", encoding="utf-8")


def test_mesh_info_counts_nodes_elements_cell_types_and_bounds() -> None:
    info = build_mesh_info(
        source="example.vtu",
        mesh_format="vtu",
        points=((0.0, 0.0, 0.0), (1.0, 2.0, 3.0), (-1.0, 0.5, 2.0)),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("line", ((0, 1), (1, 2))),
        ),
    )

    assert info.nodes == 3
    assert info.elements == 3
    assert info.cell_types == ("triangle", "line")
    assert info.bounding_box.minimum == (-1.0, 0.0, 0.0)
    assert info.bounding_box.maximum == (1.0, 2.0, 3.0)


def test_detect_mesh_format_for_supported_extensions() -> None:
    assert detect_mesh_format("case.msh") == "gmsh"
    assert detect_mesh_format("case.inp") == "abaqus"
    assert detect_mesh_format("case.bdf") == "nastran"
    assert detect_mesh_format("case.nas") == "nastran"
    assert detect_mesh_format("case.fem") == "nastran"
    assert detect_mesh_format("case.su2") == "su2"
    assert detect_mesh_format("case.vtk") == "vtk"
    assert detect_mesh_format("case.vtu") == "vtu"
    assert detect_mesh_format("case.xdmf") == "xdmf"
    assert detect_mesh_format("case.xmf") == "xdmf"
    assert detect_mesh_format("case.cgns") == "cgns"


def test_detect_mesh_format_reports_unsupported_extension() -> None:
    with pytest.raises(MeshImportError, match="Unsupported mesh format"):
        detect_mesh_format("native-cad.sldprt")


def test_meshio_read_builds_mesh_info_with_fake_meshio(tmp_path: Path) -> None:
    mesh_path = tmp_path / "small.vtu"
    mesh_path.write_text("fake", encoding="utf-8")
    fake_meshio = FakeMeshio(
        FakeMesh(
            points=((0, 0), (1, 0), (0, 1)),
            cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        )
    )

    info = load_mesh_info(mesh_path, meshio_module=fake_meshio)

    assert info.source == str(mesh_path)
    assert info.format == "vtu"
    assert info.nodes == 3
    assert info.elements == 1
    assert info.bounding_box.maximum == (1.0, 1.0, 0.0)


def test_missing_mesh_file_reports_friendly_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.vtu"

    with pytest.raises(MeshImportError, match="Mesh file does not exist"):
        load_mesh_info(missing_path, meshio_module=FakeMeshio())


def test_corrupt_mesh_reports_friendly_error(tmp_path: Path) -> None:
    mesh_path = tmp_path / "corrupt.vtu"
    mesh_path.write_text("not a mesh", encoding="utf-8")

    with pytest.raises(MeshImportError, match="Could not read mesh"):
        load_mesh_info(mesh_path, meshio_module=FakeMeshio(error=ValueError("bad mesh")))


def test_export_vtu_uses_meshio_writer(tmp_path: Path) -> None:
    mesh_data = mesh_data_from_meshio(
        FakeMesh(
            points=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
            cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        )
    )
    fake_meshio = FakeMeshio()
    output_path = tmp_path / "out.vtu"

    exported = export_vtu(mesh_data, output_path, meshio_module=fake_meshio)

    assert exported == output_path
    assert output_path.exists()
    assert fake_meshio.writes[0][2] == "vtu"
