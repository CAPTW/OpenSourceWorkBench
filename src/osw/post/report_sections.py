"""Report section builders for ProjectSchema-backed OSW reports."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from osw.core.diagnostics import DiagnosticReport
from osw.core.project_schema import Project
from osw.core.validation import ValidationReport, validate_project_sanity
from osw.post.report_model import (
    ReportAsset,
    ReportFigure,
    ReportSection,
    ReportSummary,
    ReportTable,
)

REPORT_KNOWN_LIMITATIONS = (
    "OSW v0.1 reports are an educational/research artifact and must not be read "
    "as Industrial certification or production CAE claims.",
    "OSW is not a substitute for engineering judgment; review inputs, assumptions, "
    "units, validation notes, and tool availability before using report content.",
    "Native commercial CAD direct import is not supported in v0.1.",
    "Simulink, .slx, and .mlapp workflows are not supported.",
    "MATLAB proprietary toolbox compatibility is not guaranteed.",
    "Solver adapters are template-based unless a later report section explicitly "
    "states a bounded implemented adapter.",
    "Optional dependencies may be missing; related sections show diagnostics instead "
    "of silently assuming capability.",
    ".m scripts are executable code and require explicit preview and run actions.",
    "Figure, MAT, and BoundaryCurve data are imported or normalized evidence, not "
    "proof of physical validity.",
)

REPORT_SECTION_TITLES = (
    "Overview",
    "Project Metadata",
    "Unit System",
    "Materials",
    "Geometry References",
    "Mesh Summary",
    "Physics / Boundary Conditions",
    "Solver / Plugin / Execution Environment",
    "Scripts and M-Script Preview",
    "Run Logs and Diagnostics",
    "MAT / Workspace Variables",
    "FigureDataset / Figures",
    "Boundary Curves",
    "Results Summary",
    "Validation Summary",
    "Warnings and Known Limitations",
)


def build_report_summary(
    project: Project,
    *,
    figure_datasets: Iterable[object] | None = None,
    mesh_infos: Iterable[object] | None = None,
    mat_summaries: Iterable[object] | None = None,
    plugin_health: Iterable[object] | Mapping[str, object] | None = None,
    run_results: Iterable[object] | None = None,
    result_tables: Iterable[object] | None = None,
    validation_report: ValidationReport | None = None,
    sanity_report: ValidationReport | None = None,
    warnings: Iterable[str] | None = None,
    created_at: str = "",
) -> ReportSummary:
    """Build a deterministic report summary from project and preview data."""

    figures = list(_report_figures(figure_datasets))
    assets = list(_figure_assets(figures))
    diagnostics = DiagnosticReport()
    warning_items = list(str(item) for item in warnings or ())
    _add_missing_asset_warnings(figures, diagnostics, warning_items)

    validation = _combined_validation(
        validation_report if validation_report is not None else project.validate(),
        sanity_report if sanity_report is not None else validate_project_sanity(project),
    )
    warning_items.extend(_validation_warning_text(validation))
    warning_items.extend(_project_warning_text(project))

    tables: list[ReportTable] = []
    sections: list[ReportSection] = []

    metadata_table = _project_metadata_table(project)
    unit_table = _unit_system_table(project)
    material_table = _materials_table(project)
    geometry_table = _geometry_table(project)
    mesh_table = _mesh_table(project, mesh_infos)
    boundary_table = _boundary_condition_table(project)
    solver_table = _solver_table(project)
    plugin_table = _plugin_table(project, plugin_health)
    script_table = _script_table(project)
    run_table = _run_result_table(run_results)
    mat_table = _mat_workspace_table(project, mat_summaries, figure_datasets)
    figure_table = _figure_table(figures)
    curve_table = _boundary_curve_table(project)
    result_table = _result_refs_table(project)
    validation_table = _validation_table(validation)
    external_tables = _coerce_result_tables(result_tables)

    tables.extend(
        table
        for table in (
            metadata_table,
            unit_table,
            material_table,
            geometry_table,
            mesh_table,
            boundary_table,
            solver_table,
            plugin_table,
            script_table,
            run_table,
            mat_table,
            figure_table,
            curve_table,
            result_table,
            validation_table,
            *external_tables,
        )
        if table is not None
    )

    sections.append(
        _section(
            "overview",
            "Overview",
            (
                f"Project: {project.metadata.name or 'Untitled project'}",
                f"Run label: {project.report.run_label or 'Not recorded'}",
                "Input Summary: "
                f"{len(project.geometry)} geometry, {len(project.meshes)} mesh, "
                f"{len(project.scripts)} script, {len(project.boundary_curves)} curve, "
                f"{len(project.results)} result reference(s).",
                f"Report tables: {len(tables)}",
                f"Result Tables: {len(external_tables)} supplemental result table(s).",
                f"Report figures: {len(figures)}",
            ),
        )
    )
    sections.append(_section_for_table("project-metadata", "Project Metadata", metadata_table))
    sections.append(_section_for_table("unit-system", "Unit System", unit_table))
    sections.append(_section_for_table("materials", "Materials", material_table))
    sections.append(_section_for_table("geometry", "Geometry References", geometry_table))
    sections.append(_section_for_table("mesh-summary", "Mesh Summary", mesh_table))
    sections.append(
        _section_for_table(
            "physics-boundary-conditions",
            "Physics / Boundary Conditions",
            boundary_table,
        )
    )
    sections.append(
        _section(
            "solver-plugin-environment",
            "Solver / Plugin / Execution Environment",
            (
                f"Solver configuration rows: {len(solver_table.rows)}",
                f"Plugin health rows: {len(plugin_table.rows)}",
                "Report generation did not execute solvers, scripts, or external commands.",
            ),
            metadata={"table_ids": [solver_table.table_id, plugin_table.table_id]},
        )
    )
    sections.append(
        _section_for_table(
            "scripts-mscript-preview",
            "Scripts and M-Script Preview",
            script_table,
        )
    )
    sections.append(
        _section_for_table("run-logs-diagnostics", "Run Logs and Diagnostics", run_table)
    )
    sections.append(
        _section_for_table("mat-workspace-variables", "MAT / Workspace Variables", mat_table)
    )
    sections.append(
        _section(
            "figures",
            "FigureDataset / Figures",
            (
                f"Figure records: {len(figures)}",
                "Missing or unsupported figure artifacts are listed as warnings.",
            ),
            metadata={"table_ids": [figure_table.table_id]},
        )
    )
    sections.append(_section_for_table("boundary-curves", "Boundary Curves", curve_table))
    sections.append(_section_for_table("results-summary", "Results Summary", result_table))
    sections.append(
        _section_for_table("validation-summary", "Validation Summary", validation_table)
    )
    sections.append(
        _section(
            "warnings-known-limitations",
            "Warnings and Known Limitations",
            (
                *(warning_items or ("No report warnings.",)),
                *REPORT_KNOWN_LIMITATIONS,
            ),
            diagnostics=diagnostics,
        )
    )

    return ReportSummary(
        title=project.report.title or project.metadata.name or "OSW Report",
        project_name=project.metadata.name or "Untitled project",
        run_label=project.report.run_label,
        created_at=created_at,
        sections=tuple(sections),
        tables=tuple(tables),
        figures=tuple(figures),
        assets=tuple(assets),
        warnings=tuple(dict.fromkeys(warning_items)),
        diagnostics=diagnostics,
        metadata={
            "schema_version": project.schema_version,
            "known_limitations": list(REPORT_KNOWN_LIMITATIONS),
        },
    )


def _section(
    section_id: str,
    title: str,
    content_blocks: Iterable[str],
    *,
    diagnostics: DiagnosticReport | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ReportSection:
    return ReportSection(
        section_id=section_id,
        title=title,
        content_blocks=tuple(str(item) for item in content_blocks),
        diagnostics=diagnostics or DiagnosticReport(),
        metadata=dict(metadata or {}),
    )


def _section_for_table(section_id: str, title: str, table: ReportTable) -> ReportSection:
    content_prefix = (
        ("Result Summary table contains project result references.",)
        if section_id == "results-summary"
        else ()
    )
    return _section(
        section_id,
        title,
        (
            *content_prefix,
            f"{table.title}: {len(table.rows)} row(s).",
            "No data registered yet." if not table.rows else "See report table.",
        ),
        metadata={"table_ids": [table.table_id]},
    )


def _project_metadata_table(project: Project) -> ReportTable:
    metadata = project.metadata
    rows = (
        ("Project", metadata.name or "Untitled project"),
        ("Description", metadata.description or "No description provided."),
        ("Author", metadata.author or "Not specified"),
        ("Tags", ", ".join(metadata.tags) if metadata.tags else "None"),
        ("Created", metadata.created_at or "Not recorded"),
        ("Modified", metadata.modified_at or "Not recorded"),
        ("Schema version", project.schema_version),
        ("Report path", project.report.path),
    )
    return ReportTable("project-metadata", "Project Metadata", ("Field", "Value"), rows)


def _unit_system_table(project: Project) -> ReportTable:
    units = project.units
    rows = tuple(
        (label, str(value))
        for label, value in (
            ("Name", units.name),
            ("Length", units.length),
            ("Mass", units.mass),
            ("Time", units.time),
            ("Temperature", units.temperature),
            ("Pressure", units.pressure),
            ("Stress", units.stress),
            ("Energy", units.energy),
            ("Defaulted", "yes" if units.defaulted else "no"),
        )
    )
    return ReportTable("unit-system", "Unit System", ("Quantity", "Unit"), rows)


def _materials_table(project: Project) -> ReportTable:
    rows: list[tuple[str, str, str, str]] = []
    for material in project.materials:
        density = getattr(material, "density", None)
        elastic = getattr(material, "elastic", None)
        rows.append(
            (
                str(getattr(material, "material_id", "")),
                str(getattr(material, "name", "")),
                _quantity_text(density),
                _quantity_text(getattr(elastic, "young_modulus", None)),
            )
        )
    return ReportTable(
        "materials",
        "Materials",
        ("ID", "Name", "Density", "Young modulus"),
        tuple(rows),
    )


def _geometry_table(project: Project) -> ReportTable:
    return ReportTable(
        "geometry",
        "Geometry References",
        ("ID", "Name", "Format", "Path", "Status"),
        tuple(
            (
                ref.ref_id,
                ref.name,
                ref.format,
                ref.path,
                ref.status,
            )
            for ref in project.geometry
        ),
    )


def _mesh_table(project: Project, mesh_infos: Iterable[object] | None) -> ReportTable:
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    for mesh in project.meshes:
        info = _mesh_info_payload(mesh)
        rows.append(
            (
                mesh.ref_id,
                mesh.name,
                mesh.format or str(info.get("format", "")),
                str(_mesh_count(mesh.node_count, info, "node_count", "nodes")),
                str(_mesh_count(mesh.cell_count, info, "element_count", "elements", "cell_count")),
                _cell_types_text(info),
                _bounds_text(info),
            )
        )
    for index, info in enumerate(mesh_infos or (), start=1):
        payload = _object_to_mapping(info)
        rows.append(
            (
                str(payload.get("ref_id") or payload.get("source") or f"mesh-info-{index}"),
                str(payload.get("name") or payload.get("source_path") or payload.get("source", "")),
                str(payload.get("format", "")),
                str(payload.get("node_count", payload.get("nodes", ""))),
                str(payload.get("element_count", payload.get("elements", ""))),
                _cell_types_text(payload),
                _bounds_text(payload),
            )
        )
    return ReportTable(
        "mesh-summary",
        "Mesh Summary",
        ("ID", "Name/source", "Format", "Nodes", "Elements", "Cell types", "Bounds"),
        tuple(rows),
    )


def _boundary_condition_table(project: Project) -> ReportTable:
    rows: list[tuple[str, str, str, str, str, str]] = []
    for setup in project.physics:
        for boundary in setup.boundary_conditions:
            rows.append(
                (
                    setup.setup_id,
                    boundary.name,
                    boundary.type or boundary.kind,
                    boundary.target,
                    boundary.value or _format_mapping(boundary.values) or "—",
                    boundary.curve_id,
                )
            )
    return ReportTable(
        "boundary-conditions",
        "Physics / Boundary Conditions",
        ("Setup", "Name", "Type", "Target", "Value", "Curve ID"),
        tuple(rows),
    )


def _solver_table(project: Project) -> ReportTable:
    rows = tuple(
        (
            solver.solver_id,
            solver.name or solver.solver,
            solver.execution_mode,
            solver.time_scheme,
            solver.linear_solver,
            _format_mapping(solver.parameters),
        )
        for solver in project.solvers
    )
    return ReportTable(
        "solvers",
        "Solver Configuration",
        ("ID", "Name", "Mode", "Time scheme", "Linear solver", "Parameters"),
        rows,
    )


def _plugin_table(
    project: Project,
    plugin_health: Iterable[object] | Mapping[str, object] | None,
) -> ReportTable:
    rows: list[tuple[str, str, str, str, str]] = []
    records = (
        plugin_health.values()
        if isinstance(plugin_health, Mapping)
        else tuple(plugin_health or ())
    )
    for record in records:
        data = record.to_dict() if hasattr(record, "to_dict") else _object_to_mapping(record)
        rows.append(
            (
                str(data.get("plugin_id", "")),
                str(data.get("display_name", "")),
                str(data.get("plugin_type", "")),
                str(data.get("status", "")),
                "; ".join(str(item) for item in data.get("dependency_messages", ()) or ()),
            )
        )
    if not rows:
        rows.extend(
            (
                plugin.plugin_id,
                plugin.display_name,
                "project_ref",
                "enabled" if plugin.enabled else "disabled",
                "",
            )
            for plugin in project.plugins
        )
    return ReportTable(
        "plugin-health",
        "Plugin Health",
        ("ID", "Name", "Type", "Status", "Diagnostics"),
        tuple(rows),
    )


def _script_table(project: Project) -> ReportTable:
    rows: list[tuple[str, str, str, str, str, str, str]] = []
    for script in project.scripts:
        metadata = script.metadata if isinstance(script.metadata, dict) else {}
        preview = metadata.get("preview") if isinstance(metadata.get("preview"), dict) else {}
        safety = (
            metadata.get("safety_summary")
            or _preview_metadata(preview).get("safety_summary", "")
        )
        signature = (
            metadata.get("raw_signature")
            or metadata.get("function_name")
            or _signature_text(preview.get("function_signature"))
        )
        rows.append(
            (
                script.ref_id,
                script.name,
                script.language,
                str(metadata.get("kind", preview.get("kind", ""))),
                str(metadata.get("line_count", preview.get("line_count", ""))),
                str(signature),
                str(safety),
            )
        )
    return ReportTable(
        "scripts-mscript-preview",
        "Scripts and M-Script Preview",
        ("ID", "Name", "Language", "Kind", "Lines", "Signature", "Safety"),
        tuple(rows),
    )


def _run_result_table(run_results: Iterable[object] | None) -> ReportTable:
    rows: list[tuple[str, str, str, str, str, str]] = []
    for index, result in enumerate(run_results or (), start=1):
        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        log = getattr(result, "log", None)
        stdout = getattr(result, "stdout", "") or getattr(log, "stdout", "")
        stderr = getattr(result, "stderr", "") or getattr(log, "stderr", "")
        rows.append(
            (
                str(getattr(result, "run_id", f"run-{index}")),
                str(status),
                str(getattr(result, "return_code", "")),
                str(getattr(result, "elapsed_seconds", "")),
                _tail(stdout),
                _tail(stderr),
            )
        )
    return ReportTable(
        "run-logs-diagnostics",
        "Run Logs and Diagnostics",
        ("Run ID", "Status", "Return code", "Elapsed seconds", "stdout tail", "stderr tail"),
        tuple(rows),
    )


def _mat_workspace_table(
    project: Project,
    mat_summaries: Iterable[object] | None,
    figure_datasets: Iterable[object] | None,
) -> ReportTable:
    rows: list[tuple[str, str, str, str, str, str]] = []
    for script in project.scripts:
        metadata = script.metadata if isinstance(script.metadata, dict) else {}
        summary = metadata.get("mat_summary")
        if isinstance(summary, Mapping):
            rows.extend(_mat_summary_rows(summary, source=script.path))
    for summary in mat_summaries or ():
        payload = summary.to_dict() if hasattr(summary, "to_dict") else _object_to_mapping(summary)
        rows.extend(_mat_summary_rows(payload, source=str(payload.get("source_path", ""))))
    for dataset in figure_datasets or ():
        for variable in getattr(dataset, "workspace_variables", ()) or ():
            rows.append(
                (
                    str(getattr(variable, "name", "")),
                    "workspace",
                    str(getattr(variable, "type_name", "")),
                    _shape_text(getattr(variable, "shape", ())),
                    str(getattr(variable, "dtype", "")),
                    str(getattr(variable, "source", "")),
                )
            )
    return ReportTable(
        "mat-workspace-variables",
        "MAT / Workspace Variables",
        ("Name", "Source kind", "Type", "Shape", "Dtype", "Source"),
        tuple(rows),
    )


def _figure_table(figures: Iterable[ReportFigure]) -> ReportTable:
    rows = tuple(
        (
            figure.figure_id,
            figure.title,
            figure.format,
            figure.primary_path,
            figure.source_script,
            figure.source_run_id,
        )
        for figure in figures
    )
    return ReportTable(
        "figures",
        "FigureDataset / Figures",
        ("ID", "Title", "Format", "Path", "Script", "Run ID"),
        rows,
    )


def _boundary_curve_table(project: Project) -> ReportTable:
    rows = tuple(
        (
            curve.curve_id,
            curve.name,
            curve.kind,
            str(curve.point_count),
            curve.x_unit,
            curve.y_unit,
            curve.interpolation,
            _curve_source_text(curve),
        )
        for curve in project.boundary_curves
    )
    return ReportTable(
        "boundary-curves",
        "Boundary Curves",
        ("ID", "Name", "Kind", "Points", "X unit", "Y unit", "Interpolation", "Source"),
        rows,
    )


def _result_refs_table(project: Project) -> ReportTable:
    rows = tuple(
        (
            result.ref_id,
            result.name,
            result.kind,
            result.format,
            result.run_id,
            result.path,
        )
        for result in project.results
    )
    return ReportTable(
        "results-summary",
        "Results Summary",
        ("ID", "Name", "Kind", "Format", "Run ID", "Path"),
        rows,
    )


def _validation_table(report: ValidationReport) -> ReportTable:
    return ReportTable(
        "validation-summary",
        "Validation Summary",
        ("Severity", "Path", "Message"),
        tuple((message.severity, message.path, message.message) for message in report.messages),
    )


def _coerce_result_tables(result_tables: Iterable[object] | None) -> tuple[ReportTable, ...]:
    tables: list[ReportTable] = []
    for index, table in enumerate(result_tables or (), start=1):
        if isinstance(table, ReportTable):
            tables.append(table)
            continue
        payload = table if isinstance(table, Mapping) else _object_to_mapping(table)
        tables.append(
            ReportTable(
                table_id=str(payload.get("table_id", f"result-table-{index}")),
                title=str(payload.get("title", f"Result table {index}")),
                columns=tuple(str(item) for item in payload.get("columns", ()) or ()),
                rows=tuple(
                    tuple(str(cell) for cell in row)
                    for row in payload.get("rows", ()) or ()
                ),
                truncated=bool(payload.get("truncated", False)),
                metadata={"source": str(payload.get("source", ""))},
            )
        )
    return tuple(tables)


def _report_figures(figure_datasets: Iterable[object] | None) -> tuple[ReportFigure, ...]:
    figures: list[ReportFigure] = []
    for dataset in figure_datasets or ():
        for record in getattr(dataset, "figures", ()) or ():
            figures.append(
                ReportFigure(
                    figure_id=str(getattr(record, "figure_id", "")),
                    title=str(getattr(record, "title", "")),
                    image_path=getattr(record, "image_path", None),
                    vector_path=getattr(record, "vector_path", None),
                    pdf_path=getattr(record, "pdf_path", None),
                    caption=str(getattr(record, "title", "")),
                    source_run_id=str(
                        getattr(record, "source_run_id", "")
                        or getattr(dataset, "source_run_id", "")
                    ),
                    source_script=str(
                        getattr(record, "source_script", "")
                        or getattr(dataset, "source_file", "")
                        or getattr(dataset, "source", "")
                    ),
                    metadata={
                        "dataset_id": str(getattr(dataset, "dataset_id", "")),
                        "format": str(getattr(record, "image_format", "")),
                    },
                )
            )
    return tuple(figures)


def _figure_assets(figures: Iterable[ReportFigure]) -> tuple[ReportAsset, ...]:
    assets: list[ReportAsset] = []
    for figure in figures:
        path = figure.primary_path
        if not path:
            continue
        assets.append(
            ReportAsset(
                asset_id=figure.figure_id,
                path=path,
                role="figure",
                format=figure.format,
                caption=figure.caption or figure.title,
            )
        )
    return tuple(assets)


def _add_missing_asset_warnings(
    figures: Iterable[ReportFigure],
    diagnostics: DiagnosticReport,
    warnings: list[str],
) -> None:
    for figure in figures:
        path = figure.primary_path
        if not path:
            message = f"Figure has no reportable artifact path: {figure.figure_id}"
        elif not Path(path).exists():
            message = f"Figure artifact missing: {path}"
        else:
            continue
        diagnostics.add_warning(
            "report-asset-missing",
            message,
            hint="Verify the figure artifact path or regenerate the run artifacts.",
            path=path,
        )
        warnings.append(message)


def _mat_summary_rows(
    payload: Mapping[str, Any],
    *,
    source: str,
) -> list[tuple[str, str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str, str]] = []
    for variable in payload.get("variables", ()) or ():
        if not isinstance(variable, Mapping):
            continue
        rows.append(
            (
                str(variable.get("name", "")),
                "mat",
                str(variable.get("kind", variable.get("type_name", ""))),
                _shape_text(variable.get("shape", ())),
                str(variable.get("dtype", "")),
                source or str(payload.get("source_path", "")),
            )
        )
    return rows


def _combined_validation(
    first: ValidationReport,
    second: ValidationReport | None,
) -> ValidationReport:
    combined = ValidationReport()
    combined.extend(first)
    if second is not None:
        combined.extend(second)
    return combined


def _validation_warning_text(report: ValidationReport) -> tuple[str, ...]:
    return tuple(
        f"{message.severity.upper()} {message.path}: {message.message}"
        for message in report.messages
        if message.severity == "warning"
    )


def _project_warning_text(project: Project) -> tuple[str, ...]:
    return tuple(
        f"WARNING {warning.path}: {warning.message}" for warning in project.warnings
    )


def _object_to_mapping(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        data = value.to_dict()
        return dict(data) if isinstance(data, Mapping) else {}
    return {
        key: getattr(value, key)
        for key in dir(value)
        if not key.startswith("_") and not callable(getattr(value, key, None))
    }


def _mesh_info_payload(mesh: object) -> dict[str, Any]:
    info = getattr(mesh, "mesh_info", None)
    if isinstance(info, Mapping):
        return dict(info)
    metadata = getattr(mesh, "metadata", {})
    if isinstance(metadata, Mapping) and isinstance(metadata.get("mesh_info"), Mapping):
        return dict(metadata["mesh_info"])
    return {}


def _mesh_count(explicit: object, payload: Mapping[str, Any], *keys: str) -> object:
    if explicit not in (None, ""):
        return explicit
    for key in keys:
        if payload.get(key) not in (None, ""):
            return payload[key]
    return ""


def _cell_types_text(payload: Mapping[str, Any]) -> str:
    value = payload.get("cell_types", ())
    if not value and isinstance(payload.get("cell_blocks"), list):
        value = [
            block.get("cell_type", "")
            for block in payload["cell_blocks"]
            if isinstance(block, Mapping)
        ]
    if isinstance(value, str):
        return value
    return ", ".join(str(item) for item in value if str(item)) or "none"


def _bounds_text(payload: Mapping[str, Any]) -> str:
    bounds = payload.get("bounds") or payload.get("bounding_box")
    if isinstance(bounds, Mapping):
        minimum = bounds.get("minimum") or bounds.get("min") or ()
        maximum = bounds.get("maximum") or bounds.get("max") or ()
        return f"{tuple(minimum)} -> {tuple(maximum)}"
    minimum = payload.get("minimum")
    maximum = payload.get("maximum")
    if minimum is not None or maximum is not None:
        return f"{tuple(minimum or ())} -> {tuple(maximum or ())}"
    return ""


def _quantity_text(value: object) -> str:
    if value is None:
        return ""
    amount = getattr(value, "value", None)
    unit = getattr(value, "unit", "")
    if amount is not None:
        return f"{amount:g} {unit}".strip()
    return str(value)


def _format_mapping(values: Mapping[str, Any]) -> str:
    if not values:
        return ""
    return ", ".join(f"{key}={value}" for key, value in sorted(values.items()))


def _preview_metadata(preview: object) -> Mapping[str, Any]:
    if isinstance(preview, Mapping) and isinstance(preview.get("metadata"), Mapping):
        return preview["metadata"]
    return {}


def _signature_text(value: object) -> str:
    if isinstance(value, Mapping):
        return str(value.get("raw_signature", value.get("name", "")))
    return ""


def _shape_text(value: object) -> str:
    if not value:
        return "scalar"
    if isinstance(value, str):
        return value
    return "x".join(str(item) for item in value)


def _curve_source_text(curve: object) -> str:
    source = getattr(curve, "source", None)
    if source is None:
        return ""
    return str(
        getattr(source, "source_file", "")
        or getattr(source, "source_dataset_id", "")
        or getattr(source, "source_run_id", "")
        or ", ".join(getattr(source, "variable_names", ()))
    )


def _tail(text: object, limit: int = 500) -> str:
    value = str(text or "")
    if len(value) <= limit:
        return value
    return value[-limit:]
