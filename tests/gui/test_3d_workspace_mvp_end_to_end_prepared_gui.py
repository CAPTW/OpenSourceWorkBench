"""Fresh-process visible acceptance for the complete 3D Workspace MVP journey."""

from __future__ import annotations

import builtins
import gc
import hashlib
import io
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import pytest

_PREPARED = os.environ.get("OSW_RUN_PREPARED_INTERACTIVE") == "1"
_STAGE = str(os.environ.get("OSW_E2E_STAGE", "") or "").strip().upper()
_WORKSPACE = str(os.environ.get("OSW_E2E_WORKSPACE_ROOT", "") or "").strip()

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

_STAGES = ("AUTHOR", "RESTORE", "STALE")
_CAMERA_POSITION = (11.0, 8.0, 7.0)
_CAMERA_FOCAL = (6.0, 0.4, 0.3)
_CAMERA_UP = (0.0, 0.0, 1.0)


def _workspace_root() -> Path:
    if not _WORKSPACE:
        pytest.fail("OSW_E2E_WORKSPACE_ROOT must be set when a prepared E2E stage runs.")
    root = Path(_WORKSPACE).resolve()
    if not root.is_dir():
        pytest.fail(f"OSW_E2E_WORKSPACE_ROOT does not exist: {root}")
    return root


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


def _drag(widget: object, start: object, end: object, *, steps: int = 6) -> None:
    from PySide6 import QtCore, QtTest

    QtTest.QTest.mousePress(
        widget,
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.KeyboardModifier.NoModifier,
        start,
    )
    for step in range(1, steps + 1):
        fraction = step / steps
        point = QtCore.QPoint(
            round(start.x() + (end.x() - start.x()) * fraction),
            round(start.y() + (end.y() - start.y()) * fraction),
        )
        QtTest.QTest.mouseMove(widget, point)
    QtTest.QTest.mouseRelease(
        widget,
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.KeyboardModifier.NoModifier,
        end,
    )


def _world_to_display(renderer: object, point: tuple[float, float, float]) -> tuple[float, ...]:
    renderer.SetWorldPoint(*point, 1.0)
    renderer.WorldToDisplay()
    display = tuple(float(value) for value in renderer.GetDisplayPoint())
    assert len(display) == 3
    assert all(math.isfinite(value) for value in display)
    return display


def _display_to_qt(widget: object, display: tuple[float, ...]) -> tuple[int, int, float]:
    ratio = float(widget._getPixelRatio())
    assert math.isfinite(ratio) and ratio > 0.0
    x = round(display[0] / ratio)
    y = widget.height() - 1 - round(display[1] / ratio)
    assert 0 <= x < widget.width()
    assert 0 <= y < widget.height()
    return x, y, ratio


def _capability_value(report: str, label: str) -> str:
    prefix = label.casefold()
    for raw_line in report.splitlines():
        line = raw_line.strip()
        if line.casefold().startswith(prefix):
            return line.split(":", 1)[-1].strip()
    return ""


def _observer_signature(interactor: object) -> tuple[tuple[str, int], ...]:
    values = Counter(str(event) for event in interactor.iren._observers.values())
    return tuple(sorted(values.items()))


def _is_within(path: Path, root: Path) -> bool:
    return path.resolve(strict=False).is_relative_to(root.resolve(strict=False))


