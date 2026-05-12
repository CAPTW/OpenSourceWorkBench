"""Base plugin contracts for OSW add-ins."""

from __future__ import annotations

from typing import Any, ClassVar

from .health import PluginHealth, check_manifest_health
from .manifest import PluginManifest, PluginType


class PluginContractError(TypeError):
    """Raised when a plugin class violates the OSW plugin contract."""


class WorkbenchPlugin:
    """Base class for all OSW plugin implementations."""

    manifest: ClassVar[PluginManifest]
    expected_type: ClassVar[PluginType | None] = None

    def __init__(self) -> None:
        manifest = getattr(self, "manifest", None)
        if not isinstance(manifest, PluginManifest):
            msg = f"{type(self).__name__} must define a PluginManifest named 'manifest'."
            raise PluginContractError(msg)
        if self.expected_type is not None and manifest.type is not self.expected_type:
            msg = (
                f"{type(self).__name__} manifest type must be "
                f"{self.expected_type.value}, got {manifest.type.value}."
            )
            raise PluginContractError(msg)

    @property
    def id(self) -> str:
        return self.manifest.id

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self.manifest.capabilities

    def health(self) -> PluginHealth:
        return check_manifest_health(self.manifest)


class CADImporterPlugin(WorkbenchPlugin):
    expected_type = PluginType.CAD_IMPORTER

    def preview(self, path: str) -> dict[str, Any]:
        raise NotImplementedError


class MeshImporterPlugin(WorkbenchPlugin):
    expected_type = PluginType.MESH_IMPORTER

    def preview(self, path: str) -> dict[str, Any]:
        raise NotImplementedError


class MeshGeneratorPlugin(WorkbenchPlugin):
    expected_type = PluginType.MESH_GENERATOR

    def prepare(self, parameters: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class SolverAdapterPlugin(WorkbenchPlugin):
    expected_type = PluginType.SOLVER_ADAPTER

    def prepare_case(self, parameters: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class ScriptImporterPlugin(WorkbenchPlugin):
    expected_type = PluginType.SCRIPT_IMPORTER

    def preview(self, path: str) -> dict[str, Any]:
        raise NotImplementedError


class PropertyModelPlugin(WorkbenchPlugin):
    expected_type = PluginType.PROPERTY_MODEL

    def evaluate(self, parameters: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class PostProcessorPlugin(WorkbenchPlugin):
    expected_type = PluginType.POST_PROCESSOR

    def process(self, result_ref: str) -> dict[str, Any]:
        raise NotImplementedError


class ReportPlugin(WorkbenchPlugin):
    expected_type = PluginType.REPORT

    def render(self, project_path: str) -> str:
        raise NotImplementedError
