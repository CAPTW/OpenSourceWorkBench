"""Optional PyVista scene bridge for mesh and result previews."""

from __future__ import annotations

from array import array
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

from osw.mesh.mesh_model import MeshCellBlock, MeshData, MeshInfo
from osw.post.field_dataset import FieldRenderRequest, FieldRenderResult
from osw.post.scene_model import (
    SceneScreenshotRecord,
    SceneViewState,
    build_screenshot_record,
)

_SURFACE_CELL_TYPES = frozenset({"triangle", "quad", "polygon"})
_UNSTRUCTURED_CELL_TYPES = frozenset({*_SURFACE_CELL_TYPES, "tetra"})
_FIXED_CELL_NODE_COUNTS = {
    "triangle": 3,
    "quad": 4,
    "tetra": 4,
}
_PYVISTA_CELL_TYPE_NAMES = {
    "triangle": "TRIANGLE",
    "quad": "QUAD",
    "polygon": "POLYGON",
    "tetra": "TETRA",
}


class PyVistaUnavailableError(RuntimeError):
    """Raised when a rendering operation requires the optional PyVista extra."""


@dataclass(frozen=True)
class PyVistaSceneConfig:
    """User-visible visualization options for the basic scene bridge."""

    show_surface: bool = True
    show_edges: bool = False
    show_axes: bool = True
    show_grid: bool = False
    scalar_field: str | None = None
    off_screen: bool = True


@dataclass(frozen=True)
class PyVistaSceneState:
    """Preview state that can be displayed without importing PyVista."""

    mesh_info: MeshInfo
    bounding_box: Any
    show_surface: bool
    show_edges: bool
    show_axes: bool
    show_grid: bool
    scalar_field: str | None
    warnings: tuple[str, ...]
    rendered: bool = False


@dataclass(frozen=True)
class ResultContourPlaceholder:
    scalar_field: str
    available: bool
    warning: str
    dataset_id: str = ""


def pyvista_missing_message() -> str:
    return (
        "PyVista is not installed. Install the optional visualization extra with "
        "`python -m pip install -e .[viz]` before rendering 3D scenes."
    )


def is_pyvista_available() -> bool:
    try:
        _load_pyvista()
    except PyVistaUnavailableError:
        return False
    return True


def build_scene_state(
    mesh_data: MeshData,
    *,
    config: PyVistaSceneConfig | None = None,
    rendered: bool = False,
) -> PyVistaSceneState:
    """Build mesh visualization metadata without requiring PyVista."""

    scene_config = config or PyVistaSceneConfig()
    mesh_info = mesh_data.info(source="<memory>", mesh_format="mesh")
    warnings = _scalar_warnings(mesh_data, scene_config.scalar_field)
    return PyVistaSceneState(
        mesh_info=mesh_info,
        bounding_box=mesh_info.bounding_box,
        show_surface=scene_config.show_surface,
        show_edges=scene_config.show_edges,
        show_axes=scene_config.show_axes,
        show_grid=scene_config.show_grid,
        scalar_field=scene_config.scalar_field,
        warnings=warnings,
        rendered=rendered,
    )


def build_result_contour_placeholder(
    result_dataset: object,
    *,
    scalar_field: str,
) -> ResultContourPlaceholder:
    """Describe future result contour rendering without importing PyVista."""

    return ResultContourPlaceholder(
        scalar_field=scalar_field,
        available=False,
        warning=(
            "PyVista contour rendering for ResultDataset fields is a placeholder "
            "until result-to-mesh field mapping is implemented."
        ),
        dataset_id=str(getattr(result_dataset, "dataset_id", "")),
    )