def _install_product_guards(
    monkeypatch: pytest.MonkeyPatch,
    repository_root: Path,
) -> dict[str, int]:
    from osw.core.run_manager import RunManager
    from osw.plugins.base import SolverAdapterPlugin
    from osw.scripts.mscript.octave_runner import OctaveRunner
    from osw.solvers.calculix.ccx_runner import CalculixCcxRunner as LegacyCalculiXRunner
    from osw.solvers.calculix.runner import CalculiXRunner
    from osw.solvers.runner import ExternalCommandRunner

    counters = {
        "solver_calls": 0,
        "runner_calls": 0,
        "subprocess_calls": 0,
        "automatic_saves": 0,
        "repository_outputs": 0,
    }

    def blocked_solver(*_args: object, **_kwargs: object) -> object:
        counters["solver_calls"] += 1
        pytest.fail("Prepared MVP E2E must not execute a solver.")

    def blocked_runner(*_args: object, **_kwargs: object) -> object:
        counters["runner_calls"] += 1
        pytest.fail("Prepared MVP E2E must not execute a runner.")

    def blocked_subprocess(*_args: object, **_kwargs: object) -> object:
        counters["subprocess_calls"] += 1
        pytest.fail("Prepared MVP E2E must not launch a product subprocess.")

    for owner, method_name in (
        (ExternalCommandRunner, "run"),
        (ExternalCommandRunner, "run_command"),
        (RunManager, "run"),
    ):
        monkeypatch.setattr(owner, method_name, blocked_runner)
    for owner, method_name in (
        (SolverAdapterPlugin, "run"),
        (CalculiXRunner, "run"),
        (CalculiXRunner, "run_input_deck"),
        (LegacyCalculiXRunner, "run_input_deck"),
        (OctaveRunner, "run"),
        (OctaveRunner, "run_script"),
    ):
        monkeypatch.setattr(owner, method_name, blocked_solver)
    for name in (
        "run",
        "Popen",
        "call",
        "check_call",
        "check_output",
        "getoutput",
        "getstatusoutput",
    ):
        monkeypatch.setattr(subprocess, name, blocked_subprocess)
    monkeypatch.setattr(os, "system", blocked_subprocess)
    monkeypatch.setattr(os, "popen", blocked_subprocess)

    def block_repository_output(value: object) -> None:
        if isinstance(value, str | os.PathLike) and _is_within(Path(value), repository_root):
            counters["repository_outputs"] += 1
            pytest.fail("Prepared MVP E2E attempted repository output.")

    real_builtin_open = builtins.open
    real_io_open = io.open
    real_os_open = os.open
    real_mkdir = os.mkdir
    real_makedirs = os.makedirs

    def guarded_builtin_open(
        file: object,
        mode: str = "r",
        *args: object,
        **kwargs: object,
    ) -> object:
        if any(marker in mode for marker in ("w", "a", "x", "+")):
            block_repository_output(file)
        return real_builtin_open(file, mode, *args, **kwargs)

    def guarded_io_open(
        file: object,
        mode: str = "r",
        *args: object,
        **kwargs: object,
    ) -> object:
        if any(marker in mode for marker in ("w", "a", "x", "+")):
            block_repository_output(file)
        return real_io_open(file, mode, *args, **kwargs)

    def guarded_os_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        if flags & write_flags:
            block_repository_output(path)
        return real_os_open(path, flags, *args, **kwargs)

    def guarded_mkdir(path: object, mode: int = 0o777, *, dir_fd: int | None = None) -> None:
        block_repository_output(path)
        real_mkdir(path, mode, dir_fd=dir_fd)

    def guarded_makedirs(name: object, mode: int = 0o777, exist_ok: bool = False) -> None:
        block_repository_output(name)
        real_makedirs(name, mode=mode, exist_ok=exist_ok)

    monkeypatch.setattr(builtins, "open", guarded_builtin_open)
    monkeypatch.setattr(io, "open", guarded_io_open)
    monkeypatch.setattr(os, "open", guarded_os_open)
    monkeypatch.setattr(os, "mkdir", guarded_mkdir)
    monkeypatch.setattr(os, "makedirs", guarded_makedirs)
    return counters


def _blocked_file_op(label: str) -> Callable[..., object]:
    def blocked(*_args: object, **_kwargs: object) -> object:
        pytest.fail(f"Prepared MVP E2E must not {label}.")

    return blocked


def _create_visible_window(
    app: object,
    *,
    workspace: Path,
    project: object,
    cycle: int,
    extras: dict[str, object],
) -> object:
    from PySide6 import QtGui

    from osw.gui.main_window import MainWindow

    window = MainWindow(
        project=project,
        metadata_mesh_reader=_blocked_file_op("auto-load a mesh file"),
        artifact_dir=workspace / f"artifacts-{cycle}",
        report_directory=workspace / f"reports-{cycle}",
        mesh_diagnostics_async=False,
        project_error_reporter=lambda message: pytest.fail(str(message)),
        **extras,
    )
    window._confirm_persist_scene_screenshots = lambda _count: True
    window.show()
    window.raise_()
    window.activateWindow()
    handle = window.windowHandle()
    assert handle is not None
    _settle(
        app,
        lambda: window.isVisible() and handle.isExposed(),
        f"cycle {cycle} visible MainWindow exposure",
    )
    assert QtGui.QGuiApplication.platformName().casefold() == "windows"
    return window


def _close_visible_cycle(
    app: object,
    window: object,
    *,
    cycle: int,
) -> dict[str, int]:
    from PySide6 import QtCore, QtWidgets

    controller = window.active_scene_controller
    session = controller.session
    interactor = None if session is None else session.hosted_widget
    observer_count = 0
    if interactor is not None:
        observer_count = sum(count for _name, count in _observer_signature(interactor))
    assert window.close()
    assert not window.isVisible()
    assert controller.actor_records == {}
    assert controller.pending_active_scene_state is None
    if session is not None:
        assert session.semantic_actor_ids == ()
        assert session._closed is True
        assert session._pick_callback is None
    window.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    _settle(
        app,
        lambda: len(QtWidgets.QApplication.topLevelWidgets()) == 0,
        f"cycle {cycle} top-level teardown",
    )
    assert QtWidgets.QApplication.topLevelWidgets() == []
    gc.collect()
    return {
        "actor_count_after_close": len(controller.actor_records),
        "observer_count": observer_count,
        "top_level_windows": len(QtWidgets.QApplication.topLevelWidgets()),
    }


def _assert_hardware_renderer(interactor: object) -> dict[str, str]:
    render_window = interactor.render_window
    renderer = interactor.renderer
    assert render_window is not None
    assert renderer is not None
    assert int(render_window.GetNeverRendered()) == 0
    report = str(render_window.ReportCapabilities())
    vendor = _capability_value(report, "OpenGL vendor string")
    renderer_name = _capability_value(report, "OpenGL renderer string")
    opengl_version = _capability_value(report, "OpenGL version string")
    assert vendor and renderer_name and opengl_version
    renderer_text = " ".join((vendor, renderer_name, opengl_version, report)).casefold()
    assert not any(
        item in renderer_text
        for item in ("llvmpipe", "softpipe", "software", "microsoft basic render driver")
    )
    return {
        "vendor": vendor,
        "renderer": renderer_name,
        "opengl": opengl_version,
    }


