"""Pure exact-binding catalog for interactive point and cell results.

The catalog is deliberately renderer-free.  It validates the complete
``ResultDataset``/mesh boundary once, publishes only scalar and three-component
vector fields that can be addressed without remapping, and records unsupported
field shapes as explicit exclusions.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from osw.core.result_mesh_binding import (
    ResultMeshBindingResolution,
    ResultMeshBindingResolutionState,
)
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshData

_POINT_ASSOCIATIONS = frozenset({"point", "node", "vertex"})
_CELL_ASSOCIATIONS = frozenset({"cell", "element"})
_RESERVED_FIELD_PREFIXES = ("_osw_",)


class ResultBindingStatus(StrEnum):
    """Fail-closed status for one mesh-bound interactive result catalog."""

    READY = "READY"
    STALE_MESH = "STALE_MESH"
    LEGACY_UNRESOLVED = "LEGACY_UNRESOLVED"
    INVALID_BINDING = "INVALID_BINDING"
    INVALID_POINT_COUNT = "INVALID_POINT_COUNT"
    INVALID_CELL_COUNT = "INVALID_CELL_COUNT"
    UNSUPPORTED_ASSOCIATION = "UNSUPPORTED_ASSOCIATION"
    INVALID_FIELD_SHAPE = "INVALID_FIELD_SHAPE"


class ResultFieldKind(StrEnum):
    """Supported interactive field classes in stable presentation order."""

    POINT_SCALAR = "POINT_SCALAR"
    CELL_SCALAR = "CELL_SCALAR"
    POINT_VECTOR = "POINT_VECTOR"
    CELL_VECTOR = "CELL_VECTOR"


@dataclass(frozen=True)
class ResultFieldDescriptor:
    """Validated metadata for one renderer-independent result field."""

    field_id: str
    display_name: str
    kind: ResultFieldKind
    association: str
    component_names: tuple[str, ...]
    units: str
    tuple_count: int
    finite_tuple_count: int
    nonfinite_tuple_count: int
    semantic_role: str = ""
    quantity_dimension: str = ""
    coordinate_system: str = ""
    deformation_eligible: bool = False


@dataclass(frozen=True)
class ResultFieldCatalog:
    """Validated catalog for one exact mesh/result pairing."""

    binding_status: ResultBindingStatus
    result_id: str
    display_name: str
    mesh_fingerprint: str
    point_count: int
    cell_count: int
    fields: tuple[ResultFieldDescriptor, ...] = ()
    excluded_field_ids: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()

    def field(self, field_id: str) -> ResultFieldDescriptor:
        """Return one published descriptor by its stable ResultField name."""

        for descriptor in self.fields:
            if descriptor.field_id == field_id:
                return descriptor
        raise KeyError(f"Interactive result field not found: {field_id}")


def build_result_field_catalog(
    mesh: MeshData,
    result_dataset: object,
    *,
    binding_resolution: ResultMeshBindingResolution,
) -> ResultFieldCatalog:
    """Validate and catalog supported fields for an exact mesh fingerprint."""

    point_count = len(mesh.points)
    cell_count = sum(block.count for block in mesh.cells)
    result_id = str(getattr(result_dataset, "dataset_id", "") or "")
    metadata = getattr(result_dataset, "metadata", {}) or {}
    display_name = _display_name(result_id, metadata)
    fingerprint = compute_mesh_fingerprint(mesh).digest
    blocked = _binding_status(binding_resolution, fingerprint)
    if blocked is not None:
        status, diagnostic = blocked
        return ResultFieldCatalog(
            binding_status=status,
            result_id=result_id,
            display_name=display_name,
            mesh_fingerprint=fingerprint,
            point_count=point_count,
            cell_count=cell_count,
            diagnostics=(diagnostic,),
        )

    raw_fields = tuple(getattr(result_dataset, "fields", ()) or ())
    names = tuple(str(getattr(field, "name", "") or "") for field in raw_fields)
    if any(not name for name in names):
        return _invalid_catalog(
            ResultBindingStatus.INVALID_FIELD_SHAPE,
            result_id,
            display_name,
            fingerprint,
            point_count,
            cell_count,
            "Result fields require non-empty stable field IDs.",
        )
    if len(set(names)) != len(names):
        return _invalid_catalog(
            ResultBindingStatus.INVALID_FIELD_SHAPE,
            result_id,
            display_name,
            fingerprint,
            point_count,
            cell_count,
            "ResultDataset contains duplicate field IDs.",
        )

    semantics = _field_semantics(metadata)
    descriptors: list[tuple[int, int, ResultFieldDescriptor]] = []
    excluded: list[str] = []
    diagnostics: list[str] = []
    for ordinal, field in enumerate(raw_fields):
        field_id = names[ordinal]
        if field_id.startswith(_RESERVED_FIELD_PREFIXES):
            excluded.append(field_id)
            diagnostics.append(f"Reserved transient field {field_id!r} is excluded from results.")
            continue

        association = _normalize_association(getattr(field, "location", ""))
        if not association:
            return _invalid_catalog(
                ResultBindingStatus.UNSUPPORTED_ASSOCIATION,
                result_id,
                display_name,
                fingerprint,
                point_count,
                cell_count,
                f"Result field {field_id!r} has an unsupported association.",
            )
        components = tuple(str(component) for component in getattr(field, "components", ()) or ())
        if not components or any(not component for component in components):
            return _invalid_catalog(
                ResultBindingStatus.INVALID_FIELD_SHAPE,
                result_id,
                display_name,
                fingerprint,
                point_count,
                cell_count,
                f"Result field {field_id!r} has empty component metadata.",
            )
        if len(set(components)) != len(components):
            return _invalid_catalog(
                ResultBindingStatus.INVALID_FIELD_SHAPE,
                result_id,
                display_name,
                fingerprint,
                point_count,
                cell_count,
                f"Result field {field_id!r} has duplicate component names.",
            )
        if len(components) not in {1, 3}:
            excluded.append(field_id)
            diagnostics.append(
                f"Tensor-like or unsupported field {field_id!r} has "
                f"{len(components)} components and is excluded."
            )
            continue

        target_count = point_count if association == "point" else cell_count
        rows = tuple(getattr(field, "rows", ()) or ())
        if len(rows) != target_count:
            status = (
                ResultBindingStatus.INVALID_POINT_COUNT
                if association == "point"
                else ResultBindingStatus.INVALID_CELL_COUNT
            )
            return _invalid_catalog(
                status,
                result_id,
                display_name,
                fingerprint,
                point_count,
                cell_count,
                f"Result field {field_id!r} has {len(rows)} rows; "
                f"the mesh requires {target_count} {association} rows.",
            )
        validation = _validate_rows(rows, components, target_count, field_id)
        if validation[0] is not None:
            return _invalid_catalog(
                ResultBindingStatus.INVALID_FIELD_SHAPE,
                result_id,
                display_name,
                fingerprint,
                point_count,
                cell_count,
                validation[0],
            )
        finite_count = validation[1]
        kind = _kind(association, len(components))
        semantic = semantics.get(field_id, {})
        semantic_role = str(semantic.get("semantic_role", "") or "")
        quantity_dimension = str(semantic.get("quantity_dimension", "") or "")
        coordinate_system = str(semantic.get("coordinate_system", "") or "")
        descriptors.append(
            (
                _kind_rank(kind),
                ordinal,
                ResultFieldDescriptor(
                    field_id=field_id,
                    display_name=field_id,
                    kind=kind,
                    association=association,
                    component_names=components,
                    units=str(getattr(field, "unit", "") or ""),
                    tuple_count=target_count,
                    finite_tuple_count=finite_count,
                    nonfinite_tuple_count=target_count - finite_count,
                    semantic_role=semantic_role,
                    quantity_dimension=quantity_dimension,
                    coordinate_system=coordinate_system,
                    deformation_eligible=(
                        association == "point"
                        and len(components) == 3
                        and semantic_role == "displacement"
                        and quantity_dimension == "length"
                        and coordinate_system == "global_cartesian"
                    ),
                ),
            )
        )

    descriptors.sort(key=lambda item: (item[0], item[1]))
    return ResultFieldCatalog(
        binding_status=ResultBindingStatus.READY,
        result_id=result_id,
        display_name=display_name,
        mesh_fingerprint=fingerprint,
        point_count=point_count,
        cell_count=cell_count,
        fields=tuple(item[2] for item in descriptors),
        excluded_field_ids=tuple(excluded),
        diagnostics=tuple(diagnostics),
    )


def _binding_status(
    resolution: ResultMeshBindingResolution,
    fingerprint: str,
) -> tuple[ResultBindingStatus, str] | None:
    if resolution.state is ResultMeshBindingResolutionState.RESOLVED:
        if resolution.active_mesh_fingerprint == fingerprint:
            return None
        return (
            ResultBindingStatus.INVALID_BINDING,
            "Resolved result binding does not carry the exact active fingerprint.",
        )
    diagnostic = (
        f"Result binding is {resolution.state.value}: "
        f"{resolution.reason_code}. {resolution.message}"
    )
    if resolution.reason_code == "LEGACY_BINDING_FINGERPRINT_UNVERIFIED":
        return (ResultBindingStatus.LEGACY_UNRESOLVED, diagnostic)
    if resolution.state is ResultMeshBindingResolutionState.STALE:
        return (ResultBindingStatus.STALE_MESH, diagnostic)
    return (ResultBindingStatus.INVALID_BINDING, diagnostic)


def _validate_rows(
    rows: tuple[object, ...],
    components: tuple[str, ...],
    target_count: int,
    field_id: str,
) -> tuple[str | None, int]:
    by_id: dict[int, object] = {}
    finite_count = 0
    for row in rows:
        entity_id = _finite_integer(getattr(row, "entity_id", None))
        if entity_id is None:
            return (f"Result field {field_id!r} has an invalid entity ID.", 0)
        if entity_id in by_id:
            return (f"Result field {field_id!r} has duplicate entity IDs.", 0)
        values = getattr(row, "values", None)
        if not isinstance(values, Mapping):
            return (f"Result field {field_id!r} has non-mapping row values.", 0)
        tuple_finite = True
        for component in components:
            if component not in values:
                return (
                    f"Result field {field_id!r} is missing component {component!r} "
                    "from one or more rows.",
                    0,
                )
            try:
                number = float(values[component])
            except (TypeError, ValueError, OverflowError):
                return (
                    f"Result field {field_id!r} contains a non-numeric value.",
                    0,
                )
            tuple_finite = tuple_finite and isfinite(number)
        finite_count += int(tuple_finite)
        by_id[entity_id] = row
    keys = tuple(sorted(by_id))
    if keys not in {tuple(range(target_count)), tuple(range(1, target_count + 1))}:
        return (
            f"Result field {field_id!r} entity IDs are not a complete contiguous domain.",
            0,
        )
    return (None, finite_count)


def _display_name(result_id: str, metadata: object) -> str:
    if isinstance(metadata, Mapping):
        title = str(metadata.get("title", "") or "").strip()
        if title:
            return title
    return result_id or "Result dataset"


def _field_semantics(metadata: object) -> Mapping[str, Mapping[str, object]]:
    if not isinstance(metadata, Mapping):
        return {}
    payload = metadata.get("field_semantics", {})
    if not isinstance(payload, Mapping):
        return {}
    return {str(key): value for key, value in payload.items() if isinstance(value, Mapping)}


def _normalize_association(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in _POINT_ASSOCIATIONS:
        return "point"
    if normalized in _CELL_ASSOCIATIONS:
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


def _kind(association: str, component_count: int) -> ResultFieldKind:
    if association == "point":
        return (
            ResultFieldKind.POINT_SCALAR if component_count == 1 else ResultFieldKind.POINT_VECTOR
        )
    return ResultFieldKind.CELL_SCALAR if component_count == 1 else ResultFieldKind.CELL_VECTOR


def _kind_rank(kind: ResultFieldKind) -> int:
    return {
        ResultFieldKind.POINT_SCALAR: 0,
        ResultFieldKind.CELL_SCALAR: 1,
        ResultFieldKind.POINT_VECTOR: 2,
        ResultFieldKind.CELL_VECTOR: 3,
    }[kind]


def _invalid_catalog(
    status: ResultBindingStatus,
    result_id: str,
    display_name: str,
    fingerprint: str,
    point_count: int,
    cell_count: int,
    diagnostic: str,
) -> ResultFieldCatalog:
    return ResultFieldCatalog(
        binding_status=status,
        result_id=result_id,
        display_name=display_name,
        mesh_fingerprint=fingerprint,
        point_count=point_count,
        cell_count=cell_count,
        diagnostics=(diagnostic,),
    )


__all__ = [
    "ResultBindingStatus",
    "ResultFieldCatalog",
    "ResultFieldDescriptor",
    "ResultFieldKind",
    "build_result_field_catalog",
]
