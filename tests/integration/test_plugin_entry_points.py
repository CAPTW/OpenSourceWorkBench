"""Entry point discovery smoke tests for plugin metadata."""

from __future__ import annotations

import pytest

from osw.plugins.discovery import discover_entry_points, load_entry_point_plugin
from osw.plugins.manifest import PluginManifest


def _manifest() -> PluginManifest:
    return PluginManifest.from_dict(
        {
            "id": "osw.integration.entrypoint",
            "name": "Integration Entry Point",
            "version": "0.1.0",
            "domain": "GENERAL",
            "type": "ui_extension",
            "license": "MIT",
            "capabilities": ["metadata_discovery"],
        }
    )


def test_entry_point_metadata_discovery_defers_loading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded = False

    class FakeEntryPoint:
        name = "integration"

        def load(self) -> PluginManifest:
            nonlocal loaded
            loaded = True
            return _manifest()

    monkeypatch.setattr(
        "osw.plugins.discovery.metadata.entry_points",
        lambda group=None: [FakeEntryPoint()]
        if group == "opensolver_workbench.plugins"
        else [],
    )

    result = discover_entry_points(("opensolver_workbench.plugins",))

    assert len(result.records) == 1
    assert result.records[0].source_type == "entry_point"
    assert not loaded
    assert load_entry_point_plugin(result.records[0]).id == "osw.integration.entrypoint"