def _assert_scene_rendered(window: object, mesh: object) -> None:
    from tests.helpers.workspace_3d_mvp_e2e import MESH_REF

    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererSession
    from osw.mesh.identity import compute_mesh_fingerprint

    controller = window.active_scene_controller
    session = controller.session
    assert isinstance(session, PyVistaQtRendererSession)
    assert window.central_viewport_panel.interactive_available is True
    assert controller.fallback_reason == ""
    assert controller.current_mesh_fingerprint == compute_mesh_fingerprint(mesh)
    assert controller.current_mesh_ref == MESH_REF
    assert {"base_mesh", "wireframe"}.issubset(controller.actor_records)


def _apply_authored_camera(controller: object) -> None:
    from osw.core.workspace_3d import ActiveSceneCameraState

    camera = ActiveSceneCameraState(
        position=_CAMERA_POSITION,
        focal_point=_CAMERA_FOCAL,
        view_up=_CAMERA_UP,
        view_preset="isometric",
    )
    assert controller.session is not None
    controller.session.apply_camera_state(camera)


def _run_author_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    from dataclasses import replace

    from PySide6 import QtCore, QtTest, QtWidgets
    from tests.helpers.workspace_3d_mvp_e2e import (
        CALCULIX_SUPPORTED_KINDS,
        CAPTURE_CAPTION,
        DEFORMATION_MANUAL_SCALE,
        MESH_REF,
        NS_BAD,
        NS_FIXED,
        NS_FORCE,
        NS_MATERIAL,
        NS_PICKED_CELLS,
        NS_PICKED_POINTS,
        NS_SURFACE,
        QUALITY_THRESHOLD,
        RESULT_DATASET_ID,
        RESULT_REF_ID,
        SETUP_DISPLACEMENT,
        SETUP_FIXED,
        SETUP_FORCE,
        SETUP_HEAT_FLUX,
        SETUP_MATERIAL,
        SETUP_PRESSURE,
        SETUP_TEMPERATURE,
        VECTOR_MAX_COUNT,
        VECTOR_SCALE,
        authored_e2e_project,
        create_selection_from_current,
        e2e_mesh,
        e2e_result_binding,
        e2e_result_dataset,
        merge_stage_manifest,
        mesh_snapshot,
        png_is_nonblank,
        png_signature_and_size,
        provenance_has_absolute_path,
        workspace_paths,
    )

    from osw.core.project_io import save_project
    from osw.core.project_schema import project_with
    from osw.core.selection import EntityKind
    from osw.core.solver_setup import SetupReadiness, evaluate_solver_setup
    from osw.core.solver_setup_handoff import build_solver_setup_handoff
    from osw.core.workspace_3d import (
        ACTIVE_SCENE_PROVENANCE_METADATA_KEY,
        ACTIVE_SCENE_SCHEMA,
        ActiveSceneScreenshotRequest,
        active_scene_state_digest,
    )
    from osw.gui.interactive_results_view_model import (
        RESULT_COLORBAR_ACTOR_KEY,
        RESULT_DEFORMED_ACTOR_KEY,
        RESULT_SCALAR_ACTOR_KEY,
        RESULT_VECTOR_ACTOR_KEY,
    )
    from osw.gui.mesh_diagnostics_view_model import MESH_BAD_ELEMENTS_ACTOR_KEY
    from osw.mesh.identity import compute_mesh_fingerprint
    from osw.mesh.quality import MESH_QUALITY_METRIC_SCHEMA
    from osw.post.report_generator import build_report
    from osw.post.report_model import (
        ReportBuildRequest,
        ReportFormat,
        report_assets_to_scene_screenshots,
    )
    from osw.post.result_deformation import DeformationMode, DeformationScaleMode
    from osw.post.result_probe import ResultProbeRequest
    from osw.solvers.calculix.adapter import prepare_solver_setup

    for variable in (
        "QT_QPA_PLATFORM",
        "PYVISTA_OFF_SCREEN",
        "QT_OPENGL",
        "QT_ANGLE_PLATFORM",
        "LIBGL_ALWAYS_SOFTWARE",
    ):
        assert variable not in os.environ

    workspace = _workspace_root()
    repository_root = Path(__file__).resolve().parents[2]
    import pyvista
    import pyvistaqt
    import vtk  # noqa: F401

    assert pyvista.OFF_SCREEN is False
    assert pyvistaqt is not None
    counters = _install_product_guards(monkeypatch, repository_root)
    allow_save = False

    def explicit_saver(project: object, path: object) -> None:
        if not allow_save:
            counters["automatic_saves"] += 1
            pytest.fail("Prepared MVP E2E must not automatically save a Project.")
        save_project(project, path)

    assert QtWidgets.QApplication.instance() is None
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    mesh = e2e_mesh()
    original_mesh = mesh_snapshot(mesh)
    dataset = e2e_result_dataset(mesh)
    original_dataset = dataset.to_dict()
    fingerprint = compute_mesh_fingerprint(mesh)
    changed_fingerprint = compute_mesh_fingerprint(e2e_mesh(changed=True))
    paths = workspace_paths(workspace)
    window = _create_visible_window(
        app,
        workspace=workspace,
        project=authored_e2e_project(mesh),
        cycle=1,
        extras={
            "project_saver": explicit_saver,
            "project_save_path_picker": lambda: str(paths["project"]),
            "project_open_path_picker": _blocked_file_op("open a Project during AUTHOR"),
            "project_loader": _blocked_file_op("load a Project during AUTHOR"),
        },
    )
    try:
        controller = window.active_scene_controller
        scene_result = window.central_viewport_panel.set_mesh(mesh, mesh_ref=MESH_REF)
        assert scene_result is not None
        assert scene_result.rendered is True
        _assert_scene_rendered(window, mesh)
        session = controller.session
        interactor = session.hosted_widget
        hardware = _assert_hardware_renderer(interactor)
        interactor.setFocus()
        interactor.render()

        assert controller.fit_to_scene()
        assert controller.set_camera_preset("front")
        assert controller.set_camera_preset("isometric")
        _apply_authored_camera(controller)
        assert controller.set_representation("surface_with_edges")
        assert controller.set_axes_visible(True)
        camera_before = session.get_camera_state()
        assert controller.hide_actor("wireframe")
        assert controller.show_actor("wireframe")
        assert controller.isolate_actor("base_mesh")
        assert controller.clear_isolation()
        assert controller.actor_records["wireframe"].visible is True
        restored_camera = session.get_camera_state()
        assert restored_camera.position == pytest.approx(camera_before.position)
        assert restored_camera.focal_point == pytest.approx(camera_before.focal_point)

        renderer = interactor.renderer
        point_world = tuple(float(value) for value in mesh.points[5])
        point_qx, point_qy, _ratio = _display_to_qt(
            interactor,
            _world_to_display(renderer, point_world),
        )
        assert controller.set_pick_mode("node")
        point_notes: list[object] = []
        controller.set_selection_listener(
            lambda: point_notes.append(controller.current_selection_target)
        )
        QtTest.QTest.mouseClick(
            interactor,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
            QtCore.QPoint(point_qx, point_qy),
        )
        _settle(app, lambda: len(point_notes) == 1, "native point pick")
        assert controller.current_selection_target is not None
        assert controller.current_selection_target.kind is EntityKind.NODE
        assert 5 in controller.current_selection_target.ids
        assert controller.set_selection_operation("add")
        assert controller.handle_pick(
            {
                "generation": controller.generation,
                "mesh_ref": MESH_REF,
                "mesh_fingerprint": fingerprint.digest,
                "entity_kind": "node",
                "backend_index": 4,
                "intent": "add",
            }
        )
        picked_points = create_selection_from_current(
            controller,
            selection_id=NS_PICKED_POINTS,
            name="Picked Points",
            existing=window.current_project.selections,
        )
        window.set_project(
            project_with(
                window.current_project,
                selections=(*window.current_project.selections, picked_points),
            )
        )
        controller.set_selection_listener(None)
        assert controller.set_selection_operation("replace")
        assert controller.set_pick_mode("cell")
        cell_notes: list[object] = []
        controller.set_selection_listener(
            lambda: cell_notes.append(controller.current_selection_target)
        )
        projected = tuple(
            _display_to_qt(
                interactor,
                _world_to_display(renderer, tuple(float(value) for value in mesh.points[index])),
            )
            for index in (8, 9, 10)
        )
        left = max(3, min(item[0] for item in projected) - 8)
        right = min(interactor.width() - 4, max(item[0] for item in projected) + 8)
        top = max(3, min(item[1] for item in projected) - 8)
        bottom = min(interactor.height() - 4, max(item[1] for item in projected) + 8)
        _drag(interactor, QtCore.QPoint(left, top), QtCore.QPoint(right, bottom))
        _settle(app, lambda: len(cell_notes) == 1, "native cell rectangle pick")
        assert controller.current_selection_target is not None
        assert controller.current_selection_target.kind is EntityKind.CELL
        picked_cells = create_selection_from_current(
            controller,
            selection_id=NS_PICKED_CELLS,
            name="Picked Cells",
            existing=window.current_project.selections,
        )
        window.set_project(
            project_with(
                window.current_project,
                selections=(*window.current_project.selections, picked_cells),
            )
        )
        controller.clear_current_selection()
        controller.set_selection_listener(None)
        tree_ids = {item.id for item in window.current_project.selections}
        assert {
            NS_MATERIAL,
            NS_FIXED,
            NS_FORCE,
            NS_PICKED_POINTS,
            NS_PICKED_CELLS,
        }.issubset(tree_ids)

        controller.set_named_selections(window.current_project.selections)
        controller.set_solver_setup(
            window.current_project.primary_physics,
            materials=window.current_project.materials,
        )
        statuses = evaluate_solver_setup(
            window.current_project.primary_physics,
            selections=window.current_project.selections,
            materials=window.current_project.materials,
            resolutions=controller.named_selection_resolutions,
            mesh=mesh,
            project_units=window.current_project.units,
        )
        assert all(status.state is SetupReadiness.READY for status in statuses)
        setup_keys = tuple(
            key
            for key in controller.actor_records
            if key.startswith(("setup_target:", "setup_glyph:", "setup:"))
        )
        assert setup_keys
        assert len(setup_keys) == len(set(setup_keys))
        covered = {key.rsplit(":", 1)[-1] for key in setup_keys}
        assert covered == {
            SETUP_MATERIAL,
            SETUP_FIXED,
            SETUP_DISPLACEMENT,
            SETUP_FORCE,
            SETUP_PRESSURE,
            SETUP_TEMPERATURE,
            SETUP_HEAT_FLUX,
        }
        supported = build_solver_setup_handoff(
            window.current_project,
            mesh=mesh,
            mesh_ref=MESH_REF,
            adapter_id="osw.solvers.calculix.linear_static",
            supported_kinds=CALCULIX_SUPPORTED_KINDS,
            strict=False,
        )
        unsupported = {
            item.setup_id: item.reason_code
            for item in supported.diagnostics
            if item.reason_code == "UNSUPPORTED_BY_ADAPTER"
        }
        assert set(unsupported) == {SETUP_PRESSURE, SETUP_TEMPERATURE, SETUP_HEAT_FLUX}
        disabled = project_with(
            window.current_project,
            physics=replace(
                window.current_project.primary_physics,
                pressure_load_records=[
                    replace(record, enabled=False)
                    for record in window.current_project.primary_physics.pressure_load_records
                ],
                temperature_records=[
                    replace(record, enabled=False)
                    for record in window.current_project.primary_physics.temperature_records
                ],
                heat_flux_records=[
                    replace(record, enabled=False)
                    for record in window.current_project.primary_physics.heat_flux_records
                ],
            ),
        )
        prepared = prepare_solver_setup(disabled, mesh=mesh, mesh_ref=MESH_REF)
        assert prepared.eligible is True
        assert prepared.execution_mode == "prepare_only"
        assert not hasattr(prepared, "command")
        assert counters["solver_calls"] == 0

        analysis = controller.analyze_mesh_quality()
        assert analysis is not None
        assert analysis.metric_schema == MESH_QUALITY_METRIC_SCHEMA
        assert analysis.uncovered_count == 1
        assert controller.set_mesh_quality_threshold(QUALITY_THRESHOLD)
        assert controller.mesh_quality_view_model.bad_cell_keys
        assert "3:1" in controller.mesh_quality_view_model.bad_cell_keys
        assert controller.set_mesh_quality_highlight_visible(True)
        assert MESH_BAD_ELEMENTS_ACTOR_KEY in controller.actor_records
        assert controller.set_mesh_quality_isolated(True)
        assert controller.restore_mesh_quality_visibility()
        assert controller.select_mesh_quality_bad_cells()
        bad_selection = create_selection_from_current(
            controller,
            selection_id=NS_BAD,
            name="Bad Elements",
            existing=window.current_project.selections,
        )
        assert bad_selection.targets[0].locator is not None
        assert "3:1" in bad_selection.targets[0].locator.entity_ids
        window.set_project(
            project_with(
                window.current_project,
                selections=(*window.current_project.selections, bad_selection),
            )
        )
        controller.clear_current_selection()
        assert mesh_snapshot(mesh) == original_mesh

        window.last_result_datasets = (dataset,)
        resolution = controller.set_interactive_result_dataset(
            dataset,
            e2e_result_binding(mesh),
            result_ref_id=RESULT_REF_ID,
        )
        assert resolution is not None
        assert str(resolution.state) == "RESOLVED"
        assert controller.set_scalar_result(
            "temperature",
            component="value",
            range_mode="MANUAL",
            manual_range=(300.0, 340.0),
            colormap="plasma",
            colorbar_visible=True,
        ).applied
        assert controller.set_scalar_result(
            "cell_stress",
            component="value",
            range_mode="AUTO",
            colormap="viridis",
            colorbar_visible=True,
        ).applied
        vector = controller.set_vector_result(
            "velocity",
            components=("vx", "vy", "vz"),
            maximum_glyph_count=VECTOR_MAX_COUNT,
            scale=VECTOR_SCALE,
        )
        assert vector.applied is True
        assert vector.sampled_count == VECTOR_MAX_COUNT
        point_probe = controller.probe_result(
            ResultProbeRequest(
                dataset_id=RESULT_DATASET_ID,
                field_name="temperature",
                component="value",
                association="point",
                stable_entity_key=1,
                mesh_fingerprint=fingerprint.digest,
            )
        )
        cell_probe = controller.probe_result(
            ResultProbeRequest(
                dataset_id=RESULT_DATASET_ID,
                field_name="cell_stress",
                component="value",
                association="cell",
                stable_entity_key="0:0",
                mesh_fingerprint=fingerprint.digest,
            )
        )
        table = controller.set_selected_result_table(
            field_name="temperature",
            component="value",
            association="point",
            stable_entity_keys=(0, 1, 2),
        )
        assert point_probe is not None and point_probe.value == 302.0
        assert cell_probe is not None and cell_probe.value == 10.0
        assert table is not None
        overlay = controller.set_deformed_result(
            "displacement",
            mode=DeformationMode.OVERLAY,
            scale_mode=DeformationScaleMode.MANUAL,
            manual_scale=DEFORMATION_MANUAL_SCALE,
        )
        assert overlay.applied is True
        assert {
            RESULT_SCALAR_ACTOR_KEY,
            RESULT_VECTOR_ACTOR_KEY,
            RESULT_COLORBAR_ACTOR_KEY,
            RESULT_DEFORMED_ACTOR_KEY,
        }.issubset(controller.actor_records)
        assert dataset.to_dict() == original_dataset
        controller.set_active_named_selection_ids((NS_SURFACE,))
        controller.set_active_setup_id(SETUP_FORCE)
        _apply_authored_camera(controller)

        state = controller.snapshot_active_scene_state()
        assert state is not None
        assert state.schema == ACTIVE_SCENE_SCHEMA
        assert state.representation == "surface_with_edges"
        assert state.result_state is not None
        assert state.result_state.vector_field == "velocity"
        assert state.result_state.deformation_mode == "OVERLAY"
        scene_digest = active_scene_state_digest(state)
        capture = controller.capture_active_scene_screenshot(
            ActiveSceneScreenshotRequest(
                record_id="scene-screenshot-mvp-e2e",
                output_path=str(paths["capture"]),
                path_kind="external_absolute",
                caption=CAPTURE_CAPTION,
            )
        )
        assert capture.status == "CAPTURED"
        assert capture.record is not None
        image_bytes = paths["capture"].read_bytes()
        signature_ok, image_size = png_signature_and_size(image_bytes)
        assert signature_ok and image_size is not None
        assert png_is_nonblank(image_bytes)
        provenance = capture.record.metadata[ACTIVE_SCENE_PROVENANCE_METADATA_KEY]
        assert provenance["image_sha256"] == hashlib.sha256(image_bytes).hexdigest()
        assert provenance["mesh_fingerprint"] == fingerprint.digest
        assert not provenance_has_absolute_path(provenance, workspace)
        window._scene_screenshot_candidates = (capture.record,)
        persisted = window.persist_staged_scene_screenshots()
        assert persisted == 1
        assert window.project_dirty is True
        html = build_report(
            ReportBuildRequest(
                project=window.current_project,
                output_path=paths["report_html"],
                format=ReportFormat.HTML,
            ),
            scene_screenshots=report_assets_to_scene_screenshots(
                window.current_project.report_screenshots
            ),
        )
        assert html.status in {"ok", "warning"}
        html_text = paths["report_html"].read_text(encoding="utf-8")
        assert CAPTURE_CAPTION in html_text
        pdf = build_report(
            ReportBuildRequest(
                project=window.current_project,
                output_path=workspace / "report-pdf-optional.html",
                format=ReportFormat.PDF_OPTIONAL,
            ),
            scene_screenshots=report_assets_to_scene_screenshots(
                window.current_project.report_screenshots
            ),
        )
        pdf_codes = {str(message.code) for message in pdf.diagnostics.messages}
        assert "report-pdf-deferred" in pdf_codes
        camera_after_report = session.get_camera_state()
        assert camera_after_report.position == pytest.approx(_CAMERA_POSITION)
        allow_save = True
        assert window.save_project_as() is True
        allow_save = False
        assert window.project_dirty is False
        assert mesh_snapshot(mesh) == original_mesh
        actor_count = len(controller.actor_records)
        named_selection_ids = [item.id for item in window.current_project.selections]
        quality_model = controller.mesh_quality_view_model
        bad_cell_keys = list(quality_model.bad_cell_keys) if quality_model is not None else ["3:1"]
        residue = _close_visible_cycle(app, window, cycle=1)
        merge_stage_manifest(
            workspace,
            {
                "author_pid": os.getpid(),
                "mesh_fingerprint": fingerprint.digest,
                "changed_fingerprint": changed_fingerprint.digest,
                "scene_digest": scene_digest,
                "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
                "image_byte_length": len(image_bytes),
                "image_size": list(image_size),
                "capture_id": capture.record.id,
                "vector_sampled_count": vector.sampled_count,
                "vector_scale": VECTOR_SCALE,
                "deformation_mode": overlay.mode.value,
                "deformation_scale": overlay.scale,
                "point_probe_value": point_probe.value,
                "cell_probe_value": cell_probe.value,
                "bad_cell_keys": bad_cell_keys,
                "named_selection_ids": named_selection_ids,
                "hardware": hardware,
                "author_actor_count": actor_count,
                "author_close": residue,
                "product_solver_calls": counters["solver_calls"],
                "product_runner_calls": counters["runner_calls"],
                "product_subprocess_calls": counters["subprocess_calls"],
                "automatic_saves": counters["automatic_saves"],
            },
        )
    finally:
        app.quit()


