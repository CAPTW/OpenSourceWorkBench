"""Typed solver-setup records, exact selection validation, and bounded conflicts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from osw.mesh.mesh_model import MeshData

from .materials import Material
from .selection import EntityKind, NamedSelection
from .selection_resolution import ResolutionResult, ResolutionState
from .units import Quantity, UnitSystem

SOLVER_SETUP_SCHEMA = "osw.solver_setup.v1"
SUPPORTED_SURFACE_CELL_TYPES = frozenset({"triangle", "quad", "polygon"})


class SetupRecordKind(StrEnum):
    MATERIAL_REGION = "material_region"
    MATERIAL = "material_region"  # Backward-compatible enum alias.
    FIXED_SUPPORT = "fixed_support"
    PRESCRIBED_DISPLACEMENT = "prescribed_displacement"
    FORCE = "force"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    HEAT_FLUX = "heat_flux"


class SetupReadiness(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"


class SetupValidity(StrEnum):
    VALID = "valid"
    DISABLED = "disabled"
    STALE_SELECTION = "stale_selection"
    MISSING_REFERENCE = "missing_reference"
    INCOMPATIBLE = "incompatible"
    INVALID_PARAMETERS = "invalid_parameters"
    CONFLICT = "conflict"
    LEGACY_UNRESOLVED = "legacy_unresolved"


@dataclass(frozen=True)
class MaterialAssignmentRecord:
    id: str
    name: str
    material_id: str
    target_selection_id: str
    enabled: bool = True

    @property
    def setup_kind(self) -> SetupRecordKind:
        return SetupRecordKind.MATERIAL_REGION

    @property
    def schema_version(self) -> str:
        return SOLVER_SETUP_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "material_id": self.material_id,
            "target_selection_id": self.target_selection_id,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: object) -> MaterialAssignmentRecord:
        payload = _mapping(data, "Material assignment record")
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            material_id=str(payload.get("material_id", "")),
            target_selection_id=str(payload.get("target_selection_id", "")),
            enabled=bool(payload.get("enabled", True)),
        )


MaterialRegionRecord = MaterialAssignmentRecord


@dataclass(frozen=True)
class FixedSupportRecord:
    id: str
    name: str
    target_selection_id: str
    translational_dofs: tuple[int, ...] = (1, 2, 3)
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "translational_dofs",
            tuple(int(item) for item in self.translational_dofs),
        )

    @property
    def setup_kind(self) -> SetupRecordKind:
        return SetupRecordKind.FIXED_SUPPORT

    @property
    def schema_version(self) -> str:
        return SOLVER_SETUP_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "target_selection_id": self.target_selection_id,
            "translational_dofs": list(self.translational_dofs),
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: object) -> FixedSupportRecord:
        payload = _mapping(data, "Fixed support record")
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            target_selection_id=str(payload.get("target_selection_id", "")),
            translational_dofs=tuple(
                int(item) for item in payload.get("translational_dofs", (1, 2, 3)) or ()
            ),
            enabled=bool(payload.get("enabled", True)),
        )


@dataclass(frozen=True)
class PrescribedDisplacementRecord:
    id: str
    name: str
    target_selection_id: str
    ux: Quantity | None = None
    uy: Quantity | None = None
    uz: Quantity | None = None
    coordinate_system: str = "GLOBAL"
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "coordinate_system",
            str(self.coordinate_system or "").upper(),
        )

    @property
    def setup_kind(self) -> SetupRecordKind:
        return SetupRecordKind.PRESCRIBED_DISPLACEMENT

    @property
    def schema_version(self) -> str:
        return SOLVER_SETUP_SCHEMA

    @property
    def components(self) -> tuple[Quantity | None, Quantity | None, Quantity | None]:
        return (self.ux, self.uy, self.uz)

    @property
    def constrained_dofs(self) -> tuple[int, ...]:
        return tuple(index for index, value in enumerate(self.components, 1) if value is not None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "target_selection_id": self.target_selection_id,
            "ux": _optional_quantity_to_dict(self.ux),
            "uy": _optional_quantity_to_dict(self.uy),
            "uz": _optional_quantity_to_dict(self.uz),
            "coordinate_system": self.coordinate_system,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: object) -> PrescribedDisplacementRecord:
        payload = _mapping(data, "Prescribed displacement record")
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            target_selection_id=str(payload.get("target_selection_id", "")),
            ux=_optional_quantity_from_dict(payload.get("ux")),
            uy=_optional_quantity_from_dict(payload.get("uy")),
            uz=_optional_quantity_from_dict(payload.get("uz")),
            coordinate_system=str(payload.get("coordinate_system", "GLOBAL")),
            enabled=bool(payload.get("enabled", True)),
        )


@dataclass(frozen=True)
class ForceLoadRecord:
    id: str
    name: str
    target_selection_id: str
    magnitude: Quantity
    direction: tuple[float, float, float]
    coordinate_system: str = "GLOBAL"
    application_mode: str = "PER_NODE"
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "direction", tuple(float(item) for item in self.direction))
        object.__setattr__(
            self,
            "coordinate_system",
            str(self.coordinate_system or "").upper(),
        )
        object.__setattr__(
            self,
            "application_mode",
            str(self.application_mode or "").upper(),
        )

    @property
    def setup_kind(self) -> SetupRecordKind:
        return SetupRecordKind.FORCE

    @property
    def schema_version(self) -> str:
        return SOLVER_SETUP_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "target_selection_id": self.target_selection_id,
            "magnitude": self.magnitude.to_dict(),
            "direction": list(self.direction),
            "coordinate_system": self.coordinate_system,
            "application_mode": self.application_mode,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: object) -> ForceLoadRecord:
        payload = _mapping(data, "Force load record")
        direction = tuple(float(item) for item in payload.get("direction", ()) or ())
        if len(direction) != 3:
            direction = (0.0, 0.0, 0.0)
        return cls(
            id=str(payload.get("id", "")),
            name=str(payload.get("name", "")),
            target_selection_id=str(payload.get("target_selection_id", "")),
            magnitude=Quantity.from_dict(payload.get("magnitude")),
            direction=direction,
            coordinate_system=str(payload.get("coordinate_system", "GLOBAL")),
            application_mode=str(payload.get("application_mode", "PER_NODE")),
            enabled=bool(payload.get("enabled", True)),
        )


@dataclass(frozen=True)
class PressureLoadRecord:
    id: str
    name: str
    target_selection_id: str
    value: Quantity
    enabled: bool = True

    @property
    def pressure_value(self) -> Quantity:
        return self.value

    @property
    def setup_kind(self) -> SetupRecordKind:
        return SetupRecordKind.PRESSURE

    @property
    def schema_version(self) -> str:
        return SOLVER_SETUP_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return _scalar_record_to_dict(self, "value")

    @classmethod
    def from_dict(cls, data: object) -> PressureLoadRecord:
        payload = _mapping(data, "Pressure load record")
        return cls(
            str(payload.get("id", "")),
            str(payload.get("name", "")),
            str(payload.get("target_selection_id", "")),
            Quantity.from_dict(payload.get("value", payload.get("pressure_value"))),
            bool(payload.get("enabled", True)),
        )


@dataclass(frozen=True)
class TemperatureRecord:
    id: str
    name: str
    target_selection_id: str
    value: Quantity
    enabled: bool = True

    @property
    def temperature_value(self) -> Quantity:
        return self.value

    @property
    def setup_kind(self) -> SetupRecordKind:
        return SetupRecordKind.TEMPERATURE

    @property
    def schema_version(self) -> str:
        return SOLVER_SETUP_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return _scalar_record_to_dict(self, "value")

    @classmethod
    def from_dict(cls, data: object) -> TemperatureRecord:
        payload = _mapping(data, "Temperature record")
        return cls(
            str(payload.get("id", "")),
            str(payload.get("name", "")),
            str(payload.get("target_selection_id", "")),
            Quantity.from_dict(payload.get("value", payload.get("temperature_value"))),
            bool(payload.get("enabled", True)),
        )


@dataclass(frozen=True)
class HeatFluxRecord:
    id: str
    name: str
    target_selection_id: str
    value: Quantity
    enabled: bool = True

    @property
    def heat_flux_value(self) -> Quantity:
        return self.value

    @property
    def setup_kind(self) -> SetupRecordKind:
        return SetupRecordKind.HEAT_FLUX

    @property
    def schema_version(self) -> str:
        return SOLVER_SETUP_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return _scalar_record_to_dict(self, "value")

    @classmethod
    def from_dict(cls, data: object) -> HeatFluxRecord:
        payload = _mapping(data, "Heat flux record")
        return cls(
            str(payload.get("id", "")),
            str(payload.get("name", "")),
            str(payload.get("target_selection_id", "")),
            Quantity.from_dict(payload.get("value", payload.get("heat_flux_value"))),
            bool(payload.get("enabled", True)),
        )


@dataclass(frozen=True)
class SetupRecordStatus:
    record_id: str
    record_kind: SetupRecordKind
    state: SetupReadiness
    reason_code: str
    message: str
    validity: SetupValidity = SetupValidity.INVALID_PARAMETERS
    overlay_renderable: bool | None = None

    @property
    def valid(self) -> bool:
        return self.validity is SetupValidity.VALID


class MaterialReferenceError(ValueError):
    """Raised when a referenced project material would be orphaned."""


def iter_solver_setup_records(setup: object) -> tuple[object, ...]:
    """Return typed records in one deterministic product order."""

    return (
        *(getattr(setup, "material_assignment_records", ()) or ()),
        *(getattr(setup, "fixed_support_records", ()) or ()),
        *(getattr(setup, "prescribed_displacement_records", ()) or ()),
        *(getattr(setup, "force_load_records", ()) or ()),
        *(getattr(setup, "pressure_load_records", ()) or ()),
        *(getattr(setup, "temperature_records", ()) or ()),
        *(getattr(setup, "heat_flux_records", ()) or ()),
    )


def setup_record_kind(record: object) -> SetupRecordKind:
    kind_by_type = {
        MaterialAssignmentRecord: SetupRecordKind.MATERIAL_REGION,
        FixedSupportRecord: SetupRecordKind.FIXED_SUPPORT,
        PrescribedDisplacementRecord: SetupRecordKind.PRESCRIBED_DISPLACEMENT,
        ForceLoadRecord: SetupRecordKind.FORCE,
        PressureLoadRecord: SetupRecordKind.PRESSURE,
        TemperatureRecord: SetupRecordKind.TEMPERATURE,
        HeatFluxRecord: SetupRecordKind.HEAT_FLUX,
    }
    try:
        return kind_by_type[type(record)]
    except KeyError as exc:
        raise ValueError(f"Unsupported setup record type: {type(record).__name__}") from exc


def force_direction(record: ForceLoadRecord) -> tuple[float, float, float]:
    if len(record.direction) != 3 or not all(math.isfinite(item) for item in record.direction):
        return (0.0, 0.0, 0.0)
    length = math.sqrt(sum(item * item for item in record.direction))
    if not math.isfinite(length) or length <= 0.0:
        return (0.0, 0.0, 0.0)
    return tuple(item / length for item in record.direction)


def force_vector(
    record: ForceLoadRecord,
    *,
    target_unit: str = "N",
) -> tuple[float, float, float]:
    """Return the exact signed global vector in a supported force unit."""

    scales = {
        ("N", "N"): 1.0,
        ("kN", "N"): 1000.0,
        ("kN", "kN"): 1.0,
        ("N", "kN"): 0.001,
    }
    scale = scales.get((record.magnitude.unit, target_unit))
    direction = force_direction(record)
    if scale is None or direction == (0.0, 0.0, 0.0):
        return (0.0, 0.0, 0.0)
    return tuple(component * record.magnitude.value * scale for component in direction)


def status_allows_overlay(status: SetupRecordStatus) -> bool:
    if status.overlay_renderable is not None:
        return status.overlay_renderable
    return status.state is SetupReadiness.READY


def evaluate_solver_setup(
    setup: object,
    *,
    selections: Sequence[NamedSelection],
    materials: Sequence[Material],
    resolutions: Mapping[str, ResolutionResult],
    mesh: MeshData | None = None,
    project_units: UnitSystem | None = None,
) -> tuple[SetupRecordStatus, ...]:
    """Recompute model/selection/topology validity without renderer state."""

    records = iter_solver_setup_records(setup)
    id_counts = {
        str(record.id): sum(candidate.id == record.id for candidate in records)
        for record in records
    }
    normalized_names = [str(record.name).strip().casefold() for record in records]
    name_counts = {name: normalized_names.count(name) for name in normalized_names}
    selection_by_id = {item.id: item for item in selections}
    material_ids = {item.material_id for item in materials}
    statuses: dict[str, SetupRecordStatus] = {}

    for record in records:
        kind = setup_record_kind(record)
        status = _base_status(
            record,
            kind,
            _expected_entity_kinds(kind),
            selection_by_id,
            resolutions,
            id_counts,
            name_counts,
        )
        if status.state is SetupReadiness.READY:
            status = _parameter_status(
                record,
                kind,
                status,
                material_ids=material_ids,
                resolutions=resolutions,
                mesh=mesh,
                project_units=project_units,
            )
        statuses[str(record.id)] = status

    material_records = tuple(getattr(setup, "material_assignment_records", ()) or ())
    support_records = tuple(getattr(setup, "fixed_support_records", ()) or ())
    displacement_records = tuple(getattr(setup, "prescribed_displacement_records", ()) or ())
    _block_overlapping_materials(material_records, resolutions, statuses)
    _block_fixed_displacement_conflicts(
        support_records,
        displacement_records,
        resolutions,
        statuses,
    )
    _block_displacement_conflicts(displacement_records, resolutions, statuses)
    return tuple(statuses[str(record.id)] for record in records)


def surface_cell_centroid_and_normal(
    mesh: MeshData,
    cell_index: int,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return deterministic oriented geometry for an explicit surface cell."""

    cell_type, connectivity = _cell_at_index(mesh, cell_index)
    if cell_type not in SUPPORTED_SURFACE_CELL_TYPES:
        raise ValueError("REQUIRES_EXPLICIT_SURFACE_SELECTION")
    try:
        points = tuple(mesh.points[index] for index in connectivity)
    except (IndexError, TypeError) as exc:
        raise ValueError("INVALID_SURFACE_CONNECTIVITY") from exc
    if len(points) < 3:
        raise ValueError("DEGENERATE_SURFACE_NORMAL")
    centroid = tuple(sum(point[axis] for point in points) / len(points) for axis in range(3))
    normal = _newell_normal(points)
    length = math.sqrt(sum(value * value for value in normal))
    if not math.isfinite(length) or length <= 1.0e-15:
        raise ValueError("DEGENERATE_SURFACE_NORMAL")
    return centroid, tuple(value / length for value in normal)


