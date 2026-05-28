from __future__ import annotations

from pathlib import Path

from osw.core.artifacts import RunArtifact
from osw.post.pyvista_scene import build_result_contour_placeholder
from osw.post.report_generator import build_report_model
from osw.solvers.calculix.result_parser import (
    calculix_results_to_result_dataset,
    parse_calculix_case_directory,
    parse_calculix_results,
    parse_calculix_run_artifacts,
)
from osw.solvers.calculix.results import CalculiXResultStatus
from osw.solvers.calculix.runner import CalculiXRunResult, CalculiXRunStatus

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "calculix" / "results"


def test_parse_case_directory_with_dat_sta_frd(tmp_path: Path) -> None:
    for name in ("simple_success.dat", "simple_success.sta", "simple_success.frd"):
        (tmp_path / name).write_bytes((FIXTURE_DIR / name).read_bytes())

    parsed = parse_calculix_case_directory(tmp_path)

    assert parsed.status is CalculiXResultStatus.PARTIAL
    assert parsed.displacement_summary is not None
    assert parsed.displacement_summary.max_magnitude == 1.904761905e-01
    assert parsed.stress_summary is not None
    assert parsed.status_summary is not None
    assert parsed.status_summary.completed is True
    assert any(
        message.code == "calculix-frd-parser-deferred"
        for message in parsed.diagnostics.messages
    )


def test_parse_calculix_run_result_artifacts() -> None:
    result = CalculiXRunResult(
        run_id="run-1",
        status=CalculiXRunStatus.COMPLETED,
        input_deck_path=FIXTURE_DIR / "simple_success.inp",
        case_dir=FIXTURE_DIR,
        job_name="simple_success",
        artifacts=(
            RunArtifact(FIXTURE_DIR / "simple_success.dat", "dat_result"),
            RunArtifact(FIXTURE_DIR / "simple_success.sta", "status"),
            RunArtifact(FIXTURE_DIR / "simple_success.frd", "frd_result"),
        ),
        combined_log="CalculiX completed.",
    )

    parsed = parse_calculix_run_artifacts(result)

    assert parsed.source_run_id == "run-1"
    assert parsed.job_name == "simple_success"
    assert parsed.displacement_summary is not None
    assert parsed.stress_summary is not None
    assert parsed.metadata["run_status"] == "completed"


def test_frd_placeholder_produces_deferred_diagnostic() -> None:
    parsed = parse_calculix_results(frd_path=FIXTURE_DIR / "simple_success.frd")

    assert parsed.status is CalculiXResultStatus.PARTIAL
    assert parsed.frd_path == FIXTURE_DIR / "simple_success.frd"
    assert "FRD field parsing is deferred" in parsed.diagnostics.summary()


def test_result_dataset_bridge_includes_max_displacement_and_stress() -> None:
    parsed = parse_calculix_results(dat_path=FIXTURE_DIR / "simple_success.dat")
    dataset = calculix_results_to_result_dataset(parsed)
    payload = dataset.to_dict()
    tables = dataset.to_report_tables()

    assert payload["summaries"]["max_displacement"]["value"] == 1.904761905e-01
    assert payload["summaries"]["max_von_mises_stress"]["unit"] == "Pa"
    assert tables[0].title == "CalculiX result summary"

    model = build_report_model(
        project=_minimal_project(),
        result_tables=(dataset,),
    )

    assert any(table.title == "CalculiX result summary" for table in model.result_tables)
    assert model.result_tables[0].rows[0][0] == "max_displacement"


def test_missing_dat_but_existing_frd_returns_partial_summary() -> None:
    parsed = parse_calculix_results(frd_path=FIXTURE_DIR / "simple_success.frd")
    dataset = calculix_results_to_result_dataset(parsed)

    assert parsed.status is CalculiXResultStatus.PARTIAL
    assert dataset.summaries == ()
    assert dataset.metadata["status"] == "partial"


def test_missing_all_artifacts_returns_friendly_error() -> None:
    parsed = parse_calculix_results()

    assert parsed.status is CalculiXResultStatus.MISSING_ARTIFACTS
    assert parsed.diagnostics.has_errors
    assert "No CalculiX DAT" in parsed.diagnostics.summary()


def test_pyvista_contour_placeholder_accepts_result_dataset() -> None:
    parsed = parse_calculix_results(dat_path=FIXTURE_DIR / "simple_success.dat")
    dataset = calculix_results_to_result_dataset(parsed)

    placeholder = build_result_contour_placeholder(
        dataset,
        scalar_field="max_displacement",
    )

    assert placeholder.scalar_field == "max_displacement"
    assert placeholder.available is False
    assert "PyVista contour rendering" in placeholder.warning


def _minimal_project():
    from osw.core.project_schema import Project, ProjectMetadata, ResultRef

    return Project(
        metadata=ProjectMetadata(name="Cantilever result"),
        results=[
            ResultRef(
                ref_id="calculix-result-1",
                path="results/cantilever.dat",
                kind="calculix_result",
            )
        ],
    )
