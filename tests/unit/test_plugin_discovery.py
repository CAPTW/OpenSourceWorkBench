"""Plugin discovery tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.plugins.discovery import (
    DuplicatePluginIdError,
    PluginRegistry,
    discover_entry_point_plugins,
    discover_local_plugins,
)
from osw.plugins.manifest import PluginManifest


def _manifest_data(plugin_id: str) -> dict[str, object]:
    return {
        "id": plugin_id,
        "name": "Demo mesh importer",
        "version": "0.1.0",
        "domain": "mesh",
        "type": "mesh_importer",
        "license": "MIT",
        "input_formats": ["vtu"],
        "output_formats": ["osw.mesh.preview"],
        "requires": [],
        "optional_requires": ["meshio"],
        "capabilities": ["preview", "validate"],
    }


def _write_manifest(path: Path, plugin_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_manifest_data(plugin_id)), encoding="utf-8")


def test_local_plugin_discovery_loads_nested_manifests(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "plugins" / "meshio_demo" / "osw-plugin.json", "osw.meshio")

    registry = discover_local_plugins(tmp_path / "plugins")

    assert registry.get("osw.meshio").name == "Demo mesh importer"


def test_registry_detects_duplicate_plugin_ids() -> None:
    registry = PluginRegistry()
    manifest = PluginManifest.from_dict(_manifest_data("osw.duplicate"))

    registry.add(manifest)
    with pytest.raises(DuplicatePluginIdError, match="Duplicate plugin id: osw.duplicate"):
        registry.add(manifest)


def test_local_discovery_detects_duplicate_ids(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "a" / "osw-plugin.json", "osw.duplicate")
    _write_manifest(tmp_path / "b" / "osw-plugin.json", "osw.duplicate")

    with pytest.raises(DuplicatePluginIdError):
        discover_local_plugins(tmp_path)


def test_entry_point_discovery_loads_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = PluginManifest.from_dict(_manifest_data("osw.entrypoint"))

    class FakeEntryPoint:
        name = "demo"

        def load(self) -> PluginManifest:
            return manifest

    monkeypatch.setattr(
        "osw.plugins.discovery.metadata.entry_points",
        lambda group=None: [FakeEntryPoint()] if group == "osw.plugins" else [],
    )

    registry = discover_entry_point_plugins()

    assert registry.get("osw.entrypoint") == manifest
