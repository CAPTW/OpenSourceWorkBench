from __future__ import annotations

from osw.plugins.examples import (
    builtin_cantera_plugin_manifest,
    builtin_coolprop_plugin_manifest,
    builtin_plugin_manifests,
)
from osw.plugins.health import build_plugin_health_record
from osw.plugins.manifest import PluginDomain, PluginType


def test_builtin_coolprop_plugin_manifest_validates() -> None:
    manifest = builtin_coolprop_plugin_manifest()

    assert manifest.id == "osw.coolprop"
    assert manifest.type is PluginType.PROPERTY_MODEL
    assert manifest.domain == PluginDomain.CHM.value
    assert manifest.optional_requires == ("CoolProp",)
    assert "result_dataset_binding" in manifest.capabilities
    assert "report_embedding" in manifest.capabilities
    assert not manifest.executable_names


def test_builtin_cantera_plugin_manifest_validates() -> None:
    manifest = builtin_cantera_plugin_manifest()

    assert manifest.id == "osw.cantera"
    assert manifest.type is PluginType.SOLVER_ADAPTER
    assert manifest.domain == PluginDomain.CHM.value
    assert manifest.optional_requires == ("cantera",)
    assert "zero_d_reactor" in manifest.capabilities
    assert "result_dataset_binding" in manifest.capabilities
    assert not manifest.executable_names


def test_builtin_chm_manifests_are_in_builtin_collection() -> None:
    plugin_ids = {manifest.id for manifest in builtin_plugin_manifests()}

    assert {"osw.coolprop", "osw.cantera"}.issubset(plugin_ids)


def test_chm_plugin_health_handles_missing_optional_dependencies() -> None:
    coolprop_health = build_plugin_health_record(builtin_coolprop_plugin_manifest())
    cantera_health = build_plugin_health_record(builtin_cantera_plugin_manifest())

    assert coolprop_health.plugin_id == "osw.coolprop"
    assert cantera_health.plugin_id == "osw.cantera"
    assert coolprop_health.status in {"ok", "warning"}
    assert cantera_health.status in {"ok", "warning"}

