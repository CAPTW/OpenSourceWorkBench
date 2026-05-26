"""Material section for the right properties inspector."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

DEFAULT_MATERIAL_LIBRARY = "builtin"
DEFAULT_MATERIAL = "Aluminum 6061"
MATERIAL_LIBRARY_OPTIONS = ("builtin", "project", "user")
MATERIAL_OPTIONS = ("Aluminum 6061", "Steel AISI 304", "Copper", "Air", "Water")


class MaterialSection(_BaseWidget):
    """Compact mock material selector section."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswMaterialSection")
        self._tokens = DARK_TOKENS

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 7, 8, 8)
        layout.setSpacing(6)
        self.header_label = QtWidgets.QLabel("MATERIAL", self)
        self.header_label.setObjectName("oswMaterialSectionHeader")

        form = QtWidgets.QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)
        self.library_combo = QtWidgets.QComboBox(self)
        self.library_combo.setObjectName("oswMaterialLibraryCombo")
        self.library_combo.addItems(MATERIAL_LIBRARY_OPTIONS)
        self.library_combo.setCurrentText(DEFAULT_MATERIAL_LIBRARY)
        self.material_combo = QtWidgets.QComboBox(self)
        self.material_combo.setObjectName("oswMaterialCombo")
        self.material_combo.addItems(MATERIAL_OPTIONS)
        self.material_combo.setCurrentText(DEFAULT_MATERIAL)
        form.addRow("Material Library:", self.library_combo)
        form.addRow("Material:", self.material_combo)

        self.edit_button = QtWidgets.QPushButton("Edit Material...", self)
        self.edit_button.setObjectName("oswEditMaterialButton")
        self.edit_button.clicked.connect(self._record_edit_request)
        self.last_edit_request: str | None = None

        layout.addWidget(self.header_label)
        layout.addLayout(form)
        layout.addWidget(self.edit_button)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def title(self) -> str:
        return self.header_label.text()

    def current_material_library(self) -> str:
        return self.library_combo.currentText()

    def current_material(self) -> str:
        return self.material_combo.currentText()

    def set_material_library(self, name: str) -> None:
        if self.library_combo.findText(name) < 0:
            self.library_combo.addItem(name)
        self.library_combo.setCurrentText(name)

    def set_material(self, name: str) -> None:
        if self.material_combo.findText(name) < 0:
            self.material_combo.addItem(name)
        self.material_combo.setCurrentText(name)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(_section_stylesheet(tokens, "oswMaterialSection"))

    def _record_edit_request(self) -> None:
        self.last_edit_request = "placeholder"


def _section_stylesheet(tokens: ThemeTokens, object_name: str) -> str:
    return (
        f"QWidget#{object_name} {{"
        f"background-color: {tokens.bg_panel_alt};"
        f"border: 1px solid {tokens.border};"
        "border-radius: 4px;"
        "}"
        f"QWidget#{object_name} QLabel {{"
        f"color: {tokens.text_secondary};"
        "background: transparent;"
        "border: none;"
        "}"
        f"QWidget#{object_name} QLabel#oswMaterialSectionHeader {{"
        f"color: {tokens.accent};"
        "font-weight: 800;"
        "}"
    )
