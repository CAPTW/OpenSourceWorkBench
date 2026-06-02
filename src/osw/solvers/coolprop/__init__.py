"""Optional CoolProp property plugin surfaces."""

from __future__ import annotations

from .model import (
    CoolPropPropertyRequest,
    CoolPropPropertyResult,
    CoolPropPropertyValue,
    CoolPropResultStatus,
    CoolPropSweepRequest,
    CoolPropSweepResult,
    PropertyInputPair,
    default_property_request,
    default_sweep_request,
)
from .property_adapter import (
    calculate_properties,
    coolprop_available,
    list_supported_fluids,
    sweep_properties,
)
from .property_plugin import (
    CoolPropDependencyError,
    CoolPropPropertyPlugin,
    CoolPropPropertyRecord,
    CoolPropStateInput,
)
from .property_plugin import (
    CoolPropPropertyResult as LegacyCoolPropPropertyResult,
)
from .results import (
    coolprop_result_to_result_dataset,
    coolprop_sweep_to_result_dataset,
)

__all__ = [
    "CoolPropDependencyError",
    "CoolPropPropertyPlugin",
    "CoolPropPropertyRecord",
    "LegacyCoolPropPropertyResult",
    "CoolPropPropertyRequest",
    "CoolPropPropertyResult",
    "CoolPropPropertyValue",
    "CoolPropResultStatus",
    "CoolPropStateInput",
    "CoolPropSweepRequest",
    "CoolPropSweepResult",
    "PropertyInputPair",
    "calculate_properties",
    "coolprop_available",
    "coolprop_result_to_result_dataset",
    "coolprop_sweep_to_result_dataset",
    "default_property_request",
    "default_sweep_request",
    "list_supported_fluids",
    "sweep_properties",
]
