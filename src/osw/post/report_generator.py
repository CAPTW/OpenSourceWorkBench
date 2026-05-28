"""HTML report generator for OSW project summaries and structured previews."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any

from osw.core.diagnostics import DiagnosticReport
from osw.core.project_schema import Project
from osw.core.validation import ValidationReport, validate_project_sanity
from osw.post.report_model import (
    ReportBuildRequest,
    ReportBuildResult,
    ReportFormat,
    ReportSection,
    ReportSummary,
)
from osw.post.report_sections import REPORT_KNOWN_LIMITATIONS, build_report_summary

DEFAULT_REPORT_FILENAME = "report.html"
DEFAULT_REPORT_LIMITATIONS = REPORT_KNOWN_LIMITATIONS


@dataclass(frozen=True)
class ReportFigure:
    figure_id: str
    title: str
    image_path: str
    status: str
    format: str = ""
    axes: tuple[str, ...] = field(default_factory=tuple)
    source: str = ""


@dataclass(frozen=True)
class ReportScreenshot:
    title: str
    image_path: str
    status: str
    description: str = ""


@dataclass(frozen=True)
class ReportTable:
    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    source: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReportModel:
    title: str
    project_name: str
    metadata_rows: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    input_summary: tuple[str, ...] = field(default_factory=tuple)
    input_conditions: tuple[str, ...] = field(default_factory=tuple)
    unit_system_rows: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    material_summary: tuple[str, ...] = field(default_factory=tuple)
    mesh_summary: tuple[str, ...] = field(default_factory=tuple)
    solver_summary: tuple[str, ...] = field(default_factory=tuple)
    warning_summary: tuple[str, ...] = field(default_factory=tuple)
    figures: tuple[ReportFigure, ...] = field(default_factory=tuple)
    screenshots: tuple[ReportScreenshot, ...] = field(default_factory=tuple)
    result_tables: tuple[ReportTable, ...] = field(default_factory=tuple)
    result_summary: tuple[str, ...] = field(default_factory=tuple)
    validation_summary: tuple[str, ...] = field(default_factory=tuple)
    figure_list: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = DEFAULT_REPORT_LIMITATIONS


def build_report_model(
    project: Project,
    *,
    figure_datasets: Iterable[object] | None = None,
    mesh_infos: Iterable[object] | None = None,
    result_tables: Iterable[object] | None = None,
    screenshots: Iterable[object] | None = None,
    validation_report: ValidationReport | None = None,
    sanity_report: ValidationReport | None = None,
    warnings: Iterable[str] | None = None,
) -> ReportModel:
    """Build a report model from core project data and optional preview datasets."""

    metadata = project.metadata
    metadata_rows = (
        ("Project", metadata.name or "Untitled project"),
        ("Description", metadata.description or "No description provided."),
        ("Author", metadata.author or "Not specified"),
        ("Tags", ", ".join(metadata.tags) if metadata.tags else "None"),
        ("Schema version", project.schema_version),
        ("Unit system", project.units.name),
    )

    effective_sanity_report = (
        validate_project_sanity(project) if sanity_report is None else sanity_report
    )
    validation = _combined_validation_report(
        validation_report if validation_report is not None else project.validate(),
        effective_sanity_report,
    )
    validation_lines = (
        _validation_summary(validation)
        if project.report.include_validation
        else ("Validation summary disabled by report config.",)
    )

    figures, figure_warnings, figure_list = _report_figures(figure_datasets)
    report_tables = (*_report_tables(result_tables), *_figure_workspace_tables(figure_datasets))
    report_screenshots, screenshot_warnings = _report_screenshots(screenshots)
    warning_lines = [
        *tuple(str(warning) for warning in warnings or ()),
        *(_validation_warnings(validation) if project.report.include_validation else ()),
        *figure_warnings,
        *screenshot_warnings,
    ]

    return ReportModel(
        title=project.report.title or metadata.name or "OSW Report",
        project_name=metadata.name or "Untitled project",
        metadata_rows=metadata_rows,
        input_summary=_input_summary(project),
        input_conditions=_input_conditions(project),
        unit_system_rows=_unit_system_rows(project),
        material_summary=_material_summary(project),
        mesh_summary=_mesh_summary(project, mesh_infos),
        solver_summary=_solver_summary(project),
        warning_summary=tuple(warning_lines) or ("No report warnings.",),
        figures=figures,
        screenshots=report_screenshots,
        result_tables=report_tables,
        result_summary=_result_summary(project),
        validation_summary=validation_lines,
        figure_list=figure_list,
        limitations=DEFAULT_REPORT_LIMITATIONS,
    )


def render_report_html(model: ReportModel | ReportSummary) -> str:
    if isinstance(model, ReportSummary):
        return render_report_summary_html(model)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            f"  <title>{escape(model.title)}</title>",
            "  <style>",
            "    body { font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }",
            "    section { margin-block: 1.4rem; }",
            "    table { border-collapse: collapse; margin: 1rem 0; width: 100%; }",
            "    th, td { border: 1px solid #bbb; padding: 0.4rem 0.6rem; }",
            "    th { text-align: left; background: #f2f2f2; }",
            "    figure { margin: 1rem 0; }",
            "    img { max-width: 100%; height: auto; border: 1px solid #ddd; }",
            "    .warning { color: #7a3b00; font-weight: 600; }",
            "    .muted { color: #555; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{escape(model.title)}</h1>",
            "  <section id=\"project-summary\">",
            "    <h2>Project Summary</h2>",
            _key_value_table(model.metadata_rows),
            "  </section>",
            _list_section("Input Summary", model.input_summary, section_id="input-summary"),
            _list_section(
                "Input Conditions",
                model.input_conditions,
                section_id="input-conditions",
            ),
            "  <section id=\"unit-system\">",
            "    <h2>Unit System</h2>",
            _key_value_table(model.unit_system_rows),
            "  </section>",
            _list_section("Materials", model.material_summary, section_id="materials"),
            _list_section("Mesh Info", model.mesh_summary, section_id="mesh-info"),
            _list_section(
                "Solver Settings",
                model.solver_summary,
                section_id="solver-settings",
            ),
            _list_section("Warnings", model.warning_summary, section_id="warnings"),
            _figure_section(model.figures, model.figure_list),
            _screenshot_section(model.screenshots),
            _table_section(model.result_tables),
            _list_section("Result Summary", model.result_summary, section_id="result-summary"),
            _list_section(
                "Validation Summary",
                model.validation_summary,
                section_id="validation-summary",
            ),
            _list_section("Known Limitations", model.limitations, section_id="limitations"),
            "</body>",
            "</html>",
            "",
        ]
    )


def export_report_html(
    project: Project,
    output: str | Path | None = None,
    *,
    figure_datasets: Iterable[object] | None = None,
    mesh_infos: Iterable[object] | None = None,
    result_tables: Iterable[object] | None = None,
    screenshots: Iterable[object] | None = None,
    validation_report: ValidationReport | None = None,
    sanity_report: ValidationReport | None = None,
    warnings: Iterable[str] | None = None,
) -> Path:
    target = _resolve_output_path(project, output)
    result = build_report(
        ReportBuildRequest(project=project, output_path=target, format=ReportFormat.HTML),
        figure_datasets=figure_datasets,
        mesh_infos=mesh_infos,
        result_tables=result_tables,
        validation_report=validation_report,
        sanity_report=sanity_report,
        warnings=warnings,
        metadata={"screenshots": tuple(str(item) for item in screenshots or ())},
    )
    return Path(result.output_path)


def build_report(
    request: ReportBuildRequest,
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
    metadata: Mapping[str, Any] | None = None,
) -> ReportBuildResult:
    """Build and write a deterministic report without executing tools."""

    summary = build_report_summary(
        request.project,
        figure_datasets=figure_datasets if request.include_figures else (),
        mesh_infos=mesh_infos,
        mat_summaries=mat_summaries,
        plugin_health=plugin_health,
        run_results=run_results,
        result_tables=result_tables if request.include_tables else (),
        validation_report=validation_report,
        sanity_report=sanity_report,
        warnings=warnings if request.include_warnings else (),
        created_at=str(request.metadata.get("created_at", "")),
    )
    if not request.include_known_limitations:
        summary = _summary_without_known_limitations(summary)
    output_path = _resolve_build_output_path(request)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    diagnostics = DiagnosticReport()
    report_format = str(request.format)
    if report_format == ReportFormat.JSON_SUMMARY.value:
        output_path.write_text(
            f"{json.dumps(summary.to_dict(), indent=2, sort_keys=True)}\n",
            encoding="utf-8",
        )
    elif report_format == ReportFormat.MARKDOWN.value:
        output_path.write_text(render_report_markdown(summary), encoding="utf-8")
    elif report_format in {ReportFormat.HTML.value, ReportFormat.PDF_OPTIONAL.value}:
        if report_format == ReportFormat.PDF_OPTIONAL.value:
            diagnostics.add_warning(
                "report-pdf-deferred",
                "PDF report export is optional and not enabled by default.",
                hint="Export HTML or Markdown without adding a mandatory PDF dependency.",
            )
        output_path.write_text(
            render_report_summary_html(summary, output_path=output_path),
            encoding="utf-8",
        )
    else:
        diagnostics.add_error(
            "report-format-unsupported",
            f"Unsupported report format: {request.format}",
            hint="Use html, markdown, or json_summary.",
        )
    diagnostics.extend(summary.diagnostics)
    status = (
        "error"
        if diagnostics.has_errors
        else ("warning" if diagnostics.has_warnings else "ok")
    )
    return ReportBuildResult(
        status=status,
        output_path=output_path,
        summary=summary,
        diagnostics=diagnostics,
        assets=summary.assets,
    )


def render_report_summary_html(
    summary: ReportSummary,
    *,
    output_path: str | Path | None = None,
) -> str:
    """Render a ReportSummary to deterministic standalone HTML."""

    section_html = "\n".join(
        _render_summary_section(section, summary) for section in summary.sections
    )
    table_html = "\n".join(_render_summary_table(table) for table in summary.tables)
    figure_html = _render_summary_figures(summary, output_path=output_path)
    warnings = summary.warnings or ("No report warnings.",)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            f"  <title>{escape(summary.title)}</title>",
            "  <style>",
            "    body { font-family: system-ui, sans-serif; margin: 2rem; "
            "line-height: 1.5; color: #1f2933; }",
            "    main { max-width: 1180px; }",
            "    section { margin-block: 1.4rem; }",
            "    table { border-collapse: collapse; margin: 0.75rem 0 1.25rem; width: 100%; }",
            "    th, td { border: 1px solid #b9c2cf; padding: 0.4rem 0.55rem; "
            "vertical-align: top; }",
            "    th { text-align: left; background: #eef2f6; }",
            "    figure { margin: 1rem 0; }",
            "    img { max-width: 100%; height: auto; border: 1px solid #c8d0da; }",
            "    code { background: #f2f4f7; padding: 0.05rem 0.2rem; }",
            "    .warning { color: #7a3b00; font-weight: 650; }",
            "    .muted { color: #56616f; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <main>",
            f"    <h1>{escape(summary.title)}</h1>",
            f"    <p class=\"muted\">Project: {escape(summary.project_name)}"
            f" | Run: {escape(summary.run_label or 'Not recorded')}</p>",
            section_html,
            table_html,
            figure_html,
            "    <section id=\"report-warnings\">",
            "      <h2>Report Warnings</h2>",
            "      <ul>",
            *[f"        <li>{escape(item)}</li>" for item in warnings],
            "      </ul>",
            "    </section>",
            "  </main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def render_report_markdown(summary: ReportSummary) -> str:
    """Render a lightweight Markdown report summary."""

    lines = [
        f"# {summary.title}",
        "",
        f"Project: {summary.project_name}",
        f"Run: {summary.run_label or 'Not recorded'}",
        "",
    ]
    for section in summary.sections:
        lines.extend([f"## {section.title}", ""])
        lines.extend(f"- {item}" for item in section.content_blocks)
        lines.append("")
    return "\n".join(lines)


def _resolve_output_path(project: Project, output: str | Path | None) -> Path:
    if output is None:
        return Path(project.report.path)
    target = Path(output)
    if target.suffix.lower() != ".html":
        return target / DEFAULT_REPORT_FILENAME
    return target


def _resolve_build_output_path(request: ReportBuildRequest) -> Path:
    if request.output_path:
        target = Path(request.output_path)
    else:
        target = Path(request.project.report.path)
    if target.suffix:
        return target
    suffix = {
        ReportFormat.HTML.value: ".html",
        ReportFormat.MARKDOWN.value: ".md",
        ReportFormat.JSON_SUMMARY.value: ".json",
        ReportFormat.PDF_OPTIONAL.value: ".html",
    }.get(str(request.format), ".html")
    return target / f"report{suffix}"


def _summary_without_known_limitations(summary: ReportSummary) -> ReportSummary:
    filtered_sections: list[ReportSection] = []
    for section in summary.sections:
        if section.section_id != "warnings-known-limitations":
            filtered_sections.append(section)
            continue
        blocks = tuple(
            block
            for block in section.content_blocks
            if block not in DEFAULT_REPORT_LIMITATIONS
        )
        filtered_sections.append(
            ReportSection(
                section.section_id,
                section.title,
                section.level,
                blocks or ("No report warnings.",),
                section.diagnostics,
                section.metadata,
            )
        )
    metadata = dict(summary.metadata)
    metadata["known_limitations"] = []
    return ReportSummary(
        title=summary.title,
        project_name=summary.project_name,
        run_label=summary.run_label,
        created_at=summary.created_at,
        sections=tuple(filtered_sections),
        tables=summary.tables,
        figures=summary.figures,
        assets=summary.assets,
        warnings=summary.warnings,
        diagnostics=summary.diagnostics,
        metadata=metadata,
    )


def _render_summary_section(section: ReportSection, summary: ReportSummary) -> str:
    heading_level = min(max(section.level, 2), 6)
    body = [
        f'    <section id="{escape(section.section_id)}">',
        f"      <h{heading_level}>{escape(section.title)}</h{heading_level}>",
        "      <ul>",
    ]
    for item in section.content_blocks or ("No data registered yet.",):
        body.append(f"        <li>{escape(item)}</li>")
    body.append("      </ul>")
    for table_id in section.metadata.get("table_ids", ()):
        if any(table.table_id == table_id for table in summary.tables):
            body.append(f'      <p class="muted">Table: <code>{escape(str(table_id))}</code></p>')
    body.append("    </section>")
    return "\n".join(body)


def _render_summary_table(table: object) -> str:
    title = str(getattr(table, "title", "Report table"))
    table_id = str(getattr(table, "table_id", title))
    columns = tuple(str(item) for item in getattr(table, "columns", ()) or ())
    rows = tuple(tuple(str(cell) for cell in row) for row in getattr(table, "rows", ()) or ())
    if not columns:
        return ""
    body = [
        f'    <section id="table-{escape(table_id)}">',
        f"      <h3>{escape(title)}</h3>",
        "      <table>",
        "        <thead>",
        "          <tr>" + "".join(f"<th>{escape(column)}</th>" for column in columns) + "</tr>",
        "        </thead>",
        "        <tbody>",
    ]
    if rows:
        for row in rows:
            cells = "".join(f"<td>{escape(cell)}</td>" for cell in row)
            body.append(f"          <tr>{cells}</tr>")
    else:
        body.append(
            f"          <tr><td colspan=\"{len(columns)}\" class=\"muted\">"
            "No data registered yet.</td></tr>"
        )
    body.extend(["        </tbody>", "      </table>", "    </section>"])
    return "\n".join(body)


def _render_summary_figures(
    summary: ReportSummary,
    *,
    output_path: str | Path | None,
) -> str:
    body = ['    <section id="report-figures">', "      <h2>Report Figure Assets</h2>"]
    if not summary.figures:
        body.extend(["      <p>No figure datasets registered yet.</p>", "    </section>"])
        return "\n".join(body)
    for figure in summary.figures:
        body.extend(
            [
                "      <figure>",
                f"        <figcaption>{escape(figure.figure_id)}: "
                f"{escape(figure.title or 'Figure')}</figcaption>",
            ]
        )
        path = figure.primary_path
        if path and Path(path).exists():
            href = _relative_report_href(path, output_path)
            if figure.format in {"png", "jpg", "jpeg", "svg"}:
                body.append(
                    f'        <img src="{escape(href)}" '
                    f'alt="{escape(figure.title or figure.figure_id)}">'
                )
            else:
                body.append(f'        <p><a href="{escape(href)}">Figure artifact</a></p>')
        else:
            body.append(
                f'        <p class="warning">Figure artifact missing: '
                f'{escape(path or "<none>")}</p>'
            )
        if figure.source_script or figure.source_run_id:
            body.append(
                f'        <p class="muted">Source: '
                f'{escape(figure.source_script or "not recorded")} '
                f'{escape(figure.source_run_id or "")}</p>'
            )
        body.append("      </figure>")
    body.append("    </section>")
    return "\n".join(body)


def _relative_report_href(path: str | Path, output_path: str | Path | None) -> str:
    source = Path(path)
    if output_path:
        try:
            return os.path.relpath(source, Path(output_path).parent).replace("\\", "/")
        except ValueError:
            return str(source).replace("\\", "/")
    return str(source).replace("\\", "/")


def _combined_validation_report(
    validation_report: ValidationReport,
    sanity_report: ValidationReport | None,
) -> ValidationReport:
    if sanity_report is None:
        return validation_report
    combined = ValidationReport()
    combined.extend(validation_report)
    combined.extend(sanity_report)
    return combined


def _key_value_table(rows: tuple[tuple[str, str], ...]) -> str:
    row_html = "\n".join(
        f"      <tr><th>{escape(label)}</th><td>{escape(value)}</td></tr>"
        for label, value in rows
    )
    return "\n".join(["    <table>", "      <tbody>", row_html, "      </tbody>", "    </table>"])


def _list_section(title: str, items: tuple[str, ...], *, section_id: str) -> str:
    item_html = "\n".join(f"      <li>{escape(item)}</li>" for item in items)
    return "\n".join(
        [
            f"  <section id=\"{escape(section_id)}\">",
            f"    <h2>{escape(title)}</h2>",
            "    <ul>",
            item_html,
            "    </ul>",
            "  </section>",
        ]
    )


def _figure_section(
    figures: tuple[ReportFigure, ...],
    fallback_items: tuple[str, ...],
) -> str:
    if not figures:
        return _list_section("Figures", fallback_items, section_id="figures")

    body: list[str] = ['  <section id="figures">', "    <h2>Figures</h2>"]
    for figure in figures:
        body.extend(
            [
                "    <figure>",
                "      <figcaption>"
                f"{escape(figure.figure_id)}: {escape(figure.title)}"
                "</figcaption>",
            ]
        )
        if figure.status == "available":
            if figure.format in {"png", "svg", "jpg", "jpeg"}:
                body.append(
                    f'      <img src="{escape(figure.image_path)}" '
                    f'alt="{escape(figure.title)}">'
                )
            else:
                body.append(
                    f'      <p><a href="{escape(figure.image_path)}">'
                    f"{escape(figure.format.upper() or 'artifact')} artifact</a></p>"
                )
        else:
            body.append(
                f"      <p class=\"warning\">Figure image not available: "
                f"{escape(figure.image_path)}</p>"
            )
        if figure.axes:
            body.append(f"      <p class=\"muted\">Axes: {escape(', '.join(figure.axes))}</p>")
        if figure.source:
            body.append(f"      <p class=\"muted\">Source: {escape(figure.source)}</p>")
        body.append("    </figure>")
    body.append("  </section>")
    return "\n".join(body)


def _screenshot_section(screenshots: tuple[ReportScreenshot, ...]) -> str:
    if not screenshots:
        return _list_section(
            "3D Screenshots",
            ("No 3D screenshots registered yet.",),
            section_id="screenshots",
        )

    body: list[str] = ['  <section id="screenshots">', "    <h2>3D Screenshots</h2>"]
    for screenshot in screenshots:
        body.extend(["    <figure>", f"      <figcaption>{escape(screenshot.title)}</figcaption>"])
        if screenshot.status == "available":
            body.append(
                f'      <img src="{escape(screenshot.image_path)}" '
                f'alt="{escape(screenshot.title)}">'
            )
        else:
            body.append(
                f"      <p class=\"warning\">3D screenshot not available: "
                f"{escape(screenshot.image_path)}</p>"
            )
        if screenshot.description:
            body.append(f"      <p class=\"muted\">{escape(screenshot.description)}</p>")
        body.append("    </figure>")
    body.append("  </section>")
    return "\n".join(body)


def _table_section(tables: tuple[ReportTable, ...]) -> str:
    if not tables:
        return _list_section(
            "Result Tables",
            ("No result tables registered yet.",),
            section_id="result-tables",
        )

    body: list[str] = ['  <section id="result-tables">', "    <h2>Result Tables</h2>"]
    for table in tables:
        body.extend(
            [
                f"    <h3>{escape(table.title)}</h3>",
                f"    <p class=\"muted\">Source: {escape(table.source or 'Not specified')}</p>",
                "    <table>",
                "      <thead>",
                "        <tr>"
                + "".join(f"<th>{escape(column)}</th>" for column in table.columns)
                + "</tr>",
                "      </thead>",
                "      <tbody>",
            ]
        )
        for row in table.rows:
            cells = "".join(f"<td>{escape(cell)}</td>" for cell in row)
            body.append(f"        <tr>{cells}</tr>")
        body.extend(["      </tbody>", "    </table>"])
        if table.notes:
            body.append(f"    <p class=\"muted\">Notes: {escape('; '.join(table.notes))}</p>")
    body.append("  </section>")
    return "\n".join(body)


def _input_summary(project: Project) -> tuple[str, ...]:
    return (
        f"Geometry references: {len(project.geometry)}",
        f"Mesh references: {len(project.meshes)}",
        f"Script references: {len(project.scripts)}",
        f"Material definitions: {len(project.materials)}",
        f"Physics setups: {len(project.physics)}",
        f"Solver configurations: {len(project.solvers)}",
        f"Boundary curves: {len(project.boundary_curves)}",
    )


def _input_conditions(project: Project) -> tuple[str, ...]:
    items: list[str] = [f"Boundary curves: {len(project.boundary_curves)}"]
    items.extend(
        f"Geometry {ref.ref_id}: {ref.format} at {ref.path}" for ref in project.geometry
    )
    items.extend(f"Script {ref.ref_id}: {ref.language} at {ref.path}" for ref in project.scripts)
    for setup in project.physics:
        items.append(
            f"Physics {setup.setup_id}: {setup.analysis_type}, "
            f"{len(setup.boundary_conditions)} boundary condition(s), "
            f"{len(setup.material_assignments)} material assignment(s)"
        )
    return tuple(items) or ("No input conditions registered yet.",)


def _unit_system_rows(project: Project) -> tuple[tuple[str, str], ...]:
    units = project.units
    return (
        ("Name", units.name),
        ("Length", units.length),
        ("Mass", units.mass),
        ("Time", units.time),
        ("Temperature", units.temperature),
        ("Amount", units.amount),
        ("Current", units.current),
        ("Force", units.force),
        ("Stress", units.stress),
        ("Energy", units.energy),
        ("Pressure", units.pressure),
        ("Defaulted", "yes" if units.defaulted else "no"),
    )


def _material_summary(project: Project) -> tuple[str, ...]:
    if not project.materials:
        return ("No material definitions registered yet.",)

    items: list[str] = []
    for material in project.materials:
        parts = [f"{material.material_id}: {material.name}"]
        if material.density is not None:
            parts.append(
                f"density={material.density.value:g} {material.density.unit}"
            )
        if material.elastic is not None:
            parts.append(
                "elastic="
                f"E {material.elastic.young_modulus.value:g} "
                f"{material.elastic.young_modulus.unit}, "
                f"nu {material.elastic.poisson_ratio:g}"
            )
        items.append("; ".join(parts))
    return tuple(items)


def _mesh_summary(project: Project, mesh_infos: Iterable[object] | None) -> tuple[str, ...]:
    items = [
        f"{mesh.ref_id}: {mesh.format} at {mesh.path}"
        for mesh in project.meshes
    ]
    items.extend(_mesh_info_summary(info) for info in mesh_infos or ())
    return tuple(items) or ("No mesh references or mesh metadata registered yet.",)


def _solver_summary(project: Project) -> tuple[str, ...]:
    if not project.solvers:
        return ("No solver configurations registered yet.",)
    return tuple(
        f"{solver.solver_id}: {solver.name}, mode={solver.execution_mode}, "
        f"parameters={_format_mapping(solver.parameters)}"
        for solver in project.solvers
    )


def _result_summary(project: Project) -> tuple[str, ...]:
    if not project.results:
        return ("No result datasets registered yet.",)
    return tuple(
        f"{result.ref_id}: {result.kind} at {result.path}"
        for result in project.results
    )


def _validation_summary(report: ValidationReport) -> tuple[str, ...]:
    if not report.messages:
        return ("No validation messages.",)
    return tuple(
        f"{message.severity.upper()} {message.path}: {message.message}"
        for message in report.messages
    )


def _validation_warnings(report: ValidationReport) -> tuple[str, ...]:
    return tuple(
        f"{message.severity.upper()} {message.path}: {message.message}"
        for message in report.messages
        if message.severity == "warning"
    )


def _report_figures(
    figure_datasets: Iterable[object] | None,
) -> tuple[tuple[ReportFigure, ...], tuple[str, ...], tuple[str, ...]]:
    figures: list[ReportFigure] = []
    warnings: list[str] = []
    for dataset in figure_datasets or ():
        source = str(getattr(dataset, "source", ""))
        for record in getattr(dataset, "figures", ()):
            image_path = _figure_report_path(record)
            status = "available" if image_path.exists() else "missing"
            figure = ReportFigure(
                figure_id=str(getattr(record, "figure_id", "figure")),
                title=str(getattr(record, "title", "Figure")),
                image_path=str(image_path),
                status=status,
                format=str(getattr(record, "image_format", "")),
                axes=tuple(_axis_display_text(axis) for axis in getattr(record, "axes", ())),
                source=_figure_source_text(record, source),
            )
            figures.append(figure)
            if status == "missing":
                warnings.append(f"Figure image missing: {image_path}")

    if not figures:
        return (), (), ("No figure datasets registered yet.",)

    figure_list = tuple(
        f"{figure.figure_id}: {figure.title} [{figure.status}] at {figure.image_path}"
        for figure in figures
    )
    return tuple(figures), tuple(warnings), figure_list


def _figure_workspace_tables(
    figure_datasets: Iterable[object] | None,
) -> tuple[ReportTable, ...]:
    tables: list[ReportTable] = []
    for dataset in figure_datasets or ():
        variables = tuple(getattr(dataset, "workspace_variables", ()) or ())
        if not variables:
            continue
        rows = tuple(
            (
                str(getattr(variable, "name", "")),
                str(getattr(variable, "type_name", "")),
                "x".join(str(item) for item in getattr(variable, "shape", ()) or ()),
                str(getattr(variable, "dtype", "")),
                str(getattr(variable, "source", "")),
            )
            for variable in variables
        )
        tables.append(
            ReportTable(
                title=f"Workspace variables: {getattr(dataset, 'dataset_id', 'figures')}",
                columns=("name", "type", "shape", "dtype", "source"),
                rows=rows,
                source=str(getattr(dataset, "source_file", "") or getattr(dataset, "source", "")),
                notes=("Summaries are derived from exported JSON/CSV artifacts.",),
            )
        )
    return tuple(tables)


def _figure_report_path(record: object) -> Path:
    for attribute in ("image_path", "vector_path", "pdf_path", "thumbnail_path", "data_path"):
        value = getattr(record, attribute, None)
        if value not in (None, ""):
            return Path(value)
    return Path("__missing_figure_artifact__")


def _axis_display_text(axis: object) -> str:
    if hasattr(axis, "display_label"):
        return str(axis.display_label())
    return str(axis)


def _figure_source_text(record: object, dataset_source: str) -> str:
    parts = [
        dataset_source,
        str(getattr(record, "source_script", "")),
        str(getattr(record, "source_run_id", "")),
    ]
    return " | ".join(part for part in parts if part)


def _report_screenshots(
    screenshots: Iterable[object] | None,
) -> tuple[tuple[ReportScreenshot, ...], tuple[str, ...]]:
    report_screenshots: list[ReportScreenshot] = []
    warnings: list[str] = []
    for index, screenshot in enumerate(screenshots or (), start=1):
        if isinstance(screenshot, Mapping):
            title = str(screenshot.get("title", f"3D screenshot {index}"))
            image_path = Path(str(screenshot.get("image_path", "")))
            description = str(screenshot.get("description", ""))
        else:
            title = f"3D screenshot {index}"
            image_path = Path(screenshot)
            description = ""

        status = "available" if image_path.exists() else "missing"
        report_screenshots.append(
            ReportScreenshot(
                title=title,
                image_path=str(image_path),
                status=status,
                description=description,
            )
        )
        if status == "missing":
            warnings.append(f"3D screenshot missing: {image_path}")
    return tuple(report_screenshots), tuple(warnings)


def _report_tables(result_tables: Iterable[object] | None) -> tuple[ReportTable, ...]:
    tables: list[ReportTable] = []
    for item in result_tables or ():
        if hasattr(item, "to_report_tables"):
            for table in item.to_report_tables():
                tables.append(_report_table(table, len(tables) + 1))
        else:
            tables.append(_report_table(item, len(tables) + 1))
    return tuple(tables)


def _report_table(table: object, index: int) -> ReportTable:
    if isinstance(table, Mapping):
        columns = table.get("columns", ())
        rows = table.get("rows", ())
        title = str(table.get("title", f"Result table {index}"))
        source = str(table.get("source", ""))
        notes = table.get("notes", ())
    else:
        columns = getattr(table, "columns", ())
        rows = getattr(table, "rows", ())
        title = str(getattr(table, "title", "") or f"Result table {index}")
        source = str(getattr(table, "source", ""))
        notes = getattr(table, "notes", ())

    return ReportTable(
        title=title,
        columns=tuple(str(column) for column in columns),
        rows=tuple(tuple(str(cell) for cell in row) for row in rows),
        source=source,
        notes=tuple(str(note) for note in notes),
    )


def _mesh_info_summary(info: object) -> str:
    if isinstance(info, Mapping):
        source = str(info.get("source", "mesh"))
        mesh_format = str(info.get("format", "unknown"))
        nodes = info.get("nodes", "unknown")
        elements = info.get("elements", "unknown")
        cell_types = info.get("cell_types", ())
        bounding_box = info.get("bounding_box", {})
        minimum = bounding_box.get("minimum", ()) if isinstance(bounding_box, Mapping) else ()
        maximum = bounding_box.get("maximum", ()) if isinstance(bounding_box, Mapping) else ()
    else:
        source = str(getattr(info, "source", "mesh"))
        mesh_format = str(getattr(info, "format", "unknown"))
        nodes = getattr(info, "nodes", "unknown")
        elements = getattr(info, "elements", "unknown")
        cell_types = getattr(info, "cell_types", ())
        bounding_box = getattr(info, "bounding_box", None)
        minimum = getattr(bounding_box, "minimum", ())
        maximum = getattr(bounding_box, "maximum", ())

    cell_type_text = ", ".join(str(cell_type) for cell_type in cell_types) or "none"
    return (
        f"{source} [{mesh_format}]: nodes={nodes}, elements={elements}, "
        f"cell_types={cell_type_text}, bounds={tuple(minimum)} -> {tuple(maximum)}"
    )


def _format_mapping(values: Mapping[str, Any]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(values.items()))
