"""Plugin base contract and health tests."""

from __future__ import annotations

from osw.plugins.base import MeshImporterPlugin, WorkbenchPlugin
from osw.plugins.health import PluginHealthStatus, check_manifest_health
from osw.plugins.manifest import PluginManifest


def _manifest(plugin_id: str = "osw.test.mesh") -> PluginManifest:
    return PluginManifest.from_dict(
        {
            "id": plugin_id,
            "name": "Test mesh importer",
            "version": "0.1.0",
            "domain": "mesh",
            "type": "mesh_importer",
            "license": "MIT",
            "input_formats": ["vtu"],
            "output_formats": ["osw.mesh.preview"],
            "requires": [],
            "optional_requires": [],
            "capabilities": ["preview", "validate"],
        }
    )


class DemoMeshImporter(MeshImporterPlugin):
    manifest = _manifest()


def test_plugin_base_exposes_manifest_and_health() -> None:
    plugin: WorkbenchPlugin = DemoMeshImporter()

    assert plugin.id == "osw.test.mesh"
    assert plugin.health().status == PluginHealthStatus.OK


def test_health_reports_missing_required_module() -> None:
    manifest = PluginManifest.from_dict(
        {
            **_manifest("osw.test.missing").to_dict(),
            "requires": ["definitely_missing_osw_dependency"],
        }
    )

    health = check_manifest_health(manifest)

    assert health.status == PluginHealthStatus.ERROR
    assert "definitely_missing_osw_dependency" in health.messages[0]