def find_material_references(project: object, material_id: str) -> tuple[str, ...]:
    references: list[str] = []
    for setup in getattr(project, "physics", ()) or ():
        references.extend(
            (
                f"{record.id} ({record.name})"
                if str(record.name).strip() and str(record.name) != str(record.id)
                else str(record.id)
            )
            for record in getattr(setup, "material_assignment_records", ()) or ()
            if str(record.material_id) == material_id
        )
    return tuple(references)


def ensure_material_deletable(project: object, material_id: str) -> None:
    references = find_material_references(project, material_id)
    if references:
        raise MaterialReferenceError(
            "Material is referenced by setup records: " + ", ".join(references)
        )


def _base_status(
    record: object,
    kind: SetupRecordKind,
    expected_kinds: frozenset[EntityKind],
    selections: Mapping[str, NamedSelection],
    resolutions: Mapping[str, ResolutionResult],
    id_counts: Mapping[str, int],
    name_counts: Mapping[str, int],
) -> SetupRecordStatus:
    record_id = str(getattr(record, "id", ""))
    if not record_id or id_counts.get(record_id, 0) != 1:
        return _blocked(
            record_id,
            kind,
            "DUPLICATE_OR_MISSING_RECORD_ID",
            "Setup record IDs must be non-empty and unique.",
            validity=SetupValidity.CONFLICT,
        )
    name = str(getattr(record, "name", "")).strip()
    if not name:
        return _blocked(
            record_id,
            kind,
            "MISSING_RECORD_NAME",
            "Setup record names must be non-empty after trimming.",
        )
    if name_counts.get(name.casefold(), 0) != 1:
        return _blocked(
            record_id,
            kind,
            "DUPLICATE_RECORD_NAME",
            "Setup record names must be unique (case-insensitive).",
            validity=SetupValidity.CONFLICT,
        )
    if not getattr(record, "enabled", True):
        return SetupRecordStatus(
            record_id,
            kind,
            SetupReadiness.DISABLED,
            "DISABLED",
            "Record is disabled.",
            SetupValidity.DISABLED,
            False,
        )
    target_id = str(getattr(record, "target_selection_id", ""))
    selection = selections.get(target_id)
    if selection is None:
        return _blocked(
            record_id,
            kind,
            "MISSING_SELECTION",
            "Target NamedSelection is missing.",
            validity=SetupValidity.MISSING_REFERENCE,
        )
    if selection.entity_kind not in expected_kinds:
        expected = "/".join(sorted(item.value for item in expected_kinds))
        return _blocked(
            record_id,
            kind,
            "WRONG_ENTITY_KIND",
            f"Target selection must contain {expected} entities.",
            validity=SetupValidity.INCOMPATIBLE,
        )
    resolution = resolutions.get(target_id)
    if resolution is None:
        return _blocked(
            record_id,
            kind,
            "UNRESOLVED_SELECTION",
            "Target selection has no current mesh resolution.",
            validity=SetupValidity.LEGACY_UNRESOLVED,
        )
    if resolution.state is not ResolutionState.RESOLVED:
        return _blocked(
            record_id,
            kind,
            resolution.reason_code or f"{resolution.state.value}_SELECTION",
            resolution.message,
            validity=_selection_validity(resolution),
        )
    if not resolution.transient_indices:
        return _blocked(
            record_id,
            kind,
            "EMPTY_SELECTION",
            "Target NamedSelection contains no resolved entities.",
            validity=SetupValidity.INCOMPATIBLE,
        )
    return SetupRecordStatus(
        record_id,
        kind,
        SetupReadiness.READY,
        "READY",
        "Record is valid for renderer-neutral overlay projection.",
        SetupValidity.VALID,
        True,
    )


