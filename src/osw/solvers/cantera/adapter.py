"""Cantera-backed 0D reactor plugin for bounded CHM demos."""

from __future__ import annotations

import importlib.util
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol

from osw.core.diagnostics import DiagnosticReport
from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.manifest import PluginManifest
from osw.post.table_model import TablePreview

_SAFE_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_./:+-]+$")
_LIMITATIONS = (
    "Cantera support in OSW v0.1 is a bounded 0D reactor demo, not a "
    "combustion CFD solver.",
    "This plugin is not a process simulator and does not model plant flowsheets.",
    "Inputs and outputs use SI units at the plugin boundary.",
)
_MAX_REACTOR_STEPS = 10_000
_MAX_END_TIME_S = 10.0
_PLUGIN_METADATA: dict[str, Any] = {
    "id": "osw.solvers.cantera.reactor0d",
    "name": "Cantera 0D Reactor Plugin",
    "version": "0.1.0",
    "domain": "solver",
    "type": "solver_adapter",
    "license": "GPL-3.0-or-later",
    "entry_point": "osw.solvers.cantera.adapter:CanteraReactorPlugin",
    "adapter_class": "CanteraReactorPlugin",
    "input_formats": ["osw.chm.reactor0d.si"],
    "output_formats": [
        "osw.table.species_time",
        "osw.plot.temperature_time",
        "csv",
    ],
    "requires": [],
    "optional_requires": ["cantera"],
    "capabilities": [
        "validate",
        "prepare_case",
        "reactor_0d",
        "time_integration",
        "table_result",
        "plot_dataset_placeholder",
        "dependency_diagnostic",
        "mechanism_diagnostic",
    ],
    "preview_required": True,
    "mutates_project": False,
    "executes_external_process": False,
    "dependency_behavior": (
        "Cantera is optional; importing this plugin does not import Cantera. "
        "0D reactor runs return friendly diagnostics when Cantera or a mechanism "
        "is missing."
    ),
    "safety_flags": [
        "lazy_optional_dependency",
        "no_external_process",
        "no_project_mutation",
        "si_units_required",
        "bounded_0d_demo",
    ],
    "limitations": list(_LIMITATIONS),
}


class CanteraBackend(Protocol):
    def mechanism_available(self, mechanism: str) -> bool:
        """Return whether the mechanism can be loaded."""

    def run_reactor(self, config: CanteraReactorConfig) -> tuple[CanteraStateSample, ...]:
        """Run a bounded 0D reactor and return sampled states."""


class CanteraDependencyError(RuntimeError):
    """Raised when Cantera is needed but unavailable."""

    def __init__(self, report: DiagnosticReport) -> None:
        self.report = report
        super().__init__(report.summary())


class CanteraInputError(ValueError):
    """Raised when reactor inputs are invalid."""


class CanteraMechanismError(ValueError):
    """Raised when a Cantera mechanism cannot be loaded."""

    def __init__(self, report: DiagnosticReport) -> None:
        self.report = report
        super().__init__(report.summary())

    @classmethod
    def from_message(cls, message: str, *, mechanism: str = "") -> CanteraMechanismError:
        report = DiagnosticReport()
        report.add_error("cantera.mechanism_missing", message, path=mechanism)
        return cls(report)


@dataclass(frozen=True)
class CanteraReactorConfig:
    """Explicit SI inputs for a bounded Cantera 0D reactor demo."""

    mechanism: str = "gri30.yaml"
    phase_name: str = ""
    temperature_k: float = 1000.0
    pressure_pa: float = 101325.0
    composition: Mapping[str, float] = field(
        default_factory=lambda: {"CH4": 1.0, "O2": 2.0, "N2": 7.52}
    )
    end_time_s: float = 1.0e-3
    time_step_s: float = 1.0e-4
    reactor_type: str = "constant_volume"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "composition",
            {str(species): float(amount) for species, amount in self.composition.items()},
        )
        _validate_config(self)


@dataclass(frozen=True)
class CanteraStateSample:
    time_s: float
    temperature_k: float
    pressure_pa: float
    species_mole_fractions: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "species_mole_fractions",
            {
                str(species): float(value)
                for species, value in self.species_mole_fractions.items()
            },
        )


