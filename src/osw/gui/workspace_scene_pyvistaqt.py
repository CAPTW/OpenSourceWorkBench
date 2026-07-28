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

from osw.gui.workspace_scene_controller import (
    SceneRendererInitializationError,
)
from osw.post.pyvista_scene import (
    PyVistaSceneConfig,
    build_scene_state,
    mesh_data_to_polydata,
)
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
        for semantic_id in tuple(self._actors):
            self._remove_native_actor(semantic_id)
        self._payloads.clear()
        self._clip_axis = None
        self._clip_origin = 0.0

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        if self._closed:
            raise RuntimeError("PyVistaQt renderer session is closed.")
        if semantic_id not in {"base_mesh", "wireframe"}:
            raise ValueError(f"Unsupported semantic actor: {semantic_id}")
        if not hasattr(payload, "mesh") or not hasattr(payload, "scene_state"):
            raise TypeError("Interactive scene actor requires a scene mesh payload.")
        self._payloads[semantic_id] = (payload, generation)
        self._replace_native_actor(semantic_id)
        mesh = payload.mesh
        scene_state = payload.scene_state
        config = PyVistaSceneConfig(
            **scene_state.render_options.to_pyvista_config_dict()
        )
        return build_scene_state(mesh, config=config, rendered=True)

    def remove_actor(self, semantic_id: str) -> None:
        self._payloads.pop(semantic_id, None)
        self._remove_native_actor(semantic_id)

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
        if semantic_id not in {"base_mesh", "wireframe"}:
            raise ValueError(f"Unsupported semantic actor: {semantic_id}")
        self._visibility[semantic_id] = bool(visible)
        self._apply_actor_visibility()
        self.request_render()

    def isolate_actor(self, semantic_id: str) -> None:
        if semantic_id not in {"base_mesh", "wireframe"}:
            raise ValueError(f"Unsupported semantic actor: {semantic_id}")
        for actor_id in self._visibility:
            self._visibility[actor_id] = actor_id == semantic_id
        self._apply_actor_visibility()
        self.request_render()

    def show_all_actors(self) -> None:
        self._visibility = {
            "base_mesh": True,
            "wireframe": True,
        }
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
            raise RuntimeError(
                "The active PyVistaQt session does not support screenshot capture."
            )
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
        self._remove_native_actor(semantic_id)
        mesh = payload.mesh
        scene_state = payload.scene_state
        dataset = mesh_data_to_polydata(mesh, pyvista_module=self._pyvista)
        self._attach_scalar_field(dataset, mesh, scene_state)
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

    def _remove_native_actor(self, semantic_id: str) -> None:
        actor = self._actors.pop(semantic_id, None)
        if actor is None or self._interactor is None:
            return
        remove_actor = getattr(self._interactor, "remove_actor", None)
        if callable(remove_actor):
            with suppress(Exception):
                remove_actor(actor, render=False)

    def _apply_actor_visibility(self) -> None:
        for semantic_id, actor in self._actors.items():
            _set_native_visibility(actor, self._visibility[semantic_id])

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
            raise SceneRendererInitializationError(
                "The central 3D renderer host is not attached."
            )
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
            raise SceneRendererInitializationError(
                pyvistaqt_missing_message()
            ) from exc
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


__all__ = [
    "PyVistaQtRendererFactory",
    "PyVistaQtRendererSession",
    "pyvistaqt_missing_message",
]
