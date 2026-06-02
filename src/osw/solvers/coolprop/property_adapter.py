"""Lazy optional CoolProp property adapter."""

from __future__ import annotations

import importlib
import importlib.util
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

from osw.core.diagnostics import DiagnosticCode, DiagnosticReport

from .model import (
    CoolPropPropertyRequest,
    CoolPropPropertyResult,
    CoolPropPropertyValue,
    CoolPropResultStatus,
    CoolPropSweepRequest,
    CoolPropSweepResult,
    PropertyInputPair,
)

_SAFE_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_&./:+-]+$")
_INPUT_ALIASES = {
    "T": ("T", "K"),
    "TEMPERATURE": ("T", "K"),
    "P": ("P", "Pa"),
    "PRESSURE": ("P", "Pa"),
}
_OUTPUTS = {
    "density": ("D", "kg/m^3"),
    "rho": ("D", "kg/m^3"),
    "viscosity": ("V", "Pa*s"),
    "dynamic_viscosity": ("V", "Pa*s"),
    "enthalpy": ("H", "J/kg"),
    "entropy": ("S", "J/(kg*K)"),
    "cp": ("C", "J/(kg*K)"),
    "cpmass": ("C", "J/(kg*K)"),
    "thermal_conductivity": ("L", "W/(m*K)"),
    "conductivity": ("L", "W/(m*K)"),
}
_DEPENDENCY_MESSAGE = (
    "CoolProp is not installed. Install the CHM optional extra or install CoolProp "
    "to run thermophysical property calculations."
)


def coolprop_available() -> bool:
    """Return whether the optional CoolProp package can be imported."""

    return importlib.util.find_spec("CoolProp") is not None


def list_supported_fluids(
    coolprop_module: object | None = None,
) -> tuple[list[str], DiagnosticReport]:
    """Return supported fluids when CoolProp is available, otherwise a diagnostic."""

    report = DiagnosticReport()
    module = coolprop_module or _load_coolprop_module(report)
    if module is None:
        return [], report
    fluids_list = getattr(module, "FluidsList", None)
    if not callable(fluids_list):
        report.add_warning(
            "coolprop-fluid-list-unavailable",
            "CoolProp did not expose a fluid list API in this environment.",
        )
        return [], report
    try:
        return sorted(str(item) for item in fluids_list()), report
    except Exception as exc:
        report.add_warning(
            "coolprop-fluid-list-failed",
            f"Could not list CoolProp fluids: {exc}",
        )
        return [], report


def calculate_properties(
    request: CoolPropPropertyRequest | Mapping[str, Any],
    *,
    coolprop_module: object | None = None,
) -> CoolPropPropertyResult:
    """Calculate a bounded CoolProp property point with friendly diagnostics."""

    normalized = (
        request
        if isinstance(request, CoolPropPropertyRequest)
        else CoolPropPropertyRequest.from_dict(request)
    )
    diagnostics = _validate_property_request(normalized)
    if diagnostics.has_errors:
        return CoolPropPropertyResult(
            CoolPropResultStatus.ERROR,
            normalized,
            diagnostics=diagnostics,
        )

    module = coolprop_module or _load_coolprop_module(diagnostics)
    if module is None:
        return CoolPropPropertyResult(
            CoolPropResultStatus.DEPENDENCY_MISSING,
            normalized,
            diagnostics=diagnostics,
        )

    props_si = getattr(module, "PropsSI", None)
    if not callable(props_si):
        diagnostics.add_error(
            "coolprop-propssi-unavailable",
            "CoolProp was imported but PropsSI is not available.",
        )
        return CoolPropPropertyResult(
            CoolPropResultStatus.ERROR,
            normalized,
            diagnostics=diagnostics,
        )

    input1, input2 = _normalized_input_pair(normalized.input_pair)
    values: list[CoolPropPropertyValue] = []
    for output_name in normalized.output_properties:
        try:
            output_key, unit = _output_key(output_name)
            value = float(
                props_si(
                    output_key,
                    input1[0],
                    input1[1],
                    input2[0],
                    input2[1],
                    normalized.fluid,
                )
            )
        except Exception as exc:
            diagnostics.add_error(
                "coolprop-property-failed",
                f"CoolProp could not calculate {output_name!r} for {normalized.fluid}: {exc}",
            )
            continue
        if not math.isfinite(value):
            diagnostics.add_warning(
                "coolprop-nonfinite-value",
                f"CoolProp returned a non-finite value for {output_name}.",
            )
        values.append(
            CoolPropPropertyValue(
                name=_canonical_output_name(output_name),
                value=value,
                unit=unit,
                metadata={"coolprop_key": output_key},
            )
        )

    table = {
        "columns": ["Property", "Value", "Unit"],
        "rows": [(value.name, f"{value.value:.12g}", value.unit) for value in values],
    }
    status = (
        CoolPropResultStatus.ERROR
        if diagnostics.has_errors and not values
        else CoolPropResultStatus.WARNING
        if diagnostics.has_warnings or diagnostics.has_errors
        else CoolPropResultStatus.OK
    )
    return CoolPropPropertyResult(
        status,
        normalized,
        values=tuple(values),
        table=table,
        diagnostics=diagnostics,
        metadata={"units": "SI", "source": "CoolProp PropsSI"},
    )


