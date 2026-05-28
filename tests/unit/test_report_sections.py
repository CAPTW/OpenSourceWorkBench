from __future__ import annotations

from pathlib import Path

from osw.core.boundary_curve import boundary_curve_from_xy
from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.project_schema import ScriptRef
from osw.plugins.health import PluginHealthRecord, PluginHealthStatus
from osw.post.report_sections import REPORT_SECTION_TITLES, build_report_summary
from osw.scripts.mscript.figure_dataset import (
    FigureDataset,
    FigureRecord,
    WorkspaceVariableSummary,
)
from osw.scripts.mscript.mat_model import MatFileSummary, MatVariableSummary


def test_report_summary_contains_required_sections() -> None:
    project = create_heatsink_flow_demo_project()

    summary = build_report_summary(project)

    assert summary.section_titles == REPORT_SECTION_TITLES
    assert summary.project_name == "HeatSink_Flow"
    assert summary.run_label == "Run 0001"
    assert any(
        "educational/research artifact" in block
        for block in summary.sections[-1].content_blocks
    )
    assert any(table.table_id == "project-metadata" for table in summary.tables)
    assert any(table.table_id == "validation-summary" for table in summary.tables)


def test_report_sections_bind_mesh_script_mat_figures_curves_and_plugins(
    tmp_path: Path,
) -> None:
    figure_path = tmp_path / "plot.png"
    figure_path.write_bytes(b"\x89PNG\r\n\x1a\n")
    dataset = FigureDataset(
        dataset_id="figures",
        figures=(FigureRecord("fig-1", "Plot", image_path=figure_path),),
        workspace_variables=(
            WorkspaceVariableSummary("time", "double", shape=(3,), dtype="float64"),
        ),
    )
    mat_summary = MatFileSummary(
        source_path="data.mat",
        variables=(MatVariableSummary("temperature", (3,), "float64", True, kind="numeric"),),
    )
    project = create_heatsink_flow_demo_project()
    script = ScriptRef(
        "script-preview",
        "scripts/plot.m",
        "matlab_octave",
        metadata={
            "kind": "script",
            "line_count": 12,
            "safety_summary": "0 high / 0 blocked",
            "plot_hint_count": 1,
        },
    )
    curve = boundary_curve_from_xy(
        [0, 1],
        [300, 310],
        "Temperature curve",
        curve_id="temperature-curve",
        x_unit="s",
        y_unit="K",
    )
    project = type(project)(
        metadata=project.metadata,
        units=project.units,
        materials=project.materials,
        geometry=project.geometry,
        meshes=project.meshes,
        scripts=[*project.scripts, script],
        boundary_curves=[curve],
        physics=project.physics,
        solvers=project.solvers,
        results=project.results,
        report=project.report,
        plugins=project.plugins,
        schema_version=project.schema_version,
    )
    plugin_health = (
        PluginHealthRecord(
            plugin_id="osw.report",
            display_name="Report",
            version="0.1.0",
            plugin_type="report_plugin",
            domain="REPORT",
            status=PluginHealthStatus.WARNING.value,
            dependency_status=PluginHealthStatus.OK.value,
            dependency_messages=("Optional image dependency missing",),
        ),
    )

    summary = build_report_summary(
        project,
        figure_datasets=(dataset,),
        mat_summaries=(mat_summary,),
        plugin_health=plugin_health,
    )

    table_by_id = {table.table_id: table for table in summary.tables}
    assert any("plot.m" in row for row in table_by_id["scripts-mscript-preview"].rows)
    assert any("temperature" in row for row in table_by_id["mat-workspace-variables"].rows)
    assert table_by_id["figures"].rows[0][1] == "Plot"
    assert table_by_id["boundary-curves"].rows[0][0] == "temperature-curve"
    assert table_by_id["plugin-health"].rows[0][4] == "Optional image dependency missing"
    assert summary.figure_count == 1


def test_missing_figure_artifact_becomes_warning(tmp_path: Path) -> None:
    missing = tmp_path / "missing.png"
    dataset = FigureDataset(
        dataset_id="figures",
        figures=(FigureRecord("missing", "Missing", image_path=missing),),
    )

    summary = build_report_summary(
        create_heatsink_flow_demo_project(),
        figure_datasets=(dataset,),
    )

    assert any("Figure artifact missing" in warning for warning in summary.warnings)
    assert summary.diagnostics.has_warnings