def _parameter_status(
    record: object,
    kind: SetupRecordKind,
    status: SetupRecordStatus,
    *,
    material_ids: set[str],
    resolutions: Mapping[str, ResolutionResult],
    mesh: MeshData | None,
    project_units: UnitSystem | None,
) -> SetupRecordStatus:
    if kind is SetupRecordKind.MATERIAL_REGION:
        material_id = str(getattr(record, "material_id", ""))
        if not material_id or material_id not in material_ids:
            return _blocked(
                record.id,
                kind,
                "MISSING_MATERIAL",
                "The assigned project material does not exist.",
                validity=SetupValidity.MISSING_REFERENCE,
            )
    elif kind is SetupRecordKind.FIXED_SUPPORT:
        dofs = tuple(getattr(record, "translational_dofs", ()))
        if not dofs or len(set(dofs)) != len(dofs) or any(item not in {1, 2, 3} for item in dofs):
            return _blocked(
                record.id,
                kind,
                "INVALID_TRANSLATIONAL_DOFS",
                "Fixed support DOFs must be unique translational DOFs 1 through 3.",
            )
    elif kind is SetupRecordKind.PRESCRIBED_DISPLACEMENT:
        components = tuple(getattr(record, "components", ()))
        if not components or all(component is None for component in components):
            return _blocked(
                record.id,
                kind,
                "NO_CONSTRAINED_TRANSLATIONAL_DOF",
                "At least one prescribed translational component is required.",
            )
        expected = None if project_units is None else project_units.length
        if any(
            component is not None and not _valid_quantity(component, expected)
            for component in components
        ):
            return _blocked(
                record.id,
                kind,
                "INVALID_DISPLACEMENT_QUANTITY",
                (
                    "Constrained displacement components must be finite and use "
                    "the project length unit."
                ),
            )
        if getattr(record, "coordinate_system", "") != "GLOBAL":
            return _blocked(
                record.id,
                kind,
                "UNSUPPORTED_COORDINATE_SYSTEM",
                "Only the GLOBAL coordinate system is supported.",
            )
    elif kind is SetupRecordKind.FORCE:
        magnitude = getattr(record, "magnitude", None)
        if (
            not isinstance(magnitude, Quantity)
            or not math.isfinite(magnitude.value)
            or magnitude.value == 0.0
            or magnitude.unit not in {"N", "kN"}
        ):
            return _blocked(
                record.id,
                kind,
                "INVALID_FORCE_QUANTITY",
                "Force magnitude must be finite, non-zero, and use N or kN.",
            )
        if force_direction(record) == (0.0, 0.0, 0.0):
            return _blocked(
                record.id,
                kind,
                "INVALID_FORCE_DIRECTION",
                "Force direction must be a finite non-zero 3D vector.",
            )
        if record.coordinate_system != "GLOBAL":
            return _blocked(
                record.id,
                kind,
                "UNSUPPORTED_COORDINATE_SYSTEM",
                "Only the GLOBAL coordinate system is supported.",
            )
        if record.application_mode != "PER_NODE":
            return _blocked(
                record.id,
                kind,
                "UNSUPPORTED_APPLICATION_MODE",
                "Only PER_NODE force application is supported.",
            )
    elif kind is SetupRecordKind.PRESSURE:
        expected = None if project_units is None else project_units.pressure
        if not _valid_quantity(getattr(record, "value", None), expected):
            return _blocked(
                record.id,
                kind,
                "INVALID_PRESSURE_QUANTITY",
                "Pressure must be finite and use the project pressure unit.",
            )
        return _surface_status(record, kind, status, resolutions, mesh)
    elif kind is SetupRecordKind.TEMPERATURE:
        expected = None if project_units is None else project_units.temperature
        if not _valid_quantity(getattr(record, "value", None), expected):
            return _blocked(
                record.id,
                kind,
                "INVALID_TEMPERATURE_QUANTITY",
                "Temperature must be finite and use the project temperature unit.",
            )
    elif kind is SetupRecordKind.HEAT_FLUX:
        expected = None if project_units is None else _heat_flux_unit(project_units)
        if not _valid_quantity(getattr(record, "value", None), expected):
            return _blocked(
                record.id,
                kind,
                "INVALID_HEAT_FLUX_QUANTITY",
                "Heat flux must be finite and use the project power/area unit.",
            )
        return _surface_status(record, kind, status, resolutions, mesh)
    return status


