from __future__ import annotations

import pytest

from osw.solvers.coolprop.model import (
    CoolPropPropertyRequest,
    CoolPropSweepRequest,
    PropertyInputPair,
)
from osw.solvers.coolprop.property_adapter import calculate_properties, sweep_properties
from osw.solvers.coolprop.results import (
    coolprop_result_to_result_dataset,
    coolprop_sweep_to_result_dataset,
)


def test_coolprop_optional_property_and_sweep() -> None:
    pytest.importorskip("CoolProp.CoolProp")

    property_result = calculate_properties(
        CoolPropPropertyRequest(
            "Water",
            PropertyInputPair("T", 300.0, "P", 101325.0),
            output_properties=("density",),
        )
    )
    sweep_result = sweep_properties(
        CoolPropSweepRequest(
            "Water",
            "T",
            (280.0, 300.0, 320.0),
            "P",
            101325.0,
            ("density",),
            sweep_unit="K",
            fixed_unit="Pa",
        )
    )

    assert property_result.status in {"ok", "warning"}
    assert sweep_result.status in {"ok", "warning"}
    assert coolprop_result_to_result_dataset(property_result).summaries
    assert coolprop_sweep_to_result_dataset(sweep_result).fields

