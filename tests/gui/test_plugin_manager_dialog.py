from __future__ import annotations

import importlib.util
import json
import os
import zipfile
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None

FIXTURES = Path(__file__).parents[1] / "fixtures" / "plugins"


def _install_manifest_data(plugin_id: str = "demo.gui.install") -> dict[str, object]:
    return {
        "id": plugin_id,
        "name": "GUI Install Fixture",
        "version": "0.1.0",
        "domain": "GENERAL",
        "type": "ui_extension",
        "license": "MIT",
        "capabilities": ["preview"],
    }


def _write_install_manifest(plugin_root: Path, plugin_id: str = "demo.gui.install") -> None:
    plugin_root.mkdir(parents=True, exist_ok=True)
    (plugin_root / "osw-plugin.json").write_text(
        json.dumps(_install_manifest_data(plugin_id)),
        encoding="utf-8",
    )


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _select_plugin(dialog: object, plugin_id: str) -> None:
    table = dialog.plugin_table
    for row in range(table.rowCount()):
        item = table.item(row, 2)
        if item is not None and item.text() == plugin_id:
            table.setCurrentCell(row, 0)
            return
    raise AssertionError(f"Plugin id not found in dialog table: {plugin_id}")


def _install_diagnostics_text(dialog: object) -> str:
    return "\n".join(
        dialog.install_diagnostics_list.item(index).text()
        for index in range(dialog.install_diagnostics_list.count())
    )


def test_plugin_manager_dialog_lists_fixture_manifests(app: object) -> None:
    from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog

    dialog = PluginManagerDialog(
        plugin_paths=[FIXTURES],
        include_entry_points=False,
    )

    assert dialog.objectName() == "oswPluginManagerDialog"
    assert dialog.plugin_table.objectName() == "oswPluginManagerTable"
    assert dialog.manifest_viewer.objectName() == "oswPluginManifestViewer"
    assert dialog.health_panel.objectName() == "oswPluginHealthPanel"
    assert dialog.executable_panel.objectName() == "oswPluginExecutablePanel"
    assert dialog.diagnostics_list.objectName() == "oswPluginDiagnosticsList"
    assert dialog.install_diagnostics_list.objectName() == "oswPluginInstallDiagnosticsList"
    assert dialog.install_folder_button.objectName() == "oswPluginInstallFolderButton"
    assert dialog.install_zip_button.objectName() == "oswPluginInstallZipButton"
    assert dialog.uninstall_button.objectName() == "oswPluginUninstallButton"
    assert dialog.receipt_panel.objectName() == "oswPluginInstallReceiptPanel"
    assert dialog.quarantine_panel.objectName() == "oswPluginQuarantineList"
    assert dialog.source_label.objectName() == "oswPluginInstallSourceLabel"
    assert dialog.refresh_button.objectName() == "oswPluginManagerRefreshButton"
    assert dialog.health_button.objectName() == "oswPluginManagerHealthButton"
    assert dialog.enable_button.objectName() == "oswPluginManagerEnableButton"
    assert dialog.disable_button.objectName() == "oswPluginManagerDisableButton"
    assert dialog.close_button.objectName() == "oswPluginManagerCloseButton"
    assert dialog.plugin_table.rowCount() >= 4

    _select_plugin(dialog, "osw.calculix")
    assert "CalculiX Adapter" in dialog.manifest_viewer.toPlainText()
    assert "linear_static" in dialog.capabilities_panel.toPlainText()

    del app