def _surface_status(
    record: object,
    kind: SetupRecordKind,
    status: SetupRecordStatus,
    resolutions: Mapping[str, ResolutionResult],
    mesh: MeshData | None,
) -> SetupRecordStatus:
    if mesh is None:
        return _blocked(
            record.id,
            kind,
            "MISSING_MESH_CONTEXT",
            "Surface setup validation requires the active in-memory mesh.",
            validity=SetupValidity.INCOMPATIBLE,
        )
    indices = resolutions[record.target_selection_id].transient_indices
    for index in indices:
        try:
            surface_cell_centroid_and_normal(mesh, index)
        except ValueError as exc:
            reason = str(exc)
            message = (
                "Pressure and heat flux require triangle/quad/polygon surface cells."
                if reason == "REQUIRES_EXPLICIT_SURFACE_SELECTION"
                else "The selected surface contains invalid or degenerate geometry."
            )
            return _blocked(
                record.id,
                kind,
                reason,
                message,
                validity=SetupValidity.INCOMPATIBLE,
            )
    return status


def _block_overlapping_materials(
    records: Sequence[MaterialAssignmentRecord],
    resolutions: Mapping[str, ResolutionResult],
    statuses: dict[str, SetupRecordStatus],
) -> None:
    ready = [record for record in records if _conflict_eligible(statuses.get(record.id))]
    overlapping: set[str] = set()
    for index, left in enumerate(ready):
        left_ids = set(resolutions[left.target_selection_id].transient_indices)
        for right in ready[index + 1 :]:
            right_ids = set(resolutions[right.target_selection_id].transient_indices)
            if left_ids.intersection(right_ids):
                overlapping.update((left.id, right.id))
    for record_id in overlapping:
        statuses[record_id] = _blocked(
            record_id,
            SetupRecordKind.MATERIAL_REGION,
            "OVERLAPPING_MATERIAL_ASSIGNMENT",
            "Enabled material assignments must not overlap cells.",
            validity=SetupValidity.CONFLICT,
            overlay_renderable=True,
        )


