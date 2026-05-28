"""Runner-backed Gmsh adapter for bounded primitive mesh generation."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticCode, DiagnosticReport
from osw.core.executables import ExecutablePathRegistry, ExecutableResolution
from osw.core.project_schema import MeshRef
from osw.solvers.runner import ExternalCommandRunner, RunRequest, RunStatus, TimeoutPolicy

from .gmsh_geometry import (
    GmshGeometryError,
    default_box_request,
    default_physical_groups,
    generate_geo_script,
    geometry_spec_from_project,
    write_geo_script,
)
from .gmsh_model import (
    GmshGeometryKind,
    GmshGeometrySpec,
    GmshMeshDimension,
    GmshMeshRequest,
    GmshMeshResult,
    GmshMeshSizeField,
    GmshMeshStatus,
    GmshPhysicalGroup,
)
from .mesh_model import MeshData, MeshInfo
from .meshio_bridge import MeshImportStatus, export_vtu, load_mesh, load_mesh_info, read_mesh


class GmshAdapterError(RuntimeError):
    """Raised by legacy compatibility helpers when Gmsh cannot proceed."""


MeshSizeControl = GmshMeshSizeField
PhysicalGroupMetadata = GmshPhysicalGroup


class GmshPrimitive(GmshGeometrySpec):
    """Compatibility wrapper for primitive geometry specs."""

    @classmethod
    def plate(
        cls,
        *,
        width: float,
        height: float,
        name: str = "plate",
        units: str = "",
    ) -> GmshPrimitive:
        return cls(
            GmshGeometryKind.RECTANGLE,
            {"width": width, "height": height},
            geometry_id=name,
            units=units,
        )

    @classmethod
    def rectangle(
        cls,
        *,
        width: float,
        height: float,
        name: str = "rectangle",
        units: str = "",
    ) -> GmshPrimitive:
        return cls.plate(width=width, height=height, name=name, units=units)

    @classmethod
    def box(
        cls,
        *,
        width: float,
        depth: float | None = None,
        height: float,
        length: float | None = None,
        name: str = "box",
        units: str = "",
    ) -> GmshPrimitive:
        resolved_length = float(length if length is not None else width)
        resolved_width = float(depth if depth is not None else width)
        return cls(
            GmshGeometryKind.BOX,
            {"length": resolved_length, "width": resolved_width, "height": height},
            geometry_id=name,
            units=units,
        )


def find_gmsh_executable(
    registry: ExecutablePathRegistry | None = None,
) -> ExecutableResolution:
    """Resolve Gmsh without executing it."""

    resolver = registry or ExecutablePathRegistry()
    names = ("gmsh", "gmsh.exe") if os.name == "nt" else ("gmsh",)
    resolution = resolver.resolve_any(names)
    if resolution.found:
        return resolution
    report = DiagnosticReport()
    report.add_error(
        "gmsh-executable-not-found",
        "Gmsh executable was not found.",
        hint="Install Gmsh or configure the executable path in Plugin Manager.",
        field="gmsh",
    )
    return ExecutableResolution("gmsh", None, "missing", report)


def gmsh_available(registry: ExecutablePathRegistry | None = None) -> bool:
    return find_gmsh_executable(registry).found


def is_gmsh_available(registry: ExecutablePathRegistry | None = None) -> bool:
    return gmsh_available(registry)


class GmshAdapter:
    """Generate primitive Gmsh cases and run Gmsh through ExternalCommandRunner."""

    def __init__(
        self,
        executable_registry: ExecutablePathRegistry | None = None,
        command_runner: ExternalCommandRunner | None = None,
        *,
        executable_name: str = "gmsh",
        command_prefix: tuple[str, ...] = (),
    ) -> None:
        self.executable_registry = executable_registry or ExecutablePathRegistry()
        self.command_runner = command_runner or ExternalCommandRunner(
            registry=self.executable_registry
        )
        self.executable_name = executable_name
        self.command_prefix = tuple(str(part) for part in command_prefix)

    def validate_request(self, request: GmshMeshRequest) -> DiagnosticReport:
        report = DiagnosticReport()
        if request.timeout_seconds <= 0:
            report.add_error(
                "gmsh-timeout-invalid",
                "Gmsh timeout must be greater than zero seconds.",
                hint="Use a positive timeout value.",
            )
        if request.geometry.kind is GmshGeometryKind.UNKNOWN:
            report.add_error(
                "gmsh-geometry-kind-unsupported",
                "Gmsh geometry kind is unknown.",
                hint="Choose rectangle, box, cylinder, sphere, or plate_with_hole.",
            )
        return report

    def build_gmsh_command(
        self,
        request: GmshMeshRequest,
        geo_path: str | Path,
        output_msh_path: str | Path,
    ) -> list[str]:
        return [
            self.executable_name,
            *self.command_prefix,
            str(geo_path),
            f"-{request.mesh_dimension.numeric}",
            "-format",
            "msh2",
            "-o",
            str(output_msh_path),
        ]

    def generate_mesh(self, request: GmshMeshRequest) -> GmshMeshResult:
        """Generate a mesh explicitly through the backend runner boundary."""

        diagnostics = self.validate_request(request)
        output_dir = request.output_dir.expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        geo_path = output_dir / request.geo_filename
        msh_path = output_dir / request.msh_filename
        run_id = request.run_id or f"gmsh-{uuid.uuid4().hex[:12]}"
        physical_groups = _physical_groups_for_request(request)

        try:
            if request.write_geo:
                write_geo_script(request, geo_path)
            else:
                geo_path.write_text(generate_geo_script(request), encoding="utf-8", newline="\n")
        except (GmshGeometryError, ValueError) as exc:
            diagnostics.add_error(
                "gmsh-geo-generation-failed",
                str(exc),
                hint="Check primitive geometry parameters before running Gmsh.",
                path=geo_path,
            )
            return GmshMeshResult(
                GmshMeshStatus.ERROR,
                request,
                geo_path=geo_path if geo_path.exists() else None,
                physical_groups=physical_groups,
                diagnostics=diagnostics,
            )

        resolution = find_gmsh_executable(self.executable_registry)
        if not resolution.found:
            diagnostics.extend(resolution.diagnostics)
            artifacts = (RunArtifact(geo_path, "geo", "Generated Gmsh script.", "geo"),)
            return GmshMeshResult(
                GmshMeshStatus.DEPENDENCY_MISSING,
                request,
                geo_path=geo_path,
                physical_groups=physical_groups,
                diagnostics=diagnostics,
                artifacts=artifacts,
            )

        command = self.build_gmsh_command(request, geo_path, msh_path)
        run_result = self.command_runner.run(
            RunRequest(
                command,
                cwd=output_dir,
                timeout_policy=TimeoutPolicy(timeout_seconds=request.timeout_seconds),
                artifact_patterns=(request.geo_filename, request.msh_filename),
                run_id=run_id,
                metadata={"adapter": "osw.gmsh", "request": request.to_dict()},
                artifact_dir=output_dir,
            )
        )
        diagnostics.extend(run_result.diagnostics)

        if run_result.status is RunStatus.TIMED_OUT:
            return _result(
                GmshMeshStatus.TIMED_OUT,
                request,
                geo_path,
                msh_path,
                physical_groups,
                diagnostics,
                run_result,
            )
        if run_result.status is RunStatus.MISSING_EXECUTABLE:
            return _result(
                GmshMeshStatus.DEPENDENCY_MISSING,
                request,
                geo_path,
                msh_path,
                physical_groups,
                diagnostics,
                run_result,
            )
        if run_result.status is not RunStatus.COMPLETED:
            return _result(
                GmshMeshStatus.ERROR,
                request,
                geo_path,
                msh_path,
                physical_groups,
                diagnostics,
                run_result,
            )
        if not msh_path.exists():
            diagnostics.add_error(
                "gmsh-msh-artifact-missing",
                "Gmsh completed but the expected .msh artifact was not produced.",
                hint="Inspect stdout/stderr and the requested output path.",
                path=msh_path,
            )
            return _result(
                GmshMeshStatus.ERROR,
                request,
                geo_path,
                msh_path,
                physical_groups,
                diagnostics,
                run_result,
            )

        mesh_model = None
        mesh_info = None
        converted_path = None
        status = GmshMeshStatus.OK
        if request.convert_to_vtu:
            read_result = read_mesh(msh_path)
            diagnostics.extend(read_result.diagnostics)
            if read_result.mesh is None:
                status = GmshMeshStatus.WARNING
            else:
                mesh_model = read_result.mesh
                mesh_info = read_result.mesh.info
                export_result = _write_converted_vtu(
                    mesh_model.to_mesh_data(),
                    output_dir / request.vtu_filename,
                )
                diagnostics.extend(export_result[1])
                converted_path = export_result[0]
                if converted_path is None:
                    status = GmshMeshStatus.WARNING
        else:
            read_result = read_mesh(msh_path)
            if read_result.mesh is not None:
                mesh_model = read_result.mesh
                mesh_info = read_result.mesh.info
            elif read_result.status is MeshImportStatus.DEPENDENCY_MISSING:
                diagnostics.extend(read_result.diagnostics)
                status = GmshMeshStatus.WARNING

        artifacts = _dedupe_artifacts(
            (
                *run_result.artifacts,
                RunArtifact(geo_path, "geo", "Generated Gmsh script.", "geo"),
                RunArtifact(msh_path, "msh", "Generated Gmsh mesh artifact.", "msh"),
                *(
                    (RunArtifact(converted_path, "vtu", "Converted mesh preview.", "vtu"),)
                    if converted_path is not None
                    else ()
                ),
            )
        )
        return GmshMeshResult(
            status,
            request,
            geo_path=geo_path,
            msh_path=msh_path,
            converted_mesh_path=converted_path,
            mesh_model=mesh_model,
            mesh_info=mesh_info,
            physical_groups=physical_groups,
            diagnostics=diagnostics,
            run_result=run_result,
            artifacts=artifacts,
        )

    def generate_mesh_from_project(
        self,
        project: object,
        request_overrides: dict[str, Any] | None = None,
    ) -> GmshMeshResult:
        spec, report = geometry_spec_from_project(project)
        overrides = dict(request_overrides or {})
        output_dir = overrides.pop("output_dir", Path("artifacts") / "mesh")
        request = default_box_request(output_dir) if spec is None else GmshMeshRequest(
            geometry=spec,
            output_dir=output_dir,
            output_name=overrides.pop("output_name", spec.geometry_id or "gmsh_mesh"),
            **overrides,
        )
        result = self.generate_mesh(request)
        result.diagnostics.extend(report)
        return result

    def convert_result_to_mesh_ref(
        self,
        result: GmshMeshResult,
        project_relative_path: str | None = None,
    ) -> MeshRef:
        return convert_result_to_mesh_ref(result, project_relative_path=project_relative_path)


def convert_result_to_mesh_ref(
    result: GmshMeshResult,
    project_relative_path: str | None = None,
) -> MeshRef:
    path = result.converted_mesh_path or result.msh_path or result.geo_path or Path("")
    mesh_info = result.mesh_info.to_dict() if result.mesh_info is not None else None
    metadata = {
        "generated_by": "osw.gmsh",
        "generation": result.request.to_dict(),
        "physical_groups": [group.to_dict() for group in result.physical_groups],
        "diagnostics": result.diagnostics.to_dict(),
    }
    if mesh_info is not None:
        metadata["mesh_info"] = mesh_info
    return MeshRef(
        id=result.request.output_name,
        name=Path(path).name,
        path=project_relative_path or str(path),
        format=Path(path).suffix.lstrip("."),
        status=(
            "generated"
            if result.status in {GmshMeshStatus.OK, GmshMeshStatus.WARNING}
            else result.status.value
        ),
        cell_count=result.mesh_info.element_count if result.mesh_info else None,
        node_count=result.mesh_info.node_count if result.mesh_info else None,
        quality_summary=_quality_summary(result.mesh_info),
        mesh_info=mesh_info,
        metadata=metadata,
    )


def generate_primitive_mesh(
    primitive: GmshGeometrySpec,
    output_path: str | Path,
    *,
    mesh_size: GmshMeshSizeField | None = None,
    vtu_path: str | Path | None = None,
    executable_registry: ExecutablePathRegistry | None = None,
    command_runner: ExternalCommandRunner | None = None,
    **_deprecated: Any,
) -> GmshMeshResult:
    """Compatibility helper that now uses the runner-backed adapter."""

    target = Path(output_path)
    request = GmshMeshRequest(
        geometry=primitive,
        mesh_dimension=(
            GmshMeshDimension.DIM2
            if primitive.kind in {GmshGeometryKind.RECTANGLE, GmshGeometryKind.PLATE_WITH_HOLE}
            else GmshMeshDimension.DIM3
        ),
        mesh_size=mesh_size or GmshMeshSizeField(),
        output_dir=target.parent if str(target.parent) else Path("."),
        output_name=target.stem,
        convert_to_vtu=vtu_path is not None,
    )
    result = GmshAdapter(
        executable_registry=executable_registry,
        command_runner=command_runner,
    ).generate_mesh(request)
    if vtu_path is not None and result.converted_mesh_path is not None:
        requested_vtu = Path(vtu_path)
        requested_vtu.parent.mkdir(parents=True, exist_ok=True)
        requested_vtu.write_bytes(result.converted_mesh_path.read_bytes())
        result = GmshMeshResult(
            result.status,
            result.request,
            geo_path=result.geo_path,
            msh_path=result.msh_path,
            converted_mesh_path=requested_vtu,
            mesh_model=result.mesh_model,
            mesh_info=result.mesh_info,
            physical_groups=result.physical_groups,
            diagnostics=result.diagnostics,
            run_result=result.run_result,
            artifacts=(
                *result.artifacts,
                RunArtifact(requested_vtu, "vtu", "Converted mesh preview.", "vtu"),
            ),
        )
    if result.status in {
        GmshMeshStatus.ERROR,
        GmshMeshStatus.DEPENDENCY_MISSING,
        GmshMeshStatus.TIMED_OUT,
    }:
        raise GmshAdapterError(result.diagnostics.summary())
    return result


def load_gmsh_mesh(path: str | Path, *, meshio_module: Any | None = None) -> MeshData:
    return load_mesh(_msh_path(path), meshio_module=meshio_module)


def load_gmsh_mesh_info(path: str | Path, *, meshio_module: Any | None = None) -> MeshInfo:
    return load_mesh_info(_msh_path(path), meshio_module=meshio_module)


def convert_gmsh_msh_to_vtu(
    msh_path: str | Path,
    vtu_path: str | Path,
    *,
    meshio_module: Any | None = None,
) -> Path:
    mesh_data = load_gmsh_mesh(msh_path, meshio_module=meshio_module)
    return export_vtu(mesh_data, vtu_path, meshio_module=meshio_module)


def _physical_groups_for_request(request: GmshMeshRequest) -> tuple[GmshPhysicalGroup, ...]:
    if request.geometry.physical_groups:
        return request.geometry.physical_groups
    return default_physical_groups(request.geometry.kind, request.mesh_dimension)


def _result(
    status: GmshMeshStatus,
    request: GmshMeshRequest,
    geo_path: Path,
    msh_path: Path,
    physical_groups: tuple[GmshPhysicalGroup, ...],
    diagnostics: DiagnosticReport,
    run_result: object | None,
) -> GmshMeshResult:
    artifacts = (
        RunArtifact(geo_path, "geo", "Generated Gmsh script.", "geo"),
        RunArtifact(msh_path, "msh", "Generated Gmsh mesh artifact.", "msh"),
    )
    if hasattr(run_result, "artifacts"):
        artifacts = _dedupe_artifacts((*run_result.artifacts, *artifacts))
    return GmshMeshResult(
        status,
        request,
        geo_path=geo_path,
        msh_path=msh_path,
        physical_groups=physical_groups,
        diagnostics=diagnostics,
        run_result=run_result if hasattr(run_result, "to_dict") else None,
        artifacts=artifacts,
    )


def _write_converted_vtu(
    mesh_data: MeshData,
    target: Path,
) -> tuple[Path | None, DiagnosticReport]:
    report = DiagnosticReport()
    try:
        converted = export_vtu(mesh_data, target)
    except Exception as exc:
        report.add_warning(
            DiagnosticCode.DEPENDENCY_UNAVAILABLE,
            f"Could not convert Gmsh .msh artifact to VTU: {exc}",
            hint="Install meshio or keep the generated .msh artifact.",
            path=target,
        )
        return None, report
    return converted, report


def _dedupe_artifacts(artifacts: tuple[RunArtifact, ...]) -> tuple[RunArtifact, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[RunArtifact] = []
    for artifact in artifacts:
        key = (str(artifact.path), artifact.role)
        if key in seen:
            continue
        seen.add(key)
        unique.append(artifact)
    return tuple(unique)


def _quality_summary(info: MeshInfo | None) -> str:
    if info is None:
        return ""
    return (
        f"{info.node_count} nodes, {info.element_count} elements, "
        f"cell types: {', '.join(info.cell_types) or 'none'}"
    )


def _msh_path(path: str | Path) -> Path:
    target = Path(path)
    if target.suffix.lower() != ".msh":
        msg = "Gmsh mesh path must use the .msh extension."
        raise GmshAdapterError(msg)
    return target
