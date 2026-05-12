from __future__ import annotations

from osw.core.materials import IsotropicElastic, Material
from osw.core.units import Quantity
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.solvers.calculix.input_deck import (
    CalculixBoundaryCondition,
    CalculixLinearStaticCase,
    CalculixNodeSet,
)
from osw.solvers.calculix.validation import validate_calculix_case


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


def test_missing_material_is_a_friendly_validation_error() -> None:
    case = CalculixLinearStaticCase(
        case_id="missing-material",
        mesh=sample_mesh(),
        material=None,
        node_sets=(CalculixNodeSet("FIXED", (1, 4, 5, 8)),),
        boundary_conditions=(
            CalculixBoundaryCondition.fixed(name="fixed-left", node_set="FIXED"),
        ),
    )

    report = validate_calculix_case(case)

    assert report.has_errors
    assert "Material is required" in report.friendly_summary()
    assert "isotropic elastic material" in report.friendly_summary()


def test_missing_fixed_support_is_a_warning_not_a_prepare_blocker() -> None:
    case = CalculixLinearStaticCase(
        case_id="missing-bc",
        mesh=sample_mesh(),
        material=steel(),
    )

    report = validate_calculix_case(case)

    assert not report.has_errors
    assert report.has_warnings
    assert "fixed support" in report.friendly_summary()


def test_empty_mesh_is_a_validation_error() -> None:
    case = CalculixLinearStaticCase(
        case_id="empty",
        mesh=MeshData(points=(), cells=()),
        material=steel(),
    )

    report = validate_calculix_case(case)

    assert report.has_errors
    assert "Mesh must include nodes and elements" in report.friendly_summary()


def test_boundary_condition_referencing_missing_node_set_is_clear() -> None:
    case = CalculixLinearStaticCase(
        case_id="bad-bc",
        mesh=sample_mesh(),
        material=steel(),
        node_sets=(CalculixNodeSet("FIXED", (1, 4, 5, 8)),),
        boundary_conditions=(
            CalculixBoundaryCondition.fixed(name="missing-target", node_set="UNKNOWN"),
        ),
    )

    report = validate_calculix_case(case)

    assert report.has_errors
    assert "Unknown node set 'UNKNOWN'" in report.friendly_summary()


def test_boundary_condition_node_ids_must_exist_in_mesh() -> None:
    case = CalculixLinearStaticCase(
        case_id="bad-node-id",
        mesh=sample_mesh(),
        material=steel(),
        node_sets=(CalculixNodeSet("FIXED", (99,)),),
        boundary_conditions=(
            CalculixBoundaryCondition.fixed(name="fixed-left", node_set="FIXED"),
        ),
    )

    report = validate_calculix_case(case)

    assert report.has_errors
    assert (
        "Node set FIXED references node id 99 outside mesh node range"
        in report.friendly_summary()
    )
