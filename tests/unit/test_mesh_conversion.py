from __future__ import annotations

from pathlib import Path

from osw.mesh.mesh_model import MeshCellBlock, MeshModel
from osw.mesh.meshio_bridge import MeshImportStatus, write_mesh


class FakeMesh:
    def __init__(self, points: object, cells: object) -> None:
        self.points = points
        self.cells = cells


class FakeMeshio:
    Mesh = FakeMesh

    def __init__(self) -> None:
        self.writes: list[tuple[str, FakeMesh, str | None]] = []

    def write(self, path: str, mesh: FakeMesh, file_format: str | None = None) -> None:
        self.writes.append((path, mesh, file_format))
        Path(path).write_text("mesh", encoding="utf-8")


def _mesh() -> MeshModel:
    return MeshModel(
        id="tiny",
        name="tiny",
        source_path="tiny.vtu",
        points=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )


def test_write_mesh_result_writes_supported_export(tmp_path: Path) -> None:
    fake = FakeMeshio()
    output_path = tmp_path / "out.vtu"

    result = write_mesh(_mesh(), output_path, meshio_module=fake)

    assert result.status is MeshImportStatus.OK
    assert output_path.exists()
    assert fake.writes[0][2] == "vtu"
    assert result.artifact_ref is not None
    assert result.artifact_ref.path == str(output_path)
    assert result.artifact_ref.node_count == 3


def test_write_mesh_result_reports_unsupported_export(tmp_path: Path) -> None:
    result = write_mesh(_mesh(), tmp_path / "out.native", meshio_module=FakeMeshio())

    assert result.status is MeshImportStatus.ERROR
    assert any(
        message.code == "unsupported-mesh-export-format"
        for message in result.diagnostics.messages
    )


def test_write_mesh_result_reports_missing_meshio(tmp_path: Path) -> None:
    result = write_mesh(_mesh(), tmp_path / "out.vtu")

    assert result.status in {MeshImportStatus.OK, MeshImportStatus.DEPENDENCY_MISSING}
    if result.status is MeshImportStatus.DEPENDENCY_MISSING:
        assert "meshio is not installed" in result.diagnostics.summary()
