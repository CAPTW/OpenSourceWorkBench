"""Qt-free view models and semantic payloads for interactive results."""

from __future__ import annotations

from dataclasses import dataclass

from osw.core.result_mesh_binding import ResultMeshBindingResolution
from osw.post.result_field_mapping import (
    InteractiveScalarResult,
    ResultVectorGlyphSpec,
)
from osw.post.result_probe import ResultProbeResult, SelectedResultTable

RESULT_SCALAR_ACTOR_KEY = "result:scalar"
RESULT_VECTOR_ACTOR_KEY = "result:vector"
RESULT_PROBE_ACTOR_KEY = "result:probe"
RESULT_COLORBAR_ACTOR_KEY = "result:colorbar"


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


def build_scalar_overlay_spec(
    scalar: InteractiveScalarResult,
    *,
    mesh_fingerprint: str,
) -> ScalarResultOverlaySpec | None:
    """Return one actor payload only for a complete scalar projection."""

    if (
        not scalar.applied
        or scalar.display_range is None
        or not mesh_fingerprint
    ):
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
    )


def build_colorbar_spec(
    scalar: InteractiveScalarResult,
) -> ResultColorbarSpec | None:
    """Return explicit applied colorbar state when requested."""

    if (
        not scalar.applied
        or not scalar.colorbar_visible
        or scalar.display_range is None
    ):
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
) -> InteractiveResultsViewModel:
    """Build deterministic renderer-neutral state for the existing mesh panel."""

    binding = resolution.binding if resolution is not None else None
    return InteractiveResultsViewModel(
        binding_schema=str(binding.schema if binding is not None else ""),
        binding_state=str(resolution.state.value if resolution is not None else "UNRESOLVED"),
        binding_reason=str(
            resolution.reason_code
            if resolution is not None
            else "RESULT_BINDING_NOT_CONFIGURED"
        ),
        renderer_available=bool(renderer_available),
        backend_reason=str(backend_reason),
        scalar=scalar,
        vector=vector,
        probe=probe,
        table=table,
    )


__all__ = [
    "InteractiveResultsViewModel",
    "RESULT_COLORBAR_ACTOR_KEY",
    "RESULT_PROBE_ACTOR_KEY",
    "RESULT_SCALAR_ACTOR_KEY",
    "RESULT_VECTOR_ACTOR_KEY",
    "ResultColorbarSpec",
    "ResultProbeOverlaySpec",
    "ScalarResultOverlaySpec",
    "build_colorbar_spec",
    "build_interactive_results_view_model",
    "build_scalar_overlay_spec",
]
