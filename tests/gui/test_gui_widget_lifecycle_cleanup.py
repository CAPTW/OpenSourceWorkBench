"""Regression tests for the shared GUI test lifecycle cleanup.

These prove the drain helper and autouse fixture in ``tests/gui/conftest.py``
actually reclaim top-level widgets. Reclaiming them is what keeps broad
``pytest tests/gui`` from stalling as ``MainWindow`` instances accumulate across
the single shared ``QApplication``.
"""

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
    from PySide6 import QtWidgets
else:
    QtWidgets = None


def _top_level_count() -> int:
    assert QtWidgets is not None
    return len(QtWidgets.QApplication.topLevelWidgets())


def test_drain_returns_main_window_widgets_to_baseline(qapp: object, drain_gui_widgets) -> None:
    from osw.gui.main_window import MainWindow

    # Establish the allowed baseline for this test in the shared application.
    baseline = drain_gui_widgets()

    window = MainWindow()

    assert window.objectName() == "oswMainWindow"
    # A MainWindow builds many nested top-level widgets, so it must grow the count.
    assert _top_level_count() > baseline

    remaining = drain_gui_widgets()

    # Cleanup returns the shared application to (or below) its baseline.
    assert remaining <= baseline


def test_repeated_main_window_creation_does_not_accumulate(
    qapp: object, drain_gui_widgets
) -> None:
    from osw.gui.main_window import MainWindow

    baseline = drain_gui_widgets()

    remaining_counts: list[int] = []
    for _ in range(4):
        window = MainWindow()
        # Each fresh window grows the top-level widget count before draining.
        assert _top_level_count() > baseline
        del window
        remaining_counts.append(drain_gui_widgets())

    # Every iteration drains back to (or below) the baseline: no monotonic
    # accumulation of top-level widgets across repeated MainWindow construction.
    assert max(remaining_counts) <= baseline


def test_drain_is_idempotent_when_no_widgets_remain(qapp: object, drain_gui_widgets) -> None:
    # Draining a clean application is a safe no-op that stays at the baseline
    # count, so the autouse teardown cannot destabilize back-to-back tests.
    baseline = drain_gui_widgets()
    assert drain_gui_widgets() == baseline
