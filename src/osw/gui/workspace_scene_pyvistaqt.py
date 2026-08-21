"""Lazy PyVistaQt renderer session for the central 3D workspace.

This module imports neither PyVista nor PyVistaQt at module import time.  One
session owns its QtInteractor, native actors, camera, axes state, transient
clipping state, timer, and backend callbacks until explicit idempotent close.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import suppress
from importlib import import_module
from pathlib import Path
from typing import Any

from osw.core.workspace_3d import ActiveSceneCameraState
from osw.gui.interactive_results_view_model import (
    RESULT_COLORBAR_ACTOR_KEY,
    RESULT_PROBE_ACTOR_KEY,
    RESULT_SCALAR_ACTOR_KEY,
    RESULT_VECTOR_ACTOR_KEY,
    ResultColorbarSpec,
    ResultProbeOverlaySpec,
    ScalarResultOverlaySpec,
)
from osw.gui.mesh_diagnostics_view_model import (
    MESH_QUALITY_ACTOR_KEY,
    MeshQualityOverlaySpec,
)
from osw.gui.setup_overlay_view_model import SetupOverlaySpec
from osw.gui.workspace_scene_controller import (
    SceneRendererInitializationError,
)
from osw.post.pyvista_scene import (
    PyVistaSceneConfig,
    build_scene_state,
    mesh_data_to_pyvista_dataset,
)
from osw.post.result_field_mapping import ResultVectorGlyphSpec
from osw.post.scene_model import (
    SceneScreenshotRecord,
    SceneViewState,
    build_screenshot_record,
)

_CAMERA_VECTORS = {
    "front": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    "back": ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
    "left": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "right": ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    "top": ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    "bottom": ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    "isometric": ((1.0, 1.0, 1.0), (0.0, 0.0, 1.0)),
}
_REPRESENTATION_VISIBILITY = {
    "surface": {"base_mesh": True, "wireframe": False},
    "wireframe": {"base_mesh": False, "wireframe": True},
    "surface_with_edges": {"base_mesh": True, "wireframe": True},
}
_CLIP_NORMALS = {
    "x": (1.0, 0.0, 0.0),
    "y": (0.0, 1.0, 0.0),
    "z": (0.0, 0.0, 1.0),
}


def pyvistaqt_missing_message() -> str:
    return (
        "PyVistaQt is not installed. Install the optional GUI and visualization "
        "extras with `python -m pip install -e .[gui,viz]` to enable the "
        "interactive 3D workspace."
    )


class PyVistaQtRendererSession:
    """Own one embedded QtInteractor and all of its native scene resources."""

    backend_kind = "pyvistaqt"
    capabilities = frozenset(
        {
            "mesh-preview",
            "scene-screenshot",
            "semantic-actors",
            "interactive",
            "hosted-widget",
            "camera",
            "representation",
            "semantic-visibility",
            "axes",
            "clipping",
            "picking",
            "selection-overlays",
            "setup-overlays",
            "mesh-quality-overlays",
            "result-overlays",
        }
    )

    def __init__(
        self,
        parent: object,
        *,
        pyvista_module: Any,
        interactor_factory: Callable[..., Any],
    ) -> None:
        self._pyvista = pyvista_module
        self._interactor: Any | None = None
        self._actors: dict[str, Any] = {}
        self._payloads: dict[str, tuple[object, int]] = {}
        self._visibility = {
            "base_mesh": True,
            "wireframe": False,
        }
        self._representation = "surface"
        self._axes_visible = True
        self._clip_axis: str | None = None
        self._clip_origin = 0.0
        self._pick_mode: str | None = None
        self._pick_callback: Callable[[object], object] | None = None
        self._closed = False
        try:
            self._interactor = interactor_factory(
                parent=parent,
                auto_update=False,
            )
            set_background = getattr(self._interactor, "set_background", None)
            if callable(set_background):
                set_background("#111827")
            enable_trackball = getattr(
                self._interactor,
                "enable_trackball_style",
                None,
            )
            if callable(enable_trackball):
                enable_trackball()
            self.set_axes_visible(True)
        except Exception as exc:
            self.close()
            raise SceneRendererInitializationError(
                f"PyVistaQt interactive session initialization failed: {exc}",
                partial_session=self,
            ) from exc

    @property
    def hosted_widget(self) -> object | None:
        return self._interactor

    @property
    def semantic_actor_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._actors))

    def clear(self) -> None:
        if self._closed:
            return
        self.disable_picking()
        for semantic_id in tuple(self._actors):
            self._remove_native_actor(semantic_id)
        self._payloads.clear()
        self._visibility = {
            "base_mesh": True,
            "wireframe": False,
        }
        self._clip_axis = None
        self._clip_origin = 0.0

    def set_pick_mode(
        self,
        mode: str,
        callback: Callable[[object], object],
    ) -> None:
        """Enable one native point/cell picker with renderer-neutral events."""

        if mode not in {"node", "cell"}:
            raise ValueError(f"Unsupported pick mode: {mode}")
        if not callable(callback):
            raise TypeError("Pick callback must be callable.")
        self._disable_native_picking()
        self._pick_mode = mode
        self._pick_callback = callback
        interactor = self._require_open_interactor()
        if mode == "node":
            enable = getattr(interactor, "enable_point_picking", None)
            if not callable(enable):
                raise RuntimeError("The interactive backend does not support point picking.")
            enable(
                callback=self._on_native_point_pick,
                left_clicking=True,
                show_message=False,
                show_point=False,
                use_picker=True,
            )
            return
        enable = getattr(interactor, "enable_cell_picking", None)
        if not callable(enable):
            raise RuntimeError("The interactive backend does not support cell picking.")
        enable(
            callback=self._on_native_cell_pick,
            through=False,
            show=False,
            show_message=False,
            start=True,
        )

    def disable_picking(self) -> None:
        self._disable_native_picking()
        self._pick_mode = None
        self._pick_callback = None

    def set_hover_entities(
        self,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self._set_selection_overlay(
            "hover",
            entity_kind,
            indices,
            generation,
            color="#fbbf24",
            opacity=0.75,
        )

    def clear_hover(self) -> None:
        self._remove_native_actor("hover")

    def set_current_selection(
        self,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self._set_selection_overlay(
            "current_selection",
            entity_kind,
            indices,
            generation,
            color="#22d3ee",
            opacity=1.0,
        )

    def clear_current_selection(self) -> None:
        self._remove_native_actor("current_selection")

    def set_named_selection_overlay(
        self,
        selection_id: str,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self._set_selection_overlay(
            f"named_selection:{selection_id}",
            entity_kind,
            indices,
            generation,
            color="#c084fc",
            opacity=0.65,
        )

    def remove_named_selection_overlay(self, selection_id: str) -> None:
        self._remove_native_actor(f"named_selection:{selection_id}")

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        if self._closed:
            raise RuntimeError("PyVistaQt renderer session is closed.")
        if semantic_id.startswith("setup:"):
            if not isinstance(payload, SetupOverlaySpec):
                raise TypeError("Setup overlay actor requires a SetupOverlaySpec.")
            self._payloads[semantic_id] = (payload, generation)
            self._visibility[semantic_id] = payload.visible
            return self._replace_setup_actor(semantic_id, payload)
        if semantic_id == MESH_QUALITY_ACTOR_KEY:
            if not isinstance(payload, MeshQualityOverlaySpec):
                raise TypeError("Mesh quality actor requires a MeshQualityOverlaySpec.")
            self._payloads[semantic_id] = (payload, generation)
            self._visibility[semantic_id] = payload.visible
            return self._replace_mesh_quality_actor(semantic_id, payload)
        if semantic_id == RESULT_SCALAR_ACTOR_KEY:
            if not isinstance(payload, ScalarResultOverlaySpec):
                raise TypeError("Scalar result actor requires a scalar overlay spec.")
            self._payloads[semantic_id] = (payload, generation)
            self._visibility[semantic_id] = True
            return self._replace_scalar_result_actor(semantic_id, payload)
        if semantic_id == RESULT_VECTOR_ACTOR_KEY:
            if not isinstance(payload, ResultVectorGlyphSpec):
                raise TypeError("Vector result actor requires a vector glyph spec.")
            self._payloads[semantic_id] = (payload, generation)
            self._visibility[semantic_id] = True
            return self._replace_vector_result_actor(semantic_id, payload)
        if semantic_id == RESULT_PROBE_ACTOR_KEY:
            if not isinstance(payload, ResultProbeOverlaySpec):
                raise TypeError("Probe result actor requires a probe overlay spec.")
            self._payloads[semantic_id] = (payload, generation)
            self._visibility[semantic_id] = True
            return self._replace_probe_result_actor(semantic_id, payload)
        if semantic_id == RESULT_COLORBAR_ACTOR_KEY:
            if not isinstance(payload, ResultColorbarSpec):
                raise TypeError("Result colorbar requires an applied colorbar spec.")
            self._payloads[semantic_id] = (payload, generation)
            self._visibility[semantic_id] = payload.visible
            return self._replace_result_colorbar(semantic_id, payload)
        if semantic_id not in {"base_mesh", "wireframe"}:
            raise ValueError(f"Unsupported semantic actor: {semantic_id}")
        if not hasattr(payload, "mesh") or not hasattr(payload, "scene_state"):
            raise TypeError("Interactive scene actor requires a scene mesh payload.")
        self._payloads[semantic_id] = (payload, generation)
        self._replace_native_actor(semantic_id)
        mesh = payload.mesh
        scene_state = payload.scene_state
        config = PyVistaSceneConfig(**scene_state.render_options.to_pyvista_config_dict())
        return build_scene_state(mesh, config=config, rendered=True)

    def remove_actor(self, semantic_id: str) -> None:
        self._payloads.pop(semantic_id, None)
        self._remove_native_actor(semantic_id)
        if semantic_id not in {"base_mesh", "wireframe"}:
            self._visibility.pop(semantic_id, None)

    def request_render(self) -> None:
        if self._closed or self._interactor is None:
            return
        render = getattr(self._interactor, "render", None)
        if callable(render):
            render()

    def fit_to_scene(self) -> None:
        self._require_open_interactor().reset_camera()
        self.request_render()

    def set_camera_preset(self, preset: str) -> None:
        try:
            vector, view_up = _CAMERA_VECTORS[preset]
        except KeyError as exc:
            raise ValueError(f"Unsupported camera preset: {preset}") from exc
        interactor = self._require_open_interactor()
        interactor.view_vector(vector, view_up)
        interactor.reset_camera()
        self.request_render()

    def set_interaction_mode(self, mode: str) -> None:
        if mode not in {"orbit", "pan", "zoom"}:
            raise ValueError(f"Unsupported interaction mode: {mode}")
        interactor = self._require_open_interactor()
        enable_trackball = getattr(interactor, "enable_trackball_style", None)
        if callable(enable_trackball):
            enable_trackball()

    def set_axes_visible(self, visible: bool) -> None:
        interactor = self._require_open_interactor()
        method_name = "show_axes" if visible else "hide_axes"
        method = getattr(interactor, method_name, None)
        if callable(method):
            method()
        self._axes_visible = bool(visible)
        self.request_render()

    def set_representation(self, mode: str) -> None:
        try:
            visibility = _REPRESENTATION_VISIBILITY[mode]
        except KeyError as exc:
            raise ValueError(f"Unsupported representation: {mode}") from exc
        self._representation = mode
        self._visibility.update(visibility)
        self._apply_actor_visibility()
        self.request_render()

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        if semantic_id not in self._visibility:
            raise ValueError(f"Unsupported semantic actor: {semantic_id}")
        self._visibility[semantic_id] = bool(visible)
        self._apply_actor_visibility()
        self.request_render()

    def isolate_actor(self, semantic_id: str) -> None:
        if semantic_id not in self._visibility:
            raise ValueError(f"Unsupported semantic actor: {semantic_id}")
        for actor_id in self._visibility:
            self._visibility[actor_id] = actor_id == semantic_id
        self._apply_actor_visibility()
        self.request_render()

    def show_all_actors(self) -> None:
        for semantic_id in self._visibility:
            self._visibility[semantic_id] = True
        self._representation = "surface_with_edges"
        self._apply_actor_visibility()
        self.request_render()

    def enable_clipping(self, axis: str, origin: float) -> None:
        self._set_clipping(axis, origin)

    def update_clipping(self, axis: str, origin: float) -> None:
        self._set_clipping(axis, origin)

    def clear_clipping(self) -> None:
        if self._closed:
            return
        self._clip_axis = None
        self._clip_origin = 0.0
        self._rebuild_actors()

    def set_view_state(self, scene_state: SceneViewState) -> None:
        options = scene_state.render_options
        if not options.show_surface and options.show_edges:
            representation = "wireframe"
        elif options.show_edges:
            representation = "surface_with_edges"
        else:
            representation = "surface"
        self.set_representation(representation)
        self.set_axes_visible(options.show_axes)

    def get_camera_state(self) -> ActiveSceneCameraState:
        """Return pure camera values without exposing the native camera object."""

        interactor = self._require_open_interactor()
        camera_position = getattr(interactor, "camera_position", None)
        position = focal_point = view_up = None
        if camera_position is not None:
            try:
                position, focal_point, view_up = camera_position
            except (TypeError, ValueError):
                position = focal_point = view_up = None
        camera = getattr(interactor, "camera", None)
        return ActiveSceneCameraState(
            position=position,
            focal_point=focal_point,
            view_up=view_up,
            parallel_projection=bool(getattr(camera, "parallel_projection", False)),
            parallel_scale=getattr(camera, "parallel_scale", None),
        )

    def apply_camera_state(self, camera: ActiveSceneCameraState) -> None:
        """Apply validated pure camera values to the current native session."""

        interactor = self._require_open_interactor()
        if (
            camera.position is not None
            and camera.focal_point is not None
            and camera.view_up is not None
        ):
            interactor.camera_position = [
                camera.position,
                camera.focal_point,
                camera.view_up,
            ]
        native_camera = getattr(interactor, "camera", None)
        if native_camera is not None:
            if camera.parallel_scale is not None:
                native_camera.parallel_scale = camera.parallel_scale
            if camera.parallel_projection:
                enable = getattr(native_camera, "enable_parallel_projection", None)
                if callable(enable):
                    enable()
            else:
                disable = getattr(native_camera, "disable_parallel_projection", None)
                if callable(disable):
                    disable()

    def export_screenshot_record(
        self,
        path: str,
        *,
        record_id: str,
        scene_state: SceneViewState,
        mesh: object,
        mesh_ref: str | None = None,
        selection_ids: Sequence[str] = (),
        caption: str | None = None,
        created_by: str | None = None,
    ) -> SceneScreenshotRecord:
        del mesh
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        interactor = self._require_open_interactor()
        screenshot = getattr(interactor, "screenshot", None)
        if not callable(screenshot):
            raise RuntimeError("The active PyVistaQt session does not support screenshot capture.")
        screenshot(str(target))
        return build_screenshot_record(
            str(target),
            record_id=record_id,
            scene_state=scene_state,
            caption=caption,
            mesh_ref=mesh_ref,
            selection_ids=selection_ids,
            created_by=created_by,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        interactor = self._interactor
        if interactor is None:
            self._actors.clear()
            self._payloads.clear()
            return

        self._disable_native_picking()
        self._pick_mode = None
        self._pick_callback = None
        for semantic_id in tuple(self._actors):
            self._remove_native_actor(semantic_id)
        self._payloads.clear()
        self._clip_axis = None

        render_timer = getattr(interactor, "render_timer", None)
        stop = getattr(render_timer, "stop", None)
        if callable(stop):
            with suppress(Exception):
                stop()
        hide_axes = getattr(interactor, "hide_axes", None)
        if callable(hide_axes):
            with suppress(Exception):
                hide_axes()
        clear_plane_widgets = getattr(interactor, "clear_plane_widgets", None)
        if callable(clear_plane_widgets):
            with suppress(Exception):
                clear_plane_widgets()
        close = getattr(interactor, "close", None)
        if callable(close):
            with suppress(Exception):
                close()
        set_parent = getattr(interactor, "setParent", None)
        if callable(set_parent):
            with suppress(Exception):
                set_parent(None)
        delete_later = getattr(interactor, "deleteLater", None)
        if callable(delete_later):
            with suppress(Exception):
                delete_later()
        self._interactor = None
        self._pyvista = None

    def _set_clipping(self, axis: str, origin: float) -> None:
        if axis not in _CLIP_NORMALS:
            raise ValueError(f"Unsupported clipping axis: {axis}")
        self._clip_axis = axis
        self._clip_origin = float(origin)
        self._rebuild_actors()

    def _rebuild_actors(self) -> None:
        if self._closed:
            return
        for semantic_id in tuple(self._payloads):
            self._replace_native_actor(semantic_id)
        self.request_render()

    def _replace_native_actor(self, semantic_id: str) -> None:
        payload, _generation = self._payloads[semantic_id]
        if isinstance(payload, SetupOverlaySpec):
            self._replace_setup_actor(semantic_id, payload)
            return
        if isinstance(payload, MeshQualityOverlaySpec):
            self._replace_mesh_quality_actor(semantic_id, payload)
            return
        if isinstance(payload, ScalarResultOverlaySpec):
            self._replace_scalar_result_actor(semantic_id, payload)
            return
        if isinstance(payload, ResultVectorGlyphSpec):
            self._replace_vector_result_actor(semantic_id, payload)
            return
        if isinstance(payload, ResultProbeOverlaySpec):
            self._replace_probe_result_actor(semantic_id, payload)
            return
        if isinstance(payload, ResultColorbarSpec):
            self._replace_result_colorbar(semantic_id, payload)
            return
        self._remove_native_actor(semantic_id)
        mesh = payload.mesh
        scene_state = payload.scene_state
        dataset = mesh_data_to_pyvista_dataset(mesh, pyvista_module=self._pyvista)
        self._attach_scalar_field(dataset, mesh, scene_state)
        self._attach_transient_pick_indices(dataset, mesh)
        if self._clip_axis is not None:
            clip = getattr(dataset, "clip", None)
            if callable(clip):
                origin = [0.0, 0.0, 0.0]
                origin["xyz".index(self._clip_axis)] = self._clip_origin
                dataset = clip(
                    normal=_CLIP_NORMALS[self._clip_axis],
                    origin=tuple(origin),
                )
        style = "surface" if semantic_id == "base_mesh" else "wireframe"
        actor = self._require_open_interactor().add_mesh(
            dataset,
            name=f"osw-{semantic_id}",
            style=style,
            show_edges=False,
            reset_camera=False,
            render=False,
        )
        self._actors[semantic_id] = actor
        _set_native_visibility(actor, self._visibility[semantic_id])

    def _replace_setup_actor(
        self,
        semantic_id: str,
        payload: SetupOverlaySpec,
    ) -> object:
        self._remove_native_actor(semantic_id)
        interactor = self._require_open_interactor()
        if payload.category == "material":
            base_payload = self._payloads.get("base_mesh")
            if base_payload is None:
                raise RuntimeError("Material overlays require an active mesh.")
            mesh_payload = base_payload[0]
            dataset = mesh_data_to_pyvista_dataset(
                mesh_payload.mesh,
                pyvista_module=self._pyvista,
            )
            extractor = getattr(dataset, "extract_cells", None)
            if not callable(extractor):
                raise RuntimeError("The backend cannot extract material cells.")
            subset = extractor(list(payload.entity_indices))
            actor = interactor.add_mesh(
                subset,
                name=f"osw-{semantic_id}",
                color="#60a5fa",
                opacity=0.35,
                show_edges=True,
                reset_camera=False,
                render=False,
            )
        elif payload.category == "force":
            dataset = self._force_dataset(payload)
            actor = interactor.add_mesh(
                dataset,
                name=f"osw-{semantic_id}",
                color="#ef4444",
                reset_camera=False,
                render=False,
            )
        else:
            dataset = self._pyvista.PolyData(list(payload.points))
            actor = interactor.add_mesh(
                dataset,
                name=f"osw-{semantic_id}",
                color="#22c55e",
                point_size=14,
                render_points_as_spheres=True,
                reset_camera=False,
                render=False,
            )
        self._actors[semantic_id] = actor
        _set_native_visibility(actor, self._visibility[semantic_id])
        return actor

    def _replace_mesh_quality_actor(
        self,
        semantic_id: str,
        payload: MeshQualityOverlaySpec,
    ) -> object:
        self._remove_native_actor(semantic_id)
        base_payload_entry = self._payloads.get("base_mesh")
        if base_payload_entry is None:
            raise RuntimeError("Mesh quality overlay requires an active mesh.")
        mesh_payload = base_payload_entry[0]
        active_fingerprint = getattr(
            getattr(mesh_payload, "mesh_fingerprint", None),
            "digest",
            "",
        )
        if active_fingerprint != payload.mesh_fingerprint:
            raise RuntimeError("Mesh quality overlay fingerprint does not match the active mesh.")
        dataset = mesh_data_to_pyvista_dataset(
            mesh_payload.mesh,
            pyvista_module=self._pyvista,
        )
        extractor = getattr(dataset, "extract_cells", None)
        if not callable(extractor):
            raise RuntimeError("The interactive backend cannot extract bad mesh cells.")
        subset = extractor(list(payload.entity_indices))
        actor = self._require_open_interactor().add_mesh(
            subset,
            name=f"osw-{semantic_id}",
            color="#f59e0b",
            opacity=0.75,
            show_edges=True,
            reset_camera=False,
            render=False,
        )
        self._actors[semantic_id] = actor
        _set_native_visibility(actor, self._visibility[semantic_id])
        return actor

    def _replace_scalar_result_actor(
        self,
        semantic_id: str,
        payload: ScalarResultOverlaySpec,
    ) -> object:
        self._remove_native_actor(semantic_id)
        base_payload_entry = self._payloads.get("base_mesh")
        if base_payload_entry is None:
            raise RuntimeError("Scalar result overlay requires an active mesh.")
        mesh_payload = base_payload_entry[0]
        active_fingerprint = getattr(
            getattr(mesh_payload, "mesh_fingerprint", None),
            "digest",
            "",
        )
        if active_fingerprint != payload.mesh_fingerprint:
            raise RuntimeError("Scalar result overlay fingerprint does not match the active mesh.")
        dataset = mesh_data_to_pyvista_dataset(
            mesh_payload.mesh,
            pyvista_module=self._pyvista,
        )
        if payload.association == "point":
            dataset.point_data[payload.field_name] = payload.values
        elif payload.association == "cell":
            dataset.cell_data[payload.field_name] = payload.values
        else:
            raise RuntimeError("Scalar result association must be point or cell.")
        actor = self._require_open_interactor().add_mesh(
            dataset,
            name=f"osw-{semantic_id}",
            scalars=payload.field_name,
            clim=payload.display_range,
            cmap=payload.colormap,
            show_scalar_bar=False,
            reset_camera=False,
            render=False,
        )
        self._actors[semantic_id] = actor
        _set_native_visibility(actor, self._visibility[semantic_id])
        return actor

    def _replace_vector_result_actor(
        self,
        semantic_id: str,
        payload: ResultVectorGlyphSpec,
    ) -> object:
        self._remove_native_actor(semantic_id)
        dataset = self._pyvista.PolyData(list(payload.positions))
        dataset.point_data["osw_result_vector"] = payload.vectors
        glyph = getattr(dataset, "glyph", None)
        rendered = (
            glyph(
                orient="osw_result_vector",
                scale=False,
                factor=payload.scale,
            )
            if callable(glyph)
            else dataset
        )
        actor = self._require_open_interactor().add_mesh(
            rendered,
            name=f"osw-{semantic_id}",
            color="#38bdf8",
            reset_camera=False,
            render=False,
        )
        self._actors[semantic_id] = actor
        _set_native_visibility(actor, self._visibility[semantic_id])
        return actor

    def _replace_probe_result_actor(
        self,
        semantic_id: str,
        payload: ResultProbeOverlaySpec,
    ) -> object:
        self._remove_native_actor(semantic_id)
        base_payload_entry = self._payloads.get("base_mesh")
        if base_payload_entry is None:
            raise RuntimeError("Result probe overlay requires an active mesh.")
        mesh_payload = base_payload_entry[0]
        active_fingerprint = getattr(
            getattr(mesh_payload, "mesh_fingerprint", None),
            "digest",
            "",
        )
        if active_fingerprint != payload.mesh_fingerprint:
            raise RuntimeError("Result probe overlay fingerprint does not match the active mesh.")
        dataset = mesh_data_to_pyvista_dataset(
            mesh_payload.mesh,
            pyvista_module=self._pyvista,
        )
        if payload.association == "point":
            extractor = getattr(dataset, "extract_points", None)
            subset = (
                extractor(
                    [payload.transient_backend_index],
                    adjacent_cells=False,
                    include_cells=False,
                )
                if callable(extractor)
                else self._pyvista.PolyData(
                    [mesh_payload.mesh.points[payload.transient_backend_index]]
                )
            )
        else:
            extractor = getattr(dataset, "extract_cells", None)
            if not callable(extractor):
                raise RuntimeError("Result probe backend cannot extract cells.")
            subset = extractor([payload.transient_backend_index])
        actor = self._require_open_interactor().add_mesh(
            subset,
            name=f"osw-{semantic_id}",
            color="#f43f5e",
            point_size=14,
            render_points_as_spheres=True,
            show_edges=True,
            reset_camera=False,
            render=False,
        )
        self._actors[semantic_id] = actor
        _set_native_visibility(actor, self._visibility[semantic_id])
        return actor

    def _replace_result_colorbar(
        self,
        semantic_id: str,
        payload: ResultColorbarSpec,
    ) -> object:
        self._remove_native_actor(semantic_id)
        scalar_actor = self._actors.get(RESULT_SCALAR_ACTOR_KEY)
        mapper = getattr(scalar_actor, "mapper", None)
        add_scalar_bar = getattr(
            self._require_open_interactor(),
            "add_scalar_bar",
            None,
        )
        if not callable(add_scalar_bar):
            raise RuntimeError("Result colorbar is unavailable in this backend.")
        actor = add_scalar_bar(
            title=payload.title,
            mapper=mapper,
            render=False,
        )
        self._actors[semantic_id] = actor
        _set_native_visibility(actor, self._visibility[semantic_id])
        return actor

    def _force_dataset(self, payload: SetupOverlaySpec) -> object:
        arrow = getattr(self._pyvista, "Arrow", None)
        if not callable(arrow) or payload.direction is None:
            return self._pyvista.PolyData(list(payload.points))
        arrows = [
            arrow(start=point, direction=payload.direction, scale=0.1) for point in payload.points
        ]
        if not arrows:
            return self._pyvista.PolyData([])
        merged = arrows[0]
        merge = getattr(merged, "merge", None)
        if callable(merge) and len(arrows) > 1:
            merged = merge(arrows[1:])
        return merged

    def _set_selection_overlay(
        self,
        semantic_id: str,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
        *,
        color: str,
        opacity: float,
    ) -> None:
        if entity_kind not in {"node", "cell"}:
            raise ValueError(f"Unsupported selection overlay kind: {entity_kind}")
        payload_entry = self._payloads.get("base_mesh")
        if payload_entry is None:
            raise RuntimeError("Selection overlay requires an active base mesh.")
        payload, active_generation = payload_entry
        if generation != active_generation:
            return
        self._remove_native_actor(semantic_id)
        if not indices:
            return
        mesh = payload.mesh
        dataset = mesh_data_to_pyvista_dataset(mesh, pyvista_module=self._pyvista)
        self._attach_transient_pick_indices(dataset, mesh)
        if entity_kind == "node":
            extractor = getattr(dataset, "extract_points", None)
            if callable(extractor):
                subset = extractor(
                    list(indices),
                    adjacent_cells=False,
                    include_cells=False,
                )
            else:
                subset = self._pyvista.PolyData([mesh.points[index] for index in indices])
            actor = self._require_open_interactor().add_mesh(
                subset,
                name=f"osw-{semantic_id}",
                color=color,
                point_size=12,
                render_points_as_spheres=True,
                reset_camera=False,
                render=False,
            )
        else:
            extractor = getattr(dataset, "extract_cells", None)
            if not callable(extractor):
                raise RuntimeError("The interactive backend cannot extract selected cells.")
            subset = extractor(list(indices))
            actor = self._require_open_interactor().add_mesh(
                subset,
                name=f"osw-{semantic_id}",
                color=color,
                opacity=opacity,
                show_edges=True,
                reset_camera=False,
                render=False,
            )
        self._actors[semantic_id] = actor
        self.request_render()

    def _remove_native_actor(self, semantic_id: str) -> None:
        actor = self._actors.pop(semantic_id, None)
        if actor is None or self._interactor is None:
            return
        if semantic_id == RESULT_COLORBAR_ACTOR_KEY:
            remove_scalar_bar = getattr(self._interactor, "remove_scalar_bar", None)
            get_title = getattr(actor, "GetTitle", None)
            title = str(get_title()) if callable(get_title) else ""
            if callable(remove_scalar_bar) and title:
                try:
                    remove_scalar_bar(title, render=False)
                except (KeyError, ValueError):
                    pass
                else:
                    return
        remove_actor = getattr(self._interactor, "remove_actor", None)
        if callable(remove_actor):
            with suppress(Exception):
                remove_actor(actor, render=False)

    def _apply_actor_visibility(self) -> None:
        for semantic_id, actor in self._actors.items():
            _set_native_visibility(
                actor,
                self._visibility.get(semantic_id, True),
            )

    @staticmethod
    def _attach_transient_pick_indices(dataset: object, mesh: object) -> None:
        point_data = getattr(dataset, "point_data", None)
        if point_data is not None:
            point_data["_osw_transient_point_index"] = tuple(
                range(len(getattr(mesh, "points", ())))
            )
        cell_data = getattr(dataset, "cell_data", None)
        if cell_data is not None:
            cell_count = sum(
                int(getattr(block, "count", 0)) for block in getattr(mesh, "cells", ())
            )
            cell_data["_osw_transient_cell_index"] = tuple(range(cell_count))

    def _on_native_point_pick(
        self,
        _picked_point: object,
        picker: object,
    ) -> None:
        point_index = _native_point_index(picker)
        if point_index is not None:
            self._emit_pick(point_index)

    def _on_native_cell_pick(self, picked: object) -> None:
        cell_index = _native_cell_index(picked)
        if cell_index is not None:
            self._emit_pick(cell_index)

    def _emit_pick(self, backend_index: int) -> None:
        callback = self._pick_callback
        mode = self._pick_mode
        payload_entry = self._payloads.get("base_mesh")
        if callback is None or mode is None or payload_entry is None:
            return
        payload, generation = payload_entry
        callback(
            {
                "generation": generation,
                "mesh_ref": str(payload.scene_input.mesh_ref or ""),
                "mesh_fingerprint": payload.mesh_fingerprint.digest,
                "entity_kind": mode,
                "backend_index": int(backend_index),
                "intent": "replace",
            }
        )

    def _disable_native_picking(self) -> None:
        interactor = self._interactor
        if interactor is None:
            return
        for method_name in (
            "disable_picking",
            "disable_point_picking",
            "disable_cell_picking",
        ):
            method = getattr(interactor, method_name, None)
            if callable(method):
                with suppress(Exception):
                    method()

    @staticmethod
    def _attach_scalar_field(
        dataset: object,
        mesh: object,
        scene_state: SceneViewState,
    ) -> None:
        scalar_field = scene_state.render_options.color_by
        if not scalar_field:
            return
        values = getattr(mesh, "point_data", {}).get(scalar_field)
        point_data = getattr(dataset, "point_data", None)
        if values is not None and point_data is not None:
            point_data[scalar_field] = values

    def _require_open_interactor(self) -> Any:
        if self._closed or self._interactor is None:
            raise RuntimeError("PyVistaQt renderer session is closed.")
        return self._interactor


class PyVistaQtRendererFactory:
    """Lazily import PyVistaQt and create one hosted renderer session."""

    backend_kind = PyVistaQtRendererSession.backend_kind
    capabilities = PyVistaQtRendererSession.capabilities

    def __init__(
        self,
        *,
        module_loader: Callable[[str], Any] | None = None,
    ) -> None:
        self._module_loader = module_loader or import_module
        self._host_parent: object | None = None

    def set_host_parent(self, parent: object) -> None:
        self._host_parent = parent

    def create_session(self) -> PyVistaQtRendererSession:
        if self._host_parent is None:
            raise SceneRendererInitializationError("The central 3D renderer host is not attached.")
        try:
            pyvista_module = self._module_loader("pyvista")
        except (ImportError, ModuleNotFoundError) as exc:
            raise SceneRendererInitializationError(
                "PyVista is not installed. Install the optional visualization "
                "extra before enabling the interactive 3D workspace."
            ) from exc
        try:
            pyvistaqt_module = self._module_loader("pyvistaqt")
        except (ImportError, ModuleNotFoundError) as exc:
            raise SceneRendererInitializationError(pyvistaqt_missing_message()) from exc
        interactor_factory = getattr(pyvistaqt_module, "QtInteractor", None)
        if not callable(interactor_factory):
            raise SceneRendererInitializationError(
                "PyVistaQt does not expose the required QtInteractor host."
            )
        return PyVistaQtRendererSession(
            self._host_parent,
            pyvista_module=pyvista_module,
            interactor_factory=interactor_factory,
        )


def _set_native_visibility(actor: object, visible: bool) -> None:
    setter = getattr(actor, "SetVisibility", None)
    if callable(setter):
        setter(bool(visible))
        return
    if hasattr(actor, "visibility"):
        actor.visibility = bool(visible)


def _native_point_index(picked: object) -> int | None:
    if isinstance(picked, int):
        return picked if picked >= 0 else None
    getter = getattr(picked, "GetPointId", None)
    if callable(getter):
        value = int(getter())
        return value if value >= 0 else None
    value = getattr(picked, "point_id", None)
    if value is None:
        return None
    normalized = int(value)
    return normalized if normalized >= 0 else None


def _native_cell_index(picked: object) -> int | None:
    if isinstance(picked, int):
        return picked if picked >= 0 else None
    cell_data = getattr(picked, "cell_data", None)
    if cell_data is not None:
        values = cell_data.get("_osw_transient_cell_index")
        if values is not None and len(values):
            value = int(values[0])
            return value if value >= 0 else None
    getter = getattr(picked, "GetCellId", None)
    if callable(getter):
        value = int(getter())
        return value if value >= 0 else None
    return None


__all__ = [
    "PyVistaQtRendererFactory",
    "PyVistaQtRendererSession",
    "pyvistaqt_missing_message",
]
