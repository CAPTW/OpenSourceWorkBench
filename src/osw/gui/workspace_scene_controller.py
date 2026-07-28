"""Deterministic active-scene ownership for one MainWindow document.

The controller is Qt-free and does not import PyVista.  It owns at most one
renderer session, keeps only semantic actor records outside that session, and
invalidates generation-guarded callbacks whenever scene resources are replaced
or torn down.  The current mesh-viewer ``SceneAdapterProtocol`` remains a
compatibility seam inside ``SceneAdapterRendererSession``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from osw.gui.workspace_scene_view_model import (
    DefaultSceneAdapter,
    SceneAdapterProtocol,
)
from osw.mesh.mesh_model import MeshData
from osw.post.pyvista_scene import (
    PyVistaSceneConfig,
    PyVistaUnavailableError,
    build_scene_state,
)
from osw.post.scene_model import (
    SceneInputRef,
    SceneScreenshotRecord,
    SceneViewState,
)


class SceneLifecycleState(str, Enum):
    """Lifecycle states for the one active scene owned by a document."""

    DETACHED = "detached"
    INITIALIZING = "initializing"
    READY_EMPTY = "ready_empty"
    READY_SCENE = "ready_scene"
    REPLACING = "replacing"
    FALLBACK = "fallback"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass(frozen=True)
class SceneActorRecord:
    """Renderer-neutral semantic actor record; never stores a native handle."""

    semantic_id: str
    generation: int
    visible: bool = True


@dataclass(frozen=True)
class SceneMeshPayload:
    """Logical mesh payload passed into a renderer session."""

    mesh: MeshData
    scene_input: SceneInputRef
    scene_state: SceneViewState


@runtime_checkable
class SceneRendererSessionProtocol(Protocol):
    """One renderer backend session whose native objects stay session-local."""

    backend_kind: str
    capabilities: frozenset[str]

    @property
    def hosted_widget(self) -> object | None:
        ...

    def clear(self) -> None:
        ...

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object | None:
        ...

    def remove_actor(self, semantic_id: str) -> None:
        ...

    def request_render(self) -> None:
        ...

    def fit_to_scene(self) -> None:
        ...

    def set_camera_preset(self, preset: str) -> None:
        ...

    def set_interaction_mode(self, mode: str) -> None:
        ...

    def set_axes_visible(self, visible: bool) -> None:
        ...

    def set_representation(self, mode: str) -> None:
        ...

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        ...

    def isolate_actor(self, semantic_id: str) -> None:
        ...

    def show_all_actors(self) -> None:
        ...

    def enable_clipping(self, axis: str, origin: float) -> None:
        ...

    def update_clipping(self, axis: str, origin: float) -> None:
        ...

    def clear_clipping(self) -> None:
        ...

    def close(self) -> None:
        ...


@runtime_checkable
class SceneRendererFactoryProtocol(Protocol):
    """Factory for one explicit renderer-session backend."""

    backend_kind: str
    capabilities: frozenset[str]

    def create_session(self) -> SceneRendererSessionProtocol:
        ...


class SceneRendererInitializationError(RuntimeError):
    """Renderer initialization failed, optionally after creating a session."""

    def __init__(
        self,
        message: str,
        *,
        partial_session: SceneRendererSessionProtocol | None = None,
    ) -> None:
        super().__init__(message)
        self.partial_session = partial_session


class SceneAdapterRendererSession:
    """Session wrapper that contains the existing scene-adapter compatibility seam."""

    backend_kind = "scene-adapter"
    capabilities = frozenset(
        {
            "mesh-preview",
            "scene-screenshot",
            "semantic-actors",
        }
    )

    def __init__(self, adapter: SceneAdapterProtocol) -> None:
        self._adapter = adapter
        self._closed = False
        self._last_result: object | None = None

    def clear(self) -> None:
        if self._closed:
            return
        clear = getattr(self._adapter, "clear", None)
        if callable(clear):
            clear()
        self._last_result = None

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object | None:
        del generation
        if self._closed:
            raise RuntimeError("Scene renderer session is closed.")
        if not isinstance(payload, SceneMeshPayload):
            raise TypeError("Scene adapter session requires a SceneMeshPayload.")
        if semantic_id == "base_mesh":
            self._last_result = self._adapter.load_mesh(
                payload.mesh,
                payload.scene_input,
                payload.scene_state,
            )
        return self._last_result

    def remove_actor(self, semantic_id: str) -> None:
        if semantic_id == "base_mesh":
            self.clear()

    def request_render(self) -> None:
        if self._closed:
            return
        request_render = getattr(self._adapter, "request_render", None)
        if callable(request_render):
            request_render()

    def set_view_state(self, scene_state: SceneViewState) -> None:
        if not self._closed:
            self._adapter.set_view_state(scene_state)

    def export_screenshot_record(
        self,
        path: str,
        *,
        record_id: str,
        scene_state: SceneViewState,
        mesh: MeshData,
        mesh_ref: str | None = None,
        selection_ids: Sequence[str] = (),
        caption: str | None = None,
        created_by: str | None = None,
    ) -> SceneScreenshotRecord:
        if self._closed:
            raise RuntimeError("Scene renderer session is closed.")
        return self._adapter.export_screenshot_record(
            path,
            record_id=record_id,
            scene_state=scene_state,
            mesh=mesh,
            mesh_ref=mesh_ref,
            selection_ids=selection_ids,
            caption=caption,
            created_by=created_by,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        close = getattr(self._adapter, "close", None)
        try:
            if callable(close):
                close()
        finally:
            self._last_result = None


class SceneAdapterRendererFactory:
    """Create a session around one lazily constructed compatibility adapter."""

    backend_kind = SceneAdapterRendererSession.backend_kind
    capabilities = SceneAdapterRendererSession.capabilities

    def __init__(
        self,
        adapter_factory: Callable[[], SceneAdapterProtocol] | None = None,
    ) -> None:
        self._adapter_factory = adapter_factory or DefaultSceneAdapter

    def create_session(self) -> SceneAdapterRendererSession:
        return SceneAdapterRendererSession(self._adapter_factory())


class ActiveSceneController:
    """Own one renderer session and deterministic scene replacement/teardown."""

    def __init__(self, factory: SceneRendererFactoryProtocol) -> None:
        self._factory = factory
        self._session: SceneRendererSessionProtocol | None = None
        self._actor_records: dict[str, SceneActorRecord] = {}
        self._state = SceneLifecycleState.DETACHED
        self._generation = 0
        self._fallback_reason = ""

    @property
    def state(self) -> SceneLifecycleState:
        return self._state

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def session(self) -> SceneRendererSessionProtocol | None:
        return self._session

    @property
    def actor_records(self) -> Mapping[str, SceneActorRecord]:
        return MappingProxyType(dict(self._actor_records))

    @property
    def backend_kind(self) -> str:
        if self._session is not None:
            return str(self._session.backend_kind)
        return str(self._factory.backend_kind)

    @property
    def capabilities(self) -> frozenset[str]:
        if self._session is not None:
            return frozenset(self._session.capabilities)
        return frozenset(self._factory.capabilities)

    @property
    def fallback_reason(self) -> str:
        return self._fallback_reason

    def attach_host(self, parent: object) -> object | None:
        """Attach the factory to one Qt host and return its session widget."""

        if self._state in {
            SceneLifecycleState.CLOSING,
            SceneLifecycleState.CLOSED,
        }:
            return None
        setter = getattr(self._factory, "set_host_parent", None)
        if callable(setter):
            try:
                setter(parent)
            except Exception as exc:
                self._fallback_reason = str(exc)
                self._state = SceneLifecycleState.FALLBACK
                return None
        session = self._ensure_session()
        if session is None:
            return None
        return getattr(session, "hosted_widget", None)

    def load_mesh(
        self,
        mesh: MeshData,
        scene_input: SceneInputRef,
        scene_state: SceneViewState,
    ) -> object:
        """Replace the active logical mesh without retaining native actor handles."""

        if self._state is SceneLifecycleState.CLOSED:
            raise RuntimeError("Active scene controller is closed.")
        self._generation += 1
        generation = self._generation
        session = self._ensure_session()
        if session is None:
            return self._fallback_scene_state(mesh, scene_state)

        replacing = bool(self._actor_records)
        self._state = (
            SceneLifecycleState.REPLACING
            if replacing
            else SceneLifecycleState.READY_EMPTY
        )
        if replacing:
            try:
                session.clear()
            except Exception as exc:
                self._fail_session(exc)
                return self._fallback_scene_state(mesh, scene_state)
            self._actor_records.clear()

        payload = SceneMeshPayload(
            mesh=mesh,
            scene_input=scene_input,
            scene_state=scene_state,
        )
        try:
            result = session.replace_actor(
                "base_mesh",
                payload,
                generation=generation,
            )
            self._actor_records["base_mesh"] = SceneActorRecord(
                semantic_id="base_mesh",
                generation=generation,
            )
            session.replace_actor(
                "wireframe",
                payload,
                generation=generation,
            )
            self._actor_records["wireframe"] = SceneActorRecord(
                semantic_id="wireframe",
                generation=generation,
            )
            representation = _representation_from_scene_state(scene_state)
            setter = getattr(session, "set_representation", None)
            if callable(setter):
                setter(representation)
            self._set_registry_representation(representation)
            session.request_render()
        except Exception as exc:
            self._fail_session(exc)
            return self._fallback_scene_state(mesh, scene_state)

        self._fallback_reason = ""
        self._state = SceneLifecycleState.READY_SCENE
        if result is not None:
            return result
        return self._fallback_scene_state(mesh, scene_state)

    def set_view_state(self, scene_state: SceneViewState) -> None:
        session = self._session
        if session is None or self._state is SceneLifecycleState.CLOSED:
            return
        setter = getattr(session, "set_view_state", None)
        if callable(setter):
            setter(scene_state)

    def set_interaction_mode(self, mode: str) -> bool:
        if mode not in {"orbit", "pan", "zoom"}:
            return False
        return self._call_session("interactive", "set_interaction_mode", mode)

    def fit_to_scene(self) -> bool:
        return self._call_session("camera", "fit_to_scene")

    def set_camera_preset(self, preset: str) -> bool:
        if preset not in {
            "front",
            "back",
            "left",
            "right",
            "top",
            "bottom",
            "isometric",
        }:
            return False
        return self._call_session("camera", "set_camera_preset", preset)

    def set_axes_visible(self, visible: bool) -> bool:
        return self._call_session("axes", "set_axes_visible", bool(visible))

    def set_representation(self, mode: str) -> bool:
        if mode not in _REPRESENTATION_VISIBILITY:
            return False
        if not self._call_session("representation", "set_representation", mode):
            return False
        self._set_registry_representation(mode)
        return True

    def set_actor_visible(self, semantic_id: str, visible: bool) -> bool:
        if semantic_id not in self._actor_records:
            return False
        if not self._call_session(
            "semantic-visibility",
            "set_actor_visible",
            semantic_id,
            bool(visible),
        ):
            return False
        record = self._actor_records[semantic_id]
        self._actor_records[semantic_id] = SceneActorRecord(
            semantic_id=semantic_id,
            generation=record.generation,
            visible=bool(visible),
        )
        return True

    def isolate_actor(self, semantic_id: str) -> bool:
        if semantic_id not in self._actor_records:
            return False
        if not self._call_session(
            "semantic-visibility",
            "isolate_actor",
            semantic_id,
        ):
            return False
        self._set_registry_visibility(
            {key: key == semantic_id for key in self._actor_records}
        )
        return True

    def show_all_actors(self) -> bool:
        if not self._call_session("semantic-visibility", "show_all_actors"):
            return False
        self._set_registry_visibility(
            {key: True for key in self._actor_records}
        )
        return True

    def enable_clipping(self, axis: str, origin: float) -> bool:
        normalized = axis.lower()
        if normalized not in {"x", "y", "z"}:
            return False
        return self._call_session(
            "clipping",
            "enable_clipping",
            normalized,
            float(origin),
        )

    def update_clipping(self, axis: str, origin: float) -> bool:
        normalized = axis.lower()
        if normalized not in {"x", "y", "z"}:
            return False
        return self._call_session(
            "clipping",
            "update_clipping",
            normalized,
            float(origin),
        )

    def clear_clipping(self) -> bool:
        return self._call_session("clipping", "clear_clipping")

    def export_screenshot_record(
        self,
        path: str,
        *,
        record_id: str,
        scene_state: SceneViewState,
        mesh: MeshData,
        mesh_ref: str | None = None,
        selection_ids: Sequence[str] = (),
        caption: str | None = None,
        created_by: str | None = None,
    ) -> SceneScreenshotRecord:
        session = self._ensure_session()
        if session is None:
            raise PyVistaUnavailableError(
                self._fallback_reason or "The scene renderer could not be initialized."
            )
        exporter = getattr(session, "export_screenshot_record", None)
        if not callable(exporter):
            raise PyVistaUnavailableError(
                f"Scene backend '{self.backend_kind}' does not support screenshot export."
            )
        return exporter(
            path,
            record_id=record_id,
            scene_state=scene_state,
            mesh=mesh,
            mesh_ref=mesh_ref,
            selection_ids=selection_ids,
            caption=caption,
            created_by=created_by,
        )

    def guard_callback(
        self,
        callback: Callable[..., object],
        *,
        stale_result: object | None = None,
    ) -> Callable[..., object | None]:
        """Return a callback that becomes inert after a scene generation change."""

        generation = self._generation

        def guarded(*args: object, **kwargs: object) -> object | None:
            if (
                self._generation != generation
                or self._state is SceneLifecycleState.CLOSED
            ):
                return stale_result
            return callback(*args, **kwargs)

        return guarded

    def clear(self) -> None:
        """Remove scene resources and invalidate callbacks without closing the session."""

        if self._state in {
            SceneLifecycleState.CLOSING,
            SceneLifecycleState.CLOSED,
        }:
            return
        self._generation += 1
        session = self._session
        if session is None:
            self._actor_records.clear()
            if self._state is not SceneLifecycleState.FALLBACK:
                self._state = SceneLifecycleState.DETACHED
            return
        self._state = SceneLifecycleState.REPLACING
        try:
            session.clear()
        except Exception as exc:
            self._fail_session(exc)
            return
        self._actor_records.clear()
        self._state = SceneLifecycleState.READY_EMPTY

    def close(self) -> None:
        """Deterministically close the active session; repeated calls are no-ops."""

        if self._state is SceneLifecycleState.CLOSED:
            return
        self._generation += 1
        self._state = SceneLifecycleState.CLOSING
        session = self._session
        self._session = None
        self._actor_records.clear()
        if session is not None:
            try:
                session.clear()
            except Exception as exc:
                self._fallback_reason = str(exc)
            try:
                session.close()
            except Exception as exc:
                self._fallback_reason = str(exc)
        self._state = SceneLifecycleState.CLOSED

    def _ensure_session(self) -> SceneRendererSessionProtocol | None:
        if self._session is not None:
            return self._session
        if self._state in {
            SceneLifecycleState.CLOSING,
            SceneLifecycleState.CLOSED,
        }:
            return None
        self._state = SceneLifecycleState.INITIALIZING
        try:
            session = self._factory.create_session()
        except Exception as exc:
            partial_session = getattr(exc, "partial_session", None)
            if partial_session is not None:
                try:
                    partial_session.close()
                except Exception:
                    pass
            self._fallback_reason = str(exc)
            self._state = SceneLifecycleState.FALLBACK
            return None
        self._session = session
        self._fallback_reason = ""
        self._state = SceneLifecycleState.READY_EMPTY
        return session

    def _fail_session(self, error: Exception) -> None:
        session = self._session
        self._session = None
        self._actor_records.clear()
        if session is not None:
            try:
                session.clear()
            except Exception:
                pass
            try:
                session.close()
            except Exception:
                pass
        self._fallback_reason = str(error)
        self._state = SceneLifecycleState.FALLBACK

    def _call_session(
        self,
        capability: str,
        method_name: str,
        *args: object,
    ) -> bool:
        if (
            self._state in {
                SceneLifecycleState.CLOSING,
                SceneLifecycleState.CLOSED,
                SceneLifecycleState.FALLBACK,
            }
            or capability not in self.capabilities
        ):
            return False
        session = self._session
        if session is None:
            return False
        method = getattr(session, method_name, None)
        if not callable(method):
            return False
        try:
            method(*args)
        except Exception as exc:
            self._fail_session(exc)
            return False
        return True

    def _set_registry_representation(self, mode: str) -> None:
        self._set_registry_visibility(_REPRESENTATION_VISIBILITY[mode])

    def _set_registry_visibility(self, visibility: Mapping[str, bool]) -> None:
        for semantic_id, record in tuple(self._actor_records.items()):
            self._actor_records[semantic_id] = SceneActorRecord(
                semantic_id=semantic_id,
                generation=record.generation,
                visible=bool(visibility.get(semantic_id, record.visible)),
            )

    @staticmethod
    def _fallback_scene_state(
        mesh: MeshData,
        scene_state: SceneViewState,
    ) -> object:
        config = PyVistaSceneConfig(
            **scene_state.render_options.to_pyvista_config_dict()
        )
        return build_scene_state(mesh, config=config, rendered=False)


_REPRESENTATION_VISIBILITY: Mapping[str, Mapping[str, bool]] = {
    "surface": {
        "base_mesh": True,
        "wireframe": False,
    },
    "wireframe": {
        "base_mesh": False,
        "wireframe": True,
    },
    "surface_with_edges": {
        "base_mesh": True,
        "wireframe": True,
    },
}


def _representation_from_scene_state(scene_state: SceneViewState) -> str:
    options = scene_state.render_options
    if not options.show_surface and options.show_edges:
        return "wireframe"
    if options.show_edges:
        return "surface_with_edges"
    return "surface"


__all__ = [
    "ActiveSceneController",
    "SceneActorRecord",
    "SceneAdapterRendererFactory",
    "SceneAdapterRendererSession",
    "SceneLifecycleState",
    "SceneMeshPayload",
    "SceneRendererFactoryProtocol",
    "SceneRendererInitializationError",
    "SceneRendererSessionProtocol",
]
