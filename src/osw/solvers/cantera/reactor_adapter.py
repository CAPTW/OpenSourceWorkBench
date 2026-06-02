"""Lazy optional Cantera 0D reactor adapter."""

from __future__ import annotations

import importlib
import importlib.util
import math
import re
from collections.abc import Mapping
from typing import Any

from osw.core.diagnostics import DiagnosticCode, DiagnosticReport

from .model import (
    CanteraMixtureSpec,
    CanteraReactorKind,
    CanteraReactorRequest,
    CanteraReactorResult,
    CanteraResultStatus,
)

_SAFE_MECHANISM_PATTERN = re.compile(r"^[A-Za-z0-9_./:+\\-]+$")
_MAX_REACTOR_STEPS = 10_000
_MAX_END_TIME = 10.0
_DEPENDENCY_MESSAGE = (
    "Cantera is not installed. Install the CHM optional extra or install Cantera "
    "to run reactor calculations."
)


def cantera_available() -> bool:
    """Return whether the optional Cantera package can be imported."""

    return importlib.util.find_spec("cantera") is not None


def list_available_mechanisms(
    cantera_module: object | None = None,
) -> tuple[list[str], DiagnosticReport]:
    """Return a small mechanism list when Cantera exposes data directories."""

    report = DiagnosticReport()
    module = cantera_module or _load_cantera_module(report)
    if module is None:
        return [], report
    mechanisms = ["gri30.yaml"]
    get_data_directories = getattr(module, "get_data_directories", None)
    if callable(get_data_directories):
        try:
            from pathlib import Path

            for directory in get_data_directories():
                mechanisms.extend(
                    path.name
                    for path in Path(directory).glob("*.yaml")
                    if path.name not in mechanisms
                )
        except Exception as exc:
            report.add_warning(
                "cantera-mechanism-list-warning",
                f"Could not enumerate Cantera mechanisms: {exc}",
            )
    return sorted(dict.fromkeys(mechanisms)), report


def run_zero_d_reactor(
    request: CanteraReactorRequest | Mapping[str, Any],
    *,
    cantera_module: object | None = None,
) -> CanteraReactorResult:
    """Run a bounded in-process Cantera 0D reactor when Cantera is available."""

    normalized = (
        request
        if isinstance(request, CanteraReactorRequest)
        else CanteraReactorRequest.from_dict(request)
    )
    diagnostics = _validate_request(normalized)
    if diagnostics.has_errors:
        return CanteraReactorResult(
            CanteraResultStatus.ERROR,
            normalized,
            diagnostics=diagnostics,
        )

    module = cantera_module or _load_cantera_module(diagnostics)
    if module is None:
        return CanteraReactorResult(
            CanteraResultStatus.DEPENDENCY_MISSING,
            normalized,
            diagnostics=diagnostics,
        )

    try:
        gas = _create_solution(module, normalized.mixture)
        _set_gas_state(gas, normalized.mixture)
        reactor = module.IdealGasReactor(gas)
        network = module.ReactorNet([reactor])
    except Exception as exc:
        diagnostics.add_error(
            "cantera-mechanism-or-state-error",
            (
                f"Cantera could not initialize mechanism "
                f"{normalized.mixture.mechanism!r}: {exc}"
            ),
            path=normalized.mixture.mechanism,
        )
        return CanteraReactorResult(
            CanteraResultStatus.ERROR,
            normalized,
            diagnostics=diagnostics,
        )

    tracked_species = tuple(
        normalized.tracked_species or _tracked_species_from_mixture(normalized.mixture)
    )
    times = [0.0]
    temperatures = [_temperature(reactor, gas)]
    pressures = [_pressure(reactor, gas)]
    species_series: dict[str, list[float]] = {species: [] for species in tracked_species}
    _append_species(species_series, reactor, gas, diagnostics)

    current_time = 0.0
    while current_time < normalized.end_time:
        current_time = min(normalized.end_time, current_time + normalized.time_step)
        try:
            network.advance(current_time)
        except Exception as exc:
            diagnostics.add_error(
                "cantera-reactor-advance-error",
                f"Cantera reactor integration failed at t={current_time:.12g}: {exc}",
            )
            break
        times.append(float(current_time))
        temperatures.append(_temperature(reactor, gas))
        pressures.append(_pressure(reactor, gas))
        _append_species(species_series, reactor, gas, diagnostics)

    table = _time_history_table(times, temperatures, pressures, species_series)
    status = (
        CanteraResultStatus.ERROR
        if diagnostics.has_errors and len(times) <= 1
        else CanteraResultStatus.WARNING
        if diagnostics.has_warnings or diagnostics.has_errors
        else CanteraResultStatus.OK
    )
    return CanteraReactorResult(
        status,
        normalized,
        times=tuple(times),
        temperature_series=tuple(temperatures),
        pressure_series=tuple(pressures),
        species_series={key: tuple(values) for key, values in species_series.items()},
        table=table,
        diagnostics=diagnostics,
        metadata={
            "units": "SI",
            "source": "Cantera IdealGasReactor",
            "reactor_kind": normalized.reactor_kind,
        },
    )


