"""Opt-in visible acceptance test for the prepared interactive 3D MVP."""

from __future__ import annotations

import builtins
import gc
import hashlib
import io
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from collections import Counter
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

_MESH_REF = "mesh-prepared-interactive-1"
_REPLACEMENT_MESH_REF = "mesh-prepared-interactive-2"
_DATASET_ID = "result-prepared-interactive-1"
_MESH_FINGERPRINT = "c71c671fec438602728abef4a154b9d68bad70cb412b76c43c69f2f80c6c63c0"
_REPLACEMENT_FINGERPRINT = "a51981c122efe68413295f4e1b5deff2eb0c3dd117c1966975e5bfaf47dad4da"


def _primary_mesh() -> object:
    from osw.mesh.mesh_model import MeshCellBlock, MeshData

    return MeshData(
        points=(
            (-4.0, -0.5, 0.0),
            (-3.0, -0.5, 0.0),
            (-4.0, 0.5, 0.0),
            (-4.0, -0.5, 1.0),
            (2.0, -0.1, 0.0),
            (6.0, -0.1, 0.0),
            (2.0, 0.15, 0.0),
            (2.0, -0.1, 0.25),
        ),
        cells=(
            MeshCellBlock(
                "tetra",
                (
                    (0, 1, 2, 3),
                    (4, 5, 6, 7),
                ),
            ),
        ),
    )


def _replacement_mesh() -> object:
    from osw.mesh.mesh_model import MeshCellBlock, MeshData

    return MeshData(
        points=(
            (-2.0, -1.0, 0.0),
            (-1.0, -1.0, 0.0),
            (-2.0, 0.0, 0.0),
            (-2.0, -1.0, 1.0),
        ),
        cells=(MeshCellBlock("tetra", ((0, 1, 2, 3),)),),
    )


