"""OpenFOAM bounded template helpers for OSW v0.1."""

from __future__ import annotations

from .adapter import OpenFoamCavityTemplateAdapter, OpenFoamDuctTemplateAdapter
from .case_generator import (
    OpenFoamBoundaryConfig,
    OpenFoamCaseGenerator,
    OpenFoamCaseTemplateError,
    OpenFoamCavityConfig,
    OpenFoamDuctCaseGenerator,
    OpenFoamDuctConfig,
    OpenFoamDuctPatchConfig,
    OpenFoamGeneratedCase,
    generate_cavity_case,
    generate_duct_case,
)
from .residuals import OpenFoamResidualParser, OpenFoamResidualPoint, OpenFoamResidualSeries

__all__ = [
    "OpenFoamBoundaryConfig",
    "OpenFoamCaseGenerator",
    "OpenFoamCaseTemplateError",
    "OpenFoamCavityConfig",
    "OpenFoamCavityTemplateAdapter",
    "OpenFoamDuctCaseGenerator",
    "OpenFoamDuctConfig",
    "OpenFoamDuctPatchConfig",
    "OpenFoamDuctTemplateAdapter",
    "OpenFoamGeneratedCase",
    "OpenFoamResidualParser",
    "OpenFoamResidualPoint",
    "OpenFoamResidualSeries",
    "generate_cavity_case",
    "generate_duct_case",
]
