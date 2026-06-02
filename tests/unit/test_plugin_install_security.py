from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from osw.plugins.installer import (
    PluginInstallError,
    PluginInstallManager,
    UnsafeArchiveError,
    ZipPathTraversalError,
)


def _manifest_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "demo.security.plugin",
        "name": "Security Demo Plugin",
        "version": "0.1.0",
        "domain": "GEOMETRY",
        "type": "cad_importer",
        "license": "MIT",
        "input_formats": ["step"],
        "output_formats": ["osw.geometry"],
        "requires": [],
        "optional_requires": [],
        "capabilities": ["preview"],
    }
    data.update(overrides)
    return data


def test_zip_absolute_path_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "absolute.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        # absolute path inside zip member
        archive.writestr("/tmp/evil.txt", "bad")
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))

    manager = PluginInstallManager(tmp_path / "installed")
    with pytest.raises(ZipPathTraversalError, match="is absolute, which is blocked"):
        manager.install_from_zip(archive_path)


def test_zip_windows_drive_letter_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "windows_drive.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("C:/Windows/System32/evil.dll", "bad")
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))

    manager = PluginInstallManager(tmp_path / "installed")
    with pytest.raises(ZipPathTraversalError, match="outside the install staging folder"):
        manager.install_from_zip(archive_path)


def test_zip_unc_path_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "unc.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("//server/share/evil.txt", "bad")
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))

    manager = PluginInstallManager(tmp_path / "installed")
    with pytest.raises(ZipPathTraversalError, match="is absolute, which is blocked"):
        manager.install_from_zip(archive_path)


def test_zip_backslash_traversal_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "backslash.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("..\\evil.txt", "bad")
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))

    manager = PluginInstallManager(tmp_path / "installed")
    with pytest.raises(ZipPathTraversalError, match="outside the install staging folder"):
        manager.install_from_zip(archive_path)


def test_empty_zip_archive_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(archive_path, "w"):
        pass

    manager = PluginInstallManager(tmp_path / "installed")
    with pytest.raises(UnsafeArchiveError, match="Archive is empty"):
        manager.install_from_zip(archive_path)


def test_zip_exceeds_file_count_limit(tmp_path: Path) -> None:
    archive_path = tmp_path / "limits_count.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))
        # Create 205 dummy files (exceeding 200 limit)
        for i in range(205):
            archive.writestr(f"demo/file_{i}.txt", "dummy")

    manager = PluginInstallManager(tmp_path / "installed")
    with pytest.raises(UnsafeArchiveError, match="exceeds maximum file count limit"):
        manager.install_from_zip(archive_path)


def test_zip_exceeds_uncompressed_size_limit(tmp_path: Path) -> None:
    archive_path = tmp_path / "limits_size.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))
        # uncompressed size total 11MB (limit is 10MB)
        archive.writestr("demo/large_file.txt", "a" * (11 * 1024 * 1024))

    manager = PluginInstallManager(tmp_path / "installed")
    with pytest.raises(UnsafeArchiveError, match="exceeds uncompressed size limit"):
        manager.install_from_zip(archive_path)


def test_zip_symlink_rejected_unix(tmp_path: Path) -> None:
    archive_path = tmp_path / "symlink.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))

        # We manually add a symlink entry
        # in zip, external_attr unix mode 0o120000 indicates a symlink
        info = zipfile.ZipInfo("demo/link_to_nowhere")
        info.external_attr = 0o120000 << 16
        archive.writestr(info, "target_file")

    manager = PluginInstallManager(tmp_path / "installed")
    with pytest.raises(UnsafeArchiveError, match="contains a symbolic link"):
        manager.install_from_zip(archive_path)


def test_local_folder_symlink_escape_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source" / "plugin"
    source.mkdir(parents=True)
    (source / "osw-plugin.json").write_text(
        json.dumps(_manifest_data(id="demo.local.link")),
        encoding="utf-8",
    )
    outside = tmp_path / "outside_secret.txt"
    outside.write_text("secret", encoding="utf-8")
    try:
        (source / "linked_secret.txt").symlink_to(outside)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"local symlink creation unavailable: {exc}")

    manager = PluginInstallManager(tmp_path / "installed")

    with pytest.raises(PluginInstallError, match="symbolic link|junction"):
        manager.install_from_folder(source)

    assert not manager.list_receipts()


def test_zip_pycache_excluded_during_install(tmp_path: Path) -> None:
    archive_path = tmp_path / "pycache.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))
        archive.writestr("demo/__pycache__/compiled.pyc", "binary_data")
        archive.writestr("demo/module.pyo", "binary_data")
        archive.writestr("demo/normal.py", "print('normal')")

    manager = PluginInstallManager(tmp_path / "installed")
    result = manager.install_from_zip(archive_path)

    assert result.plugin_id == "demo.security.plugin"
    assert (result.installed_path / "normal.py").exists()
    assert not (result.installed_path / "__pycache__").exists()
    assert not (result.installed_path / "module.pyo").exists()
