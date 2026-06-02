"""Structured result dataset contracts for solver and script outputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class ResultDatasetKind(StrEnum):
    CALCULIX_SUMMARY = "calculix_summary"
    OPENFOAM_RESIDUALS = "openfoam_residuals"
    COOLPROP_PROPERTY = "coolprop_property"
    COOLPROP_SWEEP = "coolprop_sweep"
    CANTERA_REACTOR = "cantera_reactor"
    FIGURE_DATASET = "figure_dataset"
    MAT_WORKSPACE = "mat_workspace"
    BOUNDARY_CURVE = "boundary_curve"
    MESH_SUMMARY = "mesh_summary"
    GENERIC_TABLE = "generic_table"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ResultScalar:
    name: str
    value: float | int | str
    unit: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultScalar:
        if not isinstance(data, Mapping):
            msg = "ResultScalar data must be a mapping."
            raise TypeError(msg)
        return cls(
            name=str(data.get("name", "")),
            value=_scalar_value(data.get("value", "")),
            unit=str(data.get("unit", "")),
            source=str(data.get("source", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ResultSeries:
    name: str
    x_values: tuple[float, ...] = field(default_factory=tuple)
    y_values: tuple[float, ...] = field(default_factory=tuple)
    x_unit: str = ""
    y_unit: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "x_values", tuple(float(item) for item in self.x_values))
        object.__setattr__(self, "y_values", tuple(float(item) for item in self.y_values))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "x_values": list(self.x_values),
            "y_values": list(self.y_values),
            "x_unit": self.x_unit,
            "y_unit": self.y_unit,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultSeries:
        if not isinstance(data, Mapping):
            msg = "ResultSeries data must be a mapping."
            raise TypeError(msg)
        return cls(
            name=str(data.get("name", "")),
            x_values=tuple(float(item) for item in data.get("x_values", ()) or ()),
            y_values=tuple(float(item) for item in data.get("y_values", ()) or ()),
            x_unit=str(data.get("x_unit", "")),
            y_unit=str(data.get("y_unit", "")),
            source=str(data.get("source", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ResultTable:
    table_id: str
    title: str = ""
    columns: tuple[str, ...] = field(default_factory=tuple)
    rows: tuple[tuple[str, ...], ...] = field(default_factory=tuple)
    truncated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(str(item) for item in self.columns))
        object.__setattr__(
            self,
            "rows",
            tuple(tuple(str(cell) for cell in row) for row in self.rows),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "title": self.title,
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
            "truncated": self.truncated,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultTable:
        if not isinstance(data, Mapping):
            msg = "ResultTable data must be a mapping."
            raise TypeError(msg)
        return cls(
            table_id=str(data.get("table_id", "")),
            title=str(data.get("title", "")),
            columns=tuple(str(item) for item in data.get("columns", ()) or ()),
            rows=tuple(
                tuple(str(cell) for cell in row)
                for row in data.get("rows", ()) or ()
            ),
            truncated=bool(data.get("truncated", False)),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ResultArtifactRef:
    path: str
    role: str = "artifact"
    format: str = ""
    exists: bool = False
    size_bytes: int | None = None
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", str(self.path))
        object.__setattr__(
            self,
            "size_bytes",
            int(self.size_bytes) if self.size_bytes is not None else None,
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_path(
        cls,
        path: str | Path,
        *,
        role: str = "artifact",
        format: str = "",
        source: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> ResultArtifactRef:
        artifact_path = Path(path)
        exists = artifact_path.exists()
        size = artifact_path.stat().st_size if exists and artifact_path.is_file() else None
        return cls(
            path=str(artifact_path),
            role=role,
            format=format or artifact_path.suffix.lstrip("."),
            exists=exists,
            size_bytes=size,
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "role": self.role,
            "format": self.format,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultArtifactRef:
        if not isinstance(data, Mapping):
            msg = "ResultArtifactRef data must be a mapping."
            raise TypeError(msg)
        path = str(data.get("path", ""))
        exists_payload = data.get("exists")
        if exists_payload is None and path:
            exists = Path(path).exists()
        else:
            exists = bool(exists_payload)
        return cls(
            path=path,
            role=str(data.get("role", data.get("kind", "artifact"))),
            format=str(data.get("format", "")),
            exists=exists,
            size_bytes=_optional_int(data.get("size_bytes")),
            source=str(data.get("source", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ResultDatasetSummary:
    dataset_id: str
    title: str = ""
    kind: str = ResultDatasetKind.UNKNOWN.value
    source: str = ""
    scalar_count: int = 0
    series_count: int = 0
    table_count: int = 0
    figure_count: int = 0
    artifact_count: int = 0
    warning_count: int = 0
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _kind_value(self.kind))
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "title": self.title,
            "kind": self.kind,
            "source": self.source,
            "scalar_count": self.scalar_count,
            "series_count": self.series_count,
            "table_count": self.table_count,
            "figure_count": self.figure_count,
            "artifact_count": self.artifact_count,
            "warning_count": self.warning_count,
            "diagnostics": list(self.diagnostics),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultDatasetSummary:
        if not isinstance(data, Mapping):
            msg = "ResultDatasetSummary data must be a mapping."
            raise TypeError(msg)
        return cls(
            dataset_id=str(data.get("dataset_id", "")),
            title=str(data.get("title", "")),
            kind=str(data.get("kind", ResultDatasetKind.UNKNOWN.value)),
            source=str(data.get("source", "")),
            scalar_count=int(data.get("scalar_count", 0)),
            series_count=int(data.get("series_count", 0)),
            table_count=int(data.get("table_count", 0)),
            figure_count=int(data.get("figure_count", 0)),
            artifact_count=int(data.get("artifact_count", 0)),
            warning_count=int(data.get("warning_count", 0)),
            diagnostics=tuple(str(item) for item in data.get("diagnostics", ()) or ()),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ResultCatalog:
    catalog_id: str
    project_name: str = ""
    datasets: tuple[ResultDataset, ...] = field(default_factory=tuple)
    selected_dataset_id: str = ""
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "datasets",
            tuple(_coerce_dataset(dataset) for dataset in self.datasets),
        )
        selected = self.selected_dataset_id
        if not selected and self.datasets:
            selected = self.datasets[0].dataset_id
        object.__setattr__(self, "selected_dataset_id", selected)
        object.__setattr__(self, "diagnostics", tuple(str(item) for item in self.diagnostics))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def selected_dataset(self) -> ResultDataset | None:
        for dataset in self.datasets:
            if dataset.dataset_id == self.selected_dataset_id:
                return dataset
        return self.datasets[0] if self.datasets else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "project_name": self.project_name,
            "datasets": [dataset.to_dict() for dataset in self.datasets],
            "selected_dataset_id": self.selected_dataset_id,
            "diagnostics": list(self.diagnostics),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultCatalog:
        if not isinstance(data, Mapping):
            msg = "ResultCatalog data must be a mapping."
            raise TypeError(msg)
        return cls(
            catalog_id=str(data.get("catalog_id", "")),
            project_name=str(data.get("project_name", "")),
            datasets=tuple(
                ResultDataset.from_dict(item)
                for item in data.get("datasets", ()) or ()
                if isinstance(item, Mapping)
            ),
            selected_dataset_id=str(data.get("selected_dataset_id", "")),
            diagnostics=tuple(str(item) for item in data.get("diagnostics", ()) or ()),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class ResultRow:
    entity_id: int
    values: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {"entity_id": self.entity_id, "values": dict(self.values)}

    @classmethod
    def from_dict(cls, data: object) -> ResultRow:
        if not isinstance(data, dict):
            msg = "ResultRow data must be a mapping."
            raise TypeError(msg)
        return cls(
            entity_id=int(data.get("entity_id", 0)),
            values={str(key): float(value) for key, value in dict(data.get("values", {})).items()},
        )


@dataclass(frozen=True)
class ResultField:
    name: str
    location: str
    components: tuple[str, ...]
    rows: tuple[ResultRow, ...] = field(default_factory=tuple)
    unit: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location,
            "components": list(self.components),
            "unit": self.unit,
            "rows": [row.to_dict() for row in self.rows],
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultField:
        if not isinstance(data, dict):
            msg = "ResultField data must be a mapping."
            raise TypeError(msg)
        return cls(
            name=str(data.get("name", "")),
            location=str(data.get("location", "")),
            components=tuple(str(item) for item in data.get("components", ()) or ()),
            rows=tuple(ResultRow.from_dict(row) for row in data.get("rows", ()) or ()),
            unit=str(data.get("unit", "")),
        )


@dataclass(frozen=True)
class ResultSummaryValue:
    name: str
    value: float
    unit: str
    source_field: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "source_field": self.source_field,
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultSummaryValue:
        if not isinstance(data, dict):
            msg = "ResultSummaryValue data must be a mapping."
            raise TypeError(msg)
        return cls(
            name=str(data.get("name", "")),
            value=float(data.get("value", 0.0)),
            unit=str(data.get("unit", "")),
            source_field=str(data.get("source_field", "")),
        )


@dataclass(frozen=True)
class ResultDataset:
    dataset_id: str
    source: str
    solver: str
    analysis_type: str
    fields: tuple[ResultField, ...] = field(default_factory=tuple)
    summaries: tuple[ResultSummaryValue, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def field(self, name: str) -> ResultField:
        for field_item in self.fields:
            if field_item.name == name:
                return field_item
        msg = f"Result field not found: {name}"
        raise KeyError(msg)

    def max_summary(self, name: str) -> ResultSummaryValue:
        for summary in self.summaries:
            if summary.name == name:
                return summary
        msg = f"Result summary not found: {name}"
        raise KeyError(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source": self.source,
            "solver": self.solver,
            "analysis_type": self.analysis_type,
            "fields": [field_item.to_dict() for field_item in self.fields],
            "summaries": {summary.name: summary.to_dict() for summary in self.summaries},
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> ResultDataset:
        if not isinstance(data, dict):
            msg = "ResultDataset data must be a mapping."
            raise TypeError(msg)
        summaries_data = data.get("summaries", {})
        if isinstance(summaries_data, dict):
            summary_items = summaries_data.values()
        else:
            summary_items = summaries_data or ()
        return cls(
            dataset_id=str(data.get("dataset_id", "")),
            source=str(data.get("source", "")),
            solver=str(data.get("solver", "")),
            analysis_type=str(data.get("analysis_type", "")),
            fields=tuple(ResultField.from_dict(item) for item in data.get("fields", ()) or ()),
            summaries=tuple(ResultSummaryValue.from_dict(item) for item in summary_items),
            warnings=tuple(str(item) for item in data.get("warnings", ()) or ()),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    def to_report_tables(self) -> tuple[object, ...]:
        tables = [_field_to_table(self, field_item) for field_item in self.fields]
        if self.summaries:
            tables.append(_summary_to_table(self))
        tables.extend(_metadata_preview_tables(self))
        return tuple(tables)


def _field_to_table(dataset: ResultDataset, field_item: ResultField) -> object:
    from osw.post.table_model import TablePreview

    columns = ("entity_id", *field_item.components)
    rows = tuple(
        (
            str(row.entity_id),
            *(_format_value(row.values.get(component)) for component in field_item.components),
        )
        for row in field_item.rows
    )
    title = f"{dataset.solver} {field_item.name}"
    notes = tuple(dataset.warnings)
    return TablePreview(
        columns=columns,
        rows=rows,
        title=title,
        source=dataset.source,
        notes=notes,
    )


def _summary_to_table(dataset: ResultDataset) -> object:
    from osw.post.table_model import TablePreview

    rows = tuple(
        (
            summary.name,
            _format_value(summary.value),
            summary.unit,
            summary.source_field,
        )
        for summary in dataset.summaries
    )
    return TablePreview(
        columns=("summary", "value", "unit", "source"),
        rows=rows,
        title=f"{dataset.solver} result summary",
        source=dataset.source,
        notes=tuple(dataset.warnings),
    )


def _metadata_preview_tables(dataset: ResultDataset) -> list[object]:
    from osw.post.table_model import TablePreview

    tables = []
    for key, default_title in (
        ("property_rows", "CHM property table"),
        ("reactor_rows", "Cantera reactor time history"),
    ):
        payload = dataset.metadata.get(key)
        if not isinstance(payload, Mapping):
            continue
        columns = tuple(str(item) for item in payload.get("columns", ()) or ())
        rows = tuple(
            tuple(str(cell) for cell in row)
            for row in payload.get("rows", ()) or ()
        )
        if columns:
            tables.append(
                TablePreview(
                    columns=columns,
                    rows=rows,
                    title=str(payload.get("title", default_title)),
                    source=dataset.source,
                    notes=tuple(dataset.warnings),
                )
            )
    return tables


def _format_value(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"


def _coerce_dataset(value: object) -> ResultDataset:
    if isinstance(value, ResultDataset):
        return value
    if isinstance(value, Mapping):
        return ResultDataset.from_dict(value)
    msg = "ResultCatalog datasets must contain ResultDataset objects or mappings."
    raise TypeError(msg)


def _kind_value(kind: str | ResultDatasetKind) -> str:
    if isinstance(kind, ResultDatasetKind):
        return kind.value
    text = str(kind or ResultDatasetKind.UNKNOWN.value)
    return text if text in {item.value for item in ResultDatasetKind} else text


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _scalar_value(value: object) -> float | int | str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int | float):
        return value
    text = str(value)
    try:
        parsed = float(text)
    except ValueError:
        return text
    if parsed.is_integer() and "." not in text and "e" not in text.lower():
        return int(parsed)
    return parsed
