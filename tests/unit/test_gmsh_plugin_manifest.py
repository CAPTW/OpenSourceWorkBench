from __future__ import annotations

from osw.plugins.examples import builtin_gmsh_plugin_manifest
from osw.plugins.manifest import PluginType


def test_builtin_gmsh_plugin_manifest_validates() -> None:
    manifest = builtin_gmsh_plugin_manifest()

    assert manifest.id == "osw.gmsh"
    assert manifest.type is PluginType.MESH_GENERATOR
    assert "gmsh" in manifest.executable_names
    assert "mesh_size_control" in manifest.capabilities
    assert "physical_group_metadata" in manifest.capabilities
    assert not [
        diagnostic
        for diagnostic in manifest.validate()
        if diagnostic.severity.value == "error"
    ]
