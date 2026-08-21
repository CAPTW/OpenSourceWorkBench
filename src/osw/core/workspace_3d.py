"""Pure, declarative persistence contracts for one 3D workspace scene."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from typing import Any

ACTIVE_SCENE_SCHEMA = "osw.active_scene.v1"
_MESH_FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REPRESENTATIONS = frozenset({"surface", "wireframe", "surface_with_edges"})
_SELECTION_MODES = frozenset({"none", "node", "point", "cell", "setup"})
_ACTOR_KINDS = frozenset(
    {
        "base_mesh",
        "wireframe",
        "named_selection",
        "material_assignment",
        "fixed_support",
        "force_load",
        "setup_target",
        "setup_glyph",
        "mesh_quality_bad_cells",
        "scalar_result",
        "vector_result",
    }
)


def _finite_vector(
    value: Sequence[float],
    *,
    name: str,
) -> tuple[float, float, float]:
    result = tuple(float(item) for item in value)
    if len(result) != 3:
        raise ValueError(f"{name} must contain exactly three values.")
    if not all(isfinite(item) for item in result):
        raise ValueError(f"{name} values must be finite.")
    return result  # type: ignore[return-value]


def _optional_finite(value: object, *, name: str) -> float | None:
    if value is None:
        return None
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _sorted_ids(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(item) for item in values if str(item)}))


def _mapping(value: object, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping.")
    return value


def _json_extensions(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        text = str(key)
        if not text or ("." not in text and ":" not in text):
            raise ValueError("Active-scene extension keys must be namespaced.")
        result[text] = item
    try:
        json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise TypeError("Active-scene extensions must be JSON-compatible.") from exc
    return result


@dataclass(frozen=True)
class ActiveSceneCameraState:
    """Renderer-independent camera values applied only after exact mesh reload."""

    position: tuple[float, float, float] | None = None
    focal_point: tuple[float, float, float] | None = None
    view_up: tuple[float, float, float] | None = None
    parallel_projection: bool = False
    parallel_scale: float | None = None
    view_preset: str = ""

    def __post_init__(self) -> None:
        for name in ("position", "focal_point", "view_up"):
            value = getattr(self, name)
            object.__setattr__(
                self,
                name,
                None if value is None else _finite_vector(value, name=f"camera.{name}"),
            )
        scale = _optional_finite(self.parallel_scale, name="camera.parallel_scale")
        if scale is not None and scale <= 0.0:
            raise ValueError("camera.parallel_scale must be finite and positive.")
        object.__setattr__(self, "parallel_projection", bool(self.parallel_projection))
        object.__setattr__(self, "parallel_scale", scale)
        object.__setattr__(self, "view_preset", str(self.view_preset or ""))

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": list(self.position) if self.position is not None else None,
            "focal_point": (list(self.focal_point) if self.focal_point is not None else None),
            "view_up": list(self.view_up) if self.view_up is not None else None,
            "parallel_projection": self.parallel_projection,
            "parallel_scale": self.parallel_scale,
            "view_preset": self.view_preset,
        }

    @classmethod
    def from_dict(cls, value: object) -> ActiveSceneCameraState:
        data = _mapping(value, name="active_scene.camera")
        return cls(
            position=data.get("position"),
            focal_point=data.get("focal_point"),
            view_up=data.get("view_up"),
            parallel_projection=bool(data.get("parallel_projection", False)),
            parallel_scale=data.get("parallel_scale"),
            view_preset=str(data.get("view_preset", "")),
        )


@dataclass(frozen=True, order=True)
class SemanticActorVisibility:
    """One durable semantic actor visibility entry without native identity."""

    kind: str
    source_id: str
    variant: str = ""
    visible: bool = True

    def __post_init__(self) -> None:
        kind = str(self.kind or "")
        source_id = str(self.source_id or "")
        if kind not in _ACTOR_KINDS:
            raise ValueError(f"Unsupported active-scene actor kind: {kind or '<empty>'}.")
        if not source_id:
            raise ValueError("Active-scene actor source_id must not be empty.")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "variant", str(self.variant or ""))
        object.__setattr__(self, "visible", bool(self.visible))

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source_id": self.source_id,
            "variant": self.variant,
            "visible": self.visible,
        }

    @classmethod
    def from_dict(cls, value: object) -> SemanticActorVisibility:
        data = _mapping(value, name="active_scene.actor_visibility[]")
        return cls(
            kind=str(data.get("kind", "")),
            source_id=str(data.get("source_id", "")),
            variant=str(data.get("variant", "")),
            visible=bool(data.get("visible", True)),
        )


@dataclass(frozen=True)
class ActiveSceneResultState:
    """Declarative interactive-result request; contains no result rows or indices."""

    result_ref_id: str = ""
    result_dataset_id: str = ""
    binding_schema: str = ""
    mesh_fingerprint: str = ""
    scalar_field: str = ""
    scalar_component: str = ""
    scalar_association: str = ""
    range_mode: str = "AUTO"
    manual_min: float | None = None
    manual_max: float | None = None
    colormap: str = "viridis"
    colorbar_visible: bool = True
    vector_field: str = ""
    vector_components: tuple[str, ...] = ()
    vector_association: str = ""
    vector_visible: bool = False
    glyph_scale: float = 1.0
    glyph_max_count: int = 500

    def __post_init__(self) -> None:
        for name in (
            "result_ref_id",
            "result_dataset_id",
            "binding_schema",
            "scalar_field",
            "scalar_component",
            "scalar_association",
            "colormap",
            "vector_field",
            "vector_association",
        ):
            object.__setattr__(self, name, str(getattr(self, name) or ""))
        fingerprint = str(self.mesh_fingerprint or "").lower()
        if fingerprint and not _MESH_FINGERPRINT_PATTERN.fullmatch(fingerprint):
            raise ValueError("result_state.mesh_fingerprint must be a SHA-256 hex digest.")
        object.__setattr__(self, "mesh_fingerprint", fingerprint)
        mode = str(self.range_mode or "AUTO").upper()
        if mode not in {"AUTO", "MANUAL"}:
            raise ValueError("result_state.range_mode must be AUTO or MANUAL.")
        object.__setattr__(self, "range_mode", mode)
        minimum = _optional_finite(self.manual_min, name="result_state.manual_min")
        maximum = _optional_finite(self.manual_max, name="result_state.manual_max")
        if mode == "MANUAL" and (minimum is None or maximum is None or minimum >= maximum):
            raise ValueError("Manual result display range must contain finite minimum < maximum.")
        object.__setattr__(self, "manual_min", minimum)
        object.__setattr__(self, "manual_max", maximum)
        object.__setattr__(
            self,
            "vector_components",
            tuple(str(item) for item in self.vector_components),
        )
        scale = float(self.glyph_scale)
        if not isfinite(scale) or scale <= 0.0:
            raise ValueError("result_state.glyph_scale must be finite and positive.")
        count = int(self.glyph_max_count)
        if count <= 0 or count > 100_000:
            raise ValueError("result_state.glyph_max_count must be between 1 and 100000.")
        object.__setattr__(self, "glyph_scale", scale)
        object.__setattr__(self, "glyph_max_count", count)
        object.__setattr__(self, "colorbar_visible", bool(self.colorbar_visible))
        object.__setattr__(self, "vector_visible", bool(self.vector_visible))

    @property
    def display_range(self) -> tuple[float, float] | None:
        if self.manual_min is None or self.manual_max is None:
            return None
        return self.manual_min, self.manual_max

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_ref_id": self.result_ref_id,
            "result_dataset_id": self.result_dataset_id,
            "binding_schema": self.binding_schema,
            "mesh_fingerprint": self.mesh_fingerprint,
            "scalar_field": self.scalar_field,
            "scalar_component": self.scalar_component,
            "scalar_association": self.scalar_association,
            "range_mode": self.range_mode,
            "manual_min": self.manual_min,
            "manual_max": self.manual_max,
            "colormap": self.colormap,
            "colorbar_visible": self.colorbar_visible,
            "vector_field": self.vector_field,
            "vector_components": list(self.vector_components),
            "vector_association": self.vector_association,
            "vector_visible": self.vector_visible,
            "glyph_scale": self.glyph_scale,
            "glyph_max_count": self.glyph_max_count,
        }

    @classmethod
    def from_dict(cls, value: object) -> ActiveSceneResultState:
        data = _mapping(value, name="active_scene.result_state")
        return cls(
            result_ref_id=str(data.get("result_ref_id", "")),
            result_dataset_id=str(data.get("result_dataset_id", "")),
            binding_schema=str(data.get("binding_schema", "")),
            mesh_fingerprint=str(data.get("mesh_fingerprint", "")),
            scalar_field=str(data.get("scalar_field", "")),
            scalar_component=str(data.get("scalar_component", "")),
            scalar_association=str(data.get("scalar_association", "")),
            range_mode=str(data.get("range_mode", "AUTO")),
            manual_min=data.get("manual_min"),
            manual_max=data.get("manual_max"),
            colormap=str(data.get("colormap", "viridis")),
            colorbar_visible=bool(data.get("colorbar_visible", True)),
            vector_field=str(data.get("vector_field", "")),
            vector_components=tuple(data.get("vector_components", ()) or ()),
            vector_association=str(data.get("vector_association", "")),
            vector_visible=bool(data.get("vector_visible", False)),
            glyph_scale=data.get("glyph_scale", 1.0),
            glyph_max_count=data.get("glyph_max_count", 500),
        )


@dataclass(frozen=True)
class MeshQualityViewState:
    """Declarative quality request; computed values and bad-cell IDs stay transient."""

    metric_schema: str
    threshold: float = 10.0
    highlight_visible: bool = False

    def __post_init__(self) -> None:
        schema = str(self.metric_schema or "")
        if schema != "osw.mesh_quality.edge_aspect_ratio.v1":
            raise ValueError("Unsupported active-scene mesh quality metric schema.")
        threshold = float(self.threshold)
        if not isfinite(threshold) or threshold <= 0.0:
            raise ValueError("Mesh quality threshold must be finite and positive.")
        object.__setattr__(self, "metric_schema", schema)
        object.__setattr__(self, "threshold", threshold)
        object.__setattr__(self, "highlight_visible", bool(self.highlight_visible))

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_schema": self.metric_schema,
            "threshold": self.threshold,
            "highlight_visible": self.highlight_visible,
        }

    @classmethod
    def from_dict(cls, value: object) -> MeshQualityViewState:
        data = _mapping(value, name="active_scene.mesh_quality_state")
        return cls(
            metric_schema=str(data.get("metric_schema", "")),
            threshold=data.get("threshold", 10.0),
            highlight_visible=bool(data.get("highlight_visible", False)),
        )


@dataclass(frozen=True)
class ActiveSceneClippingState:
    """Pure clipping request without plane widgets or callback identity."""

    enabled: bool = False
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    normal: tuple[float, float, float] = (1.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        origin = _finite_vector(self.origin, name="clipping.origin")
        normal = _finite_vector(self.normal, name="clipping.normal")
        if sum(item * item for item in normal) <= 0.0:
            raise ValueError("clipping.normal must be nonzero.")
        object.__setattr__(self, "enabled", bool(self.enabled))
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "normal", normal)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "origin": list(self.origin),
            "normal": list(self.normal),
        }

    @classmethod
    def from_dict(cls, value: object) -> ActiveSceneClippingState:
        data = _mapping(value, name="active_scene.clipping_state")
        return cls(
            enabled=bool(data.get("enabled", False)),
            origin=data.get("origin", (0.0, 0.0, 0.0)),
            normal=data.get("normal", (1.0, 0.0, 0.0)),
        )


@dataclass(frozen=True)
class ActiveSceneState:
    """Exact-fingerprint-bound declarative state for one active 3D workspace."""

    mesh_ref: str
    mesh_fingerprint: str
    schema: str = ACTIVE_SCENE_SCHEMA
    camera: ActiveSceneCameraState = field(default_factory=ActiveSceneCameraState)
    representation: str = "surface"
    axes_visible: bool = True
    actor_visibility: tuple[SemanticActorVisibility, ...] = ()
    visible_named_selection_ids: tuple[str, ...] = ()
    active_named_selection_ids: tuple[str, ...] = ()
    result_state: ActiveSceneResultState | None = None
    mesh_quality_state: MeshQualityViewState | None = None
    clipping_state: ActiveSceneClippingState = field(default_factory=ActiveSceneClippingState)
    selection_mode: str = "none"
    extensions: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        schema = str(self.schema or "")
        if schema != ACTIVE_SCENE_SCHEMA:
            raise ValueError(f"Unsupported active_scene schema: {schema or '<empty>'}.")
        mesh_ref = str(self.mesh_ref or "")
        if not mesh_ref:
            raise ValueError("active_scene.mesh_ref must not be empty.")
        fingerprint = str(self.mesh_fingerprint or "").lower()
        if not _MESH_FINGERPRINT_PATTERN.fullmatch(fingerprint):
            raise ValueError("active_scene.mesh_fingerprint must be a SHA-256 hex digest.")
        camera = (
            self.camera
            if isinstance(self.camera, ActiveSceneCameraState)
            else ActiveSceneCameraState.from_dict(self.camera)
        )
        representation = str(self.representation or "")
        if representation not in _REPRESENTATIONS:
            raise ValueError(
                f"Unsupported active-scene representation: {representation or '<empty>'}."
            )
        actors = tuple(
            item
            if isinstance(item, SemanticActorVisibility)
            else SemanticActorVisibility.from_dict(item)
            for item in self.actor_visibility
        )
        actor_keys = [(item.kind, item.source_id, item.variant) for item in actors]
        if len(actor_keys) != len(set(actor_keys)):
            raise ValueError("Active-scene actor visibility entries must be unique.")
        result_state = (
            None
            if self.result_state is None
            else (
                self.result_state
                if isinstance(self.result_state, ActiveSceneResultState)
                else ActiveSceneResultState.from_dict(self.result_state)
            )
        )
        quality_state = (
            None
            if self.mesh_quality_state is None
            else (
                self.mesh_quality_state
                if isinstance(self.mesh_quality_state, MeshQualityViewState)
                else MeshQualityViewState.from_dict(self.mesh_quality_state)
            )
        )
        clipping = (
            self.clipping_state
            if isinstance(self.clipping_state, ActiveSceneClippingState)
            else ActiveSceneClippingState.from_dict(self.clipping_state)
        )
        selection_mode = str(self.selection_mode or "none").lower()
        if selection_mode not in _SELECTION_MODES:
            raise ValueError(f"Unsupported active-scene selection mode: {selection_mode}.")
        object.__setattr__(self, "schema", schema)
        object.__setattr__(self, "mesh_ref", mesh_ref)
        object.__setattr__(self, "mesh_fingerprint", fingerprint)
        object.__setattr__(self, "camera", camera)
        object.__setattr__(self, "representation", representation)
        object.__setattr__(self, "axes_visible", bool(self.axes_visible))
        object.__setattr__(self, "actor_visibility", tuple(sorted(actors)))
        object.__setattr__(
            self,
            "visible_named_selection_ids",
            _sorted_ids(self.visible_named_selection_ids),
        )
        object.__setattr__(
            self,
            "active_named_selection_ids",
            _sorted_ids(self.active_named_selection_ids),
        )
        object.__setattr__(self, "result_state", result_state)
        object.__setattr__(self, "mesh_quality_state", quality_state)
        object.__setattr__(self, "clipping_state", clipping)
        object.__setattr__(self, "selection_mode", selection_mode)
        object.__setattr__(self, "extensions", _json_extensions(self.extensions))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "mesh_ref": self.mesh_ref,
            "mesh_fingerprint": self.mesh_fingerprint,
            "camera": self.camera.to_dict(),
            "representation": self.representation,
            "axes_visible": self.axes_visible,
            "actor_visibility": [item.to_dict() for item in self.actor_visibility],
            "visible_named_selection_ids": list(self.visible_named_selection_ids),
            "active_named_selection_ids": list(self.active_named_selection_ids),
            "result_state": (
                self.result_state.to_dict() if self.result_state is not None else None
            ),
            "mesh_quality_state": (
                self.mesh_quality_state.to_dict() if self.mesh_quality_state is not None else None
            ),
            "clipping_state": self.clipping_state.to_dict(),
            "selection_mode": self.selection_mode,
            "extensions": dict(self.extensions),
        }

    @classmethod
    def from_dict(cls, value: object) -> ActiveSceneState:
        data = _mapping(value, name="active_scene")
        schema = str(data.get("schema", ""))
        if schema != ACTIVE_SCENE_SCHEMA:
            raise ValueError(f"Unsupported active_scene schema: {schema or '<empty>'}.")
        return cls(
            schema=schema,
            mesh_ref=str(data.get("mesh_ref", "")),
            mesh_fingerprint=str(data.get("mesh_fingerprint", "")),
            camera=ActiveSceneCameraState.from_dict(data.get("camera", {})),
            representation=str(data.get("representation", "surface")),
            axes_visible=bool(data.get("axes_visible", True)),
            actor_visibility=tuple(
                SemanticActorVisibility.from_dict(item)
                for item in data.get("actor_visibility", ()) or ()
            ),
            visible_named_selection_ids=tuple(data.get("visible_named_selection_ids", ()) or ()),
            active_named_selection_ids=tuple(data.get("active_named_selection_ids", ()) or ()),
            result_state=(
                None
                if data.get("result_state") is None
                else ActiveSceneResultState.from_dict(data["result_state"])
            ),
            mesh_quality_state=(
                None
                if data.get("mesh_quality_state") is None
                else MeshQualityViewState.from_dict(data["mesh_quality_state"])
            ),
            clipping_state=ActiveSceneClippingState.from_dict(data.get("clipping_state", {})),
            selection_mode=str(data.get("selection_mode", "none")),
            extensions=dict(_mapping(data.get("extensions", {}), name="active_scene.extensions")),
        )


class ActiveSceneRestoreStatus(StrEnum):
    PENDING = "PENDING"
    RESTORED = "RESTORED"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ActiveSceneRestoreResult:
    """Deterministic restore classification and safe reason codes."""

    status: ActiveSceneRestoreStatus
    reason_codes: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", ActiveSceneRestoreStatus(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            tuple(dict.fromkeys(str(item) for item in self.reason_codes)),
        )
        object.__setattr__(
            self,
            "diagnostics",
            tuple(str(item) for item in self.diagnostics),
        )


@dataclass(frozen=True)
class ActiveSceneScreenshotRequest:
    """Explicit current-session screenshot request."""

    record_id: str
    output_path: str
    path_kind: str | None = None
    caption: str = ""
    requested_size: tuple[int, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        record_id = str(self.record_id or "")
        output_path = str(self.output_path or "")
        caption = str(self.caption or "")
        if not record_id:
            raise ValueError("Screenshot record_id must not be empty.")
        if not output_path:
            raise ValueError("Screenshot output_path must not be empty.")
        if len(caption) > 1000:
            raise ValueError("Screenshot caption must not exceed 1000 characters.")
        size = self.requested_size
        if size is not None:
            size = tuple(int(item) for item in size)
            if len(size) != 2 or any(item <= 0 for item in size):
                raise ValueError("Screenshot requested_size must contain two positive values.")
        object.__setattr__(self, "record_id", record_id)
        object.__setattr__(self, "output_path", output_path)
        object.__setattr__(
            self,
            "path_kind",
            None if self.path_kind is None else str(self.path_kind),
        )
        object.__setattr__(self, "caption", caption)
        object.__setattr__(self, "requested_size", size)
        object.__setattr__(self, "metadata", _json_extensions(self.metadata))


def active_scene_state_digest(state: ActiveSceneState) -> str:
    """Return SHA-256 of the canonical validated declarative scene state."""

    if not isinstance(state, ActiveSceneState):
        raise TypeError("active_scene_state_digest requires ActiveSceneState.")
    canonical = json.dumps(
        state.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def active_scene_provenance(
    state: ActiveSceneState,
    *,
    image_sha256: str,
    image_byte_length: int,
    image_size: tuple[int, int] | None,
    capture_backend_kind: str,
) -> dict[str, Any]:
    """Build deterministic screenshot/report provenance without a file path."""

    result = state.result_state
    quality = state.mesh_quality_state
    setup_kinds = {"material_assignment", "fixed_support", "force_load"}
    visible_setup = tuple(
        f"{item.kind}:{item.source_id}"
        for item in state.actor_visibility
        if item.kind in setup_kinds and item.visible
    )
    return {
        "active_scene_schema": state.schema,
        "active_scene_digest": active_scene_state_digest(state),
        "mesh_ref": state.mesh_ref,
        "mesh_fingerprint": state.mesh_fingerprint,
        "result_ref_id": result.result_ref_id if result else "",
        "result_dataset_id": result.result_dataset_id if result else "",
        "result_binding_schema": result.binding_schema if result else "",
        "scalar_field": result.scalar_field if result else "",
        "scalar_component": result.scalar_component if result else "",
        "scalar_association": result.scalar_association if result else "",
        "scalar_range_mode": result.range_mode if result else "",
        "scalar_display_range": (
            list(result.display_range)
            if result is not None and result.display_range is not None
            else None
        ),
        "colormap": result.colormap if result else "",
        "colorbar_visible": result.colorbar_visible if result else False,
        "vector_field": result.vector_field if result else "",
        "vector_components": list(result.vector_components) if result else [],
        "vector_association": result.vector_association if result else "",
        "glyph_scale": result.glyph_scale if result else None,
        "glyph_max_count": result.glyph_max_count if result else None,
        "visible_named_selection_ids": list(state.visible_named_selection_ids),
        "active_named_selection_ids": list(state.active_named_selection_ids),
        "visible_setup_actor_keys": list(visible_setup),
        "mesh_quality_metric_schema": (quality.metric_schema if quality is not None else ""),
        "mesh_quality_threshold": (quality.threshold if quality is not None else None),
        "mesh_quality_highlight_visible": (
            quality.highlight_visible if quality is not None else False
        ),
        "camera": state.camera.to_dict(),
        "representation": state.representation,
        "axes_visible": state.axes_visible,
        "clipping": state.clipping_state.to_dict(),
        "image_sha256": str(image_sha256),
        "image_byte_length": int(image_byte_length),
        "image_size": list(image_size) if image_size is not None else None,
        "capture_backend_kind": str(capture_backend_kind),
        "artifact_caveat": (
            "Scene screenshot is a local report artifact only; it is not "
            "validation evidence and not a release asset."
        ),
    }


__all__ = [
    "ACTIVE_SCENE_SCHEMA",
    "ActiveSceneCameraState",
    "ActiveSceneClippingState",
    "ActiveSceneRestoreResult",
    "ActiveSceneRestoreStatus",
    "ActiveSceneResultState",
    "ActiveSceneScreenshotRequest",
    "ActiveSceneState",
    "MeshQualityViewState",
    "SemanticActorVisibility",
    "active_scene_provenance",
    "active_scene_state_digest",
]
