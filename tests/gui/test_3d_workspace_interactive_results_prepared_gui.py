"""Opt-in visible native acceptance for the Interactive Results Workspace."""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Callable
from copy import deepcopy
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

_MESH_REF = "interactive-results-visible-v1"
_DATASET_ID = "interactive-results-dataset-v1"
_RESULT_REF = "interactive-results-ref-v1"


def _mesh(*, changed: bool = False) -> object:
    from osw.mesh.mesh_model import MeshCellBlock, MeshData

    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (2.25 if changed else 2.0, 0.0, 0.0),
            (0.0, 2.0, 0.0),
            (0.0, 0.0, 2.0),
            (2.0, 2.0, 2.0),
        ),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("tetra", ((1, 2, 3, 4),)),
        ),
    )


def _rows(
    values: tuple[tuple[float, ...], ...],
    components: tuple[str, ...],
) -> tuple[object, ...]:
    from osw.core.result_dataset import ResultRow

    return tuple(
        ResultRow(index, dict(zip(components, value, strict=True)))
        for index, value in enumerate(values)
    )


def _dataset() -> object:
    from osw.core.result_dataset import ResultDataset, ResultField

    return ResultDataset(
        dataset_id=_DATASET_ID,
        source="prepared-visible-interactive-result-fixture",
        solver="fixture-provider",
        analysis_type="linear_static",
        fields=(
            ResultField(
                "temperature",
                "point",
                ("value",),
                _rows(((300.0,), (310.0,), (320.0,), (330.0,), (340.0,)), ("value",)),
                "K",
            ),
            ResultField(
                "stress",
                "cell",
                ("value",),
                _rows(((100.0,), (200.0,)), ("value",)),
                "Pa",
            ),
            ResultField(
                "velocity",
                "point",
                ("vx", "vy", "vz"),
                _rows(
                    (
                        (1.0, 0.0, 0.0),
                        (0.0, 2.0, 0.0),
                        (0.0, 0.0, 3.0),
                        (1.0, 1.0, 0.0),
                        (0.0, 1.0, 1.0),
                    ),
                    ("vx", "vy", "vz"),
                ),
                "m/s",
            ),
            ResultField(
                "cell_flux",
                "cell",
                ("x", "y", "z"),
                _rows(((1.0, 0.0, 0.0), (0.0, 2.0, 0.0)), ("x", "y", "z")),
                "W/m^2",
            ),
            ResultField(
                "u",
                "point",
                ("ux", "uy", "uz"),
                _rows(
                    (
                        (0.0, 0.0, 0.0),
                        (0.1, 0.0, 0.0),
                        (0.0, 0.2, 0.0),
                        (0.0, 0.0, 0.3),
                        (0.1, 0.2, 0.3),
                    ),
                    ("ux", "uy", "uz"),
                ),
                "m",
            ),
        ),
        metadata={
            "title": "Prepared interactive result",
            "mesh_ref": _MESH_REF,
            "mesh_length_unit": "m",
            "field_semantics": {
                "u": {
                    "semantic_role": "displacement",
                    "quantity_dimension": "length",
                    "coordinate_system": "global_cartesian",
                }
            },
        },
    )


def _binding(mesh: object) -> object:
    from osw.core.result_mesh_binding import (
        RESULT_MESH_BINDING_SCHEMA_V2,
        ResultMeshBinding,
        ResultMeshSignature,
    )
    from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint

    return ResultMeshBinding(
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        mesh_ref=_MESH_REF,
        result_dataset_id=_DATASET_ID,
        field_id="temperature",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        mesh_signature=ResultMeshSignature(node_count=5, cell_count=2),
    )


