"""Typed, exact-binding displacement projection for interactive result views."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from math import fsum, isfinite, sqrt

from osw.core.result_mesh_binding import (
    ResultMeshBindingResolution,
    ResultMeshBindingResolutionState,
)
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshData

_SUPPORTED_DEFORMATION_CELL_TYPES = frozenset({"triangle", "quad", "polygon", "tetra"})
_AUTO_DEFORMATION_FRACTION = 0.1


class DeformationMode(StrEnum):
    """Geometry presentation policy for one typed displacement field."""

    ORIGINAL = "ORIGINAL"
    DEFORMED = "DEFORMED"
    OVERLAY = "OVERLAY"


class DeformationScaleMode(StrEnum):
    """Visual-only displacement scale policy."""

    AUTO = "AUTO"
    MANUAL = "MANUAL"


class DeformationStatus(StrEnum):
    """Eligibility/projection status with stale state kept explicit."""

    READY = "READY"
    INELIGIBLE = "INELIGIBLE"
    STALE = "STALE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class DisplacementEligibility:
    """Exact evidence required before creating derived display coordinates."""

    eligible: bool
    status: DeformationStatus
    field_name: str
    components: tuple[str, ...] = ()
    unit: str = ""
    mesh_length_unit: str = ""
    mesh_fingerprint: str = ""
    displacements: tuple[tuple[float, float, float], ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeformedShapeSpec:
    """Renderer-neutral derived geometry and canonical identity metadata."""

    applied: bool
    status: DeformationStatus
    field_name: str
    mode: DeformationMode = DeformationMode.ORIGINAL
    scale_mode: DeformationScaleMode = DeformationScaleMode.AUTO
    scale: float = 1.0
    bounds_diagonal: float = 0.0
    maximum_displacement: float = 0.0
    mesh_fingerprint: str = ""
    mesh_data: MeshData | None = None
    displacements: tuple[tuple[float, float, float], ...] = ()
    canonical_point_ids: tuple[int, ...] = ()
    canonical_cell_ids: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


def evaluate_displacement_eligibility(
    mesh: MeshData,
    result_dataset: object,
    *,
    binding_resolution: ResultMeshBindingResolution,
    field_name: str,
) -> DisplacementEligibility:
    """Require typed displacement semantics, exact units, shape, and binding."""

    fingerprint = compute_mesh_fingerprint(mesh).digest
    if binding_resolution.state is not ResultMeshBindingResolutionState.RESOLVED:
        status = (
            DeformationStatus.STALE
            if binding_resolution.state is ResultMeshBindingResolutionState.STALE
            else DeformationStatus.INVALID
        )
        return _ineligible(
            field_name,
            status,
            f"{binding_resolution.reason_code}: {binding_resolution.message}",
            fingerprint=fingerprint,
        )
    if binding_resolution.active_mesh_fingerprint != fingerprint:
        return _ineligible(
            field_name,
            DeformationStatus.STALE,
            "The displacement binding does not match the exact mesh fingerprint.",
            fingerprint=fingerprint,
        )
    field = _find_field(result_dataset, field_name)
    if field is None:
        return _ineligible(
            field_name,
            DeformationStatus.INVALID,
            f"Result field {field_name!r} is not available.",
            fingerprint=fingerprint,
        )
    metadata = getattr(result_dataset, "metadata", {}) or {}
    semantic = _field_semantic(metadata, field_name)
    if (
        semantic.get("semantic_role") != "displacement"
        or semantic.get("quantity_dimension") != "length"
        or semantic.get("coordinate_system") != "global_cartesian"
    ):
        return _ineligible(
            field_name,
            DeformationStatus.INELIGIBLE,
            "Deformation requires an exact displacement semantic role, length "
            "dimension, and global Cartesian coordinate system.",
            fingerprint=fingerprint,
        )
    association = _normalize_association(getattr(field, "location", ""))
    if association != "point":
        return _ineligible(
            field_name,
            DeformationStatus.INELIGIBLE,
            "Deformation requires a point-associated displacement field.",
            fingerprint=fingerprint,
        )
    components = tuple(str(item) for item in getattr(field, "components", ()) or ())
    if len(components) != 3 or len(set(components)) != 3:
        return _ineligible(
            field_name,
            DeformationStatus.INELIGIBLE,
            "Deformation requires exactly three distinct displacement components.",
            fingerprint=fingerprint,
        )
    unit = str(getattr(field, "unit", "") or "").strip()
    mesh_length_unit = (
        str(metadata.get("mesh_length_unit", "") or "").strip()
        if isinstance(metadata, Mapping)
        else ""
    )
    if not unit or not mesh_length_unit or unit != mesh_length_unit:
        return _ineligible(
            field_name,
            DeformationStatus.INELIGIBLE,
            "Displacement unit must exactly match the declared mesh length unit; "
            "implicit unit conversion is not supported.",
            components=components,
            unit=unit,
            mesh_length_unit=mesh_length_unit,
            fingerprint=fingerprint,
        )
    unsupported = sorted(
        {
            block.cell_type
            for block in mesh.cells
            if block.count > 0 and block.cell_type not in _SUPPORTED_DEFORMATION_CELL_TYPES
        }
    )
    if unsupported:
        return _ineligible(
            field_name,
            DeformationStatus.INELIGIBLE,
            "Deformation contains unsupported mesh topology: " + ", ".join(unsupported),
            components=components,
            unit=unit,
            mesh_length_unit=mesh_length_unit,
            fingerprint=fingerprint,
        )
    displacements, diagnostic = _aligned_displacements(
        field,
        components,
        len(mesh.points),
    )
    if diagnostic:
        return _ineligible(
            field_name,
            DeformationStatus.INELIGIBLE,
            diagnostic,
            components=components,
            unit=unit,
            mesh_length_unit=mesh_length_unit,
            fingerprint=fingerprint,
        )
    return DisplacementEligibility(
        eligible=True,
        status=DeformationStatus.READY,
        field_name=field_name,
        components=components,
        unit=unit,
        mesh_length_unit=mesh_length_unit,
        mesh_fingerprint=fingerprint,
        displacements=displacements,
    )


def build_deformed_shape_spec(
    mesh: MeshData,
    result_dataset: object,
    *,
    binding_resolution: ResultMeshBindingResolution,
    field_name: str,
    mode: DeformationMode | str = DeformationMode.ORIGINAL,
    scale_mode: DeformationScaleMode | str = DeformationScaleMode.AUTO,
    manual_scale: float | None = None,
) -> DeformedShapeSpec:
    """Derive display-only coordinates without mutating source mesh/results."""

    eligibility = evaluate_displacement_eligibility(
        mesh,
        result_dataset,
        binding_resolution=binding_resolution,
        field_name=field_name,
    )
    if not eligibility.eligible:
        return DeformedShapeSpec(
            applied=False,
            status=eligibility.status,
            field_name=field_name,
            mesh_fingerprint=eligibility.mesh_fingerprint,
            diagnostics=eligibility.diagnostics,
        )
    try:
        selected_mode = DeformationMode(str(mode).strip().upper())
    except ValueError:
        return _invalid_spec(field_name, "Deformation mode must be ORIGINAL, DEFORMED, or OVERLAY.")
    try:
        selected_scale_mode = DeformationScaleMode(str(scale_mode).strip().upper())
    except ValueError:
        return _invalid_spec(field_name, "Deformation scale mode must be AUTO or MANUAL.")
    magnitudes = tuple(_magnitude(item) for item in eligibility.displacements)
    maximum_displacement = max(magnitudes, default=0.0)
    bounds_diagonal = _bounds_diagonal(mesh)
    if selected_scale_mode is DeformationScaleMode.AUTO:
        scale = (
            1.0
            if maximum_displacement == 0.0
            else _AUTO_DEFORMATION_FRACTION * bounds_diagonal / maximum_displacement
        )
    else:
        try:
            scale = float(manual_scale)  # type: ignore[arg-type]
        except (TypeError, ValueError, OverflowError):
            return _invalid_spec(
                field_name,
                "Manual deformation scale must be finite and nonnegative.",
            )
        if not isfinite(scale) or scale < 0.0:
            return _invalid_spec(
                field_name,
                "Manual deformation scale must be finite and nonnegative.",
            )
    derived_mesh = None
    if selected_mode is not DeformationMode.ORIGINAL:
        derived_mesh = MeshData(
            points=tuple(
                (
                    point[0] + scale * displacement[0],
                    point[1] + scale * displacement[1],
                    point[2] + scale * displacement[2],
                )
                for point, displacement in zip(
                    mesh.points,
                    eligibility.displacements,
                    strict=True,
                )
            ),
            cells=mesh.cells,
            point_data=mesh.point_data,
            cell_data=mesh.cell_data,
            field_data=mesh.field_data,
        )
    return DeformedShapeSpec(
        applied=True,
        status=DeformationStatus.READY,
        field_name=field_name,
        mode=selected_mode,
        scale_mode=selected_scale_mode,
        scale=scale,
        bounds_diagonal=bounds_diagonal,
        maximum_displacement=maximum_displacement,
        mesh_fingerprint=eligibility.mesh_fingerprint,
        mesh_data=derived_mesh,
        displacements=eligibility.displacements,
        canonical_point_ids=tuple(range(len(mesh.points))),
        canonical_cell_ids=tuple(
            f"{block_index}:{cell_index}"
            for block_index, block in enumerate(mesh.cells)
            for cell_index in range(block.count)
        ),
    )


def _aligned_displacements(
    field: object,
    components: tuple[str, ...],
    point_count: int,
) -> tuple[tuple[tuple[float, float, float], ...], str]:
    rows = tuple(getattr(field, "rows", ()) or ())
    if len(rows) != point_count:
        return (), (
            f"Displacement point count {len(rows)} does not match mesh point count {point_count}."
        )
    by_id: dict[int, tuple[float, float, float]] = {}
    for row in rows:
        entity_id = _finite_integer(getattr(row, "entity_id", None))
        if entity_id is None or entity_id in by_id:
            return (), "Displacement entity IDs must form one unique contiguous domain."
        values = getattr(row, "values", None)
        if not isinstance(values, Mapping):
            return (), "Displacement row values must be numeric mappings."
        vector: list[float] = []
        for component in components:
            if component not in values:
                return (), f"Displacement component {component!r} is missing."
            try:
                value = float(values[component])
            except (TypeError, ValueError, OverflowError):
                return (), "Displacement components must be numeric and finite."
            if not isfinite(value):
                return (), "Displacement contains a nonfinite component."
            vector.append(value)
        by_id[entity_id] = (vector[0], vector[1], vector[2])
    keys = sorted(by_id)
    if keys == list(range(point_count)):
        offset = 0
    elif keys == list(range(1, point_count + 1)):
        offset = 1
    else:
        return (), "Displacement entity IDs must form one unique contiguous domain."
    return tuple(by_id[index + offset] for index in range(point_count)), ""


def _find_field(result_dataset: object, field_name: str) -> object | None:
    return next(
        (
            field
            for field in getattr(result_dataset, "fields", ()) or ()
            if str(getattr(field, "name", "")) == field_name
        ),
        None,
    )


def _field_semantic(metadata: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(metadata, Mapping):
        return {}
    semantics = metadata.get("field_semantics", {})
    if not isinstance(semantics, Mapping):
        return {}
    payload = semantics.get(field_name, {})
    return payload if isinstance(payload, Mapping) else {}


def _normalize_association(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"point", "node", "vertex"}:
        return "point"
    if normalized in {"cell", "element"}:
        return "cell"
    return ""


def _finite_integer(value: object) -> int | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not isfinite(number) or not number.is_integer():
        return None
    return int(number)


def _magnitude(vector: tuple[float, float, float]) -> float:
    return sqrt(fsum(component * component for component in vector))


def _bounds_diagonal(mesh: MeshData) -> float:
    if not mesh.points:
        return 0.0
    xs = tuple(point[0] for point in mesh.points)
    ys = tuple(point[1] for point in mesh.points)
    zs = tuple(point[2] for point in mesh.points)
    return sqrt((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2 + (max(zs) - min(zs)) ** 2)


def _ineligible(
    field_name: str,
    status: DeformationStatus,
    diagnostic: str,
    *,
    components: tuple[str, ...] = (),
    unit: str = "",
    mesh_length_unit: str = "",
    fingerprint: str = "",
) -> DisplacementEligibility:
    return DisplacementEligibility(
        eligible=False,
        status=status,
        field_name=field_name,
        components=components,
        unit=unit,
        mesh_length_unit=mesh_length_unit,
        mesh_fingerprint=fingerprint,
        diagnostics=(diagnostic,),
    )


def _invalid_spec(field_name: str, diagnostic: str) -> DeformedShapeSpec:
    return DeformedShapeSpec(
        applied=False,
        status=DeformationStatus.INVALID,
        field_name=field_name,
        diagnostics=(diagnostic,),
    )


__all__ = [
    "DeformationMode",
    "DeformationScaleMode",
    "DeformationStatus",
    "DeformedShapeSpec",
    "DisplacementEligibility",
    "build_deformed_shape_spec",
    "evaluate_displacement_eligibility",
]
