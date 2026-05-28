from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_calculix_deck_dialog_object_names(app: object) -> None:
    from osw.gui.dialogs.calculix_deck_dialog import CalculixDeckDialog
    from osw.solvers.calculix.adapter import create_calculix_deck

    dialog = CalculixDeckDialog(result=create_calculix_deck(options={"demo": "cantilever"}))

    assert dialog.objectName() == "oswCalculixDeckDialog"
    assert dialog.deck_preview.objectName() == "oswCalculixDeckPreview"
    assert dialog.diagnostics_list.objectName() == "oswCalculixReadinessDiagnostics"
    assert dialog.write_deck_button.objectName() == "oswCalculixWriteDeckButton"
    assert dialog.close_button.objectName() == "oswCalculixCloseButton"
    assert "*HEADING" in dialog.deck_preview.toPlainText()


def test_calculix_deck_dialog_writes_deck_without_ccx(app: object, tmp_path: Path) -> None:
    from osw.gui.dialogs.calculix_deck_dialog import CalculixDeckDialog
    from osw.solvers.calculix.adapter import create_calculix_deck

    output_path = tmp_path / "cantilever.inp"
    dialog = CalculixDeckDialog(
        result=create_calculix_deck(options={"demo": "cantilever"}),
        output_path=output_path,
    )
    written = dialog.write_deck()

    assert written == output_path
    assert output_path.exists()
    assert "*CLOAD" in output_path.read_text(encoding="utf-8")


def test_calculix_deck_dialog_theme_switching(app: object) -> None:
    from osw.gui.dialogs.calculix_deck_dialog import CalculixDeckDialog
    from osw.gui.theme_tokens import get_theme_tokens
    from osw.solvers.calculix.adapter import create_calculix_deck

    dialog = CalculixDeckDialog(result=create_calculix_deck(options={"demo": "cantilever"}))

    dialog.set_theme_tokens(get_theme_tokens("dark"))
    dialog.set_theme_tokens(get_theme_tokens("light"))
    assert dialog.styleSheet()
