from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import PhysicsSetup, Project, ProjectMetadata
from osw.core.selection import EntityKind, NamedSelection
from osw.core.units import Quantity
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _apis() -> tuple[object, object, object]:
    setup = import_module("osw.core.solver_setup")
    selection = import_module("osw.core.selection")
    adapter = import_module("osw.solvers.calculix.adapter")
    if not hasattr(adapter, "prepare_solver_setup"):
        pytest.fail("pure CalculiX setup prepare mapping is missing", pytrace=False)
    return setup, selection, adapter


def _mesh(*, two_cells: bool = False) -> MeshData:
    if two_cells:
        return MeshData(
            points=(
                (0, 0, 0),
                (1, 0, 0),
                (0, 1, 0),
                (0, 0, 1),
                (1, 1, 1),
            ),
            cells=(
                MeshCellBlock(
                    "tetra",
                    (
                        (0, 1, 2, 3),
                        (1, 2, 3, 4),
                    ),
                ),
            ),
        )
    return MeshData(
        points=((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
        cells=(MeshCellBlock("tetra", ((0, 1, 2, 3),)),),
    )


def _selection(
    selection_api: object,
    selection_id: str,
    kind: EntityKind,
    ids: tuple[int | str, ...],
    *,
    mesh: MeshData | None = None,
) -> NamedSelection:
    resolution = import_module("osw.core.selection_resolution")
    fingerprint = compute_mesh_fingerprint(mesh or _mesh())
    namespace = (
        resolution.NODE_ORDINAL_NAMESPACE
        if kind is EntityKind.NODE
        else resolution.CELL_ORDINAL_NAMESPACE
    )
    locator = selection_api.EntityLocator(
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
        targets=(
            selection_api.SelectionTargetRef(
                kind,
                ids,
                "mesh-1",
                locator=locator,
            ),
        ),
    )


def test_prepare_maps_only_ready_records_to_deterministic_one_based_fragments(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api, selection_api, adapter = _apis()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *_args, **_kwargs: pytest.fail("solver execution is forbidden"),
    )
    monkeypatch.setattr(
        Path,
        "write_text",
        lambda *_args, **_kwargs: pytest.fail("file output is forbidden"),
    )
    material = Material(
        "steel",
        "Steel",
        elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
    )
    setup = PhysicsSetup(
        setup_id="structural",
        material_assignment_records=[
            api.MaterialAssignmentRecord("mat-a", "Steel", "steel", "cells")
        ],
        fixed_support_records=[
            api.FixedSupportRecord("fix-a", "Clamp", "fixed", (1, 2, 3))
        ],
        force_load_records=[
            api.ForceLoadRecord(
                "force-a",
                "Tip",
                "tip",
                Quantity(2.0, "kN"),
                (0.0, -1.0, 0.0),
            )
        ],
    )
    project = Project(
        ProjectMetadata(name="Prepared"),
        materials=[material],
        physics=setup,
        selections=[
            _selection(selection_api, "cells", EntityKind.CELL, ("0:0",)),
            _selection(selection_api, "fixed", EntityKind.NODE, (0, 2)),
            _selection(selection_api, "tip", EntityKind.NODE, (1,)),
        ],
    )

    result = adapter.prepare_solver_setup(
        project,
        mesh=_mesh(),
        mesh_ref="mesh-1",
    )

    assert result.eligible is True
    assert result.execution_mode == "prepare_only"
    assert result.element_sets == (("MAT_MAT_A", (1,)),)
    assert result.node_sets == (
        ("FIX_FIX_A", (1, 3)),
        ("FORCE_FORCE_A", (2,)),
    )
    assert "*SOLID SECTION, ELSET=MAT_MAT_A, MATERIAL=STEEL" in result.input_preview
    assert "FORCE_FORCE_A, 2, -2000" in result.input_preview
    assert not hasattr(result, "command")
    assert list(tmp_path.iterdir()) == []


def test_prepare_fails_closed_for_stale_identity_and_normalized_name_collision() -> None:
    api, selection_api, adapter = _apis()
    setup = PhysicsSetup(
        force_load_records=[
            api.ForceLoadRecord(
                "a-b",
                "One",
                "nodes",
                Quantity(1.0, "N"),
                (1.0, 0.0, 0.0),
            ),
            api.ForceLoadRecord(
                "a_b",
                "Two",
                "nodes",
                Quantity(1.0, "N"),
                (1.0, 0.0, 0.0),
            ),
        ]
    )
    project = Project(
        ProjectMetadata(name="Blocked"),
        physics=setup,
        selections=[
            _selection(selection_api, "nodes", EntityKind.NODE, (0,))
        ],
    )

    collision = adapter.prepare_solver_setup(
        project,
        mesh=_mesh(),
        mesh_ref="mesh-1",
    )
    stale = adapter.prepare_solver_setup(
        project,
        mesh=MeshData(
            points=((0, 0, 0), (2, 0, 0), (0, 1, 0), (0, 0, 1)),
            cells=(MeshCellBlock("tetra", ((0, 1, 2, 3),)),),
        ),
        mesh_ref="mesh-1",
    )

    assert collision.eligible is False
    assert "NORMALIZED_SET_NAME_COLLISION" in collision.diagnostics
    assert stale.eligible is False
    assert stale.diagnostics == (
        "a-b:MESH_FINGERPRINT_MISMATCH",
        "a_b:MESH_FINGERPRINT_MISMATCH",
        "NORMALIZED_SET_NAME_COLLISION",
    )


@pytest.mark.parametrize(
    ("young_modulus", "poisson_ratio", "expected_diagnostic"),
    (
        (
            Quantity(float("nan"), "Pa"),
            0.3,
            "mat-a:INVALID_MATERIAL_ELASTICITY",
        ),
        (
            Quantity(-1.0, "Pa"),
            0.3,
            "mat-a:INVALID_MATERIAL_ELASTICITY",
        ),
        (
            Quantity(210_000.0, "MPa"),
            0.3,
            "mat-a:MATERIAL_STRESS_UNIT_MISMATCH",
        ),
        (
            Quantity(210e9, "Pa"),
            0.5,
            "mat-a:INVALID_MATERIAL_ELASTICITY",
        ),
    ),
)
def test_prepare_fails_closed_for_invalid_material_elasticity(
    young_modulus: Quantity,
    poisson_ratio: float,
    expected_diagnostic: str,
) -> None:
    api, selection_api, adapter = _apis()
    mesh = _mesh()
    project = Project(
        ProjectMetadata(name="Invalid material"),
        materials=[
            Material(
                "steel",
                "Steel",
                elastic=IsotropicElastic(young_modulus, poisson_ratio),
            )
        ],
        physics=PhysicsSetup(
            material_assignment_records=[
                api.MaterialAssignmentRecord(
                    "mat-a",
                    "Steel",
                    "steel",
                    "cells",
                )
            ]
        ),
        selections=[
            _selection(
                selection_api,
                "cells",
                EntityKind.CELL,
                ("0:0",),
                mesh=mesh,
            )
        ],
    )

    result = adapter.prepare_solver_setup(
        project,
        mesh=mesh,
        mesh_ref="mesh-1",
    )

    assert result.eligible is False
    assert expected_diagnostic in result.diagnostics
    assert result.input_preview == ""


def test_prepare_deduplicates_material_definitions_and_blocks_name_collisions() -> None:
    api, selection_api, adapter = _apis()
    mesh = _mesh(two_cells=True)
    selections = [
        _selection(
            selection_api,
            "cells-a",
            EntityKind.CELL,
            ("0:0",),
            mesh=mesh,
        ),
        _selection(
            selection_api,
            "cells-b",
            EntityKind.CELL,
            ("0:1",),
            mesh=mesh,
        ),
    ]
    setup = PhysicsSetup(
        material_assignment_records=[
            api.MaterialAssignmentRecord("mat-a", "A", "steel", "cells-a"),
            api.MaterialAssignmentRecord("mat-b", "B", "steel", "cells-b"),
        ]
    )
    steel = Material(
        "steel",
        "Steel",
        elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
    )
    deduplicated = adapter.prepare_solver_setup(
        Project(
            ProjectMetadata(name="Deduplicated"),
            materials=[steel],
            physics=setup,
            selections=selections,
        ),
        mesh=mesh,
        mesh_ref="mesh-1",
    )

    assert deduplicated.eligible is True
    assert deduplicated.input_preview.count("*MATERIAL, NAME=STEEL") == 1

    collision = adapter.prepare_solver_setup(
        Project(
            ProjectMetadata(name="Collision"),
            materials=[
                Material(
                    "steel-a",
                    "Steel-A",
                    elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
                ),
                Material(
                    "steel-b",
                    "Steel_A",
                    elastic=IsotropicElastic(Quantity(200e9, "Pa"), 0.3),
                ),
            ],
            physics=PhysicsSetup(
                material_assignment_records=[
                    api.MaterialAssignmentRecord(
                        "mat-a",
                        "A",
                        "steel-a",
                        "cells-a",
                    ),
                    api.MaterialAssignmentRecord(
                        "mat-b",
                        "B",
                        "steel-b",
                        "cells-b",
                    ),
                ]
            ),
            selections=selections,
        ),
        mesh=mesh,
        mesh_ref="mesh-1",
    )

    assert collision.eligible is False
    assert "NORMALIZED_MATERIAL_NAME_COLLISION" in collision.diagnostics
