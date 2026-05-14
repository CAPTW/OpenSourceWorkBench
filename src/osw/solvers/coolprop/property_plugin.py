"""CoolProp-backed property calculator plugin for bounded CHM demos."""

from __future__ import annotations

import importlib.util
import math
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol

from osw.core.diagnostics import DiagnosticReport
from osw.plugins.base import PropertyModelPlugin
from osw.plugins.manifest import PluginManifest
from osw.post.table_model import TablePreview

_SAFE_FLUID_PATTERN = re.compile(r"^[A-Za-z0-9_&./:+-]+$")
_KNOWN_OUTPUT_UNITS = {
    "D": "kg/m^3",
    "H": "J/kg",
    "S": "J/kg/K",
    "C": "J/kg/K",
    "CPMASS": "J/kg/K",
    "V": "Pa*s",
    "L": "W/m/K",
    "P": "Pa",
    "T": "K",
    "Q": "1",
}
_DEFAULT_OUTPUTS = ("D", "H")
_LIMITATIONS = (
    "CoolProp support in OSW v0.1 is a property-point and sweep-table demo, "
    "not a process flowsheet simulator.",
    "Inputs and outputs use SI units at the plugin boundary.",
)
_PLUGIN_METADATA: dict[str, Any] = {
    "id": "osw.solvers.coolprop.property",
    "name": "CoolProp Property Plugin",
    "version": "0.1.0",
    "domain": "property",
    "type": "property_model",
    "license": "GPL-3.0-or-later",
    "entry_point": "osw.solvers.coolprop.property_plugin:CoolPropPropertyPlugin",
    "adapter_class": "CoolPropPropertyPlugin",
    "input_formats": ["osw.property.state.si"],
    "output_formats": ["osw.property.table", "csv", "osw.plot.placeholder"],
    "requires": [],
    "optional_requires": ["CoolProp"],
    "capabilities": [
        "validate",
        "property_calculation",
        "sweep_table",
        "csv_export",
        "plot_dataset_placeholder",
        "dependency_diagnostic",
    ],
    "preview_required": True,
    "mutates_project": False,
    "executes_external_process": False,
    "dependency_behavior": (
        "CoolProp is optional; importing this plugin does not import CoolProp. "
        "Property calculations return a friendly diagnostic when CoolProp is missing."
    ),
    "safety_flags": [
        "lazy_optional_dependency",
        "no_external_process",
        "no_project_mutation",
        "si_units_required",
    ],
    "limitations": list(_LIMITATIONS),
}


class CoolPropBackend(Protocol):
    def props_si(
        self,
        output: str,
        input1_name: str,
        input1_value: float,
        input2_name: str,
        input2_value: float,
        fluid: str,
    ) -> float:
        """Return a CoolProp PropsSI value."""


class CoolPropDependencyError(RuntimeError):
    """Raised when CoolProp is needed but unavailable."""

    def __init__(self, report: DiagnosticReport) -> None:
        self.report = report
        super().__init__(report.summary())


class CoolPropInputError(ValueError):
    """Raised when property inputs are invalid."""


@dataclass(frozen=True)
class CoolPropStateInput:
    """Explicit SI state inputs for a CoolProp property point."""

    fluid: str
    pressure_pa: float
    temperature_k: float
    outputs: tuple[str, ...] = _DEFAULT_OUTPUTS

    def __post_init__(self) -> None:
        object.__setattr__(self, "outputs", tuple(str(output).upper() for output in self.outputs))
        _validate_state(self)


@dataclass(frozen=True)
class CoolPropPropertyRecord:
    name: str
    value: float
    unit: str
    source: str = "CoolProp"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
        }


@dataclass(frozen=True)
class CoolPropPropertyResult:
    fluid: str
    pressure_pa: float
    temperature_k: float
    properties: Mapping[str, CoolPropPropertyRecord]
    diagnostics: tuple[str, ...] = ()
    limitations: tuple[str, ...] = field(default_factory=lambda: _LIMITATIONS)
    source: str = "CoolProp"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "fluid": self.fluid,
            "pressure_pa": self.pressure_pa,
            "temperature_k": self.temperature_k,
            "properties": {
                name: record.to_dict() for name, record in self.properties.items()
            },
            "diagnostics": list(self.diagnostics),
            "limitations": list(self.limitations),
            "plot_dataset_placeholder": self.plot_dataset_placeholder(),
        }

    def to_table_preview(self) -> TablePreview:
        rows = tuple(
            (
                self.fluid,
                _format_number(self.pressure_pa),
                _format_number(self.temperature_k),
                name,
                _format_number(record.value),
                record.unit,
            )
            for name, record in self.properties.items()
        )
        return TablePreview(
            columns=("fluid", "pressure_pa", "temperature_k", "property", "value", "unit"),
            rows=rows,
            title="CoolProp property point",
            source=self.source,
            notes=self.limitations,
        )

    def plot_dataset_placeholder(self) -> dict[str, Any]:
        return {
            "kind": "property_point",
            "source": self.source,
            "x": "temperature_k",
            "y": list(self.properties),
            "status": "placeholder",
        }


