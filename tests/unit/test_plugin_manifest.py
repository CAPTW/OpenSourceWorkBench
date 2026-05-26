"""Plugin manifest contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.plugins.errors import PluginDiagnosticSeverity
from osw.plugins.manifest import (
    PluginDomain,
    PluginManifest,
    PluginManifestError,
    PluginType,
    validate_manifest_data,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "plugins"


def _manifest_data() -> dict[str, object]:
    return {
        "id": "osw.demo.step_importer",
        "name": "Demo STEP importer",
        "version": "0.1.0",
        "domain": "geometry",
        "type": "cad_importer",
        "license": "MIT",
        "input_formats": ["step", "stp"],
        "output_formats": ["osw.geometry.preview"],
        "requires": [],
        "optional_requires": ["cadquery"],
        "capabilities": ["preview", "validate"],
    }


def test_valid_manifest_loads_from_mapping() -> None:
    manifest = PluginManifest.from_dict(_manifest_data())

    assert manifest.id == "osw.demo.step_importer"
    assert manifest.type == PluginType.CAD_IMPORTER
    assert manifest.domain == PluginDomain.GEOMETRY.value
    assert manifest.input_formats == ("step", "stp")
    assert manifest.supports_capability("preview")


def test_valid_manifest_loads_from_json_file(tmp_path: Path) -> None:
    path = tmp_path / "osw-plugin.json"
    path.write_text(json.dumps(_manifest_data()), encoding="utf-8")

    manifest = PluginManifest.load(path)

    assert manifest.name == "Demo STEP importer"


def test_invalid_manifest_raises_friendly_error() -> None:
    data = _manifest_data()
    data.pop("name")

    with pytest.raises(PluginManifestError, match="missing required field: name"):
        PluginManifest.from_dict(data)


def test_manifest_rejects_unknown_plugin_type() -> None:
    data = _manifest_data()
    data["type"] = "solver_that_runs_everything"

    with pytest.raises(PluginManifestError, match="unsupported plugin type"):
        PluginManifest.from_dict(data)


def test_valid_json_fixture_loads() -> None:
    manifest = PluginManifest.load(FIXTURES / "valid_calculix" / "manifest.json")

    assert manifest.id == "osw.calculix"
    assert manifest.type == PluginType.SOLVER_ADAPTER
    assert manifest.domain == PluginDomain.CAE.value
    assert manifest.executable_names == ("ccx",)


def test_valid_yaml_fixture_loads_when_pyyaml_available() -> None:
    pytest.importorskip("yaml")

    manifest = PluginManifest.load(FIXTURES / "valid_mscript" / "manifest.yaml")

    assert manifest.id == "osw.mscript"
    assert manifest.type == PluginType.SCRIPT_IMPORTER
    assert manifest.optional_requires == ("scipy",)


def test_missing_required_fields_return_structured_diagnostics() -> None:
    diagnostics = validate_manifest_data({"name": "Missing ID"})

    missing = [item for item in diagnostics if item.code == "missing-required-field"]

    assert any(item.field == "id" for item in missing)
    assert all(item.severity is PluginDiagnosticSeverity.ERROR for item in missing)


def test_unknown_plugin_type_returns_structured_diagnostic() -> None:
    data = _manifest_data()
    data["type"] = "unsupported_plugin_type"

    diagnostics = validate_manifest_data(data)

    assert any(item.code == "invalid-plugin-type" for item in diagnostics)


def test_unknown_fields_are_preserved_in_metadata() -> None:
    path = FIXTURES / "json_equivalent" / "plugin.json"
    raw_data = json.loads(path.read_text(encoding="utf-8"))
    manifest = PluginManifest.load(path)

    assert manifest.metadata["custom_unknown_field"] == "preserved"
    assert any(
        item.code == "unknown-manifest-field"
        for item in validate_manifest_data(raw_data)
    )


def test_example_report_manifest_uses_report_plugin_type() -> None:
    manifest = PluginManifest.load(FIXTURES / "valid_report" / "plugin.json")

    assert manifest.type == PluginType.REPORT_PLUGIN
    assert manifest.output_formats == ("html",)
