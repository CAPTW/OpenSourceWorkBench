"""Cantera ResultDataset bridges."""

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

from .model import CanteraReactorResult, CanteraResultStatus


def cantera_result_to_result_dataset(result: CanteraReactorResult) -> ResultDataset:
    """Convert a Cantera reactor result into a viewer/report dataset."""

    components = ["temperature", "pressure", *result.species_series]
    rows = []
    for index, _time_value in enumerate(result.times, start=1):
        values: dict[str, float] = {}
        source_index = index - 1
        if source_index < len(result.temperature_series):
            values["temperature"] = result.temperature_series[source_index]
        if source_index < len(result.pressure_series):
            values["pressure"] = result.pressure_series[source_index]
        for species, series in result.species_series.items():
            if source_index < len(series):
                values[species] = series[source_index]
        rows.append(ResultRow(index, values))

    summaries = _reactor_summaries(result)
    return ResultDataset(
        dataset_id=_safe_dataset_id(
            "cantera-reactor",
            result.request.mixture.mechanism,
        ),
        source="Cantera",
        solver="Cantera",
        analysis_type="zero_d_reactor",
        fields=(
            ResultField(
                name="cantera_reactor",
                location="time",
                components=tuple(components),
                rows=tuple(rows),
                unit="SI",
            ),
        )
        if rows
        else (),
        summaries=tuple(summaries),
        warnings=_diagnostic_text(result),
        metadata={
            "kind": ResultDatasetKind.CANTERA_REACTOR.value,
            "title": "Cantera 0D Reactor",
            "status": result.status,
            "request": result.request.to_dict(),
            "time_values": list(result.times),
            "time_unit": result.request.time_unit,
            "series_units": {
                "temperature": result.request.mixture.temperature_unit,
                "pressure": result.request.mixture.pressure_unit,
                **{species: "mole_fraction" for species in result.species_series},
            },
            "reactor_rows": _reactor_rows(result),
            "diagnostics": result.diagnostics.to_dict(),
            "optional_dependency": "cantera",
        },
    )


def _reactor_summaries(result: CanteraReactorResult) -> list[ResultSummaryValue]:
    summaries: list[ResultSummaryValue] = []
    if result.temperature_series:
        finite = _finite(result.temperature_series)
        if finite:
            summaries.append(
                ResultSummaryValue(
                    "final_temperature",
                    finite[-1],
                    result.request.mixture.temperature_unit,
                    "Cantera",
                )
            )
            summaries.append(
                ResultSummaryValue(
                    "max_temperature",
                    max(finite),
                    result.request.mixture.temperature_unit,
                    "Cantera",
                )
            )
    if result.pressure_series:
        finite_pressure = _finite(result.pressure_series)
        if finite_pressure:
            summaries.append(
                ResultSummaryValue(
                    "final_pressure",
                    finite_pressure[-1],
                    result.request.mixture.pressure_unit,
                    "Cantera",
                )
            )
    for species, values in result.species_series.items():
        finite_species = _finite(values)
        if finite_species:
            summaries.append(
                ResultSummaryValue(
                    f"final_{species}",
                    finite_species[-1],
                    "mole_fraction",
                    "Cantera",
                )
            )
    return summaries


def _reactor_rows(result: CanteraReactorResult) -> dict[str, object]:
    if result.table:
        return {
            "title": "Cantera reactor time history",
            "columns": list(result.table.get("columns", ())),
            "rows": [list(row) for row in result.table.get("rows", ())],
        }
    species_names = tuple(result.species_series)
    rows = []
    for index, time_value in enumerate(result.times):
        rows.append(
            [
                f"{time_value:.12g}",
                _series_cell(result.temperature_series, index),
                _series_cell(result.pressure_series, index),
                *(_series_cell(result.species_series[species], index) for species in species_names),
            ]
        )
    return {
        "title": "Cantera reactor time history",
        "columns": ["time_s", "temperature_K", "pressure_Pa", *species_names],
        "rows": rows,
    }


def _series_cell(values: tuple[float, ...], index: int) -> str:
    if index >= len(values):
        return ""
    return f"{values[index]:.12g}"


def _diagnostic_text(result: CanteraReactorResult) -> tuple[str, ...]:
    warnings = []
    for message in result.diagnostics.messages:
        warnings.append(
            f"{message.severity.value} {message.code}: {message.message}".strip()
        )
    if result.status == CanteraResultStatus.DEPENDENCY_MISSING.value and not warnings:
        warnings.append("dependency_missing: Cantera is not installed.")
    return tuple(warnings)


def _finite(values: tuple[float, ...]) -> list[float]:
    return [float(item) for item in values if math.isfinite(float(item))]


def _safe_dataset_id(prefix: str, *parts: object) -> str:
    raw = "-".join(str(part) for part in (prefix, *parts) if str(part))
    text = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in raw)
    return Path(text).stem[:120] or prefix


__all__ = ["cantera_result_to_result_dataset"]
