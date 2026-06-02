from __future__ import annotations

from osw.core.diagnostics import DiagnosticReport
from osw.post.result_view_model import result_dataset_to_view_model
from osw.solvers.cantera.model import (
    CanteraMixtureSpec,
    CanteraReactorRequest,
    CanteraReactorResult,
)
from osw.solvers.cantera.results import cantera_result_to_result_dataset


def _result() -> CanteraReactorResult:
    request = CanteraReactorRequest(
        mixture=CanteraMixtureSpec(mechanism="gri30.yaml"),
        end_time=0.001,
        time_step=0.0005,
        tracked_species=("CH4", "CO2"),
    )
    return CanteraReactorResult(
        "ok",
        request,
        times=(0.0, 0.0005, 0.001),
        temperature_series=(1000.0, 1010.0, 1025.0),
        pressure_series=(101325.0, 101350.0, 101400.0),
        species_series={"CH4": (0.05, 0.04, 0.03), "CO2": (0.0, 0.01, 0.02)},
        table={
            "columns": ["time_s", "temperature_K", "pressure_Pa", "CH4", "CO2"],
            "rows": [
                ["0", "1000", "101325", "0.05", "0"],
                ["0.001", "1025", "101400", "0.03", "0.02"],
            ],
        },
    )


def test_cantera_reactor_result_converts_to_dataset_series_and_table() -> None:
    dataset = cantera_result_to_result_dataset(_result())
    view_model = result_dataset_to_view_model(dataset)

    assert dataset.metadata["kind"] == "cantera_reactor"
    assert {"final_temperature", "max_temperature", "final_CH4"}.issubset(
        {summary.name for summary in dataset.summaries}
    )
    assert "temperature" in {series.name for series in view_model.series}
    assert "CH4" in {series.name for series in view_model.series}
    assert any(table.title == "Cantera reactor time history" for table in view_model.tables)


def test_cantera_missing_dependency_diagnostic_is_preserved() -> None:
    diagnostics = DiagnosticReport()
    diagnostics.add_error("dependency-unavailable", "Cantera is not installed.")
    result = CanteraReactorResult(
        "dependency_missing",
        CanteraReactorRequest(),
        diagnostics=diagnostics,
    )

    view_model = result_dataset_to_view_model(cantera_result_to_result_dataset(result))

    assert any("Cantera is not installed" in item for item in view_model.diagnostics)

