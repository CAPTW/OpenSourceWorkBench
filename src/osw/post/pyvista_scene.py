"""Optional PyVista scene bridge for mesh and result previews."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

from osw.mesh.mesh_model import MeshCellBlock, MeshData, MeshInfo
from osw.post.field_dataset import FieldRenderRequest, FieldRenderResult


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
    return FieldRenderResult(
        status="rendered",
        message=f"Rendered scalar field '{scalar_field}'.",
        rendered=state.rendered,
        request=request,
    )


def mesh_data_to_polydata(mesh_data: MeshData, *, pyvista_module: Any | None = None) -> Any:
    """Convert supported surface cell blocks to a PyVista PolyData-like object."""

    module = pyvista_module if pyvista_module is not None else _load_pyvista()
    points = [list(point) for point in mesh_data.points]
    faces = _surface_faces(mesh_data.cells)
    return module.PolyData(points, faces)


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
        module = self._require_pyvista()
        dataset = mesh_data_to_polydata(mesh_data, pyvista_module=module)
        self._attach_scalar_field(dataset, mesh_data)

        plotter = module.Plotter(off_screen=self.config.off_screen)
        self._plotter = plotter
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

        return build_scene_state(mesh_data, config=self.config, rendered=True)

    def export_screenshot(self, mesh_data: MeshData, target_path: str | Path) -> Path:
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.add_mesh(mesh_data)
        if self._plotter is None or not hasattr(self._plotter, "screenshot"):
            msg = "PyVista plotter does not provide screenshot export in this environment."
            raise PyVistaUnavailableError(msg)
        self._plotter.screenshot(str(target))
        return target

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


def _load_pyvista() -> ModuleType:
    try:
        return import_module("pyvista")
    except ImportError as exc:
        raise PyVistaUnavailableError(pyvista_missing_message()) from exc


def _surface_faces(cells: tuple[MeshCellBlock, ...]) -> list[int]:
    faces: list[int] = []
    for block in cells:
        if block.cell_type not in {"triangle", "quad", "polygon"}:
            continue
        for row in block.data:
            faces.extend([len(row), *row])
    return faces


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
