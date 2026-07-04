"""Shared PySide6 lifecycle fixtures for OSW GUI tests.

Broad ``python -m pytest tests/gui -q`` runs every GUI test in one process that
shares a single ``QApplication``. GUI tests instantiate ``MainWindow`` and its
dialogs -- each ``MainWindow`` builds many nested top-level widgets -- but the
file-local ``app`` fixtures never closed or deleted those widgets. Qt keeps the
underlying C++ objects alive (and queues their ``DeferredDelete`` events) until
an event loop drains them, so top-level widgets accumulate across test order
until the aggregate run stalls. The per-file fallback avoids this only because
each file exits its own process and releases every Qt resource.

This conftest adds an autouse cleanup fixture that, after each GUI test, closes
leftover top-level widgets, schedules their deletion, and flushes Qt's
``DeferredDelete`` queue -- deterministically, with bounded iteration and no
sleeps. It is a test-only lifecycle helper: it changes no product behavior, it
never fails a passing test, and it skips cleanly when PySide6 is unavailable.
"""

from __future__ import annotations

import importlib.util
import os

import pytest

# Match the file-local GUI test modules: force the headless Qt platform before
# any QApplication is created so the shared cleanup never opens a real display.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

# Deleting a top-level widget can enqueue further child/dialog deletions, so a
# few bounded close/deleteLater + DeferredDelete passes are needed to converge.
# The loop also exits early as soon as no top-level widgets remain, so healthy
# tests pay only a single pass.
_MAX_DRAIN_PASSES = 8


def drain_top_level_widgets(max_passes: int = _MAX_DRAIN_PASSES) -> int:
    """Close and delete leftover top-level widgets, draining deferred deletes.

    Returns the number of top-level widgets still present after draining, so
    callers and focused tests can assert the shell returned to its baseline.
    Safe to call when PySide6 is missing or no ``QApplication`` exists (both
    return ``0``). The routine only reclaims resources; it never raises for an
    already-deleted widget, so it cannot turn a passing test into a failure.
    """
    if not PYSIDE6_AVAILABLE:
        return 0

    from PySide6 import QtCore, QtWidgets

    app = QtWidgets.QApplication.instance()
    if app is None:
        return 0

    for _ in range(max_passes):
        top_level = QtWidgets.QApplication.topLevelWidgets()
        if not top_level:
            break

        for widget in top_level:
            try:
                widget.close()
            except RuntimeError:
                # The widget's C++ object was already deleted; nothing to close.
                continue

        app.processEvents()

        for widget in QtWidgets.QApplication.topLevelWidgets():
            try:
                widget.deleteLater()
            except RuntimeError:
                continue

        # Flush queued DeferredDelete events so the C++ widgets are destroyed
        # now instead of accumulating across the whole session, then let any
        # follow-up deletions post before the next pass.
        QtCore.QCoreApplication.sendPostedEvents(
            None, QtCore.QEvent.Type.DeferredDelete
        )
        app.processEvents()

    return len(QtWidgets.QApplication.topLevelWidgets())


@pytest.fixture(scope="session")
def qapp() -> object:
    """Provide the shared headless ``QApplication`` for GUI tests.

    Mirrors the file-local ``app`` fixtures but at session scope so focused
    lifecycle tests can share one application instance.
    """
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")

    from PySide6 import QtWidgets

    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def drain_gui_widgets() -> object:
    """Expose :func:`drain_top_level_widgets` as a fixture for focused tests."""
    return drain_top_level_widgets


@pytest.fixture(autouse=True)
def _cleanup_top_level_widgets_after_test() -> object:
    """Autouse: drain leftover Qt widgets after every GUI test.

    Runs regardless of how each test obtained its ``QApplication`` (the app is a
    process singleton). Cleanup happens on teardown, after the test body and its
    own fixtures, so it only reclaims resources a passing test left behind and
    never hides a real assertion failure.
    """
    yield
    drain_top_level_widgets()
