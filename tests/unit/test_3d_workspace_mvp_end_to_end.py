"""Renderer-neutral complete 3D Workspace MVP user-journey acceptance."""

from __future__ import annotations

from pathlib import Path

from tests.helpers.workspace_3d_mvp_e2e import (
    NS_BAD,
    ActionCounters,
    e2e_mesh,
    mesh_snapshot,
    run_renderer_neutral_author_journey,
    run_renderer_neutral_restore_journey,
    run_renderer_neutral_stale_journey,
    workspace_paths,
)

from osw.core.project_io import load_project
from osw.core.workspace_3d import ACTIVE_SCENE_SCHEMA, ActiveSceneRestoreStatus
from osw.mesh.identity import compute_mesh_fingerprint


def test_complete_renderer_neutral_mvp_user_journey(tmp_path: Path) -> None:
    workspace = tmp_path / "e2e"
    workspace.mkdir()
    counters = ActionCounters()
    authored = run_renderer_neutral_author_journey(workspace, counters=counters)
    restored = run_renderer_neutral_restore_journey(workspace, counters=counters)
    stale = run_renderer_neutral_stale_journey(workspace, counters=counters)

    paths = workspace_paths(workspace)
    saved = load_project(paths["project"])
    mesh = e2e_mesh()
    changed = e2e_mesh(changed=True)

    assert authored["fingerprint"] == compute_mesh_fingerprint(mesh).digest
    assert authored["changed_fingerprint"] == compute_mesh_fingerprint(changed).digest
    assert authored["fingerprint"] != authored["changed_fingerprint"]
    assert saved.active_scene is not None
    assert saved.active_scene.schema == ACTIVE_SCENE_SCHEMA
    assert saved.active_scene.mesh_fingerprint == authored["fingerprint"]
    assert saved.report_screenshots[0].caption == "MVP E2E captured scene"
    assert paths["report_html"].is_file()
    assert paths["capture"].is_file()
    assert restored["status"] == ActiveSceneRestoreStatus.RESTORED.value
    assert stale["status"] == ActiveSceneRestoreStatus.STALE.value
    assert mesh_snapshot(mesh) == mesh_snapshot(e2e_mesh())
    assert counters.solver_calls == 0
    assert counters.runner_calls == 0
    assert counters.solver_subprocess_calls == 0
    assert counters.automatic_saves == 0
    assert counters.automatic_captures == 0
    assert counters.automatic_exports == 0
    assert counters.explicit_saves == 1
    assert counters.explicit_captures == 1
    assert counters.explicit_exports == 1
    assert counters.network_calls == 0
    assert authored["pdf_status"] == "unavailable_deferred"
    assert NS_BAD in authored["named_selection_ids"]
