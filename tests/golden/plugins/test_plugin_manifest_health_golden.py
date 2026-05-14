from __future__ import annotations

from pathlib import Path

from helpers import assert_json_matches_golden

from osw.plugins.health import build_plugin_health_record, plugin_health_records_as_json
from osw.plugins.manifest import PluginManifest


def test_plugin_manifest_health_output_matches_golden_fixture() -> None:
    manifest = PluginManifest.from_dict(
        {
            "id": "osw.golden.manifest",
            "name": "Golden Manifest Plugin",
            "version": "0.1.0",
            "domain": "solver",
            "type": "solver_adapter",
            "license": "MIT",
            "input_formats": [],
            "output_formats": [],
            "requires": ["osw_missing_dependency_for_golden_test"],
            "optional_requires": [],
            "capabilities": [
                "prepare_case",
                "requires_executable:osw-missing-golden-exe",
                "sample_project:examples/golden_manifest",
            ],
        }
    )
    record = build_plugin_health_record(
        manifest,
        source="tests/golden/plugins/osw-plugin.json",
    )
    expected = (Path(__file__).with_name("plugin_health_records.json")).read_text(
        encoding="utf-8"
    )

    assert_json_matches_golden(
        plugin_health_records_as_json((record,)),
        expected,
        label="plugins/plugin_health_records.json",
    )