@dataclass(frozen=True)
class CanteraReactorResult:
    config: CanteraReactorConfig
    samples: tuple[CanteraStateSample, ...]
    diagnostics: tuple[str, ...] = ()
    source: str = "Cantera"
    limitations: tuple[str, ...] = field(default_factory=lambda: _LIMITATIONS)

    @property
    def table(self) -> TablePreview:
        species = _species_columns(self.samples)
        rows = tuple(
            (
                _format_number(sample.time_s),
                _format_number(sample.temperature_k),
                _format_number(sample.pressure_pa),
                *[
                    _format_number(sample.species_mole_fractions.get(name, 0.0))
                    for name in species
                ],
            )
            for sample in self.samples
        )
        return TablePreview(
            columns=("time_s", "temperature_k", "pressure_pa", *species),
            rows=rows,
            title="Cantera 0D reactor species/time",
            source=self.source,
            notes=self.limitations,
        )

    @property
    def plot_dataset_placeholder(self) -> dict[str, Any]:
        return {
            "kind": "cantera_temperature_time",
            "source": self.source,
            "x": "time_s",
            "y": ["temperature_k"],
            "status": "placeholder",
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "reactor_type": self.config.reactor_type,
            "mechanism": self.config.mechanism,
            "temperature_k_initial": self.config.temperature_k,
            "pressure_pa_initial": self.config.pressure_pa,
            "table": {
                "columns": list(self.table.columns),
                "rows": [list(row) for row in self.table.rows],
            },
            "plot_dataset_placeholder": self.plot_dataset_placeholder,
            "diagnostics": list(self.diagnostics),
            "limitations": list(self.limitations),
        }


class CanteraReactorPlugin(SolverAdapterPlugin):
    """Prepare and run a bounded in-process Cantera 0D reactor demo."""

    manifest: ClassVar[PluginManifest] = PluginManifest.from_dict(_PLUGIN_METADATA)

    def __init__(
        self,
        *,
        backend: CanteraBackend | None = None,
        dependency_checker: Callable[[], bool] | None = None,
    ) -> None:
        self._backend = backend
        self._dependency_checker = dependency_checker or _cantera_available
        super().__init__()

    def metadata(self) -> dict[str, Any]:
        return {
            key: list(value) if isinstance(value, list | tuple) else value
            for key, value in _PLUGIN_METADATA.items()
        }

    def dependency_report(self) -> DiagnosticReport:
        report = DiagnosticReport()
        if self._backend is None and not self._dependency_checker():
            report.add_error(
                "cantera.missing_dependency",
                (
                    "Cantera is not installed. Install the optional Cantera "
                    "dependency to run the 0D reactor demo."
                ),
            )
        return report

    def mechanism_report(self, mechanism: str) -> DiagnosticReport:
        report = DiagnosticReport()
        if not mechanism.strip():
            report.add_error("cantera.mechanism_missing", "Cantera mechanism is required.")
            return report
        try:
            available = self._require_backend().mechanism_available(mechanism)
        except CanteraDependencyError:
            raise
        except Exception as exc:
            report.add_error(
                "cantera.mechanism_missing",
                f"Cantera mechanism was not found: {mechanism}. {exc}",
                path=mechanism,
            )
            return report
        if not available:
            report.add_error(
                "cantera.mechanism_missing",
                f"Cantera mechanism was not found: {mechanism}.",
                path=mechanism,
            )
        return report

    def validate(self, config: CanteraReactorConfig | Mapping[str, Any]) -> tuple[str, ...]:
        try:
            _coerce_config(config)
        except (TypeError, ValueError) as exc:
            return (str(exc),)
        return ()

    def prepare_case(self, parameters: dict[str, Any]) -> dict[str, Any]:
        try:
            config = _coerce_config(parameters.get("case", parameters))
        except (TypeError, ValueError) as exc:
            return {
                "solver": "Cantera",
                "adapter_id": self.id,
                "execution_mode": "preview_invalid",
                "run_preview": {
                    "mechanism": None,
                    "reactor_type": None,
                    "temperature_k": None,
                    "pressure_pa": None,
                    "end_time_s": None,
                    "time_step_s": None,
                    "time_steps": None,
                    "outputs": ["species/time table", "temperature/time plot placeholder"],
                },
                "warnings": [str(exc)],
                "limitations": list(_LIMITATIONS),
            }
        warnings: list[str] = []
        return {
            "solver": "Cantera",
            "adapter_id": self.id,
            "execution_mode": "in_process_optional",
            "run_preview": {
                "mechanism": config.mechanism,
                "reactor_type": config.reactor_type,
                "temperature_k": config.temperature_k,
                "pressure_pa": config.pressure_pa,
                "end_time_s": config.end_time_s,
                "time_step_s": config.time_step_s,
                "time_steps": _time_step_count(config),
                "outputs": ["species/time table", "temperature/time plot placeholder"],
            },
            "warnings": warnings,
            "limitations": list(_LIMITATIONS),
        }

    def run_reactor(self, config: CanteraReactorConfig | Mapping[str, Any]) -> CanteraReactorResult:
        normalized = _coerce_config(config)
        mechanism_report = self.mechanism_report(normalized.mechanism)
        if mechanism_report.has_errors:
            raise CanteraMechanismError(mechanism_report)
        samples = self._require_backend().run_reactor(normalized)
        return CanteraReactorResult(config=normalized, samples=tuple(samples))

    def _require_backend(self) -> CanteraBackend:
        if self._backend is not None:
            return self._backend
        report = self.dependency_report()
        if report.has_errors:
            raise CanteraDependencyError(report)
        self._backend = _CanteraModuleBackend()
        return self._backend


