from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.manifest import PluginType
from osw.solvers.cantera.adapter import (
    CanteraDependencyError,
    CanteraInputError,
    CanteraMechanismError,
    CanteraReactorConfig,
    CanteraReactorPlugin,
    CanteraStateSample,
)


class FakeCanteraBackend:
    def __init__(self, *, missing_mechanism: bool = False) -> None:
        self.missing_mechanism = missing_mechanism
        self.calls: list[CanteraReactorConfig] = []

    def mechanism_available(self, mechanism: str) -> bool:
        return not self.missing_mechanism and mechanism == "gri30.yaml"

    def run_reactor(self, config: CanteraReactorConfig) -> tuple[CanteraStateSample, ...]:
        self.calls.append(config)
        if self.missing_mechanism:
            raise CanteraMechanismError.from_message(
                "Cantera mechanism was not found: gri30.yaml",
                mechanism=config.mechanism,
            )
        return (
            CanteraStateSample(
                time_s=0.0,
                temperature_k=config.temperature_k,
                pressure_pa=config.pressure_pa,
                species_mole_fractions={"CH4": 0.055, "O2": 0.22},
            ),
            CanteraStateSample(
                time_s=config.end_time_s,
                temperature_k=config.temperature_k + 25.0,
                pressure_pa=config.pressure_pa + 100.0,
                species_mole_fractions={"CH4": 0.050, "O2": 0.20},
            ),
        )


def test_cantera_plugin_manifest_is_solver_adapter() -> None:
    plugin = CanteraReactorPlugin(backend=FakeCanteraBackend())
    manifest = plugin.manifest

    assert isinstance(plugin, SolverAdapterPlugin)
    assert manifest.id == "osw.solvers.cantera.reactor0d"
    assert manifest.type is PluginType.SOLVER_ADAPTER
    assert manifest.optional_requires == ("cantera",)
    assert "reactor_0d" in manifest.capabilities
    assert "time_integration" in manifest.capabilities
    assert "table_result" in manifest.capabilities


def test_cantera_manifest_metadata_declares_safety_contract() -> None:
    plugin = CanteraReactorPlugin(backend=FakeCanteraBackend())
    metadata = plugin.metadata()
    manifest_path = (
        Path(__file__).parents[2] / "src" / "osw" / "solvers" / "cantera" / "osw-plugin.json"
    )
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    for surface in (metadata, manifest_data):
        assert surface["entry_point"] == "osw.solvers.cantera.adapter:CanteraReactorPlugin"
        assert surface["adapter_class"] == "CanteraReactorPlugin"
        assert surface["preview_required"] is True
        assert surface["mutates_project"] is False
        assert surface["executes_external_process"] is False
        assert "Cantera is optional" in surface["dependency_behavior"]
        assert any("not a combustion CFD solver" in item for item in surface["limitations"])


def test_cantera_missing_dependency_diagnostic_is_friendly() -> None:
    plugin = CanteraReactorPlugin(dependency_checker=lambda: False)
    report = plugin.dependency_report()

    assert report.has_errors
    assert "Cantera is not installed" in report.summary()
    with pytest.raises(CanteraDependencyError, match="Cantera is not installed"):
        plugin.run_reactor(CanteraReactorConfig())


def test_cantera_missing_mechanism_diagnostic_is_friendly() -> None:
    plugin = CanteraReactorPlugin(backend=FakeCanteraBackend(missing_mechanism=True))
    report = plugin.mechanism_report("missing.yaml")

    assert report.has_errors
    assert "Cantera mechanism was not found" in report.summary()
    with pytest.raises(CanteraMechanismError, match="Cantera mechanism was not found"):
        plugin.run_reactor(CanteraReactorConfig(mechanism="gri30.yaml"))


def test_cantera_reactor_run_produces_table_and_plot_placeholder() -> None:
    backend = FakeCanteraBackend()
    plugin = CanteraReactorPlugin(backend=backend)
    config = CanteraReactorConfig(
        mechanism="gri30.yaml",
        temperature_k=1000.0,
        pressure_pa=101325.0,
        composition={"CH4": 1.0, "O2": 2.0, "N2": 7.52},
        end_time_s=0.002,
        time_step_s=0.001,
    )

    result = plugin.run_reactor(config)

    assert backend.calls == [config]
    assert result.samples[-1].temperature_k == 1025.0
    assert result.table.columns == (
        "time_s",
        "temperature_k",
        "pressure_pa",
        "CH4",
        "O2",
    )
    assert result.table.rows[-1] == ("0.002", "1025", "101425", "0.05", "0.2")
    assert result.plot_dataset_placeholder["x"] == "time_s"
    assert result.plot_dataset_placeholder["y"] == ["temperature_k"]
    assert result.to_dict()["source"] == "Cantera"
    assert "not a process simulator" in " ".join(result.to_dict()["limitations"])


def test_cantera_prepare_case_returns_preview_without_running() -> None:
    plugin = CanteraReactorPlugin(backend=FakeCanteraBackend())
    config = CanteraReactorConfig(end_time_s=0.002, time_step_s=0.001)

    prepared = plugin.prepare_case({"case": config})

    assert prepared["solver"] == "Cantera"
    assert prepared["execution_mode"] == "in_process_optional"
    assert prepared["run_preview"]["time_steps"] == 2
    assert prepared["run_preview"]["mechanism"] == "gri30.yaml"
    assert prepared["warnings"] == []


def test_cantera_reactor_config_rejects_unbounded_step_count() -> None:
    with pytest.raises(CanteraInputError, match="Cantera time integration is bounded"):
        CanteraReactorConfig(end_time_s=10.0, time_step_s=1e-7)


def test_cantera_reactor_config_rejects_excessive_end_time() -> None:
    with pytest.raises(CanteraInputError, match="Cantera end_time_s must not exceed"):
        CanteraReactorConfig(end_time_s=10.1, time_step_s=0.1)


def test_cantera_reactor_config_rejects_zero_sum_composition() -> None:
    with pytest.raises(CanteraInputError, match="sum to a positive value"):
        CanteraReactorConfig(composition={"CH4": 0.0, "O2": 0.0})


def test_cantera_prepare_case_returns_validation_warning_for_invalid_preview() -> None:
    plugin = CanteraReactorPlugin(backend=FakeCanteraBackend())

    prepared = plugin.prepare_case({"case": {"end_time_s": 10.0, "time_step_s": 1e-7}})

    assert prepared["solver"] == "Cantera"
    assert prepared["execution_mode"] == "preview_invalid"
    assert prepared["run_preview"]["time_steps"] is None
    assert any("bounded" in warning for warning in prepared["warnings"])


def test_cantera_example_documents_bounded_si_reactor_workflow() -> None:
    readme = Path(__file__).parents[2] / "examples" / "06_cantera_reactor" / "README.md"
    text = readme.read_text(encoding="utf-8")

    assert "temperature_k" in text
    assert "pressure_pa" in text
    assert "time_s" in text
    assert "Cantera is optional" in text
    assert "not a combustion CFD solver" in text


def test_cantera_real_reactor_optional() -> None:
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

    assert result.samples
    assert result.table.rows
