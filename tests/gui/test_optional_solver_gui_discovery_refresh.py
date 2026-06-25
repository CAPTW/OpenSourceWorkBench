from __future__ import annotations

import importlib.util
import json
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


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _manifest(stack_id: str, issue: int):
    from osw.experimental.optional_solvers import parse_optional_solver_manifest_dict

    return parse_optional_solver_manifest_dict(
        {
            "stack_id": stack_id,
            "display_name": stack_id.title(),
            "related_issue": issue,
            "capabilities": [{"capability_id": "example", "description": "Example"}],
            "executable_requirements": [
                {"identifier": f"{stack_id}-tool", "display_name": "Example Tool"}
            ],
            "prepared_machine_notes": ["Use a prepared machine."],
            "documentation_refs": ["docs/example.md"],
            "support_status": "experimental",
            "non_bundled_disclaimer": "External solvers are not bundled.",
            "safety_notes": ["No solver execution.", "No dependency install."],
        }
    )


def _stack(stack_id: str, state: str, issue: int):
    from osw.experimental.optional_solvers import (
        OptionalSolverExecutableDiscovery,
        OptionalSolverHealthState,
        OptionalSolverStackDiscovery,
    )

    active_state = OptionalSolverHealthState.from_value(state)
    found = active_state == OptionalSolverHealthState.DISCOVERED
    return OptionalSolverStackDiscovery(
        stack_id=stack_id,
        display_name=stack_id.title(),
        related_issue=issue,
        health_state=active_state,
        executables=(
            OptionalSolverExecutableDiscovery(
                identifier=f"{stack_id}-tool",
                display_name="Example Tool",
                required=True,
                found=found,
                redacted_path=f"<redacted:{stack_id}-tool.exe>" if found else "",
            ),
        ),
    )


def _report(*stacks):
    from osw.experimental.optional_solvers import OptionalSolverDiscoveryReport

    return OptionalSolverDiscoveryReport(
        stacks=tuple(stacks),
        generated_at="2026-06-25T00:00:00Z",
        source="gui-refresh-test",
    )


def _view_model():
    from osw.experimental.optional_solvers import build_optional_solver_health_panel_viewmodel

    manifests = (_manifest("alpha", 6), _manifest("beta", 7))
    return build_optional_solver_health_panel_viewmodel(
        manifests=manifests,
        discovery_reports=_report(
            _stack("alpha", "missing", 6),
            _stack("beta", "missing", 7),
        ),
        selected_stack_id="alpha",
    )


def _manifests():
    return (_manifest("alpha", 6), _manifest("beta", 7))


def test_refresh_action_exists_and_no_refresh_on_construction(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    calls = []

    def runner(request):
        calls.append(request.request_id)
        return _report(_stack("alpha", "discovered", 6), _stack("beta", "missing", 7))

    panel = OptionalSolverHealthPanel(
        _view_model(),
        refresh_runner=runner,
        refresh_manifests=_manifests(),
    )

    assert "refresh_passive_discovery" in panel.available_action_names()
    assert panel.refresh_action_enabled() is True
    assert "explicit user action" in panel.refresh_action_reason()
    assert panel.refresh_status_text() == "Refresh idle."
    assert panel.refresh_runner_call_count() == 0
    assert calls == []


def test_successful_injected_refresh_updates_summary_and_cards(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    calls = []

    def runner(request):
        calls.append(request.request_id)
        return _report(_stack("alpha", "discovered", 6), _stack("beta", "missing", 7))

    panel = OptionalSolverHealthPanel(
        _view_model(),
        refresh_runner=runner,
        refresh_manifests=_manifests(),
    )

    panel.trigger_refresh_for_test()

    assert len(calls) == 1
    assert panel.refresh_runner_call_count() == 1
    assert panel.refresh_request_id() == calls[0]
    assert "discovered=1" in panel.current_summary_text()
    assert any(
        "alpha | Alpha | #6 | health=discovered" in card
        for card in panel.current_stack_card_texts()
    )
    assert "completed" in panel.refresh_status_text().lower()
    assert "not_validation_evidence=true" in panel.refresh_result_summary_text()
    assert panel.refresh_error_text() == ""


def test_export_after_refresh_uses_refreshed_view_model(app: object, tmp_path) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    target = tmp_path / "summary.json"

    def runner(_request):
        return _report(_stack("alpha", "discovered", 6), _stack("beta", "missing", 7))

    panel = OptionalSolverHealthPanel(
        _view_model(),
        refresh_runner=runner,
        refresh_manifests=_manifests(),
        save_path_chooser=lambda _panel: target,
        export_generated_at="2026-06-25T00:00:00Z",
    )

    panel.trigger_refresh_for_test()
    panel.export_summary_button.click()

    payload = json.loads(target.read_text(encoding="utf-8"))
    alpha = next(stack for stack in payload["stacks"] if stack["stack_id"] == "alpha")
    assert alpha["health_state"] == "discovered"
    assert payload["not_validation_evidence"] is True
