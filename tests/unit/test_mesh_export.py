from __future__ import annotations

from pathlib import Path

import pytest

from osw.core.project_schema import ResultRef
from osw.mesh.conversion import (
    MeshExportArtifact,
    MeshExportError,
    convert_mesh,
    convert_mesh_to_vtu,
    export_mesh,
)
from osw.mesh.mesh_model import MeshCellBlock, MeshData


class FakeMesh:
    def __init__(self, points: object, cells: object) -> None:
        self.points = points
        self.cells = cells


class FakeMeshio:
    Mesh = FakeMesh

    def __init__(self, mesh: FakeMesh | None = None) -> None:
        self.mesh = mesh
        self.writes: list[tuple[str, FakeMesh, str | None]] = []

    def read(self, _path: str) -> FakeMesh:
        assert self.mesh is not None
        return self.mesh

    def write(self, path: str, mesh: FakeMesh, file_format: str | None = None) -> None:
        self.writes.append((path, mesh, file_format))
        Path(path).write_text(f"mesh export: {file_format}", encoding="utf-8")


def sample_mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )


def test_export_mesh_vtu_returns_artifact_and_writes_with_meshio(tmp_path: Path) -> None:
    meshio = FakeMeshio()
    output_path = tmp_path / "mesh.vtu"

    artifact = export_mesh(sample_mesh(), output_path, meshio_module=meshio)

    assert isinstance(artifact, MeshExportArtifact)
    assert artifact.path == output_path
    assert artifact.format == "vtu"
    assert artifact.node_count == 3
    assert artifact.element_count == 1
    assert artifact.cell_types == ("triangle",)
    assert output_path.exists()
    assert meshio.writes[0][2] == "vtu"


def test_export_mesh_msh_xdmf_and_inp_selects_expected_meshio_formats(
    tmp_path: Path,
) -> None:
    meshio = FakeMeshio()

    msh = export_mesh(sample_mesh(), tmp_path / "mesh.msh", meshio_module=meshio)
    xdmf = export_mesh(sample_mesh(), tmp_path / "mesh.xdmf", meshio_module=meshio)
    inp = export_mesh(sample_mesh(), tmp_path / "mesh.inp", meshio_module=meshio)

    assert msh.format == "gmsh"
    assert xdmf.format == "xdmf"
    assert inp.format == "abaqus"
    assert [write[2] for write in meshio.writes] == ["gmsh22", "xdmf", "abaqus"]


def test_artifact_serializes_and_can_create_project_result_ref(tmp_path: Path) -> None:
    artifact = export_mesh(sample_mesh(), tmp_path / "mesh.vtu", meshio_module=FakeMeshio())

    payload = artifact.to_dict()
    ref = artifact.to_result_ref("mesh-export-1")

    assert payload["path"] == str(tmp_path / "mesh.vtu")
    assert payload["format"] == "vtu"
    assert payload["cell_types"] == ["triangle"]
    assert isinstance(ref, ResultRef)
    assert ref.ref_id == "mesh-export-1"
    assert ref.kind == "mesh_export"
    assert ref.path == str(tmp_path / "mesh.vtu")
    assert ref.metadata["format"] == "vtu"


def test_unsupported_export_extension_reports_supported_formats(tmp_path: Path) -> None:
    with pytest.raises(MeshExportError, match="Unsupported mesh export format"):
        export_mesh(sample_mesh(), tmp_path / "mesh.unsupported", meshio_module=FakeMeshio())


def test_unsupported_inp_cell_type_reports_friendly_error(tmp_path: Path) -> None:
    mesh = MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("polygon", ((0, 1, 2),)),),
    )

    with pytest.raises(MeshExportError, match="Unsupported cell type 'polygon' for .inp export"):
        export_mesh(mesh, tmp_path / "mesh.inp", meshio_module=FakeMeshio())


def test_convert_mesh_preserves_path_return_for_existing_callers(tmp_path: Path) -> None:
    source_path = tmp_path / "source.vtu"
    output_path = tmp_path / "converted.vtu"
    source_path.write_text("source", encoding="utf-8")
    meshio = FakeMeshio(
        FakeMesh(
            points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        )
    )

    converted = convert_mesh(source_path, output_path, output_format="vtu", meshio_module=meshio)
    converted_vtu = convert_mesh_to_vtu(
        source_path,
        tmp_path / "converted-2.vtu",
        meshio_module=meshio,
    )

    assert converted == output_path
    assert converted_vtu == tmp_path / "converted-2.vtu"
    assert output_path.exists()
