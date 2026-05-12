"""Plugin manifest contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.plugins.manifest import PluginManifest, PluginManifestError, PluginType


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
