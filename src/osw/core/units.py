"""Unit and quantity contracts for OSW projects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .validation import ValidationReport


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str

    def __post_init__(self) -> None:
        if not self.unit:
            msg = "Quantity unit is required."
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "unit": self.unit}

    @classmethod
    def from_dict(cls, data: object) -> Quantity:
        if not isinstance(data, dict):
            msg = "Quantity must be a mapping with value and unit."
            raise ValueError(msg)
        if "unit" not in data or not data["unit"]:
            msg = "Quantity unit is required."
            raise ValueError(msg)
        if "value" not in data:
            msg = "Quantity value is required."
            raise ValueError(msg)
        return cls(value=float(data["value"]), unit=str(data["unit"]))


@dataclass(frozen=True)
class UnitSystem:
    name: str = "SI"
    length: str = "m"
    mass: str = "kg"
    time: str = "s"
    temperature: str = "K"
    amount: str = "mol"
    current: str = "A"
    force: str = "N"
    stress: str = "Pa"
    energy: str = "J"
    pressure: str = "Pa"
    defaulted: bool = False

    @classmethod
    def si(cls, *, defaulted: bool = False) -> UnitSystem:
        return cls(defaulted=defaulted)

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "length": self.length,
            "mass": self.mass,
            "time": self.time,
            "temperature": self.temperature,
            "amount": self.amount,
            "current": self.current,
            "force": self.force,
            "stress": self.stress,
            "energy": self.energy,
            "pressure": self.pressure,
        }

    @classmethod
    def from_dict(cls, data: object, *, defaulted: bool = False) -> UnitSystem:
        if not isinstance(data, dict):
            msg = "Unit system must be a mapping."
            raise ValueError(msg)

        base = cls.si(defaulted=defaulted)
        values = base.to_dict()
        for key in values:
            if key in data and data[key] is not None:
                values[key] = str(data[key])
        return cls(**values, defaulted=defaulted)

    def validate(self, *, path: str = "units") -> ValidationReport:
        report = ValidationReport()
        if self.defaulted:
            report.add_warning(path, "Unit system missing; defaulted to SI.")

        for field_name, unit in self.to_dict().items():
            if not unit:
                report.add_error(f"{path}.{field_name}", f"{field_name} unit is required.")
        return report
