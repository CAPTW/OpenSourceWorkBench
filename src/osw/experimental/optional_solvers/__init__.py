"""Declarative optional solver manifest schema models.

The optional solver schema layer is metadata-only. It does not implement
discovery, CLI commands, GUI panels, plugin loading, dependency installation,
or solver execution.
"""

from .builtin_manifests import (
    builtin_optional_solver_manifests,
    get_builtin_optional_solver_manifest,
)
from .manifest_io import (
    dump_optional_solver_manifest_json,
    load_optional_solver_manifest_json,
)
from .manifest_models import (
    OptionalSolverCapability,
    OptionalSolverHealthState,
    OptionalSolverManifest,
    OptionalSolverProbe,
    OptionalSolverRequirement,
    OptionalSolverStackId,
    OptionalSolverSupportStatus,
    explain_optional_solver_manifest,
    parse_optional_solver_manifest_dict,
)
from .manifest_validation import (
    OptionalSolverDiagnosticSeverity,
    OptionalSolverManifestDiagnostic,
    OptionalSolverManifestValidationReport,
    validate_optional_solver_manifest,
)

__all__ = [
    "OptionalSolverCapability",
    "OptionalSolverDiagnosticSeverity",
    "OptionalSolverHealthState",
    "OptionalSolverManifest",
    "OptionalSolverManifestDiagnostic",
    "OptionalSolverManifestValidationReport",
    "OptionalSolverProbe",
    "OptionalSolverRequirement",
    "OptionalSolverStackId",
    "OptionalSolverSupportStatus",
    "builtin_optional_solver_manifests",
    "dump_optional_solver_manifest_json",
    "explain_optional_solver_manifest",
    "get_builtin_optional_solver_manifest",
    "load_optional_solver_manifest_json",
    "parse_optional_solver_manifest_dict",
    "validate_optional_solver_manifest",
]
