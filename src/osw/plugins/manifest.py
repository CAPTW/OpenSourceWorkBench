"""Plugin manifest contract for OSW add-ins."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

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
ALLOWED_DOMAINS = {
    "geometry",
    "mesh",
    "solver",
    "script",
    "property",
    "post",
    "report",
    "general",
}


class PluginManifestError(ValueError):
    """Raised when plugin manifest data is missing or invalid."""


class PluginType(StrEnum):
    CAD_IMPORTER = "cad_importer"
    MESH_IMPORTER = "mesh_importer"
    MESH_GENERATOR = "mesh_generator"
    SOLVER_ADAPTER = "solver_adapter"
    SCRIPT_IMPORTER = "script_importer"
    PROPERTY_MODEL = "property_model"
    POST_PROCESSOR = "post_processor"
    REPORT = "report"


@dataclass(frozen=True)
class PluginManifest:
    id: str
    name: str
    version: str
    domain: str
    type: PluginType
    license: str
    input_formats: tuple[str, ...] = field(default_factory=tuple)
    output_formats: tuple[str, ...] = field(default_factory=tuple)
    requires: tuple[str, ...] = field(default_factory=tuple)
    optional_requires: tuple[str, ...] = field(default_factory=tuple)
    capabilities: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "type": self.type.value,
            "license": self.license,
            "input_formats": list(self.input_formats),
            "output_formats": list(self.output_formats),
            "requires": list(self.requires),
            "optional_requires": list(self.optional_requires),
            "capabilities": list(self.capabilities),
        }

    def supports_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    @classmethod
    def from_dict(cls, data: object) -> PluginManifest:
        if not isinstance(data, dict):
            msg = "Plugin manifest must be a mapping."
            raise PluginManifestError(msg)

        for field_name in REQUIRED_FIELDS:
            if field_name not in data or data[field_name] in (None, "", []):
                raise PluginManifestError(f"Plugin manifest missing required field: {field_name}")

        plugin_id = str(data["id"])
        if not PLUGIN_ID_PATTERN.match(plugin_id):
            msg = f"Plugin id must be lowercase dotted text, got: {plugin_id}"
            raise PluginManifestError(msg)

        domain = str(data["domain"])
        if domain not in ALLOWED_DOMAINS:
            allowed = ", ".join(sorted(ALLOWED_DOMAINS))
            msg = f"Plugin manifest has unsupported domain {domain!r}; expected one of: {allowed}"
            raise PluginManifestError(msg)

        try:
            plugin_type = PluginType(str(data["type"]))
        except ValueError as exc:
            msg = f"Plugin manifest has unsupported plugin type: {data['type']}"
            raise PluginManifestError(msg) from exc

        return cls(
            id=plugin_id,
            name=str(data["name"]),
            version=str(data["version"]),
            domain=domain,
            type=plugin_type,
            license=str(data["license"]),
            input_formats=_string_tuple(data.get("input_formats", []), "input_formats"),
            output_formats=_string_tuple(data.get("output_formats", []), "output_formats"),
            requires=_string_tuple(data.get("requires", []), "requires"),
            optional_requires=_string_tuple(
                data.get("optional_requires", []),
                "optional_requires",
            ),
            capabilities=_string_tuple(data.get("capabilities", []), "capabilities"),
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
    except ModuleNotFoundError:
        return json.loads(text)
    return yaml.safe_load(text)
