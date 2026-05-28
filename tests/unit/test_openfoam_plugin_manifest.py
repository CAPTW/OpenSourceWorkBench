from __future__ import annotations

from osw.plugins.examples import builtin_openfoam_plugin_manifest
from osw.plugins.manifest import PluginDomain, PluginType


def test_builtin_openfoam_plugin_manifest_validates() -> None:
    manifest = builtin_openfoam_plugin_manifest()

    assert manifest.id == "osw.openfoam"
    assert manifest.type is PluginType.SOLVER_ADAPTER
    assert manifest.domain == PluginDomain.CFD.value
    assert manifest.executable_names == ("blockMesh", "icoFoam", "simpleFoam")
    assert "cavity_template" in manifest.capabilities
    assert "duct_template" in manifest.capabilities
    assert "residual_parser" in manifest.capabilities
    assert not manifest.validate()
