"""Renderer-independent normalized handoff for persisted solver setup records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshData

from .project_schema import Project
from .selection import EntityKind, NamedSelection
from .selection_resolution import resolve_named_selection
from .solver_setup import (
    FixedSupportRecord,
    ForceLoadRecord,
    HeatFluxRecord,
    MaterialAssignmentRecord,
    PrescribedDisplacementRecord,
    PressureLoadRecord,
    SetupReadiness,
    SetupRecordKind,
    TemperatureRecord,
    evaluate_solver_setup,
    force_vector,
    iter_solver_setup_records,
    setup_record_kind,
)

SOLVER_SETUP_HANDOFF_SCHEMA = "osw.solver_setup_handoff.v1"


@dataclass(frozen=True)
class SetupHandoffDiagnostic:
    setup_id: str
    setup_kind: SetupRecordKind | None
    readiness: str
    reason_code: str
    message: str


@dataclass(frozen=True)
class SetupHandoffRecord:
    setup_id: str
    setup_kind: SetupRecordKind
    named_selection_id: str
    mesh_ref: str
    mesh_fingerprint: str
    entity_kind: EntityKind
    canonical_entity_refs: tuple[int | str, ...]
    resolved_entity_indices: tuple[int, ...]
    parameters_in_project_canonical_units: Mapping[str, Any]
    material_ref_if_applicable: str = ""
    adapter_capability: str = "supported"
    readiness: str = "ready"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_entity_refs",
            tuple(self.canonical_entity_refs),
        )
        object.__setattr__(
            self,
            "resolved_entity_indices",
            tuple(int(item) for item in self.resolved_entity_indices),
        )
        object.__setattr__(
            self,
            "parameters_in_project_canonical_units",
            dict(self.parameters_in_project_canonical_units),
        )


@dataclass(frozen=True)
class SolverSetupHandoff:
    schema_id: str
    adapter_id: str
    strict: bool
    ready: bool
    mesh_ref: str
    mesh_fingerprint: str
    records: tuple[SetupHandoffRecord, ...]
    diagnostics: tuple[SetupHandoffDiagnostic, ...]
    execution_mode: str = "prepare_only"


def build_solver_setup_handoff(
    project: Project,
    *,
    mesh: MeshData,
    mesh_ref: str,
    adapter_id: str,
    supported_kinds: Iterable[SetupRecordKind | str],
    strict: bool = True,
) -> SolverSetupHandoff:
    """Resolve exact persisted identity and never silently omit enabled blockers."""

    fingerprint = compute_mesh_fingerprint(mesh)
    setup = project.primary_physics
    if setup is None:
        diagnostic = SetupHandoffDiagnostic(
            "",
            None,
            "blocked",
            "MISSING_PHYSICS_SETUP",
            "The Project has no physics setup.",
        )
        return SolverSetupHandoff(
            SOLVER_SETUP_HANDOFF_SCHEMA,
            str(adapter_id),
            bool(strict),
            False,
            str(mesh_ref),
            fingerprint.digest,
            (),
            (diagnostic,),
        )

    supported = frozenset(SetupRecordKind(item) for item in supported_kinds)
    selection_by_id = {selection.id: selection for selection in project.selections}
    resolutions = {
        selection.id: resolve_named_selection(
            selection,
            mesh=mesh,
            mesh_ref=mesh_ref,
        )
        for selection in project.selections
    }
    statuses = evaluate_solver_setup(
        setup,
        selections=project.selections,
        materials=project.materials,
        resolutions=resolutions,
        mesh=mesh,
        project_units=project.units,
    )
    statuses_by_id = {status.record_id: status for status in statuses}
    records: list[SetupHandoffRecord] = []
    diagnostics = _legacy_unresolved_diagnostics(setup)

    for record in iter_solver_setup_records(setup):
        if not bool(getattr(record, "enabled", True)):
            continue
        kind = setup_record_kind(record)
        status = statuses_by_id[str(record.id)]
        if status.state is not SetupReadiness.READY:
            reason_code = _handoff_reason(kind, status.reason_code)
            diagnostics.append(
                SetupHandoffDiagnostic(
                    str(record.id),
                    kind,
                    "blocked",
                    reason_code,
                    status.message,
                )
            )
            continue
        if kind not in supported:
            diagnostics.append(
                SetupHandoffDiagnostic(
                    str(record.id),
                    kind,
                    "unsupported_by_adapter",
                    "UNSUPPORTED_BY_ADAPTER",
                    f"Adapter {adapter_id!r} does not consume {kind.value} records.",
                )
            )
            continue
        selection = selection_by_id[str(record.target_selection_id)]
        canonical_refs = _canonical_refs(selection)
        records.append(
            SetupHandoffRecord(
                setup_id=str(record.id),
                setup_kind=kind,
                named_selection_id=str(record.target_selection_id),
                mesh_ref=str(mesh_ref),
                mesh_fingerprint=fingerprint.digest,
                entity_kind=selection.entity_kind,
                canonical_entity_refs=canonical_refs,
                resolved_entity_indices=resolutions[
                    str(record.target_selection_id)
                ].transient_indices,
                parameters_in_project_canonical_units=_normalized_parameters(
                    record,
                    project,
                ),
                material_ref_if_applicable=str(getattr(record, "material_id", "") or ""),
            )
        )

    ready = not diagnostics
    normalized_records = () if strict and not ready else tuple(records)
    return SolverSetupHandoff(
        SOLVER_SETUP_HANDOFF_SCHEMA,
        str(adapter_id),
        bool(strict),
        ready,
        str(mesh_ref),
        fingerprint.digest,
        normalized_records,
        tuple(diagnostics),
    )


def _legacy_unresolved_diagnostics(setup: object) -> list[SetupHandoffDiagnostic]:
    """Fail closed for legacy records that lack canonical entity identity."""

    diagnostics: list[SetupHandoffDiagnostic] = []
    for index, boundary in enumerate(getattr(setup, "boundary_conditions", ())):
        name = str(getattr(boundary, "name", "") or f"boundary {index + 1}")
        diagnostics.append(
            SetupHandoffDiagnostic(
                f"legacy:boundary_condition:{index}",
                None,
                "legacy_unresolved",
                "LEGACY_UNRESOLVED",
                (
                    f"Legacy boundary condition {name!r} has no safely normalized "
                    "canonical NamedSelection binding."
                ),
            )
        )
    for target_ref in sorted(getattr(setup, "material_assignments", {})):
        diagnostics.append(
            SetupHandoffDiagnostic(
                f"legacy:material_assignment:{target_ref}",
                None,
                "legacy_unresolved",
                "LEGACY_UNRESOLVED",
                (
                    f"Legacy material assignment target {target_ref!r} has no safely "
                    "normalized canonical NamedSelection binding."
                ),
            )
        )
    return diagnostics


def _canonical_refs(selection: NamedSelection) -> tuple[int | str, ...]:
    refs: list[int | str] = []
    for target in selection.targets:
        locator = target.locator
        if locator is None:
            return ()
        refs.extend(locator.entity_ids)
    return tuple(refs)


def _normalized_parameters(record: object, project: Project) -> dict[str, Any]:
    if isinstance(record, MaterialAssignmentRecord):
        return {"material_id": record.material_id}
    if isinstance(record, FixedSupportRecord):
        return {"translational_dofs": record.translational_dofs}
    if isinstance(record, PrescribedDisplacementRecord):
        return {
            "ux": None if record.ux is None else record.ux.value,
            "uy": None if record.uy is None else record.uy.value,
            "uz": None if record.uz is None else record.uz.value,
            "unit": project.units.length,
            "coordinate_system": record.coordinate_system,
        }
    if isinstance(record, ForceLoadRecord):
        return {
            "vector": force_vector(record, target_unit=project.units.force),
            "unit": project.units.force,
            "coordinate_system": record.coordinate_system,
            "application_mode": record.application_mode,
        }
    if isinstance(record, PressureLoadRecord):
        return {"value": record.value.value, "unit": record.value.unit}
    if isinstance(record, TemperatureRecord):
        return {"value": record.value.value, "unit": record.value.unit}
    if isinstance(record, HeatFluxRecord):
        return {"value": record.value.value, "unit": record.value.unit}
    raise TypeError(f"Unsupported setup handoff record: {type(record).__name__}")


def _handoff_reason(kind: SetupRecordKind, reason_code: str) -> str:
    if (
        kind in {SetupRecordKind.PRESSURE, SetupRecordKind.HEAT_FLUX}
        and reason_code == "REQUIRES_EXPLICIT_SURFACE_SELECTION"
    ):
        return "REQUIRES_FACE_IDENTITY_OR_ADAPTER_SURFACE_MAPPING"
    return reason_code


__all__ = [
    "SOLVER_SETUP_HANDOFF_SCHEMA",
    "SetupHandoffDiagnostic",
    "SetupHandoffRecord",
    "SolverSetupHandoff",
    "build_solver_setup_handoff",
]
