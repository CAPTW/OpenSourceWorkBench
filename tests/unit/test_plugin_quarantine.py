from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from osw.plugins.installer import (
    PluginInstallError,
    PluginInstallManager,
    ZipPathTraversalError,
)


def _manifest_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "demo.quarantine.plugin",
        "name": "Quarantine Demo Plugin",
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

def test_quarantine_created_on_invalid_folder_install(tmp_path: Path) -> None:
    source = tmp_path / "source" / "invalid"
    source.mkdir(parents=True)
    # Manifest missing "name" field (invalid schema)
    (source / "osw-plugin.json").write_text(
        json.dumps({"id": "bad.quarantine", "type": "mesh_importer"}),
        encoding="utf-8",
    )

    manager = PluginInstallManager(tmp_path / "installed")
    # Pre-create install root so that quarantine record is written successfully!
    manager.install_root.mkdir(parents=True, exist_ok=True)

    with pytest.raises(PluginInstallError, match="missing required field: name"):
        manager.install_from_folder(source)

    records = manager.list_quarantine()
    assert len(records) == 1
    assert records[0].reason != ""
    reason = records[0].reason
    assert "bad.quarantine" in reason or "missing required field: name" in reason
    assert records[0].quarantine_path is not None
    assert Path(records[0].quarantine_path).exists()

def test_quarantine_created_on_zip_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "traversal.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "bad")
        archive.writestr("demo/osw-plugin.json", json.dumps(_manifest_data()))

    manager = PluginInstallManager(tmp_path / "installed")
    manager.install_root.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ZipPathTraversalError):
        manager.install_from_zip(archive_path)

    records = manager.list_quarantine()
    assert len(records) == 1
    assert "staging folder" in records[0].reason or "outside" in records[0].reason
    assert records[0].quarantine_path is not None
    assert Path(records[0].quarantine_path).exists()
