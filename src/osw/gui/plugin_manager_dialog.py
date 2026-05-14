"""Plugin manager dialog and GUI-safe plugin inventory model."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from osw.plugins.discovery import discover_entry_point_plugins, iter_manifest_paths
from osw.plugins.health import (
    PluginHealthRecord,
    build_plugin_health_record,
)
from osw.plugins.installer import PluginInstallError, PluginInstallManager, PluginInstallResult
from osw.plugins.manifest import PluginManifest, PluginManifestError

from .qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object
ENTRY_POINT_SOURCE = "entry-point"


@dataclass(frozen=True)
class PluginManagerEntry:
    plugin_id: str
    display_name: str
    version: str = ""
    plugin_type: str = ""
    domain: str = ""
    enabled: bool = False
    valid: bool = True
    health_status: str = "unknown"
    health_messages: tuple[str, ...] = field(default_factory=tuple)
    missing_executable_warnings: tuple[str, ...] = field(default_factory=tuple)
    sample_project_reference: str = ""
    last_health_check_status: str = "not-run"
    last_run_status: str = "not-run"
    manifest_text: str = ""
    error_message: str = ""
    source: str = ""
    health_record: PluginHealthRecord | None = None

    @property
    def dependency_status_lines(self) -> tuple[str, ...]:
        lines: list[str] = []
        if self.error_message:
            lines.append(self.error_message)
        lines.extend(self.health_messages)
        lines.extend(self.missing_executable_warnings)
        if not lines:
            lines.append("Dependencies available.")
        return tuple(lines)

    @property
    def dashboard_status_lines(self) -> tuple[str, ...]:
        lines = [
            f"Plugin status: {self.health_status}",
            "Dependency status: "
            + (
                self.health_record.dependency_status
                if self.health_record is not None
                else self.health_status
            ),
        ]
        lines.extend(f"Dependency: {message}" for message in self.health_messages)
        lines.extend(f"Executable: {message}" for message in self.missing_executable_warnings)
        lines.append(
            "Sample project: "
            + (self.sample_project_reference or "No sample project reference declared.")
        )
        lines.append(f"Last health check: {self.last_health_check_status}")
        lines.append(f"Last run: {self.last_run_status}")
        return tuple(lines)


class PluginEnablementStore:
    """Small local enablement store.

    A file path gives persistence for tests and future settings. Without a path
    it behaves as an in-memory stub store.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._enabled: dict[str, bool] = {}
        self._load()

    def is_enabled(self, plugin_id: str) -> bool:
        return self._enabled.get(plugin_id, True)

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        self._enabled[plugin_id] = enabled
        self._save()

    def _load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(data, dict):
            self._enabled = {str(key): bool(value) for key, value in data.items()}

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._enabled, indent=2, sort_keys=True),
            encoding="utf-8",
        )


@dataclass
class PluginManagerModel:
    entries: tuple[PluginManagerEntry, ...] = field(default_factory=tuple)
    enablement_store: PluginEnablementStore = field(default_factory=PluginEnablementStore)

    @classmethod
    def from_paths(
        cls,
        local_paths: Iterable[str | Path],
        *,
        include_entry_points: bool = True,
        enablement_store: PluginEnablementStore | None = None,
        executable_paths: Mapping[str, str | Path] | None = None,
    ) -> PluginManagerModel:
        store = enablement_store or PluginEnablementStore()
        configured_executables = executable_paths or {}
        entries: list[PluginManagerEntry] = []
        seen_ids: set[str] = set()

        for manifest_path in _manifest_paths(local_paths):
            entries.append(
                _entry_from_manifest_path(
                    manifest_path,
                    store=store,
                    seen_ids=seen_ids,
                    executable_paths=configured_executables,
                )
            )

        if include_entry_points:
            entries.extend(
                _entry_point_entries(
                    store=store,
                    seen_ids=seen_ids,
                    executable_paths=configured_executables,
                )
            )

        return cls(tuple(entries), store)

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        self.enablement_store.set_enabled(plugin_id, enabled)

    def entry_at(self, index: int) -> PluginManagerEntry | None:
        if index < 0 or index >= len(self.entries):
            return None
        return self.entries[index]


def plugin_manifest_table_rows(
    entries: Iterable[PluginManagerEntry],
) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for entry in entries:
        state = "enabled" if entry.enabled else "disabled"
        if not entry.valid:
            state = "invalid"
        rows.append(
            (
                state,
                entry.plugin_id,
                entry.display_name,
                entry.plugin_type,
                entry.health_status,
            )
        )
    return rows