def _run_restore_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    from PySide6 import QtWidgets
    from tests.helpers.workspace_3d_mvp_e2e import (
        MESH_REF,
        RESULT_REF_ID,
        e2e_mesh,
        e2e_result_binding,
        e2e_result_dataset,
        empty_e2e_project,
        merge_stage_manifest,
        mesh_snapshot,
        read_stage_manifest,
        workspace_paths,
    )

    from osw.core.project_io import load_project
    from osw.core.workspace_3d import ACTIVE_SCENE_SCHEMA, ActiveSceneRestoreStatus
    from osw.gui.interactive_results_view_model import (
        RESULT_DEFORMED_ACTOR_KEY,
        RESULT_SCALAR_ACTOR_KEY,
        RESULT_VECTOR_ACTOR_KEY,
    )
    from osw.mesh.identity import compute_mesh_fingerprint

    workspace = _workspace_root()
    repository_root = Path(__file__).resolve().parents[2]
    import pyvista
    import pyvistaqt

    assert pyvista.OFF_SCREEN is False
    assert pyvistaqt is not None
    counters = _install_product_guards(monkeypatch, repository_root)
    paths = workspace_paths(workspace)
    manifest = read_stage_manifest(workspace)
    mesh = e2e_mesh()
    dataset = e2e_result_dataset(mesh)
    original_mesh = mesh_snapshot(mesh)
    original_dataset = dataset.to_dict()

    def saver(*_args: object, **_kwargs: object) -> None:
        counters["automatic_saves"] += 1
        pytest.fail("RESTORE must not save a Project.")

    assert QtWidgets.QApplication.instance() is None
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    window = _create_visible_window(
        app,
        workspace=workspace,
        project=empty_e2e_project(),
        cycle=2,
        extras={
            "project_saver": saver,
            "project_save_path_picker": _blocked_file_op("save during RESTORE"),
            "project_open_path_picker": lambda: str(paths["project"]),
            "project_loader": load_project,
        },
    )
    try:
        assert window.open_project() is True
        controller = window.active_scene_controller
        assert controller.active_scene_restore_result.status is ActiveSceneRestoreStatus.PENDING
        scene_result = window.central_viewport_panel.set_mesh(mesh, mesh_ref=MESH_REF)
        assert scene_result is not None
        assert scene_result.rendered is True
        _assert_scene_rendered(window, mesh)
        window.last_result_datasets = (dataset,)
        controller.set_interactive_result_dataset(
            dataset,
            e2e_result_binding(mesh),
            result_ref_id=RESULT_REF_ID,
        )
        restored = controller.restore_pending_active_scene_state()
        if restored.status is not ActiveSceneRestoreStatus.RESTORED:
            restored = controller.restore_pending_active_scene_state()
        assert restored.status is ActiveSceneRestoreStatus.RESTORED
        state = controller.snapshot_active_scene_state()
        assert state is not None
        assert state.schema == ACTIVE_SCENE_SCHEMA
        assert state.mesh_fingerprint == manifest["mesh_fingerprint"]
        assert state.representation == "surface_with_edges"
        assert state.axes_visible is True
        assert state.result_state is not None
        assert state.result_state.vector_field == "velocity"
        assert state.result_state.deformation_mode == "OVERLAY"
        camera = controller.session.get_camera_state()
        assert camera.position == pytest.approx(_CAMERA_POSITION, abs=1e-3)
        assert camera.focal_point == pytest.approx(_CAMERA_FOCAL, abs=1e-3)
        capture = next(iter(window.current_project.report_screenshots))
        capture_restore = controller.restore_captured_active_scene(capture)
        assert capture_restore.status is ActiveSceneRestoreStatus.RESTORED
        actor_ids = tuple(controller.actor_records)
        assert len(actor_ids) == len(set(actor_ids))
        assert {
            RESULT_SCALAR_ACTOR_KEY,
            RESULT_VECTOR_ACTOR_KEY,
            RESULT_DEFORMED_ACTOR_KEY,
        }.issubset(controller.actor_records)
        assert mesh_snapshot(mesh) == original_mesh
        assert dataset.to_dict() == original_dataset
        assert compute_mesh_fingerprint(mesh).digest == manifest["mesh_fingerprint"]
        residue = _close_visible_cycle(app, window, cycle=2)
        merge_stage_manifest(
            workspace,
            {
                "restore_pid": os.getpid(),
                "restore_status": restored.status.value,
                "restore_actor_count": len(actor_ids),
                "restore_close": residue,
                "restore_automatic_saves": counters["automatic_saves"],
            },
        )
    finally:
        app.quit()


