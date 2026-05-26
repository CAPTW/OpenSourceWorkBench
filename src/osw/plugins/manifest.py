"""Plugin manifest contract for OSW add-ins."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from .errors import PluginDiagnostic, PluginDiagnosticSeverity, PluginValidationError

PLUGIN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
REQUIRED_FIELDS = (
    "id",
    "name",
    "version",
    "domain",
    "type",
    "license",
    "capabilities",
)
KNOWN_FIELDS = {
    *REQUIRED_FIELDS,
    "description",
    "author",
    "homepage",
    "input_formats",
    "output_formats",
    "requires",
    "optional_requires",
    "executable_names",
    "entry_point",
    "min_osw_version",
    "max_osw_version",
    "ui_panels",
    "example_projects",
    "tags",
    "metadata",
}


class PluginManifestError(PluginValidationError):
    """Raised when plugin manifest data is missing or invalid."""


class PluginType(StrEnum):
    CAD_IMPORTER = "cad_importer"
    MESH_IMPORTER = "mesh_importer"
    MESH_GENERATOR = "mesh_generator"
    SOLVER_ADAPTER = "solver_adapter"
    SCRIPT_IMPORTER = "script_importer"
    PROPERTY_MODEL = "property_model"
    POST_PROCESSOR = "post_processor"
    REPORT_PLUGIN = "report_plugin"
    REPORT = "report_plugin"
    UI_EXTENSION = "ui_extension"
    UNKNOWN = "unknown"


class PluginDomain(StrEnum):
    CAE = "CAE"
    CFD = "CFD"
    CHM = "CHM"
    MATH = "MATH"
    GEOMETRY = "GEOMETRY"
    MESH = "MESH"
    REPORT = "REPORT"
    GENERAL = "GENERAL"


LEGACY_DOMAIN_MAP = {
    "geometry": PluginDomain.GEOMETRY.value,
    "mesh": PluginDomain.MESH.value,
    "solver": PluginDomain.CAE.value,
    "script": PluginDomain.MATH.value,
    "property": PluginDomain.CHM.value,
    "post": PluginDomain.GENERAL.value,
    "report": PluginDomain.REPORT.value,
    "general": PluginDomain.GENERAL.value,
}


@dataclass(frozen=True)
class PluginManifest:
    id: str
    name: str
    version: str
    domain: str
    type: PluginType
    license: str
    capabilities: tuple[str, ...]
    description: str = ""
    author: str = ""
    homepage: str = ""
    input_formats: tuple[str, ...] = field(default_factory=tuple)
    output_formats: tuple[str, ...] = field(default_factory=tuple)
    requires: tuple[str, ...] = field(default_factory=tuple)
    optional_requires: tuple[str, ...] = field(default_factory=tuple)
    executable_names: tuple[str, ...] = field(default_factory=tuple)
    entry_point: str = ""
    min_osw_version: str = ""
    max_osw_version: str = ""
    ui_panels: tuple[str, ...] = field(default_factory=tuple)
    example_projects: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "type": self.type.value,
            "license": self.license,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "input_formats": list(self.input_formats),
            "output_formats": list(self.output_formats),
            "requires": list(self.requires),
            "optional_requires": list(self.optional_requires),
            "executable_names": list(self.executable_names),
            "entry_point": self.entry_point,
            "min_osw_version": self.min_osw_version,
            "max_osw_version": self.max_osw_version,
            "ui_panels": list(self.ui_panels),
            "example_projects": list(self.example_projects),
            "tags": list(self.tags),
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }

    def supports_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def validate(self) -> tuple[PluginDiagnostic, ...]:
        return validate_manifest_data(self.to_dict())

    @classmethod
    def from_dict(cls, data: object) -> PluginManifest:
        diagnostics = validate_manifest_data(data)
        errors = [
            diagnostic
            for diagnostic in diagnostics
            if diagnostic.severity is PluginDiagnosticSeverity.ERROR
        ]
        if errors:
            message = "; ".join(error.message for error in errors)
            raise PluginManifestError(message, tuple(diagnostics))

        if not isinstance(data, dict):
            raise PluginManifestError("Plugin manifest must be a mapping.", tuple(diagnostics))

        metadata = dict(data.get("metadata", {}) or {})
        unknown_fields = {
            key: value for key, value in data.items() if key not in KNOWN_FIELDS
        }
        metadata.update(
            {key: value for key, value in unknown_fields.items() if key not in metadata}
        )

        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            version=str(data["version"]),
            domain=_normalize_domain(str(data["domain"])),
            type=_normalize_plugin_type(str(data["type"])),
            license=str(data["license"]),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            homepage=str(data.get("homepage", "")),
            input_formats=_string_tuple(data.get("input_formats", []), "input_formats"),
            output_formats=_string_tuple(data.get("output_formats", []), "output_formats"),
            requires=_string_tuple(data.get("requires", []), "requires"),
            optional_requires=_string_tuple(
                data.get("optional_requires", []),
                "optional_requires",
            ),
            executable_names=_string_tuple(data.get("executable_names", []), "executable_names"),
            entry_point=str(data.get("entry_point", "")),
            min_osw_version=str(data.get("min_osw_version", "")),
            max_osw_version=str(data.get("max_osw_version", "")),
            ui_panels=_string_tuple(data.get("ui_panels", []), "ui_panels"),
            example_projects=_string_tuple(data.get("example_projects", []), "example_projects"),
            tags=_string_tuple(data.get("tags", []), "tags"),
            capabilities=_string_tuple(data.get("capabilities", []), "capabilities"),
            metadata=metadata,
        )

    @classmethod
    def load(cls, path: str | Path) -> PluginManifest:
        source = Path(path)
        try:
            text = source.read_text(encoding="utf-8")
            data = _loads_by_suffix(source, text)
        except PluginManifestError:
            raise
        except Exception as exc:
            msg = f"Could not parse plugin manifest {source}: {exc}"
            raise PluginManifestError(msg) from exc
        return cls.from_dict(data)


def validate_manifest_data(data: object, *, source: str = "") -> tuple[PluginDiagnostic, ...]:
    diagnostics: list[PluginDiagnostic] = []
    if not isinstance(data, dict):
        return (
            PluginDiagnostic.error(
                "invalid-manifest-shape",
                "Plugin manifest must be a mapping.",
                source=source,
            ),
        )

    missing = [
        field_name
        for field_name in REQUIRED_FIELDS
        if field_name not in data or data[field_name] in (None, "", [])
    ]
    for field_name in missing:
        diagnostics.append(
            PluginDiagnostic.error(
                "missing-required-field",
                f"Plugin manifest missing required field: {field_name}",
                field=field_name,
                source=source,
            )
        )

    plugin_id = str(data.get("id", ""))
    if plugin_id and not PLUGIN_ID_PATTERN.match(plugin_id):
        diagnostics.append(
            PluginDiagnostic.error(
                "invalid-plugin-id",
                f"Plugin id must be lowercase dotted text, got: {plugin_id}",
                field="id",
                source=source,
            )
        )

    if data.get("type") not in (None, ""):
        try:
            _normalize_plugin_type(str(data["type"]))
        except PluginManifestError:
            diagnostics.append(
                PluginDiagnostic.error(
                    "invalid-plugin-type",
                    f"Plugin manifest has unsupported plugin type: {data['type']}",
                    field="type",
                    source=source,
                )
            )

    if data.get("domain") not in (None, ""):
        try:
            _normalize_domain(str(data["domain"]))
        except PluginManifestError:
            allowed = ", ".join(item.value for item in PluginDomain)
            diagnostics.append(
                PluginDiagnostic.error(
                    "invalid-plugin-domain",
                    "Plugin manifest has unsupported domain "
                    f"{data['domain']!r}; expected one of: {allowed}",
                    field="domain",
                    source=source,
                )
            )

    for field_name in (
        "capabilities",
        "input_formats",
        "output_formats",
        "requires",
        "optional_requires",
        "executable_names",
        "ui_panels",
        "example_projects",
        "tags",
    ):
        if field_name in data and data[field_name] is not None and not isinstance(
            data[field_name],
            list | tuple,
        ):
            diagnostics.append(
                PluginDiagnostic.error(
                    "invalid-list-field",
                    f"Plugin manifest field {field_name} must be a list.",
                    field=field_name,
                    source=source,
                )
            )

    for field_name in sorted(set(data) - KNOWN_FIELDS):
        diagnostics.append(
            PluginDiagnostic.warning(
                "unknown-manifest-field",
                f"Unknown plugin manifest field preserved in metadata: {field_name}",
                field=field_name,
                source=source,
            )
        )
    return tuple(diagnostics)


def _normalize_plugin_type(value: str) -> PluginType:
    normalized = value.strip()
    if normalized == "report":
        normalized = PluginType.REPORT_PLUGIN.value
    try:
        return PluginType(normalized)
    except ValueError as exc:
        raise PluginManifestError(f"Plugin manifest has unsupported plugin type: {value}") from exc


def _normalize_domain(value: str) -> str:
    stripped = value.strip()
    if stripped in LEGACY_DOMAIN_MAP:
        return LEGACY_DOMAIN_MAP[stripped]
    upper = stripped.upper()
    try:
        return PluginDomain(upper).value
    except ValueError as exc:
        raise PluginManifestError(f"Plugin manifest has unsupported domain: {value}") from exc


def _string_tuple(data: object, field_name: str) -> tuple[str, ...]:
    if data is None:
        return ()
    if not isinstance(data, list | tuple):
        msg = f"Plugin manifest field {field_name} must be a list."
        raise PluginManifestError(msg)
    return tuple(str(item) for item in data)


def _loads_by_suffix(path: Path, text: str) -> Any:
    if path.suffix.lower() == ".json":
        return json.loads(text)

    try:
        import yaml
    except ModuleNotFoundError as exc:
        msg = (
            "YAML plugin manifest support requires optional PyYAML. "
            "Use JSON manifests or install PyYAML."
        )
        raise PluginManifestError(
            msg,
            (
                PluginDiagnostic.error(
                    "yaml-unavailable",
                    msg,
                    hint="Install PyYAML or use a JSON plugin manifest.",
                    source=str(path),
                ),
            ),
        ) from exc
    return yaml.safe_load(text)
