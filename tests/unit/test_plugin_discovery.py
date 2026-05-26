"""Plugin discovery tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from osw.plugins.discovery import (
    OSW_PLUGINS_PATH_ENV,
    DuplicatePluginIdError,
    PluginRegistry,
    discover_entry_point_plugins,
    discover_entry_points,
    discover_local_plugin_manifests,
    discover_local_plugins,
    discover_plugin_search_paths,
    load_entry_point_plugin,
)
from osw.plugins.manifest import PluginManifest

FIXTURES = Path(__file__).parents[1] / "fixtures" / "plugins"


def _manifest_data(plugin_id: str) -> dict[str, object]:
    return {
        "id": plugin_id,
        "name": "Demo mesh importer",
        "version": "0.1.0",
        "domain": "mesh",
        "type": "mesh_importer",
        "license": "MIT",
        "input_formats": ["vtu"],
        "output_formats": ["osw.mesh.preview"],
        "requires": [],
        "optional_requires": ["meshio"],
        "capabilities": ["preview", "validate"],
    }


def _write_manifest(path: Path, plugin_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_manifest_data(plugin_id)), encoding="utf-8")


def test_local_plugin_discovery_loads_nested_manifests(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "plugins" / "meshio_demo" / "osw-plugin.json", "osw.meshio")

    registry = discover_local_plugins(tmp_path / "plugins")

    assert registry.get("osw.meshio").name == "Demo mesh importer"


def test_single_manifest_path_discovery(tmp_path: Path) -> None:
    manifest_path = tmp_path / "plugin.json"
    _write_manifest(manifest_path, "osw.single")

    result = discover_local_plugin_manifests(manifest_path)

    assert result.manifests[0].id == "osw.single"
    assert result.records[0].source_type == "local_manifest"


def test_plugin_folder_and_parent_directory_discovery(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "plugins" / "a" / "manifest.json", "osw.a")
    _write_manifest(tmp_path / "plugins" / "b" / "plugin.json", "osw.b")

    result = discover_local_plugin_manifests(tmp_path / "plugins")

    assert {manifest.id for manifest in result.manifests} == {"osw.a", "osw.b"}


def test_osw_plugins_path_search_roots_are_collected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    monkeypatch.setenv(OSW_PLUGINS_PATH_ENV, f"{first}{os.pathsep}{second}")

    paths = discover_plugin_search_paths(include_project_plugins=False, include_user_plugins=False)

    assert paths == (first, second)


def test_registry_detects_duplicate_plugin_ids() -> None:
    registry = PluginRegistry()
    manifest = PluginManifest.from_dict(_manifest_data("osw.duplicate"))

    registry.add(manifest)
    with pytest.raises(DuplicatePluginIdError, match="Duplicate plugin id: osw.duplicate"):
        registry.add(manifest)


def test_local_discovery_detects_duplicate_ids(tmp_path: Path) -> None:
    _write_manifest(tmp_path / "a" / "osw-plugin.json", "osw.duplicate")
    _write_manifest(tmp_path / "b" / "osw-plugin.json", "osw.duplicate")

    with pytest.raises(DuplicatePluginIdError):
        discover_local_plugins(tmp_path)


def test_structured_discovery_reports_duplicates_without_crashing() -> None:
    result = discover_local_plugin_manifests(FIXTURES)

    assert "osw.duplicate.fixture" in result.duplicate_ids
    assert any(item.code == "duplicate-plugin-id" for item in result.diagnostics)


def test_invalid_manifest_does_not_crash_structured_discovery() -> None:
    result = discover_local_plugin_manifests(FIXTURES / "invalid_missing_id")

    assert not result.manifests
    assert any(item.code == "missing-required-field" for item in result.diagnostics)


def test_local_discovery_does_not_import_plugin_code(tmp_path: Path) -> None:
    sentinel = tmp_path / "executed.txt"
    plugin_dir = tmp_path / "plugins" / "local"
    _write_manifest(plugin_dir / "manifest.json", "osw.noimport")
    (plugin_dir / "plugin_code.py").write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n",
        encoding="utf-8",
    )

    result = discover_local_plugin_manifests(tmp_path / "plugins")

    assert result.get("osw.noimport").id == "osw.noimport"
    assert not sentinel.exists()


def test_entry_point_discovery_loads_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = PluginManifest.from_dict(_manifest_data("osw.entrypoint"))

    class FakeEntryPoint:
        name = "demo"

        def load(self) -> PluginManifest:
            return manifest

    monkeypatch.setattr(
        "osw.plugins.discovery.metadata.entry_points",
        lambda group=None: [FakeEntryPoint()] if group == "osw.plugins" else [],
    )

    registry = discover_entry_point_plugins()

    assert registry.get("osw.entrypoint") == manifest


def test_entry_point_metadata_discovery_does_not_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    loaded = False

    class FakeEntryPoint:
        name = "demo"

        def load(self) -> PluginManifest:
            nonlocal loaded
            loaded = True
            return PluginManifest.from_dict(_manifest_data("osw.loaded"))

    monkeypatch.setattr(
        "osw.plugins.discovery.metadata.entry_points",
        lambda group=None: [FakeEntryPoint()] if group == "osw.plugins" else [],
    )

    result = discover_entry_points(("osw.plugins",))

    assert len(result.records) == 1
    assert result.records[0].manifest is None
    assert not loaded


def test_explicit_entry_point_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = PluginManifest.from_dict(_manifest_data("osw.explicit"))

    class FakeEntryPoint:
        name = "demo"

        def load(self) -> PluginManifest:
            return manifest

    monkeypatch.setattr(
        "osw.plugins.discovery.metadata.entry_points",
        lambda group=None: [FakeEntryPoint()] if group == "osw.plugins" else [],
    )

    record = discover_entry_points(("osw.plugins",)).records[0]

    assert load_entry_point_plugin(record) == manifest