def _run_stale_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    from PySide6 import QtWidgets
    from tests.helpers.workspace_3d_mvp_e2e import (
        MESH_REF,
        e2e_mesh,
        empty_e2e_project,
        merge_stage_manifest,
        read_stage_manifest,
        workspace_paths,
    )

    from osw.core.project_io import load_project
    from osw.core.solver_setup import SetupReadiness
    from osw.core.workspace_3d import ActiveSceneRestoreStatus
    from osw.gui.interactive_results_view_model import (
        RESULT_DEFORMED_ACTOR_KEY,
        RESULT_SCALAR_ACTOR_KEY,
        RESULT_VECTOR_ACTOR_KEY,
    )
    from osw.gui.mesh_diagnostics_view_model import MESH_BAD_ELEMENTS_ACTOR_KEY
    from osw.mesh.identity import compute_mesh_fingerprint

    workspace = _workspace_root()
    repository_root = Path(__file__).resolve().parents[2]
    import pyvista
    import pyvistaqt

    assert pyvista.OFF_SCREEN is False
    assert pyvistaqt is not None
    counters = _install_product_guards(monkeypatch, repository_root)
    paths = workspace_paths(workspace)
    manifest = read_stage_manifest(workspace)
    changed = e2e_mesh(changed=True)
    assert compute_mesh_fingerprint(changed).digest == manifest["changed_fingerprint"]

    def saver(*_args: object, **_kwargs: object) -> None:
        counters["automatic_saves"] += 1
        pytest.fail("STALE must not save a Project.")

    assert QtWidgets.QApplication.instance() is None
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    window = _create_visible_window(
        app,
        workspace=workspace,
        project=empty_e2e_project(),
        cycle=3,
        extras={
            "project_saver": saver,
            "project_save_path_picker": _blocked_file_op("save during STALE"),
            "project_open_path_picker": lambda: str(paths["project"]),
            "project_loader": load_project,
        },
    )
    try:
        assert window.open_project() is True
        controller = window.active_scene_controller
        retained_ids = [item.id for item in window.current_project.selections]
        scene_result = window.central_viewport_panel.set_mesh(changed, mesh_ref=MESH_REF)
        assert scene_result is not None
        assert scene_result.rendered is True
        result = controller.active_scene_restore_result
        assert result.status is ActiveSceneRestoreStatus.STALE
        assert "MESH_FINGERPRINT_MISMATCH" in result.reason_codes
        camera = controller.session.get_camera_state()
        camera_delta = math.sqrt(
            sum((camera.position[index] - _CAMERA_POSITION[index]) ** 2 for index in range(3))
        )
        assert camera_delta > 0.25
        assert RESULT_SCALAR_ACTOR_KEY not in controller.actor_records
        assert RESULT_VECTOR_ACTOR_KEY not in controller.actor_records
        assert RESULT_DEFORMED_ACTOR_KEY not in controller.actor_records
        assert MESH_BAD_ELEMENTS_ACTOR_KEY not in controller.actor_records
        assert all(
            resolution.state.value == "STALE"
            for resolution in controller.named_selection_resolutions.values()
        )
        assert all(
            status.state is SetupReadiness.BLOCKED for status in controller.setup_statuses.values()
        )
        capture = next(iter(window.current_project.report_screenshots))
        capture_restore = controller.restore_captured_active_scene(capture)
        assert capture_restore.status is ActiveSceneRestoreStatus.STALE
        reloaded = load_project(paths["project"])
        assert [item.id for item in reloaded.selections] == retained_ids
        assert reloaded.active_scene is not None
        assert reloaded.active_scene.mesh_fingerprint == manifest["mesh_fingerprint"]
        residue = _close_visible_cycle(app, window, cycle=3)
        merge_stage_manifest(
            workspace,
            {
                "stale_pid": os.getpid(),
                "stale_status": result.status.value,
                "stale_reason_codes": list(result.reason_codes),
                "stale_close": residue,
                "stale_automatic_saves": counters["automatic_saves"],
                "retained_selection_ids": retained_ids,
            },
        )
    finally:
        app.quit()