def render_field_view(
    field_view_model: object,
    request: FieldRenderRequest,
    *,
    pyvista_module: Any | None = None,
    loader: Callable[[], Any] | None = None,
) -> FieldRenderResult:
    """Render a scalar field when PyVista and in-memory mesh geometry are available."""

    if request.mode == "vector" or request.vector_field:
        return FieldRenderResult(
            status="placeholder",
            message="Vector field glyph rendering is deferred for OSW v0.1.",
            request=request,
            diagnostics=("Vector fields are listed as metadata only.",),
        )
    scalar_field = request.scalar_field or _first_scalar_field(field_view_model)
    if not scalar_field:
        return FieldRenderResult(
            status="placeholder",
            message="No scalar field is selected for rendering.",
            request=request,
        )
    mesh_data = getattr(field_view_model, "mesh_data", None)
    scene: PyVistaScene | None = None
    try:
        scene = PyVistaScene(
            config=PyVistaSceneConfig(
                scalar_field=scalar_field,
                off_screen=request.off_screen,
            ),
            pyvista_module=pyvista_module,
            loader=loader,
        )
        if mesh_data is None:
            scene._require_pyvista()
            return FieldRenderResult(
                status="placeholder",
                message=(
                    "Field metadata is available, but no in-memory mesh geometry is "
                    "attached for rendering."
                ),
                request=request,
                diagnostics=("Attach a MeshModel with points/cells for PyVista rendering.",),
            )
        if request.screenshot_path:
            screenshot = scene.export_screenshot(mesh_data, request.screenshot_path)
            return FieldRenderResult(
                status="rendered",
                message=f"Rendered scalar field '{scalar_field}' and exported screenshot.",
                rendered=True,
                request=request,
                screenshot_path=str(screenshot),
            )
        state = scene.add_mesh(mesh_data)
    except PyVistaUnavailableError as exc:
        return FieldRenderResult(
            status="dependency_missing",
            message=str(exc),
            request=request,
            diagnostics=(str(exc),),
        )
    except Exception as exc:  # pragma: no cover - defensive boundary for optional backend.
        return FieldRenderResult(
            status="error",
            message=f"Field rendering failed: {exc}",
            request=request,
            diagnostics=(str(exc),),
        )
    finally:
        if scene is not None:
            scene.close()
    return FieldRenderResult(
        status="rendered",
        message=f"Rendered scalar field '{scalar_field}'.",
        rendered=state.rendered,
        request=request,
    )


def mesh_data_to_pyvista_dataset(
    mesh_data: MeshData,
    *,
    pyvista_module: Any | None = None,
) -> Any:
    """Convert renderable surface/tetra cells to a native PyVista dataset."""

    if not mesh_data.points:
        raise ValueError("PyVista dataset conversion requires non-empty mesh points.")
    populated_types = _populated_cell_types(mesh_data.cells)
    if not populated_types:
        raise ValueError(
            "PyVista dataset conversion requires non-empty triangle, quad, polygon, "
            "or tetra connectivity."
        )
    unsupported = populated_types.difference(_UNSTRUCTURED_CELL_TYPES)
    if unsupported:
        raise ValueError("Unsupported PyVista cell types: " + ", ".join(sorted(unsupported)) + ".")
    if "tetra" not in populated_types:
        return mesh_data_to_polydata(mesh_data, pyvista_module=pyvista_module)

    blocks = _validated_cell_blocks(
        mesh_data,
        supported_types=_UNSTRUCTURED_CELL_TYPES,
        conversion_name="PyVista UnstructuredGrid conversion",
    )
    point_fields = _validated_point_fields(mesh_data)
    cell_fields = _validated_cell_fields(mesh_data, blocks)
    module = pyvista_module if pyvista_module is not None else _load_pyvista()
    cells = array("q")
    cell_types = array("B")
    for block in blocks:
        vtk_cell_type = _pyvista_cell_type(module, block.cell_type)
        for row in block.data:
            cells.extend((len(row), *row))
            cell_types.append(vtk_cell_type)
    dataset = module.UnstructuredGrid(
        cells,
        cell_types,
        [list(point) for point in mesh_data.points],
    )
    _attach_mesh_fields(dataset, point_fields=point_fields, cell_fields=cell_fields)
    return dataset


def mesh_data_to_polydata(mesh_data: MeshData, *, pyvista_module: Any | None = None) -> Any:
    """Convert supported surface cells to the compatibility ``PolyData`` path."""

    if not mesh_data.points:
        raise ValueError("PyVista surface conversion requires non-empty mesh points.")
    populated_types = _populated_cell_types(mesh_data.cells)
    unsupported = populated_types.difference(_SURFACE_CELL_TYPES)
    if unsupported:
        raise ValueError(
            "Unsupported cell types for PyVista PolyData conversion: "
            + ", ".join(sorted(unsupported))
            + "."
        )
    blocks = _validated_cell_blocks(
        mesh_data,
        supported_types=_SURFACE_CELL_TYPES,
        conversion_name="PyVista PolyData conversion",
    )
    faces = _surface_faces(blocks)
    if not faces:
        raise ValueError(
            "PyVista surface conversion requires non-empty triangle, quad, or polygon connectivity."
        )
    point_fields = _validated_point_fields(mesh_data)
    cell_fields = _validated_cell_fields(mesh_data, blocks)
    module = pyvista_module if pyvista_module is not None else _load_pyvista()
    dataset = module.PolyData([list(point) for point in mesh_data.points], faces)
    _attach_mesh_fields(dataset, point_fields=point_fields, cell_fields=cell_fields)
    return dataset


