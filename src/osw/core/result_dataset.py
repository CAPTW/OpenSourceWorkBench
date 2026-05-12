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


@dataclass(frozen=True)
class ResultDataset:
    dataset_id: str
    source: str
    solver: str
    analysis_type: str
    fields: tuple[ResultField, ...] = field(default_factory=tuple)
    summaries: tuple[ResultSummaryValue, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

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
        }

    def to_report_tables(self) -> tuple[object, ...]:
        return tuple(_field_to_table(self, field_item) for field_item in self.fields)


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


def _format_value(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"
