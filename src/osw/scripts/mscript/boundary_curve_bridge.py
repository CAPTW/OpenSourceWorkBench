"""Bridge workspace variables and MAT previews into BoundaryCurve records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from osw.core.boundary_curve import (
    BoundaryCurve,
    BoundaryCurveError,
    boundary_curve_from_xy,
    make_source_trace,
)

from .mat_reader import MatFilePreview


def boundary_curve_from_workspace_variables(
    variables: Mapping[str, Any],
    *,
    x_variable: str,
    y_variable: str,
    curve_id: str,
    name: str,
    source_file: str,
    x_unit: str = "",
    y_unit: str = "",
    created_at: str | None = None,
) -> BoundaryCurve:
    missing = [
        variable_name
        for variable_name in (x_variable, y_variable)
        if variable_name not in variables
    ]
    if missing:
        msg = f"Missing workspace variable(s) for boundary curve: {', '.join(missing)}"
        raise BoundaryCurveError(msg)
    return boundary_curve_from_xy(
        curve_id=curve_id,
        name=name,
        x_values=variables[x_variable],
        y_values=variables[y_variable],
        x_unit=x_unit,
        y_unit=y_unit,
        source=make_source_trace(
            source_file=source_file,
            variable_names=(x_variable, y_variable),
            created_at=created_at,
        ),
    )


def boundary_curve_from_mat_preview(
    preview: MatFilePreview,
    *,
    x_variable: str,
    y_variable: str,
    curve_id: str,
    name: str,
    x_unit: str = "",
    y_unit: str = "",
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
        name=name,
        source_file=str(preview.file_path),
        x_unit=x_unit,
        y_unit=y_unit,
        created_at=created_at,
    )
