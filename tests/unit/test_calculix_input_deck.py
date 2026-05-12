from __future__ import annotations

from osw.core.materials import IsotropicElastic, Material
from osw.core.units import Quantity
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.solvers.calculix.input_deck import (
    CalculixBoundaryCondition,
    CalculixInputDeckGenerator,
    CalculixLinearStaticCase,
    CalculixLoad,
    CalculixNodeSet,
    CalculixSurface,
    generate_calculix_input_deck,
)


def sample_mesh() -> MeshData:
    return MeshData(
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
    )


def steel() -> Material:
    return Material(
        material_id="steel",
        name="Steel",
        density=Quantity(7850.0, "kg/m^3"),
        elastic=IsotropicElastic(
            young_modulus=Quantity(210_000_000_000.0, "Pa"),
            poisson_ratio=0.3,
        ),
    )


def cantilever_case() -> CalculixLinearStaticCase:
    return CalculixLinearStaticCase(
        case_id="cantilever",
        mesh=sample_mesh(),
        material=steel(),
        node_sets=(
            CalculixNodeSet("FIXED", (1, 4, 5, 8)),
            CalculixNodeSet("TIP", (2, 3, 6, 7)),
        ),
        boundary_conditions=(
            CalculixBoundaryCondition.fixed(name="fixed-left", node_set="FIXED"),
        ),
        loads=(
            CalculixLoad.force(
                name="tip-force",
                node_set="TIP",
                dof=2,
                value=-100.0,
            ),
        ),
    )


def test_linear_static_deck_contains_core_calculix_sections() -> None:
    text = generate_calculix_input_deck(cantilever_case())

    assert "*HEADING" in text
    assert "OSW CalculiX linear static deck: cantilever" in text
    assert "*NODE" in text
    assert "1, 0, 0, 0" in text
    assert "*ELEMENT, TYPE=C3D8, ELSET=EALL" in text
    assert "1, 1, 2, 3, 4, 5, 6, 7, 8" in text
    assert "*MATERIAL, NAME=steel" in text
    assert "*ELASTIC" in text
    assert "210000000000, 0.3" in text
    assert "*DENSITY" in text
    assert "7850" in text
    assert "*BOUNDARY" in text
    assert "FIXED, 1, 3, 0" in text
    assert "*CLOAD" in text
    assert "TIP, 2, -100" in text
    assert "*END STEP" in text


def test_generator_supports_pressure_surface_loads() -> None:
    case = CalculixLinearStaticCase(
        case_id="pressure-demo",
        mesh=sample_mesh(),
        material=steel(),
        node_sets=(CalculixNodeSet("FIXED", (1, 4, 5, 8)),),
        surfaces=(CalculixSurface("TOP", ((1, "S2"),)),),
        boundary_conditions=(
            CalculixBoundaryCondition.fixed(name="fixed-left", node_set="FIXED"),
        ),
        loads=(CalculixLoad.pressure(name="top-pressure", surface="TOP", value=12.5),),
    )

    text = CalculixInputDeckGenerator().generate(case)

    assert "*SURFACE, NAME=TOP, TYPE=ELEMENT" in text
    assert "1, S2" in text
    assert "*DLOAD" in text
    assert "TOP, P, 12.5" in text


def test_unsupported_mesh_cell_type_is_reported_clearly() -> None:
    case = CalculixLinearStaticCase(
        case_id="bad-cell",
        mesh=MeshData(
            points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            cells=(MeshCellBlock("polygon", ((0, 1, 2),)),),
        ),
        material=steel(),
        boundary_conditions=(
            CalculixBoundaryCondition.fixed(name="fixed", node_set="FIXED"),
        ),
        node_sets=(CalculixNodeSet("FIXED", (1,)),),
    )

    report = CalculixInputDeckGenerator().validate(case)

    assert report.has_errors
    assert "Unsupported CalculiX element cell type: polygon" in report.friendly_summary()
