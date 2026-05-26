"""Embeddable runtime theme selector."""

from __future__ import annotations

from osw.gui.qt_compat import require_qt_widgets
from osw.gui.theme import ThemeManager
from osw.gui.theme_tokens import ThemeMode, normalize_theme_mode

QtCore, QtWidgets = require_qt_widgets()


class ThemeSelector(QtWidgets.QWidget):
    """Small selector that applies and persists theme changes immediately."""

    modeChanged = QtCore.Signal(str)

    def __init__(
        self,
        *,
        theme_manager: ThemeManager | None = None,
        parent: object | None = None,
        auto_apply: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("themeSelector")
        self._theme_manager = theme_manager or ThemeManager()
        self._auto_apply = auto_apply

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QtWidgets.QLabel("Theme", self)
        label.setObjectName("themeSelectorLabel")
        self.combo_box = QtWidgets.QComboBox(self)
        self.combo_box.setObjectName("themeSelectorCombo")
        self.combo_box.addItem("Dark", ThemeMode.DARK.value)
        self.combo_box.addItem("Light", ThemeMode.LIGHT.value)
        self.combo_box.addItem("System", ThemeMode.SYSTEM.value)

        layout.addWidget(label)
        layout.addWidget(self.combo_box, 1)

        self._sync_from_manager()
        self.combo_box.currentIndexChanged.connect(self._on_selection_changed)
        self._theme_manager.subscribe(self._on_theme_changed)

    @property
    def theme_manager(self) -> ThemeManager:
        return self._theme_manager

    def set_mode(self, mode: ThemeMode | str) -> None:
        normalized = normalize_theme_mode(mode)
        index = self.combo_box.findData(normalized.value)
        if index >= 0 and index != self.combo_box.currentIndex():
            self.combo_box.setCurrentIndex(index)
            return
        self._apply_mode(normalized)

    def _on_selection_changed(self) -> None:
        data = self.combo_box.currentData()
        self._apply_mode(normalize_theme_mode(data))

    def _apply_mode(self, mode: ThemeMode) -> None:
        self._theme_manager.set_mode(mode)
        if self._auto_apply:
            self._theme_manager.apply_to_app(QtWidgets.QApplication.instance())
        self.modeChanged.emit(mode.value)

    def _on_theme_changed(self, _tokens: object) -> None:
        self._sync_from_manager()

    def _sync_from_manager(self) -> None:
        index = self.combo_box.findData(self._theme_manager.current_mode.value)
        if index < 0:
            return
        was_blocked = self.combo_box.blockSignals(True)
        self.combo_box.setCurrentIndex(index)
        self.combo_box.blockSignals(was_blocked)
