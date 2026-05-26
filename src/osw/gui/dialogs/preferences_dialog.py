"""Preferences dialog entry point for runtime appearance settings."""

from __future__ import annotations

from osw.gui.qt_compat import require_qt_widgets
from osw.gui.theme import ThemeManager
from osw.gui.widgets.theme_selector import ThemeSelector

QtCore, QtWidgets = require_qt_widgets()


class PreferencesDialog(QtWidgets.QDialog):
    """Compact preferences dialog with an Appearance section."""

    def __init__(
        self,
        *,
        theme_manager: ThemeManager | None = None,
        parent: object | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("preferencesDialog")
        self.setWindowTitle("Preferences")
        self.theme_manager = theme_manager or ThemeManager()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        appearance = QtWidgets.QGroupBox("Appearance", self)
        appearance.setObjectName("preferencesAppearanceGroup")
        appearance_layout = QtWidgets.QVBoxLayout(appearance)
        self.theme_selector = ThemeSelector(theme_manager=self.theme_manager, parent=appearance)
        appearance_layout.addWidget(self.theme_selector)
        layout.addWidget(appearance)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close,
            parent=self,
        )
        buttons.setObjectName("preferencesDialogButtons")
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
