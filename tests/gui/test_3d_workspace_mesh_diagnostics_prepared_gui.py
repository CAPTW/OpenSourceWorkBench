"""Opt-in visible native acceptance for the Mesh Diagnostics Workspace."""

from __future__ import annotations

import json
import math
import os
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import pytest

_PREPARED = os.environ.get("OSW_RUN_PREPARED_INTERACTIVE") == "1"

if _PREPARED:
    os.environ.pop("QT_QPA_PLATFORM", None)
    os.environ.pop("PYVISTA_OFF_SCREEN", None)

pytestmark = pytest.mark.skipif(
    not _PREPARED,
    reason=(
        "The prepared interactive environment is opt-in; "
        "set OSW_RUN_PREPARED_INTERACTIVE=1 to run it."
    ),
)

_MESH_REF = "mesh-diagnostics-visible-v1"


def _mesh(*, changed: bool = False) -> object:
    from osw.mesh.mesh_model import MeshCellBlock, MeshData

    triangle_height = math.sqrt(3.0) / 2.0
    tetra_height = math.sqrt(2.0 / 3.0)
    points = (
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.5, triangle_height, 0.0),
        (0.5, math.sqrt(3.0) / 6.0, tetra_height + (0.1 if changed else 0.0)),
        (0.5, math.sqrt(3.0) / 6.0, 0.02),
        (2.0, 0.0, 0.0),
        (3.0, 0.0, 0.0),
        (3.0, 1.0, 0.0),
        (2.0, 1.0, 0.0),
        (4.0, 0.0, 0.0),
        (5.0, 0.0, 0.0),
        (5.2, 0.7, 0.0),
        (4.5, 1.2, 0.0),
        (3.8, 0.7, 0.0),
    )
    return MeshData(
        points=points,
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("quad", ((5, 6, 7, 8),)),
            MeshCellBlock("polygon", ((9, 10, 11, 12, 13),)),
            MeshCellBlock(
                "tetra",
                (
                    (0, 1, 2, 3),
                    (0, 1, 2, 4),
                    (0, 2, 1, 3),
                ),
            ),
        ),
    )


def _project(mesh: object) -> object:
    from osw.core.project_schema import PhysicsSetup, Project, ProjectMetadata
    from osw.core.selection import EntityKind, EntityLocator, NamedSelection, SelectionTargetRef
    from osw.core.selection_resolution import NODE_ORDINAL_NAMESPACE
    from osw.core.solver_setup import FixedSupportRecord
    from osw.mesh.identity import compute_mesh_fingerprint

    fingerprint = compute_mesh_fingerprint(mesh)
    locator = EntityLocator(
        fingerprint.schema,
        _MESH_REF,
        fingerprint.digest,
        EntityKind.NODE,
        NODE_ORDINAL_NAMESPACE,
        (0,),
    )
    fixed_nodes = NamedSelection(
        "fixed-nodes",
        "Fixed nodes",
        entity_kind=EntityKind.NODE,
        targets=(
            SelectionTargetRef(
                EntityKind.NODE,
                (0,),
                _MESH_REF,
                locator=locator,
            ),
        ),
        source_mesh_ref=_MESH_REF,
    )
    setup = PhysicsSetup(
        setup_id="diagnostics-setup",
        name="Diagnostics setup",
        analysis_type="linear_static",
        fixed_support_records=(FixedSupportRecord("fixed", "Fixed support", "fixed-nodes"),),
    )
    return Project(
        ProjectMetadata(name="Visible Mesh Diagnostics"),
        physics=setup,
        selections=(fixed_nodes,),
    )


