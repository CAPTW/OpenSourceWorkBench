from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from osw.gui.plugin_manager_dialog import (
    PluginEnablementStore,
    PluginManagerEntry,
    _merge_preserved_entry_point_entries,
)
from osw.plugins.installer import (
    DuplicatePluginInstallError,
    PluginInstallError,
    PluginInstallManager,
    ZipPathTraversalError,
)


def _manifest_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "demo.plugin",
        "name": "Demo Plugin",
        "version": "0.1.0",
        "domain": "mesh",
        "type": "mesh_importer",
        "license": "MIT",
        "input_formats": ["vtu"],
        "output_formats": ["osw.mesh.preview"],
        "requires": [],
        "optional_requires": [],
        "capabilities": ["preview", "validate"],
    }
    data.update(overrides)
    return data


def _write_manifest(plugin_root: Path, **overrides: object) -> Path:
    plugin_root.mkdir(parents=True, exist_ok=True)
    manifest_path = plugin_root / "osw-plugin.json"
    manifest_path.write_text(json.dumps(_manifest_data(**overrides)), encoding="utf-8")
    return manifest_path


def test_valid_folder_installs_manifest_only_without_executing_plugin_code(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source" / "plugin"
    sentinel = tmp_path / "executed.txt"
    _write_manifest(source, entry_point="plugin_code:Plugin")
    (source / "plugin_code.py").write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n",
        encoding="utf-8",
    )

    manager = PluginInstallManager(tmp_path / "installed")
    result = manager.install_from_folder(source)

    assert result.plugin_id == "demo.plugin"
    assert result.installed_path.exists()
    assert (result.installed_path / "osw-plugin.json").exists()
    assert (result.installed_path / "plugin_code.py").exists()
    assert not sentinel.exists()


def test_invalid_manifest_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source" / "invalid"
    source.mkdir(parents=True)
    (source / "osw-plugin.json").write_text(
        json.dumps({"id": "bad.plugin", "type": "mesh_importer"}),
        encoding="utf-8",
    )

    manager = PluginInstallManager(tmp_path / "installed")

    with pytest.raises(PluginInstallError, match="missing required field: name"):
        manager.install_from_folder(source)

    assert not (tmp_path / "installed").exists()


def test_duplicate_plugin_id_is_detected(tmp_path: Path) -> None:
    first = tmp_path / "source" / "first"
    second = tmp_path / "source" / "second"
    _write_manifest(first, id="demo.duplicate")
    _write_manifest(second, id="demo.duplicate")
    manager = PluginInstallManager(tmp_path / "installed")

    manager.install_from_folder(first)

    with pytest.raises(DuplicatePluginInstallError, match="Duplicate plugin id"):
        manager.install_from_folder(second)


def test_duplicate_plugin_id_can_be_checked_against_external_registry(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source" / "plugin"
    _write_manifest(source, id="demo.external")
    manager = PluginInstallManager(tmp_path / "installed")

    with pytest.raises(DuplicatePluginInstallError, match="Duplicate plugin id"):
        manager.install_from_folder(source, existing_plugin_ids=("demo.external",))


def test_distinct_valid_ids_do_not_collide_on_install_directory(tmp_path: Path) -> None:
    ids = ("demo.a-b", "demo.a_b", "demo.a.b")
    manager = PluginInstallManager(tmp_path / "installed")
    installed_paths: set[Path] = set()

    for plugin_id in ids:
        source = tmp_path / "source" / plugin_id
        _write_manifest(source, id=plugin_id)
        installed_paths.add(manager.install_from_folder(source).installed_path)

    assert set(manager.installed_plugin_ids()) == set(ids)
    assert len(installed_paths) == len(ids)


def test_preserved_entry_points_merge_without_refreshing_discovery(tmp_path: Path) -> None:
    store = PluginEnablementStore(tmp_path / "state.json")
    store.set_enabled("entry.point", False)
    local_entry = PluginManagerEntry(
        plugin_id="local.plugin",
        display_name="Local Plugin",
        valid=True,
        source=str(tmp_path / "local" / "osw-plugin.json"),
    )
    entry_point_entry = PluginManagerEntry(
        plugin_id="entry.point",
        display_name="Entry Point Plugin",
        enabled=True,
        valid=True,
        source="entry-point",
    )

    merged = _merge_preserved_entry_point_entries(
        (local_entry,),
        (entry_point_entry,),
        store,
    )

    assert [entry.plugin_id for entry in merged] == ["local.plugin", "entry.point"]
    assert not merged[1].enabled


def test_zip_plugin_installs_from_archive(tmp_path: Path) -> None:
    archive_path = tmp_path / "demo.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))
        archive.writestr("demo/resources/readme.txt", "demo")

    manager = PluginInstallManager(tmp_path / "installed")
    result = manager.install_from_zip(archive_path)

    assert result.plugin_id == "demo.plugin"
    assert (result.installed_path / "osw-plugin.json").exists()
    assert (result.installed_path / "resources" / "readme.txt").read_text(
        encoding="utf-8"
    ) == "demo"


def test_zip_path_traversal_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "traversal.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "bad")
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))

    manager = PluginInstallManager(tmp_path / "installed")

    with pytest.raises(ZipPathTraversalError, match="outside the install staging folder"):
        manager.install_from_zip(archive_path)

    assert not (tmp_path / "outside.txt").exists()
    assert not (tmp_path / "installed").exists()


def test_dependency_warning_is_reported_without_blocking_install(tmp_path: Path) -> None:
    source = tmp_path / "source" / "plugin"
    _write_manifest(source, requires=["osw_missing_dependency_for_install_test"])
    manager = PluginInstallManager(tmp_path / "installed")

    result = manager.install_from_folder(source)

    assert result.installed_path.exists()
    assert result.warnings == (
        "Required dependency is missing: osw_missing_dependency_for_install_test",
    )
