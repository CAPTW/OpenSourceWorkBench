"""Plugin status section for the right properties inspector."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
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
    """Compact plugin enabled-state list with safe placeholder action."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswPluginsSection")
        self._tokens = DARK_TOKENS
        self._plugins = {name: enabled for name, enabled in DEMO_PLUGIN_ROWS}
        self.plugin_widgets: dict[str, object] = {}
        self.status_labels: dict[str, object] = {}
        self.last_manage_report_request: str | None = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 7, 8, 8)
        layout.setSpacing(6)
        self.header_label = QtWidgets.QLabel("PLUGINS", self)
        self.header_label.setObjectName("oswPluginsHeader")
        layout.addWidget(self.header_label)

        for name, enabled in DEMO_PLUGIN_ROWS:
            row = QtWidgets.QFrame(self)
            row.setObjectName(PLUGIN_OBJECT_NAMES[name])
            row.setProperty("oswPluginRow", True)
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(7, 4, 7, 4)
            row_layout.setSpacing(6)
            name_label = QtWidgets.QLabel(name, row)
            status_label = QtWidgets.QLabel("Enabled" if enabled else "Disabled", row)
            status_label.setProperty("oswEnabledBadge", enabled)
            row_layout.addWidget(name_label, 1)
            row_layout.addWidget(status_label)
            layout.addWidget(row)
            self.plugin_widgets[name] = row
            self.status_labels[name] = status_label

        self.manage_report_button = QtWidgets.QPushButton("Manage Report...", self)
        self.manage_report_button.setObjectName("oswManageReportButton")
        self.manage_report_button.clicked.connect(self._record_manage_report_request)
        layout.addWidget(self.manage_report_button)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def plugin_rows(self) -> list[dict[str, bool | str]]:
        return [{"name": name, "enabled": enabled} for name, enabled in self._plugins.items()]

    def set_plugin_enabled(self, name: str, enabled: bool) -> None:
        if name not in self._plugins:
            return
        self._plugins[name] = enabled
        self.status_labels[name].setText("Enabled" if enabled else "Disabled")
        self.status_labels[name].setProperty("oswEnabledBadge", enabled)
        self.set_theme_tokens(self._tokens)

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
        )

    def _record_manage_report_request(self) -> None:
        self.last_manage_report_request = "placeholder"
