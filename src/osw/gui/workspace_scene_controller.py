"""Deterministic active-scene ownership for one MainWindow document.

The controller is Qt-free and does not import PyVista.  It owns at most one
renderer session, keeps only semantic actor records outside that session, and
invalidates generation-guarded callbacks whenever scene resources are replaced
or torn down.  The current mesh-viewer ``SceneAdapterProtocol`` remains a
compatibility seam inside ``SceneAdapterRendererSession``.
"""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from dataclasses import field as dataclass_field
from enum import Enum
from inspect import Parameter, signature
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from osw.core.result_mesh_binding import (
    ResultMeshBinding,
    ResultMeshBindingResolution,
    resolve_result_mesh_binding,
)
from osw.core.selection import (
    EntityKind,
    EntityLocator,
    NamedSelection,
    SelectionMode,
    SelectionOperation,
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
from osw.core.solver_setup import (
    SetupRecordStatus,
    evaluate_solver_setup,
    iter_solver_setup_records,
    surface_cell_centroid_and_normal,
)
from osw.core.units import UnitSystem
from osw.core.workspace_3d import (
    ACTIVE_SCENE_PROVENANCE_METADATA_KEY,
    ACTIVE_SCENE_SCHEMA,
    ACTIVE_SCENE_STATE_METADATA_KEY,
    ActiveSceneCameraState,
    ActiveSceneClippingState,
    ActiveSceneRestoreResult,
    ActiveSceneRestoreStatus,
    ActiveSceneResultState,
    ActiveSceneScreenshotRequest,
    ActiveSceneState,
    MeshQualityViewState,
    SemanticActorVisibility,
    active_scene_provenance,
    captured_active_scene_state,
)
from osw.gui.interactive_results_view_model import (
    RESULT_COLORBAR_ACTOR_KEY,
    RESULT_DEFORMED_ACTOR_KEY,
    RESULT_ORIGINAL_REFERENCE_ACTOR_KEY,
    RESULT_PROBE_ACTOR_KEY,
    RESULT_SCALAR_ACTOR_KEY,
    RESULT_VECTOR_ACTOR_KEY,
    InteractiveResultSessionState,
    InteractiveResultsViewModel,
    ResultProbeOverlaySpec,
    build_colorbar_spec,
    build_deformed_overlay_spec,
    build_interactive_results_view_model,
    build_scalar_overlay_spec,
)
from osw.gui.mesh_diagnostics_view_model import (
    MESH_BAD_ELEMENTS_ACTOR_KEY,
    MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY,
    MESH_QUALITY_ACTOR_KEY,
    MESH_QUALITY_SCALARBAR_ACTOR_KEY,
    MeshDiagnosticsViewModel,
    MeshQualityOverlaySpec,
    MeshQualityScalarBarSpec,
    build_mesh_diagnostics_overlay_specs,
    build_mesh_diagnostics_view_model,
)
from osw.gui.setup_overlay_view_model import build_setup_overlay_specs
from osw.gui.workspace_scene_view_model import (
    DefaultSceneAdapter,
    SceneAdapterProtocol,
)
from osw.mesh.identity import MeshFingerprint, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshData
from osw.mesh.quality import (
    DEFAULT_DEGENERATE_EPSILON,
    DEFAULT_MESH_QUALITY_THRESHOLD,
    MESH_QUALITY_METRIC_SCHEMA,
    MESH_QUALITY_TOPOLOGY_RULES,
    MeshDiagnosticsStatus,
    MeshQualityAnalysis,
    analyze_mesh_cell_quality,
    reclassify_mesh_quality,
)
from osw.post.pyvista_scene import (
    PyVistaSceneConfig,
    PyVistaUnavailableError,
    build_scene_state,
)
from osw.post.result_deformation import (
    DeformationMode,
    DeformationScaleMode,
    DeformationStatus,
    DeformedShapeSpec,
    build_deformed_shape_spec,
)
from osw.post.result_field_catalog import (
    ResultFieldCatalog,
    build_result_field_catalog,
)
from osw.post.result_field_mapping import (
    InteractiveScalarResult,
    ResultVectorGlyphSpec,
    ScalarRangeMode,
    VectorScaleMode,
    build_result_vector_glyph_spec,
    project_interactive_scalar_result,
)
from osw.post.result_probe import (
    ResultProbeRequest,
    ResultProbeResult,
    ResultProbeStatus,
    SelectedResultTable,
    build_selected_result_table,
    probe_result_entity,
)
from osw.post.scene_model import (
    SceneCameraState,
    SceneInputRef,
    SceneRenderOptions,
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
    category: str = "geometry"
    pickable: bool = False
    isolation_eligible: bool = True
    is_helper: bool = False
    metadata: Mapping[str, object] = dataclass_field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def is_content(self) -> bool:
        return not self.is_helper


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


@dataclass(frozen=True)
class SetupPickEvent:
    """Renderer-neutral setup-overlay inspection evidence."""

    generation: int
    setup_id: str
    semantic_id: str = ""


@dataclass(frozen=True)
class ActiveSceneScreenshotResult:
    """Explicit screenshot outcome with deterministic capture provenance."""

    status: str
    record: SceneScreenshotRecord | None = None
    active_scene_digest: str = ""
    image_sha256: str = ""
    image_byte_length: int = 0
    image_size: tuple[int, int] | None = None
    backend_kind: str = ""
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class MeshQualityAnalysisRequest:
    """Immutable identity for one background-safe quality request."""

    request_id: int
    generation: int
    mesh_ref: str
    mesh_fingerprint: str
    mesh: MeshData
    threshold: float
    degenerate_epsilon: float


@dataclass(frozen=True)
class _InteractiveResultReplacementSnapshot:
    state: InteractiveResultSessionState
    probe: ResultProbeResult | None = None
    table: SelectedResultTable | None = None


@runtime_checkable
class SceneRendererSessionProtocol(Protocol):
    """One renderer backend session whose native objects stay session-local."""

    backend_kind: str
    capabilities: frozenset[str]

    @property
    def hosted_widget(self) -> object | None: ...

    def clear(self) -> None: ...

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object | None: ...

    def remove_actor(self, semantic_id: str) -> None: ...

    def request_render(self) -> None: ...

    def fit_to_scene(self) -> bool | None: ...

    def set_camera_preset(self, preset: str) -> bool | None: ...

    def set_interaction_mode(self, mode: str) -> None: ...

    def set_axes_visible(self, visible: bool) -> None: ...

    def set_representation(self, mode: str) -> None: ...

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None: ...

    def isolate_actor(self, semantic_id: str) -> None: ...

    def clear_isolation(self) -> None: ...

    def show_all_actors(self) -> None: ...

    def enable_clipping(self, axis: str, origin: float) -> None: ...

    def update_clipping(self, axis: str, origin: float) -> None: ...

    def clear_clipping(self) -> None: ...

    def set_pick_mode(
        self,
        mode: str,
        callback: Callable[[object], object],
    ) -> None: ...

    def set_selection_operation(self, operation: str) -> None: ...

    def disable_picking(self) -> None: ...

    def set_hover_entities(
        self,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None: ...

    def clear_hover(self) -> None: ...

    def set_current_selection(
        self,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None: ...

    def clear_current_selection(self) -> None: ...

    def clear_selection_highlights(self) -> None: ...

    def set_named_selection_overlay(
        self,
        selection_id: str,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None: ...

    def remove_named_selection_overlay(self, selection_id: str) -> None: ...

    def set_active_named_selection_overlay(
        self,
        selection_id: str,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None: ...

    def remove_active_named_selection_overlay(self, selection_id: str) -> None: ...

    def close(self) -> None: ...


@runtime_checkable
class SceneRendererFactoryProtocol(Protocol):
    """Factory for one explicit renderer-session backend."""

    backend_kind: str
    capabilities: frozenset[str]

    def create_session(self) -> SceneRendererSessionProtocol: ...


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
        self._scene_view_state = SceneViewState()
        self._representation = "surface"
        self._axes_visible = True
        self._isolation_snapshot: dict[str, bool] | None = None
        self._clipping_state = ActiveSceneClippingState()
        self._active_named_selection_ids: tuple[str, ...] = ()
        self._pending_active_scene_state: ActiveSceneState | None = None
        self._active_scene_restore_result = ActiveSceneRestoreResult(
            ActiveSceneRestoreStatus.PENDING,
            ("ACTIVE_MESH_NOT_LOADED",),
            ("No saved active scene is ready to restore.",),
        )
        self._pick_mode = SelectionMode.NONE
        self._selection_operation = SelectionOperation.REPLACE
        self._hover_target: SelectionTargetRef | None = None
        self._current_selection_target: SelectionTargetRef | None = None
        self._current_selection_resolution = ResolutionResult()
        self._named_selections: tuple[NamedSelection, ...] = ()
        self._named_selection_resolutions: dict[str, ResolutionResult] = {}
        self._named_overlay_ids: set[str] = set()
        self._active_named_overlay_ids: set[str] = set()
        self._solver_setup: object | None = None
        self._setup_materials: tuple[object, ...] = ()
        self._setup_units = UnitSystem.si()
        self._setup_statuses: dict[str, SetupRecordStatus] = {}
        self._setup_overlay_ids: set[str] = set()
        self._setup_overlay_categories: dict[str, str] = {}
        self._setup_record_visibility: dict[str, bool] = {}
        self._active_setup_id = ""
        self._setup_category_visibility = {
            "material": True,
            "fixed_support": True,
            "prescribed_displacement": True,
            "force": True,
            "pressure": True,
            "temperature": True,
            "heat_flux": True,
        }
        self._mesh_quality_analyzer = mesh_quality_analyzer or analyze_mesh_cell_quality
        self._mesh_quality_cache: dict[
            tuple[str, str, str, float],
            MeshQualityAnalysis,
        ] = {}
        self._mesh_quality_analysis: MeshQualityAnalysis | None = None
        self._mesh_quality_threshold = DEFAULT_MESH_QUALITY_THRESHOLD
        self._mesh_quality_degenerate_epsilon = DEFAULT_DEGENERATE_EPSILON
        self._mesh_quality_status = MeshDiagnosticsStatus.IDLE
        self._mesh_quality_coloring_visible = False
        self._mesh_quality_highlight_visible = False
        self._mesh_quality_filter_mode = "clear"
        self._mesh_quality_layer_snapshot: dict[str, bool] | None = None
        self._mesh_quality_visibility_snapshot: dict[str, bool] | None = None
        self._mesh_quality_next_request_id = 0
        self._mesh_quality_active_request: MeshQualityAnalysisRequest | None = None
        self._interactive_result_dataset: object | None = None
        self._interactive_result_binding: ResultMeshBinding | None = None
        self._interactive_result_ref_id = ""
        self._interactive_result_resolution: ResultMeshBindingResolution | None = None
        self._interactive_result_catalog: ResultFieldCatalog | None = None
        self._interactive_result_state = InteractiveResultSessionState()
        self._interactive_scalar_result: InteractiveScalarResult | None = None
        self._interactive_vector_result: ResultVectorGlyphSpec | None = None
        self._interactive_probe_result: ResultProbeResult | None = None
        self._interactive_result_table: SelectedResultTable | None = None
        self._interactive_deformation_result: DeformedShapeSpec | None = None
        self._interactive_result_visibility_snapshot: dict[str, bool] | None = None
        self._deformation_visibility_snapshot: dict[str, bool] | None = None
        self._primary_scalar_owner = ""
        self._result_primary_scalar_snapshot: dict[str, bool] | None = None
        self._quality_primary_scalar_snapshot: dict[str, bool] | None = None
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
    def isolation_active(self) -> bool:
        return self._isolation_snapshot is not None

    @property
    def representation(self) -> str:
        return self._representation

    @property
    def axes_visible(self) -> bool:
        return self._axes_visible

    @property
    def current_mesh_fingerprint(self) -> MeshFingerprint | None:
        return self._mesh_fingerprint

    @property
    def current_mesh_ref(self) -> str:
        return self._mesh_ref

    @property
    def pending_active_scene_state(self) -> ActiveSceneState | None:
        return self._pending_active_scene_state

    @property
    def active_scene_restore_result(self) -> ActiveSceneRestoreResult:
        return self._active_scene_restore_result

    @property
    def pick_mode(self) -> SelectionMode:
        return self._pick_mode

    @property
    def selection_operation(self) -> SelectionOperation:
        return self._selection_operation

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
    def resolved_selection_ids(self) -> frozenset[str]:
        return frozenset(
            selection_id
            for selection_id, resolution in self._named_selection_resolutions.items()
            if resolution.state is ResolutionState.RESOLVED and resolution.transient_indices
        )

    @property
    def active_named_selection_ids(self) -> tuple[str, ...]:
        return self._active_named_selection_ids

    @property
    def setup_statuses(self) -> Mapping[str, SetupRecordStatus]:
        return MappingProxyType(dict(self._setup_statuses))

    @property
    def active_setup_id(self) -> str:
        return self._active_setup_id

    @property
    def explicit_surface_selection_ids(self) -> frozenset[str]:
        """Return exact-resolved cell selections made only of supported surfaces."""

        if self._mesh is None:
            return frozenset()
        compatible: set[str] = set()
        for selection in self._named_selections:
            resolution = self._named_selection_resolutions.get(selection.id)
            if (
                selection.entity_kind is not EntityKind.CELL
                or resolution is None
                or resolution.state is not ResolutionState.RESOLVED
                or not resolution.transient_indices
            ):
                continue
            try:
                for cell_index in resolution.transient_indices:
                    surface_cell_centroid_and_normal(self._mesh, cell_index)
            except ValueError:
                continue
            compatible.add(selection.id)
        return frozenset(compatible)

    @property
    def mesh_quality_analysis(self) -> MeshQualityAnalysis | None:
        return self._mesh_quality_analysis

    @property
    def mesh_quality_status(self) -> MeshDiagnosticsStatus:
        return self._mesh_quality_status

    @property
    def mesh_quality_filter_mode(self) -> str:
        return self._mesh_quality_filter_mode

    @property
    def mesh_quality_view_model(self) -> MeshDiagnosticsViewModel:
        view_model = build_mesh_diagnostics_view_model(
            self._mesh_quality_analysis,
            threshold=self._mesh_quality_threshold,
            mesh_label=self._mesh_ref,
            renderer_available=self._mesh_quality_renderer_available(),
            backend_reason=self._fallback_reason,
            quality_coloring_visible=self._mesh_quality_coloring_visible,
            highlight_visible=self._mesh_quality_highlight_visible,
            filter_mode=self._mesh_quality_filter_mode,
        )
        if view_model.status != self._mesh_quality_status.value:
            view_model = replace(
                view_model,
                status=self._mesh_quality_status.value,
                overlay_actions_enabled=False,
                quality_coloring_visible=False,
                highlight_visible=False,
                filter_mode="clear",
                isolated=False,
            )
        return view_model

    @property
    def interactive_result_resolution(
        self,
    ) -> ResultMeshBindingResolution | None:
        return self._interactive_result_resolution

    @property
    def interactive_result_field_catalog(self) -> ResultFieldCatalog | None:
        return self._interactive_result_catalog

    @property
    def interactive_result_state(self) -> InteractiveResultSessionState:
        return self._interactive_result_state

    @property
    def interactive_results_view_model(self) -> InteractiveResultsViewModel:
        return build_interactive_results_view_model(
            self._interactive_result_resolution,
            renderer_available=self._interactive_result_renderer_available(),
            backend_reason=self._fallback_reason,
            scalar=self._interactive_scalar_result,
            vector=self._interactive_vector_result,
            probe=self._interactive_probe_result,
            table=self._interactive_result_table,
            catalog=self._interactive_result_catalog,
            deformation=self._interactive_deformation_result,
            state=self._interactive_result_state,
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
        incoming_fingerprint = compute_mesh_fingerprint(mesh)
        previous_analysis = self._mesh_quality_analysis
        previous_fingerprint = self._mesh_fingerprint
        result_snapshot = self._capture_interactive_result_snapshot()
        same_result_identity = bool(
            previous_fingerprint is not None
            and previous_fingerprint.digest == incoming_fingerprint.digest
        )
        same_quality_identity = bool(
            previous_analysis is not None
            and previous_fingerprint is not None
            and previous_fingerprint.digest == incoming_fingerprint.digest
        )
        self._prepare_mesh_quality_replacement(
            same_fingerprint=same_quality_identity,
            previous_analysis=previous_analysis,
        )
        self._reset_interactive_result_state(discard_binding=False)
        if result_snapshot is not None:
            self._interactive_result_state = (
                result_snapshot.state
                if same_result_identity
                else replace(
                    result_snapshot.state,
                    contour_visible=False,
                    vector_visible=False,
                    probe_mode="none",
                    deformation_mode=DeformationMode.ORIGINAL.value,
                )
            )
        self._generation += 1
        generation = self._generation
        self._mesh = mesh
        self._mesh_ref = str(scene_input.mesh_ref or "")
        self._mesh_fingerprint = incoming_fingerprint
        self._scene_view_state = scene_state
        self._representation = _representation_from_scene_state(scene_state)
        self._axes_visible = scene_state.render_options.show_axes
        self._isolation_snapshot = None
        self._clipping_state = ActiveSceneClippingState()
        self._clear_transient_state(call_session=False)
        session = self._ensure_session()
        if session is None:
            self._resolve_and_display_named_selections()
            self._resolve_interactive_result_binding()
            if same_result_identity and result_snapshot is not None:
                self._restore_interactive_result_snapshot(result_snapshot)
            if same_quality_identity:
                self._recompute_same_fingerprint_mesh_quality(previous_analysis)
            if self._pending_active_scene_state is not None:
                self.restore_pending_active_scene_state()
            self._notify_selection_listener()
            return self._fallback_scene_state(mesh, scene_state)

        replacing = bool(self._actor_records)
        self._state = (
            SceneLifecycleState.REPLACING if replacing else SceneLifecycleState.READY_EMPTY
        )
        if replacing:
            try:
                session.clear()
            except Exception as exc:
                self._fail_session(exc)
                self._resolve_and_display_named_selections()
                if self._pending_active_scene_state is not None:
                    self.restore_pending_active_scene_state()
                self._notify_selection_listener()
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
            self._actor_records["base_mesh"] = _scene_actor_record(
                "base_mesh",
                generation=generation,
            )
            session.replace_actor(
                "wireframe",
                payload,
                generation=generation,
            )
            self._actor_records["wireframe"] = _scene_actor_record(
                "wireframe",
                generation=generation,
            )
            representation = _representation_from_scene_state(scene_state)
            setter = getattr(session, "set_representation", None)
            if callable(setter):
                setter(representation)
            self._set_registry_representation(representation)
            self._configure_session_picking()
            self._resolve_and_display_named_selections()
            self._resolve_interactive_result_binding()
            if same_result_identity and result_snapshot is not None:
                self._restore_interactive_result_snapshot(result_snapshot)
            session.request_render()
        except Exception as exc:
            self._fail_session(exc)
            self._resolve_and_display_named_selections()
            self._resolve_interactive_result_binding()
            if self._pending_active_scene_state is not None:
                self.restore_pending_active_scene_state()
            self._notify_selection_listener()
            return self._fallback_scene_state(mesh, scene_state)

        self._fallback_reason = ""
        self._state = SceneLifecycleState.READY_SCENE
        if same_quality_identity:
            self._recompute_same_fingerprint_mesh_quality(previous_analysis)
        if self._pending_active_scene_state is not None:
            self.restore_pending_active_scene_state()
        self._notify_selection_listener()
        if result is not None:
            return result
        return self._fallback_scene_state(mesh, scene_state)

    def set_selection_listener(
        self,
        callback: Callable[[], object] | None,
    ) -> None:
        """Install one thin GUI notification callback."""

        self._selection_listener = callback

    def set_active_named_selection_ids(
        self,
        selection_ids: Sequence[str],
    ) -> bool:
        """Activate exact NamedSelections without changing their membership."""

        self._active_named_selection_ids = tuple(
            sorted({str(item) for item in selection_ids if str(item)})
        )
        applied = self._resolve_and_display_active_named_selections()
        self._notify_selection_listener()
        return applied

    def set_pick_mode(self, mode: str | SelectionMode) -> bool:
        """Enable deterministic node/cell picking for the active mesh."""

        normalized = SelectionMode.coerce(mode)
        if normalized not in {
            SelectionMode.NODE,
            SelectionMode.CELL,
            SelectionMode.SETUP,
        }:
            return False
        if normalized is not self._pick_mode:
            self._clear_transient_state(call_session=True)
        self._pick_mode = normalized
        configured = self._configure_session_picking()
        self._notify_selection_listener()
        return configured

    def handle_setup_pick(self, event: object) -> bool:
        """Activate semantic setup metadata without changing entity membership."""

        pick = _coerce_setup_pick_event(event)
        if (
            pick is None
            or self._pick_mode is not SelectionMode.SETUP
            or pick.generation != self._generation
            or not pick.setup_id
            or not any(
                semantic_id.endswith(f":{pick.setup_id}") for semantic_id in self._setup_overlay_ids
            )
        ):
            return False
        if pick.semantic_id and pick.semantic_id not in self._setup_overlay_ids:
            return False
        return self.set_active_setup_id(pick.setup_id)

    def set_selection_operation(
        self,
        operation: str | SelectionOperation,
    ) -> bool:
        """Set how subsequent native picks mutate the transient selection."""

        normalized = SelectionOperation.coerce(operation)
        self._selection_operation = normalized
        applied = self._call_session(
            "picking",
            "set_selection_operation",
            normalized.value,
        )
        self._notify_selection_listener()
        return applied

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
        intent = str(pick.intent or self._selection_operation.value).lower()
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
        elif intent == "subtract":
            next_ids = tuple(item for item in current_ids if item != entity_id)
        else:
            return False

        if not next_ids:
            self.clear_current_selection()
            return True
        self._apply_current_selection_ids(pick.entity_kind, next_ids)
        self._sync_active_named_selection_from_current()
        self._notify_selection_listener()
        return True

    def invert_current_selection(self) -> bool:
        """Select the exact complement of the current node/cell selection."""

        entity_kind = _entity_kind_for_mode(self._pick_mode)
        if self._mesh is None or entity_kind is None:
            return False
        current_ids = (
            ()
            if self._current_selection_target is None
            or self._current_selection_target.locator is None
            else self._current_selection_target.locator.entity_ids
        )
        domain_ids = _entity_domain_ids(self._mesh, entity_kind)
        current_set = set(current_ids)
        next_ids = tuple(item for item in domain_ids if item not in current_set)
        if not next_ids:
            self.clear_current_selection()
            return True
        self._apply_current_selection_ids(entity_kind, next_ids)
        self._sync_active_named_selection_from_current()
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
            self._actor_records.pop("hover", None)
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
        if applied:
            self._actor_records["hover"] = _scene_actor_record(
                "hover",
                generation=self._generation,
            )
        self._notify_selection_listener()
        return applied

    def clear_current_selection(self) -> bool:
        """Clear current committed transient picks without deleting named data."""

        self._current_selection_target = None
        self._active_named_selection_ids = ()
        self._current_selection_resolution = ResolutionResult(
            state=ResolutionState.UNRESOLVED,
            reason_code="CURRENT_SELECTION_EMPTY",
            message="No current entities are selected.",
        )
        self._call_session(
            "selection-overlays",
            "clear_current_selection",
        )
        self._actor_records.pop("current_selection", None)
        self.clear_result_probe()
        self._resolve_and_display_active_named_selections()
        self._notify_selection_listener()
        return True

    def clear_selection_highlights(self) -> bool:
        """Clear transient hover and current-selection native actors."""

        self._hover_target = None
        self._current_selection_target = None
        self._current_selection_resolution = ResolutionResult(
            state=ResolutionState.UNRESOLVED,
            reason_code="CURRENT_SELECTION_EMPTY",
            message="No current entities are selected.",
        )
        cleared = self._call_session(
            "selection-overlays",
            "clear_selection_highlights",
        )
        self._actor_records.pop("hover", None)
        self._actor_records.pop("current_selection", None)
        self.clear_result_probe()
        self._notify_selection_listener()
        return cleared

    def set_named_selections(
        self,
        selections: Sequence[NamedSelection],
    ) -> None:
        """Retain Project selections and resolve them only against loaded memory."""

        self._named_selections = tuple(selections)
        known_ids = {selection.id for selection in self._named_selections}
        self._active_named_selection_ids = tuple(
            selection_id
            for selection_id in self._active_named_selection_ids
            if selection_id in known_ids
        )
        self._resolve_and_display_named_selections()
        self._notify_selection_listener()

    def set_solver_setup(
        self,
        setup: object | None,
        *,
        materials: Sequence[object] = (),
        units: UnitSystem | None = None,
    ) -> None:
        """Replace transient setup projections without mutating durable records."""

        self._solver_setup = setup
        self._setup_materials = tuple(materials)
        self._setup_units = units or UnitSystem.si()
        known_ids = {
            str(record.id) for record in (() if setup is None else iter_solver_setup_records(setup))
        }
        self._setup_record_visibility = {
            record_id: visible
            for record_id, visible in self._setup_record_visibility.items()
            if record_id in known_ids
        }
        active_setup_removed = bool(
            self._active_setup_id and self._active_setup_id not in known_ids
        )
        if self._active_setup_id not in known_ids:
            self._active_setup_id = ""
        if active_setup_removed:
            self._active_named_selection_ids = ()
            self._resolve_and_display_active_named_selections()
        self._refresh_setup_overlays()
        self._notify_selection_listener()

    def set_setup_category_visible(self, category: str, visible: bool) -> bool:
        normalized = str(category)
        if normalized not in self._setup_category_visibility:
            return False
        self._setup_category_visibility[normalized] = bool(visible)
        for semantic_id in tuple(self._setup_overlay_ids):
            if self._setup_overlay_categories.get(semantic_id) == normalized:
                setup_id = semantic_id.rsplit(":", 1)[-1]
                record_visible = self._setup_record_visibility.get(setup_id, True)
                self.set_actor_visible(
                    semantic_id,
                    bool(visible) and record_visible,
                )
        return True

    def set_setup_record_visible(self, setup_id: str, visible: bool) -> bool:
        """Apply one transient visibility override without mutating the Project."""

        record_id = str(setup_id or "")
        if not record_id or not any(
            str(record.id) == record_id
            for record in (
                () if self._solver_setup is None else iter_solver_setup_records(self._solver_setup)
            )
        ):
            return False
        self._setup_record_visibility[record_id] = bool(visible)
        applied = False
        for semantic_id in tuple(self._setup_overlay_ids):
            if semantic_id.endswith(f":{record_id}"):
                category = self._setup_overlay_categories.get(semantic_id, "")
                category_visible = self._setup_category_visibility.get(category, True)
                applied = (
                    self.set_actor_visible(
                        semantic_id,
                        bool(visible) and category_visible,
                    )
                    or applied
                )
        return applied

    def set_active_setup_id(self, setup_id: str) -> bool:
        """Activate one durable setup identity and emphasize its NamedSelection."""

        record_id = str(setup_id or "")
        records = (
            () if self._solver_setup is None else iter_solver_setup_records(self._solver_setup)
        )
        record = next(
            (item for item in records if str(getattr(item, "id", "")) == record_id),
            None,
        )
        if record is None:
            return False
        self._active_setup_id = record_id
        target_id = str(getattr(record, "target_selection_id", ""))
        resolution = self._named_selection_resolutions.get(target_id)
        if resolution is not None and resolution.state is ResolutionState.RESOLVED:
            self._active_named_selection_ids = (target_id,)
        else:
            self._active_named_selection_ids = ()
        self._resolve_and_display_active_named_selections()
        self._notify_selection_listener()
        return True

    def clear_active_setup_id(self) -> bool:
        """Clear transient setup emphasis without changing persisted records."""

        if not self._active_setup_id:
            return False
        self._active_setup_id = ""
        self._notify_selection_listener()
        return True

    def set_interactive_result_dataset(
        self,
        result_dataset: object | None,
        binding: ResultMeshBinding | Mapping[str, object] | None,
        *,
        result_ref_id: str = "",
    ) -> ResultMeshBindingResolution | None:
        """Attach transient dataset data and resolve its persisted exact binding."""

        self.clear_interactive_results()
        self._interactive_result_dataset = result_dataset
        self._interactive_result_ref_id = str(result_ref_id or "")
        self._interactive_result_state = InteractiveResultSessionState(
            active_result_id=str(getattr(result_dataset, "dataset_id", "") or ""),
        )
        if isinstance(binding, ResultMeshBinding):
            self._interactive_result_binding = binding
        elif isinstance(binding, Mapping):
            try:
                self._interactive_result_binding = ResultMeshBinding.from_dict(binding)
            except (TypeError, ValueError):
                self._interactive_result_binding = None
        else:
            self._interactive_result_binding = None
        self._resolve_interactive_result_binding()
        self._restore_result_state_after_binding()
        return self._interactive_result_resolution

    def set_scalar_result(
        self,
        field_name: str,
        *,
        component: str | None = None,
        range_mode: ScalarRangeMode | str = ScalarRangeMode.AUTO,
        manual_range: tuple[float, float] | None = None,
        colormap: str = "viridis",
        colorbar_visible: bool = True,
        render: bool = True,
    ) -> InteractiveScalarResult:
        """Apply or replace one exact scalar projection without project mutation."""

        if self._mesh_quality_visibility_snapshot is not None:
            return InteractiveScalarResult(
                applied=False,
                status="INVALID",
                field_name=str(field_name),
                diagnostics=(
                    "Restore diagnostics isolation first before applying a scalar result.",
                ),
            )
        if (
            self._mesh is None
            or self._interactive_result_dataset is None
            or self._interactive_result_resolution is None
        ):
            return InteractiveScalarResult(
                applied=False,
                status="UNRESOLVED",
                field_name=str(field_name),
                diagnostics=("An exact mesh/result binding is not available.",),
            )
        result = project_interactive_scalar_result(
            self._active_result_geometry_mesh(),
            self._interactive_result_dataset,
            binding_resolution=self._interactive_result_resolution,
            field_name=field_name,
            component=component,
            range_mode=range_mode,
            manual_range=manual_range,
            colormap=colormap,
            colorbar_visible=colorbar_visible,
        )
        self._interactive_scalar_result = result
        self._interactive_result_state = replace(
            self._interactive_result_state,
            active_field_id=str(field_name),
            active_scalar_mode=(
                result.scalar_mode.value if result.applied else str(component or "scalar")
            ),
            contour_visible=bool(result.applied and render),
            range_mode=(result.range_mode.value if result.applied else str(range_mode).upper()),
            manual_range=(tuple(manual_range) if manual_range is not None else None),
            colormap=str(colormap).strip().lower(),
            colorbar_visible=bool(colorbar_visible),
        )
        if not result.applied or not render or not self._interactive_result_renderer_available():
            self._remove_result_actor(RESULT_SCALAR_ACTOR_KEY)
            self._remove_result_actor(RESULT_COLORBAR_ACTOR_KEY)
            return result
        fingerprint = self._mesh_fingerprint
        assert fingerprint is not None
        spec = build_scalar_overlay_spec(
            result,
            mesh_fingerprint=fingerprint.digest,
            result_id=str(getattr(self._interactive_result_dataset, "dataset_id", "") or ""),
            mesh=self._active_result_geometry_mesh(),
        )
        if spec is None:
            return result
        if self._interactive_result_visibility_snapshot is None:
            quality_snapshot = self._mesh_quality_layer_snapshot
            self._interactive_result_visibility_snapshot = {
                semantic_id: (
                    bool(quality_snapshot[semantic_id])
                    if quality_snapshot is not None and semantic_id in quality_snapshot
                    else self._actor_records[semantic_id].visible
                )
                for semantic_id in (
                    "base_mesh",
                    "wireframe",
                    RESULT_DEFORMED_ACTOR_KEY,
                )
                if semantic_id in self._actor_records
            }
        if not self._replace_result_actor(RESULT_SCALAR_ACTOR_KEY, spec):
            return result
        deformation_mode = self._interactive_result_state.deformation_mode
        for semantic_id in self._interactive_result_visibility_snapshot:
            if semantic_id in self._actor_records:
                hide = not (
                    deformation_mode == DeformationMode.OVERLAY.value
                    and semantic_id in {"base_mesh", "wireframe"}
                )
                if hide:
                    self.set_actor_visible(
                        semantic_id,
                        False,
                        preserve_transient=True,
                    )
        colorbar = build_colorbar_spec(result)
        if colorbar is None:
            self._remove_result_actor(RESULT_COLORBAR_ACTOR_KEY)
        else:
            self._replace_result_actor(RESULT_COLORBAR_ACTOR_KEY, colorbar)
        self._activate_result_primary_scalar()
        return result

    def set_vector_result(
        self,
        field_name: str,
        *,
        components: tuple[str, ...] | None = None,
        maximum_glyph_count: int = 500,
        scale: float = 1.0,
        scale_mode: VectorScaleMode | str = VectorScaleMode.MANUAL,
    ) -> ResultVectorGlyphSpec:
        """Apply or replace one bounded vector-glyph collection."""

        if (
            self._mesh is None
            or self._interactive_result_dataset is None
            or self._interactive_result_resolution is None
        ):
            return ResultVectorGlyphSpec(
                applied=False,
                status="UNRESOLVED",
                field_name=str(field_name),
                diagnostics=("An exact mesh/result binding is not available.",),
            )
        result = build_result_vector_glyph_spec(
            self._active_result_geometry_mesh(),
            self._interactive_result_dataset,
            binding_resolution=self._interactive_result_resolution,
            field_name=field_name,
            components=components,
            maximum_glyph_count=maximum_glyph_count,
            scale=scale,
            scale_mode=scale_mode,
        )
        self._interactive_vector_result = result
        self._interactive_result_state = replace(
            self._interactive_result_state,
            vector_field_id=str(field_name),
            vector_visible=bool(result.applied and result.sampled_count > 0),
            vector_max_glyph_count=int(maximum_glyph_count),
            vector_scale_mode=(
                result.scale_mode.value if result.applied else str(scale_mode).strip().upper()
            ),
            vector_manual_scale=float(scale),
        )
        if (
            result.applied
            and result.sampled_count > 0
            and self._interactive_result_renderer_available()
        ):
            self._replace_result_actor(RESULT_VECTOR_ACTOR_KEY, result)
        else:
            self._remove_result_actor(RESULT_VECTOR_ACTOR_KEY)
        return result

    def set_deformed_result(
        self,
        field_name: str,
        *,
        mode: DeformationMode | str = DeformationMode.ORIGINAL,
        scale_mode: DeformationScaleMode | str = DeformationScaleMode.AUTO,
        manual_scale: float | None = None,
    ) -> DeformedShapeSpec:
        """Apply one typed displacement view without mutating source geometry."""

        if (
            self._mesh is None
            or self._interactive_result_dataset is None
            or self._interactive_result_resolution is None
        ):
            return DeformedShapeSpec(
                applied=False,
                status=DeformationStatus.INVALID,
                field_name=str(field_name),
                diagnostics=("An exact mesh/result binding is not available.",),
            )
        result = build_deformed_shape_spec(
            self._mesh,
            self._interactive_result_dataset,
            binding_resolution=self._interactive_result_resolution,
            field_name=field_name,
            mode=mode,
            scale_mode=scale_mode,
            manual_scale=manual_scale,
        )
        self._interactive_deformation_result = result
        self._interactive_result_state = replace(
            self._interactive_result_state,
            deformation_field_id=str(field_name),
            deformation_mode=(result.mode.value if result.applied else str(mode).strip().upper()),
            deformation_scale_mode=(
                result.scale_mode.value if result.applied else str(scale_mode).strip().upper()
            ),
            deformation_manual_scale=(float(manual_scale) if manual_scale is not None else 1.0),
        )
        if not result.applied:
            self._remove_result_actor(RESULT_DEFORMED_ACTOR_KEY)
            self._remove_result_actor(RESULT_ORIGINAL_REFERENCE_ACTOR_KEY)
            return result
        if result.mode is DeformationMode.ORIGINAL:
            self.clear_deformed_result(preserve_configuration=True)
            return result
        spec = build_deformed_overlay_spec(
            result,
            result_id=str(getattr(self._interactive_result_dataset, "dataset_id", "") or ""),
        )
        if spec is None or not self._interactive_result_renderer_available():
            return result
        if self._deformation_visibility_snapshot is None:
            self._deformation_visibility_snapshot = {
                semantic_id: record.visible
                for semantic_id, record in self._actor_records.items()
                if semantic_id in {"base_mesh", "wireframe"}
                or record.category in {"setup", "diagnostic"}
            }
        self._replace_result_actor(RESULT_DEFORMED_ACTOR_KEY, spec)
        if self._interactive_result_visibility_snapshot is not None:
            self._interactive_result_visibility_snapshot[RESULT_DEFORMED_ACTOR_KEY] = True
        self._refresh_result_selection_geometry()
        if result.mode is DeformationMode.DEFORMED:
            self._set_visibility_map(
                {semantic_id: False for semantic_id in self._deformation_visibility_snapshot}
            )
        else:
            self._restore_deformation_snapshot(keep_snapshot=True)
        self._refresh_result_geometry_dependents()
        return result

    def clear_vector_result(self) -> bool:
        """Remove the aggregate vector actor while retaining its configuration."""

        existed = RESULT_VECTOR_ACTOR_KEY in self._actor_records
        self._remove_result_actor(RESULT_VECTOR_ACTOR_KEY)
        self._interactive_vector_result = None
        self._interactive_result_state = replace(
            self._interactive_result_state,
            vector_visible=False,
        )
        return existed

    def clear_result_probe(self) -> bool:
        """Clear one transient result probe marker and table."""

        existed = RESULT_PROBE_ACTOR_KEY in self._actor_records
        self._remove_result_actor(RESULT_PROBE_ACTOR_KEY)
        self._interactive_probe_result = None
        self._interactive_result_table = None
        self._interactive_result_state = replace(
            self._interactive_result_state,
            probe_mode="none",
        )
        return existed

    def clear_deformed_result(
        self,
        *,
        preserve_configuration: bool = False,
        refresh_dependents: bool = True,
    ) -> bool:
        """Remove derived geometry and restore original actor visibility."""

        had_deformation = self._interactive_deformation_result is not None
        self._remove_result_actor(RESULT_DEFORMED_ACTOR_KEY)
        self._remove_result_actor(RESULT_ORIGINAL_REFERENCE_ACTOR_KEY)
        restored = self._restore_deformation_snapshot(keep_snapshot=False)
        self._interactive_deformation_result = None
        if not preserve_configuration:
            self._interactive_result_state = replace(
                self._interactive_result_state,
                deformation_mode=DeformationMode.ORIGINAL.value,
            )
        if had_deformation and refresh_dependents:
            self._refresh_result_geometry_dependents()
            self._refresh_result_selection_geometry()
        return restored

    def probe_result(
        self,
        request: ResultProbeRequest,
    ) -> ResultProbeResult:
        """Resolve one exact stored point/cell value and optional probe marker."""

        if (
            self._mesh is None
            or self._interactive_result_dataset is None
            or self._interactive_result_resolution is None
        ):
            result = ResultProbeResult(
                status=ResultProbeStatus.STALE,
                stable_entity_key=request.stable_entity_key,
                entity_display_id=(f"{request.association} {request.stable_entity_key}"),
                field_name=request.field_name,
                component=request.component,
                association=request.association,
                reason_code="RESULT_BINDING_NOT_CONFIGURED",
                diagnostics=("An exact mesh/result binding is not available.",),
            )
            self._interactive_probe_result = result
            return result
        result = probe_result_entity(
            self._mesh,
            self._interactive_result_dataset,
            request,
            binding_resolution=self._interactive_result_resolution,
        )
        self._interactive_probe_result = result
        self._interactive_result_state = replace(
            self._interactive_result_state,
            probe_mode=(
                request.association if result.status is ResultProbeStatus.RESOLVED else "none"
            ),
        )
        if (
            result.status is ResultProbeStatus.RESOLVED
            and self._interactive_result_renderer_available()
        ):
            transient_index = _result_stable_key_index(
                self._mesh,
                request.association,
                request.stable_entity_key,
            )
            fingerprint = self._mesh_fingerprint
            if transient_index is not None and fingerprint is not None:
                self._replace_result_actor(
                    RESULT_PROBE_ACTOR_KEY,
                    ResultProbeOverlaySpec(
                        actor_key=RESULT_PROBE_ACTOR_KEY,
                        association=request.association,
                        stable_entity_key=request.stable_entity_key,
                        transient_backend_index=transient_index,
                        mesh_fingerprint=fingerprint.digest,
                    ),
                )
        else:
            self._remove_result_actor(RESULT_PROBE_ACTOR_KEY)
        return result

    def set_selected_result_table(
        self,
        *,
        field_name: str,
        component: str,
        association: str,
        stable_entity_keys: Sequence[int | str],
        limit: int = 500,
    ) -> SelectedResultTable | None:
        """Derive a bounded exact-value table from stable selected entities."""

        if (
            self._mesh is None
            or self._interactive_result_dataset is None
            or self._interactive_result_resolution is None
        ):
            self._interactive_result_table = None
            return None
        table = build_selected_result_table(
            self._mesh,
            self._interactive_result_dataset,
            field_name=field_name,
            component=component,
            association=association,
            stable_entity_keys=stable_entity_keys,
            binding_resolution=self._interactive_result_resolution,
            limit=limit,
        )
        self._interactive_result_table = table
        return table

    def clear_scalar_result(self) -> bool:
        """Remove scalar/colorbar resources and restore exact mesh visibility."""

        self._interactive_scalar_result = None
        self._interactive_result_state = replace(
            self._interactive_result_state,
            contour_visible=False,
        )
        self._remove_result_actor(RESULT_SCALAR_ACTOR_KEY)
        self._remove_result_actor(RESULT_COLORBAR_ACTOR_KEY)
        snapshot = self._interactive_result_visibility_snapshot
        restored = True
        if snapshot is not None:
            if self._mesh_quality_coloring_visible:
                if self._mesh_quality_layer_snapshot is None:
                    self._mesh_quality_layer_snapshot = {}
                self._mesh_quality_layer_snapshot.update(snapshot)
                self._mesh_quality_layer_snapshot.pop(RESULT_SCALAR_ACTOR_KEY, None)
                self._mesh_quality_layer_snapshot.pop(RESULT_COLORBAR_ACTOR_KEY, None)
                restored = self._refresh_mesh_quality_resources()
            else:
                for semantic_id, visible in snapshot.items():
                    if semantic_id in self._actor_records:
                        restored = (
                            self.set_actor_visible(
                                semantic_id,
                                visible,
                                preserve_transient=True,
                            )
                            and restored
                        )
        restored = self._restore_result_primary_scalar() and restored
        if restored:
            self._interactive_result_visibility_snapshot = None
        return restored

    def clear_interactive_results(self) -> bool:
        """Idempotently remove all transient interactive-result resources."""

        restored = self.clear_scalar_result()
        self._interactive_vector_result = None
        self._interactive_probe_result = None
        self._interactive_result_table = None
        self.clear_deformed_result(
            preserve_configuration=True,
            refresh_dependents=False,
        )
        self._interactive_result_state = replace(
            self._interactive_result_state,
            vector_visible=False,
            probe_mode="none",
        )
        for semantic_id in (
            RESULT_VECTOR_ACTOR_KEY,
            RESULT_PROBE_ACTOR_KEY,
        ):
            self._remove_result_actor(semantic_id)
        return restored

    def analyze_mesh_quality(
        self,
        *,
        zero_edge_tolerance: float = DEFAULT_DEGENERATE_EPSILON,
    ) -> MeshQualityAnalysis | None:
        """Synchronously execute the same request/commit seam used by the GUI worker."""

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
        if analysis is not None:
            analysis = reclassify_mesh_quality(
                analysis,
                threshold=self._mesh_quality_threshold,
            )
            self._mesh_quality_analysis = analysis
            self._mesh_quality_status = analysis.status
            self._refresh_mesh_quality_resources()
            return analysis
        request = self.begin_mesh_quality_analysis(
            degenerate_epsilon=tolerance,
        )
        if request is None:
            return None
        try:
            analysis = self._call_mesh_quality_analyzer(request)
        except Exception:
            if self._mesh_quality_active_request == request:
                self._mesh_quality_active_request = None
                self._mesh_quality_status = MeshDiagnosticsStatus.FAILED
            raise
        if not self.complete_mesh_quality_analysis(request, analysis):
            return None
        return self._mesh_quality_analysis

    def begin_mesh_quality_analysis(
        self,
        *,
        degenerate_epsilon: float = DEFAULT_DEGENERATE_EPSILON,
    ) -> MeshQualityAnalysisRequest | None:
        """Capture immutable mesh identity for one optional background request."""

        if (
            self._mesh is None
            or self._mesh_fingerprint is None
            or self._mesh_quality_active_request is not None
            or self._state in {SceneLifecycleState.CLOSING, SceneLifecycleState.CLOSED}
        ):
            return None
        epsilon = float(degenerate_epsilon)
        if not isfinite(epsilon) or epsilon < 0.0:
            raise ValueError("Degenerate epsilon must be finite and non-negative.")
        self._mesh_quality_next_request_id += 1
        request = MeshQualityAnalysisRequest(
            request_id=self._mesh_quality_next_request_id,
            generation=self._generation,
            mesh_ref=self._mesh_ref,
            mesh_fingerprint=self._mesh_fingerprint.digest,
            mesh=self._mesh,
            threshold=self._mesh_quality_threshold,
            degenerate_epsilon=epsilon,
        )
        self._mesh_quality_active_request = request
        self._mesh_quality_status = MeshDiagnosticsStatus.RUNNING
        return request

    def complete_mesh_quality_analysis(
        self,
        request: MeshQualityAnalysisRequest,
        analysis: MeshQualityAnalysis,
    ) -> bool:
        """Accept only the still-current request and exact mesh fingerprint."""

        active = self._mesh_quality_active_request
        fingerprint = self._mesh_fingerprint
        if (
            active is None
            or request.request_id != active.request_id
            or request.generation != self._generation
            or fingerprint is None
            or request.mesh_fingerprint != fingerprint.digest
            or request.mesh_ref != self._mesh_ref
            or analysis.mesh_fingerprint.digest != fingerprint.digest
            or self._state in {SceneLifecycleState.CLOSING, SceneLifecycleState.CLOSED}
        ):
            return False
        classified = reclassify_mesh_quality(
            analysis,
            threshold=self._mesh_quality_threshold,
        )
        classified = replace(classified, mesh_ref=request.mesh_ref)
        cache_key = (
            fingerprint.digest,
            MESH_QUALITY_METRIC_SCHEMA,
            MESH_QUALITY_TOPOLOGY_RULES,
            request.degenerate_epsilon,
        )
        self._mesh_quality_cache[cache_key] = classified
        self._mesh_quality_analysis = classified
        self._mesh_quality_status = classified.status
        self._mesh_quality_degenerate_epsilon = request.degenerate_epsilon
        self._mesh_quality_active_request = None
        self._refresh_mesh_quality_resources()
        return True

    def evaluate_mesh_quality_request(
        self,
        request: MeshQualityAnalysisRequest,
    ) -> MeshQualityAnalysis:
        """Pure worker entry point; committing the result remains a GUI-thread action."""

        return self._call_mesh_quality_analyzer(request)

    def cancel_mesh_quality_analysis(self) -> bool:
        """Invalidate one in-flight result without touching mesh or Project state."""

        if self._mesh_quality_active_request is None:
            return False
        self._mesh_quality_active_request = None
        self._mesh_quality_status = MeshDiagnosticsStatus.CANCELLED
        return True

    def fail_mesh_quality_analysis(
        self,
        request: MeshQualityAnalysisRequest,
    ) -> bool:
        """Commit a worker failure only when its request is still current."""

        active = self._mesh_quality_active_request
        if active is None or active.request_id != request.request_id:
            return False
        self._mesh_quality_active_request = None
        self._mesh_quality_status = MeshDiagnosticsStatus.FAILED
        return True

    def set_mesh_quality_threshold(self, threshold: float) -> bool:
        """Derive a new bad-cell subset without recomputing mesh geometry."""

        try:
            normalized = float(threshold)
            if not isfinite(normalized) or not -1.0 <= normalized <= 1.0:
                raise ValueError
            if self._mesh_quality_analysis is not None:
                self._mesh_quality_analysis = reclassify_mesh_quality(
                    self._mesh_quality_analysis,
                    threshold=normalized,
                )
        except (TypeError, ValueError):
            return False
        self._mesh_quality_threshold = normalized
        if self._mesh_quality_analysis is not None:
            self._mesh_quality_status = self._mesh_quality_analysis.status
            if (
                not self.mesh_quality_view_model.bad_cell_keys
                and self._mesh_quality_filter_mode != "clear"
            ):
                self.set_mesh_quality_filter_mode("clear")
            return self._refresh_mesh_quality_resources()
        return True

    def set_mesh_quality_range(
        self,
        mode: str,
        manual_range: tuple[float, float] | None = None,
    ) -> bool:
        """Update only color projection bounds from cached quality values."""

        analysis = self._mesh_quality_analysis
        if analysis is None:
            return False
        try:
            self._mesh_quality_analysis = reclassify_mesh_quality(
                analysis,
                threshold=self._mesh_quality_threshold,
                range_mode=mode,
                manual_range=manual_range,
            )
        except (TypeError, ValueError):
            return False
        self._mesh_quality_status = self._mesh_quality_analysis.status
        return self._refresh_mesh_quality_resources()

    def set_mesh_quality_coloring_visible(self, visible: bool) -> bool:
        """Enable one Scaled Jacobian cell-color layer and one scalar bar."""

        if not visible:
            if self._mesh_quality_filter_mode != "clear":
                self.set_mesh_quality_filter_mode("clear")
            self._mesh_quality_coloring_visible = False
            self._remove_mesh_quality_actor(MESH_QUALITY_ACTOR_KEY)
            self._remove_mesh_quality_actor(MESH_QUALITY_SCALARBAR_ACTOR_KEY)
            restored = self._restore_mesh_quality_layer_visibility()
            if self._quality_primary_scalar_snapshot is not None:
                restored = (
                    self._set_visibility_map(self._quality_primary_scalar_snapshot) and restored
                )
                self._quality_primary_scalar_snapshot = None
                self._primary_scalar_owner = (
                    "result" if self._interactive_result_state.contour_visible else ""
                )
            return restored
        if (
            self._mesh_quality_analysis is None
            or not self._mesh_quality_renderer_available()
            or self._isolation_snapshot is not None
            or self._mesh_quality_status
            not in {MeshDiagnosticsStatus.READY, MeshDiagnosticsStatus.PARTIAL_COVERAGE}
        ):
            return False
        if (
            self._interactive_result_state.contour_visible
            and RESULT_SCALAR_ACTOR_KEY in self._actor_records
        ):
            self._quality_primary_scalar_snapshot = {
                semantic_id: self._actor_records[semantic_id].visible
                for semantic_id in (
                    RESULT_SCALAR_ACTOR_KEY,
                    RESULT_COLORBAR_ACTOR_KEY,
                )
                if semantic_id in self._actor_records
            }
            self._primary_scalar_owner = "diagnostics"
        self._mesh_quality_coloring_visible = True
        return self._refresh_mesh_quality_resources()

    def set_mesh_quality_highlight_visible(self, visible: bool) -> bool:
        """Show or remove the canonical bad-element highlight actor."""

        if not visible:
            if self._mesh_quality_filter_mode != "clear":
                self.set_mesh_quality_filter_mode("clear")
            self._mesh_quality_highlight_visible = False
            self._remove_mesh_quality_actor(MESH_BAD_ELEMENTS_ACTOR_KEY)
            return True
        if (
            self._mesh_quality_analysis is None
            or not self.mesh_quality_view_model.bad_cell_keys
            or not self._mesh_quality_renderer_available()
            or self._isolation_snapshot is not None
        ):
            return False
        self._mesh_quality_highlight_visible = True
        return self._refresh_mesh_quality_resources()

    def set_mesh_quality_filter_mode(self, mode: str) -> bool:
        """Apply highlight/hide/isolate/clear without mutating mesh connectivity."""

        normalized = str(mode or "clear").strip().lower()
        if normalized == "highlight":
            if not self.set_mesh_quality_filter_mode("clear"):
                return False
            return self.set_mesh_quality_highlight_visible(True)
        if normalized not in {"clear", "hide_bad", "isolate_bad"}:
            return False
        if normalized == "clear":
            restored = self._restore_mesh_quality_filter_visibility()
            self._mesh_quality_filter_mode = "clear"
            self._remove_mesh_quality_actor(MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY)
            return restored
        if (
            self._isolation_snapshot is not None
            or self._mesh_quality_analysis is None
            or not self.mesh_quality_view_model.bad_cell_keys
            or not self._mesh_quality_renderer_available()
        ):
            return False
        if self._mesh_quality_visibility_snapshot is None:
            self._mesh_quality_visibility_snapshot = {
                semantic_id: self._actor_records[semantic_id].visible
                for semantic_id in (
                    "base_mesh",
                    "wireframe",
                    MESH_QUALITY_ACTOR_KEY,
                    MESH_BAD_ELEMENTS_ACTOR_KEY,
                    RESULT_SCALAR_ACTOR_KEY,
                )
                if semantic_id in self._actor_records
            }
        self._mesh_quality_highlight_visible = True
        self._mesh_quality_filter_mode = normalized
        if not self._refresh_mesh_quality_resources():
            return False
        if normalized == "hide_bad":
            visibility = {
                "base_mesh": False,
                "wireframe": False,
                MESH_QUALITY_ACTOR_KEY: False,
                MESH_BAD_ELEMENTS_ACTOR_KEY: False,
                RESULT_SCALAR_ACTOR_KEY: False,
                MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY: True,
            }
        else:
            self._remove_mesh_quality_actor(MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY)
            visibility = {
                "base_mesh": False,
                "wireframe": False,
                MESH_QUALITY_ACTOR_KEY: False,
                MESH_BAD_ELEMENTS_ACTOR_KEY: True,
                RESULT_SCALAR_ACTOR_KEY: False,
            }
        return self._set_mesh_quality_visibility(visibility)

    def set_mesh_quality_isolated(self, isolated: bool) -> bool:
        """Compatibility wrapper for the diagnostic isolate-bad filter."""

        return self.set_mesh_quality_filter_mode("isolate_bad" if isolated else "clear")

    def restore_mesh_quality_visibility(self) -> bool:
        """Compatibility wrapper for clearing diagnostic hide/isolate state."""

        return self.set_mesh_quality_filter_mode("clear")

    def select_mesh_quality_bad_cells(self) -> bool:
        """Promote the bad subset into the canonical transient cell selection."""

        view_model = self.mesh_quality_view_model
        analysis = self._mesh_quality_analysis
        fingerprint = self._mesh_fingerprint
        if (
            analysis is None
            or fingerprint is None
            or analysis.status
            not in {MeshDiagnosticsStatus.READY, MeshDiagnosticsStatus.PARTIAL_COVERAGE}
            or analysis.mesh_fingerprint.digest != fingerprint.digest
            or not view_model.bad_cell_keys
            or self._mesh is None
        ):
            return False
        self._apply_current_selection_ids(EntityKind.CELL, view_model.bad_cell_keys)
        self._sync_active_named_selection_from_current()
        self._notify_selection_listener()
        return self._current_selection_resolution.state is ResolutionState.RESOLVED

    def clear_mesh_quality_overlay(self) -> bool:
        """Clear transient emphasis while retaining same-fingerprint analysis."""

        restored = self.set_mesh_quality_filter_mode("clear")
        self._mesh_quality_coloring_visible = False
        self._mesh_quality_highlight_visible = False
        self._remove_mesh_quality_actor()
        return self._restore_mesh_quality_layer_visibility() and restored

    def set_view_state(self, scene_state: SceneViewState) -> None:
        self._scene_view_state = scene_state
        self._representation = _representation_from_scene_state(scene_state)
        self._axes_visible = scene_state.render_options.show_axes
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
        applied = self._call_session("axes", "set_axes_visible", bool(visible))
        if applied:
            self._axes_visible = bool(visible)
        return applied

    def set_representation(self, mode: str) -> bool:
        if mode not in _REPRESENTATION_VISIBILITY:
            return False
        if self._isolation_snapshot is not None and not self.clear_isolation():
            return False
        if not self._call_session("representation", "set_representation", mode):
            return False
        self._representation = mode
        self._set_registry_representation(mode)
        if self._mesh_quality_visibility_snapshot is not None:
            self._mesh_quality_visibility_snapshot.update(
                {key: bool(value) for key, value in _REPRESENTATION_VISIBILITY[mode].items()}
            )
            for semantic_id in _REPRESENTATION_VISIBILITY[mode]:
                if semantic_id in self._actor_records:
                    self.set_actor_visible(semantic_id, False)
        if (
            self._mesh_quality_layer_snapshot is not None
            and not self._mesh_quality_layer_snapshot.get(RESULT_SCALAR_ACTOR_KEY, False)
        ):
            self._mesh_quality_layer_snapshot.update(
                {key: bool(value) for key, value in _REPRESENTATION_VISIBILITY[mode].items()}
            )
            for semantic_id in _REPRESENTATION_VISIBILITY[mode]:
                if semantic_id in self._actor_records:
                    self.set_actor_visible(semantic_id, False)
        if self._interactive_result_visibility_snapshot is not None:
            self._interactive_result_visibility_snapshot = {
                key: bool(value) for key, value in _REPRESENTATION_VISIBILITY[mode].items()
            }
            for semantic_id in self._interactive_result_visibility_snapshot:
                if semantic_id in self._actor_records:
                    self.set_actor_visible(semantic_id, False)
        return True

    def set_actor_visible(
        self,
        semantic_id: str,
        visible: bool,
        *,
        preserve_transient: bool = False,
    ) -> bool:
        if semantic_id not in self._actor_records:
            return False
        record = self._actor_records[semantic_id]
        if record.category == "selection":
            return False
        if (
            record.isolation_eligible
            and self._isolation_snapshot is not None
            and not self.clear_isolation()
        ):
            return False
        if not self._call_session(
            "semantic-visibility",
            "set_actor_visible",
            semantic_id,
            bool(visible),
        ):
            return False
        self._actor_records[semantic_id] = replace(
            record,
            visible=bool(visible),
        )
        if not visible and record.isolation_eligible and not preserve_transient:
            self._clear_transient_state(call_session=True)
        return True

    def show_actor(self, semantic_id: str) -> bool:
        return self.set_actor_visible(semantic_id, True)

    def hide_actor(self, semantic_id: str) -> bool:
        return self.set_actor_visible(semantic_id, False)

    def isolate_actor(self, semantic_id: str) -> bool:
        if self._mesh_quality_filter_mode != "clear":
            return False
        record = self._actor_records.get(semantic_id)
        if record is None or not record.isolation_eligible:
            return False
        snapshot = self._isolation_snapshot or {
            key: item.visible
            for key, item in self._actor_records.items()
            if item.isolation_eligible
        }
        if not self._call_session(
            "semantic-visibility",
            "isolate_actor",
            semantic_id,
        ):
            return False
        if self._isolation_snapshot is None:
            self._isolation_snapshot = snapshot
        self._set_registry_visibility(
            {
                key: key == semantic_id
                for key, item in self._actor_records.items()
                if item.isolation_eligible
            }
        )
        self._clear_transient_state(call_session=True)
        return True

    def clear_isolation(self) -> bool:
        snapshot = self._isolation_snapshot
        if snapshot is None:
            return True
        if not self._call_session(
            "semantic-visibility",
            "clear_isolation",
        ):
            return False
        self._set_registry_visibility(snapshot)
        self._isolation_snapshot = None
        return True

    def show_all_actors(self) -> bool:
        if not self._call_session("semantic-visibility", "show_all_actors"):
            return False
        self._set_registry_visibility(
            {key: True for key, item in self._actor_records.items() if item.isolation_eligible}
        )
        self._isolation_snapshot = None
        if {"base_mesh", "wireframe"}.issubset(self._actor_records):
            self._representation = "surface_with_edges"
        return True

    def enable_clipping(self, axis: str, origin: float) -> bool:
        normalized = axis.lower()
        if normalized not in {"x", "y", "z"}:
            return False
        applied = self._call_session(
            "clipping",
            "enable_clipping",
            normalized,
            float(origin),
        )
        if applied:
            self._clipping_state = _clipping_from_axis(normalized, float(origin))
        return applied

    def update_clipping(self, axis: str, origin: float) -> bool:
        normalized = axis.lower()
        if normalized not in {"x", "y", "z"}:
            return False
        applied = self._call_session(
            "clipping",
            "update_clipping",
            normalized,
            float(origin),
        )
        if applied:
            self._clipping_state = _clipping_from_axis(normalized, float(origin))
        return applied

    def clear_clipping(self) -> bool:
        applied = self._call_session("clipping", "clear_clipping")
        if applied:
            self._clipping_state = ActiveSceneClippingState()
        return applied

    def snapshot_active_scene_state(self) -> ActiveSceneState | None:
        """Snapshot only durable declarative state for the active in-memory mesh."""

        fingerprint = self._mesh_fingerprint
        if self._mesh is None or fingerprint is None or not self._mesh_ref:
            return None
        actor_visibility = tuple(
            item
            for semantic_id, record in sorted(self._actor_records.items())
            if (
                item := _semantic_visibility_entry(
                    semantic_id,
                    record.visible,
                    mesh_ref=self._mesh_ref,
                )
            )
            is not None
        )
        return ActiveSceneState(
            schema=ACTIVE_SCENE_SCHEMA,
            mesh_ref=self._mesh_ref,
            mesh_fingerprint=fingerprint.digest,
            camera=self._snapshot_camera_state(),
            representation=self._representation,
            axes_visible=self._axes_visible,
            actor_visibility=actor_visibility,
            visible_named_selection_ids=tuple(sorted(self._named_overlay_ids)),
            active_named_selection_ids=self._active_named_selection_ids,
            result_state=self._snapshot_result_state(),
            mesh_quality_state=self._snapshot_mesh_quality_state(),
            clipping_state=self._clipping_state,
            isolated_actor_id=self._snapshot_isolated_actor_id(),
            selection_mode=self._pick_mode.value,
        )

    def set_pending_active_scene_state(
        self,
        state: ActiveSceneState | Mapping[str, object] | None,
    ) -> ActiveSceneRestoreResult:
        """Bind saved metadata without loading a mesh, result, or renderer."""

        if state is None:
            self._pending_active_scene_state = None
            self._active_scene_restore_result = ActiveSceneRestoreResult(
                ActiveSceneRestoreStatus.PENDING,
                (),
                ("No saved workspace state.",),
            )
            return self._active_scene_restore_result
        try:
            pending = (
                state if isinstance(state, ActiveSceneState) else ActiveSceneState.from_dict(state)
            )
        except (TypeError, ValueError):
            self._pending_active_scene_state = None
            self._active_scene_restore_result = ActiveSceneRestoreResult(
                ActiveSceneRestoreStatus.INVALID,
                ("ACTIVE_SCENE_MALFORMED",),
                ("Saved active-scene metadata is invalid.",),
            )
            return self._active_scene_restore_result
        self._pending_active_scene_state = pending
        self._active_scene_restore_result = ActiveSceneRestoreResult(
            ActiveSceneRestoreStatus.PENDING,
            ("ACTIVE_MESH_NOT_LOADED",),
            ("Saved workspace state is pending an explicit mesh reload.",),
        )
        if self._mesh is not None:
            return self.restore_pending_active_scene_state()
        return self._active_scene_restore_result

    def clear_saved_active_scene_state(self) -> None:
        """Clear controller-owned pending metadata without touching report assets."""

        self._pending_active_scene_state = None
        self._active_scene_restore_result = ActiveSceneRestoreResult(
            ActiveSceneRestoreStatus.PENDING,
            (),
            ("No saved workspace state.",),
        )

    def restore_pending_active_scene_state(self) -> ActiveSceneRestoreResult:
        """Restore compatible components in deterministic fail-closed order."""

        state = self._pending_active_scene_state
        fingerprint = self._mesh_fingerprint
        if state is None:
            return self._active_scene_restore_result
        if self._mesh is None or fingerprint is None:
            self._active_scene_restore_result = ActiveSceneRestoreResult(
                ActiveSceneRestoreStatus.PENDING,
                ("ACTIVE_MESH_NOT_LOADED",),
                ("Saved workspace state is pending an explicit mesh reload.",),
            )
            return self._active_scene_restore_result
        if state.mesh_ref != self._mesh_ref:
            return self._set_stale_restore(
                "MESH_REF_MISMATCH",
                "Saved workspace mesh reference does not match the active mesh.",
            )
        if state.mesh_fingerprint != fingerprint.digest:
            return self._set_stale_restore(
                "MESH_FINGERPRINT_MISMATCH",
                "Saved workspace mesh fingerprint does not match the active mesh.",
            )

        reasons: list[str] = []
        diagnostics: list[str] = []
        session = self._session
        renderer_available = session is not None and self._state not in {
            SceneLifecycleState.FALLBACK,
            SceneLifecycleState.CLOSED,
        }

        if renderer_available:
            if not self.set_representation(state.representation):
                reasons.append("REPRESENTATION_UNSUPPORTED")
                diagnostics.append("Saved representation is unavailable.")
            if not self.set_axes_visible(state.axes_visible):
                reasons.append("RENDERER_UNAVAILABLE")
                diagnostics.append("Saved axes visibility could not be applied.")
            apply_camera = getattr(session, "apply_camera_state", None)
            if callable(apply_camera):
                try:
                    apply_camera(state.camera)
                except Exception:
                    reasons.append("CAMERA_INVALID")
                    diagnostics.append("Saved camera could not be applied.")
            else:
                reasons.append("RENDERER_UNAVAILABLE")
                diagnostics.append("The renderer cannot apply a saved camera.")
        else:
            reasons.append("RENDERER_UNAVAILABLE")
            diagnostics.append(self._fallback_reason or "The renderer backend is unavailable.")

        self._restore_named_selection_state(state, reasons, diagnostics)
        self._restore_setup_visibility(state, reasons, diagnostics)
        self._restore_mesh_quality_state(state, reasons, diagnostics)
        self._restore_result_state(state, reasons, diagnostics)
        self._restore_actor_visibility(state, reasons, diagnostics)
        self._restore_isolation_state(state, reasons, diagnostics)
        self._restore_clipping_state(state, reasons, diagnostics)
        if state.selection_mode in {"node", "point", "cell"}:
            self._pick_mode = SelectionMode.coerce(
                "node" if state.selection_mode == "point" else state.selection_mode
            )
        self._active_named_selection_ids = tuple(
            selection_id
            for selection_id in state.active_named_selection_ids
            if any(item.id == selection_id for item in self._named_selections)
        )
        self._resolve_and_display_active_named_selections()
        if renderer_available:
            try:
                session.request_render()
            except Exception:
                reasons.append("RENDERER_UNAVAILABLE")
                diagnostics.append("The restored scene could not be rendered.")

        unique_reasons = tuple(dict.fromkeys(reasons))
        status = (
            ActiveSceneRestoreStatus.PARTIAL
            if unique_reasons
            else ActiveSceneRestoreStatus.RESTORED
        )
        self._active_scene_restore_result = ActiveSceneRestoreResult(
            status,
            unique_reasons,
            tuple(dict.fromkeys(diagnostics)),
        )
        return self._active_scene_restore_result

    def capture_active_scene_screenshot(
        self,
        request: ActiveSceneScreenshotRequest,
    ) -> ActiveSceneScreenshotResult:
        """Explicitly capture the current session and attach byte-level provenance."""

        state = self.snapshot_active_scene_state()
        if state is None or self._mesh is None:
            return ActiveSceneScreenshotResult(
                status="BLOCKED",
                diagnostics=("Load an active in-memory mesh before capture.",),
            )
        session = self._ensure_session()
        exporter = None if session is None else getattr(session, "export_screenshot_record", None)
        if not callable(exporter):
            return ActiveSceneScreenshotResult(
                status="BLOCKED",
                backend_kind=self.backend_kind,
                diagnostics=(
                    self._fallback_reason
                    or "The active renderer does not support screenshot capture.",
                ),
            )
        scene_state = _scene_view_state_from_active_scene(
            state,
            self._scene_view_state,
            requested_size=request.requested_size,
        )
        try:
            record = exporter(
                request.output_path,
                record_id=request.record_id,
                scene_state=scene_state,
                mesh=self._mesh,
                mesh_ref=self._mesh_ref,
                selection_ids=state.active_named_selection_ids,
                caption=request.caption or None,
                created_by="active-scene",
            )
            target = Path(request.output_path)
            if not target.is_file() or str(getattr(record, "path", "")) != str(target):
                raise RuntimeError("Expected screenshot file was not written.")
            image_bytes = target.read_bytes()
        except PyVistaUnavailableError:
            return ActiveSceneScreenshotResult(
                status="BLOCKED",
                backend_kind=self.backend_kind,
                diagnostics=("PyVista unavailable for active scene capture.",),
            )
        except Exception:
            return ActiveSceneScreenshotResult(
                status="FAILED",
                backend_kind=self.backend_kind,
                diagnostics=("The active scene screenshot could not be captured.",),
            )
        image_sha256 = hashlib.sha256(image_bytes).hexdigest()
        image_size = _image_dimensions(image_bytes)
        provenance = active_scene_provenance(
            state,
            image_sha256=image_sha256,
            image_byte_length=len(image_bytes),
            image_size=image_size,
            capture_backend_kind=self.backend_kind,
        )
        metadata = {
            **dict(getattr(record, "metadata", {}) or {}),
            **request.metadata,
            ACTIVE_SCENE_STATE_METADATA_KEY: state.to_dict(),
            ACTIVE_SCENE_PROVENANCE_METADATA_KEY: provenance,
        }
        replacement_values: dict[str, object] = {
            "caption": request.caption or getattr(record, "caption", None),
            "scene_state": scene_state,
            "metadata": metadata,
        }
        if request.path_kind is not None:
            replacement_values["path_kind"] = request.path_kind
        record = replace(record, **replacement_values)
        return ActiveSceneScreenshotResult(
            status="CAPTURED",
            record=record,
            active_scene_digest=provenance["active_scene_digest"],
            image_sha256=image_sha256,
            image_byte_length=len(image_bytes),
            image_size=image_size,
            backend_kind=self.backend_kind,
        )

    def restore_captured_active_scene(
        self,
        source: ActiveSceneState | Mapping[str, object] | object,
    ) -> ActiveSceneRestoreResult:
        """Restore a stored capture's logical scene when the exact mesh is still valid."""

        try:
            state = captured_active_scene_state(source)
        except (TypeError, ValueError):
            state = None
        if state is None:
            self._active_scene_restore_result = ActiveSceneRestoreResult(
                ActiveSceneRestoreStatus.INVALID,
                ("CAPTURE_SCENE_STATE_MISSING",),
                ("The selected scene capture does not contain restorable workspace state.",),
            )
            return self._active_scene_restore_result
        return self.set_pending_active_scene_state(state)

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
            if self._generation != generation or self._state is SceneLifecycleState.CLOSED:
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
        self._reset_interactive_result_state(discard_binding=True)
        self._generation += 1
        self._mesh = None
        self._mesh_ref = ""
        self._mesh_fingerprint = None
        self._scene_view_state = SceneViewState()
        self._representation = "surface"
        self._isolation_snapshot = None
        self._clipping_state = ActiveSceneClippingState()
        self._clear_transient_state(call_session=False)
        self._named_selection_resolutions = {
            selection.id: resolve_named_selection(selection) for selection in self._named_selections
        }
        self._named_overlay_ids.clear()
        self._active_named_overlay_ids.clear()
        self._setup_overlay_ids.clear()
        self._setup_overlay_categories.clear()
        self._setup_statuses = {}
        self._active_setup_id = ""
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
        self._reset_interactive_result_state(discard_binding=True)
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
        self._scene_view_state = SceneViewState()
        self._representation = "surface"
        self._axes_visible = False
        self._isolation_snapshot = None
        self._clipping_state = ActiveSceneClippingState()
        self._active_named_selection_ids = ()
        self._pending_active_scene_state = None
        self._active_scene_restore_result = ActiveSceneRestoreResult(
            ActiveSceneRestoreStatus.PENDING,
            (),
            ("No saved workspace state.",),
        )
        self._clear_transient_state(call_session=False)
        self._named_overlay_ids.clear()
        self._active_named_overlay_ids.clear()
        self._setup_overlay_ids.clear()
        self._setup_overlay_categories.clear()
        self._setup_statuses = {}

        self._active_setup_id = ""
        self._setup_record_visibility.clear()

    def _snapshot_camera_state(self) -> ActiveSceneCameraState:
        session = self._session
        getter = None if session is None else getattr(session, "get_camera_state", None)
        if callable(getter):
            try:
                value = getter()
                if isinstance(value, ActiveSceneCameraState):
                    return value
                if isinstance(value, Mapping):
                    return ActiveSceneCameraState.from_dict(value)
                return ActiveSceneCameraState(
                    position=getattr(value, "position", None),
                    focal_point=getattr(value, "focal_point", None),
                    view_up=getattr(value, "view_up", None),
                    parallel_projection=bool(getattr(value, "parallel_projection", False)),
                    parallel_scale=getattr(value, "parallel_scale", None),
                    view_preset=str(getattr(value, "view_preset", "") or ""),
                )
            except (TypeError, ValueError):
                pass
        camera = self._scene_view_state.camera
        return ActiveSceneCameraState(
            position=camera.position,
            focal_point=camera.focal_point,
            view_up=camera.view_up,
            parallel_projection=camera.parallel_projection,
            parallel_scale=camera.parallel_scale,
            view_preset=str(camera.view_preset or ""),
        )

    def _snapshot_result_state(self) -> ActiveSceneResultState | None:
        binding = self._interactive_result_binding
        scalar = self._interactive_scalar_result
        vector = self._interactive_vector_result
        session = self._interactive_result_state
        if (
            binding is None
            and scalar is None
            and vector is None
            and not session.active_result_id
            and not session.vector_field_id
            and not session.deformation_field_id
        ):
            return None
        range_mode = (
            str(getattr(scalar, "range_mode", session.range_mode or "AUTO")).split(".")[-1]
            if scalar is not None
            else str(session.range_mode or "AUTO")
        )
        display_range = getattr(scalar, "display_range", None) if range_mode == "MANUAL" else None
        if display_range is None and range_mode == "MANUAL":
            display_range = session.manual_range
        return ActiveSceneResultState(
            result_ref_id=self._interactive_result_ref_id,
            result_dataset_id=str(
                getattr(binding, "result_dataset_id", "")
                or getattr(self._interactive_result_dataset, "dataset_id", "")
                or session.active_result_id
            ),
            binding_schema=str(getattr(binding, "schema", "") or ""),
            mesh_fingerprint=str(
                getattr(binding, "mesh_fingerprint", "")
                or (self._mesh_fingerprint.digest if self._mesh_fingerprint is not None else "")
            ),
            scalar_field=str(getattr(scalar, "field_name", "") or session.active_field_id or ""),
            scalar_component=str(getattr(scalar, "component", "") or ""),
            scalar_association=str(getattr(scalar, "association", "") or ""),
            range_mode=range_mode,
            manual_min=display_range[0] if display_range is not None else None,
            manual_max=display_range[1] if display_range is not None else None,
            colormap=str(getattr(scalar, "colormap", session.colormap) or "viridis"),
            colorbar_visible=bool(getattr(scalar, "colorbar_visible", session.colorbar_visible)),
            vector_field=str(getattr(vector, "field_name", "") or session.vector_field_id or ""),
            vector_components=tuple(getattr(vector, "selected_components", ()) or ()),
            vector_association=str(getattr(vector, "association", "") or ""),
            vector_visible=bool(
                self._interactive_result_state.vector_visible
                or (
                    vector is not None
                    and vector.applied
                    and RESULT_VECTOR_ACTOR_KEY in self._actor_records
                )
            ),
            glyph_scale=float(
                self._interactive_result_state.vector_manual_scale
                or getattr(vector, "scale", 1.0)
                or 1.0
            ),
            glyph_max_count=max(
                1,
                int(self._interactive_result_state.vector_max_glyph_count or 500),
            ),
            vector_scale_mode=str(
                self._interactive_result_state.vector_scale_mode or "AUTO"
            ),
            deformation_field=str(self._interactive_result_state.deformation_field_id or ""),
            deformation_mode=str(self._interactive_result_state.deformation_mode or "ORIGINAL"),
            deformation_scale_mode=str(
                self._interactive_result_state.deformation_scale_mode or "AUTO"
            ),
            deformation_manual_scale=float(
                self._interactive_result_state.deformation_manual_scale or 1.0
            ),
        )

    def _snapshot_isolated_actor_id(self) -> str:
        if self._isolation_snapshot is None:
            return ""
        isolated = [
            semantic_id
            for semantic_id, record in self._actor_records.items()
            if record.isolation_eligible and record.visible
        ]
        return isolated[0] if len(isolated) == 1 else ""

    def _snapshot_mesh_quality_state(self) -> MeshQualityViewState | None:
        if self._mesh_quality_analysis is None and not self._mesh_quality_highlight_visible:
            return None
        return MeshQualityViewState(
            metric_schema=MESH_QUALITY_METRIC_SCHEMA,
            threshold=self._mesh_quality_threshold,
            highlight_visible=self._mesh_quality_highlight_visible,
            coloring_visible=self._mesh_quality_coloring_visible,
            filter_mode=self._mesh_quality_filter_mode,
            range_mode=(
                self._mesh_quality_analysis.range_mode
                if self._mesh_quality_analysis is not None
                else "auto"
            ),
            manual_min=(
                self._mesh_quality_analysis.display_range[0]
                if self._mesh_quality_analysis is not None
                and self._mesh_quality_analysis.range_mode == "manual"
                else None
            ),
            manual_max=(
                self._mesh_quality_analysis.display_range[1]
                if self._mesh_quality_analysis is not None
                and self._mesh_quality_analysis.range_mode == "manual"
                else None
            ),
        )

    def _set_stale_restore(
        self,
        reason_code: str,
        diagnostic: str,
    ) -> ActiveSceneRestoreResult:
        self._active_scene_restore_result = ActiveSceneRestoreResult(
            ActiveSceneRestoreStatus.STALE,
            (reason_code,),
            (diagnostic,),
        )
        return self._active_scene_restore_result

    def _restore_named_selection_state(
        self,
        state: ActiveSceneState,
        reasons: list[str],
        diagnostics: list[str],
    ) -> None:
        requested = set(state.visible_named_selection_ids)
        known = {selection.id for selection in self._named_selections}
        for selection_id in sorted(requested - known):
            reasons.append("NAMED_SELECTION_NOT_FOUND")
            diagnostics.append(f"Saved NamedSelection '{selection_id}' is not present.")
        session = self._session
        for selection_id in tuple(self._named_overlay_ids):
            if selection_id in requested:
                continue
            remover = (
                None
                if session is None
                else getattr(session, "remove_named_selection_overlay", None)
            )
            if callable(remover):
                try:
                    remover(selection_id)
                except Exception:
                    reasons.append("RENDERER_UNAVAILABLE")
                    diagnostics.append(
                        f"NamedSelection '{selection_id}' visibility was not applied."
                    )
            self._named_overlay_ids.discard(selection_id)
        for selection_id in sorted(requested & known):
            resolution = self._named_selection_resolutions.get(selection_id)
            if resolution is None or resolution.state is not ResolutionState.RESOLVED:
                reasons.append("NAMED_SELECTION_NOT_RESOLVED")
                diagnostics.append(f"NamedSelection '{selection_id}' is not exactly resolved.")

    def _restore_setup_visibility(
        self,
        state: ActiveSceneState,
        reasons: list[str],
        diagnostics: list[str],
    ) -> None:
        for item in state.actor_visibility:
            semantic_id = _semantic_id_from_visibility(item)
            if not semantic_id.startswith(("setup:", "setup_target:", "setup_glyph:")):
                continue
            status = self._setup_statuses.get(item.source_id)
            if status is None or str(getattr(status, "state", "")) != "READY":
                reasons.append("SETUP_RECORD_NOT_READY")
                diagnostics.append(f"Setup record '{item.source_id}' is not READY.")

    def _restore_mesh_quality_state(
        self,
        state: ActiveSceneState,
        reasons: list[str],
        diagnostics: list[str],
    ) -> None:
        quality = state.mesh_quality_state
        if quality is None:
            return
        analysis = self.analyze_mesh_quality()
        if analysis is None:
            reasons.append("MESH_QUALITY_RECOMPUTE_UNAVAILABLE")
            diagnostics.append("Mesh Diagnostics could not be recomputed.")
            return
        self.set_mesh_quality_threshold(quality.threshold)
        if quality.range_mode == "manual" and self._mesh_quality_analysis is not None:
            self._mesh_quality_analysis = reclassify_mesh_quality(
                self._mesh_quality_analysis,
                threshold=quality.threshold,
                range_mode="manual",
                manual_range=(float(quality.manual_min), float(quality.manual_max)),
            )
        if quality.coloring_visible and not self.set_mesh_quality_coloring_visible(True):
            reasons.append("RENDERER_UNAVAILABLE")
            diagnostics.append("Mesh Diagnostics quality coloring could not be restored.")
        if quality.highlight_visible and not self.set_mesh_quality_highlight_visible(True):
            reasons.append("RENDERER_UNAVAILABLE")
            diagnostics.append("Mesh Diagnostics highlight could not be restored.")
        if quality.filter_mode != "clear" and not self.set_mesh_quality_filter_mode(
            quality.filter_mode
        ):
            reasons.append("RENDERER_UNAVAILABLE")
            diagnostics.append("Mesh Diagnostics filter mode could not be restored.")

    def _restore_result_state(
        self,
        state: ActiveSceneState,
        reasons: list[str],
        diagnostics: list[str],
    ) -> None:
        result = state.result_state
        if result is None:
            return
        if self._interactive_result_dataset is None:
            reasons.append("RESULT_DATASET_NOT_AVAILABLE")
            diagnostics.append(f"Result dataset '{result.result_dataset_id}' is not loaded.")
            return
        if result.result_ref_id and result.result_ref_id != self._interactive_result_ref_id:
            reasons.append("RESULT_REF_NOT_AVAILABLE")
            diagnostics.append(f"Result reference '{result.result_ref_id}' is not available.")
            return
        resolution = self._interactive_result_resolution
        if (
            resolution is None
            or str(getattr(resolution, "state", "")).split(".")[-1] != "RESOLVED"
            or result.binding_schema != "osw.result_mesh_binding.v2"
        ):
            reasons.append("RESULT_BINDING_NOT_RESOLVED")
            diagnostics.append("The saved result binding is not exactly resolved.")
            return
        if result.deformation_field and result.deformation_mode != "ORIGINAL":
            deformation = self.set_deformed_result(
                result.deformation_field,
                mode=result.deformation_mode,
                scale_mode=result.deformation_scale_mode,
                manual_scale=result.deformation_manual_scale,
            )
            if not deformation.applied:
                reasons.append("RESULT_FIELD_NOT_AVAILABLE")
                diagnostics.append(
                    f"Result deformation field '{result.deformation_field}' is not available."
                )
        if result.scalar_field:
            scalar = self.set_scalar_result(
                result.scalar_field,
                component=result.scalar_component or None,
                range_mode=result.range_mode,
                manual_range=result.display_range,
                colormap=result.colormap,
                colorbar_visible=result.colorbar_visible,
            )
            if not scalar.applied:
                reasons.append("RESULT_FIELD_NOT_AVAILABLE")
                diagnostics.append(f"Result field '{result.scalar_field}' is not available.")
        if result.vector_visible and result.vector_field:
            vector = self.set_vector_result(
                result.vector_field,
                components=result.vector_components or None,
                maximum_glyph_count=result.glyph_max_count,
                scale=result.glyph_scale,
                scale_mode=result.vector_scale_mode,
            )
            if not vector.applied:
                reasons.append("RESULT_FIELD_NOT_AVAILABLE")
                diagnostics.append(f"Result vector field '{result.vector_field}' is not available.")

    def _restore_result_state_after_binding(self) -> None:
        state = self._pending_active_scene_state
        fingerprint = self._mesh_fingerprint
        saved = None if state is None else state.result_state
        current_dataset_id = str(
            getattr(self._interactive_result_dataset, "dataset_id", "") or ""
        )
        if (
            state is None
            or saved is None
            or self._mesh is None
            or fingerprint is None
            or self._active_scene_restore_result.status is ActiveSceneRestoreStatus.STALE
            or state.mesh_fingerprint != fingerprint.digest
            or (
                saved.result_dataset_id
                and current_dataset_id
                and saved.result_dataset_id != current_dataset_id
            )
            or (
                saved.result_ref_id
                and self._interactive_result_ref_id
                and saved.result_ref_id != self._interactive_result_ref_id
            )
        ):
            return
        reasons = [
            code
            for code in self._active_scene_restore_result.reason_codes
            if code
            not in {
                "RESULT_DATASET_NOT_AVAILABLE",
                "RESULT_REF_NOT_AVAILABLE",
                "RESULT_BINDING_NOT_RESOLVED",
                "RESULT_FIELD_NOT_AVAILABLE",
            }
        ]
        diagnostics = [
            item
            for item in self._active_scene_restore_result.diagnostics
            if "result" not in item.casefold()
        ]
        self._restore_result_state(state, reasons, diagnostics)
        unique_reasons = tuple(dict.fromkeys(reasons))
        status = (
            ActiveSceneRestoreStatus.PARTIAL
            if unique_reasons
            else ActiveSceneRestoreStatus.RESTORED
        )
        self._active_scene_restore_result = ActiveSceneRestoreResult(
            status,
            unique_reasons,
            tuple(dict.fromkeys(diagnostics)),
        )

    def _restore_isolation_state(
        self,
        state: ActiveSceneState,
        reasons: list[str],
        diagnostics: list[str],
    ) -> None:
        isolated_id = str(state.isolated_actor_id or "")
        if not isolated_id:
            return
        if not self.isolate_actor(isolated_id):
            reasons.append("ISOLATED_ACTOR_NOT_FOUND")
            diagnostics.append(f"Saved isolated actor '{isolated_id}' is unavailable.")

    def _restore_actor_visibility(
        self,
        state: ActiveSceneState,
        reasons: list[str],
        diagnostics: list[str],
    ) -> None:
        for item in state.actor_visibility:
            semantic_id = _semantic_id_from_visibility(item)
            if item.kind == "named_selection":
                continue
            if semantic_id not in self._actor_records:
                if item.kind in {
                    "mesh_quality_bad_cells",
                    "scalar_result",
                    "vector_result",
                    "deformed_result",
                    "original_reference",
                }:
                    continue
                reasons.append("ACTOR_VISIBILITY_TARGET_NOT_FOUND")
                diagnostics.append(
                    f"Saved actor target '{item.kind}:{item.source_id}' is unavailable."
                )
                continue
            if not self.set_actor_visible(semantic_id, item.visible):
                reasons.append("RENDERER_UNAVAILABLE")
                diagnostics.append(
                    f"Saved actor visibility for '{item.kind}:{item.source_id}' "
                    "could not be applied."
                )

    def _restore_clipping_state(
        self,
        state: ActiveSceneState,
        reasons: list[str],
        diagnostics: list[str],
    ) -> None:
        clipping = state.clipping_state
        if not clipping.enabled:
            self._clipping_state = clipping
            return
        axis = _axis_from_clipping(clipping)
        if axis is None:
            reasons.append("CLIPPING_INVALID")
            diagnostics.append(
                "Saved clipping normal is not supported by the current axis control."
            )
            return
        origin = clipping.origin["xyz".index(axis)]
        if not self.enable_clipping(axis, origin):
            reasons.append("RENDERER_UNAVAILABLE")
            diagnostics.append("Saved clipping state could not be applied.")

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
        self._named_overlay_ids.clear()
        self._active_named_overlay_ids.clear()
        self._mesh_quality_highlight_visible = False
        self._mesh_quality_visibility_snapshot = None
        self._interactive_result_visibility_snapshot = None
        self._isolation_snapshot = None
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
            self._state
            in {
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
            result = method(*args)
        except Exception as exc:
            self._fail_session(exc)
            return False
        return result is not False

    def _set_registry_representation(self, mode: str) -> None:
        self._set_registry_visibility(_REPRESENTATION_VISIBILITY[mode])

    def _set_registry_visibility(self, visibility: Mapping[str, bool]) -> None:
        for semantic_id, record in tuple(self._actor_records.items()):
            self._actor_records[semantic_id] = replace(
                record,
                visible=bool(visibility.get(semantic_id, record.visible)),
            )

    def _configure_session_picking(self) -> bool:
        if self._pick_mode is SelectionMode.SETUP:
            if self._mesh is None or self._mesh_fingerprint is None:
                return False
            callback = self.guard_callback(
                self.handle_setup_pick,
                stale_result=False,
            )
            return self._call_session(
                "picking",
                "set_pick_mode",
                SelectionMode.SETUP.value,
                callback,
            )
        if self._pick_mode not in {SelectionMode.NODE, SelectionMode.CELL}:
            return False
        if self._mesh is None or self._mesh_fingerprint is None:
            return False
        callback = self.guard_callback(self.handle_pick, stale_result=False)
        configured = self._call_session(
            "picking",
            "set_pick_mode",
            self._pick_mode.value,
            callback,
        )
        if configured:
            self._call_session(
                "picking",
                "set_selection_operation",
                self._selection_operation.value,
            )
        return configured

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
            NODE_ORDINAL_NAMESPACE if entity_kind is EntityKind.NODE else CELL_ORDINAL_NAMESPACE
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

    def _apply_current_selection_ids(
        self,
        entity_kind: EntityKind,
        entity_ids: Sequence[int | str],
    ) -> None:
        self._current_selection_target = self._target_for_ids(
            entity_kind,
            entity_ids,
        )
        assert self._mesh is not None
        self._current_selection_resolution = resolve_selection_target(
            self._current_selection_target,
            mesh=self._mesh,
            mesh_ref=self._mesh_ref,
        )
        highlighted = self._call_session(
            "selection-overlays",
            "set_current_selection",
            entity_kind.value,
            self._current_selection_resolution.transient_indices,
            self._generation,
        )
        if highlighted:
            self._actor_records["current_selection"] = _scene_actor_record(
                "current_selection",
                generation=self._generation,
            )

    def _sync_active_named_selection_from_current(self) -> None:
        target = self._current_selection_target
        if target is None or target.locator is None:
            return
        matches = tuple(
            selection.id
            for selection in self._named_selections
            if len(selection.targets) == 1
            and selection.targets[0].locator == target.locator
            and self._named_selection_resolutions.get(
                selection.id,
                ResolutionResult(),
            ).state
            is ResolutionState.RESOLVED
        )
        self._active_named_selection_ids = matches if len(matches) == 1 else ()
        self._resolve_and_display_active_named_selections()

    def _clear_transient_state(self, *, call_session: bool) -> None:
        self._hover_target = None
        self._current_selection_target = None
        self._actor_records.pop("hover", None)
        self._actor_records.pop("current_selection", None)
        self._current_selection_resolution = ResolutionResult(
            state=ResolutionState.UNRESOLVED,
            reason_code="CURRENT_SELECTION_EMPTY",
            message="No current entities are selected.",
        )
        if call_session:
            self._interactive_probe_result = None
            self._interactive_result_table = None
            self._interactive_result_state = replace(
                self._interactive_result_state,
                probe_mode="none",
            )
            self._call_session("selection-overlays", "clear_hover")
            self._call_session(
                "selection-overlays",
                "clear_current_selection",
            )
            self._remove_result_actor(RESULT_PROBE_ACTOR_KEY)
        else:
            self._actor_records.pop(RESULT_PROBE_ACTOR_KEY, None)

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
        self._resolve_and_display_active_named_selections()
        self._refresh_setup_overlays()

    def _resolve_and_display_active_named_selections(self) -> bool:
        session = self._session
        if session is not None and "selection-overlays" in self.capabilities:
            remover = getattr(
                session,
                "remove_active_named_selection_overlay",
                None,
            )
            for selection_id in tuple(self._active_named_overlay_ids):
                if callable(remover):
                    try:
                        remover(selection_id)
                    except Exception as exc:
                        self._fail_session(exc)
                        return False
                self._actor_records.pop(
                    f"active_named_selection:{selection_id}",
                    None,
                )
            self._active_named_overlay_ids.clear()

        if not self._active_named_selection_ids:
            return True
        if session is None or "selection-overlays" not in self.capabilities:
            return False
        method = getattr(session, "set_active_named_selection_overlay", None)
        if not callable(method):
            return False

        selections = {selection.id: selection for selection in self._named_selections}
        all_applied = True
        for selection_id in self._active_named_selection_ids:
            selection = selections.get(selection_id)
            resolution = self._named_selection_resolutions.get(selection_id)
            if (
                selection is None
                or resolution is None
                or resolution.state is not ResolutionState.RESOLVED
            ):
                all_applied = False
                continue
            try:
                method(
                    selection_id,
                    selection.entity_kind.value,
                    resolution.transient_indices,
                    self._generation,
                )
            except Exception as exc:
                self._fail_session(exc)
                return False
            semantic_id = f"active_named_selection:{selection_id}"
            self._active_named_overlay_ids.add(selection_id)
            self._actor_records[semantic_id] = _scene_actor_record(
                semantic_id,
                generation=self._generation,
            )
        return all_applied

    def _refresh_setup_overlays(self) -> None:
        if self._isolation_snapshot is not None and not self.clear_isolation():
            return
        session = self._session
        for semantic_id in tuple(self._setup_overlay_ids):
            if session is not None:
                remover = getattr(session, "remove_actor", None)
                if callable(remover):
                    remover(semantic_id)
            self._actor_records.pop(semantic_id, None)
        self._setup_overlay_ids.clear()
        self._setup_overlay_categories.clear()
        self._setup_statuses = {}
        if self._solver_setup is None:
            return
        statuses = evaluate_solver_setup(
            self._solver_setup,
            selections=self._named_selections,
            materials=self._setup_materials,
            resolutions=self._named_selection_resolutions,
            mesh=self._mesh,
            project_units=self._setup_units,
        )
        self._setup_statuses = {item.record_id: item for item in statuses}
        if session is None or self._mesh is None or "setup-overlays" not in self.capabilities:
            return
        specs = build_setup_overlay_specs(
            self._solver_setup,
            mesh=self._mesh,
            resolutions=self._named_selection_resolutions,
            statuses=self._setup_statuses,
            category_visibility=self._setup_category_visibility,
            mesh_ref=self._mesh_ref,
            selections=self._named_selections,
        )
        for spec in specs:
            previous = self._actor_records.get(spec.actor_key)
            visible = bool(spec.visible) and self._setup_record_visibility.get(
                spec.record_id,
                True,
            )
            session.replace_actor(
                spec.actor_key,
                spec,
                generation=self._generation,
            )
            self._actor_records[spec.actor_key] = _scene_actor_record(
                spec.actor_key,
                generation=self._generation,
                visible=visible if previous is None else previous.visible,
            )
            session.set_actor_visible(spec.actor_key, visible)
            self._setup_overlay_ids.add(spec.actor_key)
            self._setup_overlay_categories[spec.actor_key] = spec.category

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

    def _call_mesh_quality_analyzer(
        self,
        request: MeshQualityAnalysisRequest,
    ) -> MeshQualityAnalysis:
        analyzer = self._mesh_quality_analyzer
        kwargs: dict[str, float] = {}
        try:
            parameters = signature(analyzer).parameters
        except (TypeError, ValueError):
            parameters = {}
        accepts_kwargs = any(
            parameter.kind is Parameter.VAR_KEYWORD for parameter in parameters.values()
        )
        if accepts_kwargs or "threshold" in parameters:
            kwargs["threshold"] = request.threshold
        if accepts_kwargs or "degenerate_epsilon" in parameters:
            kwargs["degenerate_epsilon"] = request.degenerate_epsilon
        elif accepts_kwargs or "zero_edge_tolerance" in parameters:
            kwargs["zero_edge_tolerance"] = request.degenerate_epsilon
        analysis = analyzer(request.mesh, **kwargs)
        if not isinstance(analysis, MeshQualityAnalysis):
            raise TypeError("Mesh Diagnostics analyzer returned an incompatible result.")
        if analysis.mesh_fingerprint.digest != request.mesh_fingerprint:
            raise ValueError(
                "Mesh Diagnostics analysis does not match the requested mesh fingerprint."
            )
        return analysis

    def _refresh_mesh_quality_resources(self) -> bool:
        analysis = self._mesh_quality_analysis
        fingerprint = self._mesh_fingerprint
        if (
            analysis is None
            or fingerprint is None
            or analysis.mesh_fingerprint.digest != fingerprint.digest
            or analysis.status
            not in {MeshDiagnosticsStatus.READY, MeshDiagnosticsStatus.PARTIAL_COVERAGE}
        ):
            self._remove_mesh_quality_actor()
            return False
        if not self._mesh_quality_renderer_available():
            self._remove_mesh_quality_actor()
            return not (
                self._mesh_quality_coloring_visible
                or self._mesh_quality_highlight_visible
                or self._mesh_quality_filter_mode != "clear"
            )
        specs = build_mesh_diagnostics_overlay_specs(analysis)
        view_model = self.mesh_quality_view_model
        if specs.bad is not None and specs.bad.stable_cell_keys != view_model.bad_cell_keys:
            raise RuntimeError(
                "Mesh Diagnostics table and semantic actor cell identities diverged."
            )
        if self._mesh_quality_coloring_visible:
            if specs.quality is None or specs.scalar_bar is None:
                return False
            if self._mesh_quality_layer_snapshot is None:
                self._mesh_quality_layer_snapshot = {
                    semantic_id: self._actor_records[semantic_id].visible
                    for semantic_id in (
                        "base_mesh",
                        "wireframe",
                        RESULT_SCALAR_ACTOR_KEY,
                        RESULT_COLORBAR_ACTOR_KEY,
                    )
                    if semantic_id in self._actor_records
                }
            if not self._replace_mesh_quality_resource(specs.quality):
                return False
            if not self._replace_mesh_quality_resource(specs.scalar_bar):
                return False
            if not self._set_mesh_quality_visibility(
                {
                    "base_mesh": False,
                    "wireframe": False,
                    RESULT_SCALAR_ACTOR_KEY: False,
                    RESULT_COLORBAR_ACTOR_KEY: False,
                    MESH_QUALITY_ACTOR_KEY: True,
                    MESH_QUALITY_SCALARBAR_ACTOR_KEY: True,
                }
            ):
                return False
        else:
            self._remove_mesh_quality_actor(MESH_QUALITY_ACTOR_KEY)
            self._remove_mesh_quality_actor(MESH_QUALITY_SCALARBAR_ACTOR_KEY)

        needs_bad = self._mesh_quality_highlight_visible or (
            self._mesh_quality_filter_mode in {"hide_bad", "isolate_bad"}
        )
        if needs_bad and specs.bad is not None:
            if not self._replace_mesh_quality_resource(specs.bad):
                return False
        else:
            self._remove_mesh_quality_actor(MESH_BAD_ELEMENTS_ACTOR_KEY)

        if self._mesh_quality_filter_mode == "hide_bad" and specs.good is not None:
            if not self._replace_mesh_quality_resource(specs.good):
                return False
        elif self._mesh_quality_filter_mode != "hide_bad":
            self._remove_mesh_quality_actor(MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY)
        session = self._session
        if session is not None:
            try:
                session.request_render()
            except Exception as exc:
                self._fail_session(exc)
                return False
        return True

    def _replace_mesh_quality_resource(
        self,
        spec: MeshQualityOverlaySpec | MeshQualityScalarBarSpec,
    ) -> bool:
        session = self._session
        if session is None:
            return False
        semantic_id = spec.actor_key
        try:
            previous = self._actor_records.get(semantic_id)
            session.replace_actor(semantic_id, spec, generation=self._generation)
            visible = bool(getattr(spec, "visible", True))
            if previous is not None:
                visible = previous.visible
            self._actor_records[semantic_id] = _scene_actor_record(
                semantic_id,
                generation=self._generation,
                visible=visible,
            )
            setter = getattr(session, "set_actor_visible", None)
            if callable(setter):
                setter(semantic_id, visible)
        except Exception as exc:
            self._fail_session(exc)
            return False
        return True

    def _set_mesh_quality_visibility(self, visibility: Mapping[str, bool]) -> bool:
        session = self._session
        if session is None:
            return False
        setter = getattr(session, "set_actor_visible", None)
        if not callable(setter):
            return False
        try:
            for semantic_id, visible in visibility.items():
                record = self._actor_records.get(semantic_id)
                if record is None:
                    continue
                setter(semantic_id, bool(visible))
                self._actor_records[semantic_id] = replace(record, visible=bool(visible))
        except Exception as exc:
            self._fail_session(exc)
            return False
        return True

    def _restore_mesh_quality_filter_visibility(self) -> bool:
        snapshot = self._mesh_quality_visibility_snapshot
        if snapshot is None:
            return True
        restored = self._set_mesh_quality_visibility(snapshot)
        if restored:
            self._mesh_quality_visibility_snapshot = None
        return restored

    def _restore_mesh_quality_layer_visibility(self) -> bool:
        snapshot = self._mesh_quality_layer_snapshot
        if snapshot is None:
            return True
        restored = self._set_mesh_quality_visibility(snapshot)
        if restored:
            self._mesh_quality_layer_snapshot = None
        return restored

    def _remove_mesh_quality_actor(self, semantic_id: str | None = None) -> None:
        semantic_ids = (
            (semantic_id,)
            if semantic_id is not None
            else (
                MESH_QUALITY_ACTOR_KEY,
                MESH_BAD_ELEMENTS_ACTOR_KEY,
                MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY,
                MESH_QUALITY_SCALARBAR_ACTOR_KEY,
            )
        )
        session = self._session
        remover = None if session is None else getattr(session, "remove_actor", None)
        for actor_id in semantic_ids:
            self._actor_records.pop(actor_id, None)
            if not callable(remover):
                continue
            try:
                remover(actor_id)
            except Exception as exc:
                self._fail_session(exc)
                return

    def _prepare_mesh_quality_replacement(
        self,
        *,
        same_fingerprint: bool,
        previous_analysis: MeshQualityAnalysis | None,
    ) -> None:
        had_active_request = self._mesh_quality_active_request is not None
        self._mesh_quality_active_request = None
        self._remove_mesh_quality_actor()
        self._mesh_quality_layer_snapshot = None
        self._mesh_quality_visibility_snapshot = None
        if same_fingerprint:
            self._mesh_quality_cache.clear()
            self._mesh_quality_analysis = None
            self._mesh_quality_status = MeshDiagnosticsStatus.IDLE
            return
        self._mesh_quality_cache.clear()
        self._mesh_quality_coloring_visible = False
        self._mesh_quality_highlight_visible = False
        self._mesh_quality_filter_mode = "clear"
        self._mesh_quality_threshold = DEFAULT_MESH_QUALITY_THRESHOLD
        self._mesh_quality_degenerate_epsilon = DEFAULT_DEGENERATE_EPSILON
        if previous_analysis is None:
            self._mesh_quality_analysis = None
            self._mesh_quality_status = (
                MeshDiagnosticsStatus.STALE if had_active_request else MeshDiagnosticsStatus.IDLE
            )
            return
        self._mesh_quality_analysis = replace(
            previous_analysis,
            status=MeshDiagnosticsStatus.STALE,
            diagnostics=(
                *previous_analysis.diagnostics,
                "Active mesh fingerprint changed; diagnostic indices were not rebound.",
            ),
        )
        self._mesh_quality_status = MeshDiagnosticsStatus.STALE

    def _recompute_same_fingerprint_mesh_quality(
        self,
        previous_analysis: MeshQualityAnalysis | None,
    ) -> None:
        analysis = self.analyze_mesh_quality()
        if (
            analysis is not None
            and previous_analysis is not None
            and previous_analysis.range_mode == "manual"
        ):
            self.set_mesh_quality_range("manual", previous_analysis.display_range)

    def _reset_mesh_quality_state(self, *, discard_cache: bool) -> None:
        self._mesh_quality_active_request = None
        self._remove_mesh_quality_actor()
        self._mesh_quality_analysis = None
        self._mesh_quality_status = MeshDiagnosticsStatus.IDLE
        self._mesh_quality_threshold = DEFAULT_MESH_QUALITY_THRESHOLD
        self._mesh_quality_degenerate_epsilon = DEFAULT_DEGENERATE_EPSILON
        self._mesh_quality_coloring_visible = False
        self._mesh_quality_highlight_visible = False
        self._mesh_quality_filter_mode = "clear"
        self._mesh_quality_layer_snapshot = None
        self._mesh_quality_visibility_snapshot = None
        if discard_cache:
            self._mesh_quality_cache.clear()

    def _active_result_geometry_mesh(self) -> MeshData:
        deformation = self._interactive_deformation_result
        if deformation is not None and deformation.applied and deformation.mesh_data is not None:
            return deformation.mesh_data
        if self._mesh is None:
            raise RuntimeError("An active mesh is required for result projection.")
        return self._mesh

    def _capture_interactive_result_snapshot(
        self,
    ) -> _InteractiveResultReplacementSnapshot | None:
        if self._interactive_result_dataset is None:
            return None
        return _InteractiveResultReplacementSnapshot(
            state=self._interactive_result_state,
            probe=self._interactive_probe_result,
            table=self._interactive_result_table,
        )

    def _restore_interactive_result_snapshot(
        self,
        snapshot: _InteractiveResultReplacementSnapshot,
    ) -> None:
        resolution = self._interactive_result_resolution
        if resolution is None or resolution.state.value != "RESOLVED":
            return
        state = snapshot.state
        if state.deformation_field_id and state.deformation_mode != DeformationMode.ORIGINAL.value:
            self.set_deformed_result(
                state.deformation_field_id,
                mode=state.deformation_mode,
                scale_mode=state.deformation_scale_mode,
                manual_scale=state.deformation_manual_scale,
            )
        if state.active_field_id and state.contour_visible:
            self.set_scalar_result(
                state.active_field_id,
                component=state.active_scalar_mode,
                range_mode=state.range_mode,
                manual_range=state.manual_range,
                colormap=state.colormap,
                colorbar_visible=state.colorbar_visible,
            )
        if state.vector_field_id and state.vector_visible:
            self.set_vector_result(
                state.vector_field_id,
                maximum_glyph_count=state.vector_max_glyph_count,
                scale=state.vector_manual_scale,
                scale_mode=state.vector_scale_mode,
            )
        probe = snapshot.probe
        fingerprint = self._mesh_fingerprint
        dataset_id = str(getattr(self._interactive_result_dataset, "dataset_id", "") or "")
        if probe is not None and fingerprint is not None and state.probe_mode in {"point", "cell"}:
            self.probe_result(
                ResultProbeRequest(
                    dataset_id=dataset_id,
                    field_name=probe.field_name,
                    component=probe.component,
                    association=probe.association,
                    stable_entity_key=probe.stable_entity_key,
                    mesh_fingerprint=fingerprint.digest,
                )
            )
        table = snapshot.table
        if table is not None:
            self.set_selected_result_table(
                field_name=table.field_name,
                component=table.component,
                association=table.association,
                stable_entity_keys=tuple(row.stable_entity_key for row in table.rows),
                limit=table.limit,
            )

    def _set_visibility_map(self, visibility: Mapping[str, bool]) -> bool:
        restored = True
        for semantic_id, visible in visibility.items():
            if semantic_id in self._actor_records:
                restored = (
                    self.set_actor_visible(
                        semantic_id,
                        visible,
                        preserve_transient=True,
                    )
                    and restored
                )
        return restored

    def _restore_deformation_snapshot(self, *, keep_snapshot: bool) -> bool:
        snapshot = self._deformation_visibility_snapshot
        if snapshot is None:
            return True
        restored = self._set_visibility_map(snapshot)
        if (
            self._interactive_result_state.contour_visible
            and self._interactive_result_state.deformation_mode != DeformationMode.OVERLAY.value
        ):
            for semantic_id in ("base_mesh", "wireframe", RESULT_DEFORMED_ACTOR_KEY):
                if semantic_id in self._actor_records:
                    restored = (
                        self.set_actor_visible(
                            semantic_id,
                            False,
                            preserve_transient=True,
                        )
                        and restored
                    )
        if restored and not keep_snapshot:
            self._deformation_visibility_snapshot = None
        return restored

    def _refresh_result_geometry_dependents(self) -> None:
        state = self._interactive_result_state
        if state.contour_visible and state.active_field_id:
            self.set_scalar_result(
                state.active_field_id,
                component=state.active_scalar_mode,
                range_mode=state.range_mode,
                manual_range=state.manual_range,
                colormap=state.colormap,
                colorbar_visible=state.colorbar_visible,
            )
        if state.vector_visible and state.vector_field_id:
            self.set_vector_result(
                state.vector_field_id,
                maximum_glyph_count=state.vector_max_glyph_count,
                scale=state.vector_manual_scale,
                scale_mode=state.vector_scale_mode,
            )

    def _refresh_result_selection_geometry(self) -> None:
        """Recreate canonical selection overlays on the active displayed geometry."""

        self._call_session("selection-overlays", "clear_hover")
        self._hover_target = None
        self._actor_records.pop("hover", None)
        self._resolve_and_display_named_selections()
        target = self._current_selection_target
        resolution = self._current_selection_resolution
        if target is None or resolution.state is not ResolutionState.RESOLVED:
            return
        highlighted = self._call_session(
            "selection-overlays",
            "set_current_selection",
            target.kind.value,
            resolution.transient_indices,
            self._generation,
        )
        if highlighted:
            self._actor_records["current_selection"] = _scene_actor_record(
                "current_selection",
                generation=self._generation,
            )

    def _activate_result_primary_scalar(self) -> None:
        if self._mesh_quality_coloring_visible:
            if self._result_primary_scalar_snapshot is None:
                self._result_primary_scalar_snapshot = {
                    semantic_id: self._actor_records[semantic_id].visible
                    for semantic_id in (
                        MESH_QUALITY_ACTOR_KEY,
                        MESH_QUALITY_SCALARBAR_ACTOR_KEY,
                    )
                    if semantic_id in self._actor_records
                }
            self._set_visibility_map(
                {
                    MESH_QUALITY_ACTOR_KEY: False,
                    MESH_QUALITY_SCALARBAR_ACTOR_KEY: False,
                    RESULT_SCALAR_ACTOR_KEY: True,
                    RESULT_COLORBAR_ACTOR_KEY: self._interactive_result_state.colorbar_visible,
                }
            )
        self._primary_scalar_owner = "result"

    def _restore_result_primary_scalar(self) -> bool:
        if self._primary_scalar_owner != "result":
            self._result_primary_scalar_snapshot = None
            return True
        restored = True
        if self._mesh_quality_coloring_visible and self._result_primary_scalar_snapshot:
            restored = self._set_visibility_map(self._result_primary_scalar_snapshot)
        self._result_primary_scalar_snapshot = None
        self._primary_scalar_owner = "diagnostics" if self._mesh_quality_coloring_visible else ""
        return restored

    def _result_actor_metadata(self, payload: object) -> Mapping[str, object]:
        fingerprint = self._mesh_fingerprint
        return {
            "result_id": str(
                getattr(payload, "result_id", "")
                or getattr(self._interactive_result_dataset, "dataset_id", "")
                or ""
            ),
            "field_id": str(getattr(payload, "field_name", "") or ""),
            "association": str(getattr(payload, "association", "") or ""),
            "mesh_generation": self._generation,
            "mesh_fingerprint": str(
                getattr(payload, "mesh_fingerprint", "")
                or (fingerprint.digest if fingerprint is not None else "")
            ),
        }

    def _interactive_result_renderer_available(self) -> bool:
        return bool(
            self._session is not None
            and self._state
            not in {
                SceneLifecycleState.CLOSING,
                SceneLifecycleState.CLOSED,
                SceneLifecycleState.FALLBACK,
            }
            and "result-overlays" in self.capabilities
        )

    def _resolve_interactive_result_binding(self) -> None:
        self._interactive_result_resolution = resolve_result_mesh_binding(
            self._interactive_result_binding,
            active_mesh=self._mesh,
            active_mesh_ref=self._mesh_ref,
            result_dataset=self._interactive_result_dataset,
        )
        resolution = self._interactive_result_resolution
        if self._mesh is not None and self._interactive_result_dataset is not None:
            self._interactive_result_catalog = build_result_field_catalog(
                self._mesh,
                self._interactive_result_dataset,
                binding_resolution=resolution,
            )
            status = self._interactive_result_catalog.binding_status.value
        else:
            self._interactive_result_catalog = None
            status = "UNRESOLVED"
        stale_reason = resolution.reason_code if resolution.state.value != "RESOLVED" else ""
        self._interactive_result_state = replace(
            self._interactive_result_state,
            active_result_id=str(getattr(self._interactive_result_dataset, "dataset_id", "") or ""),
            binding_status=status,
            stale_reason=stale_reason,
        )

    def _replace_result_actor(self, semantic_id: str, payload: object) -> bool:
        if not self._interactive_result_renderer_available():
            return False
        if (
            self._isolation_snapshot is not None
            and semantic_id not in self._actor_records
            and not self.clear_isolation()
        ):
            return False
        session = self._session
        assert session is not None
        try:
            previous = self._actor_records.get(semantic_id)
            session.replace_actor(
                semantic_id,
                payload,
                generation=self._generation,
            )
            self._actor_records[semantic_id] = _scene_actor_record(
                semantic_id,
                generation=self._generation,
                visible=True if previous is None else previous.visible,
                metadata=self._result_actor_metadata(payload),
            )
            session.request_render()
        except Exception as exc:
            self._fail_session(exc)
            return False
        return True

    def _remove_result_actor(self, semantic_id: str) -> None:
        self._actor_records.pop(semantic_id, None)
        session = self._session
        if session is None:
            return
        remover = getattr(session, "remove_actor", None)
        if not callable(remover):
            return
        try:
            remover(semantic_id)
        except Exception as exc:
            self._fail_session(exc)

    def _reset_interactive_result_state(self, *, discard_binding: bool) -> None:
        self.clear_interactive_results()
        self._interactive_scalar_result = None
        self._interactive_vector_result = None
        self._interactive_deformation_result = None
        self._interactive_result_visibility_snapshot = None
        self._deformation_visibility_snapshot = None
        self._result_primary_scalar_snapshot = None
        self._quality_primary_scalar_snapshot = None
        self._primary_scalar_owner = ""
        if discard_binding:
            self._interactive_result_dataset = None
            self._interactive_result_binding = None
            self._interactive_result_ref_id = ""
            self._interactive_result_resolution = None
            self._interactive_result_catalog = None
            self._interactive_result_state = InteractiveResultSessionState()

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
        config = PyVistaSceneConfig(**scene_state.render_options.to_pyvista_config_dict())
        return build_scene_state(mesh, config=config, rendered=False)


def _scene_actor_record(
    semantic_id: str,
    *,
    generation: int,
    visible: bool = True,
    metadata: Mapping[str, object] | None = None,
) -> SceneActorRecord:
    selection = (
        semantic_id in {"hover", "current_selection"}
        or semantic_id.startswith("named_selection:")
        or semantic_id.startswith("active_named_selection:")
    )
    diagnostic = semantic_id in {
        MESH_QUALITY_ACTOR_KEY,
        MESH_BAD_ELEMENTS_ACTOR_KEY,
        MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY,
    }
    result = semantic_id in {
        RESULT_SCALAR_ACTOR_KEY,
        RESULT_VECTOR_ACTOR_KEY,
        RESULT_PROBE_ACTOR_KEY,
        RESULT_DEFORMED_ACTOR_KEY,
        RESULT_ORIGINAL_REFERENCE_ACTOR_KEY,
    }
    setup = semantic_id.startswith(("setup_target:", "setup_glyph:"))
    helper = selection or semantic_id in {
        RESULT_COLORBAR_ACTOR_KEY,
        RESULT_PROBE_ACTOR_KEY,
        MESH_QUALITY_SCALARBAR_ACTOR_KEY,
    }
    category = (
        "selection"
        if selection
        else "setup"
        if setup
        else "helper"
        if helper
        else "diagnostic"
        if diagnostic
        else "result"
        if result
        else "geometry"
    )
    return SceneActorRecord(
        semantic_id=semantic_id,
        generation=generation,
        visible=bool(visible),
        category=category,
        pickable=semantic_id
        in {
            "base_mesh",
            RESULT_DEFORMED_ACTOR_KEY,
            RESULT_SCALAR_ACTOR_KEY,
        },
        isolation_eligible=not helper,
        is_helper=helper,
        metadata=dict(metadata or {}),
    )


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


def _semantic_visibility_entry(
    semantic_id: str,
    visible: bool,
    *,
    mesh_ref: str,
) -> SemanticActorVisibility | None:
    if semantic_id == "base_mesh":
        return SemanticActorVisibility("base_mesh", mesh_ref, visible=visible)
    if semantic_id == "wireframe":
        return SemanticActorVisibility("wireframe", mesh_ref, visible=visible)
    if semantic_id.startswith("setup:material:"):
        return SemanticActorVisibility(
            "material_assignment",
            semantic_id.removeprefix("setup:material:"),
            visible=visible,
        )
    if semantic_id.startswith("setup:fixed-support:"):
        return SemanticActorVisibility(
            "fixed_support",
            semantic_id.removeprefix("setup:fixed-support:"),
            visible=visible,
        )
    if semantic_id.startswith("setup:force:"):
        return SemanticActorVisibility(
            "force_load",
            semantic_id.removeprefix("setup:force:"),
            visible=visible,
        )
    if semantic_id.startswith("setup_target:"):
        return SemanticActorVisibility(
            "setup_target",
            semantic_id.removeprefix("setup_target:"),
            visible=visible,
        )
    if semantic_id.startswith("setup_glyph:"):
        return SemanticActorVisibility(
            "setup_glyph",
            semantic_id.removeprefix("setup_glyph:"),
            visible=visible,
        )
    if semantic_id == MESH_BAD_ELEMENTS_ACTOR_KEY:
        return SemanticActorVisibility(
            "mesh_quality_bad_cells",
            MESH_QUALITY_METRIC_SCHEMA,
            visible=visible,
        )
    if semantic_id == RESULT_SCALAR_ACTOR_KEY:
        return SemanticActorVisibility(
            "scalar_result",
            RESULT_SCALAR_ACTOR_KEY,
            visible=visible,
        )
    if semantic_id == RESULT_VECTOR_ACTOR_KEY:
        return SemanticActorVisibility(
            "vector_result",
            RESULT_VECTOR_ACTOR_KEY,
            visible=visible,
        )
    if semantic_id == RESULT_DEFORMED_ACTOR_KEY:
        return SemanticActorVisibility(
            "deformed_result",
            RESULT_DEFORMED_ACTOR_KEY,
            visible=visible,
        )
    if semantic_id == RESULT_ORIGINAL_REFERENCE_ACTOR_KEY:
        return SemanticActorVisibility(
            "original_reference",
            RESULT_ORIGINAL_REFERENCE_ACTOR_KEY,
            visible=visible,
        )
    return None


def _semantic_id_from_visibility(item: SemanticActorVisibility) -> str:
    if item.kind == "base_mesh":
        return "base_mesh"
    if item.kind == "wireframe":
        return "wireframe"
    if item.kind == "material_assignment":
        return f"setup:material:{item.source_id}"
    if item.kind == "fixed_support":
        return f"setup:fixed-support:{item.source_id}"
    if item.kind == "force_load":
        return f"setup:force:{item.source_id}"
    if item.kind == "setup_target":
        return f"setup_target:{item.source_id}"
    if item.kind == "setup_glyph":
        return f"setup_glyph:{item.source_id}"
    if item.kind == "mesh_quality_bad_cells":
        return MESH_BAD_ELEMENTS_ACTOR_KEY
    if item.kind == "scalar_result":
        return RESULT_SCALAR_ACTOR_KEY
    if item.kind == "vector_result":
        return RESULT_VECTOR_ACTOR_KEY
    if item.kind == "deformed_result":
        return RESULT_DEFORMED_ACTOR_KEY
    if item.kind == "original_reference":
        return RESULT_ORIGINAL_REFERENCE_ACTOR_KEY
    if item.kind == "named_selection":
        return f"named_selection:{item.source_id}"
    return ""


def _clipping_from_axis(axis: str, origin: float) -> ActiveSceneClippingState:
    index = "xyz".index(axis)
    origin_values = [0.0, 0.0, 0.0]
    normal_values = [0.0, 0.0, 0.0]
    origin_values[index] = float(origin)
    normal_values[index] = 1.0
    return ActiveSceneClippingState(
        enabled=True,
        origin=tuple(origin_values),
        normal=tuple(normal_values),
    )


def _axis_from_clipping(clipping: ActiveSceneClippingState) -> str | None:
    normals = {
        (1.0, 0.0, 0.0): "x",
        (0.0, 1.0, 0.0): "y",
        (0.0, 0.0, 1.0): "z",
    }
    return normals.get(clipping.normal)


def _scene_view_state_from_active_scene(
    state: ActiveSceneState,
    fallback: SceneViewState,
    *,
    requested_size: tuple[int, int] | None,
) -> SceneViewState:
    show_surface = state.representation in {"surface", "surface_with_edges"}
    show_edges = state.representation in {"wireframe", "surface_with_edges"}
    camera = SceneCameraState(
        position=state.camera.position,
        focal_point=state.camera.focal_point,
        view_up=state.camera.view_up,
        parallel_projection=state.camera.parallel_projection,
        parallel_scale=state.camera.parallel_scale,
        view_preset=state.camera.view_preset or None,
    )
    options = SceneRenderOptions(
        show_surface=show_surface,
        show_edges=show_edges,
        show_axes=state.axes_visible,
        show_grid=fallback.render_options.show_grid,
        show_bounds=fallback.render_options.show_bounds,
        background=fallback.render_options.background,
        color_by=fallback.render_options.color_by,
        scalar_bar=fallback.render_options.scalar_bar,
        screenshot_size=requested_size or fallback.render_options.screenshot_size,
        metadata=fallback.render_options.metadata,
    )
    return replace(
        fallback,
        camera=camera,
        render_options=options,
        selected_selection_ids=state.active_named_selection_ids,
    )


def _image_dimensions(image_bytes: bytes) -> tuple[int, int] | None:
    if (
        len(image_bytes) >= 24
        and image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        and image_bytes[12:16] == b"IHDR"
    ):
        width, height = struct.unpack(">II", image_bytes[16:24])
        if width > 0 and height > 0:
            return width, height
    return None


def _result_stable_key_index(
    mesh: MeshData,
    association: str,
    stable_key: int | str,
) -> int | None:
    normalized = str(association).strip().lower()
    if normalized in {"point", "node", "vertex"}:
        if isinstance(stable_key, bool):
            return None
        try:
            ordinal = int(stable_key)
        except (TypeError, ValueError, OverflowError):
            return None
        return ordinal if 0 <= ordinal < len(mesh.points) else None
    if normalized not in {"cell", "element"}:
        return None
    parts = str(stable_key).split(":")
    if len(parts) != 2:
        return None
    try:
        block_ordinal, local_ordinal = (int(item) for item in parts)
    except (TypeError, ValueError, OverflowError):
        return None
    if not 0 <= block_ordinal < len(mesh.cells):
        return None
    block = mesh.cells[block_ordinal]
    if not 0 <= local_ordinal < block.count:
        return None
    return sum(item.count for item in mesh.cells[:block_ordinal]) + local_ordinal


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
            intent=str(value.get("intent", value.get("modifier", "replace"))),
        )
    except (TypeError, ValueError):
        return None


def _coerce_setup_pick_event(value: object) -> SetupPickEvent | None:
    if isinstance(value, SetupPickEvent):
        return value
    if not isinstance(value, Mapping):
        return None
    try:
        return SetupPickEvent(
            generation=int(value.get("generation", -1)),
            setup_id=str(value.get("setup_id", "")),
            semantic_id=str(value.get("semantic_id", "")),
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


def _entity_domain_ids(
    mesh: MeshData,
    entity_kind: EntityKind,
) -> tuple[int | str, ...]:
    if entity_kind is EntityKind.NODE:
        return tuple(range(len(mesh.points)))
    if entity_kind is EntityKind.CELL:
        return tuple(
            f"{block_ordinal}:{local_ordinal}"
            for block_ordinal, block in enumerate(mesh.cells)
            for local_ordinal in range(block.count)
        )
    return ()


__all__ = [
    "ActiveSceneController",
    "ActiveSceneScreenshotResult",
    "SceneActorRecord",
    "SceneAdapterRendererFactory",
    "SceneAdapterRendererSession",
    "SceneLifecycleState",
    "SceneMeshPayload",
    "ScenePickEvent",
    "SetupPickEvent",
    "SceneRendererFactoryProtocol",
    "SceneRendererInitializationError",
    "SceneRendererSessionProtocol",
]
