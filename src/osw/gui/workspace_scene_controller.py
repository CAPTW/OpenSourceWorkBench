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

from osw.core.selection import (
    EntityKind,
    EntityLocator,
    NamedSelection,
    SelectionMode,
    SelectionTargetRef,
)
from osw.core.selection_resolution import (
    CELL_ORDINAL_NAMESPACE,
    NODE_ORDINAL_NAMESPACE,
    ResolutionResult,
    ResolutionState,
    resolve_named_selection,
    resolve_selection_target,
)
from osw.core.solver_setup import SetupRecordStatus, evaluate_solver_setup
from osw.gui.mesh_diagnostics_view_model import (
    MESH_QUALITY_ACTOR_KEY,
    MeshDiagnosticsViewModel,
    build_mesh_diagnostics_view_model,
    build_mesh_quality_overlay_spec,
)
from osw.gui.setup_overlay_view_model import build_setup_overlay_specs
from osw.gui.workspace_scene_view_model import (
    DefaultSceneAdapter,
    SceneAdapterProtocol,
)
from osw.mesh.identity import MeshFingerprint, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshData
from osw.mesh.quality import (
    MESH_QUALITY_METRIC_SCHEMA,
    MESH_QUALITY_TOPOLOGY_RULES,
    MeshQualityAnalysis,
    analyze_mesh_cell_quality,
)
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
    mesh_fingerprint: MeshFingerprint


