from __future__ import annotations

from tests.unit.test_optional_solver_plugin_manifest_gui_viewmodel import (
    valid_project_report,
)

from osw.experimental.optional_solvers import (
    OptionalSolverPluginManifestAction,
    build_optional_solver_plugin_manifest_gui_viewmodel,
)


def _actions_by_id():
    view_model = build_optional_solver_plugin_manifest_gui_viewmodel(
        valid_project_report()
    )
    return {state.action: state for state in view_model.actions}


def test_action_states_mark_file_choice_as_future_display_only() -> None:
    actions = _actions_by_id()
    action = actions[OptionalSolverPluginManifestAction.CHOOSE_EXPLICIT_JSON_FILES]

    assert action.available is True
    assert action.enabled is False
    assert "file dialogs are not implemented" in action.reason.lower()


def test_action_states_mark_activation_unavailable() -> None:
    actions = _actions_by_id()
    action = actions[OptionalSolverPluginManifestAction.ACTIVATE_MANIFEST]

    assert action.available is False
    assert action.enabled is False
    assert "separate future gate" in action.reason.lower()


def test_action_states_mark_discovery_validation_install_and_issue_unavailable() -> None:
    actions = _actions_by_id()

    for action_id in (
        OptionalSolverPluginManifestAction.RUN_DISCOVERY_WITH_PLUGIN_MANIFESTS,
        OptionalSolverPluginManifestAction.RUN_VALIDATION,
        OptionalSolverPluginManifestAction.INSTALL_SOLVER,
        OptionalSolverPluginManifestAction.CLOSE_ISSUE,
    ):
        assert actions[action_id].available is False
        assert actions[action_id].enabled is False

    assert "osw-valid gate" in actions[
        OptionalSolverPluginManifestAction.RUN_VALIDATION
    ].reason.lower()
    assert "unavailable" in actions[
        OptionalSolverPluginManifestAction.INSTALL_SOLVER
    ].reason.lower()
    assert "closure gate" in actions[
        OptionalSolverPluginManifestAction.CLOSE_ISSUE
    ].reason.lower()
