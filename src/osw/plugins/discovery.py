"""Plugin manifest discovery for local directories and Python entry points."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any

from .manifest import PluginManifest, PluginManifestError

DEFAULT_ENTRY_POINT_GROUP = "osw.plugins"
MANIFEST_FILENAMES = {
    "osw-plugin.json",
    "osw-plugin.yaml",
    "osw-plugin.yml",
    "plugin.json",
    "plugin.yaml",
    "plugin.yml",
}
MANIFEST_SUFFIXES = (".manifest.json", ".manifest.yaml", ".manifest.yml")


class PluginDiscoveryError(RuntimeError):
    """Raised when plugin discovery cannot continue safely."""


class DuplicatePluginIdError(PluginDiscoveryError):
    """Raised when two discovered manifests declare the same plugin id."""


@dataclass
class PluginRegistry:
    _manifests: dict[str, PluginManifest] = field(default_factory=dict)

    def add(self, manifest: PluginManifest) -> None:
        if manifest.id in self._manifests:
            raise DuplicatePluginIdError(f"Duplicate plugin id: {manifest.id}")
        self._manifests[manifest.id] = manifest

    def extend(self, manifests: Iterable[PluginManifest]) -> None:
        for manifest in manifests:
            self.add(manifest)

    def get(self, plugin_id: str) -> PluginManifest:
        return self._manifests[plugin_id]

    def values(self) -> tuple[PluginManifest, ...]:
        return tuple(self._manifests.values())

    def __iter__(self) -> Iterator[PluginManifest]:
        return iter(self.values())

    def __len__(self) -> int:
        return len(self._manifests)


def discover_local_plugins(path: str | Path | Iterable[str | Path]) -> PluginRegistry:
    registry = PluginRegistry()
    for root in _roots(path):
        for manifest_path in iter_manifest_paths(root):
            try:
                registry.add(PluginManifest.load(manifest_path))
            except DuplicatePluginIdError:
                raise
            except PluginManifestError as exc:
                msg = f"Invalid plugin manifest {manifest_path}: {exc}"
                raise PluginDiscoveryError(msg) from exc
    return registry


def iter_manifest_paths(root: str | Path) -> Iterator[Path]:
    root_path = Path(root)
    if not root_path.exists():
        return

    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue
        if path.name in MANIFEST_FILENAMES or path.name.endswith(MANIFEST_SUFFIXES):
            yield path


def discover_entry_point_plugins(
    group: str = DEFAULT_ENTRY_POINT_GROUP,
) -> PluginRegistry:
    registry = PluginRegistry()
    for entry_point in _entry_points(group):
        manifest = _manifest_from_entry_point(entry_point)
        registry.add(manifest)
    return registry


def discover_plugins(
    *,
    local_paths: Iterable[str | Path] = (),
    include_entry_points: bool = True,
    entry_point_group: str = DEFAULT_ENTRY_POINT_GROUP,
) -> PluginRegistry:
    registry = PluginRegistry()
    registry.extend(discover_local_plugins(local_paths).values())
    if include_entry_points:
        registry.extend(discover_entry_point_plugins(entry_point_group).values())
    return registry


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


def _manifest_from_entry_point(entry_point: Any) -> PluginManifest:
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
