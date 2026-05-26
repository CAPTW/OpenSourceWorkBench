"""Plugin registry tests."""

from __future__ import annotations

import pytest

from osw.plugins.manifest import PluginManifest
from osw.plugins.registry import DuplicatePluginIdError, PluginRegistry


def _manifest(plugin_id: str, *, plugin_type: str = "mesh_importer") -> PluginManifest:
    return PluginManifest.from_dict(
        {
            "id": plugin_id,
            "name": plugin_id,
            "version": "0.1.0",
            "domain": "MESH",
            "type": plugin_type,
            "license": "MIT",
            "capabilities": ["preview"],
        }
    )


def test_add_manifest_get_list_by_type_and_domain() -> None:
    registry = PluginRegistry()
    manifest = _manifest("osw.registry.mesh")

    registry.add_manifest(manifest, source="test")

    assert registry.get("osw.registry.mesh") == manifest
    assert registry.list() == (manifest,)
    assert registry.by_type("mesh_importer") == (manifest,)
    assert registry.by_domain("mesh") == (manifest,)


def test_duplicate_detection_records_diagnostic() -> None:
    registry = PluginRegistry()
    manifest = _manifest("osw.registry.duplicate")
    registry.add_manifest(manifest)

    with pytest.raises(DuplicatePluginIdError):
        registry.add_manifest(manifest, source="duplicate")

    assert registry.detect_duplicates() == ("osw.registry.duplicate",)
    assert registry.diagnostics()[0].code == "duplicate-plugin-id"


def test_register_plugin_uses_manifest() -> None:
    manifest = _manifest("osw.registry.plugin", plugin_type="solver_adapter")

    class FakePlugin:
        pass

    plugin = FakePlugin()
    plugin.manifest = manifest

    registry = PluginRegistry()
    registry.register_plugin(plugin)

    entry = registry.get_entry("osw.registry.plugin")
    assert entry.manifest == manifest
    assert entry.plugin is plugin