class CoolPropPropertyPlugin(PropertyModelPlugin):
    """Calculate simple CoolProp property points and sweep tables."""

    manifest: ClassVar[PluginManifest] = PluginManifest.from_dict(_PLUGIN_METADATA)

    def __init__(
        self,
        *,
        backend: CoolPropBackend | None = None,
        dependency_checker: Callable[[], bool] | None = None,
    ) -> None:
        self._backend = backend
        self._dependency_checker = dependency_checker or _coolprop_available
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
                "coolprop.missing_dependency",
                (
                    "CoolProp is not installed. Install the optional CoolProp "
                    "dependency to calculate thermophysical properties."
                ),
            )
        return report

    def validate(self, state: CoolPropStateInput | Mapping[str, Any]) -> tuple[str, ...]:
        try:
            _coerce_state_input(state)
        except (TypeError, ValueError) as exc:
            return (str(exc),)
        return ()

    def evaluate(self, parameters: dict[str, Any]) -> dict[str, Any]:
        state = _coerce_state_input(parameters.get("state", parameters))
        return self.calculate_state(state).to_dict()

    def calculate_state(
        self,
        state: CoolPropStateInput | Mapping[str, Any],
    ) -> CoolPropPropertyResult:
        normalized = _coerce_state_input(state)
        backend = self._require_backend()
        records: dict[str, CoolPropPropertyRecord] = {}
        diagnostics: list[str] = []
        for output in normalized.outputs:
            try:
                value = backend.props_si(
                    output,
                    "P",
                    normalized.pressure_pa,
                    "T",
                    normalized.temperature_k,
                    normalized.fluid,
                )
            except Exception as exc:
                raise CoolPropInputError(f"CoolProp could not calculate {output}: {exc}") from exc
            if not math.isfinite(value):
                diagnostics.append(f"CoolProp returned a non-finite value for {output}.")
            records[output] = CoolPropPropertyRecord(
                name=output,
                value=float(value),
                unit=_KNOWN_OUTPUT_UNITS.get(output, "SI"),
            )
        return CoolPropPropertyResult(
            fluid=normalized.fluid,
            pressure_pa=normalized.pressure_pa,
            temperature_k=normalized.temperature_k,
            properties=records,
            diagnostics=tuple(diagnostics),
        )

    def sweep_table(
        self,
        *,
        fluid: str,
        pressure_pa: float,
        temperatures_k: Iterable[float],
        outputs: Sequence[str] = ("D",),
    ) -> TablePreview:
        normalized_outputs = tuple(str(output).upper() for output in outputs)
        property_columns = tuple(
            f"{output} [{_KNOWN_OUTPUT_UNITS.get(output, 'SI')}]"
            for output in normalized_outputs
        )
        columns = (
            "fluid",
            "pressure_pa",
            "temperature_k",
            *property_columns,
        )
        rows: list[tuple[str, ...]] = []
        for temperature_k in temperatures_k:
            result = self.calculate_state(
                CoolPropStateInput(
                    fluid=fluid,
                    pressure_pa=pressure_pa,
                    temperature_k=float(temperature_k),
                    outputs=normalized_outputs,
                )
            )
            rows.append(
                (
                    result.fluid,
                    _format_number(result.pressure_pa),
                    _format_number(result.temperature_k),
                    *[
                        _format_number(result.properties[output].value)
                        for output in normalized_outputs
                    ],
                )
            )
        return TablePreview(
            columns=columns,
            rows=tuple(rows),
            title="CoolProp property sweep",
            source="CoolProp",
            notes=_LIMITATIONS,
        )

    def _require_backend(self) -> CoolPropBackend:
        if self._backend is not None:
            return self._backend
        report = self.dependency_report()
        if report.has_errors:
            raise CoolPropDependencyError(report)
        self._backend = _load_coolprop_backend()
        return self._backend


class _CoolPropModuleBackend:
    def __init__(self) -> None:
        from CoolProp.CoolProp import PropsSI

        self._props_si = PropsSI

    def props_si(
        self,
        output: str,
        input1_name: str,
        input1_value: float,
        input2_name: str,
        input2_value: float,
        fluid: str,
    ) -> float:
        return float(
            self._props_si(output, input1_name, input1_value, input2_name, input2_value, fluid)
        )


def _load_coolprop_backend() -> CoolPropBackend:
    try:
        return _CoolPropModuleBackend()
    except ModuleNotFoundError as exc:
        report = DiagnosticReport()
        report.add_error(
            "coolprop.missing_dependency",
            (
                "CoolProp is not installed. Install the optional CoolProp dependency "
                "to calculate thermophysical properties."
            ),
        )
        raise CoolPropDependencyError(report) from exc


def _coolprop_available() -> bool:
    return importlib.util.find_spec("CoolProp") is not None


def _coerce_state_input(value: CoolPropStateInput | Mapping[str, Any]) -> CoolPropStateInput:
    if isinstance(value, CoolPropStateInput):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("CoolProp state input must be a CoolPropStateInput or mapping.")
    return CoolPropStateInput(
        fluid=str(value.get("fluid", "")),
        pressure_pa=float(value.get("pressure_pa", 0.0)),
        temperature_k=float(value.get("temperature_k", 0.0)),
        outputs=tuple(value.get("outputs", _DEFAULT_OUTPUTS)),
    )


def _validate_state(state: CoolPropStateInput) -> None:
    if not state.fluid.strip():
        raise CoolPropInputError("CoolProp fluid is required.")
    if not _SAFE_FLUID_PATTERN.match(state.fluid):
        raise CoolPropInputError(
            "CoolProp fluid contains unsupported characters; use a plain fluid name."
        )
    if state.pressure_pa <= 0:
        raise CoolPropInputError("CoolProp pressure_pa must be greater than zero.")
    if state.temperature_k <= 0:
        raise CoolPropInputError("CoolProp temperature_k must be greater than zero.")
    if not state.outputs:
        raise CoolPropInputError("At least one CoolProp output property is required.")
    for output in state.outputs:
        if not _SAFE_FLUID_PATTERN.match(output):
            raise CoolPropInputError(
                "CoolProp output property contains unsupported characters."
            )


def _format_number(value: float) -> str:
    return f"{value:.12g}"
