"""Plugin manager dialog and GUI-safe plugin inventory model."""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from osw.plugins.discovery import discover_entry_point_plugins, iter_manifest_paths
from osw.plugins.health import PluginHealthStatus, check_manifest_health
from osw.plugins.manifest import PluginManifest, PluginManifestError

from .qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object
EXECUTABLE_CAPABILITY_PREFIXES = ("requires_executable:", "executable:")


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
    manifest_text: str = ""
    error_message: str = ""
    source: str = ""

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
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("pluginManagerDialog")
        self.setWindowTitle("Plugin Manager")
        self.resize(920, 560)

        if entries is None:
            self.model = PluginManagerModel.from_paths(
                plugin_paths,
                include_entry_points=True,
                enablement_store=enablement_store,
            )
        else:
            self.model = PluginManagerModel(
                tuple(entries),
                enablement_store or PluginEnablementStore(),
            )

        self.plugin_table = QtWidgets.QTableWidget(self)
        self.plugin_table.setObjectName("pluginManagerTable")
        self.manifest_viewer = QtWidgets.QPlainTextEdit(self)
        self.manifest_viewer.setObjectName("pluginManifestViewer")
        self.manifest_viewer.setReadOnly(True)
        self.dependency_status = QtWidgets.QPlainTextEdit(self)
        self.dependency_status.setObjectName("pluginDependencyStatus")
        self.dependency_status.setReadOnly(True)
        self.executable_path_edit = QtWidgets.QLineEdit(self)
        self.executable_path_edit.setObjectName("pluginExecutablePathEdit")
        self.executable_path_edit.setPlaceholderText("Executable path setting placeholder")
        self.health_button = QtWidgets.QPushButton("Run Health Check", self)
        self.health_button.setObjectName("pluginHealthCheckButton")
        self.missing_executable_warning = QtWidgets.QLabel(self)
        self.missing_executable_warning.setObjectName("pluginMissingExecutableWarning")
        self.missing_executable_warning.setWordWrap(True)

        self._build_layout()
        self._populate_table()
        self.plugin_table.currentCellChanged.connect(self._on_current_cell_changed)
        self.plugin_table.itemChanged.connect(self._on_table_item_changed)
        self.health_button.clicked.connect(self._show_selected_entry)
        if self.model.entries:
            self.plugin_table.setCurrentCell(0, 0)
            self._show_entry(0)

    def _build_layout(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        splitter.addWidget(self.plugin_table)

        detail = QtWidgets.QWidget(splitter)
        detail_layout = QtWidgets.QVBoxLayout(detail)
        detail_layout.addWidget(QtWidgets.QLabel("Manifest"))
        detail_layout.addWidget(self.manifest_viewer, 2)
        detail_layout.addWidget(QtWidgets.QLabel("Dependency Status"))
        detail_layout.addWidget(self.dependency_status, 1)
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
            self.missing_executable_warning.clear()
            return
        self.manifest_viewer.setPlainText(entry.manifest_text)
        self.dependency_status.setPlainText("\n".join(entry.dependency_status_lines))
        self.missing_executable_warning.setText(
            "\n".join(entry.missing_executable_warnings)
        )


def _manifest_paths(local_paths: Iterable[str | Path]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for local_path in local_paths:
        paths.extend(iter_manifest_paths(local_path))
    return tuple(paths)


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
            source="entry-point",
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

    health = check_manifest_health(manifest)
    missing_executable_warnings = _missing_executable_warnings(manifest, executable_paths)
    health_status = health.status.value
    if health.status is PluginHealthStatus.OK and missing_executable_warnings:
        health_status = PluginHealthStatus.WARNING.value

    return PluginManagerEntry(
        plugin_id=manifest.id,
        display_name=manifest.name,
        version=manifest.version,
        plugin_type=manifest.type.value,
        domain=manifest.domain,
        enabled=store.is_enabled(manifest.id),
        valid=True,
        health_status=health_status,
        health_messages=health.messages,
        missing_executable_warnings=missing_executable_warnings,
        manifest_text=json.dumps(manifest.to_dict(), indent=2, sort_keys=True),
        source=source,
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


def _missing_executable_warnings(
    manifest: PluginManifest,
    executable_paths: Mapping[str, str | Path],
) -> tuple[str, ...]:
    warnings: list[str] = []
    for executable in _required_executables(manifest):
        configured_path = executable_paths.get(executable)
        configured_exists = configured_path is not None and Path(configured_path).exists()
        if configured_exists or shutil.which(executable):
            continue
        warnings.append(
            "Executable not configured or found: "
            f"{executable}. Set the path in Plugin Manager before preparing runs."
        )
    return tuple(warnings)


def _required_executables(manifest: PluginManifest) -> tuple[str, ...]:
    executables: list[str] = []
    for capability in manifest.capabilities:
        for prefix in EXECUTABLE_CAPABILITY_PREFIXES:
            if capability.startswith(prefix):
                executable = capability.removeprefix(prefix).strip()
                if executable:
                    executables.append(executable)
    return tuple(executables)
