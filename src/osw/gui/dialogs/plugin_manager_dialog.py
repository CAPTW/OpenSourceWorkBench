"""Safe Plugin Manager dialog bound to manifest discovery and health data."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from osw.core.executables import ExecutablePathRegistry
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.plugins.discovery import (
    PluginDiscoveryResult,
    discover_entry_points,
    discover_local_plugin_manifests,
    discover_plugin_search_paths,
)
from osw.plugins.errors import PluginDiagnostic
from osw.plugins.health import PluginHealthRecord, build_plugin_health_record
from osw.plugins.manifest import PluginManifest
from osw.plugins.registry import PluginRegistry
from osw.plugins.state import PluginStateStore

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


@dataclass(frozen=True)
class PluginManagerRow:
    plugin_id: str
    name: str
    version: str = ""
    plugin_type: str = ""
    domain: str = ""
    source: str = ""
    source_type: str = "local_directory"
    enabled: bool = True
    valid: bool = True
    health_status: str = "unknown"
    manifest: PluginManifest | None = None
    diagnostics: tuple[PluginDiagnostic, ...] = field(default_factory=tuple)
    metadata_text: str = ""


class ExecutablePathDialog(_BaseDialog):
    """Configure executable paths without running the executable."""

    def __init__(
        self,
        executables: tuple[str, ...],
        *,
        state_store: PluginStateStore,
        executable_registry: ExecutablePathRegistry | None = None,
        parent: object | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswExecutablePathDialog")
        self.setWindowTitle("Configure Executables")
        self.resize(760, 320)
        self._executables = tuple(dict.fromkeys(executables))
        self.state_store = state_store
        self.executable_registry = executable_registry or ExecutablePathRegistry()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.executable_table = QtWidgets.QTableWidget(self)
        self.executable_table.setObjectName("oswExecutablePathTable")
        self.executable_table.setColumnCount(4)
        self.executable_table.setHorizontalHeaderLabels(["Name", "Path", "Source", "Status"])
        self.executable_table.setRowCount(len(self._executables))
        self._populate_table()
        layout.addWidget(self.executable_table, 1)

        button_row = QtWidgets.QHBoxLayout()
        self.browse_button = QtWidgets.QPushButton("Browse...", self)
        self.browse_button.setObjectName("oswExecutableBrowseButton")
        self.clear_button = QtWidgets.QPushButton("Clear", self)
        self.clear_button.setObjectName("oswExecutableClearButton")
        self.save_button = QtWidgets.QPushButton("Save", self)
        self.save_button.setObjectName("oswExecutableSaveButton")
        button_row.addWidget(self.browse_button)
        button_row.addWidget(self.clear_button)
        button_row.addStretch(1)
        button_row.addWidget(self.save_button)
        layout.addLayout(button_row)

        self.browse_button.clicked.connect(self._browse_selected)
        self.clear_button.clicked.connect(self._clear_selected)
        self.save_button.clicked.connect(self.save_paths)

    def save_paths(self) -> None:
        for row, name in enumerate(self._executables):
            item = self.executable_table.item(row, 1)
            self.state_store.set_executable_path(name, item.text() if item else "")
        self._populate_table()

    def _populate_table(self) -> None:
        self.executable_table.blockSignals(True)
        for row, name in enumerate(self._executables):
            configured = self.state_store.get_executable_path(name) or ""
            resolution = _resolve_executable(name, {**self.state_store.executable_paths()})
            self.executable_table.setItem(row, 0, _readonly_item(name))
            self.executable_table.setItem(row, 1, QtWidgets.QTableWidgetItem(configured))
            self.executable_table.setItem(row, 2, _readonly_item(resolution.source))
            status = "available" if resolution.found else "missing"
            self.executable_table.setItem(row, 3, _readonly_item(status))
        self.executable_table.resizeColumnsToContents()
        self.executable_table.blockSignals(False)

    def _browse_selected(self) -> None:
        row = self.executable_table.currentRow()
        if row < 0:
            return
        selected, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select executable path",
        )
        if selected:
            self.executable_table.setItem(row, 1, QtWidgets.QTableWidgetItem(selected))

    def _clear_selected(self) -> None:
        row = self.executable_table.currentRow()
        if row >= 0:
            self.executable_table.setItem(row, 1, QtWidgets.QTableWidgetItem(""))


class PluginManagerDialog(_BaseDialog):
    """Manifest-first plugin manager dialog.

    Discovery reads manifest data only. It does not load local plugin modules,
    run entry points, run executables, or call the backend runner.
    """

    if QtCore is not None:
        pluginStateChanged = QtCore.Signal(str, bool)
        executablePathsChanged = QtCore.Signal()

    def __init__(
        self,
        parent: object | None = None,
        *,
        registry: PluginRegistry | None = None,
        plugin_paths: tuple[str | Path, ...] | list[str | Path] = (),
        state_store: PluginStateStore | None = None,
        executable_registry: ExecutablePathRegistry | None = None,
        include_entry_points: bool = True,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswPluginManagerDialog")
        self.setWindowTitle("Plugin Manager")
        self.resize(1080, 680)

        self.registry = registry
        self.plugin_paths = tuple(Path(path) for path in plugin_paths)
        self.state_store = state_store or PluginStateStore()
        self.executable_registry = executable_registry or ExecutablePathRegistry()
        self.include_entry_points = include_entry_points
        self._tokens = theme_tokens or DARK_TOKENS
        self._rows: list[PluginManagerRow] = []
        self._health_by_id: dict[str, PluginHealthRecord] = {}
        self._diagnostics: list[PluginDiagnostic] = []
        self._executable_dialog: ExecutablePathDialog | None = None

        from osw.plugins.installer import PluginInstallManager
        install_root = Path.home() / ".osw" / "plugins"
        self.installer = PluginInstallManager(install_root)

        self._build_layout()
        self.refresh_plugins()
        self.set_theme_tokens(self._tokens)

    def set_registry(self, registry: PluginRegistry) -> None:
        self.registry = registry
        self.refresh_plugins()

    def set_executable_registry(self, registry: ExecutablePathRegistry) -> None:
        self.executable_registry = registry
        self.run_health_check_all()

    def selected_plugin_id(self) -> str | None:
        row = self.plugin_table.currentRow()
        if row < 0 or row >= len(self._rows):
            return None
        plugin_id = self._rows[row].plugin_id
        return plugin_id if plugin_id else None

    def plugin_enabled(self, plugin_id: str) -> bool:
        return self.state_store.is_enabled(plugin_id)

    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> None:
        self.state_store.set_enabled(plugin_id, enabled)
        for row, row_data in enumerate(self._rows):
            if row_data.plugin_id == plugin_id:
                self._rows[row] = _with_enabled(row_data, enabled)
                item = self.plugin_table.item(row, 0)
                if item is not None:
                    item.setCheckState(
                        QtCore.Qt.CheckState.Checked
                        if enabled
                        else QtCore.Qt.CheckState.Unchecked
                    )
                break
        self.pluginStateChanged.emit(plugin_id, enabled)

    def refresh_plugins(self) -> None:
        self._health_by_id.clear()
        self._rows, self._diagnostics = self._collect_rows()
        self.run_health_check_all(update_table=False)
        self._populate_table()
        self._populate_diagnostics_list()
        if self._rows:
            self.plugin_table.setCurrentCell(0, 0)
            self._show_row(0)
        else:
            self._show_empty_state()

    def run_health_check_selected(self) -> None:
        plugin_id = self.selected_plugin_id()
        if plugin_id is None:
            return
        for row in self._rows:
            if row.plugin_id == plugin_id and row.manifest is not None:
                self._health_by_id[plugin_id] = build_plugin_health_record(
                    row.manifest,
                    enabled=self.state_store.is_enabled(plugin_id),
                    source=row.source,
                    executable_paths=self.state_store.executable_paths(),
                )
                break
        self._populate_table()
        self._show_row(self.plugin_table.currentRow())

    def run_health_check_all(self, *, update_table: bool = True) -> dict[str, PluginHealthRecord]:
        health: dict[str, PluginHealthRecord] = {}
        for row in self._rows:
            if row.manifest is None:
                continue
            health[row.plugin_id] = build_plugin_health_record(
                row.manifest,
                enabled=self.state_store.is_enabled(row.plugin_id),
                source=row.source,
                executable_paths=self.state_store.executable_paths(),
            )
        self._health_by_id = health
        if update_table:
            self._populate_table()
            self._show_row(self.plugin_table.currentRow())
        return dict(self._health_by_id)

    def create_executable_path_dialog(self, plugin_id: str | None = None) -> ExecutablePathDialog:
        row = self._row_for_plugin_id(plugin_id or self.selected_plugin_id())
        executables = row.manifest.executable_names if row and row.manifest else ()
        self._executable_dialog = ExecutablePathDialog(
            tuple(executables),
            state_store=self.state_store,
            executable_registry=self.executable_registry,
            parent=self,
        )
        return self._executable_dialog

    def open_executable_path_dialog(self) -> None:
        dialog = self.create_executable_path_dialog()
        dialog.exec()
        self.run_health_check_selected()
        self.executablePathsChanged.emit()

    def set_plugin_installer(self, installer: Any) -> None:
        self.installer = installer
        self.refresh_plugins()

    def install_plugin_folder(self, path: str | Path) -> None:
        try:
            result = self.installer.install_from_folder(path, allow_replace=False)
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Successfully installed plugin: {result.manifest.name} ({result.plugin_id})"
            )
            self.refresh_plugins()
        except Exception as exc:
            QtWidgets.QMessageBox.warning(
                self,
                "Installation Failed",
                f"Could not install plugin from folder:\n{exc}"
            )

    def install_plugin_zip(self, path: str | Path) -> None:
        try:
            result = self.installer.install_from_zip(path, allow_replace=False)
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Successfully installed plugin: {result.manifest.name} ({result.plugin_id})"
            )
            self.refresh_plugins()
        except Exception as exc:
            QtWidgets.QMessageBox.warning(
                self,
                "Installation Failed",
                f"Could not install plugin from ZIP:\n{exc}"
            )

    def uninstall_selected_plugin(self) -> None:
        plugin_id = self.selected_plugin_id()
        if not plugin_id:
            QtWidgets.QMessageBox.warning(self, "Warning", "No plugin selected.")
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to uninstall plugin: {plugin_id}?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.No:
            return

        try:
            self.installer.uninstall_plugin(plugin_id)
            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Successfully uninstalled plugin: {plugin_id}"
            )
            self.refresh_plugins()
        except Exception as exc:
            QtWidgets.QMessageBox.warning(
                self,
                "Uninstall Failed",
                f"Could not uninstall plugin:\n{exc}"
            )

    def _browse_install_folder(self) -> None:
        selected = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Plugin Folder to Install",
        )
        if selected:
            self.install_plugin_folder(selected)

    def _browse_install_zip(self) -> None:
        selected, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Plugin ZIP to Install",
            filter="ZIP Archives (*.zip)",
        )
        if selected:
            self.install_plugin_zip(selected)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswPluginManagerDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel[oswPluginSectionHeader='true'] {"
            f"color: {tokens.accent};"
            "font-weight: 700;"
            "}"
            "QPlainTextEdit, QListWidget, QTableWidget {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "}"
            "QPushButton:disabled {"
            f"color: {tokens.text_muted};"
            "}"
        )

    def _build_layout(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        button_row = QtWidgets.QHBoxLayout()
        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        self.refresh_button.setObjectName("oswPluginManagerRefreshButton")
        self.health_button = QtWidgets.QPushButton("Run Health Check", self)
        self.health_button.setObjectName("oswPluginManagerHealthButton")
        self.enable_button = QtWidgets.QPushButton("Enable", self)
        self.enable_button.setObjectName("oswPluginManagerEnableButton")
        self.disable_button = QtWidgets.QPushButton("Disable", self)
        self.disable_button.setObjectName("oswPluginManagerDisableButton")
        self.configure_executables_button = QtWidgets.QPushButton(
            "Configure Executables...",
            self,
        )
        self.configure_executables_button.setObjectName("oswPluginManagerExecutablesButton")
        self.install_folder_button = QtWidgets.QPushButton(
            "Install from Folder...",
            self,
        )
        self.install_folder_button.setObjectName("oswPluginInstallFolderButton")
        self.install_zip_button = QtWidgets.QPushButton("Install from Zip...", self)
        self.install_zip_button.setObjectName("oswPluginInstallZipButton")
        self.uninstall_button = QtWidgets.QPushButton("Uninstall Selected", self)
        self.uninstall_button.setObjectName("oswPluginUninstallButton")
        self.uninstall_button.setEnabled(False)
        for button in (
            self.refresh_button,
            self.health_button,
            self.enable_button,
            self.disable_button,
            self.configure_executables_button,
            self.install_folder_button,
            self.install_zip_button,
            self.uninstall_button,
        ):
            button_row.addWidget(button)
        button_row.addStretch(1)
        root.addLayout(button_row)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        self.plugin_table = QtWidgets.QTableWidget(splitter)
        self.plugin_table.setObjectName("oswPluginManagerTable")
        self.plugin_table.setColumnCount(8)
        self.plugin_table.setHorizontalHeaderLabels(
            ["Enabled", "Health", "ID", "Name", "Version", "Type", "Domain", "Source"]
        )
        self.plugin_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.plugin_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )

        details = QtWidgets.QWidget(splitter)
        details_layout = QtWidgets.QVBoxLayout(details)
        details_layout.setContentsMargins(8, 0, 0, 0)
        details_layout.setSpacing(6)
        self.details_tabs = QtWidgets.QTabWidget(details)
        self.details_tabs.setObjectName("oswPluginManagerDetailsTabs")
        self.manifest_viewer = _readonly_plain_text("oswPluginManifestViewer", details)
        self.capabilities_panel = _readonly_plain_text("oswPluginCapabilitiesPanel", details)
        self.health_panel = _readonly_plain_text("oswPluginHealthPanel", details)
        self.executable_panel = _readonly_plain_text("oswPluginExecutablePanel", details)
        self.diagnostics_list = QtWidgets.QListWidget(details)
        self.diagnostics_list.setObjectName("oswPluginDiagnosticsList")
        self.receipt_panel = _readonly_plain_text("oswPluginInstallReceiptPanel", details)
        self.quarantine_panel = _readonly_plain_text("oswPluginQuarantineList", details)
        self.source_label = QtWidgets.QLabel(details)
        self.source_label.setObjectName("oswPluginInstallSourceLabel")
        self.source_label.setStyleSheet("padding: 2px; font-style: italic;")

        self.details_tabs.addTab(self.manifest_viewer, "Manifest")
        self.details_tabs.addTab(self.capabilities_panel, "Capabilities")
        self.details_tabs.addTab(self.health_panel, "Dependencies")
        self.details_tabs.addTab(self.executable_panel, "Executables")
        self.details_tabs.addTab(self.diagnostics_list, "Diagnostics")
        self.details_tabs.addTab(self.receipt_panel, "Receipt")
        self.details_tabs.addTab(self.quarantine_panel, "Quarantine")
        
        details_layout.addWidget(self.source_label)
        details_layout.addWidget(self.details_tabs)

        splitter.addWidget(self.plugin_table)
        splitter.addWidget(details)
        splitter.setSizes([540, 520])
        root.addWidget(splitter, 1)

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName("oswPluginManagerCloseButton")
        close_row.addWidget(self.close_button)
        root.addLayout(close_row)

        self.refresh_button.clicked.connect(self.refresh_plugins)
        self.health_button.clicked.connect(self.run_health_check_selected)
        self.enable_button.clicked.connect(
            lambda: self._set_selected_enabled(enabled=True)
        )
        self.disable_button.clicked.connect(
            lambda: self._set_selected_enabled(enabled=False)
        )
        self.configure_executables_button.clicked.connect(self.open_executable_path_dialog)
        self.install_folder_button.clicked.connect(self._browse_install_folder)
        self.install_zip_button.clicked.connect(self._browse_install_zip)
        self.uninstall_button.clicked.connect(self.uninstall_selected_plugin)
        self.close_button.clicked.connect(self.accept)
        self.plugin_table.currentCellChanged.connect(
            lambda current_row, _current_col, _previous_row, _previous_col: self._show_row(
                current_row
            )
        )
        self.plugin_table.itemChanged.connect(self._on_table_item_changed)

    def _collect_rows(self) -> tuple[list[PluginManagerRow], list[PluginDiagnostic]]:
        if self.registry is not None:
            rows = [
                _row_from_manifest(
                    manifest,
                    source=self.registry.get_entry(manifest.id).source,
                    enabled=self.state_store.is_enabled(manifest.id),
                )
                for manifest in self.registry.values()
            ]
            return rows, list(self.registry.diagnostics())

        if self.plugin_paths:
            plugin_paths = list(self.plugin_paths)
        else:
            plugin_paths = list(
                discover_plugin_search_paths(
                    include_project_plugins=True,
                    include_user_plugins=False,
                )
            )
        if self.installer and self.installer.install_root not in plugin_paths:
            plugin_paths.append(self.installer.install_root)
        result = discover_local_plugin_manifests(plugin_paths)
        rows = _rows_from_discovery(result, self.state_store)
        diagnostics = list(result.diagnostics)
        if self.include_entry_points:
            entry_points = discover_entry_points()
            for record in entry_points.records:
                rows.append(
                    PluginManagerRow(
                        plugin_id=record.source_name,
                        name=f"Entry point: {record.source_name}",
                        source=record.source_name,
                        source_type="entry_point",
                        enabled=False,
                        valid=True,
                        health_status="unknown",
                        metadata_text=(
                            "Entry point metadata is listed only. "
                            "Explicit loading is deferred."
                        ),
                    )
                )
        return rows, diagnostics

    def _populate_table(self) -> None:
        self.plugin_table.blockSignals(True)
        self.plugin_table.setRowCount(len(self._rows))
        for row, row_data in enumerate(self._rows):
            health = self._health_by_id.get(row_data.plugin_id)
            status = _row_status(row_data, health)
            enabled = self.state_store.is_enabled(row_data.plugin_id) and row_data.valid
            enabled_item = QtWidgets.QTableWidgetItem("")
            enabled_item.setData(QtCore.Qt.ItemDataRole.UserRole, row_data.plugin_id)
            enabled_item.setFlags(
                enabled_item.flags()
                | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                | QtCore.Qt.ItemFlag.ItemIsEnabled
            )
            if not row_data.valid or row_data.manifest is None:
                enabled_item.setFlags(
                    enabled_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEnabled
                )
            enabled_item.setCheckState(
                QtCore.Qt.CheckState.Checked if enabled else QtCore.Qt.CheckState.Unchecked
            )
            self.plugin_table.setItem(row, 0, enabled_item)
            for column, value in enumerate(
                (
                    status,
                    row_data.plugin_id,
                    row_data.name,
                    row_data.version,
                    row_data.plugin_type,
                    row_data.domain,
                    row_data.source or row_data.source_type,
                ),
                start=1,
            ):
                item = _readonly_item(value)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, row_data.plugin_id)
                self.plugin_table.setItem(row, column, item)
        self.plugin_table.resizeColumnsToContents()
        self.plugin_table.blockSignals(False)

    def _populate_diagnostics_list(self) -> None:
        self.diagnostics_list.clear()
        all_diagnostics = list(self._diagnostics)
        for row in self._rows:
            all_diagnostics.extend(row.diagnostics)
        if not all_diagnostics:
            self.diagnostics_list.addItem("No diagnostics.")
            return
        for diagnostic in all_diagnostics:
            self.diagnostics_list.addItem(_diagnostic_line(diagnostic))

    def _show_row(self, row: int) -> None:
        if row < 0 or row >= len(self._rows):
            self._show_empty_state()
            return
        row_data = self._rows[row]
        health = self._health_by_id.get(row_data.plugin_id)
        self.manifest_viewer.setPlainText(_manifest_text(row_data))
        self.capabilities_panel.setPlainText(_capabilities_text(row_data))
        self.health_panel.setPlainText(_health_text(row_data, health))
        self.executable_panel.setPlainText(_executable_text(row_data, health))
        self._populate_diagnostics_list()
        self.configure_executables_button.setEnabled(
            bool(row_data.manifest and row_data.manifest.executable_names)
        )
        self.enable_button.setEnabled(row_data.valid and row_data.manifest is not None)
        self.disable_button.setEnabled(row_data.valid and row_data.manifest is not None)
        
        # Display Source path
        self.source_label.setText(f"Source: {row_data.source or 'unknown'}")

        # Load and show receipt details
        receipt = self.installer.get_receipt(row_data.plugin_id) if self.installer else None
        if receipt:
            self.receipt_panel.setPlainText(json.dumps(receipt.to_dict(), indent=2))
            self.uninstall_button.setEnabled(True)
        else:
            self.receipt_panel.setPlainText(
                "No installation receipt. (This is a built-in or entry point plugin.)"
            )
            self.uninstall_button.setEnabled(False)

        # Load and show quarantine details
        if self.installer:
            q_records = self.installer.list_quarantine()
            if q_records:
                q_text = "Quarantine & Rejection Logs:\n\n"
                for q in reversed(q_records):
                    q_text += (
                        f"Time: {q.created_at}\n"
                        f"Source: {q.source_path}\n"
                        f"Quarantine Path: {q.quarantine_path}\n"
                        f"Reason: {q.reason}\n"
                        "----------------------------------------\n"
                    )
                self.quarantine_panel.setPlainText(q_text)
            else:
                self.quarantine_panel.setPlainText("No quarantined or rejected plugins.")
        else:
            self.quarantine_panel.setPlainText("No quarantine records available.")

    def _show_empty_state(self) -> None:
        self.manifest_viewer.setPlainText("No local plugin manifests discovered.")
        self.capabilities_panel.clear()
        self.health_panel.setPlainText("No health check data.")
        self.executable_panel.clear()
        self.configure_executables_button.setEnabled(False)
        self.enable_button.setEnabled(False)
        self.disable_button.setEnabled(False)
        self.uninstall_button.setEnabled(False)
        self.source_label.clear()
        self.receipt_panel.setPlainText("No active plugin selected.")
        self.quarantine_panel.setPlainText("No active plugin selected.")
        self._populate_diagnostics_list()

    def _row_for_plugin_id(self, plugin_id: str | None) -> PluginManagerRow | None:
        if not plugin_id:
            return None
        for row in self._rows:
            if row.plugin_id == plugin_id:
                return row
        return None

    def _set_selected_enabled(self, *, enabled: bool) -> None:
        plugin_id = self.selected_plugin_id()
        if plugin_id:
            self.set_plugin_enabled(plugin_id, enabled)

    def _on_table_item_changed(self, item: object) -> None:
        if item.column() != 0:
            return
        plugin_id = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(plugin_id, str):
            return
        row = self._row_for_plugin_id(plugin_id)
        if row is None or not row.valid or row.manifest is None:
            return
        self.set_plugin_enabled(
            plugin_id,
            item.checkState() == QtCore.Qt.CheckState.Checked,
        )


def _rows_from_discovery(
    result: PluginDiscoveryResult,
    state_store: PluginStateStore,
) -> list[PluginManagerRow]:
    rows: list[PluginManagerRow] = []
    for record in result.records:
        if record.manifest is None:
            rows.append(
                PluginManagerRow(
                    plugin_id=Path(record.source_path).stem or "<invalid>",
                    name="Invalid plugin manifest",
                    source=record.source_path or record.source_name,
                    source_type=record.source_type,
                    enabled=False,
                    valid=False,
                    health_status="error",
                    diagnostics=record.diagnostics,
                    metadata_text="\n".join(_diagnostic_line(item) for item in record.diagnostics),
                )
            )
            continue
        duplicate = record.manifest.id in result.duplicate_ids
        diagnostics = tuple(
            diagnostic
            for diagnostic in result.diagnostics
            if diagnostic.code == "duplicate-plugin-id"
            and diagnostic.message.endswith(record.manifest.id)
        )
        rows.append(
            _row_from_manifest(
                record.manifest,
                source=record.source_path or record.source_name,
                source_type=record.source_type,
                enabled=state_store.is_enabled(record.manifest.id),
                valid=not duplicate,
                diagnostics=diagnostics,
                health_status="error" if duplicate else "unknown",
            )
        )
    return rows


def _row_from_manifest(
    manifest: PluginManifest,
    *,
    source: str = "",
    source_type: str = "local_directory",
    enabled: bool = True,
    valid: bool = True,
    diagnostics: tuple[PluginDiagnostic, ...] = (),
    health_status: str = "unknown",
) -> PluginManagerRow:
    return PluginManagerRow(
        plugin_id=manifest.id,
        name=manifest.name,
        version=manifest.version,
        plugin_type=manifest.type.value,
        domain=manifest.domain,
        source=source,
        source_type=source_type,
        enabled=enabled,
        valid=valid,
        health_status=health_status,
        manifest=manifest,
        diagnostics=diagnostics,
    )


def _with_enabled(row: PluginManagerRow, enabled: bool) -> PluginManagerRow:
    return PluginManagerRow(
        plugin_id=row.plugin_id,
        name=row.name,
        version=row.version,
        plugin_type=row.plugin_type,
        domain=row.domain,
        source=row.source,
        source_type=row.source_type,
        enabled=enabled,
        valid=row.valid,
        health_status=row.health_status,
        manifest=row.manifest,
        diagnostics=row.diagnostics,
        metadata_text=row.metadata_text,
    )


def _readonly_plain_text(object_name: str, parent: object) -> object:
    widget = QtWidgets.QPlainTextEdit(parent)
    widget.setObjectName(object_name)
    widget.setReadOnly(True)
    return widget


def _readonly_item(text: object) -> object:
    item = QtWidgets.QTableWidgetItem(str(text))
    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
    return item


def _row_status(row: PluginManagerRow, health: PluginHealthRecord | None) -> str:
    if not row.valid:
        return "error"
    if health is not None:
        return health.status
    return row.health_status


def _manifest_text(row: PluginManagerRow) -> str:
    if row.manifest is None:
        return row.metadata_text or "No manifest data available."
    return json.dumps(row.manifest.to_dict(), indent=2, sort_keys=True)


def _capabilities_text(row: PluginManagerRow) -> str:
    if row.manifest is None:
        return "No capabilities available."
    lines = [
        f"ID: {row.manifest.id}",
        f"Name: {row.manifest.name}",
        f"Version: {row.manifest.version}",
        f"Type: {row.manifest.type.value}",
        f"Domain: {row.manifest.domain}",
        "Capabilities:",
    ]
    lines.extend(f"- {capability}" for capability in row.manifest.capabilities)
    return "\n".join(lines)


def _health_text(row: PluginManagerRow, health: PluginHealthRecord | None) -> str:
    if not row.valid:
        lines = ["Status: error"]
        lines.extend(_diagnostic_line(item) for item in row.diagnostics)
        return "\n".join(lines)
    if health is None:
        return "Status: unknown"
    lines = [
        f"Status: {health.status}",
        f"Dependency status: {health.dependency_status}",
    ]
    if health.dependency_messages:
        lines.extend(f"Dependency: {message}" for message in health.dependency_messages)
    else:
        lines.append("Dependencies available.")
    return "\n".join(lines)


def _executable_text(row: PluginManagerRow, health: PluginHealthRecord | None) -> str:
    if row.manifest is None:
        return "No executable declarations available."
    if not row.manifest.executable_names:
        return "This plugin manifest does not declare executable dependencies."
    lines = ["Executable diagnostics:"]
    if health is None:
        lines.extend(f"- {name}: not checked" for name in row.manifest.executable_names)
        return "\n".join(lines)
    for executable in health.executable_status:
        state = "available" if executable.available else "missing"
        lines.append(f"- {executable.executable}: {state}")
        lines.append(f"  {executable.message}")
    return "\n".join(lines)


def _diagnostic_line(diagnostic: PluginDiagnostic) -> str:
    parts = [f"{diagnostic.severity.value}: {diagnostic.code}", diagnostic.message]
    if diagnostic.hint:
        parts.append(f"Hint: {diagnostic.hint}")
    if diagnostic.source:
        parts.append(f"Source: {diagnostic.source}")
    return " | ".join(parts)


def _resolve_executable(name: str, executable_paths: dict[str, str]) -> Any:
    registry = ExecutablePathRegistry()
    for executable, path in executable_paths.items():
        registry.register(executable, path)
    return registry.resolve(name)
