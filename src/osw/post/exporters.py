"""Report exporter convenience functions."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from osw.core.project_schema import Project
from osw.core.validation import ValidationReport
from osw.post.report_generator import (
    build_report,
    export_report_html,
    render_report_markdown,
)
from osw.post.report_model import ReportBuildRequest, ReportFormat, ReportSummary


def export_html_report(
    project: Project,
    output: str | Path | None = None,
    *,
    figure_datasets: Iterable[object] | None = None,
    mesh_infos: Iterable[object] | None = None,
    result_tables: Iterable[object] | None = None,
    screenshots: Iterable[object] | None = None,
    validation_report: ValidationReport | None = None,
    warnings: Iterable[str] | None = None,
) -> Path:
    """Export the canonical OSW HTML report."""

    return export_report_html(
        project,
        output,
        figure_datasets=figure_datasets,
        mesh_infos=mesh_infos,
        result_tables=result_tables,
        screenshots=screenshots,
        validation_report=validation_report,
        warnings=warnings,
    )


def export_markdown_report(summary: ReportSummary, output: str | Path) -> Path:
    """Write a ReportSummary as lightweight Markdown."""

    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_report_markdown(summary), encoding="utf-8")
    return target


def export_report_summary_json(summary: ReportSummary, output: str | Path) -> Path:
    """Write a ReportSummary JSON file without optional dependencies."""

    import json

    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"{json.dumps(summary.to_dict(), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return target


def export_report(
    project: Project,
    output: str | Path,
    *,
    report_format: str = ReportFormat.HTML.value,
) -> Path:
    """Export a ProjectSchema report in the requested lightweight format."""

    result = build_report(
        ReportBuildRequest(project=project, output_path=output, format=report_format)
    )
    return Path(result.output_path)