class PyVistaScene:
    """Small optional rendering adapter isolated from solver-specific formats."""

    def __init__(
        self,
        *,
        config: PyVistaSceneConfig | None = None,
        pyvista_module: Any | None = None,
        loader: Callable[[], Any] | None = None,
    ) -> None:
        self.config = config or PyVistaSceneConfig()
        self._pyvista_module = pyvista_module
        self._loader = loader or _load_pyvista
        self._plotter: Any | None = None

    def add_mesh(self, mesh_data: MeshData) -> PyVistaSceneState:
        self.close()
        module = self._require_pyvista()
        dataset = mesh_data_to_pyvista_dataset(mesh_data, pyvista_module=module)
        self._attach_scalar_field(dataset, mesh_data)

        plotter = module.Plotter(off_screen=self.config.off_screen)
        self._plotter = plotter
        try:
            if self.config.show_surface:
                scalars = (
                    self.config.scalar_field
                    if _has_scalar(mesh_data, self.config.scalar_field)
                    else None
                )
                plotter.add_mesh(
                    dataset,
                    show_edges=self.config.show_edges,
                    scalars=scalars,
                )
            if self.config.show_axes and hasattr(plotter, "add_axes"):
                plotter.add_axes()
            if self.config.show_grid and hasattr(plotter, "show_grid"):
                plotter.show_grid()
        except Exception:
            self.close()
            raise

        return build_scene_state(mesh_data, config=self.config, rendered=True)

    def export_screenshot(self, mesh_data: MeshData, target_path: str | Path) -> Path:
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.add_mesh(mesh_data)
            if self._plotter is None or not hasattr(self._plotter, "screenshot"):
                msg = "PyVista plotter does not provide screenshot export in this environment."
                raise PyVistaUnavailableError(msg)
            self._plotter.screenshot(str(target))
            return target
        finally:
            self.close()

    def close(self) -> None:
        """Close the current Plotter exactly once and release the reference."""

        plotter = self._plotter
        self._plotter = None
        if plotter is None:
            return
        close = getattr(plotter, "close", None)
        if callable(close):
            close()

    def _require_pyvista(self) -> Any:
        if self._pyvista_module is not None:
            return self._pyvista_module
        module = self._loader()
        if module is None:
            raise PyVistaUnavailableError(pyvista_missing_message())
        self._pyvista_module = module
        return module

    def _attach_scalar_field(self, dataset: Any, mesh_data: MeshData) -> None:
        scalar_field = self.config.scalar_field
        if not _has_scalar(mesh_data, scalar_field):
            return
        values = mesh_data.point_data.get(scalar_field)
        if values is not None and hasattr(dataset, "point_data"):
            dataset.point_data[scalar_field] = values


def export_screenshot_record(
    mesh_data: MeshData,
    target_path: str | Path,
    *,
    record_id: str,
    scene_state: SceneViewState | None = None,
    caption: str | None = None,
    dataset_ref: str | None = None,
    mesh_ref: str | None = None,
    selection_ids: Sequence[str] = (),
    created_by: str | None = None,
    pyvista_module: Any | None = None,
    loader: Callable[[], Any] | None = None,
) -> SceneScreenshotRecord:
    """Render an off-screen screenshot and return its local metadata record.

    The scene camera state is *recorded* in the returned record's scene_state
    but, for the MVP, is not applied to the plotter (that requires real PyVista
    camera behavior and is deferred). PyVista stays optional and lazy: a fake
    module/loader can be injected for tests, and a missing PyVista raises the
    usual friendly ``PyVistaUnavailableError``. The written path is local
    artifact metadata only -- not a release asset and not validation evidence.
    """
    if scene_state is not None:
        config = PyVistaSceneConfig(**scene_state.render_options.to_pyvista_config_dict())
    else:
        config = PyVistaSceneConfig(off_screen=True)
    scene = PyVistaScene(config=config, pyvista_module=pyvista_module, loader=loader)
    try:
        written = scene.export_screenshot(mesh_data, target_path)
    finally:
        scene.close()
    return build_screenshot_record(
        str(written),
        record_id=record_id,
        scene_state=scene_state or SceneViewState(),
        caption=caption,
        dataset_ref=dataset_ref,
        mesh_ref=mesh_ref,
        selection_ids=selection_ids,
        created_by=created_by,
    )


def _load_pyvista() -> ModuleType:
    try:
        return import_module("pyvista")
    except ImportError as exc:
        raise PyVistaUnavailableError(pyvista_missing_message()) from exc


def _surface_faces(cells: Sequence[MeshCellBlock]) -> list[int]:
    faces: list[int] = []
    for block in cells:
        if block.cell_type not in {"triangle", "quad", "polygon"}:
            continue
        for row in block.data:
            faces.extend([len(row), *row])
    return faces


