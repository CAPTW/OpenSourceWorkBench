from __future__ import annotations

from osw.plugins.examples import builtin_calculix_plugin_manifest
from osw.plugins.manifest import PluginType


def test_builtin_calculix_plugin_manifest_validates() -> None:
    manifest = builtin_calculix_plugin_manifest()

    assert manifest.id == "osw.calculix"
    assert manifest.type is PluginType.SOLVER_ADAPTER
    assert "ccx" in manifest.executable_names
    assert "linear_static" in manifest.capabilities
    assert "input_deck_generation" in manifest.capabilities
    assert not [
        diagnostic
        for diagnostic in manifest.validate()
        if diagnostic.severity.value == "error"
    ]