def _result_dataset(point_count: int) -> object:
    from osw.core.result_dataset import ResultDataset, ResultField, ResultRow

    return ResultDataset(
        dataset_id="diagnostics-result",
        source="visible-diagnostics-fixture",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                name="temperature",
                location="node",
                components=("value",),
                rows=tuple(
                    ResultRow(index, {"value": 300.0 + index}) for index in range(point_count)
                ),
                unit="K",
            ),
            ResultField(
                name="displacement",
                location="node",
                components=("ux", "uy", "uz"),
                rows=tuple(
                    ResultRow(index, {"ux": 0.01, "uy": 0.0, "uz": 0.0})
                    for index in range(point_count)
                ),
                unit="m",
            ),
        ),
    )


def _result_binding(mesh: object) -> object:
    from osw.core.result_mesh_binding import (
        RESULT_MESH_BINDING_SCHEMA_V2,
        ResultMeshBinding,
        ResultMeshSignature,
    )
    from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint

    return ResultMeshBinding(
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref=_MESH_REF,
        result_dataset_id="diagnostics-result",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        mesh_signature=ResultMeshSignature(
            node_count=len(mesh.points),
            cell_count=sum(block.count for block in mesh.cells),
        ),
    )


def _settle(
    app: object,
    predicate: Callable[[], bool],
    label: str,
    *,
    timeout: float = 15.0,
) -> None:
    from PySide6 import QtCore

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 25)
        if predicate():
            return
    pytest.fail(f"Timed out while waiting for {label}.")


def _close_cycle(app: object, window: object, session: object) -> None:
    from PySide6 import QtCore

    assert window.close()
    assert session.semantic_actor_ids == ()
    assert session._payloads == {}
    assert session._actors == {}
    assert session._pick_callback is None
    assert session._closed is True
    window.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(
        None,
        QtCore.QEvent.Type.DeferredDelete,
    )
    app.processEvents()


