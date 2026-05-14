"""SolverAdapterPlugin wrapper for prepare-only SU2 case configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.manifest import PluginManifest

from .config import Su2ConfigGenerator, Su2SimulationConfig


class Su2BasicAdapter(SolverAdapterPlugin):
    """Prepare a basic SU2 configuration without launching SU2."""

    manifest: ClassVar[PluginManifest] = PluginManifest.from_dict(
        {
            "id": "osw.solvers.su2.basic",
            "name": "SU2 Basic Adapter",
            "version": "0.1.0",
            "domain": "solver",
            "type": "solver_adapter",
            "license": "GPL-3.0-or-later",
            "input_formats": ["su2.mesh_reference", ".su2"],
            "output_formats": ["su2.cfg"],
            "requires": [],
            "optional_requires": ["SU2_CFD"],
            "capabilities": ["validate", "prepare_case", "cfg_generator", "dry_run"],
        }
    )

    def __init__(self, generator: Su2ConfigGenerator | None = None) -> None:
        self.generator = generator
        super().__init__()

    def validate(self, case: Su2SimulationConfig) -> tuple[str, ...]:
        if not isinstance(case, Su2SimulationConfig):
            msg = "SU2 validation requires a Su2SimulationConfig."
            raise TypeError(msg)
        return tuple(Su2ConfigGenerator(case).validate())

    def prepare_case(self, parameters: dict[str, Any]) -> dict[str, Any]:
        case = parameters.get("case")
        if not isinstance(case, Su2SimulationConfig):
            msg = "SU2 prepare_case requires a Su2SimulationConfig in parameters['case']."
            raise TypeError(msg)

        output_dir = Path(parameters.get("output_dir", "."))
        generator = self.generator or Su2ConfigGenerator(case)
        if generator.config != case:
            generator = Su2ConfigGenerator(case)
        generated = generator.write(output_dir)

        return {
            "solver": "SU2",
            "adapter_id": self.id,
            "case_id": case.case_name,
            "execution_mode": "prepare_only",
            "config_path": str(generated.path),
            "mesh_reference": generated.mesh_reference,
            "run_command_preview": ["SU2_CFD", generated.path.name],
            "validation": self.validate(case),
            "warnings": list(generated.warnings),
            "limitations": [
                "OSW v0.1 prepares a basic SU2 config for review and external use.",
                "This adapter does not provide a broad SU2 workflow or GUI controls.",
            ],
        }
