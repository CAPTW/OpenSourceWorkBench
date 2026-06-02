from __future__ import annotations

import pytest

from osw.solvers.cantera.model import (
    CanteraMixtureSpec,
    CanteraReactorRequest,
)
from osw.solvers.cantera.reactor_adapter import (
    cantera_available,
    run_zero_d_reactor,
)


class _SpeciesView:
    def __init__(self, value: float) -> None:
        self.X = [value]


class FakeGas:
    def __init__(self, mechanism: str) -> None:
        if mechanism == "missing.yaml":
            raise ValueError("mechanism was not found")
        self.T = 0.0
        self.P = 0.0
        self._species = {"CH4": 0.05, "O2": 0.20, "CO2": 0.0, "H2O": 0.0}

    @property
    def TPX(self) -> tuple[float, float, object]:
        return self.T, self.P, dict(self._species)

    @TPX.setter
    def TPX(self, values: tuple[float, float, object]) -> None:
        self.T = float(values[0])
        self.P = float(values[1])

    def __getitem__(self, species: str) -> _SpeciesView:
        return _SpeciesView(self._species[species])

    def species_index(self, species: str) -> int:
        return list(self._species).index(species)

    @property
    def X(self) -> list[float]:
        return list(self._species.values())


class FakeReactor:
    def __init__(self, gas: FakeGas) -> None:
        self.thermo = gas
        self.T = gas.T
        self.P = gas.P


class FakeNetwork:
    def __init__(self, reactors: list[FakeReactor]) -> None:
        self.reactor = reactors[0]

    def advance(self, time_value: float) -> None:
        gas = self.reactor.thermo
        gas.T += 50.0 * time_value
        gas.P += 10.0 * time_value
        gas._species["CH4"] = max(0.0, gas._species["CH4"] - time_value)
        gas._species["CO2"] += time_value
        self.reactor.T = gas.T
        self.reactor.P = gas.P


class FakeCanteraModule:
    @staticmethod
    def Solution(mechanism: str, _phase_name: str | None = None) -> FakeGas:
        return FakeGas(mechanism)

    @staticmethod
    def IdealGasReactor(gas: FakeGas) -> FakeReactor:
        return FakeReactor(gas)

    @staticmethod
    def ReactorNet(reactors: list[FakeReactor]) -> FakeNetwork:
        return FakeNetwork(reactors)


def test_cantera_import_is_optional() -> None:
    assert isinstance(cantera_available(), bool)


def test_missing_cantera_returns_dependency_diagnostic(monkeypatch: pytest.MonkeyPatch) -> None:
    from osw.solvers.cantera import reactor_adapter

    def missing(_name: str) -> object:
        raise ModuleNotFoundError("cantera")

    monkeypatch.setattr(reactor_adapter.importlib, "import_module", missing)

    result = run_zero_d_reactor(CanteraReactorRequest())

    assert result.status == "dependency_missing"
    assert "Cantera is not installed" in result.diagnostics.summary()


def test_invalid_mechanism_is_friendly_with_fake_module() -> None:
    result = run_zero_d_reactor(
        CanteraReactorRequest(
            mixture=CanteraMixtureSpec(mechanism="missing.yaml"),
        ),
        cantera_module=FakeCanteraModule,
    )

    assert result.status == "error"
    assert "mechanism was not found" in result.diagnostics.summary()


def test_fake_cantera_reactor_time_history() -> None:
    result = run_zero_d_reactor(
        CanteraReactorRequest(
            mixture=CanteraMixtureSpec(
                mechanism="gri30.yaml",
                composition="CH4:1,O2:2,N2:7.52",
                temperature=1000.0,
                pressure=101325.0,
            ),
            end_time=0.001,
            time_step=0.0005,
            tracked_species=("CH4", "CO2"),
        ),
        cantera_module=FakeCanteraModule,
    )

    assert result.status == "ok"
    assert result.times == (0.0, 0.0005, 0.001)
    assert result.temperature_series[-1] > result.temperature_series[0]
    assert result.species_series["CH4"][-1] < result.species_series["CH4"][0]
    assert result.table["columns"][:3] == ["time_s", "temperature_K", "pressure_Pa"]


def test_real_cantera_reactor_optional() -> None:
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

    assert result.status in {"ok", "warning"}
    assert result.times

