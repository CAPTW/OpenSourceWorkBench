"""Unit system tests for OSW core contracts."""

from __future__ import annotations

import pytest

from osw.core.project_schema import Project
from osw.core.units import Quantity, UnitSystem, default_engineering_units, default_si_units


def test_si_unit_system_has_named_base_units() -> None:
    units = UnitSystem.si()

    assert units.name == "SI"
    assert units.length == "m"
    assert units.mass == "kg"
    assert units.time == "s"
    assert units.force == "N"
    assert units.stress == "Pa"
    assert units.power == "W"


def test_default_unit_helpers_return_named_systems() -> None:
    assert default_si_units().name == "SI"
    engineering = default_engineering_units()
    assert engineering.name == "Engineering"
    assert engineering.length == "mm"


def test_project_missing_units_defaults_to_si_with_warning() -> None:
    project = Project.from_dict({"metadata": {"name": "missing units demo"}})
    report = project.validate()

    assert project.units == UnitSystem.si(defaulted=True)
    assert report.has_warnings
    assert "Unit system missing; defaulted to SI." in report.messages[0].message


def test_quantity_requires_unit_when_loaded_from_mapping() -> None:
    with pytest.raises(ValueError, match="unit"):
        Quantity.from_dict({"value": 10.0})


def test_quantity_round_trips_value_and_unit() -> None:
    quantity = Quantity(210.0, "GPa")

    assert Quantity.from_dict(quantity.to_dict()) == quantity