def _block_fixed_displacement_conflicts(
    supports: Sequence[FixedSupportRecord],
    displacements: Sequence[PrescribedDisplacementRecord],
    resolutions: Mapping[str, ResolutionResult],
    statuses: dict[str, SetupRecordStatus],
) -> None:
    conflicting_supports: set[str] = set()
    conflicting_displacements: set[str] = set()
    for support in supports:
        if not _conflict_eligible(statuses.get(support.id)):
            continue
        support_points = set(resolutions[support.target_selection_id].transient_indices)
        for displacement in displacements:
            if not _conflict_eligible(statuses.get(displacement.id)):
                continue
            displacement_points = set(
                resolutions[displacement.target_selection_id].transient_indices
            )
            if not support_points.intersection(displacement_points):
                continue
            for dof in support.translational_dofs:
                value = displacement.components[dof - 1]
                if value is not None and value.value != 0.0:
                    conflicting_supports.add(support.id)
                    conflicting_displacements.add(displacement.id)
    for record_id in conflicting_supports:
        statuses[record_id] = _blocked(
            record_id,
            SetupRecordKind.FIXED_SUPPORT,
            "FIXED_SUPPORT_DISPLACEMENT_CONFLICT",
            "A fixed DOF overlaps a non-zero prescribed displacement.",
            validity=SetupValidity.CONFLICT,
            overlay_renderable=True,
        )
    for record_id in conflicting_displacements:
        statuses[record_id] = _blocked(
            record_id,
            SetupRecordKind.PRESCRIBED_DISPLACEMENT,
            "FIXED_SUPPORT_DISPLACEMENT_CONFLICT",
            "A non-zero prescribed displacement overlaps a fixed DOF.",
            validity=SetupValidity.CONFLICT,
            overlay_renderable=True,
        )


