from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.plugins.installer import (
    PluginInstallError,
    PluginInstallManager,
    PluginInstallReceipt,
)


def _manifest_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "demo.ux.plugin",
        "name": "UX Demo Plugin",
        "version": "0.1.0",
        "domain": "GENERAL",
        "type": "ui_extension",
        "license": "MIT",
        "requires": [],
        "optional_requires": [],
        "capabilities": ["preview"],
    }
    data.update(overrides)
    return data


def _write_manifest(plugin_root: Path, **overrides: object) -> None:
    plugin_root.mkdir(parents=True, exist_ok=True)
    (plugin_root / "osw-plugin.json").write_text(
        json.dumps(_manifest_data(**overrides)),
        encoding="utf-8",
    )


def test_receipt_summary_reports_managed_install_state(tmp_path: Path) -> None:
    source = tmp_path / "source" / "plugin"
    _write_manifest(source)
    (source / "payload.txt").write_text("demo", encoding="utf-8")
    manager = PluginInstallManager(tmp_path / "installed")

    result = manager.install_from_folder(source)
    summary = manager.summarize_plugin_install_state("demo.ux.plugin")

    assert result.receipt is not None
    assert manager.list_installed_receipts()[0].plugin_id == "demo.ux.plugin"
    assert summary.receipt_present
    assert summary.install_status == "installed"
    assert summary.source_kind == "local_folder"
    assert summary.uninstall_eligible
    assert summary.diagnostics_count == 0
    assert result.receipt.metadata["file_count"] == 2


def test_receipt_summary_handles_missing_and_corrupt_receipts_json(tmp_path: Path) -> None:
    manager = PluginInstallManager(tmp_path / "installed")

    missing_summary = manager.summarize_plugin_install_state("missing.plugin")
    assert not missing_summary.receipt_present
    assert missing_summary.diagnostics == ()

    manager.install_root.mkdir(parents=True)
    (manager.install_root / "receipts.json").write_text("{not-json", encoding="utf-8")

    corrupt_summary = manager.summarize_plugin_install_state("missing.plugin")
    assert not manager.list_receipts()
    assert not corrupt_summary.receipt_present
    assert any("Receipt registry is unreadable" in item for item in corrupt_summary.diagnostics)


def test_quarantine_summary_reports_records_and_corrupt_registry(tmp_path: Path) -> None:
    source = tmp_path / "source" / "invalid"
    source.mkdir(parents=True)
    (source / "osw-plugin.json").write_text(
        json.dumps({"id": "bad.ux.plugin", "type": "ui_extension"}),
        encoding="utf-8",
    )
    manager = PluginInstallManager(tmp_path / "installed")

    with pytest.raises(PluginInstallError, match="missing required field: name"):
        manager.install_from_folder(source)

    records = manager.list_quarantine_records()
    summary = manager.summarize_plugin_install_state("bad.ux.plugin")
    assert len(records) == 1
    assert records[0].metadata["source_kind"] == "local_folder"
    assert summary.quarantine_count == 1

    (manager.install_root / "quarantine_records.json").write_text(
        "[not-json",
        encoding="utf-8",
    )
    corrupt_summary = manager.summarize_plugin_install_state("bad.ux.plugin")
    assert not manager.list_quarantine_records()
    assert any(
        "Quarantine registry is unreadable" in item
        for item in corrupt_summary.diagnostics
    )


def test_uninstall_eligibility_false_for_receipt_outside_managed_root(
    tmp_path: Path,
) -> None:
    manager = PluginInstallManager(tmp_path / "installed")
    outside = tmp_path / "outside" / "plugin"
    outside.mkdir(parents=True)
    receipt = PluginInstallReceipt(
        plugin_id="demo.outside",
        name="Outside Plugin",
        version="0.1.0",
        source_kind="local_folder",
        source_path=str(tmp_path / "source"),
        installed_path=str(outside),
        manifest_path=str(outside / "osw-plugin.json"),
    )
    manager.install_root.mkdir(parents=True)
    (manager.install_root / "receipts.json").write_text(
        json.dumps({"demo.outside": receipt.to_dict()}),
        encoding="utf-8",
    )

    summary = manager.summarize_plugin_install_state("demo.outside")

    assert summary.receipt_present
    assert not summary.uninstall_eligible
    assert any("outside the managed install root" in item for item in summary.diagnostics)
