"""OpenFOAM bounded template helpers for OSW v0.1."""

from __future__ import annotations

from .adapter import OpenFoamCavityTemplateAdapter
from .case_generator import (
    OpenFoamBoundaryConfig,
    OpenFoamCaseGenerator,
    OpenFoamCaseTemplateError,
    OpenFoamCavityConfig,
    OpenFoamGeneratedCase,
    generate_cavity_case,
)

__all__ = [
    "OpenFoamBoundaryConfig",
    "OpenFoamCaseGenerator",
    "OpenFoamCaseTemplateError",
    "OpenFoamCavityConfig",
    "OpenFoamCavityTemplateAdapter",
    "OpenFoamGeneratedCase",
    "generate_cavity_case",
]
