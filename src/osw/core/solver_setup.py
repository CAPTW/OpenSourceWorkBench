"""Typed, solver-neutral structural setup records and readiness evaluation."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .materials import Material
from .selection import EntityKind, NamedSelection
from .selection_resolution import ResolutionResult, ResolutionState
from .units import Quantity


class SetupRecordKind(StrEnum):
    MATERIAL = "material"
    FIXED_SUPPORT = "fixed_support"
    FORCE = "force"


class SetupReadiness(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"


@dataclass(frozen=True)
class MaterialAssignmentRecord:
    id: str
    name: str
    material_id: str
    target_selection_id: str
    enabled: bool = True

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
        if not isinstance(data, Mapping):
            raise ValueError("Material assignment record must be a mapping.")
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            material_id=str(data.get("material_id", "")),
            target_selection_id=str(data.get("target_selection_id", "")),
            enabled=bool(data.get("enabled", True)),
        )


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
        if not isinstance(data, Mapping):
            raise ValueError("Fixed support record must be a mapping.")
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            target_selection_id=str(data.get("target_selection_id", "")),
            translational_dofs=tuple(
                int(item)
                for item in data.get("translational_dofs", (1, 2, 3)) or ()
            ),
            enabled=bool(data.get("enabled", True)),
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
        object.__setattr__(
            self,
            "direction",
            tuple(float(item) for item in self.direction),
        )
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
        if not isinstance(data, Mapping):
            raise ValueError("Force load record must be a mapping.")
        direction = tuple(float(item) for item in data.get("direction", ()) or ())
        if len(direction) != 3:
            direction = (0.0, 0.0, 0.0)
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            target_selection_id=str(data.get("target_selection_id", "")),
            magnitude=Quantity.from_dict(data.get("magnitude")),
            direction=direction,
            coordinate_system=str(data.get("coordinate_system", "GLOBAL")),
            application_mode=str(data.get("application_mode", "PER_NODE")),
            enabled=bool(data.get("enabled", True)),
        )


@dataclass(frozen=True)
class SetupRecordStatus:
    record_id: str
    record_kind: SetupRecordKind
    state: SetupReadiness
    reason_code: str
    message: str


def force_direction(record: ForceLoadRecord) -> tuple[float, float, float]:
    if len(record.direction) != 3 or not all(
        math.isfinite(item) for item in record.direction
    ):
        return (0.0, 0.0, 0.0)
    length = math.sqrt(sum(item * item for item in record.direction))
    if not math.isfinite(length) or length <= 0.0:
        return (0.0, 0.0, 0.0)
    return tuple(item / length for item in record.direction)


def evaluate_solver_setup(
    setup: object,
    *,
    selections: Sequence[NamedSelection],
    materials: Sequence[Material],
    resolutions: Mapping[str, ResolutionResult],
) -> tuple[SetupRecordStatus, ...]:
    material_records = tuple(
        getattr(setup, "material_assignment_records", ()) or ()
    )
    support_records = tuple(getattr(setup, "fixed_support_records", ()) or ())
    force_records = tuple(getattr(setup, "force_load_records", ()) or ())
    all_records = (*material_records, *support_records, *force_records)
    id_counts = {
        record.id: sum(candidate.id == record.id for candidate in all_records)
        for record in all_records
    }
    selection_by_id = {item.id: item for item in selections}
    material_ids = {item.material_id for item in materials}
    statuses: dict[str, SetupRecordStatus] = {}

    for record in material_records:
        statuses[record.id] = _base_status(
            record,
            SetupRecordKind.MATERIAL,
            EntityKind.CELL,
            selection_by_id,
            resolutions,
            id_counts,
        )
        if statuses[record.id].state is SetupReadiness.READY and (
            not record.material_id
            or record.material_id not in material_ids
        ):
            statuses[record.id] = _blocked(
                record.id,
                SetupRecordKind.MATERIAL,
                "MISSING_MATERIAL",
                "The assigned project material does not exist.",
            )

    for record in support_records:
        statuses[record.id] = _base_status(
            record,
            SetupRecordKind.FIXED_SUPPORT,
            EntityKind.NODE,
            selection_by_id,
            resolutions,
            id_counts,
        )
        if statuses[record.id].state is SetupReadiness.READY and (
            not record.translational_dofs
            or len(set(record.translational_dofs)) != len(record.translational_dofs)
            or any(item not in {1, 2, 3} for item in record.translational_dofs)
        ):
            statuses[record.id] = _blocked(
                record.id,
                SetupRecordKind.FIXED_SUPPORT,
                "INVALID_TRANSLATIONAL_DOFS",
                "Fixed support DOFs must be unique translational DOFs 1 through 3.",
            )

    for record in force_records:
        statuses[record.id] = _base_status(
            record,
            SetupRecordKind.FORCE,
            EntityKind.NODE,
            selection_by_id,
            resolutions,
            id_counts,
        )
        if statuses[record.id].state is not SetupReadiness.READY:
            continue
        if (
            not math.isfinite(record.magnitude.value)
            or record.magnitude.unit not in {"N", "kN"}
        ):
            statuses[record.id] = _blocked(
                record.id,
                SetupRecordKind.FORCE,
                "INVALID_FORCE_QUANTITY",
                "Force magnitude must be finite and use N or kN.",
            )
        elif force_direction(record) == (0.0, 0.0, 0.0):
            statuses[record.id] = _blocked(
                record.id,
                SetupRecordKind.FORCE,
                "INVALID_FORCE_DIRECTION",
                "Force direction must be a finite non-zero 3D vector.",
            )
        elif record.coordinate_system != "GLOBAL":
            statuses[record.id] = _blocked(
                record.id,
                SetupRecordKind.FORCE,
                "UNSUPPORTED_COORDINATE_SYSTEM",
                "Only the GLOBAL coordinate system is supported.",
            )
        elif record.application_mode != "PER_NODE":
            statuses[record.id] = _blocked(
                record.id,
                SetupRecordKind.FORCE,
                "UNSUPPORTED_APPLICATION_MODE",
                "Only PER_NODE force application is supported.",
            )

    _block_overlapping_materials(material_records, resolutions, statuses)
    return tuple(statuses[record.id] for record in all_records)


def _base_status(
    record: object,
    kind: SetupRecordKind,
    expected_kind: EntityKind,
    selections: Mapping[str, NamedSelection],
    resolutions: Mapping[str, ResolutionResult],
    id_counts: Mapping[str, int],
) -> SetupRecordStatus:
    record_id = str(getattr(record, "id", ""))
    if not record_id or id_counts.get(record_id, 0) != 1:
        return _blocked(
            record_id,
            kind,
            "DUPLICATE_OR_MISSING_RECORD_ID",
            "Setup record IDs must be non-empty and unique.",
        )
    if not getattr(record, "enabled", True):
        return SetupRecordStatus(
            record_id,
            kind,
            SetupReadiness.DISABLED,
            "DISABLED",
            "Record is disabled.",
        )
    target_id = str(getattr(record, "target_selection_id", ""))
    selection = selections.get(target_id)
    if selection is None:
        return _blocked(
            record_id,
            kind,
            "MISSING_SELECTION",
            "Target NamedSelection is missing.",
        )
    if selection.entity_kind is not expected_kind:
        return _blocked(
            record_id,
            kind,
            "WRONG_ENTITY_KIND",
            f"Target selection must contain {expected_kind.value} entities.",
        )
    resolution = resolutions.get(target_id)
    if resolution is None:
        return _blocked(
            record_id,
            kind,
            "UNRESOLVED_SELECTION",
            "Target selection has no current mesh resolution.",
        )
    if resolution.state is not ResolutionState.RESOLVED:
        return _blocked(
            record_id,
            kind,
            resolution.reason_code or f"{resolution.state.value}_SELECTION",
            resolution.message,
        )
    return SetupRecordStatus(
        record_id,
        kind,
        SetupReadiness.READY,
        "READY",
        "Record is ready for overlay and prepare-only handoff.",
    )


def _block_overlapping_materials(
    records: Sequence[MaterialAssignmentRecord],
    resolutions: Mapping[str, ResolutionResult],
    statuses: dict[str, SetupRecordStatus],
) -> None:
    ready = [
        record
        for record in records
        if statuses[record.id].state is SetupReadiness.READY
    ]
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
            SetupRecordKind.MATERIAL,
            "OVERLAPPING_MATERIAL_ASSIGNMENT",
            "Enabled material assignments must not overlap cells.",
        )


def _blocked(
    record_id: str,
    kind: SetupRecordKind,
    reason_code: str,
    message: str,
) -> SetupRecordStatus:
    return SetupRecordStatus(
        record_id,
        kind,
        SetupReadiness.BLOCKED,
        reason_code,
        message,
    )


__all__ = [
    "FixedSupportRecord",
    "ForceLoadRecord",
    "MaterialAssignmentRecord",
    "SetupReadiness",
    "SetupRecordKind",
    "SetupRecordStatus",
    "evaluate_solver_setup",
    "force_direction",
]
