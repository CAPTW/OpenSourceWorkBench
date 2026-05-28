"""Structured result dataset contracts for solver and script outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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


def _format_value(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"