def _populated_cell_types(cells: Sequence[MeshCellBlock]) -> frozenset[str]:
    return frozenset(block.cell_type for block in cells if block.count > 0 or bool(block.data))


def _validated_cell_blocks(
    mesh_data: MeshData,
    *,
    supported_types: frozenset[str],
    conversion_name: str,
) -> tuple[MeshCellBlock, ...]:
    blocks = tuple(block for block in mesh_data.cells if block.count > 0 or bool(block.data))
    if not blocks:
        raise ValueError(f"{conversion_name} requires non-empty connectivity.")
    unsupported = {block.cell_type for block in blocks}.difference(supported_types)
    if unsupported:
        raise ValueError(
            f"Unsupported cell types for {conversion_name}: " + ", ".join(sorted(unsupported)) + "."
        )
    point_count = len(mesh_data.points)
    for block in blocks:
        if block.count != len(block.data):
            raise ValueError(
                f"{conversion_name} cell block '{block.cell_type}' declares "
                f"{block.count} cells but provides {len(block.data)} connectivity rows."
            )
        for row in block.data:
            expected = _FIXED_CELL_NODE_COUNTS.get(block.cell_type)
            if expected is not None and len(row) != expected:
                raise ValueError(
                    f"{conversion_name} cell type '{block.cell_type}' requires "
                    f"{expected} point indices; received {len(row)}."
                )
            if block.cell_type == "polygon" and len(row) < 3:
                raise ValueError(
                    f"{conversion_name} polygon cells require at least 3 point indices."
                )
            invalid_indices = tuple(index for index in row if not 0 <= index < point_count)
            if invalid_indices:
                raise ValueError(
                    f"{conversion_name} cell type '{block.cell_type}' contains "
                    f"out-of-range point indices: {invalid_indices}."
                )
    return blocks


def _pyvista_cell_type(module: Any, cell_type: str) -> int:
    cell_type_enum = getattr(module, "CellType", None)
    enum_name = _PYVISTA_CELL_TYPE_NAMES[cell_type]
    value = getattr(cell_type_enum, enum_name, None)
    if value is None:
        raise RuntimeError(f"PyVista does not expose the required CellType.{enum_name} value.")
    return int(value)


def _validated_point_fields(mesh_data: MeshData) -> dict[str, object]:
    point_count = len(mesh_data.points)
    fields: dict[str, object] = {}
    for name, values in mesh_data.point_data.items():
        actual = _field_length(values, association="Point", name=name)
        if actual != point_count:
            raise ValueError(
                f"Point data field '{name}' has {actual} values; expected {point_count}."
            )
        fields[name] = values
    return fields


def _validated_cell_fields(
    mesh_data: MeshData,
    blocks: Sequence[MeshCellBlock],
) -> dict[str, object]:
    block_counts = tuple(len(block.data) for block in blocks)
    cell_count = sum(block_counts)
    fields: dict[str, object] = {}
    for name, values in mesh_data.cell_data.items():
        actual = _field_length(values, association="Cell", name=name)
        if actual == len(block_counts) and _is_blockwise_cell_field(values, block_counts):
            fields[name] = tuple(item for block_values in values for item in block_values)
            continue
        if actual != cell_count:
            raise ValueError(
                f"Cell data field '{name}' has {actual} values; expected {cell_count}."
            )
        fields[name] = values
    return fields


def _field_length(values: object, *, association: str, name: str) -> int:
    try:
        return len(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{association} data field '{name}' must be a sized sequence.") from exc


def _is_blockwise_cell_field(values: object, block_counts: Sequence[int]) -> bool:
    try:
        return all(
            len(block_values) == expected_count
            for block_values, expected_count in zip(values, block_counts, strict=True)  # type: ignore[arg-type]
        )
    except (TypeError, ValueError):
        return False


def _attach_mesh_fields(
    dataset: Any,
    *,
    point_fields: dict[str, object],
    cell_fields: dict[str, object],
) -> None:
    for name, values in point_fields.items():
        dataset.point_data[name] = values
    for name, values in cell_fields.items():
        dataset.cell_data[name] = values


def _has_scalar(mesh_data: MeshData, scalar_field: str | None) -> bool:
    if scalar_field is None:
        return False
    return scalar_field in mesh_data.point_data or scalar_field in mesh_data.cell_data


def _first_scalar_field(field_view_model: object) -> str:
    fields = getattr(field_view_model, "scalar_fields", ()) or ()
    return str(fields[0]) if fields else ""


def _scalar_warnings(mesh_data: MeshData, scalar_field: str | None) -> tuple[str, ...]:
    if scalar_field is None or _has_scalar(mesh_data, scalar_field):
        return ()
    return (f"Scalar field '{scalar_field}' is not present on the mesh.",)
