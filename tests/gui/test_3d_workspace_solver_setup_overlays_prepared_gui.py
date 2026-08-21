"""Opt-in visible native acceptance for persistent solver setup overlays."""

from __future__ import annotations

import json
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

_MESH_REF = "mesh-solver-setup-visible-1"


def _mesh() -> object:
    from osw.mesh.mesh_model import MeshCellBlock, MeshData

    return MeshData(
        points=((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("tetra", ((0, 1, 2, 3),)),
        ),
    )


def _changed_mesh() -> object:
    from osw.mesh.mesh_model import MeshCellBlock, MeshData

    return MeshData(
        points=((0.0, 0.0, 0.0), (2.5, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("tetra", ((0, 1, 2, 3),)),
        ),
    )


def _project(mesh: object) -> object:
    from osw.core.materials import IsotropicElastic, Material
    from osw.core.project_schema import PhysicsSetup, Project, ProjectMetadata
    from osw.core.selection import (
        EntityKind,
        EntityLocator,
        NamedSelection,
        SelectionTargetRef,
    )
    from osw.core.selection_resolution import (
        CELL_ORDINAL_NAMESPACE,
        NODE_ORDINAL_NAMESPACE,
    )
    from osw.core.solver_setup import (
        FixedSupportRecord,
        ForceLoadRecord,
        HeatFluxRecord,
        MaterialAssignmentRecord,
        PrescribedDisplacementRecord,
        PressureLoadRecord,
        TemperatureRecord,
    )
    from osw.core.units import Quantity
    from osw.mesh.identity import compute_mesh_fingerprint

    fingerprint = compute_mesh_fingerprint(mesh)

    def selection(
        selection_id: str,
        name: str,
        kind: EntityKind,
        ids: tuple[int | str, ...],
    ) -> NamedSelection:
        namespace = NODE_ORDINAL_NAMESPACE if kind is EntityKind.NODE else CELL_ORDINAL_NAMESPACE
        locator = EntityLocator(
            fingerprint.schema,
            _MESH_REF,
            fingerprint.digest,
            kind,
            namespace,
            ids,
        )
        return NamedSelection(
            selection_id,
            name,
            entity_kind=kind,
            targets=(
                SelectionTargetRef(
                    kind,
                    ids,
                    _MESH_REF,
                    locator=locator,
                ),
            ),
            source_mesh_ref=_MESH_REF,
        )

    selections = (
        selection("fixed-nodes", "Fixed nodes", EntityKind.NODE, (0,)),
        selection("move-nodes", "Move nodes", EntityKind.NODE, (1,)),
        selection("force-nodes", "Force nodes", EntityKind.NODE, (2,)),
        selection("temperature-nodes", "Temperature nodes", EntityKind.NODE, (3,)),
        selection("surface-cells", "Surface cells", EntityKind.CELL, ("0:0",)),
        selection("volume-cells", "Volume cells", EntityKind.CELL, ("1:0",)),
    )
    material = Material(
        "steel",
        "Steel",
        elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
    )
    setup = PhysicsSetup(
        setup_id="linear-static",
        name="Linear static setup",
        analysis_type="linear_static",
        material_assignment_records=[
            MaterialAssignmentRecord(
                "material",
                "Steel region",
                "steel",
                "volume-cells",
            )
        ],
        fixed_support_records=[FixedSupportRecord("fixed", "Fixed support", "fixed-nodes")],
        prescribed_displacement_records=[
            PrescribedDisplacementRecord(
                "move",
                "Prescribed move",
                "move-nodes",
                ux=Quantity(0.002, "m"),
            )
        ],
        force_load_records=[
            ForceLoadRecord(
                "force",
                "Nodal force",
                "force-nodes",
                Quantity(100.0, "N"),
                (0.0, -1.0, 0.0),
            )
        ],
        pressure_load_records=[
            PressureLoadRecord(
                "pressure",
                "Surface pressure",
                "surface-cells",
                Quantity(25.0, "Pa"),
            )
        ],
        temperature_records=[
            TemperatureRecord(
                "temperature",
                "Nodal temperature",
                "temperature-nodes",
                Quantity(300.0, "K"),
            )
        ],
        heat_flux_records=[
            HeatFluxRecord(
                "heat-flux",
                "Surface heat flux",
                "surface-cells",
                Quantity(10.0, "W/m^2"),
            )
        ],
    )
    return Project(
        ProjectMetadata(name="Visible solver setup overlays"),
        materials=[material],
        physics=setup,
        selections=selections,
    )


def _result_dataset() -> object:
    from osw.core.result_dataset import ResultDataset, ResultField, ResultRow

    return ResultDataset(
        dataset_id="solver-setup-result",
        source="visible-setup-fixture",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                name="result_temperature",
                location="node",
                components=("value",),
                rows=tuple(
                    ResultRow(index, {"value": value})
                    for index, value in enumerate((300.0, 301.0, 302.0, 303.0))
                ),
                unit="K",
            ),
        ),
        metadata={"mesh_ref": _MESH_REF},
    )


