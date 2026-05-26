"""Curated demo ProjectSchema instances used by the frozen GUI baseline."""

from __future__ import annotations

from .materials import builtin_materials
from .project_schema import (
    BoundaryCondition,
    GeometryRef,
    MeshRef,
    PhysicsSetup,
    PluginRef,
    Project,
    ProjectMetadata,
    ReportConfig,
    ResultRef,
    ScriptRef,
    SolverConfig,
)
from .units import default_si_units


def create_heatsink_flow_demo_project() -> Project:
    """Return the HeatSink_Flow project that backs the visual shell mock data."""

    solver = SolverConfig(
        solver_id="cht-solver",
        solver="chtSolver",
        name="chtSolver",
        time_scheme="Steady-State",
        linear_solver="GMRES",
        preconditioner="AMG",
        convergence_tolerance=1.0e-6,
        max_iterations=125,
        settings={"settings_file": "settings.json"},
    )
    boundaries = [
        BoundaryCondition("inlet", type="Velocity Inlet", value="3.0 m/s", target="inlet"),
        BoundaryCondition("outlet", type="Pressure Outlet", value="0 Pa", target="outlet"),
        BoundaryCondition("wall_heatsink", type="Wall (No Slip)", value="—", target="wall"),
        BoundaryCondition(
            "base_bottom",
            type="Heat Flux",
            value="1.0e5 W/m²",
            target="base_bottom",
        ),
        BoundaryCondition("symmetry", type="Symmetry", value="—", target="symmetry"),
    ]
    return Project(
        schema_version="0.1",
        metadata=ProjectMetadata(
            name="HeatSink_Flow",
            description="Demo conjugate heat transfer project for the OSW visual shell.",
            author="OpenSolver Workbench",
            tags=["demo", "cfd", "heat-transfer"],
        ),
        unit_system=default_si_units(),
        materials=[builtin_materials().get("aluminum-6061")],
        geometry_refs=[
            GeometryRef("geom-heatsink", "geometry/heatsink.step", "STEP", name="heatsink.step"),
            GeometryRef("geom-enclosure", "geometry/enclosure.stp", "STP", name="enclosure.stp"),
            GeometryRef(
                "geom-fluid-domain",
                "geometry/fluid_domain.csg",
                "CSG",
                name="fluid_domain.csg",
            ),
        ],
        mesh_refs=[
            MeshRef(
                "mesh-main",
                "mesh/mesh.msh",
                "MSH",
                name="mesh.msh",
                status="complete",
                cell_count=1_200_000,
                face_count=3_800_000,
                quality_summary="Mesh skewness is high in 142 cells",
            ),
            MeshRef(
                "mesh-stats",
                "mesh/mesh_stats.txt",
                "TXT",
                name="mesh_stats.txt",
                role="summary",
            ),
        ],
        physics=[
            PhysicsSetup(
                setup_id="cht-flow",
                name="Conjugate heat transfer",
                domain="MULTIPHYSICS",
                analysis_type="Conjugate Heat Transfer",
                materials=["Aluminum 6061"],
                material_assignments={"heatsink": "aluminum-6061"},
                boundary_conditions=boundaries,
                solver_config=solver,
                files=["heat_transfer.yaml", "turbulence.yaml"],
            )
        ],
        solvers=[solver],
        script_refs=[
            ScriptRef(
                "script-preprocess",
                "scripts/preprocess.m",
                "matlab_octave",
                name="preprocess.m",
                role="preprocess",
            ),
            ScriptRef(
                "script-run-case",
                "scripts/run_case.m",
                "matlab_octave",
                name="run_case.m",
                role="run",
            ),
            ScriptRef(
                "script-postprocess",
                "scripts/postprocess.m",
                "matlab_octave",
                name="postprocess.m",
                role="postprocess",
            ),
        ],
        result_refs=[
            ResultRef(
                "result-run-0001",
                "results/run_0001",
                "directory",
                name="run_0001",
                run_id="run_0001",
                role="run",
            ),
            ResultRef(
                "result-fields",
                "results/run_0001/fields.ex2",
                "EX2",
                name="fields.ex2",
                run_id="run_0001",
                role="field",
            ),
            ResultRef(
                "result-residuals",
                "results/run_0001/residuals.dat",
                "DAT",
                name="residuals.dat",
                run_id="run_0001",
                role="residuals",
            ),
            ResultRef(
                "result-monitor",
                "results/run_0001/monitor.log",
                "LOG",
                name="monitor.log",
                run_id="run_0001",
                role="log",
            ),
            ResultRef(
                "result-run-0000",
                "results/run_0000",
                "directory",
                name="run_0000 (baseline)",
                run_id="run_0000",
                role="baseline",
            ),
        ],
        report=ReportConfig(
            path="reports/report.md",
            title="HeatSink_Flow Simulation Report",
            run_label="Run 0001",
            sections=["Overview", "Key Results", "Summary"],
            export_formats=["md", "pdf"],
            artifacts=["report.md", "report.pdf"],
        ),
        plugins=[
            PluginRef("octave-matlab-interface", "Octave / MATLAB Interface", True),
            PluginRef("paraview-catalyst", "ParaView Catalyst", True),
            PluginRef("mesh-quality-checker", "Mesh Quality Checker", True),
            PluginRef("report-generator", "Report Generator", True),
        ],
    )
