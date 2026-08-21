from __future__ import annotations

from pathlib import Path

from helpers import assert_text_matches_golden
from osw.core.materials import IsotropicElastic, Material
from osw.core.units import Quantity
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.solvers.calculix.input_deck import (
    CalculixBoundaryCondition,
    CalculixLinearStaticCase,
    CalculixLoad,
    CalculixNodeSet,
    generate_calculix_input_deck,
)


def cantilever_case() -> CalculixLinearStaticCase:
    return CalculixLinearStaticCase(
        case_id="cantilever",
        mesh=MeshData(
            points=(
                (0.0, 0.0, 0.0),
                (1.0, 0.0, 0.0),
                (1.0, 0.2, 0.0),
                (0.0, 0.2, 0.0),
                (0.0, 0.0, 0.2),
                (1.0, 0.0, 0.2),
                (1.0, 0.2, 0.2),
                (0.0, 0.2, 0.2),
            ),
            cells=(MeshCellBlock("hexahedron", ((0, 1, 2, 3, 4, 5, 6, 7),)),),
        ),
        material=Material(
            material_id="steel",
            name="Steel",
            density=Quantity(7850.0, "kg/m^3"),
            elastic=IsotropicElastic(
                young_modulus=Quantity(210_000_000_000.0, "Pa"),
                poisson_ratio=0.3,
            ),
        ),
        node_sets=(
            CalculixNodeSet("FIXED", (1, 4, 5, 8)),
            CalculixNodeSet("TIP", (2, 3, 6, 7)),
        ),
        boundary_conditions=(CalculixBoundaryCondition.fixed(name="fixed-left", node_set="FIXED"),),
        loads=(
            CalculixLoad.force(
                name="tip-force",
                node_set="TIP",
                dof=2,
                value=-100.0,
            ),
        ),
    )


def test_cantilever_input_deck_matches_golden_fixture() -> None:
    expected = Path(__file__).with_name("cantilever_linear_static.inp").read_text(encoding="utf-8")

    assert_text_matches_golden(
        generate_calculix_input_deck(cantilever_case()),
        expected,
        label="calculix/cantilever_linear_static.inp",
    )