def _block_displacement_conflicts(
    records: Sequence[PrescribedDisplacementRecord],
    resolutions: Mapping[str, ResolutionResult],
    statuses: dict[str, SetupRecordStatus],
) -> None:
    conflicting: set[str] = set()
    eligible = [record for record in records if _conflict_eligible(statuses.get(record.id))]
    for index, left in enumerate(eligible):
        left_points = set(resolutions[left.target_selection_id].transient_indices)
        for right in eligible[index + 1 :]:
            if not left_points.intersection(
                resolutions[right.target_selection_id].transient_indices
            ):
                continue
            for left_value, right_value in zip(left.components, right.components, strict=True):
                if left_value is None or right_value is None:
                    continue
                if (left_value.value, left_value.unit) != (right_value.value, right_value.unit):
                    conflicting.update((left.id, right.id))
    for record_id in conflicting:
        statuses[record_id] = _blocked(
            record_id,
            SetupRecordKind.PRESCRIBED_DISPLACEMENT,
            "CONFLICTING_PRESCRIBED_DISPLACEMENT",
            "Enabled prescribed displacements disagree on the same point and DOF.",
            validity=SetupValidity.CONFLICT,
            overlay_renderable=True,
        )


def _blocked(
    record_id: str,
    kind: SetupRecordKind,
    reason_code: str,
    message: str,
    *,
    validity: SetupValidity = SetupValidity.INVALID_PARAMETERS,
    overlay_renderable: bool = False,
) -> SetupRecordStatus:
    return SetupRecordStatus(
        record_id,
        kind,
        SetupReadiness.BLOCKED,
        reason_code,
        message,
        validity,
        overlay_renderable,
    )


