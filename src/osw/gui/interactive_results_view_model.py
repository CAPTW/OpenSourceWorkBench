"""Qt-free view models and semantic payloads for interactive results."""

from __future__ import annotations

from dataclasses import dataclass

from osw.core.result_mesh_binding import ResultMeshBindingResolution
from osw.mesh.mesh_model import MeshData
from osw.post.result_deformation import DeformedShapeSpec
from osw.post.result_field_catalog import ResultFieldCatalog
from osw.post.result_field_mapping import (
    InteractiveScalarResult,
    ResultVectorGlyphSpec,
)
from osw.post.result_probe import ResultProbeResult, SelectedResultTable

RESULT_SCALAR_ACTOR_KEY = "result:scalar"
RESULT_VECTOR_ACTOR_KEY = "result:vector"
RESULT_PROBE_ACTOR_KEY = "result:probe"
RESULT_COLORBAR_ACTOR_KEY = "result:colorbar"
RESULT_DEFORMED_ACTOR_KEY = "result:deformed"
RESULT_ORIGINAL_REFERENCE_ACTOR_KEY = "result:original_reference"


@dataclass(frozen=True)
class InteractiveResultSessionState:
    """Serializable-ready result interaction state with no native handles."""

    active_result_id: str = ""
    binding_status: str = "UNRESOLVED"
    active_field_id: str = ""
    active_scalar_mode: str = "scalar"
    contour_visible: bool = False
    range_mode: str = "AUTO"
    manual_range: tuple[float, float] | None = None
    colormap: str = "viridis"
    colorbar_visible: bool = True
    vector_field_id: str = ""
    vector_visible: bool = False
    vector_max_glyph_count: int = 500
    vector_scale_mode: str = "AUTO"
    vector_manual_scale: float = 1.0
    probe_mode: str = "none"
    deformation_field_id: str = ""
    deformation_mode: str = "ORIGINAL"
    deformation_scale_mode: str = "AUTO"
    deformation_manual_scale: float = 1.0
    stale_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible transient state mirrored by ActiveSceneResultState."""

        return {
            "active_result_id": self.active_result_id,
            "binding_status": self.binding_status,
            "active_field_id": self.active_field_id,
            "active_scalar_mode": self.active_scalar_mode,
            "contour_visible": self.contour_visible,
            "range_mode": self.range_mode,
            "manual_range": (list(self.manual_range) if self.manual_range is not None else None),
            "colormap": self.colormap,
            "colorbar_visible": self.colorbar_visible,
            "vector_field_id": self.vector_field_id,
            "vector_visible": self.vector_visible,
            "vector_max_glyph_count": self.vector_max_glyph_count,
            "vector_scale_mode": self.vector_scale_mode,
            "vector_manual_scale": self.vector_manual_scale,
            "probe_mode": self.probe_mode,
            "deformation_field_id": self.deformation_field_id,
            "deformation_mode": self.deformation_mode,
            "deformation_scale_mode": self.deformation_scale_mode,
            "deformation_manual_scale": self.deformation_manual_scale,
            "stale_reason": self.stale_reason,
        }


@dataclass(frozen=True)
class ScalarResultOverlaySpec:
    """One scalar surface payload with an exact point/cell value array."""

    actor_key: str
    field_name: str
    component: str
    association: str
    values: tuple[float, ...]
    display_range: tuple[float, float]
    colormap: str
    mesh_fingerprint: str
    result_id: str = ""
    array_name: str = ""
    mesh: MeshData | None = None


@dataclass(frozen=True)
class ResultColorbarSpec:
    """Logical colorbar state applied alongside a scalar result actor."""

    actor_key: str
    title: str
    display_range: tuple[float, float]
    colormap: str
    visible: bool


@dataclass(frozen=True)
class ResultProbeOverlaySpec:
    """Transient probe marker identified by the current stable entity key."""

    actor_key: str
    association: str
    stable_entity_key: int | str
    transient_backend_index: int
    mesh_fingerprint: str


@dataclass(frozen=True)
class DeformedResultOverlaySpec:
    """One derived geometry actor with original canonical identity."""

    actor_key: str
    result_id: str
    field_name: str
    mesh: MeshData
    mesh_fingerprint: str
    mode: str
    scale: float
    opacity: float = 1.0
    representation: str = "surface"
    pickable: bool = True


@dataclass(frozen=True)
class InteractiveResultsViewModel:
    """Safe UI projection of current binding and transient result state."""

    binding_schema: str
    binding_state: str
    binding_reason: str
    renderer_available: bool
    backend_reason: str
    scalar: InteractiveScalarResult | None = None
    vector: ResultVectorGlyphSpec | None = None
    probe: ResultProbeResult | None = None
    table: SelectedResultTable | None = None
    catalog: ResultFieldCatalog | None = None
    deformation: DeformedShapeSpec | None = None
    state: InteractiveResultSessionState = InteractiveResultSessionState()


def build_scalar_overlay_spec(
    scalar: InteractiveScalarResult,
    *,
    mesh_fingerprint: str,
    result_id: str = "",
    mesh: MeshData | None = None,
) -> ScalarResultOverlaySpec | None:
    """Return one actor payload only for a complete scalar projection."""

    if not scalar.applied or scalar.display_range is None or not mesh_fingerprint:
        return None
    return ScalarResultOverlaySpec(
        actor_key=RESULT_SCALAR_ACTOR_KEY,
        field_name=scalar.field_name,
        component=scalar.component,
        association=scalar.association,
        values=scalar.values,
        display_range=scalar.display_range,
        colormap=scalar.colormap,
        mesh_fingerprint=mesh_fingerprint,
        result_id=result_id,
        array_name=scalar.array_name,
        mesh=mesh,
    )


def build_deformed_overlay_spec(
    deformation: DeformedShapeSpec,
    *,
    result_id: str,
) -> DeformedResultOverlaySpec | None:
    """Return a native payload only for an applied derived geometry mode."""

    if not deformation.applied or deformation.mesh_data is None:
        return None
    return DeformedResultOverlaySpec(
        actor_key=RESULT_DEFORMED_ACTOR_KEY,
        result_id=str(result_id),
        field_name=deformation.field_name,
        mesh=deformation.mesh_data,
        mesh_fingerprint=deformation.mesh_fingerprint,
        mode=deformation.mode.value,
        scale=deformation.scale,
        opacity=0.65 if deformation.mode.value == "OVERLAY" else 1.0,
    )


def build_colorbar_spec(
    scalar: InteractiveScalarResult,
) -> ResultColorbarSpec | None:
    """Return explicit applied colorbar state when requested."""

    if not scalar.applied or not scalar.colorbar_visible or scalar.display_range is None:
        return None
    return ResultColorbarSpec(
        actor_key=RESULT_COLORBAR_ACTOR_KEY,
        title=scalar.colorbar_title,
        display_range=scalar.display_range,
        colormap=scalar.colormap,
        visible=True,
    )


def build_interactive_results_view_model(
    resolution: ResultMeshBindingResolution | None,
    *,
    renderer_available: bool,
    backend_reason: str = "",
    scalar: InteractiveScalarResult | None = None,
    vector: ResultVectorGlyphSpec | None = None,
    probe: ResultProbeResult | None = None,
    table: SelectedResultTable | None = None,
    catalog: ResultFieldCatalog | None = None,
    deformation: DeformedShapeSpec | None = None,
    state: InteractiveResultSessionState | None = None,
) -> InteractiveResultsViewModel:
    """Build deterministic renderer-neutral state for the existing mesh panel."""

    binding = resolution.binding if resolution is not None else None
    return InteractiveResultsViewModel(
        binding_schema=str(binding.schema if binding is not None else ""),
        binding_state=str(resolution.state.value if resolution is not None else "UNRESOLVED"),
        binding_reason=str(
            resolution.reason_code if resolution is not None else "RESULT_BINDING_NOT_CONFIGURED"
        ),
        renderer_available=bool(renderer_available),
        backend_reason=str(backend_reason),
        scalar=scalar,
        vector=vector,
        probe=probe,
        table=table,
        catalog=catalog,
        deformation=deformation,
        state=state or InteractiveResultSessionState(),
    )


__all__ = [
    "InteractiveResultsViewModel",
    "RESULT_COLORBAR_ACTOR_KEY",
    "RESULT_DEFORMED_ACTOR_KEY",
    "RESULT_ORIGINAL_REFERENCE_ACTOR_KEY",
    "RESULT_PROBE_ACTOR_KEY",
    "RESULT_SCALAR_ACTOR_KEY",
    "RESULT_VECTOR_ACTOR_KEY",
    "DeformedResultOverlaySpec",
    "InteractiveResultSessionState",
    "ResultColorbarSpec",
    "ResultProbeOverlaySpec",
    "ScalarResultOverlaySpec",
    "build_colorbar_spec",
    "build_deformed_overlay_spec",
    "build_interactive_results_view_model",
    "build_scalar_overlay_spec",
]
