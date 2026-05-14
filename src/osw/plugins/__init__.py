"""Plugin and add-in contract package."""

from __future__ import annotations

from osw.plugins.base import (
    CADImporterPlugin,
    MeshGeneratorPlugin,
    MeshImporterPlugin,
    PluginContractError,
    PostProcessorPlugin,
    PropertyModelPlugin,
    ReportPlugin,
    ScriptImporterPlugin,
    SolverAdapterPlugin,
    WorkbenchPlugin,
)
from osw.plugins.discovery import (
    DuplicatePluginIdError,
    PluginDiscoveryError,
    PluginRegistry,
    discover_entry_point_plugins,
    discover_local_plugins,
    discover_plugins,
)
from osw.plugins.health import PluginHealth, PluginHealthStatus, check_manifest_health
from osw.plugins.installer import (
    DuplicatePluginInstallError,
    PluginInstallError,
    PluginInstallManager,
    PluginInstallResult,
    PluginValidationResult,
    ZipPathTraversalError,
)
from osw.plugins.manifest import PluginManifest, PluginManifestError, PluginType

__all__ = [
    "CADImporterPlugin",
    "DuplicatePluginIdError",
    "DuplicatePluginInstallError",
    "MeshGeneratorPlugin",
    "MeshImporterPlugin",
    "PluginContractError",
    "PluginDiscoveryError",
    "PluginHealth",
    "PluginHealthStatus",
    "PluginInstallError",
    "PluginInstallManager",
    "PluginInstallResult",
    "PluginManifest",
    "PluginManifestError",
    "PluginRegistry",
    "PluginType",
    "PluginValidationResult",
    "PostProcessorPlugin",
    "PropertyModelPlugin",
    "ReportPlugin",
    "ScriptImporterPlugin",
    "SolverAdapterPlugin",
    "WorkbenchPlugin",
    "ZipPathTraversalError",
    "check_manifest_health",
    "discover_entry_point_plugins",
    "discover_local_plugins",
    "discover_plugins",
]
