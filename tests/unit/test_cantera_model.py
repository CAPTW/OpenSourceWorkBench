from __future__ import annotations

import json
from pathlib import Path

from osw.solvers.cantera.model import (
    CanteraMixtureSpec,
    CanteraReactorRequest,
    CanteraReactorResult,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "chm"


def test_cantera_mixture_spec_serializes() -> None:
    mixture = CanteraMixtureSpec(
        mechanism="gri30.yaml",
        composition={"CH4": 1.0, "O2": 2.0},
        temperature=1000.0,
        pressure=101325.0,
    )

    restored = CanteraMixtureSpec.from_dict(json.loads(json.dumps(mixture.to_dict())))

    assert restored.mechanism == "gri30.yaml"
    assert restored.composition == {"CH4": 1.0, "O2": 2.0}


def test_cantera_reactor_request_serializes() -> None:
    request = CanteraReactorRequest.from_dict(
        json.loads((FIXTURES / "cantera_reactor_request.json").read_text(encoding="utf-8"))
    )

    restored = CanteraReactorRequest.from_dict(json.loads(json.dumps(request.to_dict())))

    assert restored.reactor_kind == "constant_volume"
    assert restored.end_time == 0.001
    assert restored.tracked_species == ("CH4", "O2")


def test_cantera_reactor_result_serializes() -> None:
    request = CanteraReactorRequest.from_dict(
        json.loads((FIXTURES / "cantera_reactor_request.json").read_text(encoding="utf-8"))
    )
    result = CanteraReactorResult(
        "ok",
        request,
        times=(0.0, 0.001),
        temperature_series=(1000.0, 1100.0),
        pressure_series=(101325.0, 101500.0),
        species_series={"CH4": (0.1, 0.05)},
    )

    restored = CanteraReactorResult.from_dict(json.loads(json.dumps(result.to_dict())))

    assert restored.status == "ok"
    assert restored.times == (0.0, 0.001)
    assert restored.species_series["CH4"][-1] == 0.05

