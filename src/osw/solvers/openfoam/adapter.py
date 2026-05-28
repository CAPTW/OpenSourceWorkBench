"""SolverAdapterPlugin wrapper for prepare-only OpenFOAM cavity templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.manifest import PluginManifest

from .case_generator import (
    OpenFoamCaseGenerator,
    OpenFoamCavityConfig,
    OpenFoamDuctCaseGenerator,
    OpenFoamDuctConfig,
    default_cavity_request,
    default_duct_request,
)
from .model import OpenFOAMCaseRequest, OpenFOAMTemplateKind


class OpenFoamCavityTemplateAdapter(SolverAdapterPlugin):
    """Prepare a lid-driven cavity case directory without launching OpenFOAM."""

    manifest: ClassVar[PluginManifest] = PluginManifest.from_dict(
        {
            "id": "osw.solvers.openfoam.cavity_template",
            "name": "OpenFOAM Cavity Template Adapter",
            "version": "0.1.0",
            "domain": "solver",
            "type": "solver_adapter",
            "license": "GPL-3.0-or-later",
            "input_formats": ["osw.project.cfd_template"],
            "output_formats": ["openfoam.case_directory"],
            "requires": [],
            "optional_requires": [],
            "capabilities": ["validate", "prepare_case", "cavity_template", "dry_run"],
        }
    )

    def __init__(self, generator: OpenFoamCaseGenerator | None = None) -> None:
        self.generator = generator or OpenFoamCaseGenerator()
        super().__init__()

    def prepare_case(self, parameters: dict[str, Any]) -> dict[str, Any]:
        case = parameters.get("case")
        if not isinstance(case, OpenFoamCavityConfig):
            msg = "OpenFOAM prepare_case requires an OpenFoamCavityConfig in parameters['case']."
            raise TypeError(msg)

        output_dir = Path(parameters.get("output_dir", "."))
        generated = self.generator.generate(case, output_dir)

        return {
            "solver": "OpenFOAM",
            "adapter_id": self.id,
            "case_id": case.case_name,
            "execution_mode": "prepare_only",
            "case_dir": str(generated.root),
            "files": list(generated.relative_paths),
            "run_command_preview": ["blockMesh", "icoFoam"],
            "validation": self.generator.validate(case).friendly_summary(),
            "warnings": list(generated.warnings),
            "limitations": [
                "OSW v0.1 prepares a cavity template for review and external use.",
                "This adapter does not execute OpenFOAM or manage arbitrary OpenFOAM cases.",
            ],
        }


class OpenFoamDuctTemplateAdapter(SolverAdapterPlugin):
    """Prepare an internal duct flow case directory without launching OpenFOAM."""

    manifest: ClassVar[PluginManifest] = PluginManifest.from_dict(
        {
            "id": "osw.solvers.openfoam.duct_template",
            "name": "OpenFOAM Duct Template Adapter",
            "version": "0.1.0",
            "domain": "solver",
            "type": "solver_adapter",
            "license": "GPL-3.0-or-later",
            "input_formats": ["osw.project.cfd_template"],
            "output_formats": ["openfoam.case_directory"],
            "requires": [],
            "optional_requires": [],
            "capabilities": ["validate", "prepare_case", "duct_template", "dry_run"],
        }
    )

    def __init__(self, generator: OpenFoamDuctCaseGenerator | None = None) -> None:
        self.generator = generator or OpenFoamDuctCaseGenerator()
        super().__init__()

    def prepare_case(self, parameters: dict[str, Any]) -> dict[str, Any]:
        case = parameters.get("case")
        if not isinstance(case, OpenFoamDuctConfig):
            msg = "OpenFOAM prepare_case requires an OpenFoamDuctConfig in parameters['case']."
            raise TypeError(msg)

        output_dir = Path(parameters.get("output_dir", "."))
        generated = self.generator.generate(case, output_dir)

        return {
            "solver": "OpenFOAM",
            "adapter_id": self.id,
            "case_id": case.case_name,
            "execution_mode": "prepare_only",
            "case_dir": str(generated.root),
            "files": list(generated.relative_paths),
            "run_command_preview": ["blockMesh", str(case.solver)],
            "validation": self.generator.validate(case).friendly_summary(),
            "warnings": list(generated.warnings),
            "limitations": [
                "OSW v0.1 prepares a duct template for review and external use.",
                "This adapter does not execute OpenFOAM or manage arbitrary OpenFOAM cases.",
            ],
        }


def openfoam_case_request_from_project(
    project: object,
    *,
    output_dir: str | Path,
) -> OpenFOAMCaseRequest:
    """Create a bounded OpenFOAM template request from explicit solver metadata."""

    for solver in getattr(project, "solvers", ()) or ():
        solver_name = str(getattr(solver, "solver", "") or getattr(solver, "name", ""))
        parameters = dict(getattr(solver, "parameters", {}) or {})
        settings = dict(getattr(solver, "settings", {}) or {})
        metadata = {**settings, **parameters}
        template = str(metadata.get("openfoam_template", metadata.get("template", ""))).lower()
        if "openfoam" not in solver_name.lower() and template not in {
            OpenFOAMTemplateKind.CAVITY.value,
            OpenFOAMTemplateKind.DUCT.value,
        }:
            continue
        if template == OpenFOAMTemplateKind.DUCT.value:
            return default_duct_request(
                output_dir,
                inlet_velocity=float(metadata.get("inlet_velocity", 1.0)),
                outlet_pressure=float(metadata.get("outlet_pressure", 0.0)),
            )
        if template == OpenFOAMTemplateKind.CAVITY.value:
            return default_cavity_request(output_dir)
    return default_cavity_request(output_dir)