def _load_cantera_module(diagnostics: DiagnosticReport) -> object | None:
    try:
        return importlib.import_module("cantera")
    except ModuleNotFoundError:
        diagnostics.add_error(
            DiagnosticCode.DEPENDENCY_UNAVAILABLE,
            _DEPENDENCY_MESSAGE,
            hint="Install the CHM optional extra or install Cantera.",
        )
        return None


def _validate_request(request: CanteraReactorRequest) -> DiagnosticReport:
    diagnostics = DiagnosticReport()
    mixture = request.mixture
    if not mixture.mechanism.strip():
        diagnostics.add_error("cantera-mechanism-missing", "Cantera mechanism is required.")
    elif not _SAFE_MECHANISM_PATTERN.match(mixture.mechanism):
        diagnostics.add_error(
            "cantera-mechanism-invalid",
            "Cantera mechanism contains unsupported characters.",
            field="mechanism",
        )
    if request.reactor_kind != CanteraReactorKind.CONSTANT_VOLUME.value:
        diagnostics.add_error(
            "cantera-reactor-kind-unsupported",
            "OSW v0.1 supports Cantera constant_volume reactors only.",
        )
    if mixture.temperature <= 0:
        diagnostics.add_error(
            "cantera-invalid-temperature",
            "Cantera mixture temperature must be a positive SI value.",
        )
    if mixture.pressure <= 0:
        diagnostics.add_error(
            "cantera-invalid-pressure",
            "Cantera mixture pressure must be a positive SI value.",
        )
    if request.end_time <= 0 or request.end_time > _MAX_END_TIME:
        diagnostics.add_error(
            "cantera-invalid-end-time",
            f"Cantera end_time must be > 0 and <= {_MAX_END_TIME:g} seconds.",
        )
    if request.time_step <= 0 or request.time_step > request.end_time:
        diagnostics.add_error(
            "cantera-invalid-time-step",
            "Cantera time_step must be positive and no greater than end_time.",
        )
    step_count = math.ceil(request.end_time / request.time_step) if request.time_step > 0 else 0
    if step_count > _MAX_REACTOR_STEPS:
        diagnostics.add_error(
            "cantera-time-step-limit",
            f"Cantera reactor integration is bounded to {_MAX_REACTOR_STEPS} steps.",
        )
    if not request.tracked_species:
        diagnostics.add_warning(
            "cantera-no-tracked-species",
            "No tracked species were provided; species from composition will be used.",
        )
    return diagnostics


def _create_solution(module: object, mixture: CanteraMixtureSpec) -> object:
    if mixture.phase_name:
        return module.Solution(mixture.mechanism, mixture.phase_name)
    return module.Solution(mixture.mechanism)


def _set_gas_state(gas: object, mixture: CanteraMixtureSpec) -> None:
    if mixture.equivalence_ratio is not None and mixture.fuel and mixture.oxidizer:
        gas.TP = mixture.temperature, mixture.pressure
        gas.set_equivalence_ratio(mixture.equivalence_ratio, mixture.fuel, mixture.oxidizer)
        return
    gas.TPX = mixture.temperature, mixture.pressure, mixture.composition


def _tracked_species_from_mixture(mixture: CanteraMixtureSpec) -> tuple[str, ...]:
    if isinstance(mixture.composition, Mapping):
        return tuple(str(key) for key in mixture.composition)
    species = []
    for token in str(mixture.composition).split(","):
        name = token.split(":", 1)[0].strip()
        if name:
            species.append(name)
    return tuple(species)


def _temperature(reactor: object, gas: object) -> float:
    thermo = getattr(reactor, "thermo", None)
    return float(getattr(reactor, "T", getattr(thermo, "T", getattr(gas, "T", 0.0))))


def _pressure(reactor: object, gas: object) -> float:
    thermo = getattr(reactor, "thermo", None)
    return float(getattr(reactor, "P", getattr(thermo, "P", getattr(gas, "P", 0.0))))


def _append_species(
    species_series: dict[str, list[float]],
    reactor: object,
    gas: object,
    diagnostics: DiagnosticReport,
) -> None:
    thermo = getattr(reactor, "thermo", gas)
    for species, values in species_series.items():
        try:
            values.append(_species_mole_fraction(thermo, species))
        except Exception as exc:
            diagnostics.add_warning(
                "cantera-species-unavailable",
                f"Cantera species {species!r} is not available: {exc}",
            )
            values.append(math.nan)


def _species_mole_fraction(thermo: object, species: str) -> float:
    try:
        return float(thermo[species].X[0])
    except Exception:
        index = thermo.species_index(species)
        return float(thermo.X[index])


def _time_history_table(
    times: list[float],
    temperatures: list[float],
    pressures: list[float],
    species_series: dict[str, list[float]],
) -> dict[str, object]:
    species_names = tuple(species_series)
    rows = []
    for index, time_value in enumerate(times):
        rows.append(
            (
                f"{time_value:.12g}",
                f"{temperatures[index]:.12g}",
                f"{pressures[index]:.12g}",
                *(
                    f"{species_series[species][index]:.12g}"
                    if index < len(species_series[species])
                    else ""
                    for species in species_names
                ),
            )
        )
    return {
        "columns": ["time_s", "temperature_K", "pressure_Pa", *species_names],
        "rows": rows,
    }


__all__ = [
    "cantera_available",
    "list_available_mechanisms",
    "run_zero_d_reactor",
]