def _result_dataset() -> object:
    from osw.core.result_dataset import ResultDataset, ResultField, ResultRow

    temperature_values = (10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0)
    vectors = (
        (1.0, 0.0, 0.0),
        (0.0, 2.0, 0.0),
        (0.0, 0.0, 3.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
    )
    return ResultDataset(
        dataset_id=_DATASET_ID,
        source="prepared-interactive-fixture",
        solver="fixture",
        analysis_type="static",
        fields=(
            ResultField(
                name="temperature",
                location="node",
                components=("value",),
                rows=tuple(
                    ResultRow(index, {"value": value})
                    for index, value in enumerate(temperature_values)
                ),
                unit="K",
            ),
            ResultField(
                name="pressure",
                location="cell",
                components=("value",),
                rows=(
                    ResultRow(0, {"value": 1.0}),
                    ResultRow(1, {"value": 2.0}),
                ),
                unit="Pa",
            ),
            ResultField(
                name="displacement",
                location="node",
                components=("ux", "uy", "uz"),
                rows=tuple(
                    ResultRow(
                        index,
                        {"ux": vector[0], "uy": vector[1], "uz": vector[2]},
                    )
                    for index, vector in enumerate(vectors)
                ),
                unit="mm",
            ),
        ),
        metadata={"mesh_ref": _MESH_REF},
    )


def _result_binding() -> object:
    from osw.core.result_mesh_binding import (
        RESULT_MESH_BINDING_SCHEMA_V2,
        ResultMeshBinding,
        ResultMeshSignature,
    )
    from osw.mesh.identity import MESH_IDENTITY_SCHEMA

    return ResultMeshBinding(
        mesh_ref=_MESH_REF,
        result_dataset_id=_DATASET_ID,
        schema=RESULT_MESH_BINDING_SCHEMA_V2,
        field_id="temperature",
        mesh_identity_schema=MESH_IDENTITY_SCHEMA,
        mesh_fingerprint=_MESH_FINGERPRINT,
        mesh_signature=ResultMeshSignature(node_count=8, cell_count=2),
    )


def _project() -> object:
    from osw.core.project_schema import Project, ProjectMetadata

    return Project(
        metadata=ProjectMetadata(name="Prepared interactive acceptance"),
        schema_version="0.3",
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
        app.processEvents(
            QtCore.QEventLoop.ProcessEventsFlag.AllEvents,
            25,
        )
        if predicate():
            return
    pytest.fail(f"Timed out while waiting for {label}.")


def _drag(
    widget: object,
    start: object,
    end: object,
    *,
    steps: int = 6,
) -> None:
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


def _actor_visibility(actor: object) -> bool:
    getter = getattr(actor, "GetVisibility", None)
    if callable(getter):
        return bool(getter())
    return bool(actor.visibility)


def _normalized_camera_to_focal(camera: object) -> tuple[float, float, float]:
    position = tuple(float(value) for value in camera.position)
    focal_point = tuple(float(value) for value in camera.focal_point)
    direction = tuple(focal_point[index] - position[index] for index in range(3))
    magnitude = math.sqrt(sum(value * value for value in direction))
    assert math.isfinite(magnitude) and magnitude > 0.0
    return tuple(value / magnitude for value in direction)


def _observer_signature(interactor: object) -> tuple[tuple[str, int], ...]:
    values = Counter(str(event) for event in interactor.iren._observers.values())
    return tuple(sorted(values.items()))


def _capability_value(report: str, label: str) -> str:
    prefix = label.casefold()
    for raw_line in report.splitlines():
        line = raw_line.strip()
        if line.casefold().startswith(prefix):
            return line.split(":", 1)[-1].strip()
    return ""


def _is_within(path: Path, root: Path) -> bool:
    return path.resolve(strict=False).is_relative_to(root.resolve(strict=False))


def _install_execution_guards(
    monkeypatch: pytest.MonkeyPatch,
    repository_root: Path,
) -> tuple[dict[str, int], Callable[..., object], Callable[..., object], Callable[..., object]]:
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
        "automatic_loads": 0,
        "repository_outputs": 0,
    }

    def blocked_solver(*_args: object, **_kwargs: object) -> object:
        counters["solver_calls"] += 1
        pytest.fail("Prepared interactive acceptance must not execute a solver.")

    def blocked_runner(*_args: object, **_kwargs: object) -> object:
        counters["runner_calls"] += 1
        pytest.fail("Prepared interactive acceptance must not execute a runner.")

    def blocked_subprocess(*_args: object, **_kwargs: object) -> object:
        counters["subprocess_calls"] += 1
        pytest.fail("Prepared interactive acceptance must not launch a subprocess.")

    def blocked_save(*_args: object, **_kwargs: object) -> object:
        counters["automatic_saves"] += 1
        pytest.fail("Prepared interactive acceptance must not save a Project.")

    def blocked_load(*_args: object, **_kwargs: object) -> object:
        counters["automatic_loads"] += 1
        pytest.fail("Prepared interactive acceptance must not load a Project.")

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

    def guarded_target(value: object) -> bool:
        if not isinstance(value, str | os.PathLike):
            return False
        return _is_within(Path(value), repository_root)

    def block_repository_output(value: object) -> None:
        if guarded_target(value):
            counters["repository_outputs"] += 1
            pytest.fail("Prepared interactive acceptance attempted repository output.")

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

    def guarded_os_open(
        path: object,
        flags: int,
        *args: object,
        **kwargs: object,
    ) -> int:
        write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        if flags & write_flags:
            block_repository_output(path)
        return real_os_open(path, flags, *args, **kwargs)

    def guarded_mkdir(
        path: object,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> None:
        block_repository_output(path)
        real_mkdir(path, mode, dir_fd=dir_fd)

    def guarded_makedirs(
        name: object,
        mode: int = 0o777,
        exist_ok: bool = False,
    ) -> None:
        block_repository_output(name)
        real_makedirs(name, mode=mode, exist_ok=exist_ok)

    monkeypatch.setattr(builtins, "open", guarded_builtin_open)
    monkeypatch.setattr(io, "open", guarded_io_open)
    monkeypatch.setattr(os, "open", guarded_os_open)
    monkeypatch.setattr(os, "mkdir", guarded_mkdir)
    monkeypatch.setattr(os, "makedirs", guarded_makedirs)
    return counters, blocked_save, blocked_load, blocked_load


def _close_visible_cycle(
    app: object,
    window: object,
    session: object,
    interactor: object,
    owned_windows: list[object],
    cycle: int,
) -> dict[str, object]:
    from PySide6 import QtCore, QtWidgets

    assert window.close()
    assert not window.isVisible()
    assert session.semantic_actor_ids == ()
    assert session._payloads == {}
    assert session._closed is True
    assert session.axes_visible is False
    assert session._isolation_snapshot is None
    assert session._visibility == {}
    assert session._pick_callback is None
    assert not interactor.render_timer.isActive()
    window.deleteLater()
    owned_windows.remove(window)
    QtCore.QCoreApplication.sendPostedEvents(
        None,
        QtCore.QEvent.Type.DeferredDelete,
    )
    _settle(
        app,
        lambda: len(QtWidgets.QApplication.topLevelWidgets()) == 0,
        f"cycle {cycle} top-level teardown",
    )
    assert QtWidgets.QApplication.topLevelWidgets() == []
    assert owned_windows == []
    return {
        "cycle": cycle,
        "session_count": 1,
        "rendered": True,
        "closed": True,
        "final_windows": 0,
        "residual_resources": 0,
    }


def test_3d_workspace_mvp_prepared_interactive_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for variable in (
        "QT_QPA_PLATFORM",
        "PYVISTA_OFF_SCREEN",
        "QT_OPENGL",
        "QT_ANGLE_PLATFORM",
        "LIBGL_ALWAYS_SOFTWARE",
    ):
        assert variable not in os.environ

    import PySide6
    import pyvista
    import pyvistaqt
    import qtpy
    import shiboken6
    from PySide6 import QtCore, QtGui, QtTest, QtWidgets
    from vtkmodules.vtkCommonCore import vtkVersion

    from osw.core.result_mesh_binding import ResultMeshBindingResolutionState
    from osw.core.selection import EntityKind
    from osw.core.selection_resolution import (
        CELL_ORDINAL_NAMESPACE,
        NODE_ORDINAL_NAMESPACE,
    )
    from osw.core.workspace_3d import ActiveSceneScreenshotRequest
    from osw.gui.interactive_results_view_model import (
        RESULT_COLORBAR_ACTOR_KEY,
        RESULT_PROBE_ACTOR_KEY,
        RESULT_SCALAR_ACTOR_KEY,
        RESULT_VECTOR_ACTOR_KEY,
    )
    from osw.gui.main_window import MainWindow
    from osw.gui.mesh_diagnostics_view_model import MESH_QUALITY_ACTOR_KEY
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererSession
    from osw.mesh.identity import compute_mesh_fingerprint
    from osw.post.result_probe import ResultProbeRequest, ResultProbeStatus

    assert QtWidgets.QApplication.instance() is None
    assert pyvista.OFF_SCREEN is False

    repository_root = Path(__file__).resolve().parents[2]
    durable_root = Path(sys.executable).resolve().parents[2]
    counters, blocked_save, blocked_load, blocked_mesh_read = _install_execution_guards(
        monkeypatch,
        repository_root,
    )

    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    assert QtGui.QGuiApplication.platformName().casefold() == "windows"
    assert QtWidgets.QApplication.instance() is app
    assert QtWidgets.QApplication.topLevelWidgets() == []

    output_root = Path(tempfile.mkdtemp(prefix="osw-prepared-interactive-")).resolve()
    assert output_root.is_dir()
    assert not _is_within(output_root, repository_root)
    assert not _is_within(output_root, durable_root)

    owned_windows: list[object] = []
    cycle_evidence: list[dict[str, object]] = []

    def create_window(cycle: int) -> object:
        window = MainWindow(
            project=_project(),
            metadata_mesh_reader=blocked_mesh_read,
            project_loader=blocked_load,
            project_saver=blocked_save,
            artifact_dir=output_root / f"artifacts-{cycle}",
            report_directory=output_root / f"reports-{cycle}",
        )
        owned_windows.append(window)
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
        return window

    try:
        mesh = _primary_mesh()
        replacement_mesh = _replacement_mesh()
        primary_fingerprint = compute_mesh_fingerprint(mesh)
        replacement_fingerprint = compute_mesh_fingerprint(replacement_mesh)
        assert primary_fingerprint.digest == _MESH_FINGERPRINT
        assert replacement_fingerprint.digest == _REPLACEMENT_FINGERPRINT
        assert primary_fingerprint.digest != replacement_fingerprint.digest

        window = create_window(1)
        controller = window.active_scene_controller
        session = controller.session
        assert isinstance(session, PyVistaQtRendererSession)
        interactor = session.hosted_widget
        assert isinstance(interactor, pyvistaqt.QtInteractor)
        assert window.central_viewport_panel.hosted_widget is interactor
        assert window.central_viewport_panel.interactive_available is True
        assert controller.session is session

        interactor.setFocus()
        interactor.render()
        render_window = interactor.render_window
        renderer = interactor.renderer
        assert render_window is not None
        assert renderer is not None
        assert int(render_window.GetNeverRendered()) == 0
        report = str(render_window.ReportCapabilities())
        assert report.strip()
        vendor = _capability_value(report, "OpenGL vendor string")
        renderer_name = _capability_value(report, "OpenGL renderer string")
        opengl_version = _capability_value(report, "OpenGL version string")
        assert vendor and renderer_name and opengl_version
        report_sha256 = hashlib.sha256(report.encode("utf-8")).hexdigest()
        software_indicators = (
            "llvmpipe",
            "softpipe",
            "software",
            "microsoft basic render driver",
        )
        renderer_text = " ".join((vendor, renderer_name, opengl_version, report)).casefold()
        assert not any(item in renderer_text for item in software_indicators)
        renderer_classification = "HARDWARE_OPENGL_RENDERER_OBSERVED"
        render_window_class = str(render_window.GetClassName())
        assert render_window_class

        generation_before_load = controller.generation
        scene_result = window.central_viewport_panel.set_mesh(
            mesh,
            mesh_ref=_MESH_REF,
        )
        assert scene_result is not None
        assert scene_result.rendered, (
            "Initial 3D scene load entered fallback: "
            f"reason={controller.fallback_reason!r}; "
            f"generation={controller.generation}; "
            f"actor_ids={sorted(controller.actor_records)}"
        )
        assert controller.fallback_reason == ""
        assert controller.generation == generation_before_load + 1
        assert controller.current_mesh_fingerprint == primary_fingerprint
        assert len(mesh.points) == 8
        assert sum(block.count for block in mesh.cells) == 2
        bounds = (
            tuple(min(point[index] for point in mesh.points) for index in range(3)),
            tuple(max(point[index] for point in mesh.points) for index in range(3)),
        )
        assert bounds == ((-4.0, -0.5, 0.0), (6.0, 0.5, 1.0))
        assert set(controller.actor_records) == {"base_mesh", "wireframe"}
        assert controller.actor_records["base_mesh"].category == "geometry"
        assert controller.actor_records["base_mesh"].pickable is True
        assert controller.actor_records["base_mesh"].isolation_eligible is True
        assert controller.actor_records["base_mesh"].is_helper is False
        assert session.semantic_actor_ids == ("base_mesh", "wireframe")
        base_dataset = session._actors["base_mesh"].mapper.dataset
        assert isinstance(base_dataset, pyvista.UnstructuredGrid)
        assert base_dataset.n_points == 8
        assert base_dataset.n_cells == 2
        assert bool(renderer.HasViewProp(session._actors["base_mesh"]))
        assert int(render_window.GetNeverRendered()) == 0

        assert controller.disable_picking()
        camera_initial = session.get_camera_state()
        assert controller.fit_to_scene()
        fit_camera = session.get_camera_state()
        assert fit_camera.focal_point == pytest.approx((1.0, 0.0, 0.5))
        assert fit_camera.position is not None
        assert all(math.isfinite(value) for value in fit_camera.position)
        fit_distance = math.sqrt(
            sum(
                (fit_camera.position[index] - fit_camera.focal_point[index]) ** 2
                for index in range(3)
            )
        )
        assert fit_distance > 5.0
        assert all(math.isfinite(value) for value in interactor.camera.clipping_range)

        preset_directions = {
            "front": (0.0, 1.0, 0.0),
            "back": (0.0, -1.0, 0.0),
            "left": (1.0, 0.0, 0.0),
            "right": (-1.0, 0.0, 0.0),
            "top": (0.0, 0.0, -1.0),
            "bottom": (0.0, 0.0, 1.0),
        }
        for preset, expected_direction in preset_directions.items():
            assert controller.set_camera_preset(preset)
            camera = session.get_camera_state()
            assert _normalized_camera_to_focal(camera) == pytest.approx(expected_direction)
            assert camera.focal_point == pytest.approx((1.0, 0.0, 0.5))
        assert controller.set_camera_preset("isometric")
        isometric_camera = session.get_camera_state()
        assert all(
            isometric_camera.position[index] > isometric_camera.focal_point[index]
            for index in range(3)
        )
        assert controller.set_camera_preset("top")
        camera_preset = session.get_camera_state()
        assert controller.set_camera_preset("top")
        assert _normalized_camera_to_focal(session.get_camera_state()) == pytest.approx(
            _normalized_camera_to_focal(camera_preset)
        )
        assert camera_preset.position != camera_initial.position
        assert controller.set_interaction_mode("orbit")
        center = QtCore.QPoint(interactor.width() // 2, interactor.height() // 2)
        orbit_end = QtCore.QPoint(center.x() + 80, center.y() + 35)
        _drag(interactor, center, orbit_end)
        interactor.render()
        camera_orbit = session.get_camera_state()
        assert camera_orbit.position != camera_preset.position

        assert controller.set_representation("wireframe")
        assert not _actor_visibility(session._actors["base_mesh"])
        assert _actor_visibility(session._actors["wireframe"])
        assert controller.set_representation("surface")
        assert _actor_visibility(session._actors["base_mesh"])
        assert not _actor_visibility(session._actors["wireframe"])
        assert controller.set_representation("surface_with_edges")
        assert _actor_visibility(session._actors["base_mesh"])
        assert _actor_visibility(session._actors["wireframe"])
        assert controller.isolate_actor("wireframe")
        assert not _actor_visibility(session._actors["base_mesh"])
        assert _actor_visibility(session._actors["wireframe"])
        assert controller.isolate_actor("base_mesh")
        assert _actor_visibility(session._actors["base_mesh"])
        assert not _actor_visibility(session._actors["wireframe"])
        assert controller.clear_isolation()
        assert _actor_visibility(session._actors["base_mesh"])
        assert _actor_visibility(session._actors["wireframe"])
        assert controller.hide_actor("wireframe")
        assert not _actor_visibility(session._actors["wireframe"])
        assert controller.show_actor("wireframe")
        assert _actor_visibility(session._actors["wireframe"])
        assert controller.set_representation("surface")
        assert _actor_visibility(session._actors["base_mesh"])
        assert not _actor_visibility(session._actors["wireframe"])
        assert controller.set_axes_visible(False)
        assert interactor.renderer.axes_enabled is False
        assert controller.set_axes_visible(True)
        assert interactor.renderer.axes_enabled is True
        axes_actor = interactor.renderer.axes_actor
        assert axes_actor is not None
        assert controller.set_axes_visible(True)
        assert interactor.renderer.axes_actor is axes_actor
        assert controller.set_camera_preset("top")
        assert controller.fit_to_scene()
        interactor.render()
        print("OSW_PREPARED_SCENE_INTERACTION_CORE_PASS", flush=True)

        render_width, render_height = (int(value) for value in render_window.GetSize())
        assert render_width > 0 and render_height > 0
        point_world = tuple(float(value) for value in mesh.points[1])
        point_display = _world_to_display(renderer, point_world)
        point_qx, point_qy, device_pixel_ratio = _display_to_qt(
            interactor,
            point_display,
        )
        assert abs(render_width - round(interactor.width() * device_pixel_ratio)) <= 2
        assert abs(render_height - round(interactor.height() * device_pixel_ratio)) <= 2

        assert controller.set_pick_mode("node")
        point_notifications: list[object] = []
        controller.set_selection_listener(
            lambda: point_notifications.append(controller.current_selection_target)
        )
        assert session._pick_mode == "node"
        assert interactor.picking._picker_in_use is True
        point_picker = interactor.iren.picker
        assert "PointPicker" in type(point_picker).__name__
        assert _observer_signature(interactor)
        QtTest.QTest.mouseClick(
            interactor,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
            QtCore.QPoint(point_qx, point_qy),
        )
        _settle(
            app,
            lambda: len(point_notifications) == 1,
            "one native point-selection notification",
        )
        app.processEvents()
        assert len(point_notifications) == 1
        point_target = point_notifications[0]
        assert point_target is controller.current_selection_target
        assert point_target is not None
        assert point_target.kind is EntityKind.NODE
        assert point_target.ids == (1,)
        assert point_target.locator is not None
        assert point_target.locator.entity_ids == (1,)
        assert point_target.locator.id_namespace == NODE_ORDINAL_NAMESPACE
        assert point_target.locator.mesh_fingerprint == _MESH_FINGERPRINT
        assert int(point_picker.GetPointId()) == 1
        point_highlight_actor = session._actors["current_selection"]
        point_highlight_record = controller.actor_records["current_selection"]
        assert point_highlight_record.category == "selection"
        assert point_highlight_record.is_helper is True
        assert point_highlight_record.isolation_eligible is False
        print("OSW_PREPARED_NATIVE_POINT_EVENT_PASS", flush=True)

        controller.set_selection_listener(None)
        assert controller.set_selection_operation("add")
        assert session._selection_operation == "add"
        assert controller.handle_pick(
            {
                "generation": controller.generation,
                "mesh_ref": _MESH_REF,
                "mesh_fingerprint": _MESH_FINGERPRINT,
                "entity_kind": "node",
                "backend_index": 2,
                "intent": "add",
            }
        )
        assert controller.current_selection_target is not None
        assert controller.current_selection_target.ids == (1, 2)
        assert controller.set_selection_operation("subtract")
        assert controller.handle_pick(
            {
                "generation": controller.generation,
                "mesh_ref": _MESH_REF,
                "mesh_fingerprint": _MESH_FINGERPRINT,
                "entity_kind": "node",
                "backend_index": 1,
                "intent": "subtract",
            }
        )
        assert controller.current_selection_target is not None
        assert controller.current_selection_target.ids == (2,)
        assert controller.invert_current_selection()
        assert controller.current_selection_target is not None
        assert controller.current_selection_target.ids == (0, 1, 3, 4, 5, 6, 7)

        from osw.core.selection_resolution import create_named_selection

        prepared_selection = create_named_selection(
            (),
            controller.current_selection_target,
            controller.current_selection_resolution,
            selection_id="prepared-active-nodes",
            name="Prepared Active Nodes",
        )[0]
        controller.set_named_selections((prepared_selection,))
        assert controller.set_active_named_selection_ids((prepared_selection.id,))
        assert controller.active_named_selection_ids == (prepared_selection.id,)
        assert "named_selection:prepared-active-nodes" in session.semantic_actor_ids
        assert "active_named_selection:prepared-active-nodes" in session.semantic_actor_ids
        assert bool(
            renderer.HasViewProp(session._actors["active_named_selection:prepared-active-nodes"])
        )
        print("OSW_PREPARED_NATIVE_MULTI_NAMED_SELECTION_PASS", flush=True)

        assert controller.set_selection_operation("replace")
        assert controller.set_pick_mode("cell")
        cell_notifications: list[object] = []
        controller.set_selection_listener(
            lambda: cell_notifications.append(controller.current_selection_target)
        )
        assert session._pick_mode == "cell"
        assert interactor.picking._picker_in_use is True
        assert type(interactor.iren._style_class).__name__ == "InteractorStyleRubberBandPick"
        projected_target = tuple(
            _display_to_qt(
                interactor,
                _world_to_display(renderer, tuple(float(value) for value in mesh.points[index])),
            )
            for index in (4, 5, 6, 7)
        )
        left = max(3, min(item[0] for item in projected_target) - 8)
        right = min(interactor.width() - 4, max(item[0] for item in projected_target) + 8)
        top = max(3, min(item[1] for item in projected_target) - 8)
        bottom = min(
            interactor.height() - 4,
            max(item[1] for item in projected_target) + 8,
        )
        assert left < right and top < bottom
        cell_start = QtCore.QPoint(left, top)
        cell_end = QtCore.QPoint(right, bottom)
        _drag(interactor, cell_start, cell_end)
        _settle(
            app,
            lambda: len(cell_notifications) == 1,
            "one native cell rectangle-selection notification",
        )
        app.processEvents()
        assert len(cell_notifications) == 1
        assert len(point_notifications) == 1
        cell_target = cell_notifications[0]
        assert cell_target is controller.current_selection_target
        assert cell_target is not None
        assert cell_target.kind is EntityKind.CELL
        assert cell_target.ids == ("0:1",)
        assert cell_target.locator is not None
        assert cell_target.locator.entity_ids == ("0:1",)
        assert cell_target.locator.id_namespace == CELL_ORDINAL_NAMESPACE
        assert cell_target.locator.mesh_fingerprint == _MESH_FINGERPRINT
        pick_area = tuple(int(value) for value in renderer.get_pick_position())
        assert len(pick_area) == 4
        assert min(pick_area) >= 0
        assert pick_area[0] != pick_area[2]
        assert pick_area[1] != pick_area[3]
        cell_highlight_actor = session._actors["current_selection"]
        assert cell_highlight_actor is not point_highlight_actor
        assert not bool(renderer.HasViewProp(point_highlight_actor))
        assert bool(renderer.HasViewProp(cell_highlight_actor))
        print("OSW_PREPARED_NATIVE_CELL_RECTANGLE_EVENT_PASS", flush=True)

        dataset = _result_dataset()
        binding = _result_binding()
        resolution = controller.set_interactive_result_dataset(
            dataset,
            binding,
            result_ref_id="result-ref-prepared-interactive",
        )
        assert resolution is not None
        assert resolution.state is ResultMeshBindingResolutionState.RESOLVED

        scalar = controller.set_scalar_result(
            "temperature",
            component="value",
            colorbar_visible=True,
        )
        assert scalar.applied is True
        assert scalar.association == "point"
        assert scalar.data_range == (10.0, 80.0)
        assert scalar.display_range == (10.0, 80.0)
        assert {RESULT_SCALAR_ACTOR_KEY, RESULT_COLORBAR_ACTOR_KEY}.issubset(
            controller.actor_records
        )

        vector = controller.set_vector_result(
            "displacement",
            components=("ux", "uy", "uz"),
            maximum_glyph_count=2,
            scale=1.0,
        )
        assert vector.applied is True
        assert vector.candidate_count == 3
        assert vector.sampled_count == 2
        assert vector.zero_vector_count == 5
        assert vector.selected_candidate_ranks == (0, 2)
        assert vector.stable_entity_keys == (0, 2)
        assert RESULT_VECTOR_ACTOR_KEY in controller.actor_records

        analysis = controller.analyze_mesh_quality()
        assert analysis is not None
        assert analysis.mesh_fingerprint.digest == _MESH_FINGERPRINT
        assert analysis.evaluated_count == 2
        assert analysis.minimum == pytest.approx(math.sqrt(2.0))
        assert analysis.maximum == pytest.approx(math.sqrt(257.0))
        assert controller.set_mesh_quality_threshold(5.0)
        assert controller.set_mesh_quality_highlight_visible(True)
        diagnostics = controller.mesh_quality_view_model
        assert diagnostics.bad_cell_keys == ("0:1",)
        assert diagnostics.table_bad_cell_keys == ("0:1",)
        assert MESH_QUALITY_ACTOR_KEY in controller.actor_records

        colorbar_record = controller.actor_records[RESULT_COLORBAR_ACTOR_KEY]
        assert colorbar_record.category == "helper"
        assert colorbar_record.is_helper is True
        assert colorbar_record.isolation_eligible is False
        colorbar_visibility = _actor_visibility(session._actors[RESULT_COLORBAR_ACTOR_KEY])
        eligible_visibility = {
            semantic_id: record.visible
            for semantic_id, record in controller.actor_records.items()
            if record.isolation_eligible
        }
        assert controller.isolate_actor(RESULT_VECTOR_ACTOR_KEY)
        assert controller.current_selection_target is None
        assert "current_selection" not in controller.actor_records
        assert _actor_visibility(session._actors[RESULT_VECTOR_ACTOR_KEY])
        assert _actor_visibility(session._actors[RESULT_COLORBAR_ACTOR_KEY]) is (
            colorbar_visibility
        )
        assert controller.clear_isolation()
        assert {
            semantic_id: controller.actor_records[semantic_id].visible
            for semantic_id in eligible_visibility
        } == eligible_visibility

        assert controller.clear_scalar_result()
        assert RESULT_SCALAR_ACTOR_KEY not in controller.actor_records
        assert RESULT_COLORBAR_ACTOR_KEY not in controller.actor_records
        assert RESULT_VECTOR_ACTOR_KEY in controller.actor_records
        assert MESH_QUALITY_ACTOR_KEY in controller.actor_records
        visibility_before_isolate = {
            semantic_id: _actor_visibility(session._actors[semantic_id])
            for semantic_id in ("base_mesh", "wireframe", RESULT_VECTOR_ACTOR_KEY)
        }
        assert controller.set_mesh_quality_isolated(True)
        assert not _actor_visibility(session._actors["base_mesh"])
        assert not _actor_visibility(session._actors["wireframe"])
        assert _actor_visibility(session._actors[RESULT_VECTOR_ACTOR_KEY])
        assert _actor_visibility(session._actors[MESH_QUALITY_ACTOR_KEY])
        assert controller.restore_mesh_quality_visibility()
        assert {
            semantic_id: _actor_visibility(session._actors[semantic_id])
            for semantic_id in ("base_mesh", "wireframe", RESULT_VECTOR_ACTOR_KEY)
        } == visibility_before_isolate

        scalar = controller.set_scalar_result(
            "temperature",
            component="value",
            colorbar_visible=True,
        )
        assert scalar.applied is True
        assert RESULT_VECTOR_ACTOR_KEY in controller.actor_records
        assert MESH_QUALITY_ACTOR_KEY in controller.actor_records

        probe = controller.probe_result(
            ResultProbeRequest(
                dataset_id=_DATASET_ID,
                field_name="temperature",
                component="value",
                association="point",
                stable_entity_key=1,
                mesh_fingerprint=_MESH_FINGERPRINT,
            )
        )
        assert probe.status is ResultProbeStatus.RESOLVED
        assert probe.stable_entity_key == 1
        assert probe.value == 20.0
        assert probe.unit == "K"
        assert RESULT_PROBE_ACTOR_KEY in controller.actor_records

        expected_actors = {
            "base_mesh",
            "wireframe",
            RESULT_SCALAR_ACTOR_KEY,
            RESULT_COLORBAR_ACTOR_KEY,
            RESULT_VECTOR_ACTOR_KEY,
            MESH_QUALITY_ACTOR_KEY,
            RESULT_PROBE_ACTOR_KEY,
        }
        assert expected_actors.issubset(controller.actor_records)
        assert expected_actors.issubset(session.semantic_actor_ids)
        assert len(session.semantic_actor_ids) == len(set(session.semantic_actor_ids))
        assert set(session._actors) == set(session.semantic_actor_ids)
        assert (
            len(tuple(key for key in session.semantic_actor_ids if key == MESH_QUALITY_ACTOR_KEY))
            == 1
        )
        for semantic_id in expected_actors:
            native_actor = session._actors[semantic_id]
            assert native_actor is not None, semantic_id
            assert bool(renderer.HasViewProp(native_actor))
        assert _actor_visibility(session._actors[RESULT_VECTOR_ACTOR_KEY])
        assert _actor_visibility(session._actors[MESH_QUALITY_ACTOR_KEY])
        assert _actor_visibility(session._actors[RESULT_PROBE_ACTOR_KEY])
        print("OSW_PREPARED_ACTOR_COHABITATION_PASS", flush=True)

        screenshot_path = output_root / "active-session.png"
        capture = controller.capture_active_scene_screenshot(
            ActiveSceneScreenshotRequest(
                record_id="prepared-interactive-active-session",
                output_path=str(screenshot_path),
                caption="Prepared interactive active session",
            )
        )
        assert capture.status == "CAPTURED"
        assert capture.record is not None
        assert capture.record.path == str(screenshot_path)
        assert screenshot_path.is_file()
        screenshot_bytes = screenshot_path.read_bytes()
        assert screenshot_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        assert len(screenshot_bytes) > 0
        screenshot_sha256 = hashlib.sha256(screenshot_bytes).hexdigest()
        assert capture.image_sha256 == screenshot_sha256
        assert capture.image_byte_length == len(screenshot_bytes)
        encoded = QtCore.QByteArray(screenshot_bytes)
        decoded = QtGui.QImage.fromData(encoded)
        assert not decoded.isNull()
        screenshot_width = decoded.width()
        screenshot_height = decoded.height()
        assert screenshot_width > 0 and screenshot_height > 0
        assert capture.image_size == (screenshot_width, screenshot_height)
        rgba_image = decoded.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)
        rgba_bytes = bytes(rgba_image.constBits())
        pixel_values = memoryview(rgba_bytes).cast("I")
        sampled_color_count = len(set(pixel_values))
        assert sampled_color_count > 1
        provenance = capture.record.metadata["osw.active_scene.provenance"]
        assert provenance["mesh_fingerprint"] == _MESH_FINGERPRINT
        assert provenance["image_sha256"] == screenshot_sha256
        assert provenance["image_byte_length"] == len(screenshot_bytes)
        screenshot_bytes_count = len(screenshot_bytes)
        del pixel_values
        del rgba_bytes
        del rgba_image
        del decoded
        del encoded
        del screenshot_bytes
        gc.collect()
        renamed_screenshot = output_root / "active-session-renamed.png"
        assert screenshot_path.rename(renamed_screenshot) == renamed_screenshot
        assert renamed_screenshot.is_file() and not screenshot_path.exists()
        assert renamed_screenshot.rename(screenshot_path) == screenshot_path
        assert screenshot_path.is_file() and not renamed_screenshot.exists()
        screenshot_path.unlink()
        assert not screenshot_path.exists()
        assert controller.session is session
        assert not session._closed
        print("OSW_PREPARED_ACTIVE_SESSION_SCREENSHOT_PASS", flush=True)

        controller_identity = id(controller)
        session_identity = id(session)
        interactor_identity = id(interactor)
        old_generation = controller.generation
        old_actor_handles = dict(session._actors)
        old_actor_handle_ids = {id(actor) for actor in old_actor_handles.values()}
        observer_signature_before = _observer_signature(interactor)
        render_timer = interactor.render_timer
        render_timer_active_before = render_timer.isActive()

        replacement_result = window.central_viewport_panel.set_mesh(
            replacement_mesh,
            mesh_ref=_REPLACEMENT_MESH_REF,
        )
        assert replacement_result is not None
        assert id(window.active_scene_controller) == controller_identity
        assert id(controller.session) == session_identity
        assert id(session.hosted_widget) == interactor_identity
        assert controller.generation == old_generation + 1
        assert controller.current_mesh_fingerprint == replacement_fingerprint
        assert controller.current_selection_target is None
        assert controller.mesh_quality_analysis is None
        assert controller.mesh_quality_view_model.analysis_available is False
        assert controller.interactive_result_resolution is not None
        assert (
            controller.interactive_result_resolution.state is ResultMeshBindingResolutionState.STALE
        )
        assert controller.interactive_result_resolution.reason_code == "MESH_REF_MISMATCH"
        assert set(controller.actor_records) == {"base_mesh", "wireframe"}
        assert session.semantic_actor_ids == ("base_mesh", "wireframe")
        assert not old_actor_handle_ids.intersection(
            id(actor) for actor in session._actors.values()
        )
        for old_actor in old_actor_handles.values():
            assert not bool(renderer.HasViewProp(old_actor))
        assert _observer_signature(interactor) == observer_signature_before
        assert interactor.render_timer is render_timer
        assert render_timer.isActive() is render_timer_active_before
        interactor.render()
        assert int(render_window.GetNeverRendered()) == 0
        print("OSW_PREPARED_SAME_SESSION_MESH_REPLACEMENT_PASS", flush=True)

        cycle_evidence.append(
            _close_visible_cycle(
                app,
                window,
                session,
                interactor,
                owned_windows,
                1,
            )
        )

        for cycle in (2, 3):
            cycle_window = create_window(cycle)
            cycle_controller = cycle_window.active_scene_controller
            cycle_session = cycle_controller.session
            assert isinstance(cycle_session, PyVistaQtRendererSession)
            cycle_interactor = cycle_session.hosted_widget
            assert isinstance(cycle_interactor, pyvistaqt.QtInteractor)
            assert cycle_controller.session is cycle_session
            assert cycle_window.central_viewport_panel.hosted_widget is cycle_interactor
            cycle_window.central_viewport_panel.set_mesh(
                replacement_mesh if cycle == 2 else mesh,
                mesh_ref=_REPLACEMENT_MESH_REF if cycle == 2 else _MESH_REF,
            )
            cycle_interactor.render()
            assert int(cycle_interactor.render_window.GetNeverRendered()) == 0
            assert cycle_session.semantic_actor_ids == ("base_mesh", "wireframe")
            cycle_evidence.append(
                _close_visible_cycle(
                    app,
                    cycle_window,
                    cycle_session,
                    cycle_interactor,
                    owned_windows,
                    cycle,
                )
            )

        assert len(cycle_evidence) == 3
        assert all(item["final_windows"] == 0 for item in cycle_evidence)
        assert QtWidgets.QApplication.topLevelWidgets() == []
        print("OSW_PREPARED_THREE_VISIBLE_LIFECYCLE_CYCLES_PASS", flush=True)

        assert counters == {
            "solver_calls": 0,
            "runner_calls": 0,
            "subprocess_calls": 0,
            "automatic_saves": 0,
            "automatic_loads": 0,
            "repository_outputs": 0,
        }
        assert list(output_root.iterdir()) == []
        output_root.rmdir()
        assert not output_root.exists()

        evidence = {
            "versions": {
                "python": sys.version.split()[0],
                "pyside6": PySide6.__version__,
                "pyvista": pyvista.__version__,
                "pyvistaqt": pyvistaqt.__version__,
                "qtpy": qtpy.__version__,
                "vtk": vtkVersion().GetVTKVersion(),
            },
            "qt_platform": QtGui.QGuiApplication.platformName(),
            "render_window_class": render_window_class,
            "opengl": {
                "classification": renderer_classification,
                "vendor": vendor,
                "renderer": renderer_name,
                "version": opengl_version,
                "capability_report_bytes": len(report.encode("utf-8")),
                "capability_report_sha256": report_sha256,
            },
            "mesh": {
                "fingerprint": _MESH_FINGERPRINT,
                "points": 8,
                "cells": 2,
                "bounds": bounds,
            },
            "point_event": {
                "route": "PySide6.QtTest.QTest.mouseClick",
                "world": point_world,
                "vtk_display": point_display,
                "qt": (point_qx, point_qy),
                "device_pixel_ratio": device_pixel_ratio,
                "notifications": len(point_notifications),
                "stable_locator": (1,),
                "namespace": NODE_ORDINAL_NAMESPACE,
            },
            "cell_event": {
                "route": "PySide6.QtTest.QTest press-move-release",
                "qt_rectangle": (left, top, right, bottom),
                "vtk_pick_area": pick_area,
                "notifications": len(cell_notifications),
                "stable_locator": ("0:1",),
                "namespace": CELL_ORDINAL_NAMESPACE,
            },
            "result_actors": sorted(expected_actors),
            "scalar_range": scalar.data_range,
            "vector": {
                "candidate_count": vector.candidate_count,
                "sampled_count": vector.sampled_count,
                "selected_candidate_ranks": vector.selected_candidate_ranks,
                "stable_entity_keys": vector.stable_entity_keys,
                "zero_vector_count": vector.zero_vector_count,
            },
            "diagnostics_bad_cells": diagnostics.bad_cell_keys,
            "probe": {
                "stable_entity_key": probe.stable_entity_key,
                "value": probe.value,
                "unit": probe.unit,
            },
            "screenshot": {
                "width": screenshot_width,
                "height": screenshot_height,
                "bytes": screenshot_bytes_count,
                "sampled_colors": sampled_color_count,
                "sha256": screenshot_sha256,
                "deleted_before_teardown": True,
            },
            "replacement": {
                "same_controller": True,
                "same_session": True,
                "same_interactor": True,
                "old_fingerprint": _MESH_FINGERPRINT,
                "new_fingerprint": _REPLACEMENT_FINGERPRINT,
                "old_generation": old_generation,
                "new_generation": old_generation + 1,
                "remaining_actors": ("base_mesh", "wireframe"),
                "observer_signature": observer_signature_before,
                "timer_reused": True,
            },
            "cycles": cycle_evidence,
            "final_top_level_windows": len(QtWidgets.QApplication.topLevelWidgets()),
            "guards": counters,
            "temporary_output_removed": True,
        }
        print(
            "OSW_PREPARED_INTERACTIVE_EVIDENCE="
            + json.dumps(evidence, sort_keys=True, separators=(",", ":")),
            flush=True,
        )
    finally:
        for owned_window in tuple(owned_windows):
            if shiboken6.isValid(owned_window):
                owned_window.close()
                owned_window.deleteLater()
        owned_windows.clear()
        QtCore.QCoreApplication.sendPostedEvents(
            None,
            QtCore.QEvent.Type.DeferredDelete,
        )
        app.processEvents()
        if output_root.exists():
            for item in output_root.iterdir():
                assert item.is_file()
                item.unlink()
            output_root.rmdir()
