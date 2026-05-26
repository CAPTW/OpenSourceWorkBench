"""Runtime theme management for the optional PySide6 GUI."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from osw.gui.theme_tokens import (
    ThemeMode,
    ThemeTokens,
    get_theme_tokens,
    normalize_theme_mode,
)

SETTINGS_ORGANIZATION = "OpenSolver"
SETTINGS_APPLICATION = "OpenSolver Workbench"
THEME_SETTINGS_KEY = "appearance/theme_mode"

ThemeCallback = Callable[[ThemeTokens], None]

_FALLBACK_SETTINGS: dict[str, str] = {}


def build_stylesheet(tokens: ThemeTokens) -> str:
    """Build theme-aware QSS from semantic tokens."""

    return f"""
QMainWindow {{
    background-color: {tokens.bg_app};
    color: {tokens.text_primary};
}}

QWidget {{
    background-color: {tokens.bg_panel};
    color: {tokens.text_primary};
    font-family: "Segoe UI", "Inter", "Noto Sans", "Arial", sans-serif;
    font-size: 10pt;
    selection-background-color: {tokens.primary};
    selection-color: {tokens.text_primary};
}}

QFrame {{
    background-color: {tokens.bg_panel};
    border: 1px solid {tokens.border};
}}

QLabel {{
    background: transparent;
    color: {tokens.text_primary};
    border: none;
}}

QPushButton, QToolButton {{
    background-color: {tokens.bg_panel_alt};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border};
    border-radius: 4px;
    padding: 4px 8px;
}}

QPushButton:hover, QToolButton:hover {{
    background-color: {tokens.primary_hover};
    border-color: {tokens.border_strong};
}}

QPushButton:pressed, QToolButton:pressed {{
    background-color: {tokens.primary};
}}

QPushButton:disabled, QToolButton:disabled {{
    background-color: {tokens.bg_header};
    color: {tokens.text_muted};
    border-color: {tokens.border};
}}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
    background-color: {tokens.bg_viewport};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border};
    border-radius: 3px;
    padding: 3px 6px;
}}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {tokens.accent};
}}

QComboBox QAbstractItemView {{
    background-color: {tokens.bg_panel};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border_strong};
    selection-background-color: {tokens.primary};
}}

QTreeWidget, QTreeView, QTableWidget, QTableView {{
    background-color: {tokens.bg_panel};
    alternate-background-color: {tokens.bg_panel_alt};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border};
    gridline-color: {tokens.border};
    selection-background-color: {tokens.primary};
    selection-color: {tokens.text_primary};
}}

QHeaderView::section {{
    background-color: {tokens.bg_header};
    color: {tokens.text_secondary};
    border: 1px solid {tokens.border};
    padding: 4px 6px;
}}

QTabWidget::pane {{
    border: 1px solid {tokens.border};
    background-color: {tokens.bg_panel};
}}

QTabBar::tab {{
    background-color: {tokens.bg_header};
    color: {tokens.text_secondary};
    border: 1px solid {tokens.border};
    padding: 5px 10px;
}}

QTabBar::tab:selected {{
    background-color: {tokens.bg_panel_alt};
    color: {tokens.text_primary};
    border-bottom-color: {tokens.primary};
}}

QGroupBox {{
    background-color: {tokens.bg_panel};
    border: 1px solid {tokens.border};
    border-radius: 4px;
    margin-top: 10px;
    padding: 8px;
}}

QGroupBox::title {{
    color: {tokens.text_secondary};
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}}

QSplitter::handle {{
    background-color: {tokens.border};
}}

QProgressBar {{
    background-color: {tokens.bg_viewport};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border};
    border-radius: 3px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {tokens.success};
    border-radius: 2px;
}}

QScrollBar:vertical, QScrollBar:horizontal {{
    background-color: {tokens.bg_header};
    border: 1px solid {tokens.border};
    margin: 0;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background-color: {tokens.border_strong};
    border-radius: 3px;
    min-height: 24px;
    min-width: 24px;
}}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
    background-color: {tokens.primary_hover};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    background: transparent;
    border: none;
    width: 0;
    height: 0;
}}

QMenuBar {{
    background-color: {tokens.bg_header};
    color: {tokens.text_primary};
    border-bottom: 1px solid {tokens.border};
}}

QMenuBar::item:selected {{
    background-color: {tokens.bg_panel_alt};
}}

QMenu {{
    background-color: {tokens.bg_panel};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border_strong};
}}

QMenu::item:selected {{
    background-color: {tokens.primary};
}}

QStatusBar {{
    background-color: {tokens.bg_header};
    color: {tokens.text_secondary};
    border-top: 1px solid {tokens.border};
}}