class _CanteraModuleBackend:
    def __init__(self) -> None:
        import cantera as ct

        self._ct = ct

    def mechanism_available(self, mechanism: str) -> bool:
        try:
            self._solution(mechanism, "")
        except Exception:
            return False
        return True

    def run_reactor(self, config: CanteraReactorConfig) -> tuple[CanteraStateSample, ...]:
        gas = self._solution(config.mechanism, config.phase_name)
        gas.TPX = (
            config.temperature_k,
            config.pressure_pa,
            _composition_string(config.composition),
        )
        reactor = self._ct.IdealGasReactor(gas)
        network = self._ct.ReactorNet([reactor])
        samples = [
            _sample_from_gas(0.0, gas, tuple(config.composition)),
        ]
        current_time = 0.0
        while current_time < config.end_time_s:
            current_time = min(config.end_time_s, current_time + config.time_step_s)
            network.advance(current_time)
            samples.append(_sample_from_gas(current_time, gas, tuple(config.composition)))
        return tuple(samples)

    def _solution(self, mechanism: str, phase_name: str):
        if phase_name:
            return self._ct.Solution(mechanism, phase_name)
        return self._ct.Solution(mechanism)


def _cantera_available() -> bool:
    return importlib.util.find_spec("cantera") is not None


def _coerce_config(value: CanteraReactorConfig | Mapping[str, Any]) -> CanteraReactorConfig:
    if isinstance(value, CanteraReactorConfig):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("Cantera reactor config must be a CanteraReactorConfig or mapping.")
    return CanteraReactorConfig(
        mechanism=str(value.get("mechanism", "gri30.yaml")),
        phase_name=str(value.get("phase_name", "")),
        temperature_k=float(value.get("temperature_k", 1000.0)),
        pressure_pa=float(value.get("pressure_pa", 101325.0)),
        composition=dict(value.get("composition", {"CH4": 1.0, "O2": 2.0, "N2": 7.52})),
        end_time_s=float(value.get("end_time_s", 1.0e-3)),
        time_step_s=float(value.get("time_step_s", 1.0e-4)),
        reactor_type=str(value.get("reactor_type", "constant_volume")),
    )


def _validate_config(config: CanteraReactorConfig) -> None:
    for field_name, value in (
        ("mechanism", config.mechanism),
        ("phase_name", config.phase_name),
        ("reactor_type", config.reactor_type),
    ):
        if value and not _SAFE_TOKEN_PATTERN.match(value):
            raise CanteraInputError(f"Cantera {field_name} contains unsupported characters.")
    if config.temperature_k <= 0:
        raise CanteraInputError("Cantera temperature_k must be greater than zero.")
    if config.pressure_pa <= 0:
        raise CanteraInputError("Cantera pressure_pa must be greater than zero.")
    if config.end_time_s <= 0:
        raise CanteraInputError("Cantera end_time_s must be greater than zero.")
    if config.end_time_s > _MAX_END_TIME_S:
        raise CanteraInputError(
            f"Cantera end_time_s must not exceed {_MAX_END_TIME_S:g} seconds for v0.1."
        )
    if config.time_step_s <= 0:
        raise CanteraInputError("Cantera time_step_s must be greater than zero.")
    if config.time_step_s > config.end_time_s:
        raise CanteraInputError("Cantera time_step_s must not exceed end_time_s.")
    if _time_step_count(config) > _MAX_REACTOR_STEPS:
        raise CanteraInputError(
            f"Cantera time integration is bounded to {_MAX_REACTOR_STEPS} steps for v0.1."
        )
    if config.reactor_type != "constant_volume":
        raise CanteraInputError("OSW v0.1 Cantera plugin supports only constant_volume.")
    if not config.composition:
        raise CanteraInputError("Cantera gas composition is required.")
    for species, amount in config.composition.items():
        if not species or not _SAFE_TOKEN_PATTERN.match(species):
            raise CanteraInputError("Cantera species names must be plain tokens.")
        if amount < 0 or not math.isfinite(amount):
            raise CanteraInputError("Cantera species amounts must be finite and non-negative.")
    if sum(config.composition.values()) <= 0:
        raise CanteraInputError("Cantera species amounts must sum to a positive value.")


def _time_step_count(config: CanteraReactorConfig) -> int:
    return int(math.ceil(config.end_time_s / config.time_step_s))


def _species_columns(samples: tuple[CanteraStateSample, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for sample in samples:
        for species in sample.species_mole_fractions:
            if species not in seen:
                seen.append(species)
    return tuple(seen)


def _composition_string(composition: Mapping[str, float]) -> str:
    return ", ".join(f"{species}:{amount:.12g}" for species, amount in composition.items())


def _sample_from_gas(
    time_s: float,
    gas: Any,
    species_names: tuple[str, ...],
) -> CanteraStateSample:
    fractions = {species: float(gas[species].X[0]) for species in species_names}
    return CanteraStateSample(
        time_s=float(time_s),
        temperature_k=float(gas.T),
        pressure_pa=float(gas.P),
        species_mole_fractions=fractions,
    )


def _format_number(value: float) -> str:
    return f"{value:.12g}"