@dataclass(frozen=True)
class ScenePickEvent:
    """Renderer-neutral transient pick evidence."""

    generation: int
    mesh_ref: str
    mesh_fingerprint: str
    entity_kind: EntityKind
    backend_index: int
    intent: str = "replace"


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

    def set_pick_mode(
        self,
        mode: str,
        callback: Callable[[object], object],
    ) -> None:
        ...

    def disable_picking(self) -> None:
        ...

    def set_hover_entities(
        self,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        ...

    def clear_hover(self) -> None:
        ...

    def set_current_selection(
        self,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        ...

    def clear_current_selection(self) -> None:
        ...

    def set_named_selection_overlay(
        self,
        selection_id: str,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        ...

    def remove_named_selection_overlay(self, selection_id: str) -> None:
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

    def __init__(
        self,
        factory: SceneRendererFactoryProtocol,
        *,
        mesh_quality_analyzer: Callable[..., MeshQualityAnalysis] | None = None,
    ) -> None:
        self._factory = factory
        self._session: SceneRendererSessionProtocol | None = None
        self._actor_records: dict[str, SceneActorRecord] = {}
        self._state = SceneLifecycleState.DETACHED
        self._generation = 0
        self._fallback_reason = ""
        self._mesh: MeshData | None = None
        self._mesh_ref = ""
        self._mesh_fingerprint: MeshFingerprint | None = None
        self._pick_mode = SelectionMode.NONE
        self._hover_target: SelectionTargetRef | None = None
        self._current_selection_target: SelectionTargetRef | None = None
        self._current_selection_resolution = ResolutionResult()
        self._named_selections: tuple[NamedSelection, ...] = ()
        self._named_selection_resolutions: dict[str, ResolutionResult] = {}
        self._named_overlay_ids: set[str] = set()
        self._solver_setup: object | None = None
        self._setup_materials: tuple[object, ...] = ()
        self._setup_statuses: dict[str, SetupRecordStatus] = {}
        self._setup_overlay_ids: set[str] = set()
        self._setup_category_visibility = {
            "material": True,
            "fixed_support": True,
            "force": True,
        }
        self._mesh_quality_analyzer = (
            mesh_quality_analyzer or analyze_mesh_cell_quality
        )
        self._mesh_quality_cache: dict[
            tuple[str, str, str, float],
            MeshQualityAnalysis,
        ] = {}
        self._mesh_quality_analysis: MeshQualityAnalysis | None = None
        self._mesh_quality_threshold = 10.0
        self._mesh_quality_highlight_visible = False
        self._mesh_quality_visibility_snapshot: dict[str, bool] | None = None
        self._selection_listener: Callable[[], object] | None = None

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

    @property
    def current_mesh_fingerprint(self) -> MeshFingerprint | None:
        return self._mesh_fingerprint

    @property
    def current_mesh_ref(self) -> str:
        return self._mesh_ref

    @property
    def pick_mode(self) -> SelectionMode:
        return self._pick_mode

    @property
    def hover_target(self) -> SelectionTargetRef | None:
        return self._hover_target

    @property
    def current_selection_target(self) -> SelectionTargetRef | None:
        return self._current_selection_target

    @property
    def current_selection_resolution(self) -> ResolutionResult:
        return self._current_selection_resolution

    @property
    def named_selection_resolutions(self) -> Mapping[str, ResolutionResult]:
        return MappingProxyType(dict(self._named_selection_resolutions))

    @property
    def setup_statuses(self) -> Mapping[str, SetupRecordStatus]:
        return MappingProxyType(dict(self._setup_statuses))

    @property
    def mesh_quality_analysis(self) -> MeshQualityAnalysis | None:
        return self._mesh_quality_analysis

    @property
    def mesh_quality_view_model(self) -> MeshDiagnosticsViewModel:
        return build_mesh_diagnostics_view_model(
            self._mesh_quality_analysis,
            threshold=self._mesh_quality_threshold,
            mesh_label=self._mesh_ref,
            renderer_available=self._mesh_quality_renderer_available(),
            backend_reason=self._fallback_reason,
            highlight_visible=self._mesh_quality_highlight_visible,
            isolated=self._mesh_quality_visibility_snapshot is not None,
        )

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
        self._reset_mesh_quality_state(discard_cache=True)
        self._generation += 1
        generation = self._generation
        self._mesh = mesh
        self._mesh_ref = str(scene_input.mesh_ref or "")
        self._mesh_fingerprint = compute_mesh_fingerprint(mesh)
        self._clear_transient_state(call_session=False)
        session = self._ensure_session()
        if session is None:
            self._resolve_and_display_named_selections()
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
                self._resolve_and_display_named_selections()
                return self._fallback_scene_state(mesh, scene_state)
            self._actor_records.clear()

        payload = SceneMeshPayload(
            mesh=mesh,
            scene_input=scene_input,
            scene_state=scene_state,
            mesh_fingerprint=self._mesh_fingerprint,
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
            self._configure_session_picking()
            self._resolve_and_display_named_selections()
            session.request_render()
        except Exception as exc:
            self._fail_session(exc)
            self._resolve_and_display_named_selections()
            return self._fallback_scene_state(mesh, scene_state)

        self._fallback_reason = ""
        self._state = SceneLifecycleState.READY_SCENE
        if result is not None:
            return result
        return self._fallback_scene_state(mesh, scene_state)

    def set_selection_listener(
        self,
        callback: Callable[[], object] | None,
    ) -> None:
        """Install one thin GUI notification callback."""

        self._selection_listener = callback

    def set_pick_mode(self, mode: str | SelectionMode) -> bool:
        """Enable deterministic node/cell picking for the active mesh."""

        normalized = SelectionMode.coerce(mode)
        if normalized not in {SelectionMode.NODE, SelectionMode.CELL}:
            return False
        if normalized is not self._pick_mode:
            self._clear_transient_state(call_session=True)
        self._pick_mode = normalized
        configured = self._configure_session_picking()
        self._notify_selection_listener()
        return configured

    def disable_picking(self) -> bool:
        """Disable picking and clear incompatible transient state."""

        disabled = self._call_session("picking", "disable_picking")
        self._pick_mode = SelectionMode.NONE
        self._clear_transient_state(call_session=True)
        self._notify_selection_listener()
        return disabled

    def handle_pick(self, event: object) -> bool:
        """Validate and apply one renderer pick without persisting it."""

        pick = _coerce_pick_event(event)
        if pick is None or not self._pick_matches_current_scene(pick):
            return False
        entity_id = self._durable_id_from_backend_index(
            pick.entity_kind,
            pick.backend_index,
        )
        if entity_id is None:
            return False
        current_ids = (
            ()
            if self._current_selection_target is None
            or self._current_selection_target.locator is None
            else self._current_selection_target.locator.entity_ids
        )
        intent = pick.intent.lower()
        if intent == "replace":
            next_ids = (entity_id,)
        elif intent == "add":
            next_ids = _stable_entity_ids(
                pick.entity_kind,
                (*current_ids, entity_id),
            )
        elif intent == "toggle":
            if entity_id in current_ids:
                next_ids = tuple(item for item in current_ids if item != entity_id)
            else:
                next_ids = _stable_entity_ids(
                    pick.entity_kind,
                    (*current_ids, entity_id),
                )
        else:
            return False

        if not next_ids:
            self.clear_current_selection()
            return True
        self._current_selection_target = self._target_for_ids(
            pick.entity_kind,
            next_ids,
        )
        assert self._mesh is not None
        self._current_selection_resolution = resolve_selection_target(
            self._current_selection_target,
            mesh=self._mesh,
            mesh_ref=self._mesh_ref,
        )
        self._call_session(
            "selection-overlays",
            "set_current_selection",
            pick.entity_kind.value,
            self._current_selection_resolution.transient_indices,
            self._generation,
        )
        self._notify_selection_listener()
        return True

    def set_hover_target(self, backend_index: int | None) -> bool:
        """Update one transient hover target, separate from current selection."""

        if backend_index is None:
            self._hover_target = None
            cleared = self._call_session(
                "selection-overlays",
                "clear_hover",
            )
            self._notify_selection_listener()
            return cleared
        kind = _entity_kind_for_mode(self._pick_mode)
        if kind is None:
            return False
        entity_id = self._durable_id_from_backend_index(kind, int(backend_index))
        if entity_id is None:
            return False
        self._hover_target = self._target_for_ids(kind, (entity_id,))
        assert self._mesh is not None
        resolution = resolve_selection_target(
            self._hover_target,
            mesh=self._mesh,
            mesh_ref=self._mesh_ref,
        )
        applied = self._call_session(
            "selection-overlays",
            "set_hover_entities",
            kind.value,
            resolution.transient_indices,
            self._generation,
        )
        self._notify_selection_listener()
        return applied

    def clear_current_selection(self) -> bool:
        """Clear current committed transient picks without deleting named data."""

        self._current_selection_target = None
        self._current_selection_resolution = ResolutionResult(
            state=ResolutionState.UNRESOLVED,
            reason_code="CURRENT_SELECTION_EMPTY",
            message="No current entities are selected.",
        )
        self._call_session(
            "selection-overlays",
            "clear_current_selection",
        )
        self._notify_selection_listener()
        return True

    def set_named_selections(
        self,
        selections: Sequence[NamedSelection],
    ) -> None:
        """Retain Project selections and resolve them only against loaded memory."""

        self._named_selections = tuple(selections)
        self._resolve_and_display_named_selections()
        self._notify_selection_listener()

    def set_solver_setup(
        self,
        setup: object | None,
        *,
        materials: Sequence[object] = (),
    ) -> None:
        """Replace transient setup projections without mutating durable records."""

        self._solver_setup = setup
        self._setup_materials = tuple(materials)
        self._refresh_setup_overlays()
        self._notify_selection_listener()

    def set_setup_category_visible(self, category: str, visible: bool) -> bool:
        normalized = str(category)
        if normalized not in self._setup_category_visibility:
            return False
        self._setup_category_visibility[normalized] = bool(visible)
        for semantic_id in tuple(self._setup_overlay_ids):
            marker = (
                "fixed-support"
                if normalized == "fixed_support"
                else normalized
            )
            if semantic_id.startswith(f"setup:{marker}:"):
                self.set_actor_visible(semantic_id, visible)
        return True

    def analyze_mesh_quality(
        self,
        *,
        zero_edge_tolerance: float = 1e-12,
    ) -> MeshQualityAnalysis | None:
        """Analyze the active in-memory mesh once per exact geometry cache key."""

        mesh = self._mesh
        fingerprint = self._mesh_fingerprint
        if mesh is None or fingerprint is None:
            return None
        tolerance = float(zero_edge_tolerance)
        cache_key = (
            fingerprint.digest,
            MESH_QUALITY_METRIC_SCHEMA,
            MESH_QUALITY_TOPOLOGY_RULES,
            tolerance,
        )
        analysis = self._mesh_quality_cache.get(cache_key)
        if analysis is None:
            analysis = self._mesh_quality_analyzer(
                mesh,
                zero_edge_tolerance=tolerance,
            )
            if analysis.mesh_fingerprint.digest != fingerprint.digest:
                raise ValueError(
                    "Mesh Diagnostics analysis does not match the active mesh fingerprint."
                )
            self._mesh_quality_cache[cache_key] = analysis
        self._mesh_quality_analysis = analysis
        if self._mesh_quality_highlight_visible:
            self._refresh_mesh_quality_actor()
        return analysis

    def set_mesh_quality_threshold(self, threshold: float) -> bool:
        """Derive a new bad-cell subset without recomputing mesh geometry."""

        try:
            build_mesh_diagnostics_view_model(
                self._mesh_quality_analysis,
                threshold=float(threshold),
                mesh_label=self._mesh_ref,
                renderer_available=self._mesh_quality_renderer_available(),
                backend_reason=self._fallback_reason,
            )
        except (TypeError, ValueError):
            return False
        self._mesh_quality_threshold = float(threshold)
        if self._mesh_quality_highlight_visible:
            return self._refresh_mesh_quality_actor()
        return True

    def set_mesh_quality_highlight_visible(self, visible: bool) -> bool:
        """Show or remove the one semantic bad-cell actor."""

        if not visible:
            self.restore_mesh_quality_visibility()
            self._mesh_quality_highlight_visible = False
            self._remove_mesh_quality_actor()
            return True
        if (
            self._mesh_quality_analysis is None
            or not self._mesh_quality_renderer_available()
        ):
            return False
        self._mesh_quality_highlight_visible = True
        return self._refresh_mesh_quality_actor()

    def set_mesh_quality_isolated(self, isolated: bool) -> bool:
        """Hide only base/wireframe actors while preserving unrelated overlays."""

        if not isolated:
            return self.restore_mesh_quality_visibility()
        if (
            not self._mesh_quality_highlight_visible
            or MESH_QUALITY_ACTOR_KEY not in self._actor_records
            or not self._mesh_quality_renderer_available()
        ):
            return False
        if self._mesh_quality_visibility_snapshot is not None:
            return True
        snapshot = {
            semantic_id: self._actor_records[semantic_id].visible
            for semantic_id in ("base_mesh", "wireframe")
            if semantic_id in self._actor_records
        }
        self._mesh_quality_visibility_snapshot = snapshot
        for semantic_id in snapshot:
            if not self.set_actor_visible(semantic_id, False):
                self._mesh_quality_visibility_snapshot = None
                return False
        return True

    def restore_mesh_quality_visibility(self) -> bool:
        """Restore the diagnostics-local base/wireframe visibility snapshot."""

        snapshot = self._mesh_quality_visibility_snapshot
        if snapshot is None:
            return True
        restored = True
        for semantic_id, visible in snapshot.items():
            if semantic_id in self._actor_records:
                restored = self.set_actor_visible(semantic_id, visible) and restored
        if restored:
            self._mesh_quality_visibility_snapshot = None
        return restored

    def clear_mesh_quality_overlay(self) -> bool:
        """Clear transient emphasis while retaining same-fingerprint analysis."""

        restored = self.restore_mesh_quality_visibility()
        self._mesh_quality_highlight_visible = False
        self._remove_mesh_quality_actor()
        return restored

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
        if self._mesh_quality_visibility_snapshot is not None:
            self._mesh_quality_visibility_snapshot = {
                key: bool(value)
                for key, value in _REPRESENTATION_VISIBILITY[mode].items()
            }
            for semantic_id in self._mesh_quality_visibility_snapshot:
                if semantic_id in self._actor_records:
                    self.set_actor_visible(semantic_id, False)
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
        self._reset_mesh_quality_state(discard_cache=True)
        self._generation += 1
        self._mesh = None
        self._mesh_ref = ""
        self._mesh_fingerprint = None
        self._clear_transient_state(call_session=False)
        self._named_selection_resolutions = {
            selection.id: resolve_named_selection(selection)
            for selection in self._named_selections
        }
        self._named_overlay_ids.clear()
        self._setup_overlay_ids.clear()
        self._setup_statuses = {}
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
        self._reset_mesh_quality_state(discard_cache=True)
        self._generation += 1
        self._state = SceneLifecycleState.CLOSING
        session = self._session
        self._session = None
        self._actor_records.clear()
        if session is not None:
            disable_picking = getattr(session, "disable_picking", None)
            if callable(disable_picking):
                try:
                    disable_picking()
                except Exception as exc:
                    self._fallback_reason = str(exc)
            try:
                session.clear()
            except Exception as exc:
                self._fallback_reason = str(exc)
            try:
                session.close()
            except Exception as exc:
                self._fallback_reason = str(exc)
        self._state = SceneLifecycleState.CLOSED
        self._mesh = None
        self._mesh_ref = ""
        self._mesh_fingerprint = None
        self._clear_transient_state(call_session=False)
        self._named_overlay_ids.clear()
        self._setup_overlay_ids.clear()
        self._setup_statuses = {}

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
        self._mesh_quality_highlight_visible = False
        self._mesh_quality_visibility_snapshot = None
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

    def _configure_session_picking(self) -> bool:
        if self._pick_mode not in {SelectionMode.NODE, SelectionMode.CELL}:
            return False
        if self._mesh is None or self._mesh_fingerprint is None:
            return False
        callback = self.guard_callback(self.handle_pick, stale_result=False)
        return self._call_session(
            "picking",
            "set_pick_mode",
            self._pick_mode.value,
            callback,
        )

    def _pick_matches_current_scene(self, event: ScenePickEvent) -> bool:
        expected_kind = _entity_kind_for_mode(self._pick_mode)
        fingerprint = self._mesh_fingerprint
        return bool(
            self._mesh is not None
            and fingerprint is not None
            and event.generation == self._generation
            and event.mesh_ref == self._mesh_ref
            and event.mesh_fingerprint == fingerprint.digest
            and event.entity_kind is expected_kind
        )

    def _durable_id_from_backend_index(
        self,
        entity_kind: EntityKind,
        backend_index: int,
    ) -> int | str | None:
        mesh = self._mesh
        if mesh is None or backend_index < 0:
            return None
        if entity_kind is EntityKind.NODE:
            return backend_index if backend_index < len(mesh.points) else None
        if entity_kind is not EntityKind.CELL:
            return None
        remaining = backend_index
        for block_ordinal, block in enumerate(mesh.cells):
            if remaining < block.count:
                return f"{block_ordinal}:{remaining}"
            remaining -= block.count
        return None

    def _target_for_ids(
        self,
        entity_kind: EntityKind,
        entity_ids: Sequence[int | str],
    ) -> SelectionTargetRef:
        fingerprint = self._mesh_fingerprint
        if fingerprint is None:
            raise RuntimeError("Cannot build a durable locator without a loaded mesh.")
        namespace = (
            NODE_ORDINAL_NAMESPACE
            if entity_kind is EntityKind.NODE
            else CELL_ORDINAL_NAMESPACE
        )
        stable_ids = _stable_entity_ids(entity_kind, entity_ids)
        locator = EntityLocator(
            identity_schema=fingerprint.schema,
            mesh_ref=self._mesh_ref,
            mesh_fingerprint=fingerprint.digest,
            entity_kind=entity_kind,
            id_namespace=namespace,
            entity_ids=stable_ids,
        )
        return SelectionTargetRef(
            kind=entity_kind,
            ids=stable_ids,
            mesh_ref=self._mesh_ref,
            locator=locator,
        )

    def _clear_transient_state(self, *, call_session: bool) -> None:
        self._hover_target = None
        self._current_selection_target = None
        self._current_selection_resolution = ResolutionResult(
            state=ResolutionState.UNRESOLVED,
            reason_code="CURRENT_SELECTION_EMPTY",
            message="No current entities are selected.",
        )
        if call_session:
            self._call_session("selection-overlays", "clear_hover")
            self._call_session(
                "selection-overlays",
                "clear_current_selection",
            )

    def _resolve_and_display_named_selections(self) -> None:
        session = self._session
        if session is not None and "selection-overlays" in self.capabilities:
            for selection_id in tuple(self._named_overlay_ids):
                method = getattr(
                    session,
                    "remove_named_selection_overlay",
                    None,
                )
                if callable(method):
                    try:
                        method(selection_id)
                    except Exception as exc:
                        self._fail_session(exc)
                        return
            self._named_overlay_ids.clear()

        self._named_selection_resolutions = {}
        for selection in self._named_selections:
            result = resolve_named_selection(
                selection,
                mesh=self._mesh,
                mesh_ref=self._mesh_ref if self._mesh is not None else None,
            )
            self._named_selection_resolutions[selection.id] = result
            if (
                result.state is not ResolutionState.RESOLVED
                or session is None
                or "selection-overlays" not in self.capabilities
            ):
                continue
            method = getattr(session, "set_named_selection_overlay", None)
            if not callable(method):
                continue
            try:
                method(
                    selection.id,
                    selection.entity_kind.value,
                    result.transient_indices,
                    self._generation,
                )
            except Exception as exc:
                self._fail_session(exc)
                return
            self._named_overlay_ids.add(selection.id)
        self._refresh_setup_overlays()

    def _refresh_setup_overlays(self) -> None:
        session = self._session
        for semantic_id in tuple(self._setup_overlay_ids):
            if session is not None:
                remover = getattr(session, "remove_actor", None)
                if callable(remover):
                    remover(semantic_id)
            self._actor_records.pop(semantic_id, None)
        self._setup_overlay_ids.clear()
        self._setup_statuses = {}
        if self._solver_setup is None:
            return
        statuses = evaluate_solver_setup(
            self._solver_setup,
            selections=self._named_selections,
            materials=self._setup_materials,
            resolutions=self._named_selection_resolutions,
        )
        self._setup_statuses = {item.record_id: item for item in statuses}
        if (
            session is None
            or self._mesh is None
            or "setup-overlays" not in self.capabilities
        ):
            return
        specs = build_setup_overlay_specs(
            self._solver_setup,
            mesh=self._mesh,
            resolutions=self._named_selection_resolutions,
            statuses=self._setup_statuses,
            category_visibility=self._setup_category_visibility,
        )
        for spec in specs:
            session.replace_actor(
                spec.actor_key,
                spec,
                generation=self._generation,
            )
            self._actor_records[spec.actor_key] = SceneActorRecord(
                semantic_id=spec.actor_key,
                generation=self._generation,
                visible=spec.visible,
            )
            session.set_actor_visible(spec.actor_key, spec.visible)
            self._setup_overlay_ids.add(spec.actor_key)

    def _mesh_quality_renderer_available(self) -> bool:
        return bool(
            self._session is not None
            and self._state
            not in {
                SceneLifecycleState.CLOSING,
                SceneLifecycleState.CLOSED,
                SceneLifecycleState.FALLBACK,
            }
            and "mesh-quality-overlays" in self.capabilities
        )

    def _refresh_mesh_quality_actor(self) -> bool:
        analysis = self._mesh_quality_analysis
        fingerprint = self._mesh_fingerprint
        if (
            analysis is None
            or fingerprint is None
            or analysis.mesh_fingerprint.digest != fingerprint.digest
        ):
            self._remove_mesh_quality_actor()
            return False
        spec = build_mesh_quality_overlay_spec(
            analysis,
            threshold=self._mesh_quality_threshold,
            visible=True,
        )
        if spec is None:
            self.restore_mesh_quality_visibility()
            self._remove_mesh_quality_actor()
            return True
        view_model = self.mesh_quality_view_model
        if spec.stable_cell_keys != view_model.bad_cell_keys:
            raise RuntimeError(
                "Mesh Diagnostics table and semantic actor cell identities diverged."
            )
        if not self._mesh_quality_renderer_available():
            self._remove_mesh_quality_actor()
            return False
        session = self._session
        assert session is not None
        try:
            session.replace_actor(
                MESH_QUALITY_ACTOR_KEY,
                spec,
                generation=self._generation,
            )
            self._actor_records[MESH_QUALITY_ACTOR_KEY] = SceneActorRecord(
                semantic_id=MESH_QUALITY_ACTOR_KEY,
                generation=self._generation,
                visible=True,
            )
            session.set_actor_visible(MESH_QUALITY_ACTOR_KEY, True)
            session.request_render()
        except Exception as exc:
            self._fail_session(exc)
            return False
        return True

    def _remove_mesh_quality_actor(self) -> None:
        self._actor_records.pop(MESH_QUALITY_ACTOR_KEY, None)
        session = self._session
        if session is None:
            return
        remover = getattr(session, "remove_actor", None)
        if not callable(remover):
            return
        try:
            remover(MESH_QUALITY_ACTOR_KEY)
        except Exception as exc:
            self._fail_session(exc)

    def _reset_mesh_quality_state(self, *, discard_cache: bool) -> None:
        self._remove_mesh_quality_actor()
        self._mesh_quality_analysis = None
        self._mesh_quality_threshold = 10.0
        self._mesh_quality_highlight_visible = False
        self._mesh_quality_visibility_snapshot = None
        if discard_cache:
            self._mesh_quality_cache.clear()

    def _notify_selection_listener(self) -> None:
        callback = self._selection_listener
        if callback is None:
            return
        try:
            callback()
        except Exception:
            return

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


def _coerce_pick_event(value: object) -> ScenePickEvent | None:
    if isinstance(value, ScenePickEvent):
        return value
    if not isinstance(value, Mapping):
        return None
    try:
        return ScenePickEvent(
            generation=int(value.get("generation", -1)),
            mesh_ref=str(value.get("mesh_ref", "")),
            mesh_fingerprint=str(value.get("mesh_fingerprint", "")).lower(),
            entity_kind=EntityKind.coerce(value.get("entity_kind")),
            backend_index=int(value.get("backend_index", -1)),
            intent=str(
                value.get("intent", value.get("modifier", "replace"))
            ),
        )
    except (TypeError, ValueError):
        return None


def _entity_kind_for_mode(mode: SelectionMode) -> EntityKind | None:
    if mode is SelectionMode.NODE:
        return EntityKind.NODE
    if mode is SelectionMode.CELL:
        return EntityKind.CELL
    return None


def _stable_entity_ids(
    entity_kind: EntityKind,
    values: Sequence[int | str],
) -> tuple[int | str, ...]:
    unique = set(values)
    if entity_kind is EntityKind.NODE:
        return tuple(sorted(unique, key=int))

    def cell_key(value: int | str) -> tuple[int, int]:
        pieces = str(value).split(":")
        return int(pieces[0]), int(pieces[1])

    return tuple(sorted(unique, key=cell_key))


__all__ = [
    "ActiveSceneController",
    "SceneActorRecord",
    "SceneAdapterRendererFactory",
    "SceneAdapterRendererSession",
    "SceneLifecycleState",
    "SceneMeshPayload",
    "ScenePickEvent",
    "SceneRendererFactoryProtocol",
    "SceneRendererInitializationError",
    "SceneRendererSessionProtocol",
]
