"""JSON-safe Cantera 0D reactor request/result models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from osw.core.diagnostics import DiagnosticReport


class CanteraResultStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    DEPENDENCY_MISSING = "dependency_missing"


class CanteraReactorKind(StrEnum):
    CONSTANT_VOLUME = "constant_volume"
    CONSTANT_PRESSURE_PLACEHOLDER = "constant_pressure_placeholder"
    EQUILIBRIUM_PLACEHOLDER = "equilibrium_placeholder"


@dataclass(frozen=True)
class CanteraMixtureSpec:
    mechanism: str = "gri30.yaml"
    composition: str | dict[str, float] = "CH4:1,O2:2,N2:7.52"
    temperature: float = 1000.0
    pressure: float = 101325.0
    phase_name: str = ""
    equivalence_ratio: float | None = None
    fuel: str = ""
    oxidizer: str = ""
    temperature_unit: str = "K"
    pressure_unit: str = "Pa"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "mechanism", str(self.mechanism))
        if isinstance(self.composition, Mapping):
            composition: str | dict[str, float] = {
                str(species): float(amount)
                for species, amount in self.composition.items()
            }
        else:
            composition = str(self.composition)
        object.__setattr__(self, "composition", composition)
        object.__setattr__(self, "temperature", float(self.temperature))
        object.__setattr__(self, "pressure", float(self.pressure))
        object.__setattr__(self, "phase_name", str(self.phase_name))
        object.__setattr__(
            self,
            "equivalence_ratio",
            None if self.equivalence_ratio is None else float(self.equivalence_ratio),
        )
        object.__setattr__(self, "fuel", str(self.fuel))
        object.__setattr__(self, "oxidizer", str(self.oxidizer))
        object.__setattr__(self, "temperature_unit", str(self.temperature_unit))
        object.__setattr__(self, "pressure_unit", str(self.pressure_unit))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "mechanism": self.mechanism,
            "phase_name": self.phase_name,
            "composition": self.composition,
            "temperature": self.temperature,
            "temperature_unit": self.temperature_unit,
            "pressure": self.pressure,
            "pressure_unit": self.pressure_unit,
            "equivalence_ratio": self.equivalence_ratio,
            "fuel": self.fuel,
            "oxidizer": self.oxidizer,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CanteraMixtureSpec:
        if not isinstance(data, Mapping):
            msg = "CanteraMixtureSpec data must be a mapping."
            raise TypeError(msg)
        return cls(
            mechanism=str(data.get("mechanism", "gri30.yaml")),
            phase_name=str(data.get("phase_name", "")),
            composition=data.get("composition", "CH4:1,O2:2,N2:7.52"),
            temperature=float(data.get("temperature", 1000.0)),
            temperature_unit=str(data.get("temperature_unit", "K")),
            pressure=float(data.get("pressure", 101325.0)),
            pressure_unit=str(data.get("pressure_unit", "Pa")),
            equivalence_ratio=_optional_float(data.get("equivalence_ratio")),
            fuel=str(data.get("fuel", "")),
            oxidizer=str(data.get("oxidizer", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CanteraReactorRequest:
    mixture: CanteraMixtureSpec = field(default_factory=CanteraMixtureSpec)
    reactor_kind: str | CanteraReactorKind = CanteraReactorKind.CONSTANT_VOLUME
    end_time: float = 0.001
    time_step: float = 0.00025
    tracked_species: tuple[str, ...] = ("CH4", "O2", "CO2", "H2O")
    time_unit: str = "s"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        mixture = (
            self.mixture
            if isinstance(self.mixture, CanteraMixtureSpec)
            else CanteraMixtureSpec.from_dict(self.mixture)
        )
        object.__setattr__(self, "mixture", mixture)
        object.__setattr__(self, "reactor_kind", _reactor_kind_value(self.reactor_kind))
        object.__setattr__(self, "end_time", float(self.end_time))
        object.__setattr__(self, "time_step", float(self.time_step))
        object.__setattr__(
            self,
            "tracked_species",
            tuple(str(species) for species in self.tracked_species),
        )
        object.__setattr__(self, "time_unit", str(self.time_unit))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "mixture": self.mixture.to_dict(),
            "reactor_kind": self.reactor_kind,
            "end_time": self.end_time,
            "time_step": self.time_step,
            "time_unit": self.time_unit,
            "tracked_species": list(self.tracked_species),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CanteraReactorRequest:
        if not isinstance(data, Mapping):
            msg = "CanteraReactorRequest data must be a mapping."
            raise TypeError(msg)
        return cls(
            mixture=CanteraMixtureSpec.from_dict(data.get("mixture", {})),
            reactor_kind=str(data.get("reactor_kind", CanteraReactorKind.CONSTANT_VOLUME.value)),
            end_time=float(data.get("end_time", 0.001)),
            time_step=float(data.get("time_step", 0.00025)),
            time_unit=str(data.get("time_unit", "s")),
            tracked_species=tuple(str(item) for item in data.get("tracked_species", ()) or ()),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CanteraReactorResult:
    status: str | CanteraResultStatus
    request: CanteraReactorRequest
    times: tuple[float, ...] = field(default_factory=tuple)
    temperature_series: tuple[float, ...] = field(default_factory=tuple)
    pressure_series: tuple[float, ...] = field(default_factory=tuple)
    species_series: dict[str, tuple[float, ...]] = field(default_factory=dict)
    table: dict[str, Any] = field(default_factory=dict)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _status_value(self.status))
        request = (
            self.request
            if isinstance(self.request, CanteraReactorRequest)
            else CanteraReactorRequest.from_dict(self.request)
        )
        object.__setattr__(self, "request", request)
        object.__setattr__(self, "times", tuple(float(item) for item in self.times))
        object.__setattr__(
            self,
            "temperature_series",
            tuple(float(item) for item in self.temperature_series),
        )
        object.__setattr__(
            self,
            "pressure_series",
            tuple(float(item) for item in self.pressure_series),
        )
        object.__setattr__(
            self,
            "species_series",
            {
                str(name): tuple(float(item) for item in values)
                for name, values in self.species_series.items()
            },
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
            "times": list(self.times),
            "temperature_series": list(self.temperature_series),
            "pressure_series": list(self.pressure_series),
            "species_series": {
                species: list(values)
                for species, values in self.species_series.items()
            },
            "table": dict(self.table),
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> CanteraReactorResult:
        if not isinstance(data, Mapping):
            msg = "CanteraReactorResult data must be a mapping."
            raise TypeError(msg)
        return cls(
            status=str(data.get("status", CanteraResultStatus.ERROR.value)),
            request=CanteraReactorRequest.from_dict(data.get("request", {})),
            times=tuple(float(item) for item in data.get("times", ()) or ()),
            temperature_series=tuple(
                float(item) for item in data.get("temperature_series", ()) or ()
            ),
            pressure_series=tuple(float(item) for item in data.get("pressure_series", ()) or ()),
            species_series={
                str(key): tuple(float(item) for item in values)
                for key, values in dict(data.get("species_series", {}) or {}).items()
            },
            table=dict(data.get("table", {}) or {}),
            diagnostics=DiagnosticReport.from_dict(dict(data.get("diagnostics", {}) or {})),
            metadata=dict(data.get("metadata", {}) or {}),
        )


def default_reactor_request() -> CanteraReactorRequest:
    return CanteraReactorRequest()


def _status_value(status: str | CanteraResultStatus) -> str:
    if isinstance(status, CanteraResultStatus):
        return status.value
    text = str(status or CanteraResultStatus.ERROR.value)
    try:
        return CanteraResultStatus(text).value
    except ValueError:
        return text


def _reactor_kind_value(kind: str | CanteraReactorKind) -> str:
    if isinstance(kind, CanteraReactorKind):
        return kind.value
    text = str(kind or CanteraReactorKind.CONSTANT_VOLUME.value)
    try:
        return CanteraReactorKind(text).value
    except ValueError:
        return text


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


__all__ = [
    "CanteraMixtureSpec",
    "CanteraReactorKind",
    "CanteraReactorRequest",
    "CanteraReactorResult",
    "CanteraResultStatus",
    "default_reactor_request",
]

