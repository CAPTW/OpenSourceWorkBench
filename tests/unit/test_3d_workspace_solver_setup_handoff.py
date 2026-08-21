from __future__ import annotations

from dataclasses import asdict
from importlib import import_module

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import BoundaryCondition, PhysicsSetup, Project, ProjectMetadata
from osw.core.selection import EntityKind, EntityLocator, NamedSelection, SelectionTargetRef
from osw.core.selection_resolution import CELL_ORDINAL_NAMESPACE, NODE_ORDINAL_NAMESPACE
from osw.core.units import Quantity
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _apis() -> tuple[object, object]:
    return (
        import_module("osw.core.solver_setup"),
        import_module("osw.core.solver_setup_handoff"),
    )


def _mesh() -> MeshData:
    return MeshData(
        points=((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2),)),
            MeshCellBlock("tetra", ((0, 1, 2, 3),)),
        ),
    )


def _selection(selection_id: str, kind: EntityKind, ids: tuple[int | str, ...]) -> NamedSelection:
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


def _project(api: object, *, include_temperature: bool = False) -> Project:
    setup = PhysicsSetup(
        material_assignment_records=[
            api.MaterialAssignmentRecord("material", "Material", "steel", "volume")
        ],
        fixed_support_records=[api.FixedSupportRecord("fixed", "Fixed", "fixed-nodes")],
        prescribed_displacement_records=[
            api.PrescribedDisplacementRecord(
                "move",
                "Move",
                "move-nodes",
                uy=Quantity(-0.002, "m"),
            )
        ],
        force_load_records=[
            api.ForceLoadRecord(
                "force",
                "Force",
                "nodes",
                Quantity(2.0, "kN"),
                (1.0, 0.0, 0.0),
            )
        ],
        temperature_records=(
            [
                api.TemperatureRecord(
                    "temperature",
                    "Temperature",
                    "nodes",
                    Quantity(300.0, "K"),
                )
            ]
            if include_temperature
            else []
        ),
    )
    return Project(
        ProjectMetadata(name="Handoff"),
        materials=[
            Material(
                "steel",
                "Steel",
                elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
            )
        ],
        physics=setup,
        selections=[
            _selection("nodes", EntityKind.NODE, (0, 2)),
            _selection("fixed-nodes", EntityKind.NODE, (0,)),
            _selection("move-nodes", EntityKind.NODE, (2,)),
            _selection("volume", EntityKind.CELL, ("1:0",)),
        ],
    )


def test_normalized_handoff_is_zero_based_renderer_independent_and_strict() -> None:
    api, handoff_api = _apis()
    result = handoff_api.build_solver_setup_handoff(
        _project(api),
        mesh=_mesh(),
        mesh_ref="mesh-1",
        adapter_id="calculix",
        supported_kinds=(
            api.SetupRecordKind.MATERIAL_REGION,
            api.SetupRecordKind.FIXED_SUPPORT,
            api.SetupRecordKind.PRESCRIBED_DISPLACEMENT,
            api.SetupRecordKind.FORCE,
        ),
        strict=True,
    )

    assert result.schema_id == "osw.solver_setup_handoff.v1"
    assert result.ready is True
    assert [record.setup_id for record in result.records] == [
        "material",
        "fixed",
        "move",
        "force",
    ]
    assert result.records[0].canonical_entity_refs == ("1:0",)
    assert result.records[0].resolved_entity_indices == (1,)
    assert result.records[1].canonical_entity_refs == (0,)
    assert result.records[1].resolved_entity_indices == (0,)
    force_parameters = result.records[-1].parameters_in_project_canonical_units
    assert force_parameters["vector"] == (2000.0, 0.0, 0.0)
    assert force_parameters["unit"] == "N"
    text = repr(asdict(result)).lower()
    assert "vtk" not in text
    assert "pyvista" not in text
    assert "native_actor" not in text


def test_strict_handoff_does_not_silently_omit_adapter_unsupported_records() -> None:
    api, handoff_api = _apis()
    result = handoff_api.build_solver_setup_handoff(
        _project(api, include_temperature=True),
        mesh=_mesh(),
        mesh_ref="mesh-1",
        adapter_id="calculix",
        supported_kinds=(
            api.SetupRecordKind.MATERIAL_REGION,
            api.SetupRecordKind.FIXED_SUPPORT,
            api.SetupRecordKind.PRESCRIBED_DISPLACEMENT,
            api.SetupRecordKind.FORCE,
        ),
        strict=True,
    )

    assert result.ready is False
    assert result.records == ()
    assert [(item.setup_id, item.reason_code) for item in result.diagnostics] == [
        ("temperature", "UNSUPPORTED_BY_ADAPTER")
    ]


def test_volume_pressure_reports_face_identity_mapping_blocker_at_handoff() -> None:
    api, handoff_api = _apis()
    project = Project(
        ProjectMetadata(name="No fabricated faces"),
        physics=PhysicsSetup(
            pressure_load_records=[
                api.PressureLoadRecord(
                    "pressure",
                    "Pressure",
                    "volume",
                    Quantity(1.0, "Pa"),
                )
            ]
        ),
        selections=[_selection("volume", EntityKind.CELL, ("1:0",))],
    )

    result = handoff_api.build_solver_setup_handoff(
        project,
        mesh=_mesh(),
        mesh_ref="mesh-1",
        adapter_id="surface-capable",
        supported_kinds=(api.SetupRecordKind.PRESSURE,),
    )

    assert result.ready is False
    assert result.records == ()
    assert result.diagnostics[0].reason_code == (
        "REQUIRES_FACE_IDENTITY_OR_ADAPTER_SURFACE_MAPPING"
    )


def test_unsafe_legacy_setup_records_remain_persisted_but_fail_handoff_closed() -> None:
    api, handoff_api = _apis()
    project = Project(
        ProjectMetadata(name="Legacy setup"),
        physics=PhysicsSetup(
            boundary_conditions=[BoundaryCondition("legacy-fixed", "fixed", "0", target="left")],
            material_assignments={"solid": "steel"},
        ),
    )

    result = handoff_api.build_solver_setup_handoff(
        project,
        mesh=_mesh(),
        mesh_ref="mesh-1",
        adapter_id="calculix",
        supported_kinds=tuple(api.SetupRecordKind),
    )

    assert result.ready is False
    assert result.records == ()
    assert [item.readiness for item in result.diagnostics] == [
        "legacy_unresolved",
        "legacy_unresolved",
    ]
    assert {item.reason_code for item in result.diagnostics} == {"LEGACY_UNRESOLVED"}
    serialized = project.to_dict()["physics"][0]
    assert serialized["boundary_conditions"][0]["name"] == "legacy-fixed"
    assert serialized["material_assignments"] == {"solid": "steel"}
