"""SolverAdapterPlugin wrapper for prepare-only CalculiX linear static decks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from osw.plugins.base import SolverAdapterPlugin
from osw.plugins.manifest import PluginManifest

from .input_deck import CalculixInputDeckGenerator, CalculixLinearStaticCase


class CalculixLinearStaticAdapter(SolverAdapterPlugin):
    """Prepare CalculiX `.inp` files without launching an external solver."""

    manifest: ClassVar[PluginManifest] = PluginManifest.from_dict(
        {
            "id": "osw.solvers.calculix.linear_static",
            "name": "CalculiX Linear Static Adapter",
            "version": "0.1.0",
            "domain": "solver",
            "type": "solver_adapter",
            "license": "GPL-3.0-or-later",
            "input_formats": ["osw.mesh", "osw.project.material"],
            "output_formats": ["calculix.inp"],
            "requires": [],
            "optional_requires": [],
            "capabilities": ["validate", "prepare_case", "linear_static", "dry_run"],
        }
    )

    def __init__(self, generator: CalculixInputDeckGenerator | None = None) -> None:
        self.generator = generator or CalculixInputDeckGenerator()
        super().__init__()

    def prepare_case(self, parameters: dict[str, Any]) -> dict[str, Any]:
        case = parameters.get("case")
        if not isinstance(case, CalculixLinearStaticCase):
            msg = "CalculiX prepare_case requires a CalculixLinearStaticCase in parameters['case']."
            raise TypeError(msg)

        output_path = Path(parameters.get("output_path", f"{case.case_id}.inp"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        deck_text = self.generator.generate(case)
        output_path.write_text(deck_text, encoding="utf-8")

        return {
            "solver": "CalculiX",
            "adapter_id": self.id,
            "case_id": case.case_id,
            "execution_mode": "prepare_only",
            "input_deck_path": str(output_path),
            "run_command_preview": ["ccx", output_path.stem],
            "validation": self.generator.validate(case).friendly_summary(),
            "limitations": [
                "OSW v0.1 prepares linear static CalculiX decks only.",
                "External solver execution is intentionally outside this adapter.",
            ],
        }
