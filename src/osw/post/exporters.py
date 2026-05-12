"""Report exporter convenience functions."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from osw.core.project_schema import Project
from osw.core.validation import ValidationReport
from osw.post.report_generator import export_report_html


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
