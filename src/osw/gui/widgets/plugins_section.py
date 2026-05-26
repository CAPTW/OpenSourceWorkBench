"""Plugin status section for the right properties inspector."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

DEMO_PLUGIN_ROWS = (
    ("Octave / MATLAB Interface", True),
    ("ParaView Catalyst", True),
    ("Mesh Quality Checker", True),
    ("Report Generator", True),
)
PLUGIN_OBJECT_NAMES = {
    "Octave / MATLAB Interface": "oswPluginOctaveMatlab",
    "ParaView Catalyst": "oswPluginParaViewCatalyst",
    "Mesh Quality Checker": "oswPluginMeshQualityChecker",
    "Report Generator": "oswPluginReportGenerator",
}


class PluginsSection(_BaseWidget):
    """Compact plugin enabled-state list with registry-backed rows."""

    if QtCore is not None:
        manage_plugins_requested = QtCore.Signal()

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswPluginsSection")
        self._tokens = DARK_TOKENS
        self._plugins: list[dict[str, bool | str]] = []
        self._registry: object | None = None
        self._health_by_id: Mapping[str, object] = {}
        self._use_demo_when_empty = True
        self.plugin_widgets: dict[str, object] = {}
        self.status_labels: dict[str, object] = {}
        self.last_manage_report_request: str | None = None

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(8, 7, 8, 8)
        self._layout.setSpacing(6)
        self.header_label = QtWidgets.QLabel("PLUGINS", self)
        self.header_label.setObjectName("oswPluginsHeader")
        self._layout.addWidget(self.header_label)

        self.rows_container = QtWidgets.QWidget(self)
        self.rows_layout = QtWidgets.QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(5)
        self._layout.addWidget(self.rows_container)

        self.manage_report_button = QtWidgets.QPushButton("Manage Report...", self)
        self.manage_report_button.setObjectName("oswManageReportButton")
        self.manage_report_button.clicked.connect(self._record_manage_report_request)
        self._layout.addWidget(self.manage_report_button)

        self._set_rows(_demo_row_dicts())
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def plugin_rows(self) -> list[dict[str, bool | str]]:
        rows: list[dict[str, bool | str]] = []
        for row in self._plugins:
            if row.get("_demo"):
                rows.append({"name": str(row["name"]), "enabled": bool(row["enabled"])})
            else:
                rows.append({key: value for key, value in row.items() if key != "_demo"})
        return rows

    def use_demo_rows_when_empty(self, enabled: bool) -> None:
        self._use_demo_when_empty = enabled
        self.refresh_from_plugins()

    def set_plugin_registry(self, registry: object | None) -> None:
        self._registry = registry
        self.refresh_from_plugins()

    def set_plugin_health_map(self, health_by_id: Mapping[str, object] | None) -> None:
        self._health_by_id = health_by_id or {}
        self.refresh_from_plugins()

    def refresh_from_plugins(self) -> None:
        rows = self._rows_from_registry()
        if not rows and self._use_demo_when_empty:
            rows = _demo_row_dicts()
        self._set_rows(rows)

    def set_plugin_enabled(self, name: str, enabled: bool) -> None:
        for row in self._plugins:
            if row.get("name") == name or row.get("plugin_id") == name:
                row["enabled"] = enabled
                label = self.status_labels.get(str(row["name"]))
                if label is not None:
                    label.setText(_status_text(row))
                    label.setProperty("oswEnabledBadge", bool(enabled))
                self.set_theme_tokens(self._tokens)
                return

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswPluginsSection {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel#oswPluginsHeader {"
            f"color: {tokens.accent};"
            "font-weight: 800;"
            "background: transparent;"
            "border: none;"
            "}"
            "QFrame[oswPluginRow='true'] {"
            f"background-color: {tokens.bg_panel};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 3px;"
            "}"
            "QFrame[oswPluginRow='true'] QLabel {"
            f"color: {tokens.text_secondary};"
            "background: transparent;"
            "border: none;"
            "}"
            "QLabel[oswEnabledBadge='true'] {"
            f"color: {tokens.success};"
            "font-weight: 700;"
            "}"
            "QLabel[oswWarningBadge='true'] {"
            f"color: {tokens.warning};"
            "font-weight: 700;"
            "}"
        )

    def _rows_from_registry(self) -> list[dict[str, bool | str]]:
        if self._registry is None or not hasattr(self._registry, "values"):
            return []
        rows: list[dict[str, bool | str]] = []
        for manifest in self._registry.values():
            plugin_id = str(getattr(manifest, "id", ""))
            health = self._health_by_id.get(plugin_id)
            enabled = bool(getattr(health, "enabled", True))
            status = str(getattr(health, "status", "unknown"))
            rows.append(
                {
                    "name": str(getattr(manifest, "name", plugin_id)),
                    "plugin_id": plugin_id,
                    "enabled": enabled,
                    "status": status,
                }
            )
        return rows

    def _set_rows(self, rows: list[dict[str, bool | str]]) -> None:
        self._clear_rows()
        self._plugins = rows
        for row_data in rows:
            row = QtWidgets.QFrame(self.rows_container)
            name = str(row_data["name"])
            row.setObjectName(PLUGIN_OBJECT_NAMES.get(name, _dynamic_row_object_name(name)))
            row.setProperty("oswPluginRow", True)
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(7, 4, 7, 4)
            row_layout.setSpacing(6)
            name_label = QtWidgets.QLabel(name, row)
            status_label = QtWidgets.QLabel(_status_text(row_data), row)
            status_label.setProperty("oswEnabledBadge", bool(row_data.get("enabled", False)))
            status_label.setProperty(
                "oswWarningBadge",
                str(row_data.get("status", "")).lower() in {"warning", "error", "unavailable"},
            )
            row_layout.addWidget(name_label, 1)
            row_layout.addWidget(status_label)
            self.rows_layout.addWidget(row)
            self.plugin_widgets[name] = row
            self.status_labels[name] = status_label
        self.set_theme_tokens(self._tokens)

    def _clear_rows(self) -> None:
        self.plugin_widgets.clear()
        self.status_labels.clear()
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _record_manage_report_request(self) -> None:
        self.last_manage_report_request = "plugin-manager"
        self.manage_plugins_requested.emit()


def _demo_row_dicts() -> list[dict[str, bool | str]]:
    return [
        {
            "name": name,
            "plugin_id": name,
            "enabled": enabled,
            "status": "ok",
            "_demo": True,
        }
        for name, enabled in DEMO_PLUGIN_ROWS
    ]


def _status_text(row: Mapping[str, object]) -> str:
    enabled = bool(row.get("enabled", False))
    status = str(row.get("status", "")).lower()
    if not enabled:
        return "Disabled"
    if status and status not in {"ok", "unknown"}:
        return f"Enabled · {status}"
    return "Enabled"


def _dynamic_row_object_name(name: str) -> str:
    slug = "".join(char if char.isalnum() else "_" for char in name).strip("_")
    return f"oswPluginRow_{slug or 'plugin'}"
