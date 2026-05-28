"""Bridge MAT, workspace, CSV, and FigureDataset data into BoundaryCurve records."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from osw.core.boundary_curve import (
    BoundaryCurve,
    BoundaryCurveError,
    BoundaryCurveKind,
    BoundaryCurveSource,
    CurveInterpolation,
    boundary_curve_from_csv,
    boundary_curve_from_xy,
    make_source_trace,
)

from .figure_dataset import FigureDataset, WorkspaceVariableSummary
from .mat_model import MatFilePreview, MatFileSummary, MatReadResult, MatVariableSummary


def boundary_curve_from_workspace_variables(
    variables: Mapping[str, Any] | Sequence[WorkspaceVariableSummary],
    x_name: str = "",
    y_name: str = "",
    *,
    x_variable: str = "",
    y_variable: str = "",
    curve_id: str = "",
    name: str = "",
    source_file: str = "workspace",
    x_unit: str = "",
    y_unit: str = "",
    kind: str | BoundaryCurveKind = BoundaryCurveKind.GENERIC_XY,
    interpolation: str | CurveInterpolation = CurveInterpolation.LINEAR,
    created_at: str | None = None,
) -> BoundaryCurve:
    x_key = x_variable or x_name
    y_key = y_variable or y_name
    if not x_key or not y_key:
        msg = "Boundary curve conversion requires x and y variable names."
        raise BoundaryCurveError(msg)
    values = _workspace_values(variables)
    missing = [variable_name for variable_name in (x_key, y_key) if variable_name not in values]
    if missing:
        msg = f"Missing workspace variable(s) for boundary curve: {', '.join(missing)}"
        raise BoundaryCurveError(msg)
    return boundary_curve_from_xy(
        values[x_key],
        values[y_key],
        name or f"{x_key} to {y_key}",
        curve_id=curve_id or f"{x_key}-{y_key}",
        x_unit=x_unit,
        y_unit=y_unit,
        kind=kind,
        interpolation=interpolation,
        source=make_source_trace(
            source_file=source_file,
            variable_names=(x_key, y_key),
            created_at=created_at,
            source_type="workspace_variable",
        ),
    )


def boundary_curve_from_mat_preview(
    preview: MatFilePreview,
    *,
    x_variable: str,
    y_variable: str,
    curve_id: str = "",
    name: str = "",
    x_unit: str = "",
    y_unit: str = "",
    kind: str | BoundaryCurveKind = BoundaryCurveKind.GENERIC_XY,
    interpolation: str | CurveInterpolation = CurveInterpolation.LINEAR,
    created_at: str | None = None,
) -> BoundaryCurve:
    return boundary_curve_from_workspace_variables(
        {
            x_variable: preview.value(x_variable),
            y_variable: preview.value(y_variable),
        },
        x_variable=x_variable,
        y_variable=y_variable,
        curve_id=curve_id,
        name=name or f"{x_variable} to {y_variable}",
        source_file=str(preview.file_path),
        x_unit=x_unit,
        y_unit=y_unit,
        kind=kind,
        interpolation=interpolation,
        created_at=created_at,
    )


def boundary_curve_from_mat_summary(
    mat_summary: MatFileSummary | MatReadResult,
    x_variable: str,
    y_variable: str,
    *,
    curve_id: str = "",
    name: str = "",
    x_unit: str = "",
    y_unit: str = "",
    kind: str | BoundaryCurveKind = BoundaryCurveKind.GENERIC_XY,
    interpolation: str | CurveInterpolation = CurveInterpolation.LINEAR,
    created_at: str | None = None,
) -> BoundaryCurve:
    values = _mat_values(mat_summary, x_variable, y_variable)
    summary = mat_summary.summary if isinstance(mat_summary, MatReadResult) else mat_summary
    return boundary_curve_from_workspace_variables(
        values,
        x_variable=x_variable,
        y_variable=y_variable,
        curve_id=curve_id,
        name=name or f"{x_variable} to {y_variable}",
        source_file=summary.source_path,
        x_unit=x_unit,
        y_unit=y_unit,
        kind=kind,
        interpolation=interpolation,
        created_at=created_at,
    )


def boundary_curve_from_figure_dataset(
    dataset: FigureDataset,
    x_variable: str,
    y_variable: str,
    *,
    curve_id: str = "",
    name: str = "",
    x_unit: str = "",
    y_unit: str = "",
    kind: str | BoundaryCurveKind = BoundaryCurveKind.GENERIC_XY,
    interpolation: str | CurveInterpolation = CurveInterpolation.LINEAR,
    created_at: str | None = None,
) -> BoundaryCurve:
    values = _workspace_values(dataset.workspace_variables)
    missing = [variable for variable in (x_variable, y_variable) if variable not in values]
    if missing:
        msg = (
            "FigureDataset workspace summaries do not contain full numeric values for: "
            f"{', '.join(missing)}"
        )
        raise BoundaryCurveError(msg)
    return boundary_curve_from_xy(
        values[x_variable],
        values[y_variable],
        name or f"{x_variable} to {y_variable}",
        curve_id=curve_id or f"{dataset.dataset_id}-{x_variable}-{y_variable}",
        x_unit=x_unit,
        y_unit=y_unit,
        kind=kind,
        interpolation=interpolation,
        source=BoundaryCurveSource(
            source_type="figure_dataset",
            source_file=dataset.source_file,
            source_run_id=dataset.source_run_id,
            source_dataset_id=dataset.dataset_id,
            x_variable=x_variable,
            y_variable=y_variable,
            created_at=created_at or dataset.created_at,
        ),
    )


def boundary_curve_from_csv_file(
    path: str,
    x_column: str,
    y_column: str,
    **kwargs: Any,
) -> BoundaryCurve:
    return boundary_curve_from_csv(path, x_column, y_column, **kwargs)


def _workspace_values(
    variables: Mapping[str, Any] | Sequence[WorkspaceVariableSummary],
) -> dict[str, Any]:
    if isinstance(variables, Mapping):
        return dict(variables)
    values: dict[str, Any] = {}
    for variable in variables:
        value = _value_from_workspace_summary(variable)
        if value is not None:
            values[variable.name] = value
    return values


def _value_from_workspace_summary(variable: WorkspaceVariableSummary) -> Any | None:
    metadata = variable.metadata if isinstance(variable.metadata, Mapping) else {}
    for key in ("values", "data", "raw_values", "array"):
        if key in metadata:
            return metadata[key]
    parsed = _parse_preview_sequence(variable.preview)
    if parsed is not None:
        return parsed
    return None


def _mat_values(
    mat_summary: MatFileSummary | MatReadResult,
    x_variable: str,
    y_variable: str,
) -> dict[str, Any]:
    if isinstance(mat_summary, MatReadResult):
        values = dict(mat_summary.values or {})
        missing = [variable for variable in (x_variable, y_variable) if variable not in values]
        if missing:
            msg = (
                "MAT variable values are unavailable for boundary curve conversion: "
                f"{', '.join(missing)}"
            )
            raise BoundaryCurveError(msg)
        return {x_variable: values[x_variable], y_variable: values[y_variable]}

    values: dict[str, Any] = {}
    for variable in mat_summary.variables:
        if variable.name in {x_variable, y_variable}:
            values[variable.name] = _value_from_mat_variable_summary(variable)
    missing = [variable for variable in (x_variable, y_variable) if variable not in values]
    if missing:
        msg = (
            "MAT summary does not include full numeric values for boundary curve conversion: "
            f"{', '.join(missing)}"
        )
        raise BoundaryCurveError(msg)
    return values


def _value_from_mat_variable_summary(variable: MatVariableSummary) -> Any:
    metadata = variable.metadata if isinstance(variable.metadata, Mapping) else {}
    for key in ("values", "data", "raw_values", "array"):
        if key in metadata:
            return metadata[key]
    parsed = _parse_preview_sequence(variable.preview)
    if parsed is not None:
        return parsed
    msg = f"MAT variable summary does not include full numeric values: {variable.name}"
    raise BoundaryCurveError(msg)


def _parse_preview_sequence(text: str) -> list[float] | None:
    candidate = str(text or "").strip()
    if not candidate:
        return None
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        payload = candidate.replace(";", ",").split(",")
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes)):
        return None
    values: list[float] = []
    try:
        for item in payload:
            values.append(float(str(item).strip()))
    except (TypeError, ValueError):
        return None
    return values
