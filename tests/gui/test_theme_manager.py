from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtCore, QtWidgets
else:
    QtCore = None
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_theme_manager_can_instantiate() -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.theme_tokens import ThemeMode

    manager = ThemeManager(auto_load=False)

    assert manager.current_mode is ThemeMode.DARK


def test_set_mode_updates_current_tokens() -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.theme_tokens import DARK_TOKENS, LIGHT_TOKENS, ThemeMode

    manager = ThemeManager(auto_load=False)

    manager.set_mode("light", save=False)
    assert manager.current_mode is ThemeMode.LIGHT
    assert manager.current_tokens is LIGHT_TOKENS

    manager.set_mode("dark", save=False)
    assert manager.current_mode is ThemeMode.DARK
    assert manager.current_tokens is DARK_TOKENS


def test_system_mode_stores_system_and_resolves_safely() -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.theme_tokens import ThemeMode

    manager = ThemeManager(auto_load=False)

    manager.set_mode("system", save=False)

    assert manager.current_mode is ThemeMode.SYSTEM
    assert manager.resolved_mode in {ThemeMode.DARK, ThemeMode.LIGHT}


def test_apply_to_app_sets_non_empty_stylesheet(app: object) -> None:
    from osw.gui.theme import ThemeManager

    manager = ThemeManager(auto_load=False)

    stylesheet = manager.apply_to_app(app)

    assert "QMainWindow" in stylesheet
    assert app.styleSheet() == stylesheet


def test_settings_persistence_round_trips_mode(tmp_path: object) -> None:
    assert QtCore is not None
    from osw.gui.theme import ThemeManager
    from osw.gui.theme_tokens import ThemeMode

    settings_path = tmp_path / "theme.ini"
    settings = QtCore.QSettings(str(settings_path), QtCore.QSettings.Format.IniFormat)
    first = ThemeManager(settings=settings, auto_load=False)
    first.set_mode(ThemeMode.SYSTEM)

    second_settings = QtCore.QSettings(
        str(settings_path),
        QtCore.QSettings.Format.IniFormat,
    )
    second = ThemeManager(settings=second_settings)

    assert second.current_mode is ThemeMode.SYSTEM


def test_theme_change_callback_fires() -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.theme_tokens import LIGHT_TOKENS

    manager = ThemeManager(auto_load=False)
    observed = []
    manager.subscribe(observed.append)

    manager.set_mode("light", save=False)

    assert observed == [LIGHT_TOKENS]


def test_theme_selector_applies_selection_immediately(app: object) -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.theme_tokens import ThemeMode
    from osw.gui.widgets.theme_selector import ThemeSelector

    manager = ThemeManager(auto_load=False)
    selector = ThemeSelector(theme_manager=manager)

    selector.set_mode(ThemeMode.LIGHT)

    assert manager.current_mode is ThemeMode.LIGHT
    assert app.styleSheet()
