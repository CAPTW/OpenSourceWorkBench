"""Plugin manifest discovery for local directories and Python entry points."""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any

from .errors import PluginDiagnostic
from .manifest import PluginManifest, PluginManifestError
from .registry import DuplicatePluginIdError, PluginRegistry

DEFAULT_ENTRY_POINT_GROUPS = ("osw.plugins", "opensolver_workbench.plugins")
DEFAULT_ENTRY_POINT_GROUP = DEFAULT_ENTRY_POINT_GROUPS[0]
MANIFEST_FILENAMES = {
    "manifest.json",
    "manifest.yaml",
    "manifest.yml",
    "plugin.json",
    "plugin.yaml",
    "plugin.yml",
    "osw-plugin.json",
    "osw-plugin.yaml",
    "osw-plugin.yml",
}
MANIFEST_SUFFIXES = (".manifest.json", ".manifest.yaml", ".manifest.yml")
OSW_PLUGINS_PATH_ENV = "OSW_PLUGINS_PATH"


class PluginDiscoveryError(RuntimeError):
    """Raised when plugin discovery cannot continue safely."""


@dataclass(frozen=True)
class PluginDiscoveryRecord:
    manifest: PluginManifest | None
    source_type: str
    source_path: str = ""
    source_name: str = ""
    diagnostics: tuple[PluginDiagnostic, ...] = field(default_factory=tuple)
    entry_point: Any | None = None


@dataclass
class PluginDiscoveryResult:
    records: list[PluginDiscoveryRecord] = field(default_factory=list)
    diagnostics: list[PluginDiagnostic] = field(default_factory=list)
    duplicate_ids: list[str] = field(default_factory=list)
    skipped_paths: list[str] = field(default_factory=list)

    @property
    def manifests(self) -> tuple[PluginManifest, ...]:
        return tuple(record.manifest for record in self.records if record.manifest is not None)

    def to_registry(self) -> PluginRegistry:
        registry = PluginRegistry()
        for record in self.records:
            if record.manifest is None:
                continue
            try:
                registry.add_manifest(
                    record.manifest,
                    source=record.source_path or record.source_name,
                )
            except DuplicatePluginIdError:
                continue
        for diagnostic in self.diagnostics:
            registry.add_diagnostic(diagnostic)
        return registry

    def get(self, plugin_id: str) -> PluginManifest:
        return self.to_registry().get(plugin_id)

    def values(self) -> tuple[PluginManifest, ...]:
        return self.manifests

    def __iter__(self) -> Iterator[PluginManifest]:
        return iter(self.manifests)

    def __len__(self) -> int:
        return len(self.manifests)


def discover_local_plugins(path: str | Path | Iterable[str | Path]) -> PluginDiscoveryResult:
    return discover_local_plugin_manifests(path, raise_on_duplicate=True)


def discover_local_plugin_manifests(
    path: str | Path | Iterable[str | Path],
    *,
    raise_on_duplicate: bool = False,
) -> PluginDiscoveryResult:
    result = PluginDiscoveryResult()
    seen: dict[str, str] = {}
    for root in _roots(path):
        if not root.exists():
            result.skipped_paths.append(str(root))
            continue
        for manifest_path in iter_manifest_paths(root):
            try:
                manifest = PluginManifest.load(manifest_path)
            except PluginManifestError as exc:
                diagnostics = tuple(getattr(exc, "diagnostics", ())) or (
                    PluginDiagnostic.error(
                        "invalid-manifest",
                        f"Invalid plugin manifest {manifest_path}: {exc}",
                        source=str(manifest_path),
                    ),
                )
                result.diagnostics.extend(diagnostics)
                result.records.append(
                    PluginDiscoveryRecord(
                        manifest=None,
                        source_type=_source_type_for(root, manifest_path),
                        source_path=str(manifest_path),
                        diagnostics=diagnostics,
                    )
                )
                continue
            if manifest.id in seen:
                result.duplicate_ids.append(manifest.id)
                diagnostic = PluginDiagnostic.error(
                    "duplicate-plugin-id",
                    f"Duplicate plugin id: {manifest.id}",
                    field="id",
                    source=str(manifest_path),
                )
                result.diagnostics.append(diagnostic)
                if raise_on_duplicate:
                    raise DuplicatePluginIdError(f"Duplicate plugin id: {manifest.id}")
            else:
                seen[manifest.id] = str(manifest_path)
            result.records.append(
                PluginDiscoveryRecord(
                    manifest=manifest,
                    source_type=_source_type_for(root, manifest_path),
                    source_path=str(manifest_path),
                )
            )
    return result


