"""Minimal HTML report generator for OSW project summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from osw.core.project_schema import Project

DEFAULT_REPORT_FILENAME = "report.html"
DEFAULT_REPORT_LIMITATIONS = (
    "OSW v0.1 reports are an educational/research artifact and must not be "
    "read as Industrial certification or production CAE claims.",
    "Inputs, assumptions, units, validation status, and external tool availability "
    "must be reviewed before using report content.",
    "Result and figure sections are placeholders until structured datasets are added.",
)


@dataclass(frozen=True)
class ReportModel:
    title: str
    project_name: str
    metadata_rows: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    input_summary: tuple[str, ...] = field(default_factory=tuple)
    result_summary: tuple[str, ...] = field(default_factory=tuple)
    figure_list: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = DEFAULT_REPORT_LIMITATIONS


def build_report_model(project: Project) -> ReportModel:
    metadata = project.metadata
    metadata_rows = (
        ("Project", metadata.name or "Untitled project"),
        ("Description", metadata.description or "No description provided."),
        ("Author", metadata.author or "Not specified"),
        ("Tags", ", ".join(metadata.tags) if metadata.tags else "None"),
        ("Schema version", project.schema_version),
        ("Unit system", project.units.name),
    )

    return ReportModel(
        title=project.report.title or metadata.name or "OSW Report",
        project_name=metadata.name or "Untitled project",
        metadata_rows=metadata_rows,
        input_summary=_input_summary(project),
        result_summary=_result_summary(project),
        figure_list=("No figure datasets registered yet.",),
        limitations=DEFAULT_REPORT_LIMITATIONS,
    )


def render_report_html(model: ReportModel) -> str:
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            f"  <title>{escape(model.title)}</title>",
            "  <style>",
            "    body { font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }",
            "    table { border-collapse: collapse; margin: 1rem 0; }",
            "    th, td { border: 1px solid #bbb; padding: 0.4rem 0.6rem; }",
            "    th { text-align: left; background: #f2f2f2; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>{escape(model.title)}</h1>",
            "  <section>",
            "    <h2>Project Summary</h2>",
            _metadata_table(model.metadata_rows),
            "  </section>",
            _list_section("Input Summary", model.input_summary),
            _list_section("Result Summary", model.result_summary),
            _list_section("Figure List", model.figure_list),
            _list_section("Known Limitations", model.limitations),
            "</body>",
            "</html>",
            "",
        ]
    )


def export_report_html(project: Project, output: str | Path | None = None) -> Path:
    target = _resolve_output_path(project, output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_report_html(build_report_model(project)), encoding="utf-8")
    return target


def _resolve_output_path(project: Project, output: str | Path | None) -> Path:
    if output is None:
        return Path(project.report.path)
    target = Path(output)
    if target.suffix.lower() != ".html":
        return target / DEFAULT_REPORT_FILENAME
    return target


def _metadata_table(rows: tuple[tuple[str, str], ...]) -> str:
    row_html = "\n".join(
        f"      <tr><th>{escape(label)}</th><td>{escape(value)}</td></tr>"
        for label, value in rows
    )
    return "\n".join(["    <table>", "      <tbody>", row_html, "      </tbody>", "    </table>"])


def _list_section(title: str, items: tuple[str, ...]) -> str:
    item_html = "\n".join(f"      <li>{escape(item)}</li>" for item in items)
    return "\n".join(
        [
            "  <section>",
            f"    <h2>{escape(title)}</h2>",
            "    <ul>",
            item_html,
            "    </ul>",
            "  </section>",
        ]
    )


def _input_summary(project: Project) -> tuple[str, ...]:
    return (
        f"Geometry references: {len(project.geometry)}",
        f"Mesh references: {len(project.meshes)}",
        f"Script references: {len(project.scripts)}",
        f"Material definitions: {len(project.materials)}",
        f"Physics setups: {len(project.physics)}",
        f"Solver configurations: {len(project.solvers)}",
    )


def _result_summary(project: Project) -> tuple[str, ...]:
    if not project.results:
        return ("No result datasets registered yet.",)
    return tuple(
        f"{result.ref_id}: {result.kind} at {result.path}"
        for result in project.results
    )
