"""Base plugin contracts for OSW add-ins.

These contracts define method surfaces only. OSW-FUNC-002 intentionally does
not provide concrete importer, solver, script, post-processing, or report
behavior.
"""

from __future__ import annotations

from pathlib import Path
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
    def name(self) -> str:
        return self.manifest.name

    @property
    def version(self) -> str:
        return self.manifest.version

    @property
    def domain(self) -> str:
        return self.manifest.domain

    @property
    def plugin_type(self) -> str:
        return self.manifest.type.value

    @property
    def capabilities(self) -> tuple[str, ...]:
        return self.manifest.capabilities

    def health(self) -> PluginHealth:
        return self.validate_environment()

    def validate_environment(self) -> PluginHealth:
        return check_manifest_health(self.manifest)

    def describe(self) -> dict[str, Any]:
        return self.manifest.to_dict()

    def register(self, registry: Any) -> None:
        registry.register_plugin(self)


class CADImporterPlugin(WorkbenchPlugin):
    expected_type = PluginType.CAD_IMPORTER
    supported_extensions: ClassVar[tuple[str, ...]] = ()

    def can_read(self, path: str | Path) -> bool:
        return Path(path).suffix.lower().lstrip(".") in self.supported_extensions

    def read(self, path: str | Path) -> Any:
        raise NotImplementedError


class MeshImporterPlugin(WorkbenchPlugin):
    expected_type = PluginType.MESH_IMPORTER
    supported_extensions: ClassVar[tuple[str, ...]] = ()

    def can_read(self, path: str | Path) -> bool:
        return Path(path).suffix.lower().lstrip(".") in self.supported_extensions

    def read(self, path: str | Path) -> Any:
        raise NotImplementedError


class MeshGeneratorPlugin(WorkbenchPlugin):
    expected_type = PluginType.MESH_GENERATOR
    supported_geometry_types: ClassVar[tuple[str, ...]] = ()

    def generate_mesh(
        self,
        project: Any,
        output_dir: str | Path,
        settings: dict[str, Any],
    ) -> Any:
        raise NotImplementedError


class SolverAdapterPlugin(WorkbenchPlugin):
    expected_type = PluginType.SOLVER_ADAPTER
    supported_problem_types: ClassVar[tuple[str, ...]] = ()

    def validate(self, project: Any) -> Any:
        raise NotImplementedError

    def generate_case(self, project: Any, case_dir: str | Path) -> Any:
        raise NotImplementedError

    def run(self, case_dir: str | Path, runner: Any) -> Any:
        raise NotImplementedError

    def parse_results(self, case_dir: str | Path) -> Any:
        raise NotImplementedError

    def prepare_case(self, parameters: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class ScriptImporterPlugin(WorkbenchPlugin):
    expected_type = PluginType.SCRIPT_IMPORTER
    supported_extensions: ClassVar[tuple[str, ...]] = ()

    def preview(self, path: str | Path) -> Any:
        raise NotImplementedError

    def validate_script(self, path: str | Path) -> Any:
        raise NotImplementedError

    def import_script(self, path: str | Path) -> Any:
        raise NotImplementedError


class PropertyModelPlugin(WorkbenchPlugin):
    expected_type = PluginType.PROPERTY_MODEL
    supported_properties: ClassVar[tuple[str, ...]] = ()

    def evaluate(self, inputs: dict[str, Any]) -> Any:
        raise NotImplementedError

    def validate_inputs(self, inputs: dict[str, Any]) -> Any:
        raise NotImplementedError


class PostProcessorPlugin(WorkbenchPlugin):
    expected_type = PluginType.POST_PROCESSOR
    supported_result_formats: ClassVar[tuple[str, ...]] = ()

    def can_read(self, path: str | Path) -> bool:
        return Path(path).suffix.lower().lstrip(".") in self.supported_result_formats

    def read(self, path: str | Path) -> Any:
        raise NotImplementedError

    def to_result_dataset(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class ReportPlugin(WorkbenchPlugin):
    expected_type = PluginType.REPORT_PLUGIN
    supported_export_formats: ClassVar[tuple[str, ...]] = ()

    def generate_report(
        self,
        project: Any,
        output_path: str | Path,
        options: dict[str, Any],
    ) -> Any:
        raise NotImplementedError
