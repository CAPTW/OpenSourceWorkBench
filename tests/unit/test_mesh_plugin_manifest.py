from __future__ import annotations

from osw.plugins.examples import builtin_meshio_plugin_manifest
from osw.plugins.manifest import PluginDomain, PluginType


def test_builtin_meshio_plugin_manifest_validates() -> None:
    manifest = builtin_meshio_plugin_manifest()

    assert manifest.id == "osw.meshio"
    assert manifest.name == "meshio Mesh Import Bridge"
    assert manifest.type is PluginType.MESH_IMPORTER
    assert manifest.domain == PluginDomain.MESH.value
    assert "msh" in manifest.input_formats
    assert "inp" in manifest.input_formats
    assert "vtu" in manifest.input_formats
    assert "vtu" in manifest.output_formats
    assert "mesh_info" in manifest.capabilities
    assert not [
        diagnostic
        for diagnostic in manifest.validate()
        if diagnostic.severity.value == "error"
    ]
