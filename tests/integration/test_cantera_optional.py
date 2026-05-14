from __future__ import annotations

import pytest

from osw.solvers.cantera.adapter import CanteraReactorConfig, CanteraReactorPlugin


def test_cantera_optional_real_backend_runs_small_reactor() -> None:
    pytest.importorskip("cantera")
    plugin = CanteraReactorPlugin()

    result = plugin.run_reactor(
        CanteraReactorConfig(
            mechanism="gri30.yaml",
            temperature_k=1000.0,
            pressure_pa=101325.0,
            composition={"CH4": 1.0, "O2": 2.0, "N2": 7.52},
            end_time_s=1e-5,
            time_step_s=1e-5,
        )
    )

    assert result.table.rows
    assert result.plot_dataset_placeholder["kind"] == "cantera_temperature_time"
