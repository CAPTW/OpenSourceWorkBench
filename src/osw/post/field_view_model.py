"""Viewer-ready field metadata adapters."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from osw.core.result_dataset import ResultDataset
from osw.mesh.mesh_model import MeshData, MeshInfo, MeshModel
from osw.post.field_dataset import (
    FieldArraySummary,
    FieldArtifactSummary,
    FieldDatasetSummary,
    FieldRenderRequest,
    field_dataset_from_result_dataset,
    inspect_field_artifacts,
)


@dataclass(frozen=True)
class FieldViewModel:
    """Field panel data that can be displayed without PyVista."""

    dataset_id: str
    title: str
    source: str = ""
    mesh_info: MeshInfo | None = None
    arrays: tuple[FieldArraySummary, ...] = field(default_factory=tuple)
    artifacts: tuple[FieldArtifactSummary, ...] = field(default_factory=tuple)
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    empty_state_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    mesh_data: MeshData | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "arrays", tuple(self.arrays))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def scalar_fields(self) -> tuple[str, ...]:
        return tuple(array.name for array in self.arrays if array.is_scalar)

    @property
    def vector_fields(self) -> tuple[str, ...]:
        return tuple(array.name for array in self.arrays if array.is_vector)

    @property
    def default_render_request(self) -> FieldRenderRequest:
        scalar = self.scalar_fields[0] if self.scalar_fields else ""
        vector = "" if scalar else (self.vector_fields[0] if self.vector_fields else "")
        return FieldRenderRequest(
            dataset_id=self.dataset_id,
            scalar_field=scalar,
            vector_field=vector,
            mode="scalar" if scalar else ("vector" if vector else "metadata"),
            artifact_path=self.artifacts[0].path if self.artifacts else "",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "title": self.title,
            "source": self.source,
            "mesh_info": self.mesh_info.to_dict() if self.mesh_info is not None else None,
            "arrays": [array.to_dict() for array in self.arrays],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "diagnostics": list(self.diagnostics),
            "empty_state_message": self.empty_state_message,
            "metadata": dict(self.metadata),
            "has_mesh_data": self.mesh_data is not None,
        }


def field_view_model_from_result_dataset(
    dataset: ResultDataset | Mapping[str, Any],
) -> FieldViewModel:
    """Convert ResultDataset metadata or fields into a field viewer model."""

    field_dataset = field_dataset_from_result_dataset(dataset)
    return field_view_model_from_field_dataset(field_dataset)


def field_view_model_from_field_dataset(
    field_dataset: FieldDatasetSummary,
    *,
    mesh_data: MeshData | None = None,
) -> FieldViewModel:
    empty = (
        ""
        if field_dataset.arrays
        else "No mesh field arrays are available for this dataset."
    )
    return FieldViewModel(
        dataset_id=field_dataset.dataset_id,
        title=field_dataset.title or field_dataset.dataset_id or "Field Dataset",
        source=field_dataset.source,
        mesh_info=field_dataset.mesh_info,
        arrays=field_dataset.arrays,
        artifacts=field_dataset.artifacts,
        diagnostics=field_dataset.diagnostics,
        empty_state_message=empty,
        metadata=field_dataset.metadata,
        mesh_data=mesh_data,
    )


def field_view_model_from_mesh_info(mesh_info: MeshInfo) -> FieldViewModel:
    field_dataset = FieldDatasetSummary(
        dataset_id=Path(mesh_info.source_path).stem or "mesh-summary",
        title="Mesh Fields",
        source=mesh_info.source_path,
        mesh_info=mesh_info,
        arrays=_arrays_from_mesh_info(mesh_info),
        diagnostics=mesh_info.warnings,
        metadata={"kind": "field_dataset"},
    )
    return field_view_model_from_field_dataset(field_dataset)


def field_view_model_from_mesh_model(mesh_model: MeshModel) -> FieldViewModel:
    mesh_data = mesh_model.to_mesh_data()
    arrays = [
        _array_from_values(
            name,
            values,
            location="point",
            value_count=len(mesh_model.points),
            source=Path(mesh_model.source_path).name,
        )
        for name, values in mesh_model.point_data.items()
    ]
    arrays.extend(
        _array_from_values(
            name,
            values,
            location="cell",
            value_count=mesh_model.info.element_count,
            source=Path(mesh_model.source_path).name,
        )
        for name, values in mesh_model.cell_data.items()
    )
    field_dataset = FieldDatasetSummary(
        dataset_id=mesh_model.id,
        title=mesh_model.name,
        source=mesh_model.source_path,
        mesh_info=mesh_model.info,
        arrays=tuple(arrays),
        diagnostics=mesh_model.info.warnings,
        metadata={"kind": "field_dataset"},
    )
    return field_view_model_from_field_dataset(field_dataset, mesh_data=mesh_data)


def field_view_model_from_artifacts(path: str | Path) -> FieldViewModel:
    source = Path(path)
    artifacts = inspect_field_artifacts(source)
    arrays = _dedupe_arrays(array for artifact in artifacts for array in artifact.arrays)
    mesh_info = next((artifact.mesh_info for artifact in artifacts if artifact.mesh_info), None)
    diagnostics = tuple(
        dict.fromkeys(
            diagnostic for artifact in artifacts for diagnostic in artifact.diagnostics
        )
    )
    empty = "" if arrays else "No mesh field arrays were discovered in these artifacts."
    return FieldViewModel(
        dataset_id="field-artifacts",
        title="Field Artifacts",
        source=str(source),
        mesh_info=mesh_info,
        arrays=arrays,
        artifacts=artifacts,
        diagnostics=diagnostics,
        empty_state_message=empty,
        metadata={"kind": "field_dataset"},
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
    return tuple(arrays)


def _array_from_values(
    name: str,
    values: object,
    *,
    location: str,
    value_count: int,
    source: str,
) -> FieldArraySummary:
    field_type, components = _field_shape(values, name)
    minimum, maximum = _scalar_range(values) if field_type == "scalar" else (None, None)
    return FieldArraySummary(
        name=name,
        location=location,
        field_type=field_type,
        components=components,
        value_count=value_count,
        minimum=minimum,
        maximum=maximum,
        source=source,
    )


def _field_shape(values: object, name: str) -> tuple[str, tuple[str, ...]]:
    first = _first_value(values)
    if _is_sequence(first):
        count = len(tuple(first))  # type: ignore[arg-type]
        if count in {2, 3}:
            return "vector", ("x", "y", "z")[:count]
        return "tensor", tuple(f"c{index + 1}" for index in range(count))
    return "scalar", (name,)


def _scalar_range(values: object) -> tuple[float | None, float | None]:
    if not _is_sequence(values):
        return None, None
    numbers = []
    for item in values:  # type: ignore[union-attr]
        try:
            numbers.append(float(item))
        except (TypeError, ValueError):
            continue
    return (min(numbers), max(numbers)) if numbers else (None, None)


def _first_value(values: object) -> object:
    if not _is_sequence(values):
        return None
    for item in values:  # type: ignore[union-attr]
        return item
    return None


def _is_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def _dedupe_arrays(arrays: Iterable[FieldArraySummary]) -> tuple[FieldArraySummary, ...]:
    seen: set[tuple[str, str]] = set()
    unique = []
    for array in arrays:
        key = (array.name, array.location)
        if key in seen:
            continue
        seen.add(key)
        unique.append(array)
    return tuple(unique)


__all__ = [
    "FieldViewModel",
    "field_view_model_from_artifacts",
    "field_view_model_from_field_dataset",
    "field_view_model_from_mesh_info",
    "field_view_model_from_mesh_model",
    "field_view_model_from_result_dataset",
]