def discover_plugin_search_paths(
    explicit_paths: Iterable[str | Path] = (),
    *,
    include_project_plugins: bool = True,
    include_user_plugins: bool = True,
) -> tuple[Path, ...]:
    paths: list[Path] = [Path(path) for path in explicit_paths]
    env_value = os.environ.get(OSW_PLUGINS_PATH_ENV, "")
    if env_value:
        paths.extend(Path(item) for item in env_value.split(os.pathsep) if item)
    if include_project_plugins:
        project_plugins = Path.cwd() / "plugins"
        if project_plugins.exists():
            paths.append(project_plugins)
    if include_user_plugins:
        paths.append(user_plugin_dir())
    return tuple(dict.fromkeys(paths))


def user_plugin_dir() -> Path:
    return Path.home() / ".osw" / "plugins"


def iter_manifest_paths(root: str | Path) -> Iterator[Path]:
    root_path = Path(root)
    if not root_path.exists():
        return
    if root_path.is_file():
        if _is_manifest_path(root_path):
            yield root_path
        return

    direct_manifest = _first_direct_manifest(root_path)
    if direct_manifest is not None:
        yield direct_manifest
        return

    for child in sorted(root_path.iterdir()):
        if child.is_file() and _is_manifest_path(child):
            yield child
        elif child.is_dir():
            manifest = _first_direct_manifest(child)
            if manifest is not None:
                yield manifest


def discover_entry_points(
    groups: Iterable[str] = DEFAULT_ENTRY_POINT_GROUPS,
) -> PluginDiscoveryResult:
    result = PluginDiscoveryResult()
    for group in groups:
        for entry_point in _entry_points(group):
            result.records.append(
                PluginDiscoveryRecord(
                    manifest=None,
                    source_type="entry_point",
                    source_name=f"{group}:{getattr(entry_point, 'name', '<unknown>')}",
                    entry_point=entry_point,
                )
            )
    return result


def discover_entry_point_plugins(
    group: str = DEFAULT_ENTRY_POINT_GROUP,
) -> PluginRegistry:
    registry = PluginRegistry()
    for record in discover_entry_points((group,)).records:
        manifest = load_entry_point_plugin(record)
        registry.add_manifest(manifest, source=record.source_name)
    return registry


def load_entry_point_plugin(record_or_entry_point: PluginDiscoveryRecord | Any) -> PluginManifest:
    entry_point = (
        record_or_entry_point.entry_point
        if isinstance(record_or_entry_point, PluginDiscoveryRecord)
        else record_or_entry_point
    )
    try:
        loaded = entry_point.load()
    except Exception as exc:
        name = getattr(entry_point, "name", "<unknown>")
        raise PluginDiscoveryError(f"Could not load plugin entry point {name}: {exc}") from exc

    if isinstance(loaded, PluginManifest):
        return loaded
    if isinstance(loaded, dict):
        return PluginManifest.from_dict(loaded)

    manifest = getattr(loaded, "manifest", None)
    if isinstance(manifest, PluginManifest):
        return manifest
    msg = "Plugin entry point must load a PluginManifest, dict, or plugin with manifest."
    raise PluginDiscoveryError(msg)


def discover_plugins(
    *,
    local_paths: Iterable[str | Path] = (),
    include_entry_points: bool = True,
    entry_point_groups: Iterable[str] = DEFAULT_ENTRY_POINT_GROUPS,
) -> PluginDiscoveryResult:
    result = discover_local_plugin_manifests(local_paths)
    if include_entry_points:
        entry_points_result = discover_entry_points(entry_point_groups)
        result.records.extend(entry_points_result.records)
        result.diagnostics.extend(entry_points_result.diagnostics)
        result.skipped_paths.extend(entry_points_result.skipped_paths)
    return result


def _roots(path: str | Path | Iterable[str | Path]) -> tuple[Path, ...]:
    if isinstance(path, str | Path):
        return (Path(path),)
    return tuple(Path(item) for item in path)


def _entry_points(group: str) -> Iterable[Any]:
    try:
        return metadata.entry_points(group=group)
    except TypeError:
        entry_points = metadata.entry_points()
        if hasattr(entry_points, "select"):
            return entry_points.select(group=group)
        return entry_points.get(group, ())


def _first_direct_manifest(root: Path) -> Path | None:
    candidates = [
        child for child in root.iterdir() if child.is_file() and _is_manifest_path(child)
    ]
    return sorted(candidates)[0] if candidates else None


def _is_manifest_path(path: Path) -> bool:
    return path.name in MANIFEST_FILENAMES or path.name.endswith(MANIFEST_SUFFIXES)


def _source_type_for(root: Path, manifest_path: Path) -> str:
    return "local_manifest" if root.is_file() and root == manifest_path else "local_directory"
