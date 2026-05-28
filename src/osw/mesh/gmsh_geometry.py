"""Deterministic Gmsh `.geo` generation for bounded primitive templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from osw.core.diagnostics import DiagnosticReport

from .gmsh_model import (
    GmshGeometryKind,
    GmshGeometrySpec,
    GmshMeshDimension,
    GmshMeshRequest,
    GmshMeshSizeField,
    GmshPhysicalGroup,
)


class GmshGeometryError(ValueError):
    """Raised when a primitive cannot be expressed as a safe Gmsh template."""


def generate_geo_script(request: GmshMeshRequest) -> str:
    """Return deterministic `.geo` text without executing Gmsh."""

    geometry = request.geometry
    lines = [
        "// OpenSolver Workbench Gmsh primitive template",
        f"// geometry_id: {geometry.geometry_id}",
        f"// kind: {geometry.kind.value}",
        f"// mesh_dimension: {request.mesh_dimension.numeric}",
        f"// units: {geometry.units or 'unspecified'}",
        "",
        *_mesh_size_lines(request.mesh_size),
        "",
    ]
    if geometry.kind is GmshGeometryKind.RECTANGLE:
        lines.extend(_rectangle_lines(geometry, request.mesh_size))
    elif geometry.kind is GmshGeometryKind.BOX:
        lines.extend(_box_lines(geometry))
    elif geometry.kind is GmshGeometryKind.CYLINDER:
        lines.extend(_cylinder_lines(geometry))
    elif geometry.kind is GmshGeometryKind.SPHERE:
        lines.extend(_sphere_lines(geometry))
    elif geometry.kind is GmshGeometryKind.PLATE_WITH_HOLE:
        lines.extend(_plate_with_hole_lines(geometry, request.mesh_size))
    else:
        msg = (
            f"Unsupported Gmsh geometry kind: {geometry.kind.value}. "
            "Use rectangle, box, cylinder, sphere, or plate_with_hole."
        )
        raise GmshGeometryError(msg)
    return "\n".join(lines).rstrip() + "\n"


def write_geo_script(request: GmshMeshRequest, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(generate_geo_script(request), encoding="utf-8", newline="\n")
    return target


def default_box_request(output_dir: str | Path) -> GmshMeshRequest:
    return GmshMeshRequest(
        geometry=GmshGeometrySpec(
            GmshGeometryKind.BOX,
            {"length": 1.0, "width": 0.2, "height": 0.1},
            geometry_id="box",
            units="m",
        ),
        mesh_dimension=GmshMeshDimension.DIM3,
        mesh_size=GmshMeshSizeField(global_size=0.05),
        output_dir=output_dir,
        output_name="box",
    )


def geometry_spec_from_project(
    project: object,
    geometry_id: str | None = None,
) -> tuple[GmshGeometrySpec | None, DiagnosticReport]:
    """Create a conservative placeholder spec from ProjectSchema geometry refs."""

    report = DiagnosticReport()
    geometry_refs = tuple(getattr(project, "geometry_refs", ()) or ())
    if geometry_id:
        geometry_refs = tuple(
            ref
            for ref in geometry_refs
            if getattr(ref, "id", "") == geometry_id or getattr(ref, "name", "") == geometry_id
        )
    if not geometry_refs:
        report.add_warning(
            "gmsh-project-geometry-placeholder",
            "No project geometry reference could be mapped to a Gmsh primitive.",
            hint="Choose an explicit primitive geometry for Gmsh generation.",
        )
        return None, report
    ref = geometry_refs[0]
    metadata = dict(getattr(ref, "metadata", {}) or {})
    kind = str(metadata.get("gmsh_kind", metadata.get("kind", "box")))
    parameters = dict(
        metadata.get(
            "gmsh_parameters",
            {"length": 1.0, "width": 1.0, "height": 1.0},
        )
    )
    return (
        GmshGeometrySpec(
            kind=kind,
            parameters=parameters,
            geometry_id=str(getattr(ref, "id", "") or getattr(ref, "name", "") or "geometry"),
            units=str(metadata.get("units", "")),
            metadata={"source_geometry_ref": getattr(ref, "path", "")},
        ),
        report,
    )


def default_physical_groups(
    kind: GmshGeometryKind,
    mesh_dimension: GmshMeshDimension,
) -> tuple[GmshPhysicalGroup, ...]:
    if kind is GmshGeometryKind.RECTANGLE:
        return (
            GmshPhysicalGroup("inlet", 1, (4,), tag=1, role="inlet"),
            GmshPhysicalGroup("outlet", 1, (2,), tag=2, role="outlet"),
            GmshPhysicalGroup("wall", 1, (1, 3), tag=3, role="wall"),
            GmshPhysicalGroup("domain", 2, (1,), tag=4, role="domain"),
        )
    if kind is GmshGeometryKind.PLATE_WITH_HOLE:
        return (
            GmshPhysicalGroup("outer_wall", 1, (1, 2, 3, 4), tag=1, role="wall"),
            GmshPhysicalGroup("hole_wall", 1, (5, 6, 7, 8), tag=2, role="wall"),
            GmshPhysicalGroup("domain", 2, (1,), tag=3, role="domain"),
        )
    if mesh_dimension is GmshMeshDimension.DIM3:
        return (
            GmshPhysicalGroup("inlet", 2, (1,), tag=1, role="inlet"),
            GmshPhysicalGroup("outlet", 2, (2,), tag=2, role="outlet"),
            GmshPhysicalGroup("wall", 2, (3, 4, 5, 6), tag=3, role="wall"),
            GmshPhysicalGroup("domain", 3, (1,), tag=4, role="domain"),
        )
    return (GmshPhysicalGroup("domain", mesh_dimension.numeric, (1,), tag=1, role="domain"),)


def _mesh_size_lines(mesh_size: GmshMeshSizeField) -> list[str]:
    lines = [
        f"lc = {_num(mesh_size.global_size)};",
        f"Mesh.CharacteristicLengthMin = {_num(mesh_size.effective_min)};",
        f"Mesh.CharacteristicLengthMax = {_num(mesh_size.effective_max)};",
    ]
    if mesh_size.curvature_based:
        lines.append("Mesh.MeshSizeFromCurvature = 1;")
    if mesh_size.boundary_layer_placeholder:
        lines.append("// Boundary layer sizing is recorded as metadata only in OSW v0.1.")
    return lines


def _rectangle_lines(geometry: GmshGeometrySpec, mesh_size: GmshMeshSizeField) -> list[str]:
    width = _positive_parameter(geometry, "width")
    height = _positive_parameter(geometry, "height")
    return [
        "SetFactory(\"Built-in\");",
        f"Point(1) = {{0, 0, 0, {_num(mesh_size.global_size)}}};",
        f"Point(2) = {{{_num(width)}, 0, 0, {_num(mesh_size.global_size)}}};",
        f"Point(3) = {{{_num(width)}, {_num(height)}, 0, {_num(mesh_size.global_size)}}};",
        f"Point(4) = {{0, {_num(height)}, 0, {_num(mesh_size.global_size)}}};",
        "Line(1) = {1, 2};",
        "Line(2) = {2, 3};",
        "Line(3) = {3, 4};",
        "Line(4) = {4, 1};",
        "Curve Loop(1) = {1, 2, 3, 4};",
        "Plane Surface(1) = {1};",
        "Physical Curve(\"inlet\") = {4};",
        "Physical Curve(\"outlet\") = {2};",
        "Physical Curve(\"wall\") = {1, 3};",
        "Physical Surface(\"domain\") = {1};",
    ]


def _box_lines(geometry: GmshGeometrySpec) -> list[str]:
    length = _positive_parameter(geometry, "length")
    width = _positive_parameter(geometry, "width")
    height = _positive_parameter(geometry, "height")
    return [
        "SetFactory(\"OpenCASCADE\");",
        f"Box(1) = {{0, 0, 0, {_num(length)}, {_num(width)}, {_num(height)}}};",
        "Physical Surface(\"inlet\") = {1};",
        "Physical Surface(\"outlet\") = {2};",
        "Physical Surface(\"wall\") = {3, 4, 5, 6};",
        "Physical Volume(\"domain\") = {1};",
    ]


def _cylinder_lines(geometry: GmshGeometrySpec) -> list[str]:
    radius = _positive_parameter(geometry, "radius")
    height = _positive_parameter(geometry, "height")
    return [
        "SetFactory(\"OpenCASCADE\");",
        f"Cylinder(1) = {{0, 0, 0, 0, 0, {_num(height)}, {_num(radius)}}};",
        "Physical Surface(\"inlet\") = {1};",
        "Physical Surface(\"outlet\") = {2};",
        "Physical Surface(\"wall\") = {3};",
        "Physical Volume(\"domain\") = {1};",
    ]


def _sphere_lines(geometry: GmshGeometrySpec) -> list[str]:
    radius = _positive_parameter(geometry, "radius")
    return [
        "SetFactory(\"OpenCASCADE\");",
        f"Sphere(1) = {{0, 0, 0, {_num(radius)}}};",
        "Physical Surface(\"wall\") = {1};",
        "Physical Volume(\"domain\") = {1};",
    ]


def _plate_with_hole_lines(
    geometry: GmshGeometrySpec,
    mesh_size: GmshMeshSizeField,
) -> list[str]:
    width = _positive_parameter(geometry, "width")
    height = _positive_parameter(geometry, "height")
    radius = _positive_parameter(geometry, "hole_radius")
    center = geometry.parameters.get("center", (width / 2.0, height / 2.0))
    if not isinstance(center, (list, tuple)) or len(center) != 2:
        msg = "plate_with_hole center must be a two-value sequence."
        raise GmshGeometryError(msg)
    cx, cy = float(center[0]), float(center[1])
    return [
        "SetFactory(\"Built-in\");",
        f"Point(1) = {{0, 0, 0, {_num(mesh_size.global_size)}}};",
        f"Point(2) = {{{_num(width)}, 0, 0, {_num(mesh_size.global_size)}}};",
        f"Point(3) = {{{_num(width)}, {_num(height)}, 0, {_num(mesh_size.global_size)}}};",
        f"Point(4) = {{0, {_num(height)}, 0, {_num(mesh_size.global_size)}}};",
        f"Point(5) = {{{_num(cx)}, {_num(cy)}, 0, {_num(mesh_size.global_size)}}};",
        f"Point(6) = {{{_num(cx + radius)}, {_num(cy)}, 0, {_num(mesh_size.global_size)}}};",
        f"Point(7) = {{{_num(cx)}, {_num(cy + radius)}, 0, {_num(mesh_size.global_size)}}};",
        f"Point(8) = {{{_num(cx - radius)}, {_num(cy)}, 0, {_num(mesh_size.global_size)}}};",
        f"Point(9) = {{{_num(cx)}, {_num(cy - radius)}, 0, {_num(mesh_size.global_size)}}};",
        "Line(1) = {1, 2};",
        "Line(2) = {2, 3};",
        "Line(3) = {3, 4};",
        "Line(4) = {4, 1};",
        "Circle(5) = {6, 5, 7};",
        "Circle(6) = {7, 5, 8};",
        "Circle(7) = {8, 5, 9};",
        "Circle(8) = {9, 5, 6};",
        "Curve Loop(1) = {1, 2, 3, 4};",
        "Curve Loop(2) = {5, 6, 7, 8};",
        "Plane Surface(1) = {1, 2};",
        "Physical Curve(\"outer_wall\") = {1, 2, 3, 4};",
        "Physical Curve(\"hole_wall\") = {5, 6, 7, 8};",
        "Physical Surface(\"domain\") = {1};",
    ]


def _positive_parameter(geometry: GmshGeometrySpec, name: str) -> float:
    value = _parameter(geometry, name)
    if value <= 0:
        msg = f"Gmsh {geometry.kind.value} parameter '{name}' must be positive."
        raise GmshGeometryError(msg)
    return value


def _parameter(geometry: GmshGeometrySpec, name: str) -> float:
    try:
        return float(geometry.parameters[name])
    except KeyError as exc:
        msg = f"Gmsh {geometry.kind.value} is missing required parameter '{name}'."
        raise GmshGeometryError(msg) from exc
    except (TypeError, ValueError) as exc:
        msg = f"Gmsh {geometry.kind.value} parameter '{name}' must be numeric."
        raise GmshGeometryError(msg) from exc


def _num(value: Any) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.12g}"