class PluginManagerDialog(_BaseDialog):
    """PySide6 dialog for manifest review and local plugin enablement."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        entries: Iterable[PluginManagerEntry] | None = None,
        plugin_paths: Iterable[str | Path] = (),
        enablement_store: PluginEnablementStore | None = None,
        install_root: str | Path | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("pluginManagerDialog")
        self.setWindowTitle("Plugin Manager")
        self.resize(920, 560)

        self.install_root = Path(install_root) if install_root else _default_install_root()
        self.install_manager = PluginInstallManager(self.install_root)
        self._plugin_paths = _deduplicate_paths([*plugin_paths, self.install_root])

        if entries is None:
            self.model = PluginManagerModel.from_paths(
                self._plugin_paths,
                include_entry_points=True,
                enablement_store=enablement_store,
            )
        else:
            self.model = PluginManagerModel(
                tuple(entries),
                enablement_store or PluginEnablementStore(),
            )
        self._preserved_entry_point_entries = _entry_point_entries_from(self.model.entries)

        self.plugin_table = QtWidgets.QTableWidget(self)
        self.plugin_table.setObjectName("pluginManagerTable")
        self.manifest_viewer = QtWidgets.QPlainTextEdit(self)
        self.manifest_viewer.setObjectName("pluginManifestViewer")
        self.manifest_viewer.setReadOnly(True)
        self.dependency_status = QtWidgets.QPlainTextEdit(self)
        self.dependency_status.setObjectName("pluginDependencyStatus")
        self.dependency_status.setReadOnly(True)
        self.health_dashboard = QtWidgets.QPlainTextEdit(self)
        self.health_dashboard.setObjectName("pluginHealthDashboard")
        self.health_dashboard.setReadOnly(True)
        self.executable_path_edit = QtWidgets.QLineEdit(self)
        self.executable_path_edit.setObjectName("pluginExecutablePathEdit")
        self.executable_path_edit.setPlaceholderText("Executable path setting placeholder")
        self.health_button = QtWidgets.QPushButton("Run Health Check", self)
        self.health_button.setObjectName("pluginHealthCheckButton")
        self.install_folder_button = QtWidgets.QPushButton("Install Folder", self)
        self.install_folder_button.setObjectName("pluginInstallFolderButton")
        self.install_zip_button = QtWidgets.QPushButton("Install Zip", self)
        self.install_zip_button.setObjectName("pluginInstallZipButton")
        self.install_status = QtWidgets.QLabel(self)
        self.install_status.setObjectName("pluginInstallStatus")
        self.install_status.setWordWrap(True)
        self.missing_executable_warning = QtWidgets.QLabel(self)
        self.missing_executable_warning.setObjectName("pluginMissingExecutableWarning")
        self.missing_executable_warning.setWordWrap(True)

        self._build_layout()
        self._populate_table()
        self.plugin_table.currentCellChanged.connect(self._on_current_cell_changed)
        self.plugin_table.itemChanged.connect(self._on_table_item_changed)
        self.health_button.clicked.connect(self._show_selected_entry)
        self.install_folder_button.clicked.connect(self._choose_install_folder)
        self.install_zip_button.clicked.connect(self._choose_install_zip)
        if self.model.entries:
            self.plugin_table.setCurrentCell(0, 0)
            self._show_entry(0)

    def _build_layout(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        install_row = QtWidgets.QHBoxLayout()
        install_row.addWidget(self.install_folder_button)
        install_row.addWidget(self.install_zip_button)
        install_row.addStretch(1)
        root.addLayout(install_row)
        root.addWidget(self.install_status)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        splitter.addWidget(self.plugin_table)

        detail = QtWidgets.QWidget(splitter)
        detail_layout = QtWidgets.QVBoxLayout(detail)
        detail_layout.addWidget(QtWidgets.QLabel("Manifest"))
        detail_layout.addWidget(self.manifest_viewer, 2)
        detail_layout.addWidget(QtWidgets.QLabel("Dependency Status"))
        detail_layout.addWidget(self.dependency_status, 1)
        detail_layout.addWidget(QtWidgets.QLabel("Health Dashboard"))
        detail_layout.addWidget(self.health_dashboard, 1)
        detail_layout.addWidget(QtWidgets.QLabel("Executable Path"))
        detail_layout.addWidget(self.executable_path_edit)
        detail_layout.addWidget(self.missing_executable_warning)
        detail_layout.addWidget(self.health_button)
        splitter.addWidget(detail)

        root.addWidget(splitter)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _populate_table(self) -> None:
        self.plugin_table.blockSignals(True)
        self.plugin_table.setColumnCount(5)
        self.plugin_table.setHorizontalHeaderLabels(
            ["Enabled", "ID", "Name", "Type", "Health"]
        )
        self.plugin_table.setRowCount(len(self.model.entries))
        for row, entry in enumerate(self.model.entries):
            enabled_item = QtWidgets.QTableWidgetItem("")
            enabled_item.setFlags(
                enabled_item.flags()
                | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                | QtCore.Qt.ItemFlag.ItemIsEnabled
            )
            enabled_item.setCheckState(
                QtCore.Qt.CheckState.Checked
                if entry.enabled
                else QtCore.Qt.CheckState.Unchecked
            )
            if not entry.valid:
                enabled_item.setFlags(enabled_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEnabled)
            self.plugin_table.setItem(row, 0, enabled_item)
            self.plugin_table.setItem(row, 1, QtWidgets.QTableWidgetItem(entry.plugin_id))
            self.plugin_table.setItem(row, 2, QtWidgets.QTableWidgetItem(entry.display_name))
            self.plugin_table.setItem(row, 3, QtWidgets.QTableWidgetItem(entry.plugin_type))
            self.plugin_table.setItem(row, 4, QtWidgets.QTableWidgetItem(entry.health_status))
        self.plugin_table.resizeColumnsToContents()
        self.plugin_table.blockSignals(False)

    def _on_current_cell_changed(
        self,
        current_row: int,
        _current_column: int,
        _previous_row: int,
        _previous_column: int,
    ) -> None:
        self._show_entry(current_row)

    def _on_table_item_changed(self, item: object) -> None:
        if item.column() != 0:
            return
        entry = self.model.entry_at(item.row())
        if entry is None or not entry.valid:
            return
        enabled = item.checkState() == QtCore.Qt.CheckState.Checked
        self.model.set_enabled(entry.plugin_id, enabled)

    def _show_selected_entry(self) -> None:
        self._show_entry(self.plugin_table.currentRow())

    def _show_entry(self, index: int) -> None:
        entry = self.model.entry_at(index)
        if entry is None:
            self.manifest_viewer.clear()
            self.dependency_status.clear()
            self.health_dashboard.clear()
            self.missing_executable_warning.clear()
            return
        self.manifest_viewer.setPlainText(entry.manifest_text)
        self.dependency_status.setPlainText("\n".join(entry.dependency_status_lines))
        self.health_dashboard.setPlainText("\n".join(entry.dashboard_status_lines))
        self.missing_executable_warning.setText(
            "\n".join(entry.missing_executable_warnings)
        )

    def _choose_install_folder(self) -> None:
        selected = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Install OSW Plugin Folder",
        )
        if selected:
            self.install_plugin_folder(selected)

    def _choose_install_zip(self) -> None:
        selected, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Install OSW Plugin Zip",
            "",
            "Zip archives (*.zip)",
        )
        if selected:
            self.install_plugin_zip(selected)

    def install_plugin_folder(self, source: str | Path) -> PluginInstallResult | None:
        return self._install_and_refresh(
            lambda: self.install_manager.install_from_folder(
                source,
                existing_plugin_ids=self._current_plugin_ids(),
            )
        )

    def install_plugin_zip(self, source: str | Path) -> PluginInstallResult | None:
        return self._install_and_refresh(
            lambda: self.install_manager.install_from_zip(
                source,
                existing_plugin_ids=self._current_plugin_ids(),
            )
        )

    def _install_and_refresh(
        self,
        operation: Callable[[], PluginInstallResult],
    ) -> PluginInstallResult | None:
        try:
            result = operation()
        except PluginInstallError as exc:
            self.install_status.setText(f"Install rejected: {exc}")
            return None

        warning_suffix = ""
        if result.warnings:
            warning_suffix = " Warnings: " + "; ".join(result.warnings)
        self.install_status.setText(
            f"Installed plugin {result.plugin_id} into {result.installed_path}.{warning_suffix}"
        )
        self._refresh_model(selected_plugin_id=result.plugin_id)
        return result

    def _refresh_model(self, *, selected_plugin_id: str | None = None) -> None:
        refreshed_model = PluginManagerModel.from_paths(
            self._plugin_paths,
            include_entry_points=False,
            enablement_store=self.model.enablement_store,
        )
        entries = _merge_preserved_entry_point_entries(
            refreshed_model.entries,
            self._preserved_entry_point_entries,
            refreshed_model.enablement_store,
        )
        self.model = PluginManagerModel(entries, refreshed_model.enablement_store)
        self._populate_table()
        selected_row = 0
        if selected_plugin_id is not None:
            for row, entry in enumerate(self.model.entries):
                if entry.plugin_id == selected_plugin_id:
                    selected_row = row
                    break
        if self.model.entries:
            self.plugin_table.setCurrentCell(selected_row, 0)
            self._show_entry(selected_row)

    def _current_plugin_ids(self) -> tuple[str, ...]:
        return tuple(entry.plugin_id for entry in self.model.entries if entry.valid)


def _manifest_paths(local_paths: Iterable[str | Path]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for local_path in local_paths:
        paths.extend(iter_manifest_paths(local_path))
    return tuple(paths)


def _default_install_root() -> Path:
    return Path.home() / ".osw" / "plugins"


def _deduplicate_paths(paths: Iterable[str | Path]) -> tuple[Path, ...]:
    seen: set[Path] = set()
    deduplicated: list[Path] = []
    for path in paths:
        resolved = Path(path)
        if resolved in seen:
            continue
        seen.add(resolved)
        deduplicated.append(resolved)
    return tuple(deduplicated)


def _entry_point_entries_from(
    entries: Iterable[PluginManagerEntry],
) -> tuple[PluginManagerEntry, ...]:
    return tuple(entry for entry in entries if entry.source == ENTRY_POINT_SOURCE)


def _merge_preserved_entry_point_entries(
    entries: tuple[PluginManagerEntry, ...],
    preserved_entries: Iterable[PluginManagerEntry],
    store: PluginEnablementStore,
) -> tuple[PluginManagerEntry, ...]:
    seen_ids = {entry.plugin_id for entry in entries if entry.valid}
    merged = list(entries)
    for entry in preserved_entries:
        if entry.plugin_id in seen_ids:
            continue
        merged.append(replace(entry, enabled=store.is_enabled(entry.plugin_id)))
    return tuple(merged)


def _entry_from_manifest_path(
    manifest_path: Path,
    *,
    store: PluginEnablementStore,
    seen_ids: set[str],
    executable_paths: Mapping[str, str | Path],
) -> PluginManagerEntry:
    try:
        manifest = PluginManifest.load(manifest_path)
    except PluginManifestError as exc:
        return _invalid_entry(manifest_path, f"Invalid plugin manifest {manifest_path}: {exc}")
    return _entry_from_manifest(
        manifest,
        source=str(manifest_path),
        store=store,
        seen_ids=seen_ids,
        executable_paths=executable_paths,
    )


def _entry_point_entries(
    *,
    store: PluginEnablementStore,
    seen_ids: set[str],
    executable_paths: Mapping[str, str | Path],
) -> tuple[PluginManagerEntry, ...]:
    try:
        registry = discover_entry_point_plugins()
    except Exception as exc:
        return (_invalid_entry("entry-points", f"Invalid plugin entry point: {exc}"),)
    return tuple(
        _entry_from_manifest(
            manifest,
            source=ENTRY_POINT_SOURCE,
            store=store,
            seen_ids=seen_ids,
            executable_paths=executable_paths,
        )
        for manifest in registry
    )


def _entry_from_manifest(
    manifest: PluginManifest,
    *,
    source: str,
    store: PluginEnablementStore,
    seen_ids: set[str],
    executable_paths: Mapping[str, str | Path],
) -> PluginManagerEntry:
    if manifest.id in seen_ids:
        return _invalid_entry(source, f"Duplicate plugin id: {manifest.id}")
    seen_ids.add(manifest.id)

    health_record = build_plugin_health_record(
        manifest,
        enabled=store.is_enabled(manifest.id),
        valid=True,
        source=source,
        executable_paths=executable_paths,
        last_health_check_status="checked",
        last_run_status="not-run",
    )

    return PluginManagerEntry(
        plugin_id=manifest.id,
        display_name=manifest.name,
        version=manifest.version,
        plugin_type=manifest.type.value,
        domain=manifest.domain,
        enabled=store.is_enabled(manifest.id),
        valid=True,
        health_status=health_record.status,
        health_messages=health_record.dependency_messages,
        missing_executable_warnings=health_record.executable_messages,
        sample_project_reference=health_record.sample_project_reference,
        last_health_check_status=health_record.last_health_check_status,
        last_run_status=health_record.last_run_status,
        manifest_text=json.dumps(manifest.to_dict(), indent=2, sort_keys=True),
        source=source,
        health_record=health_record,
    )


def _invalid_entry(source: str | Path, message: str) -> PluginManagerEntry:
    source_text = str(source)
    return PluginManagerEntry(
        plugin_id=Path(source_text).stem or "<invalid>",
        display_name=Path(source_text).name or "Invalid plugin",
        enabled=False,
        valid=False,
        health_status="invalid",
        manifest_text=message,
        error_message=message,
        source=source_text,
    )