def sweep_properties(
    request: CoolPropSweepRequest | Mapping[str, Any],
    *,
    coolprop_module: object | None = None,
) -> CoolPropSweepResult:
    """Calculate a T/P CoolProp property sweep with table and series output."""

    normalized = (
        request
        if isinstance(request, CoolPropSweepRequest)
        else CoolPropSweepRequest.from_dict(request)
    )
    diagnostics = _validate_sweep_request(normalized)
    if diagnostics.has_errors:
        return CoolPropSweepResult(
            CoolPropResultStatus.ERROR,
            normalized,
            diagnostics=diagnostics,
        )

    module = coolprop_module or _load_coolprop_module(diagnostics)
    if module is None:
        return CoolPropSweepResult(
            CoolPropResultStatus.DEPENDENCY_MISSING,
            normalized,
            diagnostics=diagnostics,
        )

    sweep_name, default_sweep_unit = _normalize_input_name(normalized.sweep_variable)
    sweep_unit = normalized.sweep_unit or default_sweep_unit
    columns = (
        f"{sweep_name} [{sweep_unit}]",
        *(
            f"{_canonical_output_name(output)} [{_output_key(output)[1]}]"
            for output in normalized.output_properties
        ),
    )
    rows: list[tuple[float, ...]] = []
    series: dict[str, list[float]] = {
        _canonical_output_name(output): [] for output in normalized.output_properties
    }
    for sweep_value in normalized.sweep_values:
        input_pair = _pair_for_sweep(normalized, sweep_value)
        property_result = calculate_properties(
            CoolPropPropertyRequest(
                fluid=normalized.fluid,
                input_pair=input_pair,
                output_properties=normalized.output_properties,
                backend=normalized.backend,
                metadata=dict(normalized.metadata),
            ),
            coolprop_module=module,
        )
        diagnostics.extend(property_result.diagnostics)
        if not property_result.values:
            continue
        by_name = {value.name: value.value for value in property_result.values}
        row_values = [float(sweep_value)]
        for output in normalized.output_properties:
            name = _canonical_output_name(output)
            value = float(by_name.get(name, math.nan))
            row_values.append(value)
            series[name].append(value)
        rows.append(tuple(row_values))

    status = (
        CoolPropResultStatus.ERROR
        if diagnostics.has_errors and not rows
        else CoolPropResultStatus.WARNING
        if diagnostics.has_warnings or diagnostics.has_errors
        else CoolPropResultStatus.OK
    )
    return CoolPropSweepResult(
        status,
        normalized,
        columns=columns,
        rows=tuple(rows),
        series={key: tuple(values) for key, values in series.items()},
        diagnostics=diagnostics,
        metadata={"units": "SI", "source": "CoolProp PropsSI"},
    )


def _load_coolprop_module(diagnostics: DiagnosticReport) -> object | None:
    try:
        return importlib.import_module("CoolProp.CoolProp")
    except ModuleNotFoundError:
        diagnostics.add_error(
            DiagnosticCode.DEPENDENCY_UNAVAILABLE,
            _DEPENDENCY_MESSAGE,
            hint="Install the CHM optional extra or install CoolProp.",
        )
        return None


def _validate_property_request(request: CoolPropPropertyRequest) -> DiagnosticReport:
    diagnostics = DiagnosticReport()
    if not request.fluid.strip():
        diagnostics.add_error("coolprop-invalid-fluid", "CoolProp fluid is required.")
    elif not _SAFE_TOKEN_PATTERN.match(request.fluid):
        diagnostics.add_error(
            "coolprop-invalid-fluid",
            "CoolProp fluid contains unsupported characters.",
            field="fluid",
        )
    _validate_input_pair(request.input_pair, diagnostics)
    if not request.output_properties:
        diagnostics.add_error(
            "coolprop-missing-outputs",
            "At least one CoolProp output property is required.",
        )
    for output in request.output_properties:
        try:
            _output_key(output)
        except ValueError as exc:
            diagnostics.add_error("coolprop-invalid-output", str(exc), field="output_properties")
    return diagnostics


