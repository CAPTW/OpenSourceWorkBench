"""CoolProp ResultDataset bridges."""

from __future__ import annotations

import math
from pathlib import Path

from osw.core.result_dataset import (
    ResultDataset,
    ResultDatasetKind,
    ResultField,
    ResultRow,
    ResultSummaryValue,
)

from .model import (
    CoolPropPropertyResult,
    CoolPropResultStatus,
    CoolPropSweepResult,
)


def coolprop_result_to_result_dataset(result: CoolPropPropertyResult) -> ResultDataset:
    """Convert a CoolProp property point result to a viewer/report dataset."""

    dataset_id = _safe_dataset_id(
        "coolprop-property",
        result.request.fluid,
        result.request.input_pair.first_value,
        result.request.input_pair.second_value,
    )
    warnings = _diagnostic_text(result)
    return ResultDataset(
        dataset_id=dataset_id,
        source="CoolProp",
        solver="CoolProp",
        analysis_type="thermophysical_property",
        summaries=tuple(
            ResultSummaryValue(value.name, value.value, value.unit, "CoolProp")
            for value in result.values
        ),
        warnings=warnings,
        metadata={
            "kind": ResultDatasetKind.COOLPROP_PROPERTY.value,
            "title": f"CoolProp Properties: {result.request.fluid}",
            "status": result.status,
            "request": result.request.to_dict(),
            "property_rows": _property_rows(result),
            "diagnostics": result.diagnostics.to_dict(),
            "optional_dependency": "CoolProp",
        },
    )


def coolprop_sweep_to_result_dataset(result: CoolPropSweepResult) -> ResultDataset:
    """Convert a CoolProp sweep result to a viewer/report dataset."""

    rows = []
    components = tuple(result.series)
    for index, row in enumerate(result.rows, start=1):
        values = {
            component: float(row[column_index + 1])
            for column_index, component in enumerate(components)
            if len(row) > column_index + 1
        }
        rows.append(ResultRow(index, values))

    summaries: list[ResultSummaryValue] = []
    units = _series_units(result)
    for name, values in result.series.items():
        finite = [float(item) for item in values if math.isfinite(float(item))]
        if not finite:
            continue
        summaries.extend(
            (
                ResultSummaryValue(f"{name}_first", finite[0], units.get(name, ""), "CoolProp"),
                ResultSummaryValue(f"{name}_last", finite[-1], units.get(name, ""), "CoolProp"),
                ResultSummaryValue(f"{name}_min", min(finite), units.get(name, ""), "CoolProp"),
                ResultSummaryValue(f"{name}_max", max(finite), units.get(name, ""), "CoolProp"),
            )
        )

    return ResultDataset(
        dataset_id=_safe_dataset_id("coolprop-sweep", result.request.fluid),
        source="CoolProp",
        solver="CoolProp",
        analysis_type="property_sweep",
        fields=(
            ResultField(
                name="coolprop_sweep",
                location="sweep",
                components=components,
                rows=tuple(rows),
                unit="SI",
            ),
        )
        if rows and components
        else (),
        summaries=tuple(summaries),
        warnings=_diagnostic_text(result),
        metadata={
            "kind": ResultDatasetKind.COOLPROP_SWEEP.value,
            "title": f"CoolProp Sweep: {result.request.fluid}",
            "status": result.status,
            "request": result.request.to_dict(),
            "sweep_variable": result.request.sweep_variable,
            "sweep_unit": result.request.sweep_unit,
            "sweep_values": list(result.request.sweep_values),
            "property_rows": {
                "title": "CoolProp sweep table",
                "columns": list(result.columns),
                "rows": [list(row) for row in result.rows],
            },
            "series_units": units,
            "diagnostics": result.diagnostics.to_dict(),
            "optional_dependency": "CoolProp",
        },
    )


def _property_rows(result: CoolPropPropertyResult) -> dict[str, object]:
    if result.table:
        return {
            "title": "CoolProp property table",
            "columns": list(result.table.get("columns", ())),
            "rows": [list(row) for row in result.table.get("rows", ())],
        }
    return {
        "title": "CoolProp property table",
        "columns": ["Property", "Value", "Unit"],
        "rows": [
            [value.name, f"{value.value:.12g}", value.unit]
            for value in result.values
        ],
    }


def _series_units(result: CoolPropSweepResult) -> dict[str, str]:
    units: dict[str, str] = {}
    for column in result.columns[1:]:
        if "[" in column and column.endswith("]"):
            name, unit = column.rsplit("[", 1)
            units[name.strip()] = unit[:-1]
    return units


def _diagnostic_text(result: object) -> tuple[str, ...]:
    diagnostics = getattr(result, "diagnostics", None)
    messages = getattr(diagnostics, "messages", ()) if diagnostics is not None else ()
    warnings = []
    for message in messages:
        warnings.append(
            f"{getattr(getattr(message, 'severity', ''), 'value', '')} "
            f"{getattr(message, 'code', '')}: {getattr(message, 'message', '')}".strip()
        )
    status = str(getattr(result, "status", ""))
    if status == CoolPropResultStatus.DEPENDENCY_MISSING.value and not warnings:
        warnings.append("dependency_missing: CoolProp is not installed.")
    return tuple(warnings)


def _safe_dataset_id(prefix: str, *parts: object) -> str:
    raw = "-".join(str(part) for part in (prefix, *parts) if str(part))
    text = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in raw)
    return Path(text).stem[:120] or prefix


__all__ = [
    "coolprop_result_to_result_dataset",
    "coolprop_sweep_to_result_dataset",
]