def test_mesh_diagnostics_prepared_visible_native_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    for variable in (
        "QT_QPA_PLATFORM",
        "PYVISTA_OFF_SCREEN",
        "QT_OPENGL",
        "QT_ANGLE_PLATFORM",
        "LIBGL_ALWAYS_SOFTWARE",
    ):
        assert variable not in os.environ

    import pyvista
    import pyvistaqt
    import shiboken6
    import vtk
    from PySide6 import QtCore, QtGui, QtWidgets

    from osw.core.project_schema import Project
    from osw.core.selection_resolution import ResolutionState
    from osw.core.workspace_3d import ActiveSceneScreenshotRequest
    from osw.gui.interactive_results_view_model import (
        RESULT_COLORBAR_ACTOR_KEY,
        RESULT_SCALAR_ACTOR_KEY,
        RESULT_VECTOR_ACTOR_KEY,
    )
    from osw.gui.main_window import MainWindow
    from osw.gui.mesh_diagnostics_view_model import (
        MESH_BAD_ELEMENTS_ACTOR_KEY,
        MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY,
        MESH_QUALITY_ACTOR_KEY,
        MESH_QUALITY_SCALARBAR_ACTOR_KEY,
    )
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererSession
    from osw.mesh.quality import MeshDiagnosticsStatus

    assert pyvista.OFF_SCREEN is False
    assert pyvista.__version__ == "0.48.4"
    assert vtk.vtkVersion.GetVTKVersion() == "9.6.2"
    assert QtWidgets.QApplication.instance() is None
    app = QtWidgets.QApplication([])
    assert QtGui.QGuiApplication.platformName().casefold() == "windows"
    app.setQuitOnLastWindowClosed(False)

    process_calls: list[str] = []

    def blocked_process(*_args: object, **_kwargs: object) -> object:
        process_calls.append("blocked")
        raise AssertionError("Solver/runner subprocess execution is forbidden.")

    for name in ("run", "call", "check_call", "check_output", "Popen"):
        monkeypatch.setattr(subprocess, name, blocked_process)

    mesh = _mesh()
    changed_mesh = _mesh(changed=True)
    source_before = (mesh.points, mesh.cells, dict(mesh.point_data), dict(mesh.cell_data))
    project = _project(mesh)
    save_path = tmp_path / "mesh-diagnostics-roundtrip.osw.json"
    screenshot_path = tmp_path / "mesh-diagnostics-visible.png"

    def save_project(project_to_save: object, path: str) -> None:
        Path(path).write_text(
            json.dumps(project_to_save.to_dict(), sort_keys=True),
            encoding="utf-8",
        )

    def create_window(project_to_open: object, cycle: int) -> object:
        window = MainWindow(
            project=project_to_open,
            project_save_path_picker=lambda: str(save_path),
            project_saver=save_project,
            artifact_dir=tmp_path / f"artifacts-{cycle}",
            report_directory=tmp_path / f"reports-{cycle}",
        )
        window.show()
        window.raise_()
        window.activateWindow()
        handle = window.windowHandle()
        assert handle is not None
        _settle(
            app,
            lambda: window.isVisible() and handle.isExposed(),
            f"diagnostics cycle {cycle} exposure",
        )
        return window

    cycle_count = 0
    window = create_window(project, 1)
    try:
        controller = window.active_scene_controller
        session = controller.session
        assert isinstance(session, PyVistaQtRendererSession)
        assert isinstance(session.hosted_widget, pyvistaqt.QtInteractor)
        scene_result = window.central_viewport_panel.set_mesh(mesh, mesh_ref=_MESH_REF)
        assert scene_result is not None and scene_result.rendered
        assert controller.fallback_reason == ""
        assert "setup_glyph:fixed" in controller.actor_records

        dataset = _result_dataset(len(mesh.points))
        resolution = controller.set_interactive_result_dataset(
            dataset,
            _result_binding(mesh),
            result_ref_id="diagnostics-result-ref",
        )
        assert resolution is not None and resolution.state.value == "RESOLVED"
        assert controller.set_scalar_result("temperature", component="value").applied
        vector = controller.set_vector_result(
            "displacement",
            components=("ux", "uy", "uz"),
            maximum_glyph_count=8,
            scale=1.0,
        )
        assert vector.applied and RESULT_VECTOR_ACTOR_KEY in controller.actor_records

        window.mesh_diagnostics_panel.analyze_button.click()
        _settle(
            app,
            lambda: window._mesh_diagnostics_thread is None
            and controller.mesh_quality_status is MeshDiagnosticsStatus.PARTIAL_COVERAGE,
            "native Scaled Jacobian evaluation",
        )
        analysis = controller.mesh_quality_analysis
        assert analysis is not None
        assert analysis.metric_schema == "osw.mesh_quality.scaled_jacobian.v1"
        assert analysis.provider_schema == "osw.mesh_quality.provider.pyvista_vtk.v1"
        assert analysis.provider_version == "pyvista-0.48.4;vtk-9.6.2"
        assert analysis.cell_count == 6
        assert analysis.covered_count == 5
        assert analysis.uncovered_count == 1
        assert analysis.records[2].cell_type == "polygon"
        assert analysis.records[2].status.value == "UNCOVERED"
        assert analysis.records[3].value == pytest.approx(1.0, abs=1.0e-12)
        assert 0.0 < analysis.records[4].value < 0.2
        assert analysis.records[5].value == pytest.approx(-1.0, abs=1.0e-12)
        assert window.mesh_diagnostics_panel.coverage_label.text() == "5 / 6 (83.3%)"

        values_before_threshold = tuple(record.value for record in analysis.records)
        assert controller.set_mesh_quality_threshold(0.2)
        assert (
            tuple(record.value for record in controller.mesh_quality_analysis.records)
            == values_before_threshold
        )
        assert controller.mesh_quality_view_model.bad_cell_keys == ("3:1", "3:2")

        assert controller.set_camera_preset("isometric")
        session.hosted_widget.render()
        app.processEvents()
        camera_before = session.get_camera_state()
        assert controller.set_mesh_quality_coloring_visible(True)
        assert controller.set_mesh_quality_highlight_visible(True)
        assert {
            MESH_QUALITY_ACTOR_KEY,
            MESH_QUALITY_SCALARBAR_ACTOR_KEY,
            MESH_BAD_ELEMENTS_ACTOR_KEY,
        }.issubset(controller.actor_records)
        assert list(session.semantic_actor_ids).count(MESH_QUALITY_ACTOR_KEY) == 1
        assert list(session.semantic_actor_ids).count(MESH_QUALITY_SCALARBAR_ACTOR_KEY) == 1
        assert controller.actor_records[RESULT_SCALAR_ACTOR_KEY].visible is False
        assert controller.actor_records[RESULT_COLORBAR_ACTOR_KEY].visible is False
        assert controller.actor_records[RESULT_VECTOR_ACTOR_KEY].visible is True
        assert controller.actor_records["setup_glyph:fixed"].visible is True

        assert controller.set_mesh_quality_filter_mode("hide_bad")
        assert MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY in controller.actor_records
        good_spec = session._payloads[MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY][0]
        assert "2:0" in good_spec.stable_cell_keys
        assert controller.isolate_actor("base_mesh") is False
        assert controller.set_mesh_quality_filter_mode("clear")
        assert controller.set_mesh_quality_filter_mode("isolate_bad")
        assert controller.set_mesh_quality_filter_mode("clear")
        assert controller.set_representation("wireframe")
        assert controller.set_representation("surface_with_edges")
        camera_after = session.get_camera_state()
        assert camera_after.position == pytest.approx(camera_before.position)
        assert camera_after.focal_point == pytest.approx(camera_before.focal_point)
        assert camera_after.view_up == pytest.approx(camera_before.view_up)

        assert controller.select_mesh_quality_bad_cells()
        assert controller.current_selection_target.locator.entity_ids == ("3:1", "3:2")
        window.mesh_diagnostics_panel.named_selection_name.setText("Scaled Jacobian review")
        window.mesh_diagnostics_panel.create_named_selection_button.click()
        bad_selection = next(
            item
            for item in window.current_project.selections
            if item.name == "Scaled Jacobian review"
        )
        assert bad_selection.entity_kind.value == "cell"
        assert bad_selection.targets[0].locator.entity_ids == ("3:1", "3:2")
        assert bad_selection.targets[0].locator.mesh_fingerprint == (
            controller.current_mesh_fingerprint.digest
        )
        assert not hasattr(bad_selection, "quality_values")
        window.project_tree_panel.select_mesh_diagnostics()
        assert window.properties_panel.mesh_diagnostics_property_rows()["Bad"] == "2"
        assert window.properties_panel.mesh_diagnostics_property_rows()["Uncovered"] == "1"

        first_json = tmp_path / "mesh-diagnostics-a.json"
        second_json = tmp_path / "mesh-diagnostics-b.json"
        csv_path = tmp_path / "mesh-diagnostics.csv"
        assert window.export_mesh_diagnostics("json", first_json) == first_json
        assert window.export_mesh_diagnostics("json", second_json) == second_json
        assert window.export_mesh_diagnostics("csv", csv_path) == csv_path
        assert first_json.read_bytes() == second_json.read_bytes()
        exported = json.loads(first_json.read_text(encoding="utf-8"))
        assert exported["mesh_ref"] == _MESH_REF
        assert exported["quality"]["bad_canonical_cell_ids"] == ["3:1", "3:2"]
        assert exported["claim"] == (
            "Mesh diagnostics are advisory and do not certify solver suitability."
        )

        capture = controller.capture_active_scene_screenshot(
            ActiveSceneScreenshotRequest(
                record_id="mesh-diagnostics-visible",
                output_path=str(screenshot_path),
                caption="Visible Scaled Jacobian diagnostics",
            )
        )
        assert capture.status == "CAPTURED"
        assert screenshot_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert len(screenshot_path.read_bytes()) > 1024

        controller.clear_interactive_results()
        assert controller.set_mesh_quality_coloring_visible(True)
        assert window.save_project_as()
        saved = Project.from_dict(json.loads(save_path.read_text(encoding="utf-8")))
        assert any(item.name == "Scaled Jacobian review" for item in saved.selections)

        same_result = window.central_viewport_panel.set_mesh(mesh, mesh_ref=_MESH_REF)
        assert same_result is not None and same_result.rendered
        assert controller.mesh_quality_status is MeshDiagnosticsStatus.PARTIAL_COVERAGE
        assert MESH_QUALITY_ACTOR_KEY in controller.actor_records
        assert controller.named_selection_resolutions[bad_selection.id].state is (
            ResolutionState.RESOLVED
        )

        changed_result = window.central_viewport_panel.set_mesh(
            changed_mesh,
            mesh_ref=_MESH_REF,
        )
        assert changed_result is not None and changed_result.rendered
        assert controller.mesh_quality_status is MeshDiagnosticsStatus.STALE
        assert controller.named_selection_resolutions[bad_selection.id].state is (
            ResolutionState.STALE
        )
        assert not {
            MESH_QUALITY_ACTOR_KEY,
            MESH_QUALITY_SCALARBAR_ACTOR_KEY,
            MESH_BAD_ELEMENTS_ACTOR_KEY,
            MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY,
        }.intersection(controller.actor_records)
        assert controller.select_mesh_quality_bad_cells() is False
        assert source_before == (
            mesh.points,
            mesh.cells,
            mesh.point_data,
            mesh.cell_data,
        )
        assert process_calls == []
        cycle_count += 1
        _close_cycle(app, window, session)

        window = create_window(saved, 2)
        controller = window.active_scene_controller
        session = controller.session
        assert isinstance(session, PyVistaQtRendererSession)
        reopened_result = window.central_viewport_panel.set_mesh(mesh, mesh_ref=_MESH_REF)
        assert reopened_result is not None and reopened_result.rendered
        reopened_selection = next(
            item for item in saved.selections if item.name == "Scaled Jacobian review"
        )
        assert controller.named_selection_resolutions[reopened_selection.id].state is (
            ResolutionState.RESOLVED
        )
        assert controller.mesh_quality_status is MeshDiagnosticsStatus.PARTIAL_COVERAGE
        assert MESH_QUALITY_ACTOR_KEY in controller.actor_records
        assert "setup_glyph:fixed" in controller.actor_records
        cycle_count += 1
        _close_cycle(app, window, session)

        window = create_window(saved, 3)
        controller = window.active_scene_controller
        session = controller.session
        assert isinstance(session, PyVistaQtRendererSession)
        third_result = window.central_viewport_panel.set_mesh(mesh, mesh_ref=_MESH_REF)
        assert third_result is not None and third_result.rendered
        assert controller.mesh_quality_status is MeshDiagnosticsStatus.PARTIAL_COVERAGE
        assert list(session.semantic_actor_ids).count(MESH_QUALITY_ACTOR_KEY) == 1
        assert list(session.semantic_actor_ids).count(MESH_QUALITY_SCALARBAR_ACTOR_KEY) == 1
        cycle_count += 1
        _close_cycle(app, window, session)

        assert cycle_count == 3
        assert process_calls == []
        assert not any(widget.isVisible() for widget in QtWidgets.QApplication.topLevelWidgets())
        print("OSW_PREPARED_MESH_DIAGNOSTICS_PASS", flush=True)
    finally:
        if window is not None and shiboken6.isValid(window) and window.isVisible():
            window.close()
            window.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(
            None,
            QtCore.QEvent.Type.DeferredDelete,
        )
        app.processEvents()
        app.quit()
        shiboken6.delete(app)
        assert QtWidgets.QApplication.instance() is None
