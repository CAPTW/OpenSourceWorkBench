from __future__ import annotations

import json
from pathlib import Path

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.solvers.calculix.results import (
    CalculiXDisplacementSummary,
    CalculiXFieldSummary,
    CalculiXParsedResults,
    CalculiXResultStatus,
    CalculiXStatusSummary,
    CalculiXStressSummary,
)
from osw.solvers.log_parser import LogEvent, LogSeverity


def test_calculix_field_summary_round_trips() -> None:
    summary = CalculiXFieldSummary(
        name="von_mises_stress",
        component_names=("S",),
        location="element",
        max_value=2.0,
        max_entity_id=7,
        unit="Pa",
    )

    assert CalculiXFieldSummary.from_dict(json.loads(json.dumps(summary.to_dict()))) == summary


def test_calculix_displacement_summary_round_trips() -> None:
    summary = CalculiXDisplacementSummary(
        max_magnitude=0.001,
        max_node_id=42,
        components=(0.0, -0.001, 0.0),
    )

    assert CalculiXDisplacementSummary.from_dict(summary.to_dict()) == summary


def test_calculix_stress_summary_round_trips() -> None:
    summary = CalculiXStressSummary(max_von_mises=2.3e8, max_element_id=7)

    assert CalculiXStressSummary.from_dict(summary.to_dict()) == summary


def test_calculix_status_summary_round_trips() -> None:
    summary = CalculiXStatusSummary(
        completed=True,
        increments=2,
        last_step=1,
        last_increment=2,
        warnings=("warning",),
    )

    assert CalculiXStatusSummary.from_dict(summary.to_dict()) == summary


def test_calculix_parsed_results_round_trips_paths_and_diagnostics(tmp_path: Path) -> None:
    diagnostics = DiagnosticReport()
    diagnostics.add_warning("fixture-warning", "Fixture warning.")
    artifact = RunArtifact(tmp_path / "cantilever.dat", "dat_result", exists=True)
    parsed = CalculiXParsedResults(
        source_run_id="run-1",
        job_name="cantilever",
        dat_path=tmp_path / "cantilever.dat",
        frd_path=tmp_path / "cantilever.frd",
        sta_path=tmp_path / "cantilever.sta",
        status=CalculiXResultStatus.PARTIAL,
        displacement_summary=CalculiXDisplacementSummary(max_magnitude=1.0),
        stress_summary=CalculiXStressSummary(max_von_mises=2.0),
        field_summaries=(CalculiXFieldSummary(name="field"),),
        status_summary=CalculiXStatusSummary(completed=True),
        log_events=(LogEvent(LogSeverity.WARNING, "warn", 3),),
        artifacts=(artifact,),
        diagnostics=diagnostics,
    )

    restored = CalculiXParsedResults.from_dict(json.loads(json.dumps(parsed.to_dict())))

    assert restored.status is CalculiXResultStatus.PARTIAL
    assert restored.dat_path == tmp_path / "cantilever.dat"
    assert restored.artifacts[0].role == "dat_result"
    assert restored.diagnostics.has_warnings
