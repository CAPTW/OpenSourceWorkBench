from __future__ import annotations

from osw.experimental.optional_solvers import (
    OptionalSolverRefreshAction,
    OptionalSolverRefreshState,
    build_optional_solver_refresh_status_viewmodel,
)


def _action_enabled(state: OptionalSolverRefreshState, action: OptionalSolverRefreshAction):
    status = build_optional_solver_refresh_status_viewmodel(state=state)
    return next(item.enabled for item in status.actions if item.action == action)


def test_builds_all_refresh_states() -> None:
    expected_status = {
        OptionalSolverRefreshState.IDLE: "Refresh idle.",
        OptionalSolverRefreshState.PENDING: "Passive discovery refresh pending.",
        OptionalSolverRefreshState.RUNNING: "Passive discovery refresh running.",
        OptionalSolverRefreshState.COMPLETED: "Passive discovery refresh completed.",
        OptionalSolverRefreshState.FAILED: "Passive discovery refresh failed.",
        OptionalSolverRefreshState.CANCELED: "Passive discovery refresh canceled.",
        OptionalSolverRefreshState.STALE_IGNORED: (
            "Stale passive discovery refresh result ignored."
        ),
    }

    for state, phrase in expected_status.items():
        status = build_optional_solver_refresh_status_viewmodel(state=state)
        assert status.state == state
        assert phrase in status.status_text
        assert status.not_validation_evidence is True


def test_action_states_mark_unsafe_actions_unavailable() -> None:
    status = build_optional_solver_refresh_status_viewmodel()
    actions = {item.action: item for item in status.actions}

    assert actions[OptionalSolverRefreshAction.RUN_VALIDATION].available is False
    assert actions[OptionalSolverRefreshAction.INSTALL_SOLVER].available is False
    assert actions[OptionalSolverRefreshAction.CLOSE_ISSUE].available is False
    assert actions[OptionalSolverRefreshAction.RUN_VALIDATION].enabled is False
    assert actions[OptionalSolverRefreshAction.INSTALL_SOLVER].enabled is False
    assert actions[OptionalSolverRefreshAction.CLOSE_ISSUE].enabled is False


def test_refresh_and_cancel_availability_follow_state() -> None:
    assert _action_enabled(
        OptionalSolverRefreshState.IDLE,
        OptionalSolverRefreshAction.REFRESH_PASSIVE_DISCOVERY,
    )
    assert not _action_enabled(
        OptionalSolverRefreshState.RUNNING,
        OptionalSolverRefreshAction.REFRESH_PASSIVE_DISCOVERY,
    )
    assert _action_enabled(
        OptionalSolverRefreshState.RUNNING,
        OptionalSolverRefreshAction.CANCEL_REFRESH,
    )
    assert not _action_enabled(
        OptionalSolverRefreshState.IDLE,
        OptionalSolverRefreshAction.CANCEL_REFRESH,
    )
