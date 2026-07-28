"""Qt-free view-model helpers for the 3D workspace mesh viewer panel.

This module maps :class:`~osw.mesh.mesh_model.MeshData` / ``MeshInfo`` onto the
reviewed post-level scene shell (``SceneInputRef``, ``SceneViewState``,
``SceneScreenshotRecord``). It imports no GUI toolkit and no rendering package:
mapping is pure, and rendering is delegated to an injected scene adapter so the
helpers stay unit-testable without PySide6.

Rendering stays optional and lazy. The default adapter reaches PyVista only
through :mod:`osw.post.pyvista_scene`, which loads the package on demand; a
missing PyVista surfaces a friendly status instead of a crash. A local scene
screenshot is artifact metadata only -- it is not a release asset and not
validation evidence. This module runs no external process and no solver.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from math import isfinite
from typing import Any, Protocol, runtime_checkable

from osw.mesh.mesh_model import MeshData, MeshInfo
from osw.post.pyvista_scene import (
    PyVistaSceneConfig,
    build_scene_state,
    export_screenshot_record,
)
from osw.post.scene_model import (
    SceneGlyphOptions,
    SceneInputRef,
    SceneRenderOptions,
    SceneScreenshotRecord,
    SceneViewState,
)

_MEMORY_SOURCE = "<memory>"


def mesh_input_ref(
    mesh_ref: str | None,
    selection_ids: Sequence[str] = (),
    *,
    result_dataset_ref: str | None = None,
    field_id: str | None = None,
) -> SceneInputRef:
    """Build a mesh-sourced :class:`SceneInputRef` (``source_kind='mesh'``).

    ``result_dataset_ref``/``field_id`` optionally record the provenance of a
    result field mapped onto the mesh as an overlay scalar (additive metadata;
    the source kind stays ``'mesh'`` because the geometry is still the mesh).
    """
    return SceneInputRef(
        source_kind="mesh",
        mesh_ref=mesh_ref or None,
        result_dataset_ref=result_dataset_ref or None,
        field_id=field_id or None,
        selection_ids=tuple(str(item) for item in selection_ids),
    )


def scene_view_state_from_toggles(
    *,
    show_surface: bool = True,
    show_edges: bool = False,
    show_axes: bool = True,
    show_grid: bool = False,
    color_by: str | None = None,
    glyph_enabled: bool = False,
    glyph_vector_field: str | None = None,
    glyph_scale: float = 1.0,
    glyph_max_count: int | None = None,
    selected_selection_ids: Sequence[str] = (),
) -> SceneViewState:
    """Build a :class:`SceneViewState` from simple render toggles.

    ``color_by`` is the scalar field name to color the mesh by (or ``None`` for
    no coloring); it is recorded on ``SceneRenderOptions.color_by`` (which the
    scene shell maps to ``PyVistaSceneConfig.scalar_field``) and on
    ``SceneViewState.scalar_field_id``.
    """
    resolved_color_by = color_by or None
    resolved_vector_field = glyph_vector_field or None
    return SceneViewState(
        render_options=SceneRenderOptions(
            show_surface=bool(show_surface),
            show_edges=bool(show_edges),
            show_axes=bool(show_axes),
            show_grid=bool(show_grid),
            color_by=resolved_color_by,
        ),
        glyph_options=SceneGlyphOptions(
            enabled=bool(glyph_enabled and resolved_vector_field),
            vector_field=resolved_vector_field if glyph_enabled else None,
            scale=glyph_scale,
            max_glyph_count=glyph_max_count,
        ),
        scalar_field_id=resolved_color_by,
        selected_selection_ids=tuple(str(item) for item in selected_selection_ids),
    )


def mesh_scalar_field_names(mesh: MeshData | None) -> tuple[str, ...]:
    """Return the mesh's colorable scalar field names (no PyVista needed).

    Combines ``point_data`` and ``cell_data`` array names (order preserved,
    de-duplicated). ``field_data`` is global metadata, not a per-node/cell
    scalar, so it is excluded. Returns ``()`` when there is no mesh or no fields.
    """
    if mesh is None:
        return ()
    names: list[str] = []
    seen: set[str] = set()
    for data_map in (mesh.point_data, mesh.cell_data):
        for name, values in data_map.items():
            if _is_vector_array(values):
                continue
            if name not in seen:
                seen.add(name)
                names.append(name)
    return tuple(names)


def mesh_vector_field_names(mesh: MeshData | None) -> tuple[str, ...]:
    """Return compatible per-node/cell 3-component vector array names."""
    if mesh is None:
        return ()
    names: list[str] = []
    seen: set[str] = set()
    for data_map in (mesh.point_data, mesh.cell_data):
        for name, values in data_map.items():
            if not _is_vector_array(values):
                continue
            if name not in seen:
                seen.add(name)
                names.append(name)
    return tuple(names)


def mesh_summary_rows(mesh: MeshData | None) -> tuple[tuple[str, str], ...]:
    """Return label/value display rows summarizing a mesh (no PyVista needed)."""
    if mesh is None:
        return (("Mesh", "No mesh loaded."),)
    info: MeshInfo = mesh.info(source=_MEMORY_SOURCE, mesh_format="mesh")
    cell_types = ", ".join(info.cell_types) or "none"
    bounds = info.bounds
    return (
        ("Nodes", str(info.node_count)),
        ("Elements", str(info.element_count)),
        ("Cell types", cell_types),
        ("Bounds min", _format_point(bounds.minimum)),
        ("Bounds max", _format_point(bounds.maximum)),
    )


@dataclass
class MeshViewerState:
    """Transient GUI state for the mesh viewer panel; never persisted."""

    mesh: MeshData | None = None
    mesh_ref: str = ""
    scene_input: SceneInputRef | None = None
    scene_state: SceneViewState = field(default_factory=SceneViewState)
    selected_selection_ids: tuple[str, ...] = ()
    summary_rows: tuple[tuple[str, str], ...] = ()
    status_message: str = ""
    error_message: str | None = None
    warning_messages: tuple[str, ...] = ()
    pyvista_available: bool | None = None
    screenshot_record: SceneScreenshotRecord | None = None


@runtime_checkable
class SceneAdapterProtocol(Protocol):
    """Injection seam for mesh preview and screenshot-record capture.

    Implementations must not run any external process or solver. The default
    implementation renders (when asked) only through the optional PyVista
    bridge; tests inject a recording fake so no live rendering is required.
    """

    def load_mesh(
        self,
        mesh: MeshData,
        scene_input: SceneInputRef,
        scene_state: SceneViewState,
    ) -> Any:
        ...

    def set_view_state(self, scene_state: SceneViewState) -> None:
        ...

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
        ...


class DefaultSceneAdapter:
    """Scene adapter backed by the optional PyVista scene bridge.

    PyVista stays optional and lazy: nothing here imports the ``pyvista``
    package at import time -- :mod:`osw.post.pyvista_scene` loads it on demand,
    and a fake module/loader can be injected for tests. ``load_mesh`` builds the
    PyVista-free summary state only (a live plotter is deferred to a later
    slice), so previewing a mesh never requires PyVista. Only
    ``export_screenshot_record`` reaches a real renderer, and a missing PyVista
    raises the friendly ``PyVistaUnavailableError`` for the panel to present.
    """

    def __init__(
        self,
        *,
        pyvista_module: Any | None = None,
        loader: Any | None = None,
    ) -> None:
        self._pyvista_module = pyvista_module
        self._loader = loader
        self._scene_input: SceneInputRef | None = None
        self._scene_state = SceneViewState()

    def load_mesh(
        self,
        mesh: MeshData,
        scene_input: SceneInputRef,
        scene_state: SceneViewState,
    ) -> Any:
        self._scene_input = scene_input
        self._scene_state = scene_state
        config = PyVistaSceneConfig(**scene_state.render_options.to_pyvista_config_dict())
        return build_scene_state(mesh, config=config, rendered=False)

    def set_view_state(self, scene_state: SceneViewState) -> None:
        self._scene_state = scene_state

    def clear(self) -> None:
        """Release transient logical scene references (no native renderer is retained)."""

        self._scene_input = None
        self._scene_state = SceneViewState()

    def close(self) -> None:
        """Idempotently clear this compatibility adapter."""

        self.clear()

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
        return export_screenshot_record(
            mesh,
            path,
            record_id=record_id,
            scene_state=scene_state,
            caption=caption,
            mesh_ref=mesh_ref,
            selection_ids=selection_ids,
            created_by=created_by,
            pyvista_module=self._pyvista_module,
            loader=self._loader,
        )


def summary_rows_to_text(rows: Sequence[tuple[str, str]]) -> str:
    """Render label/value rows as a multi-line summary string."""
    return "\n".join(f"{label}: {value}" for label, value in rows)


def _format_point(point: Sequence[float]) -> str:
    return "(" + ", ".join(f"{float(value):.6g}" for value in point) + ")"


def _tuple_or_none(value: object) -> tuple[object, ...] | None:
    if isinstance(value, (str, bytes)):
        return None
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError:
        return None


def _is_vector_array(values: object) -> bool:
    rows = _tuple_or_none(values)
    if not rows:
        return False
    for row in rows:
        components = _tuple_or_none(row)
        if components is None or len(components) != 3:
            return False
        try:
            if not all(isfinite(float(component)) for component in components):
                return False
        except (TypeError, ValueError, OverflowError):
            return False
    return True


__all__ = [
    "DefaultSceneAdapter",
    "MeshViewerState",
    "SceneAdapterProtocol",
    "mesh_input_ref",
    "mesh_scalar_field_names",
    "mesh_summary_rows",
    "mesh_vector_field_names",
    "scene_view_state_from_toggles",
    "summary_rows_to_text",
]
