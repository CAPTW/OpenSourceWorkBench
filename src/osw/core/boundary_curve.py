"""Boundary curve contracts for script-to-solver data handoff."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import isfinite
from typing import Any

from .validation import ValidationReport


class BoundaryCurveError(ValueError):
    """Raised when boundary curve data cannot be built safely."""


@dataclass(frozen=True)
class BoundaryCurveSourceTrace:
    source_file: str
    variable_names: tuple[str, ...]
    created_at: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "variable_names", tuple(self.variable_names))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "variable_names": list(self.variable_names),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: object) -> BoundaryCurveSourceTrace:
        if not isinstance(data, dict):
            msg = "Boundary curve source trace must be a mapping."
            raise BoundaryCurveError(msg)
        return cls(
            source_file=str(data.get("source_file", "")),
            variable_names=tuple(str(item) for item in data.get("variable_names", ())),
            created_at=str(data.get("created_at", "")),
        )


@dataclass(frozen=True)
class BoundaryCurve:
    curve_id: str
    name: str
    x_values: tuple[float, ...]
    y_values: tuple[float, ...]
    x_unit: str = ""
    y_unit: str = ""
    source: BoundaryCurveSourceTrace | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "x_values", tuple(float(item) for item in self.x_values))
        object.__setattr__(self, "y_values", tuple(float(item) for item in self.y_values))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def validate(self, *, path: str = "boundary_curves") -> ValidationReport:
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
        if any(not isfinite(value) for value in (*self.x_values, *self.y_values)):
            report.add_error(f"{path}.values", "Boundary curve values must be finite numbers.")
        if not self.x_unit:
            report.add_warning(f"{path}.x_unit", "Boundary curve x unit is missing.")
        if not self.y_unit:
            report.add_warning(f"{path}.y_unit", "Boundary curve y unit is missing.")
        if self.source is None:
            report.add_warning(f"{path}.source", "Boundary curve source trace is missing.")
        return report

    def to_dict(self) -> dict[str, Any]:
        return {
            "curve_id": self.curve_id,
            "name": self.name,
            "x_values": list(self.x_values),
            "y_values": list(self.y_values),
            "x_unit": self.x_unit,
            "y_unit": self.y_unit,
            "source": self.source.to_dict() if self.source is not None else None,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> BoundaryCurve:
        if not isinstance(data, dict):
            msg = "Boundary curve must be a mapping."
            raise BoundaryCurveError(msg)
        return cls(
            curve_id=str(data.get("curve_id", "")),
            name=str(data.get("name", "")),
            x_values=_numeric_tuple(data.get("x_values", ()), label="x_values"),
            y_values=_numeric_tuple(data.get("y_values", ()), label="y_values"),
            x_unit=str(data.get("x_unit", "")),
            y_unit=str(data.get("y_unit", "")),
            source=(
                BoundaryCurveSourceTrace.from_dict(data["source"])
                if data.get("source") is not None
                else None
            ),
            metadata=dict(data.get("metadata", {})),
        )


def boundary_curve_from_xy(
    *,
    curve_id: str,
    name: str,
    x_values: Sequence[object],
    y_values: Sequence[object],
    x_unit: str = "",
    y_unit: str = "",
    source: BoundaryCurveSourceTrace | None = None,
    metadata: dict[str, Any] | None = None,
) -> BoundaryCurve:
    x_numeric = _numeric_tuple(x_values, label="x_values")
    y_numeric = _numeric_tuple(y_values, label="y_values")
    if len(x_numeric) != len(y_numeric):
        msg = "Boundary curve x and y arrays must have the same length."
        raise BoundaryCurveError(msg)
    curve = BoundaryCurve(
        curve_id=curve_id,
        name=name,
        x_values=x_numeric,
        y_values=y_numeric,
        x_unit=x_unit,
        y_unit=y_unit,
        source=source,
        metadata=metadata or {},
    )
    report = curve.validate()
    if report.has_errors:
        raise BoundaryCurveError(report.friendly_summary())
    return curve


def make_source_trace(
    *,
    source_file: str,
    variable_names: tuple[str, str],
    created_at: str | None = None,
) -> BoundaryCurveSourceTrace:
    return BoundaryCurveSourceTrace(
        source_file=source_file,
        variable_names=variable_names,
        created_at=created_at or _utc_now(),
    )


def _numeric_tuple(values: object, *, label: str) -> tuple[float, ...]:
    raw = values.tolist() if hasattr(values, "tolist") else values
    flattened = _flatten(raw)
    if not flattened:
        msg = f"Boundary curve {label} must contain at least one value."
        raise BoundaryCurveError(msg)
    try:
        numeric = tuple(float(item) for item in flattened)
    except (TypeError, ValueError) as exc:
        msg = f"Boundary curve {label} must contain numeric values."
        raise BoundaryCurveError(msg) from exc
    if any(not isfinite(value) for value in numeric):
        msg = f"Boundary curve {label} must contain finite numeric values."
        raise BoundaryCurveError(msg)
    return numeric


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


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
