from __future__ import annotations

import json
from pathlib import Path

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.post.exporters import (
    export_markdown_report,
    export_report,
    export_report_summary_json,
)
from osw.post.report_sections import build_report_summary


def test_export_report_writes_utf8_html_and_creates_parent(tmp_path: Path) -> None:
    project = create_heatsink_flow_demo_project()
    output = tmp_path / "nested" / "demo.html"

    path = export_report(project, output)

    assert path == output
    text = path.read_text(encoding="utf-8")
    assert "<!doctype html>" in text
    assert "HeatSink_Flow Simulation Report" in text
    assert "Warnings and Known Limitations" in text


def test_export_report_summary_json_round_trips(tmp_path: Path) -> None:
    summary = build_report_summary(create_heatsink_flow_demo_project())
    output = export_report_summary_json(summary, tmp_path / "summary.json")

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["project_name"] == "HeatSink_Flow"
    assert "sections" in payload


def test_export_markdown_report(tmp_path: Path) -> None:
    summary = build_report_summary(create_heatsink_flow_demo_project())
    output = export_markdown_report(summary, tmp_path / "report.md")

    text = output.read_text(encoding="utf-8")
    assert text.startswith("# HeatSink_Flow Simulation Report")
    assert "## Project Metadata" in text


def test_export_report_json_summary_format(tmp_path: Path) -> None:
    path = export_report(
        create_heatsink_flow_demo_project(),
        tmp_path / "report-summary.json",
        report_format="json_summary",
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["title"] == "HeatSink_Flow Simulation Report"
