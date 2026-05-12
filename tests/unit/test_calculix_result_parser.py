from __future__ import annotations

from pathlib import Path

from osw.core.result_dataset import ResultDataset
from osw.post.pyvista_scene import build_result_contour_placeholder
from osw.post.report_generator import build_report_model
from osw.solvers.calculix.result_parser import (
    CalculixFrdParserUnavailable,
    parse_calculix_dat,
    parse_calculix_results,
)

VALID_DAT = """
OSW CALCULIX RESULT SUMMARY

DISPLACEMENTS
NODE U1 U2 U3
1 0.0 0.0 0.0
2 0.0 -0.0025 0.0
3 0.0 -0.0040 0.0

STRESSES
ELEMENT SXX SYY SZZ SXY SYZ SXZ VON_MISES
1 1.0e6 0.0 0.0 0.0 0.0 0.0 1.0e6
2 2.0e6 0.0 0.0 0.0 0.0 0.0 2.0e6
"""


def test_parse_valid_dat_extracts_displacement_and_stress_summary(tmp_path: Path) -> None:
    dat_path = tmp_path / "cantilever.dat"
    dat_path.write_text(VALID_DAT, encoding="utf-8")

    dataset = parse_calculix_dat(dat_path)

    assert isinstance(dataset, ResultDataset)
    assert dataset.dataset_id == "cantilever"
    assert dataset.solver == "CalculiX"
    assert dataset.analysis_type == "linear_static"
    assert dataset.max_summary("displacement_magnitude").value == 0.004
    assert dataset.max_summary("von_mises_stress").value == 2.0e6
    assert dataset.field("displacement").rows[2].entity_id == 3
    assert dataset.field("stress").rows[1].values["VON_MISES"] == 2.0e6
    assert dataset.warnings == ()


def test_partial_or_corrupt_dat_produces_warnings_and_partial_dataset(tmp_path: Path) -> None:
    dat_path = tmp_path / "broken.dat"
    dat_path.write_text(
        "\n".join(
            [
                "DISPLACEMENTS",
                "NODE U1 U2 U3",
                "1 0 0 0",
                "not-a-valid-row",
                "STRESSES",
                "ELEMENT SXX SYY SZZ SXY SYZ SXZ VON_MISES",
                "2 bad 0 0 0 0 0 10",
            ]
        ),
        encoding="utf-8",
    )

    dataset = parse_calculix_dat(dat_path)

    assert dataset.field("displacement").rows[0].entity_id == 1
    assert dataset.field("stress").rows == ()
    assert any("Could not parse displacement row" in warning for warning in dataset.warnings)
    assert any("Could not parse stress row" in warning for warning in dataset.warnings)


def test_result_dataset_serializes_and_builds_report_tables(tmp_path: Path) -> None:
    dat_path = tmp_path / "cantilever.dat"
    dat_path.write_text(VALID_DAT, encoding="utf-8")

    dataset = parse_calculix_dat(dat_path)
    payload = dataset.to_dict()
    tables = dataset.to_report_tables()

    assert payload["summaries"]["displacement_magnitude"]["value"] == 0.004
    assert payload["summaries"]["von_mises_stress"]["unit"] == "Pa"
    assert tables[0].title == "CalculiX displacement"
    assert tables[1].title == "CalculiX stress"

    model = build_report_model(
        project=_minimal_project(),
        result_tables=(dataset,),
    )

    assert any(table.title == "CalculiX displacement" for table in model.result_tables)
    assert any("calculix-result-1" in item for item in model.result_summary)


def test_parse_calculix_results_prefers_dat_and_reports_frd_stub(tmp_path: Path) -> None:
    dat_path = tmp_path / "cantilever.dat"
    frd_path = tmp_path / "cantilever.frd"
    dat_path.write_text(VALID_DAT, encoding="utf-8")
    frd_path.write_text("frd placeholder", encoding="utf-8")

    dataset = parse_calculix_results(dat_path=dat_path, frd_path=frd_path)

    assert dataset.source == str(dat_path)
    assert any("FRD parsing is not implemented" in warning for warning in dataset.warnings)


def test_frd_only_parse_is_explicit_stub(tmp_path: Path) -> None:
    frd_path = tmp_path / "cantilever.frd"
    frd_path.write_text("frd placeholder", encoding="utf-8")

    try:
        parse_calculix_results(frd_path=frd_path)
    except CalculixFrdParserUnavailable as exc:
        assert "FRD parsing is not implemented" in str(exc)
    else:
        raise AssertionError("FRD-only parse should be explicit about the stub.")


def test_pyvista_contour_placeholder_accepts_result_dataset(tmp_path: Path) -> None:
    dat_path = tmp_path / "cantilever.dat"
    dat_path.write_text(VALID_DAT, encoding="utf-8")
    dataset = parse_calculix_dat(dat_path)

    placeholder = build_result_contour_placeholder(
        dataset,
        scalar_field="displacement_magnitude",
    )

    assert placeholder.scalar_field == "displacement_magnitude"
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