def _child_env(workspace: Path, stage: str) -> dict[str, str]:
    env = os.environ.copy()
    env["OSW_RUN_PREPARED_INTERACTIVE"] = "1"
    env["OSW_E2E_STAGE"] = stage
    env["OSW_E2E_WORKSPACE_ROOT"] = str(workspace)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
    env.pop("PYTHONOPTIMIZE", None)
    for key in (
        "QT_QPA_PLATFORM",
        "PYVISTA_OFF_SCREEN",
        "QT_OPENGL",
        "QT_ANGLE_PLATFORM",
        "LIBGL_ALWAYS_SOFTWARE",
    ):
        env.pop(key, None)
    return env


def _orchestrate() -> None:
    from tests.helpers.workspace_3d_mvp_e2e import merge_stage_manifest, read_stage_manifest

    repository_root = Path(__file__).resolve().parents[2]
    workspace = Path(tempfile.mkdtemp(prefix="osw-mvp-e2e-")).resolve()
    assert workspace.is_dir()
    assert not _is_within(workspace, repository_root)
    test_id = (
        "tests/gui/test_3d_workspace_mvp_end_to_end_prepared_gui.py::"
        "test_3d_workspace_mvp_end_to_end_prepared_fresh_process"
    )
    try:
        pids: list[int] = []
        for stage in _STAGES:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    test_id,
                    "-q",
                    "--tb=short",
                ],
                cwd=str(repository_root),
                env=_child_env(workspace, stage),
                check=False,
                capture_output=True,
                text=True,
                timeout=240,
            )
            if completed.returncode != 0:
                raise AssertionError(
                    f"{stage} failed ({completed.returncode})\n"
                    f"{completed.stdout}\n{completed.stderr}"
                )
            manifest = read_stage_manifest(workspace)
            pid_key = {
                "AUTHOR": "author_pid",
                "RESTORE": "restore_pid",
                "STALE": "stale_pid",
            }[stage]
            pids.append(int(manifest[pid_key]))
        assert len(set(pids)) == 3
        assert os.getpid() not in pids
        merge_stage_manifest(
            workspace,
            {
                "orchestrator_pid": os.getpid(),
                "stage_pids": pids,
                "test_harness_processes": 3,
            },
        )
        shutil.rmtree(workspace)
        assert not workspace.exists()
    except Exception:
        raise
    else:
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)


def test_3d_workspace_mvp_end_to_end_prepared_fresh_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if _STAGE:
        if _STAGE not in _STAGES:
            pytest.fail(f"Unsupported OSW_E2E_STAGE={_STAGE!r}")
        {
            "AUTHOR": _run_author_stage,
            "RESTORE": _run_restore_stage,
            "STALE": _run_stale_stage,
        }[_STAGE](monkeypatch)
        return
    _orchestrate()
