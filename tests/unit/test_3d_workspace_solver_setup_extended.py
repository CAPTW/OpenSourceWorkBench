from __future__ import annotations

import json
from dataclasses import fields
from importlib import import_module

import pytest

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import PhysicsSetup, Project, ProjectMetadata
from osw.core.selection import EntityKind, EntityLocator, NamedSelection, SelectionTargetRef
from osw.core.selection_resolution import (
    CELL_ORDINAL_NAMESPACE,
    NODE_ORDINAL_NAMESPACE,
    resolve_named_selection,
)
from osw.core.units import Quantity, UnitSystem
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _api() -> object:
    return import_module("osw.core.solver_setup")


def _mesh() -> MeshData:
    return MeshData(
        points=((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("tetra", ((0, 1, 2, 3),)),
        ),
    )


def _selection(
    selection_id: str,
    kind: EntityKind,
    ids: tuple[int | str, ...],
) -> NamedSelection:
    mesh = _mesh()
    fingerprint = compute_mesh_fingerprint(mesh)
    namespace = NODE_ORDINAL_NAMESPACE if kind is EntityKind.NODE else CELL_ORDINAL_NAMESPACE
    locator = EntityLocator(
        fingerprint.schema,
        "mesh-1",
        fingerprint.digest,
        kind,
        namespace,
        ids,
    )
    return NamedSelection(
        selection_id,
        selection_id,
        entity_kind=kind,
        targets=(SelectionTargetRef(kind, ids, "mesh-1", locator=locator),),
    )


def _context() -> tuple[MeshData, tuple[NamedSelection, ...], dict[str, object]]:
    mesh = _mesh()
    selections = (
        _selection("nodes", EntityKind.NODE, (0, 1)),
        _selection("fixed-nodes", EntityKind.NODE, (0,)),
        _selection("move-nodes", EntityKind.NODE, (1,)),
        _selection("surface", EntityKind.CELL, ("0:0",)),
        _selection("volume", EntityKind.CELL, ("1:0",)),
    )
    resolutions = {
        selection.id: resolve_named_selection(
            selection,
            mesh=mesh,
            mesh_ref="mesh-1",
        )
        for selection in selections
    }
    return mesh, selections, resolutions


def _material() -> Material:
    return Material(
        "steel",
        "Steel",
        elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
    )


def _all_records(api: object) -> PhysicsSetup:
    return PhysicsSetup(
        material_assignment_records=[
            api.MaterialAssignmentRecord("material", "Steel region", "steel", "volume")
        ],
        fixed_support_records=[api.FixedSupportRecord("fixed", "Fixed", "fixed-nodes")],
        prescribed_displacement_records=[
            api.PrescribedDisplacementRecord(
                "displacement",
                "Move X",
                "move-nodes",
                ux=Quantity(0.001, "m"),
            )
        ],
        force_load_records=[
            api.ForceLoadRecord(
                "force",
                "Force",
                "nodes",
                Quantity(10.0, "N"),
                (1.0, -1.0, 0.0),
            )
        ],
        pressure_load_records=[
            api.PressureLoadRecord(
                "pressure",
                "Pressure",
                "surface",
                Quantity(2.0, "Pa"),
            )
        ],
        temperature_records=[
            api.TemperatureRecord(
                "temperature",
                "Temperature",
                "nodes",
                Quantity(300.0, "K"),
            )
        ],
        heat_flux_records=[
            api.HeatFluxRecord(
                "heat-flux",
                "Heat flux",
                "surface",
                Quantity(-4.0, "W/m^2"),
            )
        ],
    )


def test_all_seven_typed_setup_kinds_roundtrip_in_additive_schema_0_4() -> None:
    api = _api()
    project = Project(
        ProjectMetadata(name="Seven setup kinds"),
        materials=[_material()],
        physics=_all_records(api),
    )

    payload = json.loads(json.dumps(project.to_dict()))
    reopened = Project.from_dict(payload)
    setup = reopened.primary_physics

    assert project.schema_version == "0.4"
    assert reopened.schema_version == "0.4"
    assert setup is not None
    assert [record.id for record in api.iter_solver_setup_records(setup)] == [
        "material",
        "fixed",
        "displacement",
        "force",
        "pressure",
        "temperature",
        "heat-flux",
    ]
    assert setup.prescribed_displacement_records[0].ux == Quantity(0.001, "m")
    assert setup.pressure_load_records[0].value == Quantity(2.0, "Pa")
    assert setup.temperature_records[0].value == Quantity(300.0, "K")
    assert setup.heat_flux_records[0].value == Quantity(-4.0, "W/m^2")


def test_seven_kinds_validate_against_named_selection_and_surface_topology() -> None:
    api = _api()
    mesh, selections, resolutions = _context()

    statuses = api.evaluate_solver_setup(
        _all_records(api),
        selections=selections,
        materials=(_material(),),
        resolutions=resolutions,
        mesh=mesh,
        project_units=UnitSystem.si(),
    )

    assert [status.record_kind for status in statuses] == [
        api.SetupRecordKind.MATERIAL_REGION,
        api.SetupRecordKind.FIXED_SUPPORT,
        api.SetupRecordKind.PRESCRIBED_DISPLACEMENT,
        api.SetupRecordKind.FORCE,
        api.SetupRecordKind.PRESSURE,
        api.SetupRecordKind.TEMPERATURE,
        api.SetupRecordKind.HEAT_FLUX,
    ]
    assert {status.reason_code for status in statuses} == {"READY"}
    assert all(status.overlay_renderable for status in statuses)


def test_pressure_and_heat_flux_reject_volume_cells_without_face_fabrication() -> None:
    api = _api()
    mesh, selections, resolutions = _context()
    setup = PhysicsSetup(
        pressure_load_records=[
            api.PressureLoadRecord(
                "pressure",
                "Pressure",
                "volume",
                Quantity(1.0, "Pa"),
            )
        ],
        heat_flux_records=[
            api.HeatFluxRecord(
                "heat-flux",
                "Heat flux",
                "volume",
                Quantity(1.0, "W/m^2"),
            )
        ],
    )

    statuses = api.evaluate_solver_setup(
        setup,
        selections=selections,
        materials=(),
        resolutions=resolutions,
        mesh=mesh,
        project_units=UnitSystem.si(),
    )

    assert [status.reason_code for status in statuses] == [
        "REQUIRES_EXPLICIT_SURFACE_SELECTION",
        "REQUIRES_EXPLICIT_SURFACE_SELECTION",
    ]
    assert not any(status.overlay_renderable for status in statuses)


def test_parameter_name_and_constraint_conflicts_are_deterministic() -> None:
    api = _api()
    mesh, selections, resolutions = _context()
    setup = PhysicsSetup(
        fixed_support_records=[api.FixedSupportRecord("fixed", "Clamp", "nodes", (1,))],
        prescribed_displacement_records=[
            api.PrescribedDisplacementRecord(
                "move-a",
                "Move A",
                "nodes",
                ux=Quantity(0.1, "m"),
            ),
            api.PrescribedDisplacementRecord(
                "move-b",
                "Move B",
                "nodes",
                ux=Quantity(0.2, "m"),
            ),
        ],
        force_load_records=[
            api.ForceLoadRecord(
                "force-a",
                "duplicate",
                "nodes",
                Quantity(1.0, "N"),
                (1.0, 0.0, 0.0),
            ),
            api.ForceLoadRecord(
                "force-b",
                " Duplicate ",
                "nodes",
                Quantity(1.0, "N"),
                (0.0, 1.0, 0.0),
            ),
        ],
    )

    by_id = {
        status.record_id: status
        for status in api.evaluate_solver_setup(
            setup,
            selections=selections,
            materials=(),
            resolutions=resolutions,
            mesh=mesh,
            project_units=UnitSystem.si(),
        )
    }

    assert by_id["fixed"].reason_code == "FIXED_SUPPORT_DISPLACEMENT_CONFLICT"
    assert by_id["move-a"].reason_code == "CONFLICTING_PRESCRIBED_DISPLACEMENT"
    assert by_id["move-b"].reason_code == "CONFLICTING_PRESCRIBED_DISPLACEMENT"
    assert by_id["move-a"].overlay_renderable is True
    assert by_id["force-a"].reason_code == "DUPLICATE_RECORD_NAME"
    assert by_id["force-b"].reason_code == "DUPLICATE_RECORD_NAME"


def test_product_records_and_statuses_never_store_native_backend_handles() -> None:
    api = _api()
    forbidden = {"native_actor", "vtk_id", "pyvista", "backend_index"}
    for contract in (
        api.MaterialAssignmentRecord,
        api.FixedSupportRecord,
        api.PrescribedDisplacementRecord,
        api.ForceLoadRecord,
        api.PressureLoadRecord,
        api.TemperatureRecord,
        api.HeatFluxRecord,
        api.SetupRecordStatus,
    ):
        assert forbidden.isdisjoint(field.name for field in fields(contract))


def test_extended_parameter_and_entity_failures_are_explicit() -> None:
    api = _api()
    mesh, selections, resolutions = _context()
    setup = PhysicsSetup(
        material_assignment_records=[
            api.MaterialAssignmentRecord("material", "Material", "steel", "nodes")
        ],
        fixed_support_records=[api.FixedSupportRecord("fixed", "Fixed", "surface")],
        prescribed_displacement_records=[api.PrescribedDisplacementRecord("move", "Move", "nodes")],
        force_load_records=[
            api.ForceLoadRecord(
                "force",
                "Force",
                "nodes",
                Quantity(0.0, "N"),
                (1.0, 0.0, 0.0),
            )
        ],
        pressure_load_records=[
            api.PressureLoadRecord(
                "pressure",
                "Pressure",
                "volume",
                Quantity(1.0, "Pa"),
            )
        ],
        temperature_records=[
            api.TemperatureRecord(
                "temperature",
                "Temperature",
                "nodes",
                Quantity(float("inf"), "K"),
            )
        ],
        heat_flux_records=[
            api.HeatFluxRecord(
                "flux",
                "Flux",
                "volume",
                Quantity(1.0, "W/m^2"),
            )
        ],
    )

    statuses = {
        status.record_id: status
        for status in api.evaluate_solver_setup(
            setup,
            selections=selections,
            materials=(_material(),),
            resolutions=resolutions,
            mesh=mesh,
            project_units=UnitSystem.si(),
        )
    }

    assert {record_id: status.reason_code for record_id, status in statuses.items()} == {
        "material": "WRONG_ENTITY_KIND",
        "fixed": "WRONG_ENTITY_KIND",
        "move": "NO_CONSTRAINED_TRANSLATIONAL_DOF",
        "force": "INVALID_FORCE_QUANTITY",
        "pressure": "REQUIRES_EXPLICIT_SURFACE_SELECTION",
        "temperature": "INVALID_TEMPERATURE_QUANTITY",
        "flux": "REQUIRES_EXPLICIT_SURFACE_SELECTION",
    }


def test_temperature_supports_point_and_cell_and_allowed_overlaps_remain_ready() -> None:
    api = _api()
    mesh, selections, resolutions = _context()
    setup = PhysicsSetup(
        force_load_records=[
            api.ForceLoadRecord(
                "force-a",
                "Force A",
                "nodes",
                Quantity(1.0, "N"),
                (1.0, 0.0, 0.0),
            ),
            api.ForceLoadRecord(
                "force-b",
                "Force B",
                "nodes",
                Quantity(2.0, "N"),
                (0.0, 1.0, 0.0),
            ),
        ],
        pressure_load_records=[
            api.PressureLoadRecord(
                "pressure",
                "Pressure",
                "surface",
                Quantity(1.0, "Pa"),
            )
        ],
        temperature_records=[
            api.TemperatureRecord(
                "temperature-nodes",
                "Node temperature",
                "nodes",
                Quantity(300.0, "K"),
            ),
            api.TemperatureRecord(
                "temperature-cells",
                "Cell temperature",
                "surface",
                Quantity(310.0, "K"),
            ),
        ],
        heat_flux_records=[
            api.HeatFluxRecord(
                "flux",
                "Flux",
                "surface",
                Quantity(1.0, "W/m^2"),
            )
        ],
    )

    statuses = api.evaluate_solver_setup(
        setup,
        selections=selections,
        materials=(),
        resolutions=resolutions,
        mesh=mesh,
        project_units=UnitSystem.si(),
    )

    assert {status.reason_code for status in statuses} == {"READY"}


def test_degenerate_surface_and_persisted_reference_deletion_fail_closed() -> None:
    api = _api()
    degenerate = MeshData(
        points=((0, 0, 0), (1, 0, 0), (2, 0, 0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )
    cell = NamedSelection("surface", "Surface", entity_kind=EntityKind.CELL)
    resolution_api = import_module("osw.core.selection_resolution")
    resolved = resolution_api.ResolutionResult(
        state=resolution_api.ResolutionState.RESOLVED,
        transient_indices=(0,),
        total_requested=1,
        resolved_count=1,
        reason_code="RESOLVED",
        message="Resolved.",
    )
    status = api.evaluate_solver_setup(
        PhysicsSetup(
            pressure_load_records=[
                api.PressureLoadRecord(
                    "pressure",
                    "Pressure",
                    "surface",
                    Quantity(1.0, "Pa"),
                )
            ]
        ),
        selections=(cell,),
        materials=(),
        resolutions={"surface": resolved},
        mesh=degenerate,
        project_units=UnitSystem.si(),
    )[0]
    assert status.reason_code == "DEGENERATE_SURFACE_NORMAL"
    assert status.overlay_renderable is False

    project = Project(
        ProjectMetadata(name="Material references"),
        materials=[_material()],
        physics=PhysicsSetup(
            material_assignment_records=[
                api.MaterialAssignmentRecord(
                    "material",
                    "Steel region",
                    "steel",
                    "surface",
                    enabled=False,
                )
            ]
        ),
    )
    assert api.find_material_references(project, "steel") == ("material (Steel region)",)
    with pytest.raises(api.MaterialReferenceError, match="material.*Steel region"):
        api.ensure_material_deletable(project, "steel")


def test_all_setup_kinds_participate_in_named_selection_delete_guard() -> None:
    api = _api()
    selection_api = import_module("osw.core.selection_resolution")
    setup = PhysicsSetup(
        material_assignment_records=[
            api.MaterialAssignmentRecord("material", "Region", "steel", "target")
        ],
        fixed_support_records=[api.FixedSupportRecord("fixed", "Clamp", "target")],
        prescribed_displacement_records=[
            api.PrescribedDisplacementRecord(
                "move",
                "Move",
                "target",
                ux=Quantity(0.0, "m"),
            )
        ],
        force_load_records=[
            api.ForceLoadRecord(
                "force",
                "Force",
                "target",
                Quantity(1.0, "N"),
                (1.0, 0.0, 0.0),
            )
        ],
        pressure_load_records=[
            api.PressureLoadRecord(
                "pressure",
                "Pressure",
                "target",
                Quantity(1.0, "Pa"),
            )
        ],
        temperature_records=[
            api.TemperatureRecord(
                "temperature",
                "Temperature",
                "target",
                Quantity(300.0, "K"),
            )
        ],
        heat_flux_records=[
            api.HeatFluxRecord(
                "flux",
                "Flux",
                "target",
                Quantity(1.0, "W/m^2"),
            )
        ],
    )
    project = Project(ProjectMetadata(name="References"), physics=setup)

    references = selection_api.find_named_selection_references(project, "target")

    assert [(item.reference_kind, item.owner_id) for item in references] == [
        ("material_assignment", "material (Region)"),
        ("fixed_support", "fixed (Clamp)"),
        ("prescribed_displacement", "move (Move)"),
        ("force_load", "force (Force)"),
        ("pressure_load", "pressure (Pressure)"),
        ("temperature", "temperature (Temperature)"),
        ("heat_flux", "flux (Flux)"),
    ]