def _result_binding(mesh: object) -> object:
    from osw.core.result_mesh_binding import (
        RESULT_MESH_BINDING_SCHEMA_V2,
        ResultMeshBinding,
        ResultMeshSignature,
    )
    from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint

    return ResultMeshBinding(
        mesh_ref=_MESH_REF,
        result_dataset_id="solver-setup-result",
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        field_id="result_temperature",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=compute_mesh_fingerprint(mesh).digest,
        mesh_signature=ResultMeshSignature(node_count=4, cell_count=2),
    )


def _settle(
    app: object,
    predicate: Callable[[], bool],
    label: str,
    *,
    timeout: float = 10.0,
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
    assert session._pick_callback is None
    assert session._closed is True
    window.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(
        None,
        QtCore.QEvent.Type.DeferredDelete,
    )
    app.processEvents()


def test_solver_setup_overlays_prepared_visible_native_roundtrip(
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
    from PySide6 import QtCore, QtGui, QtWidgets

    from osw.core.project_schema import Project
    from osw.core.result_mesh_binding import ResultMeshBindingResolutionState
    from osw.core.solver_setup import SetupRecordKind
    from osw.core.solver_setup_handoff import build_solver_setup_handoff
    from osw.core.workspace_3d import ActiveSceneScreenshotRequest
    from osw.gui.interactive_results_view_model import RESULT_SCALAR_ACTOR_KEY
    from osw.gui.main_window import MainWindow
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererSession
    from osw.solvers.calculix.adapter import prepare_solver_setup

    assert pyvista.OFF_SCREEN is False
    assert QtGui.QGuiApplication.platformName().casefold() == "windows"
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)

    process_calls: list[str] = []

    def blocked_process(*_args: object, **_kwargs: object) -> object:
        process_calls.append("blocked")
        raise AssertionError("Solver/runner subprocess execution is forbidden.")

    for name in ("run", "call", "check_call", "check_output", "Popen"):
        monkeypatch.setattr(subprocess, name, blocked_process)

    mesh = _mesh()
    project = _project(mesh)
    save_path = tmp_path / "solver-setup-roundtrip.osw.json"
    screenshot_path = tmp_path / "solver-setup-overlays.png"

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
            f"setup cycle {cycle} exposure",
        )
        return window

    cycle_count = 0
    window = create_window(project, 1)
    try:
        controller = window.active_scene_controller
        session = controller.session
        assert isinstance(session, PyVistaQtRendererSession)
        assert isinstance(session.hosted_widget, pyvistaqt.QtInteractor)
        result = window.central_viewport_panel.set_mesh(mesh, mesh_ref=_MESH_REF)
        assert result is not None and result.rendered
        assert controller.fallback_reason == ""
        assert {status.reason_code for status in controller.setup_statuses.values()} == {"READY"}
        setup_actor_ids = {
            semantic_id
            for semantic_id in controller.actor_records
            if semantic_id.startswith(("setup_target:", "setup_glyph:"))
        }
        assert setup_actor_ids == {
            "setup_target:material",
            "setup_glyph:fixed",
            "setup_glyph:move",
            "setup_glyph:force",
            "setup_target:pressure",
            "setup_glyph:pressure",
            "setup_target:temperature",
            "setup_target:heat-flux",
            "setup_glyph:heat-flux",
        }
        assert len(setup_actor_ids) == 9
        assert all(semantic_id in session._actors for semantic_id in setup_actor_ids)
        assert all(
            bool(session.hosted_widget.renderer.HasViewProp(session._actors[semantic_id]))
            for semantic_id in setup_actor_ids
        )

        pressure_spec = session._payloads["setup_glyph:pressure"][0]
        heat_flux_spec = session._payloads["setup_glyph:heat-flux"][0]
        force_spec = session._payloads["setup_glyph:force"][0]
        assert pressure_spec.points[0] == pytest.approx((2 / 3, 2 / 3, 0.0))
        assert pressure_spec.vectors[0] == pytest.approx((0.0, 0.0, -1.0))
        assert heat_flux_spec.vectors[0] == pytest.approx((0.0, 0.0, 1.0))
        assert force_spec.vectors[0] == pytest.approx((0.0, -1.0, 0.0))

        assert window.project_tree_panel.setup_item("material").parent().text(0) == ("Materials")
        assert window.project_tree_panel.setup_item("fixed").parent().text(0) == (
            "Boundary Conditions"
        )
        assert window.project_tree_panel.setup_item("pressure").parent().text(0) == ("Loads")
        assert window.project_tree_panel.setup_item("heat-flux").parent().text(0) == (
            "Thermal Conditions"
        )

        window.project_tree.setCurrentItem(window.project_tree_panel.setup_item("force"))
        assert controller.active_setup_id == "force"
        assert window.properties_panel.row_value("Setup ID") == "force"
        assert window.properties_panel.row_value("Direction") == "0, -1, 0"
        assert controller.active_named_selection_ids == ("force-nodes",)

        assert controller.set_pick_mode("setup")
        session._on_native_setup_pick(session._actors["setup_glyph:pressure"])
        assert controller.active_setup_id == "pressure"
        assert window.project_tree_panel.current_setup_id() == "pressure"
        assert window.properties_panel.row_value("Setup ID") == "pressure"
        assert controller.current_selection_target is None
        assert controller.set_pick_mode("node")

        assert controller.set_camera_preset("isometric")
        session.hosted_widget.render()
        app.processEvents()
        camera_before_edit = session.get_camera_state()
        window.project_tree.setCurrentItem(window.project_tree_panel.setup_item("force"))
        window.setup_overlay_panel.enabled_checkbox.setChecked(False)
        window.setup_overlay_panel.edit_button.click()
        assert controller.setup_statuses["force"].reason_code == "DISABLED"
        assert "setup_glyph:force" not in controller.actor_records
        window.setup_overlay_panel.enabled_checkbox.setChecked(True)
        window.setup_overlay_panel.edit_button.click()
        assert controller.setup_statuses["force"].reason_code == "READY"
        assert "setup_glyph:force" in controller.actor_records

        window.project_tree.setCurrentItem(window.project_tree_panel.setup_item("pressure"))
        old_pressure_actor = session._actors["setup_glyph:pressure"]
        window.setup_overlay_panel.scalar_spin.setValue(-25.0)
        window.setup_overlay_panel.edit_button.click()
        assert session._actors["setup_glyph:pressure"] is not old_pressure_actor
        updated_pressure = session._payloads["setup_glyph:pressure"][0]
        assert updated_pressure.vectors[0] == pytest.approx((0.0, 0.0, 1.0))
        session.hosted_widget.render()
        app.processEvents()
        camera_after_edit = session.get_camera_state()
        assert camera_after_edit.position == pytest.approx(camera_before_edit.position)
        assert camera_after_edit.focal_point == pytest.approx(camera_before_edit.focal_point)
        assert camera_after_edit.view_up == pytest.approx(camera_before_edit.view_up)
        assert (
            len(
                [
                    key
                    for key in session.semantic_actor_ids
                    if key.startswith("setup_glyph:pressure")
                ]
            )
            == 1
        )

        assert controller.set_setup_record_visible("pressure", False)
        assert controller.actor_records["setup_target:pressure"].visible is False
        assert controller.actor_records["setup_glyph:pressure"].visible is False
        assert controller.set_setup_record_visible("pressure", True)
        assert controller.set_representation("wireframe")
        assert setup_actor_ids.issubset(controller.actor_records)
        assert controller.set_representation("surface")

        resolution = controller.set_interactive_result_dataset(
            _result_dataset(),
            _result_binding(mesh),
            result_ref_id="solver-setup-result-ref",
        )
        assert resolution is not None
        assert resolution.state is ResultMeshBindingResolutionState.RESOLVED
        scalar = controller.set_scalar_result(
            "result_temperature",
            component="value",
            colorbar_visible=True,
        )
        assert scalar.applied is True
        assert RESULT_SCALAR_ACTOR_KEY in controller.actor_records
        assert setup_actor_ids.issubset(controller.actor_records)

        handoff = build_solver_setup_handoff(
            window.current_project,
            mesh=mesh,
            mesh_ref=_MESH_REF,
            adapter_id="visible-all-setup-preview",
            supported_kinds=tuple(SetupRecordKind),
        )
        assert handoff.ready is True
        assert len(handoff.records) == 7
        assert handoff.diagnostics == ()
        assert all(
            record.mesh_fingerprint == handoff.mesh_fingerprint for record in handoff.records
        )
        calculix_preview = prepare_solver_setup(
            window.current_project,
            mesh=mesh,
            mesh_ref=_MESH_REF,
        )
        assert calculix_preview.eligible is False
        assert {diagnostic.split(":", 1)[-1] for diagnostic in calculix_preview.diagnostics} == {
            "UNSUPPORTED_BY_ADAPTER"
        }
        assert process_calls == []

        capture = controller.capture_active_scene_screenshot(
            ActiveSceneScreenshotRequest(
                record_id="solver-setup-visible",
                output_path=str(screenshot_path),
                caption="Visible solver setup overlays",
            )
        )
        assert capture.status == "CAPTURED"
        assert screenshot_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

        assert window.save_project_as()
        assert save_path.is_file()
        saved = Project.from_dict(json.loads(save_path.read_text(encoding="utf-8")))
        assert saved.schema_version == "0.4"
        assert len(saved.primary_physics.heat_flux_records) == 1
        assert saved.primary_physics.pressure_load_records[0].value.value == -25.0
        assert process_calls == []
        cycle_count += 1
        _close_cycle(app, window, session)

        window = create_window(saved, 2)
        controller = window.active_scene_controller
        session = controller.session
        assert isinstance(session, PyVistaQtRendererSession)
        result = window.central_viewport_panel.set_mesh(mesh, mesh_ref=_MESH_REF)
        assert result is not None and result.rendered
        assert {status.reason_code for status in controller.setup_statuses.values()} == {"READY"}
        assert setup_actor_ids.issubset(controller.actor_records)

        result = window.central_viewport_panel.set_mesh(
            _changed_mesh(),
            mesh_ref=_MESH_REF,
        )
        assert result is not None and result.rendered
        assert {status.reason_code for status in controller.setup_statuses.values()} == {
            "MESH_FINGERPRINT_MISMATCH"
        }
        assert not any(
            key.startswith(("setup_target:", "setup_glyph:")) for key in controller.actor_records
        )
        cycle_count += 1
        _close_cycle(app, window, session)

        window = create_window(saved, 3)
        controller = window.active_scene_controller
        session = controller.session
        assert isinstance(session, PyVistaQtRendererSession)
        result = window.central_viewport_panel.set_mesh(mesh, mesh_ref=_MESH_REF)
        assert result is not None and result.rendered
        assert setup_actor_ids.issubset(controller.actor_records)
        cycle_count += 1
        _close_cycle(app, window, session)

        assert cycle_count == 3
        assert process_calls == []
        assert not any(widget.isVisible() for widget in QtWidgets.QApplication.topLevelWidgets())
        print("OSW_PREPARED_SOLVER_SETUP_OVERLAYS_PASS", flush=True)
    finally:
        if window is not None and shiboken6.isValid(window) and window.isVisible():
            window.close()
            window.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(
            None,
            QtCore.QEvent.Type.DeferredDelete,
        )
        app.processEvents()