def _selection_validity(resolution: ResolutionResult) -> SetupValidity:
    if resolution.reason_code == "LEGACY_IDENTITY_UNVERIFIED":
        return SetupValidity.LEGACY_UNRESOLVED
    if resolution.state in {ResolutionState.STALE, ResolutionState.PARTIAL}:
        return SetupValidity.STALE_SELECTION
    return SetupValidity.INCOMPATIBLE


def _expected_entity_kinds(kind: SetupRecordKind) -> frozenset[EntityKind]:
    if kind in {
        SetupRecordKind.FIXED_SUPPORT,
        SetupRecordKind.PRESCRIBED_DISPLACEMENT,
        SetupRecordKind.FORCE,
    }:
        return frozenset({EntityKind.NODE})
    if kind is SetupRecordKind.TEMPERATURE:
        return frozenset({EntityKind.NODE, EntityKind.CELL})
    return frozenset({EntityKind.CELL})


def _valid_quantity(value: object, expected_unit: str | None) -> bool:
    return bool(
        isinstance(value, Quantity)
        and math.isfinite(value.value)
        and value.unit
        and (expected_unit is None or value.unit == expected_unit)
    )


def _heat_flux_unit(units: UnitSystem) -> str:
    return f"{units.power}/{units.length}^2"


def _cell_at_index(mesh: MeshData, cell_index: int) -> tuple[str, tuple[int, ...]]:
    if cell_index < 0:
        raise ValueError("INVALID_SURFACE_CONNECTIVITY")
    remaining = int(cell_index)
    for block in mesh.cells:
        if remaining < block.count:
            if remaining >= len(block.data):
                raise ValueError("INVALID_SURFACE_CONNECTIVITY")
            return block.cell_type.casefold(), block.data[remaining]
        remaining -= block.count
    raise ValueError("INVALID_SURFACE_CONNECTIVITY")