def _project(mesh: object) -> object:
    from osw.core.project_schema import PhysicsSetup, Project, ProjectMetadata, ResultRef
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
    fixed = NamedSelection(
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
        setup_id="interactive-result-setup",
        name="Interactive result setup",
        analysis_type="linear_static",
        fixed_support_records=(FixedSupportRecord("fixed", "Fixed support", "fixed-nodes"),),
    )
    return Project(
        ProjectMetadata(name="Visible Interactive Results"),
        physics=setup,
        selections=(fixed,),
        results=(
            ResultRef(
                id=_RESULT_REF,
                name="Prepared interactive result",
                metadata={
                    "result_dataset_id": _DATASET_ID,
                    "mesh_binding": _binding(mesh).to_dict(),
                },
            ),
        ),
    )


def _nonfinite_dataset() -> object:
    from osw.core.result_dataset import ResultDataset, ResultField

    return ResultDataset(
        dataset_id=_DATASET_ID,
        source="prepared-nonfinite-invalid-path",
        solver="fixture-provider",
        analysis_type="linear_static",
        fields=(
            ResultField(
                "temperature",
                "point",
                ("value",),
                _rows(((float("nan"),),) * 5, ("value",)),
                "K",
            ),
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


def _actor_visible(actor: object) -> bool:
    getter = getattr(actor, "GetVisibility", None)
    return bool(getter()) if callable(getter) else bool(actor.visibility)


def _assert_camera_unchanged(before: object, after: object) -> None:
    assert after.position == pytest.approx(before.position)
    assert after.focal_point == pytest.approx(before.focal_point)
    assert after.view_up == pytest.approx(before.view_up)


def _close_cycle(app: object, window: object, session: object) -> None:
    from PySide6 import QtCore, QtWidgets

    assert window.close()
    assert session.semantic_actor_ids == ()
    assert session._payloads == {}
    assert session._actors == {}
    assert session._pick_callback is None
    assert session._closed is True
    window.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    app.processEvents()
    assert QtWidgets.QApplication.topLevelWidgets() == []


def test_interactive_results_prepared_visible_native_roundtrip(
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
    import vtk
    from PySide6 import QtGui, QtWidgets

    from osw.core.result_mesh_binding import resolve_result_mesh_binding
    from osw.core.workspace_3d import ActiveSceneScreenshotRequest
    from osw.gui.interactive_results_view_model import (
        RESULT_COLORBAR_ACTOR_KEY,
        RESULT_DEFORMED_ACTOR_KEY,
        RESULT_PROBE_ACTOR_KEY,
        RESULT_SCALAR_ACTOR_KEY,
        RESULT_VECTOR_ACTOR_KEY,
    )
    from osw.gui.main_window import MainWindow
    from osw.gui.mesh_diagnostics_view_model import MESH_QUALITY_ACTOR_KEY
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererSession
    from osw.gui.workspace_scene_view_model import mesh_input_ref, scene_view_state_from_toggles
    from osw.post.result_field_mapping import project_interactive_scalar_result
    from osw.post.result_probe import ResultProbeStatus

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
    dataset = _dataset()
    binding = _binding(mesh)
    source_mesh_before = deepcopy(mesh)
    source_result_before = deepcopy(dataset.to_dict())
    screenshot_path = tmp_path / "interactive-results-visible.png"

    def create_window(cycle: int) -> object:
        window = MainWindow(
            project=_project(mesh),
            artifact_dir=tmp_path / f"artifacts-{cycle}",
            report_directory=tmp_path / f"reports-{cycle}",
        )
        window.last_result_datasets = (dataset,)
        window.show()
        window.raise_()
        window.activateWindow()
        handle = window.windowHandle()
        assert handle is not None
        _settle(
            app,
            lambda: window.isVisible() and handle.isExposed(),
            f"interactive results cycle {cycle} exposure",
        )
        return window

    window = create_window(1)
    try:
        window.load_mesh_into_viewer(mesh, mesh_ref=_MESH_REF)
        controller = window.active_scene_controller
        session = controller.session
        assert isinstance(session, PyVistaQtRendererSession)
        assert isinstance(session.hosted_widget, pyvistaqt.QtInteractor)
        session.hosted_widget.render()
        app.processEvents()
        assert controller.fallback_reason == ""
        assert int(session.hosted_widget.render_window.GetNeverRendered()) == 0
        assert "setup_glyph:fixed" in controller.actor_records
        assert "named_selection:fixed-nodes" in session.semantic_actor_ids

        panel = window.mesh_viewer
        assert panel.binding_state_label.text() == "RESOLVED"
        catalog = controller.interactive_result_field_catalog
        assert catalog is not None and catalog.binding_status.value == "READY"
        assert tuple(field.field_id for field in catalog.fields) == (
            "temperature",
            "stress",
            "velocity",
            "u",
            "cell_flux",
        )
        result_item = window.project_tree_panel.result_item(_RESULT_REF)
        assert result_item is not None
        assert result_item.text(1) == "READY"
        assert result_item.childCount() == 5

        assert window.project_tree_panel.select_result_field(
            _RESULT_REF,
            "temperature",
        )
        app.processEvents()
        assert panel.selected_result_field_id() == "temperature"
        assert RESULT_SCALAR_ACTOR_KEY not in controller.actor_records
        panel.scalar_component_selector.setCurrentText("scalar")
        panel.apply_scalar_button.click()
        assert {RESULT_SCALAR_ACTOR_KEY, RESULT_COLORBAR_ACTOR_KEY}.issubset(
            controller.actor_records
        )
        assert controller.interactive_results_view_model.scalar.data_range == (
            300.0,
            340.0,
        )

        assert controller.set_camera_preset("isometric")
        session.hosted_widget.render()
        app.processEvents()
        camera_before = session.get_camera_state()
        panel.range_mode_selector.setCurrentText("MANUAL")
        panel.manual_min_input.setValue(290.0)
        panel.manual_max_input.setValue(350.0)
        panel.colormap_selector.setCurrentText("plasma")
        panel.colorbar_toggle.setChecked(True)
        panel.apply_scalar_button.click()
        scalar = controller.interactive_results_view_model.scalar
        assert scalar is not None and scalar.display_range == (290.0, 350.0)
        assert scalar.colormap == "plasma"
        _assert_camera_unchanged(camera_before, session.get_camera_state())

        assert window.project_tree_panel.select_result_field(_RESULT_REF, "velocity")
        panel.scalar_component_selector.setCurrentText("x")
        panel.apply_scalar_button.click()
        scalar = controller.interactive_results_view_model.scalar
        assert scalar is not None and scalar.component == "x" and not scalar.derived
        panel.scalar_component_selector.setCurrentText("magnitude")
        panel.apply_scalar_button.click()
        scalar = controller.interactive_results_view_model.scalar
        assert scalar is not None and scalar.derived
        assert "(derived)" in scalar.colorbar_title

        panel.vector_selector.setCurrentText("result vector: velocity")
        panel.glyph_toggle.setChecked(True)
        panel.glyph_max_count_input.setValue(2)
        panel.vector_scale_mode_selector.setCurrentText("AUTO")
        panel.apply_vector_button.click()
        point_vector = controller.interactive_results_view_model.vector
        assert point_vector is not None and point_vector.sampled_count == 2
        point_membership = point_vector.stable_entity_keys
        panel.vector_scale_mode_selector.setCurrentText("MANUAL")
        panel.glyph_scale_input.setValue(3.0)
        panel.apply_vector_button.click()
        assert controller.interactive_results_view_model.vector.stable_entity_keys == (
            point_membership
        )
        assert controller.interactive_results_view_model.vector.scale == 3.0

        assert window.project_tree_panel.select_result_field(_RESULT_REF, "stress")
        panel.scalar_component_selector.setCurrentText("scalar")
        panel.apply_scalar_button.click()
        assert controller.interactive_results_view_model.scalar.association == "cell"
        panel.vector_selector.setCurrentText("result vector: cell_flux")
        panel.apply_vector_button.click()
        cell_vector = controller.interactive_results_view_model.vector
        assert cell_vector is not None and cell_vector.association == "cell"
        assert cell_vector.stable_entity_keys == ("0:0", "1:0")

        assert window.project_tree_panel.select_result_field(_RESULT_REF, "temperature")
        point_probe = panel.probe_result_entity("point", 1)
        point_table = panel.set_selected_result_entities("point", (2, 0))
        assert point_probe is not None and point_probe.status is ResultProbeStatus.RESOLVED
        assert point_probe.value == 310.0
        assert point_table is not None and point_table.total_count == 2
        assert panel.selected_result_table.rowCount() == 2
        assert RESULT_PROBE_ACTOR_KEY in controller.actor_records

        assert window.project_tree_panel.select_result_field(_RESULT_REF, "stress")
        cell_probe = panel.probe_result_entity("cell", "1:0")
        assert cell_probe is not None and cell_probe.status is ResultProbeStatus.RESOLVED
        assert cell_probe.value == 200.0
        assert cell_probe.cell_type == "tetra"
        assert cell_probe.connectivity == (1, 2, 3, 4)
        assert window.properties_panel.row_value("Probe").startswith("cell 1:0")

        analysis = controller.analyze_mesh_quality()
        assert analysis is not None
        assert controller.set_mesh_quality_coloring_visible(True)
        assert MESH_QUALITY_ACTOR_KEY in controller.actor_records
        assert controller.actor_records[RESULT_SCALAR_ACTOR_KEY].visible is False
        assert controller.set_scalar_result("stress", component="scalar").applied
        assert controller.actor_records[MESH_QUALITY_ACTOR_KEY].visible is False
        assert controller.actor_records[RESULT_SCALAR_ACTOR_KEY].visible is True
        assert controller.set_active_named_selection_ids(("fixed-nodes",))
        assert "active_named_selection:fixed-nodes" in session.semantic_actor_ids
        assert controller.actor_records["setup_glyph:fixed"].visible is True

        assert window.project_tree_panel.select_result_field(_RESULT_REF, "u")
        panel.scalar_component_selector.setCurrentText("magnitude")
        panel.apply_scalar_button.click()
        panel.deformation_mode_selector.setCurrentText("DEFORMED")
        panel.deformation_scale_mode_selector.setCurrentText("MANUAL")
        panel.deformation_scale_input.setValue(2.0)
        panel.apply_deformation_button.click()
        deformation = controller.interactive_results_view_model.deformation
        assert deformation is not None and deformation.applied
        assert deformation.mesh_data is not None
        assert deformation.scale == 2.0
        assert RESULT_DEFORMED_ACTOR_KEY in controller.actor_records
        assert controller.actor_records[RESULT_DEFORMED_ACTOR_KEY].visible is False
        assert controller.actor_records["setup_glyph:fixed"].visible is False
        assert "active_named_selection:fixed-nodes" in session.semantic_actor_ids
        assert mesh == source_mesh_before
        assert dataset.to_dict() == source_result_before

        assert controller.set_pick_mode("node")
        session._emit_pick(1)
        app.processEvents()
        assert controller.current_selection_target.locator.entity_ids == (1,)
        assert "current_selection" in session._actors
        assert window.properties_panel.row_value("Probe").startswith("point 1")
        picked_probe = controller.interactive_results_view_model.probe
        assert picked_probe is not None and picked_probe.status is ResultProbeStatus.RESOLVED
        assert RESULT_PROBE_ACTOR_KEY in controller.actor_records

        panel.deformation_mode_selector.setCurrentText("ORIGINAL")
        panel.apply_deformation_button.click()
        assert RESULT_DEFORMED_ACTOR_KEY not in controller.actor_records
        assert controller.actor_records["setup_glyph:fixed"].visible is True
        assert controller.interactive_result_state.probe_mode == "point"
        assert RESULT_PROBE_ACTOR_KEY in controller.actor_records
        panel.deformation_mode_selector.setCurrentText("OVERLAY")
        panel.deformation_scale_input.setValue(3.0)
        panel.apply_deformation_button.click()
        assert RESULT_DEFORMED_ACTOR_KEY in controller.actor_records
        assert controller.actor_records["setup_glyph:fixed"].visible is True
        assert controller.interactive_results_view_model.deformation.scale == 3.0
        assert controller.interactive_result_state.probe_mode == "point"
        assert RESULT_PROBE_ACTOR_KEY in controller.actor_records
        _assert_camera_unchanged(camera_before, session.get_camera_state())

        invalid_dataset = _nonfinite_dataset()
        invalid_resolution = resolve_result_mesh_binding(
            binding,
            active_mesh=mesh,
            active_mesh_ref=_MESH_REF,
            result_dataset=invalid_dataset,
        )
        invalid_scalar = project_interactive_scalar_result(
            mesh,
            invalid_dataset,
            binding_resolution=invalid_resolution,
            field_name="temperature",
            component="scalar",
        )
        assert invalid_scalar.applied is False
        assert invalid_scalar.display_range is None
        assert "finite" in invalid_scalar.diagnostics[0].lower()

        assert controller.interactive_result_state.probe_mode == "point"
        assert RESULT_PROBE_ACTOR_KEY in controller.actor_records
        same_result = controller.load_mesh(
            _mesh(),
            mesh_input_ref(_MESH_REF),
            scene_view_state_from_toggles(),
        )
        assert same_result is not None and same_result.rendered
        assert controller.interactive_result_resolution.state.value == "RESOLVED"
        expected_restored_result_actors = {
            RESULT_SCALAR_ACTOR_KEY,
            RESULT_COLORBAR_ACTOR_KEY,
            RESULT_VECTOR_ACTOR_KEY,
            RESULT_DEFORMED_ACTOR_KEY,
            RESULT_PROBE_ACTOR_KEY,
        }
        restored_actor_ids = set(controller.actor_records)
        assert expected_restored_result_actors.issubset(restored_actor_ids), (
            expected_restored_result_actors - restored_actor_ids
        )
        assert len(session.semantic_actor_ids) == len(set(session.semantic_actor_ids))

        stale_result = controller.load_mesh(
            changed_mesh,
            mesh_input_ref(_MESH_REF),
            scene_view_state_from_toggles(),
        )
        assert stale_result is not None and stale_result.rendered
        assert controller.interactive_result_resolution.state.value == "STALE"
        assert controller.interactive_result_state.binding_status == "STALE_MESH"
        assert controller.interactive_result_state.stale_reason == ("MESH_FINGERPRINT_MISMATCH")
        assert not any(
            semantic_id.startswith("result:") for semantic_id in controller.actor_records
        )
        assert not any(
            semantic_id.startswith("result:") for semantic_id in session.semantic_actor_ids
        )
        window._sync_interactive_result_tree()
        stale_item = window.project_tree_panel.result_item(_RESULT_REF)
        assert stale_item is not None and stale_item.text(1) == "STALE_MESH"

        capture = controller.capture_active_scene_screenshot(
            ActiveSceneScreenshotRequest(
                record_id="interactive-results-visible",
                output_path=str(screenshot_path),
                caption="Interactive results stale-state boundary",
            )
        )
        assert capture.status == "CAPTURED"
        assert screenshot_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert screenshot_path.stat().st_size > 0
        assert process_calls == []
        assert mesh == source_mesh_before
        assert dataset.to_dict() == source_result_before
    finally:
        first_session = window.active_scene_controller.session
        _close_cycle(app, window, first_session)

    for cycle in (2, 3):
        cycle_window = create_window(cycle)
        try:
            result = cycle_window.central_viewport_panel.set_mesh(
                mesh,
                mesh_ref=_MESH_REF,
            )
            assert result is not None and result.rendered
            cycle_session = cycle_window.active_scene_controller.session
            assert isinstance(cycle_session, PyVistaQtRendererSession)
            cycle_session.hosted_widget.render()
            assert int(cycle_session.hosted_widget.render_window.GetNeverRendered()) == 0
        finally:
            _close_cycle(app, cycle_window, cycle_session)

    assert process_calls == []
    assert QtWidgets.QApplication.topLevelWidgets() == []
    print("OSW_PREPARED_INTERACTIVE_RESULTS_PASS", flush=True)
