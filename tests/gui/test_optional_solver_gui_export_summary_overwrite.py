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


def test_overwrite_is_rejected_by_default(app: object, tmp_path) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    target = tmp_path / "summary.json"
    target.write_text("existing", encoding="utf-8")
    confirm_paths: list[str] = []

    def reject(path: str) -> bool:
        confirm_paths.append(path)
        return False

    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: target,
        overwrite_confirmer=reject,
    )

    panel.export_summary_button.click()

    assert confirm_paths == [str(target)]
    assert target.read_text(encoding="utf-8") == "existing"
    assert panel.export_status_text() == "Export not written."
    assert "OSE_OVERWRITE_BLOCKED" in panel.export_error_text()


def test_overwrite_writes_only_after_injected_confirmation(app: object, tmp_path) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    target = tmp_path / "summary.json"
    target.write_text("existing", encoding="utf-8")
    confirm_paths: list[str] = []

    def accept(path: str) -> bool:
        confirm_paths.append(path)
        return True

    panel = OptionalSolverHealthPanel(
        sample_optional_solver_health_view_model(),
        save_path_chooser=lambda _panel: target,
        overwrite_confirmer=accept,
    )

    panel.export_summary_button.click()

    content = target.read_text(encoding="utf-8")
    assert confirm_paths == [str(target)]
    assert content != "existing"
    assert '"not_validation_evidence": true' in content
    assert sorted(path.name for path in tmp_path.iterdir()) == ["summary.json"]
    assert panel.export_error_text() == ""
    assert panel.last_export_path() == str(target)
