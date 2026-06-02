from __future__ import annotations

from osw.core.diagnostics import DiagnosticReport
from osw.post.result_view_model import result_dataset_to_view_model
from osw.solvers.coolprop.model import (
    CoolPropPropertyRequest,
    CoolPropPropertyResult,
    CoolPropPropertyValue,
    CoolPropSweepRequest,
    CoolPropSweepResult,
    PropertyInputPair,
)
from osw.solvers.coolprop.results import (
    coolprop_result_to_result_dataset,
    coolprop_sweep_to_result_dataset,
)


def test_coolprop_property_result_converts_to_result_dataset() -> None:
    result = CoolPropPropertyResult(
        "ok",
        CoolPropPropertyRequest("Water", PropertyInputPair("T", 300.0, "P", 101325.0)),
        values=(
            CoolPropPropertyValue("density", 997.0, "kg/m^3"),
            CoolPropPropertyValue("cp", 4180.0, "J/(kg*K)"),
        ),
    )

    dataset = coolprop_result_to_result_dataset(result)
    view_model = result_dataset_to_view_model(dataset)

    assert dataset.metadata["kind"] == "coolprop_property"
    assert {summary.name for summary in dataset.summaries} == {"density", "cp"}
    assert any(table.title == "CoolProp property table" for table in view_model.tables)


def test_coolprop_sweep_result_converts_to_result_dataset_with_series() -> None:
    result = CoolPropSweepResult(
        "ok",
        CoolPropSweepRequest(
            "Water",
            "T",
            (280.0, 300.0),
            "P",
            101325.0,
            ("density",),
            sweep_unit="K",
            fixed_unit="Pa",
        ),
        columns=("T [K]", "density [kg/m^3]"),
        rows=((280.0, 1000.0), (300.0, 997.0)),
        series={"density": (1000.0, 997.0)},
    )

    dataset = coolprop_sweep_to_result_dataset(result)
    view_model = result_dataset_to_view_model(dataset)

    assert dataset.metadata["kind"] == "coolprop_sweep"
    assert view_model.series[0].x_values == (280.0, 300.0)
    assert view_model.series[0].name == "density"
    assert any(summary.name == "density_min" for summary in dataset.summaries)


def test_coolprop_missing_dependency_result_preserves_diagnostic() -> None:
    diagnostics = DiagnosticReport()
    diagnostics.add_error("dependency-unavailable", "CoolProp is not installed.")
    result = CoolPropPropertyResult(
        "dependency_missing",
        CoolPropPropertyRequest("Water", PropertyInputPair("T", 300.0, "P", 101325.0)),
        diagnostics=diagnostics,
    )

    dataset = coolprop_result_to_result_dataset(result)
    view_model = result_dataset_to_view_model(dataset)

    assert any("CoolProp is not installed" in item for item in view_model.diagnostics)