def _newell_normal(
    points: Sequence[tuple[float, float, float]],
) -> tuple[float, float, float]:
    x = y = z = 0.0
    following_points = (*points[1:], points[0])
    for current, following in zip(points, following_points, strict=True):
        x += (current[1] - following[1]) * (current[2] + following[2])
        y += (current[2] - following[2]) * (current[0] + following[0])
        z += (current[0] - following[0]) * (current[1] + following[1])
    return (x, y, z)


def _mapping(data: object, label: str) -> Mapping[str, object]:
    if not isinstance(data, Mapping):
        raise ValueError(f"{label} must be a mapping.")
    return data


def _optional_quantity_to_dict(value: Quantity | None) -> dict[str, Any] | None:
    return None if value is None else value.to_dict()


def _optional_quantity_from_dict(value: object) -> Quantity | None:
    return None if value is None else Quantity.from_dict(value)


def _scalar_record_to_dict(record: object, value_name: str) -> dict[str, Any]:
    return {
        "id": str(getattr(record, "id", "")),
        "name": str(getattr(record, "name", "")),
        "target_selection_id": str(getattr(record, "target_selection_id", "")),
        value_name: getattr(record, value_name).to_dict(),
        "enabled": bool(getattr(record, "enabled", True)),
    }


def _conflict_eligible(status: SetupRecordStatus | None) -> bool:
    return bool(
        status is not None
        and (status.state is SetupReadiness.READY or status.validity is SetupValidity.CONFLICT)
    )


__all__ = [
    "FixedSupportRecord",
    "ForceLoadRecord",
    "HeatFluxRecord",
    "MaterialAssignmentRecord",
    "MaterialReferenceError",
    "MaterialRegionRecord",
    "PrescribedDisplacementRecord",
    "PressureLoadRecord",
    "SOLVER_SETUP_SCHEMA",
    "SUPPORTED_SURFACE_CELL_TYPES",
    "SetupReadiness",
    "SetupRecordKind",
    "SetupRecordStatus",
    "SetupValidity",
    "TemperatureRecord",
    "ensure_material_deletable",
    "evaluate_solver_setup",
    "find_material_references",
    "force_direction",
    "force_vector",
    "iter_solver_setup_records",
    "setup_record_kind",
    "status_allows_overlay",
    "surface_cell_centroid_and_normal",
]
