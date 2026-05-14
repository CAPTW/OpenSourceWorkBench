from __future__ import annotations

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import (
    BoundaryCondition,
    MeshRef,
    PhysicsSetup,
    Project,
    ProjectMetadata,
    ReportConfig,
    SolverConfig,
)
from osw.core.units import Quantity, UnitSystem
from osw.core.validation import validate_mesh_sanity, validate_project_sanity
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.report_generator import build_report_model, render_report_html


def _steel() -> Material:
    return Material(
        material_id="steel",
        name="Steel",
        density=Quantity(7850.0, "kg/m^3"),
        elastic=IsotropicElastic(
            young_modulus=Quantity(210e9, "Pa"),
            poisson_ratio=0.3,
        ),
    )


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )


def test_negative_density_fails_physical_sanity() -> None:
    project = Project(
        metadata=ProjectMetadata(name="bad density"),
        materials=[
            Material(
                material_id="bad",
                name="Bad density",
                density=Quantity(-1.0, "kg/m^3"),
            )
        ],
    )

    report = validate_project_sanity(project)

    assert report.has_errors
    assert any("density must be nonnegative" in message.message for message in report.messages)


def test_nonfinite_density_fails_physical_sanity() -> None:
    project = Project(
        metadata=ProjectMetadata(name="nonfinite density"),
        materials=[
            Material(
                material_id="bad",
                name="Bad density",
                density=Quantity(float("nan"), "kg/m^3"),
            )
        ],
    )

    report = validate_project_sanity(project)

    assert report.has_errors
    assert any("density must be finite" in message.message for message in report.messages)


def test_nonpositive_viscosity_fails_physical_sanity() -> None:
    project = Project(
        metadata=ProjectMetadata(name="bad viscosity"),
        materials=[
            Material(
                material_id="water",
                name="Water",
                density=Quantity(997.0, "kg/m^3"),
                metadata={"dynamic_viscosity": {"value": 0.0, "unit": "Pa*s"}},
            )
        ],
    )

    report = validate_project_sanity(project)

    assert report.has_errors
    assert any("Viscosity must be positive" in message.message for message in report.messages)


def test_nonfinite_viscosity_fails_physical_sanity() -> None:
    project = Project(
        metadata=ProjectMetadata(name="bad viscosity"),
        materials=[
            Material(
                material_id="water",
                name="Water",
                density=Quantity(997.0, "kg/m^3"),
                metadata={"dynamic_viscosity": {"value": float("inf"), "unit": "Pa*s"}},
            )
        ],
    )

    report = validate_project_sanity(project)

    assert report.has_errors
    assert any("Viscosity must be finite" in message.message for message in report.messages)


def test_zero_mesh_cells_fail_for_mesh_payload_and_reference_metadata() -> None:
    empty_mesh = MeshData(points=((0.0, 0.0, 0.0),), cells=())
    project = Project(
        metadata=ProjectMetadata(name="empty mesh"),
        meshes=[
            MeshRef(
                ref_id="mesh-1",
                path="mesh/empty.vtu",
                format="vtu",
                metadata={"element_count": 0},
            )
        ],
    )

    mesh_report = validate_mesh_sanity(empty_mesh)
    project_report = validate_project_sanity(project, meshes={"mesh-1": empty_mesh})

    assert mesh_report.has_errors
    assert any("at least one cell" in message.message for message in mesh_report.messages)
    assert project_report.has_errors
    assert any("zero cells" in message.message for message in project_report.messages)


def test_nonfinite_mesh_metadata_cell_count_fails() -> None:
    project = Project(
        metadata=ProjectMetadata(name="nonfinite mesh count"),
        meshes=[
            MeshRef(
                ref_id="mesh-1",
                path="mesh/bad.vtu",
                format="vtu",
                metadata={"element_count": float("inf")},
            )
        ],
    )

    report = validate_project_sanity(project)

    assert report.has_errors
    assert any("cell count must be finite" in message.message for message in report.messages)


def test_unit_consistency_missing_material_and_boundary_completeness_are_reported() -> None:
    project = Project(
        metadata=ProjectMetadata(name="sanity setup"),
        units=UnitSystem.si(defaulted=True),
        physics=[
            PhysicsSetup(
                setup_id="static",
                name="Static setup",
                analysis_type="linear_static",
                boundary_conditions=[
                    BoundaryCondition(
                        name="",
                        kind="",
                        target="",
                        values={},
                    )
                ],
                material_assignments={},
            )
        ],
        solvers=[
            SolverConfig(
                solver_id="ccx",
                name="CalculiX",
                parameters={},
            )
        ],
    )

    report = validate_project_sanity(project)
    summary = report.friendly_summary()

    assert report.has_errors
    assert "Unit system defaulted to SI" in summary
    assert "Boundary condition kind is required" in summary
    assert "Boundary condition target is required" in summary
    assert "No material assignments defined" in summary
    assert "Solver convergence status not recorded" in summary


def test_missing_material_assignment_for_nonstructural_domain_is_warning() -> None:
    project = Project(
        metadata=ProjectMetadata(name="fluid setup"),
        physics=[
            PhysicsSetup(
                setup_id="fluid",
                name="Fluid setup",
                analysis_type="cfd_template",
                material_assignments={},
            )
        ],
    )

    report = validate_project_sanity(project)

    assert not report.has_errors
    assert report.has_warnings
    assert any("No material assignments defined" in message.message for message in report.messages)


def test_unknown_material_assignment_fails() -> None:
    project = Project(
        metadata=ProjectMetadata(name="unknown material"),
        materials=[_steel()],
        physics=[
            PhysicsSetup(
                setup_id="static",
                name="Static setup",
                analysis_type="linear_static",
                boundary_conditions=[
                    BoundaryCondition(
                        name="Fixed",
                        kind="displacement",
                        target="left",
                        values={"ux": 0.0},
                    )
                ],
                material_assignments={"solid": "aluminum"},
            )
        ],
    )

    report = validate_project_sanity(project, meshes=(_mesh(),))

    assert report.has_errors
    assert any("unknown material id: aluminum" in message.message for message in report.messages)


def test_structural_assignment_without_material_definitions_fails() -> None:
    project = Project(
        metadata=ProjectMetadata(name="missing material definition"),
        physics=[
            PhysicsSetup(
                setup_id="static",
                name="Static setup",
                analysis_type="linear_static",
                boundary_conditions=[
                    BoundaryCondition(
                        name="Fixed",
                        kind="displacement",
                        target="left",
                        values={"ux": 0.0},
                    )
                ],
                material_assignments={"solid": "steel"},
            )
        ],
    )

    report = validate_project_sanity(project)

    assert report.has_errors
    assert any("no material definitions" in message.message for message in report.messages)


def test_sanity_warnings_appear_in_default_report_summary() -> None:
    project = Project(
        metadata=ProjectMetadata(name="Report Sanity"),
        materials=[_steel()],
        solvers=[
            SolverConfig(
                solver_id="solver-1",
                name="Solver",
                parameters={"convergence_status": "unknown"},
            )
        ],
        report=ReportConfig(title="Report Sanity"),
    )

    model = build_report_model(project)
    html = render_report_html(model)

    assert any("Solver convergence status is" in item for item in model.warning_summary)
    assert "WARNING project.solvers[0].convergence" in html