QToolTip {{
    background-color: {tokens.bg_panel_alt};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border_strong};
}}
""".strip()


class ThemeManager:
    """Load, persist, apply, and broadcast the active GUI theme."""

    def __init__(
        self,
        mode: ThemeMode | str | None = None,
        *,
        settings: Any | None = None,
        settings_key: str = THEME_SETTINGS_KEY,
        auto_load: bool = True,
    ) -> None:
        self._current_mode = normalize_theme_mode(mode, default=ThemeMode.DARK)
        self._settings = settings
        self._settings_key = settings_key
        self._callbacks: list[ThemeCallback] = []
        self._app: Any | None = None
        self._last_stylesheet = ""
        if mode is None and auto_load:
            self.load_settings()

    @property
    def current_mode(self) -> ThemeMode:
        return self._current_mode

    @property
    def resolved_mode(self) -> ThemeMode:
        if self._current_mode is ThemeMode.SYSTEM:
            return self.detect_system_theme()
        return self._current_mode

    @property
    def resolved_theme(self) -> ThemeMode:
        return self.resolved_mode

    @property
    def current_tokens(self) -> ThemeTokens:
        return get_theme_tokens(self.resolved_mode)

    @property
    def last_stylesheet(self) -> str:
        return self._last_stylesheet

    def set_mode(
        self,
        mode: ThemeMode | str,
        *,
        save: bool = True,
        notify: bool = True,
    ) -> ThemeMode:
        self._current_mode = normalize_theme_mode(mode)
        if save:
            self.save_settings()
        if self._app is not None:
            self.apply_to_app(self._app)
        if notify:
            self._notify()
        return self._current_mode

    def apply_to_app(self, app: Any | None = None) -> str:
        """Apply the current theme to a QApplication-like object."""

        target = app or self._current_qapplication()
        stylesheet = build_stylesheet(self.current_tokens)
        self._last_stylesheet = stylesheet
        if target is not None:
            if hasattr(target, "setStyleSheet"):
                target.setStyleSheet(stylesheet)
            self._apply_palette(target, self.current_tokens)
            self._app = target
        return stylesheet

    def load_settings(self) -> ThemeMode:
        stored_value = self._read_setting()
        try:
            self._current_mode = normalize_theme_mode(
                stored_value,
                default=ThemeMode.DARK,
            )
        except ValueError:
            self._current_mode = ThemeMode.DARK
        return self._current_mode

    def save_settings(self) -> None:
        self._write_setting(self._current_mode.value)

    def detect_system_theme(self) -> ThemeMode:
        """Resolve the OS theme without creating a QApplication."""

        try:
            from PySide6 import QtCore, QtGui, QtWidgets
        except ModuleNotFoundError:
            return ThemeMode.DARK

        try:
            app = QtGui.QGuiApplication.instance()
            if app is not None:
                style_hints = app.styleHints()
                color_scheme = style_hints.colorScheme()
                if color_scheme == QtCore.Qt.ColorScheme.Dark:
                    return ThemeMode.DARK
                if color_scheme == QtCore.Qt.ColorScheme.Light:
                    return ThemeMode.LIGHT
                scheme_name = getattr(color_scheme, "name", "").lower()
                if "dark" in scheme_name:
                    return ThemeMode.DARK
                if "light" in scheme_name:
                    return ThemeMode.LIGHT
        except (AttributeError, RuntimeError, TypeError):
            pass

        try:
            app = QtWidgets.QApplication.instance()
            if app is not None:
                window_color = app.palette().color(QtGui.QPalette.ColorRole.Window)
                return ThemeMode.DARK if window_color.lightness() < 128 else ThemeMode.LIGHT
        except (AttributeError, RuntimeError, TypeError):
            pass

        return ThemeMode.DARK

    def subscribe(self, callback: ThemeCallback) -> Callable[[], None]:
        self._callbacks.append(callback)

        def unsubscribe() -> None:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

        return unsubscribe

    def _notify(self) -> None:
        tokens = self.current_tokens
        for callback in list(self._callbacks):
            callback(tokens)

    def _read_setting(self) -> Any | None:
        settings = self._settings_backend()
        if isinstance(settings, dict):
            return settings.get(self._settings_key)
        if hasattr(settings, "value"):
            return settings.value(self._settings_key, None)
        return None

    def _write_setting(self, value: str) -> None:
        settings = self._settings_backend()
        if isinstance(settings, dict):
            settings[self._settings_key] = value
            return
        if hasattr(settings, "setValue"):
            settings.setValue(self._settings_key, value)
        if hasattr(settings, "sync"):
            settings.sync()

    def _settings_backend(self) -> Any:
        if self._settings is not None:
            return self._settings
        qsettings = self._make_qsettings()
        if qsettings is not None:
            self._settings = qsettings
            return self._settings
        return _FALLBACK_SETTINGS

    @staticmethod
    def _make_qsettings() -> Any | None:
        try:
            from PySide6 import QtCore
        except ModuleNotFoundError:
            return None
        return QtCore.QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)

    @staticmethod
    def _current_qapplication() -> Any | None:
        try:
            from PySide6 import QtWidgets
        except ModuleNotFoundError:
            return None
        return QtWidgets.QApplication.instance()

    @staticmethod
    def _apply_palette(app: Any, tokens: ThemeTokens) -> None:
        try:
            from PySide6 import QtGui
        except ModuleNotFoundError:
            return

        if not hasattr(app, "palette") or not hasattr(app, "setPalette"):
            return

        palette = app.palette()
        role = QtGui.QPalette.ColorRole
        palette.setColor(role.Window, QtGui.QColor(tokens.bg_app))
        palette.setColor(role.WindowText, QtGui.QColor(tokens.text_primary))
        palette.setColor(role.Base, QtGui.QColor(tokens.bg_panel))
        palette.setColor(role.AlternateBase, QtGui.QColor(tokens.bg_panel_alt))
        palette.setColor(role.Text, QtGui.QColor(tokens.text_primary))
        palette.setColor(role.Button, QtGui.QColor(tokens.bg_panel_alt))
        palette.setColor(role.ButtonText, QtGui.QColor(tokens.text_primary))
        palette.setColor(role.Highlight, QtGui.QColor(tokens.primary))
        palette.setColor(role.HighlightedText, QtGui.QColor(tokens.text_primary))
        palette.setColor(role.ToolTipBase, QtGui.QColor(tokens.bg_panel_alt))
        palette.setColor(role.ToolTipText, QtGui.QColor(tokens.text_primary))
        app.setPalette(palette)
