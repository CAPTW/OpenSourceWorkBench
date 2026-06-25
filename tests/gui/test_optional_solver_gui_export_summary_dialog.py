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


def test_cancelled_export_does_not_write_file(app: object, tmp_path) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: None,
    )

    panel.export_summary_button.click()

    assert list(tmp_path.iterdir()) == []
    assert panel.export_status_text() == "Export cancelled."
    assert panel.export_error_text() == ""
    assert panel.last_export_path() == ""
    assert panel.last_export_format() == ""


def test_markdown_export_writes_one_file(app: object, tmp_path) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    target = tmp_path / "summary.md"
    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: (target, "Markdown (*.md)"),
    )

    panel.export_summary_button.click()

    content = target.read_text(encoding="utf-8")
    assert sorted(path.name for path in tmp_path.iterdir()) == ["summary.md"]
    assert "# Optional Solver Health Summary" in content
    assert "Not validation evidence: True" in content
    assert "C:/Users/USER" not in content
    assert panel.last_export_format() == "markdown"


def test_text_export_writes_one_file(app: object, tmp_path) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    target = tmp_path / "summary.txt"
    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: (target, "Plain text (*.txt)"),
    )

    panel.export_summary_button.click()

    content = target.read_text(encoding="utf-8")
    assert sorted(path.name for path in tmp_path.iterdir()) == ["summary.txt"]
    assert "Optional Solver Health Summary" in content
    assert "Not validation evidence: True" in content
    assert "C:/Users/USER" not in content
    assert panel.last_export_format() == "text"


def test_missing_parent_is_rejected_without_write(app: object, tmp_path) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    target = tmp_path / "missing" / "summary.json"
    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: target,
    )

    panel.export_summary_button.click()

    assert not target.exists()
    assert panel.export_status_text() == "Export not written."
    assert "OSE_PARENT_MISSING" in panel.export_error_text()


def test_unsupported_extension_is_rejected_without_write(app: object, tmp_path) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    target = tmp_path / "summary.pdf"
    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: target,
    )

    panel.export_summary_button.click()

    assert not target.exists()
    assert panel.export_status_text() == "Export not written."
    assert "OSE_UNSUPPORTED_EXTENSION" in panel.export_error_text()