def _validate_sweep_request(request: CoolPropSweepRequest) -> DiagnosticReport:
    diagnostics = DiagnosticReport()
    if not request.fluid.strip() or not _SAFE_TOKEN_PATTERN.match(request.fluid):
        diagnostics.add_error("coolprop-invalid-fluid", "CoolProp fluid is required.")
    if not request.sweep_values:
        diagnostics.add_error(
            "coolprop-empty-sweep",
            "CoolProp sweep_values must contain at least one value.",
        )
    try:
        sweep_name, _ = _normalize_input_name(request.sweep_variable)
        fixed_name, _ = _normalize_input_name(request.fixed_variable)
    except ValueError as exc:
        diagnostics.add_error("coolprop-invalid-input-pair", str(exc))
        return diagnostics
    if {sweep_name, fixed_name} != {"T", "P"}:
        diagnostics.add_error(
            "coolprop-invalid-input-pair",
            "CoolProp v0.1 sweeps support T at fixed P or P at fixed T.",
        )
    for output in request.output_properties:
        try:
            _output_key(output)
        except ValueError as exc:
            diagnostics.add_error("coolprop-invalid-output", str(exc))
    return diagnostics


def _validate_input_pair(pair: PropertyInputPair, diagnostics: DiagnosticReport) -> None:
    try:
        first, second = _normalized_input_pair(pair)
    except ValueError as exc:
        diagnostics.add_error("coolprop-invalid-input-pair", str(exc))
        return
    if {first[0], second[0]} != {"T", "P"}:
        diagnostics.add_error(
            "coolprop-invalid-input-pair",
            "CoolProp v0.1 supports T/P or P/T input pairs only.",
        )
    for name, value in (first, second):
        if value <= 0 or not math.isfinite(value):
            diagnostics.add_error(
                "coolprop-invalid-input-value",
                f"CoolProp input {name} must be a finite positive SI value.",
            )


def _normalized_input_pair(pair: PropertyInputPair) -> tuple[tuple[str, float], tuple[str, float]]:
    first_name, _ = _normalize_input_name(pair.first_name)
    second_name, _ = _normalize_input_name(pair.second_name)
    return (first_name, float(pair.first_value)), (second_name, float(pair.second_value))


def _pair_for_sweep(request: CoolPropSweepRequest, sweep_value: float) -> PropertyInputPair:
    sweep_name, sweep_unit = _normalize_input_name(request.sweep_variable)
    fixed_name, fixed_unit = _normalize_input_name(request.fixed_variable)
    return PropertyInputPair(
        first_name=sweep_name,
        first_value=float(sweep_value),
        first_unit=request.sweep_unit or sweep_unit,
        second_name=fixed_name,
        second_value=request.fixed_value,
        second_unit=request.fixed_unit or fixed_unit,
    )


def _normalize_input_name(name: str) -> tuple[str, str]:
    key = str(name).strip().upper()
    if key not in _INPUT_ALIASES:
        msg = f"Unsupported CoolProp input variable: {name!r}. Use T or P."
        raise ValueError(msg)
    return _INPUT_ALIASES[key]


def _output_key(name: str) -> tuple[str, str]:
    key = str(name).strip().lower()
    if key not in _OUTPUTS:
        supported = ", ".join(sorted({key for key in _OUTPUTS if key.isalpha()}))
        msg = f"Unsupported CoolProp output property: {name!r}. Supported: {supported}."
        raise ValueError(msg)
    return _OUTPUTS[key]


def _canonical_output_name(name: str) -> str:
    key = str(name).strip().lower()
    if key in {"rho"}:
        return "density"
    if key in {"dynamic_viscosity"}:
        return "viscosity"
    if key in {"cpmass"}:
        return "cp"
    if key in {"conductivity"}:
        return "thermal_conductivity"
    return key


def _series_summary(values: Sequence[float]) -> tuple[float, float, float, float]:
    finite = [float(item) for item in values if math.isfinite(float(item))]
    if not finite:
        return math.nan, math.nan, math.nan, math.nan
    return finite[0], finite[-1], min(finite), max(finite)


__all__ = [
    "calculate_properties",
    "coolprop_available",
    "list_supported_fluids",
    "sweep_properties",
]
