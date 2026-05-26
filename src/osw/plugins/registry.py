"""In-memory plugin manifest and implementation registry."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any

from .errors import PluginDiagnostic
from .manifest import PluginManifest


class DuplicatePluginIdError(RuntimeError):
    """Raised when two plugin records declare the same id."""


@dataclass(frozen=True)
class PluginRegistryEntry:
    plugin_id: str
    manifest: PluginManifest | None = None
    plugin: Any | None = None
    source: str = ""


@dataclass
class PluginRegistry:
    _entries: dict[str, PluginRegistryEntry] = field(default_factory=dict)
    _diagnostics: list[PluginDiagnostic] = field(default_factory=list)
    _duplicate_ids: list[str] = field(default_factory=list)

    def add(self, manifest: PluginManifest, source: str = "") -> None:
        self.add_manifest(manifest, source=source)

    def add_manifest(self, manifest: PluginManifest, source: str = "") -> None:
        if manifest.id in self._entries:
            self._duplicate_ids.append(manifest.id)
            self.add_diagnostic(
                PluginDiagnostic.error(
                    "duplicate-plugin-id",
                    f"Duplicate plugin id: {manifest.id}",
                    field="id",
                    source=source,
                )
            )
            raise DuplicatePluginIdError(f"Duplicate plugin id: {manifest.id}")
        self._entries[manifest.id] = PluginRegistryEntry(
            plugin_id=manifest.id,
            manifest=manifest,
            source=source,
        )

    def register_plugin(self, plugin: Any, source: str = "") -> None:
        manifest = getattr(plugin, "manifest", None)
        if not isinstance(manifest, PluginManifest):
            msg = f"Plugin implementation must expose PluginManifest: {plugin!r}"
            raise TypeError(msg)
        if manifest.id in self._entries:
            self._duplicate_ids.append(manifest.id)
            self.add_diagnostic(
                PluginDiagnostic.error(
                    "duplicate-plugin-id",
                    f"Duplicate plugin id: {manifest.id}",
                    field="id",
                    source=source,
                )
            )
            raise DuplicatePluginIdError(f"Duplicate plugin id: {manifest.id}")
        self._entries[manifest.id] = PluginRegistryEntry(
            plugin_id=manifest.id,
            manifest=manifest,
            plugin=plugin,
            source=source,
        )

    def extend(self, manifests: Iterable[PluginManifest]) -> None:
        for manifest in manifests:
            self.add_manifest(manifest)

    def get(self, plugin_id: str) -> PluginManifest:
        entry = self._entries[plugin_id]
        if entry.manifest is None:
            raise KeyError(plugin_id)
        return entry.manifest

    def get_entry(self, plugin_id: str) -> PluginRegistryEntry:
        return self._entries[plugin_id]

    def list(self) -> tuple[PluginManifest, ...]:
        return self.values()

    def values(self) -> tuple[PluginManifest, ...]:
        return tuple(
            entry.manifest for entry in self._entries.values() if entry.manifest is not None
        )

    def by_type(self, plugin_type: str) -> tuple[PluginManifest, ...]:
        return tuple(
            manifest for manifest in self.values() if manifest.type.value == plugin_type
        )

    def by_domain(self, domain: str) -> tuple[PluginManifest, ...]:
        normalized = domain.strip().upper()
        return tuple(manifest for manifest in self.values() if manifest.domain == normalized)

    def diagnostics(self) -> tuple[PluginDiagnostic, ...]:
        return tuple(self._diagnostics)

    def add_diagnostic(self, diagnostic: PluginDiagnostic) -> None:
        self._diagnostics.append(diagnostic)

    def detect_duplicates(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(self._duplicate_ids))

    def __iter__(self) -> Iterator[PluginManifest]:
        return iter(self.values())

    def __len__(self) -> int:
        return len(self._entries)
