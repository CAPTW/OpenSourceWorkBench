"""Lazy PyVista/VTK provider for the Scaled Jacobian product metric."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from osw.post.pyvista_scene import mesh_data_to_pyvista_dataset

from .mesh_model import MeshData
from .quality import MeshQualityProviderError, MeshQualityProviderUnavailableError


class PyVistaScaledJacobianProvider:
    """Evaluate the exact retained ``DataSetFilters.cell_quality`` operation."""

    provider_schema = "osw.mesh_quality.provider.pyvista_vtk.v1"

    def __init__(self, *, pyvista_module: Any | None = None) -> None:
        self._pyvista = pyvista_module

    @property
    def provider_version(self) -> str:
        pyvista = self._require_pyvista()
        vtk_version = "unknown"
        try:
            vtk = import_module("vtk")
            vtk_version = str(vtk.vtkVersion.GetVTKVersion())
        except (ModuleNotFoundError, AttributeError):
            pass
        return f"pyvista-{getattr(pyvista, '__version__', 'unknown')};vtk-{vtk_version}"

    def evaluate(self, mesh: MeshData) -> tuple[float, ...]:
        pyvista = self._require_pyvista()
        try:
            dataset = mesh_data_to_pyvista_dataset(mesh, pyvista_module=pyvista)
            operation = getattr(dataset, "cell_quality", None)
            if not callable(operation):
                raise MeshQualityProviderError(
                    "The retained PyVista dataset has no cell_quality operation."
                )
            evaluated = operation(
                quality_measure="scaled_jacobian",
                null_value=float("nan"),
            )
            values = evaluated.cell_data.get("scaled_jacobian")
            if values is None:
                raise MeshQualityProviderError(
                    "PyVista did not return the scaled_jacobian cell array."
                )
            return tuple(float(value) for value in values)
        except MeshQualityProviderError:
            raise
        except Exception as exc:
            raise MeshQualityProviderError(
                f"PyVista Scaled Jacobian evaluation failed: {type(exc).__name__}: {exc}"
            ) from exc

    def _require_pyvista(self) -> Any:
        if self._pyvista is not None:
            return self._pyvista
        try:
            self._pyvista = import_module("pyvista")
        except ModuleNotFoundError as exc:
            raise MeshQualityProviderUnavailableError(
                "Scaled Jacobian is unavailable because the optional PyVista/VTK "
                "post-processing extra is not installed."
            ) from exc
        return self._pyvista


__all__ = ["PyVistaScaledJacobianProvider"]
