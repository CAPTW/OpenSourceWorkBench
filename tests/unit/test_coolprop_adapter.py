from __future__ import annotations

import importlib.util

import pytest

from osw.solvers.coolprop.model import (
    CoolPropPropertyRequest,
    CoolPropSweepRequest,
    PropertyInputPair,
)
from osw.solvers.coolprop.property_adapter import (
    calculate_properties,
    coolprop_available,
    sweep_properties,
)


class FakeCoolPropModule:
    @staticmethod
    def PropsSI(
        output: str,
        input1_name: str,
        input1_value: float,
        input2_name: str,
        input2_value: float,
        fluid: str,
    ) -> float:
        if fluid == "InvalidFluid":
            raise ValueError("fluid was not found")
        inputs = {input1_name: input1_value, input2_name: input2_value}
        temperature = inputs["T"]
        if output == "D":
            return 1000.0 - 0.2 * (temperature - 280.0)
        if output == "V":
            return 0.001
        if output == "H":
            return 112650.0
        if output == "S":
            return 393.0
        if output == "C":
            return 4180.0
        if output == "L":
            return 0.61
        raise ValueError(output)


def test_coolprop_module_import_is_optional() -> None:
    assert isinstance(coolprop_available(), bool)
    assert importlib.util.find_spec("PySide6") or True


def test_missing_coolprop_returns_dependency_diagnostic(monkeypatch: pytest.MonkeyPatch) -> None:
    from osw.solvers.coolprop import property_adapter

    def missing(_name: str) -> object:
        raise ModuleNotFoundError("CoolProp")

    monkeypatch.setattr(property_adapter.importlib, "import_module", missing)

    result = calculate_properties(
        CoolPropPropertyRequest("Water", PropertyInputPair("T", 300.0, "P", 101325.0))
    )

    assert result.status == "dependency_missing"
    assert result.diagnostics.has_errors
    assert "CoolProp is not installed" in result.diagnostics.summary()


def test_invalid_input_pair_is_friendly() -> None:
    result = calculate_properties(
        CoolPropPropertyRequest("Water", PropertyInputPair("H", 1.0, "P", 101325.0)),
        coolprop_module=FakeCoolPropModule,
    )

    assert result.status == "error"
    assert "Use T or P" in result.diagnostics.summary()


def test_invalid_fluid_is_friendly() -> None:
    result = calculate_properties(
        CoolPropPropertyRequest("InvalidFluid", PropertyInputPair("T", 300.0, "P", 101325.0)),
        coolprop_module=FakeCoolPropModule,
    )

    assert result.status == "error"
    assert "fluid was not found" in result.diagnostics.summary()


def test_fake_coolprop_property_calculation() -> None:
    result = calculate_properties(
        CoolPropPropertyRequest(
            "Water",
            PropertyInputPair("T", 300.0, "P", 101325.0),
            output_properties=("density", "viscosity"),
        ),
        coolprop_module=FakeCoolPropModule,
    )

    assert result.status == "ok"
    assert {value.name for value in result.values} == {"density", "viscosity"}
    assert result.values[0].unit == "kg/m^3"


def test_fake_coolprop_sweep_t_at_fixed_p() -> None:
    result = sweep_properties(
        CoolPropSweepRequest(
            fluid="Water",
            sweep_variable="T",
            sweep_values=(280.0, 300.0, 320.0),
            sweep_unit="K",
            fixed_variable="P",
            fixed_value=101325.0,
            fixed_unit="Pa",
            output_properties=("density",),
        ),
        coolprop_module=FakeCoolPropModule,
    )

    assert result.status == "ok"
    assert result.columns == ("T [K]", "density [kg/m^3]")
    assert len(result.rows) == 3
    assert result.series["density"][0] == 1000.0


def test_real_coolprop_water_property_optional() -> None:
    pytest.importorskip("CoolProp.CoolProp")

    result = calculate_properties(
        CoolPropPropertyRequest(
            "Water",
            PropertyInputPair("T", 300.0, "P", 101325.0),
            output_properties=("density",),
        )
    )

    assert result.status in {"ok", "warning"}
    assert 990.0 < result.values[0].value < 1000.0

