"""PyVista-free 3D Workspace scene data contracts.

Serializable scene state (camera, render options, view state), a local
screenshot record, and a scene input reference. These are pure data models:
they import no rendering, GUI toolkit, mesh-io, or solver code and never render
or run anything. A local scene screenshot is artifact metadata only -- it is
not a release asset and not validation evidence. The rendering adapter lives in
``osw.post.pyvista_scene``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from osw.core.validation import ValidationReport

_KNOWN_VIEW_PRESETS = frozenset({"iso", "xy", "xz", "yz", "yx", "zx", "zy", "fit", "default"})
_KNOWN_SOURCE_KINDS = frozenset({"mesh", "result_field", "selection"})


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _string_dict(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})


def _optional_triple(value: object) -> tuple[float, float, float] | None:
    if value is None:
        return None
    values = tuple(float(item) for item in value)
    if len(values) != 3:
        msg = "Scene 3D vector must contain exactly three values."
        raise ValueError(msg)
    return values


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def _positive_float(value: object) -> float:
    number = float(value)
    if not (isfinite(number) and number > 0.0):
        msg = "Scene positive value must be finite and positive."
        raise ValueError(msg)
    return number


def _optional_size(value: object) -> tuple[int, int] | None:
    if value is None:
        return None
    values = tuple(int(item) for item in value)
    if len(values) != 2:
        msg = "Screenshot size must contain exactly two values (width, height)."
        raise ValueError(msg)
    return values


def _str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class SceneCameraState:
    """Reproducible camera state; recorded, not applied to a live plotter here."""

    position: tuple[float, float, float] | None = None
    focal_point: tuple[float, float, float] | None = None
    view_up: tuple[float, float, float] | None = None
    parallel_projection: bool = False
    parallel_scale: float | None = None
    view_preset: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "position", _optional_triple(self.position))
        object.__setattr__(self, "focal_point", _optional_triple(self.focal_point))
        object.__setattr__(self, "view_up", _optional_triple(self.view_up))
        object.__setattr__(self, "parallel_projection", bool(self.parallel_projection))
        object.__setattr__(self, "parallel_scale", _optional_float(self.parallel_scale))
        object.__setattr__(self, "view_preset", _optional_str(self.view_preset))
        object.__setattr__(self, "metadata", _string_dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": list(self.position) if self.position is not None else None,
            "focal_point": list(self.focal_point) if self.focal_point is not None else None,
            "view_up": list(self.view_up) if self.view_up is not None else None,
            "parallel_projection": self.parallel_projection,
            "parallel_scale": self.parallel_scale,
            "view_preset": self.view_preset,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> SceneCameraState:
        if not isinstance(data, Mapping):
            msg = "SceneCameraState data must be a mapping."
            raise TypeError(msg)
        return cls(
            position=data.get("position"),
            focal_point=data.get("focal_point"),
            view_up=data.get("view_up"),
            parallel_projection=bool(data.get("parallel_projection", False)),
            parallel_scale=data.get("parallel_scale"),
            view_preset=data.get("view_preset"),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "camera") -> ValidationReport:
        report = ValidationReport()
        for name in ("position", "focal_point", "view_up"):
            vector = getattr(self, name)
            if vector is not None and not all(isfinite(value) for value in vector):
                report.add_error(f"{path}.{name}", "Scene camera vector must be finite.")
        if self.parallel_scale is not None and not (
            isfinite(self.parallel_scale) and self.parallel_scale > 0
        ):
            report.add_error(
                f"{path}.parallel_scale", "Parallel scale must be finite and positive."
            )
        if self.view_preset and self.view_preset.lower() not in _KNOWN_VIEW_PRESETS:
            report.add_warning(
                f"{path}.view_preset",
                f"Unknown scene view preset {self.view_preset!r}; it does not force rendering.",
            )
        return report


@dataclass(frozen=True)
class SceneRenderOptions:
    """Serializable render toggles; a superset of PyVistaSceneConfig."""

    show_surface: bool = True
    show_edges: bool = False
    show_axes: bool = True
    show_grid: bool = False
    show_bounds: bool = False
    background: str | None = None
    color_by: str | None = None
    scalar_bar: bool = True
    screenshot_size: tuple[int, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "show_surface", bool(self.show_surface))
        object.__setattr__(self, "show_edges", bool(self.show_edges))
        object.__setattr__(self, "show_axes", bool(self.show_axes))
        object.__setattr__(self, "show_grid", bool(self.show_grid))
        object.__setattr__(self, "show_bounds", bool(self.show_bounds))
        object.__setattr__(self, "background", _optional_str(self.background))
        object.__setattr__(self, "color_by", _optional_str(self.color_by))
        object.__setattr__(self, "scalar_bar", bool(self.scalar_bar))
        object.__setattr__(self, "screenshot_size", _optional_size(self.screenshot_size))
        object.__setattr__(self, "metadata", _string_dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "show_surface": self.show_surface,
            "show_edges": self.show_edges,
            "show_axes": self.show_axes,
            "show_grid": self.show_grid,
            "show_bounds": self.show_bounds,
            "background": self.background,
            "color_by": self.color_by,
            "scalar_bar": self.scalar_bar,
            "screenshot_size": list(self.screenshot_size) if self.screenshot_size else None,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> SceneRenderOptions:
        if not isinstance(data, Mapping):
            msg = "SceneRenderOptions data must be a mapping."
            raise TypeError(msg)
        return cls(
            show_surface=bool(data.get("show_surface", True)),
            show_edges=bool(data.get("show_edges", False)),
            show_axes=bool(data.get("show_axes", True)),
            show_grid=bool(data.get("show_grid", False)),
            show_bounds=bool(data.get("show_bounds", False)),
            background=data.get("background"),
            color_by=data.get("color_by"),
            scalar_bar=bool(data.get("scalar_bar", True)),
            screenshot_size=data.get("screenshot_size"),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "render_options") -> ValidationReport:
        report = ValidationReport()
        if self.screenshot_size is not None and not all(
            value > 0 for value in self.screenshot_size
        ):
            report.add_error(
                f"{path}.screenshot_size", "Screenshot size width and height must be positive."
            )
        return report

    def to_pyvista_config_dict(self) -> dict[str, Any]:
        """Map the render toggles to PyVistaSceneConfig keyword arguments (pure)."""
        return {
            "show_surface": self.show_surface,
            "show_edges": self.show_edges,
            "show_axes": self.show_axes,
            "show_grid": self.show_grid,
            "scalar_field": self.color_by,
            "off_screen": True,
        }

    def to_pyvista_config(self) -> Any:
        """Build a PyVistaSceneConfig (imported lazily to avoid an import cycle)."""
        from osw.post.pyvista_scene import PyVistaSceneConfig

        return PyVistaSceneConfig(**self.to_pyvista_config_dict())


@dataclass(frozen=True)
class SceneGlyphOptions:
    """Preview-only vector glyph request state; not a live-render guarantee."""

    enabled: bool = False
    vector_field: str | None = None
    scale: float = 1.0
    max_glyph_count: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        max_count = self.max_glyph_count
        object.__setattr__(self, "enabled", bool(self.enabled))
        object.__setattr__(self, "vector_field", _optional_str(self.vector_field))
        object.__setattr__(self, "scale", _positive_float(self.scale))
        object.__setattr__(
            self,
            "max_glyph_count",
            int(max_count) if max_count not in (None, "") else None,
        )
        object.__setattr__(self, "metadata", _string_dict(self.metadata))
        if self.max_glyph_count is not None and self.max_glyph_count <= 0:
            msg = "Scene glyph max count must be positive when provided."
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "vector_field": self.vector_field,
            "scale": self.scale,
            "max_glyph_count": self.max_glyph_count,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> SceneGlyphOptions:
        if not isinstance(data, Mapping):
            msg = "SceneGlyphOptions data must be a mapping."
            raise TypeError(msg)
        return cls(
            enabled=bool(data.get("enabled", False)),
            vector_field=data.get("vector_field"),
            scale=data.get("scale", 1.0),
            max_glyph_count=data.get("max_glyph_count"),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "glyph_options") -> ValidationReport:
        report = ValidationReport()
        if self.enabled and not self.vector_field:
            report.add_error(
                f"{path}.vector_field",
                "Glyph preview requires a selected vector field.",
            )
        if not (isfinite(self.scale) and self.scale > 0.0):
            report.add_error(f"{path}.scale", "Glyph scale must be finite and positive.")
        if self.max_glyph_count is not None and self.max_glyph_count <= 0:
            report.add_error(
                f"{path}.max_glyph_count",
                "Glyph max count must be positive when provided.",
            )
        return report


@dataclass(frozen=True)
class SceneViewState:
    """Serializable 3D workspace view state."""

    camera: SceneCameraState = field(default_factory=SceneCameraState)
    render_options: SceneRenderOptions = field(default_factory=SceneRenderOptions)
    glyph_options: SceneGlyphOptions = field(default_factory=SceneGlyphOptions)
    selected_selection_ids: tuple[str, ...] = ()
    scalar_field_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "camera", _coerce_camera(self.camera))
        object.__setattr__(self, "render_options", _coerce_render_options(self.render_options))
        object.__setattr__(self, "glyph_options", _coerce_glyph_options(self.glyph_options))
        object.__setattr__(self, "selected_selection_ids", _str_tuple(self.selected_selection_ids))
        object.__setattr__(self, "scalar_field_id", _optional_str(self.scalar_field_id))
        object.__setattr__(self, "metadata", _string_dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "camera": self.camera.to_dict(),
            "render_options": self.render_options.to_dict(),
            "glyph_options": self.glyph_options.to_dict(),
            "selected_selection_ids": list(self.selected_selection_ids),
            "scalar_field_id": self.scalar_field_id,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> SceneViewState:
        if not isinstance(data, Mapping):
            msg = "SceneViewState data must be a mapping."
            raise TypeError(msg)
        return cls(
            camera=_coerce_camera(data.get("camera", {})),
            render_options=_coerce_render_options(data.get("render_options", {})),
            glyph_options=_coerce_glyph_options(data.get("glyph_options", {})),
            selected_selection_ids=_str_tuple(data.get("selected_selection_ids", ())),
            scalar_field_id=data.get("scalar_field_id"),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "scene_view") -> ValidationReport:
        report = ValidationReport()
        report.extend(self.camera.validate(path=f"{path}.camera"))
        report.extend(self.render_options.validate(path=f"{path}.render_options"))
        report.extend(self.glyph_options.validate(path=f"{path}.glyph_options"))
        return report


@dataclass(frozen=True)
class SceneScreenshotRecord:
    """Local scene screenshot metadata; not a release asset, not validation evidence."""

    id: str
    path: str
    caption: str | None = None
    scene_state: SceneViewState = field(default_factory=SceneViewState)
    dataset_ref: str | None = None
    mesh_ref: str | None = None
    selection_ids: tuple[str, ...] = ()
    created_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", str(self.id or ""))
        object.__setattr__(self, "path", str(self.path or ""))
        object.__setattr__(self, "caption", _optional_str(self.caption))
        object.__setattr__(self, "scene_state", _coerce_view_state(self.scene_state))
        object.__setattr__(self, "dataset_ref", _optional_str(self.dataset_ref))
        object.__setattr__(self, "mesh_ref", _optional_str(self.mesh_ref))
        object.__setattr__(self, "selection_ids", _str_tuple(self.selection_ids))
        object.__setattr__(self, "created_by", _optional_str(self.created_by))
        object.__setattr__(self, "metadata", _string_dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "caption": self.caption,
            "scene_state": self.scene_state.to_dict(),
            "dataset_ref": self.dataset_ref,
            "mesh_ref": self.mesh_ref,
            "selection_ids": list(self.selection_ids),
            "created_by": self.created_by,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> SceneScreenshotRecord:
        if not isinstance(data, Mapping):
            msg = "SceneScreenshotRecord data must be a mapping."
            raise TypeError(msg)
        return cls(
            id=str(data.get("id", "")),
            path=str(data.get("path", "")),
            caption=data.get("caption"),
            scene_state=_coerce_view_state(data.get("scene_state", {})),
            dataset_ref=data.get("dataset_ref"),
            mesh_ref=data.get("mesh_ref"),
            selection_ids=_str_tuple(data.get("selection_ids", ())),
            created_by=data.get("created_by"),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "scene_screenshot") -> ValidationReport:
        # Model validation only; filesystem existence is a report/export concern.
        report = ValidationReport()
        if not self.id:
            report.add_error(f"{path}.id", "Scene screenshot record id is required.")
        if not self.path:
            report.add_error(f"{path}.path", "Scene screenshot record path is required.")
        report.extend(self.scene_state.validate(path=f"{path}.scene_state"))
        return report


@dataclass(frozen=True)
class SceneInputRef:
    """Reference describing what feeds a scene (mesh / result field / selection)."""

    source_kind: str = "mesh"
    mesh_ref: str | None = None
    result_dataset_ref: str | None = None
    field_id: str | None = None
    selection_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_kind", str(self.source_kind or ""))
        object.__setattr__(self, "mesh_ref", _optional_str(self.mesh_ref))
        object.__setattr__(self, "result_dataset_ref", _optional_str(self.result_dataset_ref))
        object.__setattr__(self, "field_id", _optional_str(self.field_id))
        object.__setattr__(self, "selection_ids", _str_tuple(self.selection_ids))
        object.__setattr__(self, "metadata", _string_dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "mesh_ref": self.mesh_ref,
            "result_dataset_ref": self.result_dataset_ref,
            "field_id": self.field_id,
            "selection_ids": list(self.selection_ids),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> SceneInputRef:
        if not isinstance(data, Mapping):
            msg = "SceneInputRef data must be a mapping."
            raise TypeError(msg)
        return cls(
            source_kind=str(data.get("source_kind", "mesh")),
            mesh_ref=data.get("mesh_ref"),
            result_dataset_ref=data.get("result_dataset_ref"),
            field_id=data.get("field_id"),
            selection_ids=_str_tuple(data.get("selection_ids", ())),
            metadata=_string_dict(data.get("metadata", {})),
        )

    def validate(self, *, path: str = "scene_input") -> ValidationReport:
        report = ValidationReport()
        if not self.source_kind:
            report.add_error(f"{path}.source_kind", "Scene input source_kind is required.")
        elif self.source_kind not in _KNOWN_SOURCE_KINDS:
            report.add_warning(
                f"{path}.source_kind",
                f"Unknown scene input source_kind {self.source_kind!r}.",
            )
        if self.field_id and not self.result_dataset_ref:
            report.add_warning(
                f"{path}.result_dataset_ref",
                "Scene input has a field_id but no result_dataset_ref to resolve it.",
            )
        return report


def _coerce_camera(value: object) -> SceneCameraState:
    if isinstance(value, SceneCameraState):
        return value
    if isinstance(value, Mapping):
        return SceneCameraState.from_dict(value)
    msg = "Scene camera must be a SceneCameraState or mapping."
    raise TypeError(msg)


def _coerce_render_options(value: object) -> SceneRenderOptions:
    if isinstance(value, SceneRenderOptions):
        return value
    if isinstance(value, Mapping):
        return SceneRenderOptions.from_dict(value)
    msg = "Scene render options must be a SceneRenderOptions or mapping."
    raise TypeError(msg)


def _coerce_glyph_options(value: object) -> SceneGlyphOptions:
    if isinstance(value, SceneGlyphOptions):
        return value
    if isinstance(value, Mapping):
        return SceneGlyphOptions.from_dict(value)
    msg = "Scene glyph options must be a SceneGlyphOptions or mapping."
    raise TypeError(msg)


def _coerce_view_state(value: object) -> SceneViewState:
    if isinstance(value, SceneViewState):
        return value
    if isinstance(value, Mapping):
        return SceneViewState.from_dict(value)
    msg = "Scene view state must be a SceneViewState or mapping."
    raise TypeError(msg)


def build_screenshot_record(
    path: str,
    *,
    record_id: str,
    scene_state: SceneViewState | None = None,
    caption: str | None = None,
    dataset_ref: str | None = None,
    mesh_ref: str | None = None,
    selection_ids: Sequence[str] = (),
    created_by: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SceneScreenshotRecord:
    """Assemble a SceneScreenshotRecord from a written local screenshot path."""
    return SceneScreenshotRecord(
        id=record_id,
        path=str(path),
        caption=caption,
        scene_state=scene_state or SceneViewState(),
        dataset_ref=dataset_ref,
        mesh_ref=mesh_ref,
        selection_ids=tuple(str(item) for item in selection_ids),
        created_by=created_by,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "SceneCameraState",
    "SceneGlyphOptions",
    "SceneInputRef",
    "SceneRenderOptions",
    "SceneScreenshotRecord",
    "SceneViewState",
    "build_screenshot_record",
]
