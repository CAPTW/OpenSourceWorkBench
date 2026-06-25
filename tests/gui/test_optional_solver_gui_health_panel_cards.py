from __future__ import annotations

import importlib.util
import os

import pytest
from tests.gui.test_optional_solver_gui_health_panel import (
    sample_optional_solver_health_view_model,
)

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


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_stack_cards_render_all_supplied_stacks(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    cards = panel.stack_card_texts()

    assert len(cards) == 3
    assert any("gmsh | Gmsh | #6 | health=missing" in card for card in cards)
    assert any(
        "calculix | CalculiX ccx | #8 | health=partially_installed" in card
        for card in cards
    )
    assert any(
        "pyvista_meshio | PyVista / meshio | #11 | health=discovered" in card
        for card in cards
    )


def test_stack_cards_render_issue_health_support_and_counts(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    joined = "\n".join(panel.stack_card_texts())

    assert "support=experimental" in joined
    assert "missing=1" in joined
    assert "diagnostics=1" in joined
    assert "non-bundled" in joined
    assert "selected" in joined