def test_plugin_manager_dialog_installs_folder_with_injected_installer(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog
    from osw.plugins.installer import PluginInstallManager

    source = tmp_path / "source" / "plugin"
    _write_install_manifest(source, "demo.gui.folder")
    dialog = PluginManagerDialog(plugin_paths=[], include_entry_points=False)
    dialog.set_plugin_installer(PluginInstallManager(tmp_path / "installed"))

    result = dialog.install_plugin_folder(source)

    assert result is not None
    _select_plugin(dialog, "demo.gui.folder")
    assert "demo.gui.folder" in dialog.receipt_panel.toPlainText()
    assert "Installed folder plugin" in _install_diagnostics_text(dialog)
    assert dialog.uninstall_selected_plugin()
    assert "Uninstalled managed plugin: demo.gui.folder" in _install_diagnostics_text(dialog)

    del app


def test_plugin_manager_dialog_invalid_and_duplicate_installs_show_diagnostics(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog
    from osw.plugins.installer import PluginInstallManager

    first = tmp_path / "source" / "first"
    duplicate = tmp_path / "source" / "duplicate"
    invalid = tmp_path / "source" / "invalid"
    _write_install_manifest(first, "demo.gui.duplicate")
    _write_install_manifest(duplicate, "demo.gui.duplicate")
    invalid.mkdir(parents=True)
    (invalid / "osw-plugin.json").write_text(
        json.dumps({"id": "demo.gui.invalid", "type": "ui_extension"}),
        encoding="utf-8",
    )
    dialog = PluginManagerDialog(plugin_paths=[], include_entry_points=False)
    dialog.set_plugin_installer(PluginInstallManager(tmp_path / "installed"))

    assert dialog.install_plugin_folder(first) is not None
    assert dialog.install_plugin_folder(duplicate) is None
    assert dialog.install_plugin_folder(invalid) is None

    text = _install_diagnostics_text(dialog)
    assert "Duplicate plugin id" in text
    assert "missing required field: name" in text

    del app


def test_plugin_manager_dialog_zip_traversal_shows_diagnostic(
    app: object,
    tmp_path: Path,
) -> None:
    from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog
    from osw.plugins.installer import PluginInstallManager

    archive_path = tmp_path / "traversal.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "bad")
        archive.writestr("demo/osw-plugin.json", json.dumps(_install_manifest_data("demo.zip")))
    dialog = PluginManagerDialog(plugin_paths=[], include_entry_points=False)
    dialog.set_plugin_installer(PluginInstallManager(tmp_path / "installed"))

    assert dialog.install_plugin_zip(archive_path) is None

    assert "outside the install staging folder" in _install_diagnostics_text(dialog)

    del app


def test_plugin_manager_dialog_surfaces_diagnostics_and_health(app: object) -> None:
    from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog

    dialog = PluginManagerDialog(
        plugin_paths=[FIXTURES],
        include_entry_points=False,
    )
    diagnostics_text = "\n".join(
        dialog.diagnostics_list.item(index).text()
        for index in range(dialog.diagnostics_list.count())
    )

    assert "missing-required-field" in diagnostics_text
    assert "invalid-plugin-type" in diagnostics_text
    assert "duplicate-plugin-id" in diagnostics_text

    _select_plugin(dialog, "osw.missing.executable")
    dialog.health_button.click()

    assert "osw-definitely-missing-executable" in dialog.executable_panel.toPlainText()
    assert "missing" in dialog.executable_panel.toPlainText()

    del app


def test_plugin_manager_enable_disable_updates_state(app: object) -> None:
    from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog
    from osw.plugins.state import PluginStateStore

    state = PluginStateStore()
    dialog = PluginManagerDialog(
        plugin_paths=[FIXTURES],
        include_entry_points=False,
        state_store=state,
    )

    _select_plugin(dialog, "osw.calculix")
    dialog.disable_button.click()
    assert not dialog.plugin_enabled("osw.calculix")
    dialog.enable_button.click()
    assert dialog.plugin_enabled("osw.calculix")

    del app


def test_executable_path_dialog_can_save_without_executing(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog
    from osw.plugins.state import PluginStateStore

    state = PluginStateStore()
    executable = tmp_path / "ccx.exe"
    executable.write_text("", encoding="utf-8")
    dialog = PluginManagerDialog(
        plugin_paths=[FIXTURES],
        include_entry_points=False,
        state_store=state,
    )

    path_dialog = dialog.create_executable_path_dialog("osw.calculix")
    assert path_dialog.objectName() == "oswExecutablePathDialog"
    assert path_dialog.executable_table.objectName() == "oswExecutablePathTable"
    assert path_dialog.save_button.objectName() == "oswExecutableSaveButton"
    path_dialog.executable_table.setItem(0, 1, QtWidgets.QTableWidgetItem(str(executable)))
    path_dialog.save_paths()

    assert state.get_executable_path("ccx") == str(executable)

    del app


def test_dialog_discovery_does_not_import_plugin_code(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog

    sentinel = tmp_path / "executed.txt"
    plugin_dir = tmp_path / "plugins" / "safe"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "id": "osw.safe.gui",
                "name": "Safe GUI Fixture",
                "version": "0.1.0",
                "domain": "GENERAL",
                "type": "ui_extension",
                "license": "MIT",
                "entry_point": "plugin_code:Plugin",
                "capabilities": ["preview"],
            }
        ),
        encoding="utf-8",
    )
    (plugin_dir / "plugin_code.py").write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n",
        encoding="utf-8",
    )

    dialog = PluginManagerDialog(
        plugin_paths=[tmp_path / "plugins"],
        include_entry_points=False,
    )

    assert dialog.plugin_table.rowCount() == 1
    assert not sentinel.exists()

    del app


def test_plugin_manager_dialog_theme_switch_smoke(app: object) -> None:
    from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog
    from osw.gui.theme_tokens import DARK_TOKENS, LIGHT_TOKENS

    dialog = PluginManagerDialog(
        plugin_paths=[FIXTURES],
        include_entry_points=False,
    )

    dialog.set_theme_tokens(DARK_TOKENS)
    dialog.set_theme_tokens(LIGHT_TOKENS)

    del app
