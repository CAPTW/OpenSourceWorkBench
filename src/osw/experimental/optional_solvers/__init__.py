"""Declarative optional solver manifest and passive discovery helpers.

The optional solver schema layer is metadata-only. It does not implement
CLI commands, GUI panels, plugin loading, dependency installation, or solver
execution. Passive discovery records presence evidence only.
"""

from .builtin_manifests import (
    builtin_optional_solver_manifests,
    get_builtin_optional_solver_manifest,
)
from .discovery_models import (
    OptionalSolverDiscoveryDiagnostic,
    OptionalSolverDiscoveryOptions,
    OptionalSolverDiscoveryReport,
    OptionalSolverEnvironmentHintDiscovery,
    OptionalSolverExecutableDiscovery,
    OptionalSolverPathRedactionMode,
    OptionalSolverPythonPackageDiscovery,
    OptionalSolverStackDiscovery,
    optional_solver_discovery_report_from_dict,
    optional_solver_discovery_report_to_dict,
)
from .discovery_service import (
    discover_builtin_optional_solvers,
    discover_optional_solver_manifests,
    discover_optional_solver_stack,
    explain_optional_solver_discovery,
)
from .gui_health_viewmodel import (
    OptionalSolverDiagnosticRowViewModel,
    OptionalSolverGuidanceRowViewModel,
    OptionalSolverHealthPanelAction,
    OptionalSolverHealthPanelActionState,
    OptionalSolverHealthPanelViewModel,
    OptionalSolverHealthSummaryViewModel,
    OptionalSolverRequirementRowViewModel,
    OptionalSolverStackCardViewModel,
    OptionalSolverStackDetailsViewModel,
    OptionalSolverValidationHistoryRowViewModel,
    build_optional_solver_health_panel_viewmodel,
    build_optional_solver_stack_card_viewmodel,
    explain_optional_solver_health_panel,
    summarize_optional_solver_health_panel,
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
    "OptionalSolverDiscoveryDiagnostic",
    "OptionalSolverDiscoveryOptions",
    "OptionalSolverDiscoveryReport",
    "OptionalSolverEnvironmentHintDiscovery",
    "OptionalSolverExecutableDiscovery",
    "OptionalSolverDiagnosticRowViewModel",
    "OptionalSolverGuidanceRowViewModel",
    "OptionalSolverHealthState",
    "OptionalSolverHealthPanelAction",
    "OptionalSolverHealthPanelActionState",
    "OptionalSolverHealthPanelViewModel",
    "OptionalSolverHealthSummaryViewModel",
    "OptionalSolverManifest",
    "OptionalSolverManifestDiagnostic",
    "OptionalSolverManifestValidationReport",
    "OptionalSolverPathRedactionMode",
    "OptionalSolverProbe",
    "OptionalSolverPythonPackageDiscovery",
    "OptionalSolverRequirementRowViewModel",
    "OptionalSolverRequirement",
    "OptionalSolverStackDiscovery",
    "OptionalSolverStackCardViewModel",
    "OptionalSolverStackDetailsViewModel",
    "OptionalSolverStackId",
    "OptionalSolverSupportStatus",
    "OptionalSolverValidationHistoryRowViewModel",
    "build_optional_solver_health_panel_viewmodel",
    "build_optional_solver_stack_card_viewmodel",
    "builtin_optional_solver_manifests",
    "discover_builtin_optional_solvers",
    "discover_optional_solver_manifests",
    "discover_optional_solver_stack",
    "dump_optional_solver_manifest_json",
    "explain_optional_solver_health_panel",
    "explain_optional_solver_discovery",
    "explain_optional_solver_manifest",
    "get_builtin_optional_solver_manifest",
    "load_optional_solver_manifest_json",
    "optional_solver_discovery_report_from_dict",
    "optional_solver_discovery_report_to_dict",
    "parse_optional_solver_manifest_dict",
    "summarize_optional_solver_health_panel",
    "validate_optional_solver_manifest",
]
