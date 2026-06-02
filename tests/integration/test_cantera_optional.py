from __future__ import annotations

import pytest

from osw.solvers.cantera.model import CanteraMixtureSpec, CanteraReactorRequest
from osw.solvers.cantera.reactor_adapter import run_zero_d_reactor
from osw.solvers.cantera.results import cantera_result_to_result_dataset


def test_cantera_optional_reactor_to_result_dataset() -> None:
    pytest.importorskip("cantera")

    result = run_zero_d_reactor(
        CanteraReactorRequest(
            mixture=CanteraMixtureSpec(
                mechanism="gri30.yaml",
                composition="CH4:1,O2:2,N2:7.52",
                temperature=1000.0,
                pressure=101325.0,
            ),
            end_time=1e-5,
            time_step=1e-5,
            tracked_species=("CH4",),
        )
    )
    dataset = cantera_result_to_result_dataset(result)

    assert result.status in {"ok", "warning"}
    assert dataset.fields
    assert dataset.summaries

