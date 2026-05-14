from __future__ import annotations

import json
from pathlib import Path

from osw.gui.plugin_manager_dialog import (
    PluginEnablementStore,
    PluginManagerModel,
    plugin_manifest_table_rows,
)


def _manifest_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "demo.mesh",
        "name": "Demo Mesh Importer",
        "version": "0.1.0",
        "domain": "mesh",
        "type": "mesh_importer",
        "license": "MIT",
        "input_formats": ["vtk"],
        "output_formats": ["osw-mesh"],
        "requires": ["json"],
        "optional_requires": [],
        "capabilities": ["preview", "validate"],
    }
    data.update(overrides)
    return data


def _write_manifest(path: Path, data: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_plugin_manager_model_displays_discovered_manifest(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "plugins" / "demo" / "osw-plugin.json", _manifest_data())

    model = PluginManagerModel.from_paths([tmp_path / "plugins"], include_entry_points=False)
    rows = plugin_manifest_table_rows(model.entries)

    assert len(model.entries) == 1
    assert model.entries[0].plugin_id == "demo.mesh"
    assert model.entries[0].display_name == "Demo Mesh Importer"
    assert model.entries[0].enabled
    assert model.entries[0].valid
    assert rows == [("enabled", "demo.mesh", "Demo Mesh Importer", "mesh_importer", "ok")]


def test_plugin_manager_model_reports_invalid_manifest(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path / "plugins" / "invalid" / "osw-plugin.json",
        {"id": "bad.plugin", "type": "mesh_importer"},
    )

    model = PluginManagerModel.from_paths([tmp_path / "plugins"], include_entry_points=False)
    entry = model.entries[0]

    assert not entry.valid
    assert not entry.enabled
    assert "Invalid plugin manifest" in entry.error_message
    assert "missing required field" in entry.error_message


def test_plugin_enablement_store_persists_state(tmp_path: Path) -> None:
    store_path = tmp_path / "plugin-state.json"
    store = PluginEnablementStore(store_path)

    store.set_enabled("demo.mesh", False)

    restored = PluginEnablementStore(store_path)
    assert not restored.is_enabled("demo.mesh")


def test_plugin_manager_model_reports_missing_executable_warning(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path / "plugins" / "solver" / "osw-plugin.json",
        _manifest_data(
            id="demo.solver",
            name="Demo Solver",
            domain="solver",
            type="solver_adapter",
            capabilities=["prepare_case", "requires_executable:osw-missing-exe-for-test"],
        ),
    )

    model = PluginManagerModel.from_paths([tmp_path / "plugins"], include_entry_points=False)
    warning = model.entries[0].missing_executable_warnings[0]

    assert "Executable not configured or found" in warning
    assert "osw-missing-exe-for-test" in warning
    assert "Plugin Manager" in warning


def test_manifest_viewer_text_is_pretty_json(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "plugins" / "demo" / "osw-plugin.json", _manifest_data())

    model = PluginManagerModel.from_paths([tmp_path / "plugins"], include_entry_points=False)
    manifest_text = model.entries[0].manifest_text

    assert '"id": "demo.mesh"' in manifest_text
    assert '"capabilities": [' in manifest_text
