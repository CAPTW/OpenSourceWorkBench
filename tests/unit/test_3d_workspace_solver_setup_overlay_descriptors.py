from __future__ import annotations

from dataclasses import asdict
from importlib import import_module

from osw.core.materials import Material
from osw.core.project_schema import PhysicsSetup
from osw.core.selection import EntityKind, EntityLocator, NamedSelection, SelectionTargetRef
from osw.core.selection_resolution import CELL_ORDINAL_NAMESPACE, NODE_ORDINAL_NAMESPACE
from osw.core.units import Quantity, UnitSystem
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _mesh() -> MeshData:
    return MeshData(
        points=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
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


def test_renderer_neutral_descriptors_preserve_canonical_identity_and_physics() -> None:
    setup_api = import_module("osw.core.solver_setup")
    view_api = import_module("osw.gui.setup_overlay_view_model")
    mesh = _mesh()
    selections = (
        _selection("nodes", EntityKind.NODE, (0, 2)),
        _selection("surface", EntityKind.CELL, ("0:0",)),
    )
    resolution_api = import_module("osw.core.selection_resolution")
    resolutions = {
        selection.id: resolution_api.resolve_named_selection(
            selection,
            mesh=mesh,
            mesh_ref="mesh-1",
        )
        for selection in selections
    }
    setup = PhysicsSetup(
        force_load_records=[
            setup_api.ForceLoadRecord(
                "force",
                "Force",
                "nodes",
                Quantity(10.0, "N"),
                (-2.0, 0.0, 0.0),
            )
        ],
        pressure_load_records=[
            setup_api.PressureLoadRecord(
                "pressure",
                "Pressure",
                "surface",
                Quantity(5.0, "Pa"),
            )
        ],
        heat_flux_records=[
            setup_api.HeatFluxRecord(
                "flux",
                "Flux",
                "surface",
                Quantity(-2.0, "W/m^2"),
            )
        ],
    )
    statuses = {
        status.record_id: status
        for status in setup_api.evaluate_solver_setup(
            setup,
            selections=selections,
            materials=(),
            resolutions=resolutions,
            mesh=mesh,
            project_units=UnitSystem.si(),
        )
    }

    descriptors = view_api.build_setup_overlay_descriptors(
        setup,
        mesh=mesh,
        mesh_ref="mesh-1",
        selections=selections,
        resolutions=resolutions,
        statuses=statuses,
    )

    assert [item.setup_id for item in descriptors] == ["force", "pressure", "flux"]
    assert all(item.schema_id == "osw.solver_setup_overlay.v1" for item in descriptors)
    assert descriptors[0].canonical_entity_refs == (0, 2)
    assert descriptors[0].glyph_vectors == ((-1.0, 0.0, 0.0),) * 2
    assert descriptors[1].canonical_entity_refs == ("0:0",)
    assert descriptors[1].glyph_points == ((1 / 3, 1 / 3, 0.0),)
    assert descriptors[1].glyph_vectors == ((0.0, 0.0, -1.0),)
    assert descriptors[2].glyph_vectors == ((0.0, 0.0, -1.0),)
    assert all(
        item.mesh_fingerprint == compute_mesh_fingerprint(mesh).digest for item in descriptors
    )
    serialized = repr([asdict(item) for item in descriptors]).lower()
    assert "vtk" not in serialized
    assert "pyvista" not in serialized
    assert "native_actor" not in serialized


def test_actor_specs_use_bounded_target_and_glyph_semantic_ids() -> None:
    setup_api = import_module("osw.core.solver_setup")
    view_api = import_module("osw.gui.setup_overlay_view_model")
    mesh = _mesh()
    surface = _selection("surface", EntityKind.CELL, ("0:0",))
    resolution_api = import_module("osw.core.selection_resolution")
    resolution = resolution_api.resolve_named_selection(
        surface,
        mesh=mesh,
        mesh_ref="mesh-1",
    )
    setup = PhysicsSetup(
        pressure_load_records=[
            setup_api.PressureLoadRecord(
                "pressure",
                "Pressure",
                "surface",
                Quantity(5.0, "Pa"),
            )
        ]
    )
    status = setup_api.evaluate_solver_setup(
        setup,
        selections=(surface,),
        materials=(),
        resolutions={"surface": resolution},
        mesh=mesh,
        project_units=UnitSystem.si(),
    )[0]

    specs = view_api.build_setup_overlay_specs(
        setup,
        mesh=mesh,
        mesh_ref="mesh-1",
        selections=(surface,),
        resolutions={"surface": resolution},
        statuses={"pressure": status},
    )

    assert [item.actor_key for item in specs] == [
        "setup_target:pressure",
        "setup_glyph:pressure",
    ]
    assert {item.overlay_role for item in specs} == {"target", "glyph"}
    assert all(item.record_id == "pressure" for item in specs)
    assert len([item for item in specs if item.overlay_role == "target"]) == 1
    assert len([item for item in specs if item.overlay_role == "glyph"]) == 1


def test_material_support_displacement_and_temperature_descriptors_are_typed() -> None:
    setup_api = import_module("osw.core.solver_setup")
    view_api = import_module("osw.gui.setup_overlay_view_model")
    resolution_api = import_module("osw.core.selection_resolution")
    mesh = _mesh()
    nodes = _selection("nodes", EntityKind.NODE, (0, 2))
    surface = _selection("surface", EntityKind.CELL, ("0:0",))
    selections = (nodes, surface)
    resolutions = {
        selection.id: resolution_api.resolve_named_selection(
            selection,
            mesh=mesh,
            mesh_ref="mesh-1",
        )
        for selection in selections
    }
    setup = PhysicsSetup(
        material_assignment_records=[
            setup_api.MaterialAssignmentRecord(
                "material",
                "Material",
                "steel",
                "surface",
            )
        ],
        fixed_support_records=[setup_api.FixedSupportRecord("fixed", "Fixed", "nodes")],
        prescribed_displacement_records=[
            setup_api.PrescribedDisplacementRecord(
                "move",
                "Move",
                "nodes",
                ux=Quantity(0.0, "m"),
            )
        ],
        temperature_records=[
            setup_api.TemperatureRecord(
                "temperature",
                "Temperature",
                "nodes",
                Quantity(300.0, "K"),
            )
        ],
    )
    statuses = {
        status.record_id: status
        for status in setup_api.evaluate_solver_setup(
            setup,
            selections=selections,
            materials=(Material("steel", "Steel"),),
            resolutions=resolutions,
            mesh=mesh,
            project_units=UnitSystem.si(),
        )
    }

    descriptors = view_api.build_setup_overlay_descriptors(
        setup,
        mesh=mesh,
        mesh_ref="mesh-1",
        selections=selections,
        resolutions=resolutions,
        statuses=statuses,
    )
    specs = view_api.build_setup_overlay_specs(
        setup,
        mesh=mesh,
        mesh_ref="mesh-1",
        selections=selections,
        resolutions=resolutions,
        statuses=statuses,
    )

    assert [item.overlay_role for item in descriptors] == [
        "target",
        "glyph",
        "glyph",
        "target",
    ]
    assert descriptors[2].glyph_points == ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    assert descriptors[2].glyph_vectors == ()
    assert descriptors[3].entity_kind is EntityKind.NODE
    assert [item.actor_key for item in specs] == [
        "setup_target:material",
        "setup_glyph:fixed",
        "setup_glyph:move",
        "setup_target:temperature",
    ]
