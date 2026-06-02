"""Field dataset summaries and read-only artifact inspection."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from osw.core.result_dataset import ResultDataset
from osw.mesh.mesh_model import MeshBounds, MeshCellBlock, MeshInfo

FIELD_ARTIFACT_EXTENSIONS = {".vtk", ".vtu", ".json"}


@dataclass(frozen=True)
class FieldArraySummary:
    """Serializable summary of one mesh-associated field array."""

    name: str
    location: str = "unknown"
    field_type: str = ""
    components: tuple[str, ...] = field(default_factory=tuple)
    value_count: int = 0
    unit: str = ""
    minimum: float | None = None
    maximum: float | None = None
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        components = tuple(str(item) for item in self.components)
        field_type = str(self.field_type or _infer_field_type(components)).lower()
        object.__setattr__(self, "location", str(self.location or "unknown").lower())
        object.__setattr__(self, "field_type", field_type)
        object.__setattr__(self, "components", components)
        object.__setattr__(self, "value_count", int(self.value_count or 0))
        object.__setattr__(self, "minimum", _optional_float(self.minimum))
        object.__setattr__(self, "maximum", _optional_float(self.maximum))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def component_count(self) -> int:
        return len(self.components)

    @property
    def is_scalar(self) -> bool:
        return self.field_type == "scalar"

    @property
    def is_vector(self) -> bool:
        return self.field_type == "vector"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location,
            "field_type": self.field_type,
            "components": list(self.components),
            "value_count": self.value_count,
            "unit": self.unit,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> FieldArraySummary:
        if not isinstance(data, Mapping):
            msg = "FieldArraySummary data must be a mapping."
            raise TypeError(msg)
        return cls(
            name=str(data.get("name", "")),
            location=str(data.get("location", "unknown")),
            field_type=str(data.get("field_type", data.get("kind", ""))),
            components=tuple(str(item) for item in data.get("components", ()) or ()),
            value_count=int(data.get("value_count", data.get("count", 0)) or 0),
            unit=str(data.get("unit", "")),
            minimum=_optional_float(data.get("minimum", data.get("min"))),
            maximum=_optional_float(data.get("maximum", data.get("max"))),
            source=str(data.get("source", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class FieldArtifactSummary:
    """Read-only summary of a field-capable artifact."""

    path: str
    role: str = "field"
    format: str = ""
    exists: bool | None = None
    size_bytes: int | None = None
    mesh_info: MeshInfo | None = None
    arrays: tuple[FieldArraySummary, ...] = field(default_factory=tuple)
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        artifact_path = Path(self.path) if self.path else None
        exists = (
            bool(artifact_path.exists())
            if self.exists is None and artifact_path is not None
            else bool(self.exists)
        )
        size = self.size_bytes
        if size is None and exists and artifact_path is not None and artifact_path.is_file():
            size = artifact_path.stat().st_size
        object.__setattr__(self, "path", str(self.path))
        object.__setattr__(self, "role", str(self.role or "field"))
        object.__setattr__(
            self,
            "format",
            str(self.format or (artifact_path.suffix.lstrip(".") if artifact_path else "")),
        )
        object.__setattr__(self, "exists", exists)
        object.__setattr__(self, "size_bytes", int(size) if size is not None else None)
        object.__setattr__(self, "arrays", tuple(self.arrays))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def scalar_arrays(self) -> tuple[FieldArraySummary, ...]:
        return tuple(array for array in self.arrays if array.is_scalar)

    @property
    def vector_arrays(self) -> tuple[FieldArraySummary, ...]:
        return tuple(array for array in self.arrays if array.is_vector)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "role": self.role,
            "format": self.format,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "mesh_info": self.mesh_info.to_dict() if self.mesh_info is not None else None,
            "arrays": [array.to_dict() for array in self.arrays],
            "diagnostics": list(self.diagnostics),
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> FieldArtifactSummary:
        if not isinstance(data, Mapping):
            msg = "FieldArtifactSummary data must be a mapping."
            raise TypeError(msg)
        mesh_payload = data.get("mesh_info")
        return cls(
            path=str(data.get("path", "")),
            role=str(data.get("role", "field")),
            format=str(data.get("format", "")),
            exists=_optional_bool(data.get("exists")),
            size_bytes=_optional_int(data.get("size_bytes")),
            mesh_info=(
                MeshInfo.from_dict(mesh_payload) if isinstance(mesh_payload, Mapping) else None
            ),
            arrays=tuple(
                FieldArraySummary.from_dict(item)
                for item in data.get("arrays", ()) or ()
                if isinstance(item, Mapping)
            ),
            diagnostics=tuple(str(item) for item in data.get("diagnostics", ()) or ()),
            source=str(data.get("source", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class FieldRenderRequest:
    """Viewer render request that stays serializable and execution-free."""

    dataset_id: str
    scalar_field: str = ""
    vector_field: str = ""
    mode: str = "scalar"
    artifact_path: str = ""
    screenshot_path: str = ""
    off_screen: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        mode = str(self.mode or ("vector" if self.vector_field else "scalar")).lower()
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "scalar_field": self.scalar_field,
            "vector_field": self.vector_field,
            "mode": self.mode,
            "artifact_path": self.artifact_path,
            "screenshot_path": self.screenshot_path,
            "off_screen": self.off_screen,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> FieldRenderRequest:
        if not isinstance(data, Mapping):
            msg = "FieldRenderRequest data must be a mapping."
            raise TypeError(msg)
        return cls(
            dataset_id=str(data.get("dataset_id", "")),
            scalar_field=str(data.get("scalar_field", "")),
            vector_field=str(data.get("vector_field", "")),
            mode=str(data.get("mode", "scalar")),
            artifact_path=str(data.get("artifact_path", "")),
            screenshot_path=str(data.get("screenshot_path", "")),
            off_screen=bool(data.get("off_screen", True)),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class FieldRenderResult:
    """Result of an optional rendering attempt."""

    status: str
    message: str
    rendered: bool = False
    request: FieldRenderRequest | None = None
    screenshot_path: str = ""
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", str(self.status))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "rendered": self.rendered,
            "request": self.request.to_dict() if self.request is not None else None,
            "screenshot_path": self.screenshot_path,
            "diagnostics": list(self.diagnostics),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> FieldRenderResult:
        if not isinstance(data, Mapping):
            msg = "FieldRenderResult data must be a mapping."
            raise TypeError(msg)
        request_payload = data.get("request")
        return cls(
            status=str(data.get("status", "")),
            message=str(data.get("message", "")),
            rendered=bool(data.get("rendered", False)),
            request=(
                FieldRenderRequest.from_dict(request_payload)
                if isinstance(request_payload, Mapping)
                else None
            ),
            screenshot_path=str(data.get("screenshot_path", "")),
            diagnostics=tuple(str(item) for item in data.get("diagnostics", ()) or ()),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class FieldDatasetSummary:
    """Viewer-ready field metadata extracted from results, meshes, or artifacts."""

    dataset_id: str
    title: str = ""
    source: str = ""
    mesh_info: MeshInfo | None = None
    arrays: tuple[FieldArraySummary, ...] = field(default_factory=tuple)
    artifacts: tuple[FieldArtifactSummary, ...] = field(default_factory=tuple)
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "arrays", tuple(self.arrays))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def scalar_arrays(self) -> tuple[FieldArraySummary, ...]:
        return tuple(array for array in self.arrays if array.is_scalar)

    @property
    def vector_arrays(self) -> tuple[FieldArraySummary, ...]:
        return tuple(array for array in self.arrays if array.is_vector)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "title": self.title,
            "source": self.source,
            "mesh_info": self.mesh_info.to_dict() if self.mesh_info is not None else None,
            "arrays": [array.to_dict() for array in self.arrays],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "diagnostics": list(self.diagnostics),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> FieldDatasetSummary:
        if not isinstance(data, Mapping):
            msg = "FieldDatasetSummary data must be a mapping."
            raise TypeError(msg)
        mesh_payload = data.get("mesh_info")
        return cls(
            dataset_id=str(data.get("dataset_id", "")),
            title=str(data.get("title", "")),
            source=str(data.get("source", "")),
            mesh_info=(
                MeshInfo.from_dict(mesh_payload) if isinstance(mesh_payload, Mapping) else None
            ),
            arrays=tuple(
                FieldArraySummary.from_dict(item)
                for item in data.get("arrays", data.get("field_arrays", ())) or ()
                if isinstance(item, Mapping)
            ),
            artifacts=tuple(
                FieldArtifactSummary.from_dict(item)
                for item in data.get("artifacts", data.get("field_artifacts", ())) or ()
                if isinstance(item, Mapping)
            ),
            diagnostics=tuple(str(item) for item in data.get("diagnostics", ()) or ()),
            metadata=dict(data.get("metadata", {}) or {}),
        )


def field_dataset_from_result_dataset(
    dataset: ResultDataset | Mapping[str, Any],
) -> FieldDatasetSummary:
    """Extract field metadata from a ResultDataset without rendering or parsing solvers."""

    normalized = dataset if isinstance(dataset, ResultDataset) else ResultDataset.from_dict(dataset)
    metadata = normalized.metadata
    mesh_payload = metadata.get("mesh_info")
    mesh_info = MeshInfo.from_dict(mesh_payload) if isinstance(mesh_payload, Mapping) else None
    arrays = _arrays_from_metadata(metadata)
    if not arrays:
        arrays = _arrays_from_result_fields(normalized)
    if not arrays and mesh_info is not None:
        arrays = _arrays_from_mesh_info(mesh_info)
    artifacts = _artifacts_from_metadata(metadata)
    title = str(metadata.get("title", "") or normalized.dataset_id or "Field Dataset")
    diagnostics = [*normalized.warnings, *_metadata_diagnostics(metadata)]
    return FieldDatasetSummary(
        dataset_id=normalized.dataset_id,
        title=title,
        source=normalized.source,
        mesh_info=mesh_info,
        arrays=arrays,
        artifacts=artifacts,
        diagnostics=tuple(dict.fromkeys(diagnostics)),
        metadata=dict(metadata),
    )


def field_dataset_from_json_file(path: str | Path) -> FieldDatasetSummary:
    """Load a FieldDatasetSummary or ResultDataset JSON file into field metadata."""

    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        msg = "Field dataset JSON must contain an object."
        raise ValueError(msg)
    if "arrays" in payload and "dataset_id" in payload and "solver" not in payload:
        return FieldDatasetSummary.from_dict(payload)
    return field_dataset_from_result_dataset(ResultDataset.from_dict(payload))


def inspect_field_artifacts(path: str | Path) -> tuple[FieldArtifactSummary, ...]:
    """Inspect a field artifact file or directory without executing external tools."""

    source = Path(path)
    if source.is_dir():
        return tuple(
            inspect_field_artifact(item)
            for item in sorted(source.iterdir())
            if item.is_file() and item.suffix.lower() in FIELD_ARTIFACT_EXTENSIONS
        )
    return (inspect_field_artifact(source),)


def inspect_field_artifact(path: str | Path) -> FieldArtifactSummary:
    """Inspect lightweight metadata from known field artifact types."""

    artifact_path = Path(path)
    suffix = artifact_path.suffix.lower()
    if not artifact_path.exists():
        return FieldArtifactSummary(
            path=str(artifact_path),
            format=suffix.lstrip("."),
            exists=False,
            diagnostics=(f"Missing field artifact: {artifact_path}",),
        )
    if suffix == ".vtk":
        return _inspect_legacy_vtk(artifact_path)
    if suffix == ".vtu":
        return _inspect_vtu_xml(artifact_path)
    if suffix == ".json":
        return _inspect_field_json(artifact_path)
    return FieldArtifactSummary(
        path=str(artifact_path),
        format=suffix.lstrip("."),
        exists=True,
        diagnostics=(f"Unsupported field artifact format: {suffix or '<none>'}",),
    )


def _inspect_legacy_vtk(path: Path) -> FieldArtifactSummary:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return FieldArtifactSummary(
            path=str(path),
            format="vtk",
            exists=path.exists(),
            diagnostics=(f"Could not read field artifact: {path}: {exc}",),
        )
    node_count = 0
    element_count = 0
    points: list[tuple[float, float, float]] = []
    arrays: list[FieldArraySummary] = []
    point_names: list[str] = []
    cell_names: list[str] = []
    location = "unknown"
    location_count = 0
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        upper = stripped.upper()
        parts = stripped.split()
        if upper.startswith("POINTS ") and len(parts) >= 2:
            node_count = _safe_int(parts[1])
            values, consumed = _collect_numeric_values(lines, index + 1, node_count * 3)
            points = [
                (values[item], values[item + 1], values[item + 2])
                for item in range(0, len(values) - 2, 3)
            ][:node_count]
            index += consumed
        elif upper.startswith(("POLYGONS ", "CELLS ")) and len(parts) >= 2:
            element_count = _safe_int(parts[1])
        elif upper.startswith("POINT_DATA ") and len(parts) >= 2:
            location = "point"
            location_count = _safe_int(parts[1])
        elif upper.startswith("CELL_DATA ") and len(parts) >= 2:
            location = "cell"
            location_count = _safe_int(parts[1])
        elif upper.startswith("SCALARS ") and len(parts) >= 3:
            name = parts[1]
            component_count = _safe_int(parts[3]) if len(parts) >= 4 else 1
            components = (name,) if component_count <= 1 else _component_names(component_count)
            values, consumed = _vtk_scalar_values(
                lines,
                index + 1,
                location_count * component_count,
            )
            arrays.append(
                FieldArraySummary(
                    name=name,
                    location=location,
                    field_type=_infer_field_type(components),
                    components=components,
                    value_count=location_count,
                    minimum=min(values) if values else None,
                    maximum=max(values) if values else None,
                    source=path.name,
                    metadata={"data_type": parts[2]},
                )
            )
            (point_names if location == "point" else cell_names).append(name)
            index += consumed
        elif upper.startswith("VECTORS ") and len(parts) >= 3:
            name = parts[1]
            arrays.append(
                FieldArraySummary(
                    name=name,
                    location=location,
                    field_type="vector",
                    components=("x", "y", "z"),
                    value_count=location_count,
                    source=path.name,
                    metadata={"data_type": parts[2]},
                )
            )
            (point_names if location == "point" else cell_names).append(name)
        index += 1
    cell_blocks = (MeshCellBlock("triangle", count=element_count),) if element_count else ()
    mesh_info = MeshInfo(
        source_path=str(path),
        format="vtk",
        node_count=node_count,
        element_count=element_count,
        cell_blocks=cell_blocks,
        bounds=_bounds_from_points(points),
        point_data_names=point_names,
        cell_data_names=cell_names,
    )
    diagnostics = () if arrays else ("No field arrays discovered in legacy VTK artifact.",)
    return FieldArtifactSummary(
        path=str(path),
        format="vtk",
        exists=True,
        mesh_info=mesh_info,
        arrays=tuple(arrays),
        diagnostics=diagnostics,
    )


def _inspect_vtu_xml(path: Path) -> FieldArtifactSummary:
    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError) as exc:
        return FieldArtifactSummary(
            path=str(path),
            format="vtu",
            exists=path.exists(),
            diagnostics=(f"Could not inspect VTU field artifact: {path}: {exc}",),
        )
    piece = root.find(".//{*}Piece")
    node_count = _safe_int(piece.get("NumberOfPoints", "0")) if piece is not None else 0
    element_count = _safe_int(piece.get("NumberOfCells", "0")) if piece is not None else 0
    arrays: list[FieldArraySummary] = []
    for section_name, location, count in (
        ("PointData", "point", node_count),
        ("CellData", "cell", element_count),
    ):
        section = root.find(f".//{{*}}{section_name}")
        if section is None:
            continue
        for data_array in section.findall("{*}DataArray"):
            name = data_array.get("Name", "")
            if not name:
                continue
            component_count = _safe_int(data_array.get("NumberOfComponents", "1")) or 1
            components = (name,) if component_count == 1 else _component_names(component_count)
            arrays.append(
                FieldArraySummary(
                    name=name,
                    location=location,
                    field_type=_infer_field_type(components),
                    components=components,
                    value_count=count,
                    source=path.name,
                    metadata={"data_type": data_array.get("type", "")},
                )
            )
    mesh_info = MeshInfo(
        source_path=str(path),
        format="vtu",
        node_count=node_count,
        element_count=element_count,
        point_data_names=[array.name for array in arrays if array.location == "point"],
        cell_data_names=[array.name for array in arrays if array.location == "cell"],
    )
    diagnostics = () if arrays else ("No VTU PointData or CellData arrays discovered.",)
    return FieldArtifactSummary(
        path=str(path),
        format="vtu",
        exists=True,
        mesh_info=mesh_info,
        arrays=tuple(arrays),
        diagnostics=diagnostics,
    )


def _inspect_field_json(path: Path) -> FieldArtifactSummary:
    try:
        field_dataset = field_dataset_from_json_file(path)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return FieldArtifactSummary(
            path=str(path),
            format="json",
            exists=path.exists(),
            diagnostics=(f"Could not inspect field JSON artifact: {path}: {exc}",),
        )
    return FieldArtifactSummary(
        path=str(path),
        format="json",
        exists=True,
        mesh_info=field_dataset.mesh_info,
        arrays=field_dataset.arrays,
        diagnostics=field_dataset.diagnostics,
        metadata={"dataset_id": field_dataset.dataset_id, "title": field_dataset.title},
    )


def _arrays_from_metadata(metadata: Mapping[str, Any]) -> tuple[FieldArraySummary, ...]:
    return tuple(
        FieldArraySummary.from_dict(item)
        for item in metadata.get("field_arrays", metadata.get("arrays", ())) or ()
        if isinstance(item, Mapping)
    )


def _artifacts_from_metadata(metadata: Mapping[str, Any]) -> tuple[FieldArtifactSummary, ...]:
    return tuple(
        FieldArtifactSummary.from_dict(item)
        for item in metadata.get("field_artifacts", metadata.get("artifacts", ())) or ()
        if isinstance(item, Mapping)
    )


def _arrays_from_mesh_info(mesh_info: MeshInfo) -> tuple[FieldArraySummary, ...]:
    arrays: list[FieldArraySummary] = []
    arrays.extend(
        FieldArraySummary(
            name=name,
            location="point",
            field_type="scalar",
            components=(name,),
            value_count=mesh_info.node_count,
            source=Path(mesh_info.source_path).name,
        )
        for name in mesh_info.point_data_names
    )
    arrays.extend(
        FieldArraySummary(
            name=name,
            location="cell",
            field_type="scalar",
            components=(name,),
            value_count=mesh_info.element_count,
            source=Path(mesh_info.source_path).name,
        )
        for name in mesh_info.cell_data_names
    )
    arrays.extend(
        FieldArraySummary(
            name=name,
            location="field",
            field_type="scalar",
            components=(name,),
            value_count=1,
            source=Path(mesh_info.source_path).name,
        )
        for name in mesh_info.field_data_names
    )
    return tuple(arrays)


def _arrays_from_result_fields(dataset: ResultDataset) -> tuple[FieldArraySummary, ...]:
    arrays = []
    for field_item in dataset.fields:
        location = field_item.location.lower()
        if location not in {"node", "point", "cell", "element", "face"}:
            continue
        arrays.append(
            FieldArraySummary(
                name=field_item.name,
                location="point" if location == "node" else location,
                field_type=_infer_field_type(field_item.components),
                components=field_item.components,
                value_count=len(field_item.rows),
                unit=field_item.unit,
                source=dataset.source,
            )
        )
    return tuple(arrays)


def _metadata_diagnostics(metadata: Mapping[str, Any]) -> tuple[str, ...]:
    diagnostics = metadata.get("diagnostics")
    if not isinstance(diagnostics, Mapping):
        return ()
    messages = []
    for message in diagnostics.get("messages", ()) or ():
        if isinstance(message, Mapping):
            text = str(message.get("message", ""))
            if text:
                messages.append(text)
    return tuple(messages)


def _infer_field_type(components: Sequence[str]) -> str:
    count = len(tuple(components))
    if count <= 1:
        return "scalar"
    if count in {2, 3}:
        return "vector"
    return "tensor"


def _component_names(count: int) -> tuple[str, ...]:
    if count == 2:
        return ("x", "y")
    if count == 3:
        return ("x", "y", "z")
    return tuple(f"c{index + 1}" for index in range(max(count, 0)))


def _bounds_from_points(points: Sequence[Sequence[float]]) -> MeshBounds:
    if not points:
        return MeshBounds()
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    zs = [float(point[2]) for point in points]
    return MeshBounds(
        min_x=min(xs),
        min_y=min(ys),
        min_z=min(zs),
        max_x=max(xs),
        max_y=max(ys),
        max_z=max(zs),
    )


def _collect_numeric_values(
    lines: Sequence[str],
    start_index: int,
    expected_count: int,
) -> tuple[list[float], int]:
    values: list[float] = []
    consumed = 0
    for line in lines[start_index:]:
        stripped = line.strip()
        if not stripped:
            consumed += 1
            continue
        if _looks_like_vtk_keyword(stripped) and values:
            break
        for part in stripped.split():
            try:
                values.append(float(part))
            except ValueError:
                pass
        consumed += 1
        if len(values) >= expected_count:
            break
    return values[:expected_count], consumed


def _vtk_scalar_values(
    lines: Sequence[str],
    start_index: int,
    expected_count: int,
) -> tuple[list[float], int]:
    index = start_index
    consumed = 0
    if index < len(lines) and lines[index].strip().upper().startswith("LOOKUP_TABLE"):
        index += 1
        consumed += 1
    values, extra = _collect_numeric_values(lines, index, expected_count)
    return values, consumed + extra


def _looks_like_vtk_keyword(text: str) -> bool:
    first = text.split()[0].upper() if text.split() else ""
    return first in {
        "POINTS",
        "POLYGONS",
        "CELLS",
        "POINT_DATA",
        "CELL_DATA",
        "SCALARS",
        "VECTORS",
        "FIELD",
        "LOOKUP_TABLE",
    }


def _safe_int(value: object) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)  # type: ignore[arg-type]


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)  # type: ignore[arg-type]


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    return bool(value)


__all__ = [
    "FIELD_ARTIFACT_EXTENSIONS",
    "FieldArraySummary",
    "FieldArtifactSummary",
    "FieldDatasetSummary",
    "FieldRenderRequest",
    "FieldRenderResult",
    "field_dataset_from_json_file",
    "field_dataset_from_result_dataset",
    "inspect_field_artifact",
    "inspect_field_artifacts",
]
