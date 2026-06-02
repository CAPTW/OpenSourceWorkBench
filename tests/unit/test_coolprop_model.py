from __future__ import annotations

import json
from pathlib import Path

from osw.solvers.coolprop.model import (
    CoolPropPropertyRequest,
    CoolPropPropertyResult,
    CoolPropPropertyValue,
    CoolPropResultStatus,
    CoolPropSweepRequest,
    CoolPropSweepResult,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "chm"


def test_coolprop_property_request_serializes() -> None:
    request = CoolPropPropertyRequest.from_dict(
        json.loads((FIXTURES / "coolprop_property_request.json").read_text(encoding="utf-8"))
    )

    restored = CoolPropPropertyRequest.from_dict(json.loads(json.dumps(request.to_dict())))

    assert restored.fluid == "Water"
    assert restored.input_pair.first_name == "T"
    assert restored.output_properties == ("density", "viscosity", "enthalpy")
    assert restored.metadata["fixture"] is True


def test_coolprop_sweep_request_serializes() -> None:
    request = CoolPropSweepRequest.from_dict(
        json.loads((FIXTURES / "coolprop_sweep_request.json").read_text(encoding="utf-8"))
    )

    restored = CoolPropSweepRequest.from_dict(json.loads(json.dumps(request.to_dict())))

    assert restored.sweep_variable == "T"
    assert restored.fixed_variable == "P"
    assert restored.sweep_values == (280.0, 300.0, 320.0)


def test_coolprop_property_result_serializes() -> None:
    request = CoolPropPropertyRequest.from_dict(
        json.loads((FIXTURES / "coolprop_property_request.json").read_text(encoding="utf-8"))
    )
    result = CoolPropPropertyResult(
        CoolPropResultStatus.OK,
        request,
        values=(CoolPropPropertyValue("density", 997.0, "kg/m^3"),),
    )

    restored = CoolPropPropertyResult.from_dict(json.loads(json.dumps(result.to_dict())))

    assert restored.status == "ok"
    assert restored.values[0].name == "density"
    assert restored.values[0].value == 997.0


def test_coolprop_sweep_result_serializes() -> None:
    request = CoolPropSweepRequest.from_dict(
        json.loads((FIXTURES / "coolprop_sweep_request.json").read_text(encoding="utf-8"))
    )
    result = CoolPropSweepResult(
        "ok",
        request,
        columns=("T [K]", "density [kg/m^3]"),
        rows=((280.0, 999.0), (300.0, 997.0)),
        series={"density": (999.0, 997.0)},
    )

    restored = CoolPropSweepResult.from_dict(json.loads(json.dumps(result.to_dict())))

    assert restored.rows[1][0] == 300.0
    assert restored.series["density"] == (999.0, 997.0)

