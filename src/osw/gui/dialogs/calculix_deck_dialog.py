"""Theme-aware CalculiX input deck preview dialog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class CalculixDeckDialog(_BaseDialog):
    """Preview and write CalculiX `.inp` text without running `ccx`."""

    if QtCore is not None:
        deckWritten = QtCore.Signal(str)

    def __init__(
        self,
        parent: object | None = None,
        *,
        result: object | None = None,
        theme_tokens: ThemeTokens | None = None,
        output_path: str | Path = Path("artifacts") / "calculix" / "cantilever.inp",
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswCalculixDeckDialog")
        self.setWindowTitle("Generate CalculiX Input Deck")
        self.resize(920, 720)
        self._tokens = theme_tokens or DARK_TOKENS
        self.output_path = Path(output_path)
        self.result = result

        layout = QtWidgets.QVBoxLayout(self)
        self.deck_preview = QtWidgets.QPlainTextEdit(self)
        self.deck_preview.setObjectName("oswCalculixDeckPreview")
        self.deck_preview.setReadOnly(True)
        layout.addWidget(self.deck_preview, 1)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswCalculixReadinessDiagnostics")
        layout.addWidget(self.diagnostics_list)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.write_deck_button = QtWidgets.QPushButton("Write Deck", self)
        self.write_deck_button.setObjectName("oswCalculixWriteDeckButton")
        self.close_button = QtWidgets.QPushButton("Close", self)
        self.close_button.setObjectName("oswCalculixCloseButton")
        buttons.addWidget(self.write_deck_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

        self.write_deck_button.clicked.connect(self.write_deck)
        self.close_button.clicked.connect(self.close)
        self.set_theme_tokens(self._tokens)
        if self.result is not None:
            self.set_deck_result(self.result)
        else:
            self.deck_preview.setPlainText("")
            self.diagnostics_list.addItem("INFO project: No CalculiX deck preview loaded.")
            self.write_deck_button.setEnabled(False)

    def set_deck_result(self, result: object) -> None:
        self.result = result
        self.deck_preview.setPlainText(str(getattr(result, "input_text", "") or ""))
        self.diagnostics_list.clear()
        for item in getattr(result, "diagnostics", ()) or ():
            if isinstance(item, dict):
                severity = str(item.get("severity", "")).upper()
                path = str(item.get("path", ""))
                message = str(item.get("message", ""))
                self.diagnostics_list.addItem(f"{severity} {path}: {message}")
        self.write_deck_button.setEnabled(bool(getattr(result, "input_text", "")))

    def write_deck(self) -> Path | None:
        text = str(self.deck_preview.toPlainText())
        if not text:
            return None
        output_path = self.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        self.deckWritten.emit(str(output_path))
        return output_path

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswCalculixDeckDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QPlainTextEdit, QListWidget {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "}"
            "QPushButton {"
            f"background-color: {tokens.accent};"
            f"color: {tokens.bg_app};"
            f"border: 1px solid {tokens.primary_hover};"
            "padding: 6px 12px;"
            "}"
        )
