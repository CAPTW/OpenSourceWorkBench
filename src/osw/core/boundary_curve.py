"""Boundary curve contracts for script-data-to-project handoff."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any

from .diagnostics import DiagnosticReport
from .validation import ValidationReport


class BoundaryCurveError(ValueError):
    """Raised when boundary curve data cannot be built safely."""


class CurveInterpolation(StrEnum):
    LINEAR = "linear"
    NEAREST = "nearest"
    PREVIOUS = "previous"
    CUBIC_PLACEHOLDER = "cubic_placeholder"
    NONE = "none"


class BoundaryCurveKind(StrEnum):
    TIME_SERIES = "time_series"
    SPATIAL_PROFILE = "spatial_profile"
    TEMPERATURE_PROFILE = "temperature_profile"
    PRESSURE_PROFILE = "pressure_profile"
    VELOCITY_PROFILE = "velocity_profile"
    HEAT_FLUX_PROFILE = "heat_flux_profile"
    GENERIC_XY = "generic_xy"


@dataclass(frozen=True)
class CurveAxis:
    name: str
    unit: str = ""
    role: str = "independent"
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        role = str(self.role or "").strip().lower()
        if role not in {"independent", "dependent"}:
            role = "independent"
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "unit": self.unit,
            "role": self.role,
            "description": self.description,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CurveAxis:
        if not isinstance(data, Mapping):
            msg = "Curve axis must be a mapping."
            raise BoundaryCurveError(msg)
        return cls(
            name=str(data.get("name", "")),
            unit=str(data.get("unit", "")),
            role=str(data.get("role", "independent")),
            description=str(data.get("description", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True, init=False)
class BoundaryCurveSource:
    source_type: str
    source_file: str
    source_run_id: str
    source_dataset_id: str
    x_variable: str
    y_variable: str
    created_at: str
    metadata: dict[str, Any]

    def __init__(
        self,
        source_file: str = "",
        variable_names: Sequence[str] | None = None,
        created_at: str = "",
        *,
        source_type: str = "unknown",
        source_run_id: str = "",
        source_dataset_id: str = "",
        x_variable: str = "",
        y_variable: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        variables = tuple(str(item) for item in (variable_names or ()) if str(item))
        resolved_x = str(x_variable or (variables[0] if len(variables) > 0 else ""))
        resolved_y = str(y_variable or (variables[1] if len(variables) > 1 else ""))
        object.__setattr__(self, "source_type", str(source_type or "unknown"))
        object.__setattr__(self, "source_file", str(source_file))
        object.__setattr__(self, "source_run_id", str(source_run_id))
        object.__setattr__(self, "source_dataset_id", str(source_dataset_id))
        object.__setattr__(self, "x_variable", resolved_x)
        object.__setattr__(self, "y_variable", resolved_y)
        object.__setattr__(self, "created_at", str(created_at))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def variable_names(self) -> tuple[str, ...]:
        return tuple(name for name in (self.x_variable, self.y_variable) if name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_file": self.source_file,
            "source_run_id": self.source_run_id,
            "source_dataset_id": self.source_dataset_id,
            "x_variable": self.x_variable,
            "y_variable": self.y_variable,
            "variable_names": list(self.variable_names),
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> BoundaryCurveSource:
        if not isinstance(data, Mapping):
            msg = "Boundary curve source trace must be a mapping."
            raise BoundaryCurveError(msg)
        return cls(
            source_type=str(data.get("source_type", "unknown")),
            source_file=str(data.get("source_file", "")),
            source_run_id=str(data.get("source_run_id", "")),
            source_dataset_id=str(data.get("source_dataset_id", "")),
            x_variable=str(data.get("x_variable", "")),
            y_variable=str(data.get("y_variable", "")),
            variable_names=tuple(str(item) for item in data.get("variable_names", ()) or ()),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


BoundaryCurveSourceTrace = BoundaryCurveSource


@dataclass(frozen=True, init=False)
class BoundaryCurve:
    curve_id: str
    name: str
    kind: str
    x_axis: CurveAxis
    y_axis: CurveAxis
    x_values: tuple[float, ...]
    y_values: tuple[float, ...]
    interpolation: str
    source: BoundaryCurveSource | None
    diagnostics: DiagnosticReport
    metadata: dict[str, Any]

    def __init__(
        self,
        curve_id: str,
        name: str,
        x_values: Sequence[object],
        y_values: Sequence[object],
        x_unit: str = "",
        y_unit: str = "",
        source: BoundaryCurveSource | None = None,
        metadata: Mapping[str, Any] | None = None,
        *,
        kind: str | BoundaryCurveKind = BoundaryCurveKind.GENERIC_XY,
        x_axis: CurveAxis | Mapping[str, Any] | None = None,
        y_axis: CurveAxis | Mapping[str, Any] | None = None,
        interpolation: str | CurveInterpolation = CurveInterpolation.LINEAR,
        diagnostics: DiagnosticReport | Mapping[str, Any] | None = None,
    ) -> None:
        resolved_x_axis = _coerce_axis(
            x_axis,
            fallback_name="x",
            fallback_unit=x_unit,
            fallback_role="independent",
        )
        resolved_y_axis = _coerce_axis(
            y_axis,
            fallback_name="y",
            fallback_unit=y_unit,
            fallback_role="dependent",
        )
        object.__setattr__(self, "curve_id", str(curve_id))
        object.__setattr__(self, "name", str(name))
        object.__setattr__(self, "kind", _kind_value(kind))
        object.__setattr__(self, "x_axis", resolved_x_axis)
        object.__setattr__(self, "y_axis", resolved_y_axis)
        object.__setattr__(self, "x_values", _numeric_tuple(x_values, label="x_values"))
        object.__setattr__(self, "y_values", _numeric_tuple(y_values, label="y_values"))
        object.__setattr__(self, "interpolation", _interpolation_value(interpolation))
        object.__setattr__(self, "source", source)
        object.__setattr__(
            self,
            "diagnostics",
            _coerce_diagnostic_report(diagnostics),
        )
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def x_unit(self) -> str:
        return self.x_axis.unit

    @property
    def y_unit(self) -> str:
        return self.y_axis.unit

    @property
    def point_count(self) -> int:
        return min(len(self.x_values), len(self.y_values))

    def validate(
        self,
        *,
        path: str = "boundary_curves",
        allow_non_monotonic: bool = False,
    ) -> ValidationReport:
        report = ValidationReport()
        if not self.curve_id:
            report.add_error(f"{path}.curve_id", "Boundary curve id is required.")
        if not self.name:
            report.add_error(f"{path}.name", "Boundary curve name is required.")
        if not self.x_values or not self.y_values:
            report.add_error(f"{path}.values", "Boundary curve x and y values are required.")
        if len(self.x_values) != len(self.y_values):
            report.add_error(
                f"{path}.values",
                "Boundary curve x and y arrays must have the same length.",
            )
        if self.interpolation != CurveInterpolation.NONE.value and self.point_count < 2:
            report.add_error(
                f"{path}.values",
                "Boundary curve interpolation requires at least 2 data points.",
            )
        if any(not isfinite(value) for value in (*self.x_values, *self.y_values)):
            report.add_error(f"{path}.values", "Boundary curve values must be finite numbers.")
        if self.interpolation not in {item.value for item in CurveInterpolation}:
            report.add_error(
                f"{path}.interpolation",
                f"Unsupported boundary curve interpolation: {self.interpolation}",
            )
        if not self.x_unit:
            report.add_warning(f"{path}.x_unit", "Boundary curve x unit is missing.")
        if not self.y_unit:
            report.add_warning(f"{path}.y_unit", "Boundary curve y unit is missing.")
        _validate_unit_hint(self, report, path=path)
        _validate_x_order(self, report, path=path, allow_non_monotonic=allow_non_monotonic)
        if self.source is None:
            report.add_warning(f"{path}.source", "Boundary curve source trace is missing.")
        else:
            if not (
                self.source.source_file
                or self.source.source_run_id
                or self.source.source_dataset_id
                or self.source.variable_names
            ):
                report.add_warning(
                    f"{path}.source",
                    "Boundary curve source trace has no file, run, dataset, or variable names.",
                )
        return report

    def preview_rows(self, max_rows: int = 20) -> list[dict[str, float]]:
        return curve_preview(self, max_rows=max_rows)

    def to_dict(self) -> dict[str, Any]:
        return {
            "curve_id": self.curve_id,
            "name": self.name,
            "kind": self.kind,
            "x_axis": self.x_axis.to_dict(),
            "y_axis": self.y_axis.to_dict(),
            "x_values": list(self.x_values),
            "y_values": list(self.y_values),
            "x_unit": self.x_unit,
            "y_unit": self.y_unit,
            "interpolation": self.interpolation,
            "source": self.source.to_dict() if self.source is not None else None,
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> BoundaryCurve:
        if not isinstance(data, Mapping):
            msg = "Boundary curve must be a mapping."
            raise BoundaryCurveError(msg)
        return cls(
            curve_id=str(data.get("curve_id", "")),
            name=str(data.get("name", "")),
            kind=str(data.get("kind", BoundaryCurveKind.GENERIC_XY.value)),
            x_axis=(
                CurveAxis.from_dict(data["x_axis"])
                if isinstance(data.get("x_axis"), Mapping)
                else None
            ),
            y_axis=(
                CurveAxis.from_dict(data["y_axis"])
                if isinstance(data.get("y_axis"), Mapping)
                else None
            ),
            x_values=_numeric_tuple(data.get("x_values", ()), label="x_values"),
            y_values=_numeric_tuple(data.get("y_values", ()), label="y_values"),
            x_unit=str(data.get("x_unit", "")),
            y_unit=str(data.get("y_unit", "")),
            interpolation=str(data.get("interpolation", CurveInterpolation.LINEAR.value)),
            source=(
                BoundaryCurveSource.from_dict(data["source"])
                if data.get("source") is not None
                else None
            ),
            diagnostics=(
                DiagnosticReport.from_dict(data.get("diagnostics", {}) or {})
                if isinstance(data.get("diagnostics"), Mapping)
                else None
            ),
            metadata=dict(data.get("metadata", {}) or {}),
        )


def boundary_curve_from_xy(
    x_values: Sequence[object] | None = None,
    y_values: Sequence[object] | None = None,
    name: str = "",
    *,
    curve_id: str = "",
    x_unit: str = "",
    y_unit: str = "",
    kind: str | BoundaryCurveKind = BoundaryCurveKind.GENERIC_XY,
    interpolation: str | CurveInterpolation = CurveInterpolation.LINEAR,
    source: BoundaryCurveSource | None = None,
    metadata: Mapping[str, Any] | None = None,
    x_axis: CurveAxis | Mapping[str, Any] | None = None,
    y_axis: CurveAxis | Mapping[str, Any] | None = None,
) -> BoundaryCurve:
    curve = BoundaryCurve(
        curve_id=curve_id or _slug(name or "boundary-curve"),
        name=name or curve_id or "Boundary curve",
        x_values=() if x_values is None else x_values,
        y_values=() if y_values is None else y_values,
        x_unit=x_unit,
        y_unit=y_unit,
        kind=kind,
        interpolation=interpolation,
        source=source,
        metadata=metadata or {},
        x_axis=x_axis,
        y_axis=y_axis,
    )
    report = curve.validate()
    if report.has_errors:
        raise BoundaryCurveError(report.friendly_summary())
    return curve


def boundary_curve_from_csv(
    path: str | Path,
    x_column: str,
    y_column: str,
    *,
    name: str = "",
    curve_id: str = "",
    x_unit: str = "",
    y_unit: str = "",
    kind: str | BoundaryCurveKind = BoundaryCurveKind.GENERIC_XY,
    interpolation: str | CurveInterpolation = CurveInterpolation.LINEAR,
) -> BoundaryCurve:
    source_path = Path(path)
    if not source_path.exists():
        msg = f"Boundary curve CSV file does not exist: {source_path}"
        raise BoundaryCurveError(msg)
    with source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            msg = "Boundary curve CSV must include a header row."
            raise BoundaryCurveError(msg)
        missing = [column for column in (x_column, y_column) if column not in reader.fieldnames]
        if missing:
            msg = f"Missing CSV column(s) for boundary curve: {', '.join(missing)}"
            raise BoundaryCurveError(msg)
        x_values: list[float] = []
        y_values: list[float] = []
        for row_index, row in enumerate(reader, start=2):
            try:
                x_values.append(float(str(row.get(x_column, "")).strip()))
                y_values.append(float(str(row.get(y_column, "")).strip()))
            except (TypeError, ValueError) as exc:
                msg = (
                    f"Boundary curve CSV contains non-numeric data at row {row_index} "
                    f"for {x_column!r}/{y_column!r}."
                )
                raise BoundaryCurveError(msg) from exc
    return boundary_curve_from_xy(
        x_values,
        y_values,
        name or f"{x_column} to {y_column}",
        curve_id=curve_id or _slug(f"{source_path.stem}-{x_column}-{y_column}"),
        x_unit=x_unit,
        y_unit=y_unit,
        kind=kind,
        interpolation=interpolation,
        source=BoundaryCurveSource(
            source_type="csv",
            source_file=str(source_path),
            x_variable=x_column,
            y_variable=y_column,
            created_at=_utc_now(),
        ),
    )


def import_boundary_curve_csv(path: str | Path, **kwargs: Any) -> BoundaryCurve:
    return boundary_curve_from_csv(path, **kwargs)


def export_boundary_curve_csv(curve: BoundaryCurve, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    x_name = curve.x_axis.name or "x"
    y_name = curve.y_axis.name or "y"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([x_name, y_name])
        writer.writerows(zip(curve.x_values, curve.y_values, strict=False))
    return target


def save_boundary_curve_json(curve: BoundaryCurve, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"{json.dumps(curve.to_dict(), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return target


def load_boundary_curve_json(path: str | Path) -> BoundaryCurve:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return BoundaryCurve.from_dict(payload)


def curve_preview(curve: BoundaryCurve, max_rows: int = 20) -> list[dict[str, float]]:
    max_count = max(0, int(max_rows))
    rows = []
    for x_value, y_value in zip(curve.x_values, curve.y_values, strict=False):
        if len(rows) >= max_count:
            break
        rows.append({"x": x_value, "y": y_value})
    return rows


def make_source_trace(
    *,
    source_file: str,
    variable_names: tuple[str, str],
    created_at: str | None = None,
    source_type: str = "unknown",
    source_run_id: str = "",
    source_dataset_id: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> BoundaryCurveSource:
    return BoundaryCurveSource(
        source_type=source_type,
        source_file=source_file,
        source_run_id=source_run_id,
        source_dataset_id=source_dataset_id,
        variable_names=variable_names,
        created_at=created_at or _utc_now(),
        metadata=metadata,
    )


def _validate_x_order(
    curve: BoundaryCurve,
    report: ValidationReport,
    *,
    path: str,
    allow_non_monotonic: bool,
) -> None:
    if len(curve.x_values) < 2:
        return
    duplicate_indexes = [
        index
        for index in range(1, len(curve.x_values))
        if curve.x_values[index] == curve.x_values[index - 1]
    ]
    if duplicate_indexes:
        report.add_warning(
            f"{path}.x_values",
            "Boundary curve contains duplicate x values; interpolation may be ambiguous.",
        )
    if curve.kind in {
        BoundaryCurveKind.TIME_SERIES.value,
        BoundaryCurveKind.SPATIAL_PROFILE.value,
    } and not allow_non_monotonic:
        non_monotonic = any(
            curve.x_values[index] < curve.x_values[index - 1]
            for index in range(1, len(curve.x_values))
        )
        if non_monotonic:
            report.add_warning(
                f"{path}.x_values",
                "Boundary curve x values should be monotonic increasing for this curve kind.",
            )


def _validate_unit_hint(curve: BoundaryCurve, report: ValidationReport, *, path: str) -> None:
    if not curve.y_unit:
        return
    y_unit = _normalize_unit_text(curve.y_unit)
    expected = {
        BoundaryCurveKind.TEMPERATURE_PROFILE.value: {"k", "c", "degc", "°c", "kelvin"},
        BoundaryCurveKind.PRESSURE_PROFILE.value: {"pa", "kpa", "mpa", "bar", "psi"},
        BoundaryCurveKind.HEAT_FLUX_PROFILE.value: {"w/m^2", "w/m²", "wm-2", "w m-2"},
        BoundaryCurveKind.VELOCITY_PROFILE.value: {"m/s", "mps", "m s-1"},
    }.get(curve.kind)
    if expected and y_unit not in expected:
        report.add_warning(
            f"{path}.y_axis.unit",
            (
                f"Boundary curve kind {curve.kind!r} usually expects one of "
                f"{', '.join(sorted(expected))}; got {curve.y_unit!r}."
            ),
        )


def _coerce_axis(
    value: CurveAxis | Mapping[str, Any] | None,
    *,
    fallback_name: str,
    fallback_unit: str,
    fallback_role: str,
) -> CurveAxis:
    if isinstance(value, CurveAxis):
        if fallback_unit and not value.unit:
            return CurveAxis(
                value.name,
                unit=fallback_unit,
                role=value.role,
                description=value.description,
                metadata=value.metadata,
            )
        return value
    if isinstance(value, Mapping):
        axis = CurveAxis.from_dict(value)
        if fallback_unit and not axis.unit:
            return CurveAxis(
                axis.name,
                unit=fallback_unit,
                role=axis.role,
                description=axis.description,
                metadata=axis.metadata,
            )
        return axis
    return CurveAxis(fallback_name, unit=fallback_unit, role=fallback_role)


def _numeric_tuple(values: object, *, label: str) -> tuple[float, ...]:
    raw = values.tolist() if hasattr(values, "tolist") else values
    flattened = _flatten(raw)
    if not flattened:
        return ()
    try:
        return tuple(float(item) for item in flattened)
    except (TypeError, ValueError) as exc:
        msg = f"Boundary curve {label} must contain numeric values."
        raise BoundaryCurveError(msg) from exc


def _flatten(values: object) -> tuple[object, ...]:
    if isinstance(values, (str, bytes)):
        return (values,)
    if isinstance(values, Sequence):
        flattened: list[object] = []
        for value in values:
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                flattened.extend(_flatten(value))
            else:
                flattened.append(value)
        return tuple(flattened)
    return (values,)


def _interpolation_value(value: str | CurveInterpolation) -> str:
    if isinstance(value, CurveInterpolation):
        return value.value
    text = str(value or CurveInterpolation.LINEAR.value).strip().lower()
    try:
        return CurveInterpolation(text).value
    except ValueError:
        return text


def _kind_value(value: str | BoundaryCurveKind) -> str:
    if isinstance(value, BoundaryCurveKind):
        return value.value
    text = str(value or BoundaryCurveKind.GENERIC_XY.value).strip().lower()
    try:
        return BoundaryCurveKind(text).value
    except ValueError:
        return BoundaryCurveKind.GENERIC_XY.value


def _coerce_diagnostic_report(
    value: DiagnosticReport | Mapping[str, Any] | None,
) -> DiagnosticReport:
    if isinstance(value, DiagnosticReport):
        return value
    if isinstance(value, Mapping):
        return DiagnosticReport.from_dict(dict(value))
    return DiagnosticReport()


def _normalize_unit_text(value: str) -> str:
    return value.strip().casefold().replace(" ", "").replace("°", "deg")


def _slug(value: str) -> str:
    text = value.strip().casefold()
    slug = "".join(char if char.isalnum() else "-" for char in text)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "boundary-curve"


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
