from __future__ import annotations

from pathlib import Path

import pytest

from osw.mesh.gmsh_adapter import (
    GmshAdapterError,
    GmshPrimitive,
    MeshSizeControl,
    convert_gmsh_msh_to_vtu,
    generate_primitive_mesh,
    load_gmsh_mesh_info,
)
from osw.mesh.mesh_model import MeshCellBlock


class FakeMesh:
    def __init__(self, points: object, cells: object) -> None:
        self.points = points
        self.cells = cells


class FakeMeshio:
    Mesh = FakeMesh

    def __init__(self) -> None:
        self.writes: list[tuple[str, FakeMesh, str | None]] = []

    def read(self, _path: str) -> FakeMesh:
        return FakeMesh(
            points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        )

    def write(self, path: str, mesh: FakeMesh, file_format: str | None = None) -> None:
        self.writes.append((path, mesh, file_format))
        Path(path).write_text("<VTKFile />", encoding="utf-8")


class FakeGmshOption:
    def __init__(self) -> None:
        self.values: dict[str, float] = {}

    def setNumber(self, name: str, value: float) -> None:  # noqa: N802 - gmsh API spelling
        self.values[name] = value


class FakeGmshOcc:
    def __init__(self) -> None:
        self.boxes: list[tuple[float, float, float, float, float, float]] = []
        self.rectangles: list[tuple[float, float, float, float, float]] = []
        self.synchronized = False

    def addBox(  # noqa: N802 - gmsh API spelling
        self,
        x: float,
        y: float,
        z: float,
        dx: float,
        dy: float,
        dz: float,
    ) -> int:
        self.boxes.append((x, y, z, dx, dy, dz))
        return 31

    def addRectangle(  # noqa: N802 - gmsh API spelling
        self,
        x: float,
        y: float,
        z: float,
        dx: float,
        dy: float,
    ) -> int:
        self.rectangles.append((x, y, z, dx, dy))
        return 21

    def synchronize(self) -> None:
        self.synchronized = True


class FakeGmshMesh:
    def __init__(self) -> None:
        self.generated_dimensions: list[int] = []

    def generate(self, dimension: int) -> None:
        self.generated_dimensions.append(dimension)


class FakeGmshModel:
    def __init__(self) -> None:
        self.occ = FakeGmshOcc()
        self.mesh = FakeGmshMesh()
        self.model_names: list[str] = []
        self.physical_groups: list[tuple[int, tuple[int, ...], int]] = []
        self.physical_names: list[tuple[int, int, str]] = []

    def add(self, name: str) -> None:
        self.model_names.append(name)

    def addPhysicalGroup(  # noqa: N802 - gmsh API spelling
        self,
        dimension: int,
        entities: list[int],
        tag: int,
    ) -> int:
        self.physical_groups.append((dimension, tuple(entities), tag))
        return tag

    def setPhysicalName(  # noqa: N802 - gmsh API spelling
        self,
        dimension: int,
        tag: int,
        name: str,
    ) -> None:
        self.physical_names.append((dimension, tag, name))


class FakeGmsh:
    def __init__(self) -> None:
        self.option = FakeGmshOption()
        self.model = FakeGmshModel()
        self.initialized = False
        self.finalized = False
        self.written_paths: list[str] = []

    def initialize(self) -> None:
        self.initialized = True

    def finalize(self) -> None:
        self.finalized = True

    def write(self, path: str) -> None:
        self.written_paths.append(path)
        Path(path).write_text("$MeshFormat\n4.1 0 8\n$EndMeshFormat\n", encoding="utf-8")


def test_missing_gmsh_reports_friendly_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_import(name: str) -> object:
        if name == "gmsh":
            raise ImportError("no gmsh")
        raise AssertionError(name)

    monkeypatch.setattr("osw.mesh.gmsh_adapter.import_module", fail_import)

    with pytest.raises(GmshAdapterError, match="gmsh is not installed"):
        generate_primitive_mesh(
            GmshPrimitive.plate(width=1.0, height=1.0),
            Path("out.msh"),
        )


def test_mesh_size_control_validates_positive_values() -> None:
    with pytest.raises(GmshAdapterError, match="mesh size"):
        MeshSizeControl(target_size=0.0)

    control = MeshSizeControl(target_size=0.5, min_size=0.1, max_size=1.0)

    assert control.effective_min == 0.1
    assert control.effective_max == 1.0


def test_generate_plate_mesh_uses_fake_gmsh_and_meshio(tmp_path: Path) -> None:
    gmsh = FakeGmsh()
    meshio = FakeMeshio()
    msh_path = tmp_path / "plate.msh"
    vtu_path = tmp_path / "plate.vtu"

    result = generate_primitive_mesh(
        GmshPrimitive.plate(width=2.0, height=1.0, name="plate"),
        msh_path,
        mesh_size=MeshSizeControl(target_size=0.25),
        gmsh_module=gmsh,
        meshio_module=meshio,
        vtu_path=vtu_path,
    )

    assert gmsh.initialized is True
    assert gmsh.finalized is True
    assert gmsh.option.values["Mesh.CharacteristicLengthMin"] == 0.25
    assert gmsh.option.values["Mesh.CharacteristicLengthMax"] == 0.25
    assert gmsh.model.occ.rectangles == [(0.0, 0.0, 0.0, 2.0, 1.0)]
    assert gmsh.model.mesh.generated_dimensions == [2]
    assert gmsh.model.physical_names == [(2, 1, "plate")]
    assert result.msh_path == msh_path
    assert result.vtu_path == vtu_path
    assert result.mesh_info is not None
    assert result.mesh_info.nodes == 3
    assert result.physical_groups[0].name == "plate"
    assert meshio.writes[0][2] == "vtu"


def test_generate_box_mesh_records_volume_physical_group(tmp_path: Path) -> None:
    gmsh = FakeGmsh()
    result = generate_primitive_mesh(
        GmshPrimitive.box(width=1.0, depth=2.0, height=3.0, name="box"),
        tmp_path / "box.msh",
        gmsh_module=gmsh,
    )

    assert gmsh.model.occ.boxes == [(0.0, 0.0, 0.0, 1.0, 2.0, 3.0)]
    assert gmsh.model.mesh.generated_dimensions == [3]
    assert gmsh.model.physical_names == [(3, 1, "box")]
    assert result.mesh_info is None


def test_load_gmsh_mesh_info_uses_meshio_bridge(tmp_path: Path) -> None:
    msh_path = tmp_path / "generated.msh"
    msh_path.write_text("$MeshFormat\n", encoding="utf-8")

    info = load_gmsh_mesh_info(msh_path, meshio_module=FakeMeshio())

    assert info.source == str(msh_path)
    assert info.format == "gmsh"
    assert info.elements == 1


def test_convert_gmsh_msh_to_vtu_uses_meshio_bridge(tmp_path: Path) -> None:
    msh_path = tmp_path / "generated.msh"
    vtu_path = tmp_path / "generated.vtu"
    msh_path.write_text("$MeshFormat\n", encoding="utf-8")
    meshio = FakeMeshio()

    exported = convert_gmsh_msh_to_vtu(msh_path, vtu_path, meshio_module=meshio)

    assert exported == vtu_path
    assert vtu_path.exists()
    assert meshio.writes[0][2] == "vtu"


def test_invalid_primitive_dimensions_are_friendly() -> None:
    with pytest.raises(GmshAdapterError, match="positive"):
        GmshPrimitive.plate(width=-1.0, height=1.0)
