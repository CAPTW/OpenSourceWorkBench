"""JSON-safe CoolProp property calculation models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from osw.core.diagnostics import DiagnosticReport


class CoolPropResultStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    DEPENDENCY_MISSING = "dependency_missing"


@dataclass(frozen=True)
class PropertyInputPair:
    first_name: str
    first_value: float
    second_name: str
    second_value: float
    first_unit: str = ""
    second_unit: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "first_name", str(self.first_name))
        object.__setattr__(self, "first_value", float(self.first_value))
        object.__setattr__(self, "second_name", str(self.second_name))
        object.__setattr__(self, "second_value", float(self.second_value))
        object.__setattr__(self, "first_unit", str(self.first_unit))
        object.__setattr__(self, "second_unit", str(self.second_unit))

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_name": self.first_name,
            "first_value": self.first_value,
            "first_unit": self.first_unit,
            "second_name": self.second_name,
            "second_value": self.second_value,
            "second_unit": self.second_unit,
        }

    @classmethod
    def from_dict(cls, data: object) -> PropertyInputPair:
        if not isinstance(data, Mapping):
            msg = "PropertyInputPair data must be a mapping."
            raise TypeError(msg)
        return cls(
            first_name=str(data.get("first_name", "")),
            first_value=float(data.get("first_value", 0.0)),
            first_unit=str(data.get("first_unit", "")),
            second_name=str(data.get("second_name", "")),
            second_value=float(data.get("second_value", 0.0)),
            second_unit=str(data.get("second_unit", "")),
        )


@dataclass(frozen=True)
class CoolPropPropertyRequest:
    fluid: str
    input_pair: PropertyInputPair
    output_properties: tuple[str, ...] = (
        "density",
        "viscosity",
        "enthalpy",
        "entropy",
        "cp",
        "thermal_conductivity",
    )
    backend: str = "HEOS"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "fluid", str(self.fluid))
        pair = (
            self.input_pair
            if isinstance(self.input_pair, PropertyInputPair)
            else PropertyInputPair.from_dict(self.input_pair)
        )
        object.__setattr__(self, "input_pair", pair)
        object.__setattr__(
            self,
            "output_properties",
            tuple(str(item) for item in self.output_properties),
        )
        object.__setattr__(self, "backend", str(self.backend))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "fluid": self.fluid,
            "input_pair": self.input_pair.to_dict(),
            "output_properties": list(self.output_properties),
            "backend": self.backend,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CoolPropPropertyRequest:
        if not isinstance(data, Mapping):
            msg = "CoolPropPropertyRequest data must be a mapping."
            raise TypeError(msg)
        return cls(
            fluid=str(data.get("fluid", "")),
            input_pair=PropertyInputPair.from_dict(data.get("input_pair", {})),
            output_properties=tuple(
                str(item)
                for item in data.get("output_properties", ()) or ()
            )
            or ("density",),
            backend=str(data.get("backend", "HEOS")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CoolPropSweepRequest:
    fluid: str
    sweep_variable: str
    sweep_values: tuple[float, ...]
    fixed_variable: str
    fixed_value: float
    output_properties: tuple[str, ...] = ("density",)
    sweep_unit: str = ""
    fixed_unit: str = ""
    backend: str = "HEOS"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "fluid", str(self.fluid))
        object.__setattr__(self, "sweep_variable", str(self.sweep_variable))
        object.__setattr__(self, "sweep_values", tuple(float(item) for item in self.sweep_values))
        object.__setattr__(self, "fixed_variable", str(self.fixed_variable))
        object.__setattr__(self, "fixed_value", float(self.fixed_value))
        object.__setattr__(
            self,
            "output_properties",
            tuple(str(item) for item in self.output_properties),
        )
        object.__setattr__(self, "sweep_unit", str(self.sweep_unit))
        object.__setattr__(self, "fixed_unit", str(self.fixed_unit))
        object.__setattr__(self, "backend", str(self.backend))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "fluid": self.fluid,
            "sweep_variable": self.sweep_variable,
            "sweep_values": list(self.sweep_values),
            "sweep_unit": self.sweep_unit,
            "fixed_variable": self.fixed_variable,
            "fixed_value": self.fixed_value,
            "fixed_unit": self.fixed_unit,
            "output_properties": list(self.output_properties),
            "backend": self.backend,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CoolPropSweepRequest:
        if not isinstance(data, Mapping):
            msg = "CoolPropSweepRequest data must be a mapping."
            raise TypeError(msg)
        return cls(
            fluid=str(data.get("fluid", "")),
            sweep_variable=str(data.get("sweep_variable", "")),
            sweep_values=tuple(float(item) for item in data.get("sweep_values", ()) or ()),
            sweep_unit=str(data.get("sweep_unit", "")),
            fixed_variable=str(data.get("fixed_variable", "")),
            fixed_value=float(data.get("fixed_value", 0.0)),
            fixed_unit=str(data.get("fixed_unit", "")),
            output_properties=tuple(
                str(item)
                for item in data.get("output_properties", ()) or ()
            )
            or ("density",),
            backend=str(data.get("backend", "HEOS")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CoolPropPropertyValue:
    name: str
    value: float
    unit: str = ""
    source: str = "CoolProp"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "value", float(self.value))
        object.__setattr__(self, "unit", str(self.unit))
        object.__setattr__(self, "source", str(self.source))
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
    def from_dict(cls, data: object) -> CoolPropPropertyValue:
        if not isinstance(data, Mapping):
            msg = "CoolPropPropertyValue data must be a mapping."
            raise TypeError(msg)
        return cls(
            name=str(data.get("name", "")),
            value=float(data.get("value", 0.0)),
            unit=str(data.get("unit", "")),
            source=str(data.get("source", "CoolProp")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CoolPropPropertyResult:
    status: str | CoolPropResultStatus
    request: CoolPropPropertyRequest
    values: tuple[CoolPropPropertyValue, ...] = field(default_factory=tuple)
    table: dict[str, Any] = field(default_factory=dict)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _status_value(self.status))
        request = (
            self.request
            if isinstance(self.request, CoolPropPropertyRequest)
            else CoolPropPropertyRequest.from_dict(self.request)
        )
        object.__setattr__(self, "request", request)
        object.__setattr__(
            self,
            "values",
            tuple(
                item
                if isinstance(item, CoolPropPropertyValue)
                else CoolPropPropertyValue.from_dict(item)
                for item in self.values
            ),
        )
        object.__setattr__(self, "table", dict(self.table))
        diagnostics = (
            self.diagnostics
            if isinstance(self.diagnostics, DiagnosticReport)
            else DiagnosticReport.from_dict(self.diagnostics)
        )
        object.__setattr__(self, "diagnostics", diagnostics)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "request": self.request.to_dict(),
            "values": [value.to_dict() for value in self.values],
            "table": dict(self.table),
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CoolPropPropertyResult:
        if not isinstance(data, Mapping):
            msg = "CoolPropPropertyResult data must be a mapping."
            raise TypeError(msg)
        return cls(
            status=str(data.get("status", CoolPropResultStatus.ERROR.value)),
            request=CoolPropPropertyRequest.from_dict(data.get("request", {})),
            values=tuple(
                CoolPropPropertyValue.from_dict(item)
                for item in data.get("values", ()) or ()
            ),
            table=dict(data.get("table", {}) or {}),
            diagnostics=DiagnosticReport.from_dict(dict(data.get("diagnostics", {}) or {})),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CoolPropSweepResult:
    status: str | CoolPropResultStatus
    request: CoolPropSweepRequest
    columns: tuple[str, ...] = field(default_factory=tuple)
    rows: tuple[tuple[float | str, ...], ...] = field(default_factory=tuple)
    series: dict[str, tuple[float, ...]] = field(default_factory=dict)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _status_value(self.status))
        request = (
            self.request
            if isinstance(self.request, CoolPropSweepRequest)
            else CoolPropSweepRequest.from_dict(self.request)
        )
        object.__setattr__(self, "request", request)
        object.__setattr__(self, "columns", tuple(str(item) for item in self.columns))
        object.__setattr__(
            self,
            "rows",
            tuple(tuple(item for item in row) for row in self.rows),
        )
        object.__setattr__(
            self,
            "series",
            {
                str(key): tuple(float(item) for item in values)
                for key, values in self.series.items()
            },
        )
        diagnostics = (
            self.diagnostics
            if isinstance(self.diagnostics, DiagnosticReport)
            else DiagnosticReport.from_dict(self.diagnostics)
        )
        object.__setattr__(self, "diagnostics", diagnostics)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "request": self.request.to_dict(),
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
            "series": {name: list(values) for name, values in self.series.items()},
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CoolPropSweepResult:
        if not isinstance(data, Mapping):
            msg = "CoolPropSweepResult data must be a mapping."
            raise TypeError(msg)
        return cls(
            status=str(data.get("status", CoolPropResultStatus.ERROR.value)),
            request=CoolPropSweepRequest.from_dict(data.get("request", {})),
            columns=tuple(str(item) for item in data.get("columns", ()) or ()),
            rows=tuple(tuple(item for item in row) for row in data.get("rows", ()) or ()),
            series={
                str(key): tuple(float(item) for item in values)
                for key, values in dict(data.get("series", {}) or {}).items()
            },
            diagnostics=DiagnosticReport.from_dict(dict(data.get("diagnostics", {}) or {})),
            metadata=dict(data.get("metadata", {}) or {}),
        )


def default_property_request(fluid: str = "Water") -> CoolPropPropertyRequest:
    return CoolPropPropertyRequest(
        fluid=fluid,
        input_pair=PropertyInputPair("T", 300.0, "P", 101325.0, "K", "Pa"),
    )


def default_sweep_request(fluid: str = "Water") -> CoolPropSweepRequest:
    return CoolPropSweepRequest(
        fluid=fluid,
        sweep_variable="T",
        sweep_values=(280.0, 290.0, 300.0, 310.0, 320.0),
        sweep_unit="K",
        fixed_variable="P",
        fixed_value=101325.0,
        fixed_unit="Pa",
        output_properties=("density",),
    )


def _status_value(status: str | CoolPropResultStatus) -> str:
    if isinstance(status, CoolPropResultStatus):
        return status.value
    text = str(status or CoolPropResultStatus.ERROR.value)
    try:
        return CoolPropResultStatus(text).value
    except ValueError:
        return text


__all__ = [
    "CoolPropPropertyRequest",
    "CoolPropPropertyResult",
    "CoolPropPropertyValue",
    "CoolPropResultStatus",
    "CoolPropSweepRequest",
    "CoolPropSweepResult",
    "PropertyInputPair",
    "default_property_request",
    "default_sweep_request",
]
