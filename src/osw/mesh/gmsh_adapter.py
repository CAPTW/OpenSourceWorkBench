"""Dependency-guarded Gmsh adapter for small educational mesh templates."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

from .mesh_model import MeshData, MeshInfo
from .meshio_bridge import export_vtu, load_mesh, load_mesh_info

PrimitiveKind = Literal["plate", "box"]
Point3D = tuple[float, float, float]


class GmshAdapterError(RuntimeError):
    """Raised when Gmsh mesh generation cannot proceed safely."""


@dataclass(frozen=True)
class MeshSizeControl:
    """Small mesh size control model for v0.1 Gmsh templates."""

    target_size: float = 1.0
    min_size: float | None = None
    max_size: float | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("target mesh size", self.target_size),
            ("minimum mesh size", self.min_size),
            ("maximum mesh size", self.max_size),
        ):
            if value is not None and value <= 0:
                msg = f"{label} must be positive."
                raise GmshAdapterError(msg)
        if (
            self.min_size is not None
            and self.max_size is not None
            and self.min_size > self.max_size
        ):
            msg = "minimum mesh size must be less than or equal to maximum mesh size."
            raise GmshAdapterError(msg)

    @property
    def effective_min(self) -> float:
        return self.min_size if self.min_size is not None else self.target_size

    @property
    def effective_max(self) -> float:
        return self.max_size if self.max_size is not None else self.target_size

    def to_dict(self) -> dict[str, float | None]:
        return {
            "target_size": self.target_size,
            "min_size": self.min_size,
            "max_size": self.max_size,
        }


@dataclass(frozen=True)
class GmshPrimitive:
    """Primitive geometry template used when CAD bridge input is unavailable."""

    kind: PrimitiveKind
    dimensions: tuple[float, float, float]
    origin: Point3D = (0.0, 0.0, 0.0)
    name: str = "domain"

    def __post_init__(self) -> None:
        object.__setattr__(self, "origin", _point3d(self.origin, label="origin"))
        object.__setattr__(
            self,
            "dimensions",
            _point3d(self.dimensions, label="dimensions"),
        )
        _validate_primitive(self.kind, self.dimensions)
        if not self.name:
            msg = "Gmsh primitive name is required."
            raise GmshAdapterError(msg)

    @classmethod
    def plate(
        cls,
        *,
        width: float,
        height: float,
        origin: Point3D = (0.0, 0.0, 0.0),
        name: str = "plate",
    ) -> GmshPrimitive:
        return cls(kind="plate", dimensions=(width, height, 0.0), origin=origin, name=name)

    @classmethod
    def box(
        cls,
        *,
        width: float,
        depth: float,
        height: float,
        origin: Point3D = (0.0, 0.0, 0.0),
        name: str = "box",
    ) -> GmshPrimitive:
        return cls(kind="box", dimensions=(width, depth, height), origin=origin, name=name)

    @property
    def mesh_dimension(self) -> int:
        return 2 if self.kind == "plate" else 3


@dataclass(frozen=True)
class PhysicalGroupMetadata:
    """Placeholder metadata for physical groups exported by Gmsh."""

    name: str
    dimension: int
    tag: int
    entities: tuple[int, ...]
    role: str = "domain"

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "dimension": self.dimension,
            "tag": self.tag,
            "entities": list(self.entities),
            "role": self.role,
        }


@dataclass(frozen=True)
class GmshMeshResult:
    msh_path: Path
    mesh_size: MeshSizeControl
    primitive: GmshPrimitive
    physical_groups: tuple[PhysicalGroupMetadata, ...]
    mesh_info: MeshInfo | None = None
    vtu_path: Path | None = None


def is_gmsh_available() -> bool:
    try:
        _load_gmsh()
    except GmshAdapterError:
        return False
    return True


def generate_primitive_mesh(
    primitive: GmshPrimitive,
    output_path: str | Path,
    *,
    mesh_size: MeshSizeControl | None = None,
    gmsh_module: Any | None = None,
    meshio_module: Any | None = None,
    vtu_path: str | Path | None = None,
) -> GmshMeshResult:
    """Generate a small primitive mesh with Gmsh and optional meshio conversion."""

    target = _msh_path(output_path)
    control = mesh_size or MeshSizeControl()
    gmsh = gmsh_module if gmsh_module is not None else _load_gmsh()
    target.parent.mkdir(parents=True, exist_ok=True)

    initialized = False
    physical_groups: tuple[PhysicalGroupMetadata, ...]
    try:
        gmsh.initialize()
        initialized = True
        gmsh.model.add(primitive.name)
        _apply_mesh_size(gmsh, control)
        entity_tag = _add_primitive(gmsh, primitive)
        gmsh.model.occ.synchronize()
        physical_groups = (_add_domain_physical_group(gmsh, primitive, entity_tag),)
        gmsh.model.mesh.generate(primitive.mesh_dimension)
        gmsh.write(str(target))
    except GmshAdapterError:
        raise
    except Exception as exc:
        msg = f"Could not generate Gmsh mesh '{target}': {exc}"
        raise GmshAdapterError(msg) from exc
    finally:
        if initialized:
            gmsh.finalize()

    mesh_info = None
    converted_vtu = None
    if meshio_module is not None:
        mesh_info = load_gmsh_mesh_info(target, meshio_module=meshio_module)
    if vtu_path is not None:
        converted_vtu = convert_gmsh_msh_to_vtu(
            target,
            vtu_path,
            meshio_module=meshio_module,
        )
        if mesh_info is None and meshio_module is not None:
            mesh_info = load_gmsh_mesh_info(target, meshio_module=meshio_module)

    return GmshMeshResult(
        msh_path=target,
        mesh_size=control,
        primitive=primitive,
        physical_groups=physical_groups,
        mesh_info=mesh_info,
        vtu_path=converted_vtu,
    )


def load_gmsh_mesh(path: str | Path, *, meshio_module: Any | None = None) -> MeshData:
    """Load a Gmsh `.msh` file through the existing meshio bridge."""

    return load_mesh(_msh_path(path), meshio_module=meshio_module)


def load_gmsh_mesh_info(path: str | Path, *, meshio_module: Any | None = None) -> MeshInfo:
    """Load preview-safe mesh metadata from a Gmsh `.msh` file."""

    return load_mesh_info(_msh_path(path), meshio_module=meshio_module)


def convert_gmsh_msh_to_vtu(
    msh_path: str | Path,
    vtu_path: str | Path,
    *,
    meshio_module: Any | None = None,
) -> Path:
    """Convert a Gmsh `.msh` output to VTU via meshio."""

    mesh_data = load_gmsh_mesh(msh_path, meshio_module=meshio_module)
    return export_vtu(mesh_data, vtu_path, meshio_module=meshio_module)


def _load_gmsh() -> ModuleType:
    try:
        return import_module("gmsh")
    except ImportError as exc:
        msg = (
            "gmsh is not installed. Install the optional mesh extra, for example "
            "`pip install open-solver-workbench[mesh]`, before generating Gmsh meshes."
        )
        raise GmshAdapterError(msg) from exc


def _msh_path(path: str | Path) -> Path:
    target = Path(path)
    if target.suffix.lower() != ".msh":
        msg = "Gmsh mesh path must use the .msh extension."
        raise GmshAdapterError(msg)
    return target


def _apply_mesh_size(gmsh: Any, control: MeshSizeControl) -> None:
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", control.effective_min)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", control.effective_max)


def _add_primitive(gmsh: Any, primitive: GmshPrimitive) -> int:
    x, y, z = primitive.origin
    dx, dy, dz = primitive.dimensions
    if primitive.kind == "plate":
        return int(gmsh.model.occ.addRectangle(x, y, z, dx, dy))
    if primitive.kind == "box":
        return int(gmsh.model.occ.addBox(x, y, z, dx, dy, dz))
    msg = f"Unsupported Gmsh primitive kind: {primitive.kind}"
    raise GmshAdapterError(msg)


def _add_domain_physical_group(
    gmsh: Any,
    primitive: GmshPrimitive,
    entity_tag: int,
) -> PhysicalGroupMetadata:
    physical_tag = 1
    gmsh.model.addPhysicalGroup(primitive.mesh_dimension, [entity_tag], physical_tag)
    gmsh.model.setPhysicalName(primitive.mesh_dimension, physical_tag, primitive.name)
    return PhysicalGroupMetadata(
        name=primitive.name,
        dimension=primitive.mesh_dimension,
        tag=physical_tag,
        entities=(entity_tag,),
    )


def _point3d(values: tuple[float, float, float], *, label: str) -> Point3D:
    if len(values) != 3:
        msg = f"Gmsh primitive {label} must contain exactly three values."
        raise GmshAdapterError(msg)
    return (float(values[0]), float(values[1]), float(values[2]))


def _validate_primitive(kind: PrimitiveKind, dimensions: Point3D) -> None:
    dx, dy, dz = dimensions
    if kind == "plate":
        if dx <= 0 or dy <= 0:
            msg = "Gmsh plate width and height must be positive."
            raise GmshAdapterError(msg)
        return
    if kind == "box":
        if dx <= 0 or dy <= 0 or dz <= 0:
            msg = "Gmsh box width, depth, and height must be positive."
            raise GmshAdapterError(msg)
        return
    msg = f"Unsupported Gmsh primitive kind: {kind}"
    raise GmshAdapterError(msg)
