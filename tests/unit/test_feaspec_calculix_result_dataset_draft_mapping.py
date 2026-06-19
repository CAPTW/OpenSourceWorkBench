from __future__ import annotations

import json
from pathlib import Path

from osw.experimental.feaspec import (
    FEASpecCalculiXResultDatasetDraftMapping,
    FEASpecCalculiXResultDatasetDraftSummary,
    FEASpecCalculiXResultDraftArtifact,
    FEASpecCalculiXResultDraftFieldReference,
    FEASpecCalculiXResultDraftLimitation,
    FEASpecCalculiXResultDraftProvenance,
    FEASpecCalculiXResultDraftScalar,
    FEASpecCalculiXResultDraftStatus,
    FEASpecCalculiXResultDraftTable,
    build_calculix_result_dataset_draft,
    build_calculix_result_dataset_draft_mapping,
    explain_calculix_result_dataset_draft_mapping,
    plan_calculix_result_import,
    summarize_calculix_result_dataset_draft_mapping,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_result_dir(root: Path) -> Path:
    root.mkdir()
    _write_json(
        root / "run_metadata.json",
        {
            "status": "ran",
            "solver_execution_performed": True,
            "exit_code": 0,
            "timed_out": False,
            "source_feaspec_id": "mapping_feaspec",
            "case_id": "mapping_case",
            "osw_version": "0.1.4rc1",
            "scalar_summaries": {"metadata_only": "preserved"},
        },
    )
    _write_json(
        root / "mapping_case.manifest.json",
        {
            "target_solver": "calculix",
            "source_feaspec_id": "mapping_feaspec",
            "case_id": "mapping_case",
            "release_tag": "v0.1.4-rc1",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "mapping_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("review first\n", encoding="utf-8")
    (root / "mapping_case.inp").write_text("*NODE\n", encoding="utf-8")
    (root / "mapping_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "mapping_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    (root / "mapping_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\n"
        "max displacement = 2.5 mm\n"
        "DISPLACEMENTS\n"
        "node | ux\n"
        "units | - | mm\n"
        "1 | 0.1\n",
        encoding="utf-8",
    )
    (root / "mapping_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    return root


def _mapping(root: Path) -> FEASpecCalculiXResultDatasetDraftMapping:
    return build_calculix_result_dataset_draft_mapping(
        plan_calculix_result_import(root)
    )


def test_draft_mapping_module_imports_and_exports_required_api() -> None:
    assert build_calculix_result_dataset_draft_mapping
    assert summarize_calculix_result_dataset_draft_mapping
    assert explain_calculix_result_dataset_draft_mapping
    assert FEASpecCalculiXResultDatasetDraftMapping
    assert FEASpecCalculiXResultDatasetDraftSummary
    assert FEASpecCalculiXResultDraftArtifact
    assert FEASpecCalculiXResultDraftScalar
    assert FEASpecCalculiXResultDraftTable
    assert FEASpecCalculiXResultDraftFieldReference
    assert FEASpecCalculiXResultDraftProvenance
    assert FEASpecCalculiXResultDraftLimitation
    assert FEASpecCalculiXResultDraftStatus


def test_empty_or_blocked_import_plan_produces_blocked_mapping(tmp_path: Path) -> None:
    plan = plan_calculix_result_import(tmp_path / "missing")

    mapping = build_calculix_result_dataset_draft_mapping(plan)

    assert mapping.status is FEASpecCalculiXResultDraftStatus.BLOCKED
    assert mapping.writes_files is False
    assert mapping.result_dataset_persistence is False


def test_artifact_metadata_maps_to_draft_artifacts_with_hash_and_size(
    tmp_path: Path,
) -> None:
    root = _write_result_dir(tmp_path / "result")

    mapping = _mapping(root)

    dat_artifact = next(item for item in mapping.artifacts if item.suffix == ".dat")
    assert dat_artifact.filename == "mapping_case.dat"
    assert dat_artifact.sha256
    assert dat_artifact.size_bytes > 0
    assert "result_parser" in dat_artifact.parser_summary_keys
    assert "dat_minimal_parse_summary" in dat_artifact.parser_summary_keys


def test_status_summaries_map_sta_and_cvg_text_counts(tmp_path: Path) -> None:
    mapping = _mapping(_write_result_dir(tmp_path / "result"))

    assert len(mapping.status_summaries) == 2
    counts = {}
    for summary in mapping.status_summaries:
        payload = summary["summary"]
        for key, value in payload["category_counts"].items():
            counts[key] = counts.get(key, 0) + value
    assert counts["progress"] == 1
    assert counts["completion"] == 1
    assert counts["convergence"] == 1


def test_dat_scalar_and_table_candidates_map_raw_and_parsed_values(
    tmp_path: Path,
) -> None:
    mapping = _mapping(_write_result_dir(tmp_path / "result"))

    assert len(mapping.scalar_candidates) == 1
    scalar = mapping.scalar_candidates[0]
    assert scalar.label == "max displacement"
    assert scalar.raw_value == "2.5"
    assert scalar.parsed_value == 2.5
    assert scalar.unit == "mm"
    assert scalar.line_number > 0

    assert len(mapping.table_candidates) == 1
    table = mapping.table_candidates[0]
    assert table.heading == "DISPLACEMENTS"
    assert table.raw_headers == ("node", "ux")
    assert table.raw_cells == (("1", "0.1"),)
    assert table.parsed_cells == ((None, 0.1),)
    assert table.unit_context["ux"] == "mm"


def test_units_are_preserved_and_not_inferred(tmp_path: Path) -> None:
    mapping = _mapping(_write_result_dir(tmp_path / "result"))
    payload = mapping.to_dict()

    assert mapping.units_inferred is False
    assert payload["units_inferred"] is False
    assert mapping.scalar_candidates[0].unit == "mm"
    assert mapping.table_candidates[0].unit_context == {"ux": "mm"}


def test_frd_reference_candidates_map_to_field_references_only(
    tmp_path: Path,
) -> None:
    mapping = _mapping(_write_result_dir(tmp_path / "result"))

    kinds = {item.reference_kind for item in mapping.field_references}
    assert {"node", "field"} <= kinds
    assert all(item.values_parsed is False for item in mapping.field_references)
    assert all(item.mesh_reconstructed is False for item in mapping.field_references)
    assert all(item.units_inferred is False for item in mapping.field_references)
    assert mapping.frd_numerical_field_parser is False
    assert mapping.mesh_reconstructed is False


def test_diagnostics_provenance_and_limitations_propagate(tmp_path: Path) -> None:
    mapping = _mapping(_write_result_dir(tmp_path / "result"))

    assert mapping.provenance is not None
    assert mapping.provenance.case_id == "mapping_case"
    assert mapping.provenance.source_feaspec_id == "mapping_feaspec"
    assert mapping.diagnostics
    assert any("ResultDataset persistence" in item.message for item in mapping.limitations)
    assert any("#8" in item.message for item in mapping.limitations)


def test_summary_counts_are_deterministic(tmp_path: Path) -> None:
    root = _write_result_dir(tmp_path / "result")
    first = summarize_calculix_result_dataset_draft_mapping(_mapping(root))
    second = summarize_calculix_result_dataset_draft_mapping(_mapping(root))

    assert first.to_dict() == second.to_dict()
    assert first.artifact_count >= 1
    assert first.status_summary_count == 2
    assert first.scalar_candidate_count == 1
    assert first.table_candidate_count == 1
    assert first.field_reference_count >= 2
    assert first.writes_files is False


def test_mapping_writes_no_files_and_does_not_parse_additional_content(
    tmp_path: Path,
) -> None:
    root = _write_result_dir(tmp_path / "result")
    before = sorted(path.name for path in root.iterdir())

    mapping = _mapping(root)
    after = sorted(path.name for path in root.iterdir())
    payload = mapping.to_dict()

    assert before == after
    assert mapping.writes_files is False
    assert mapping.result_dataset_persistence is False
    assert payload["frd_numerical_field_parser"] is False
    assert payload["mesh_reconstructed"] is False
    assert payload["engineering_correctness_claimed"] is False


def test_result_import_model_includes_draft_mapping_without_breaking_draft(
    tmp_path: Path,
) -> None:
    plan = plan_calculix_result_import(_write_result_dir(tmp_path / "result"))

    draft = build_calculix_result_dataset_draft(plan)
    payload = draft.to_dict()

    assert draft.writes_files is False
    assert payload["draft_mapping"]["writes_files"] is False
    assert payload["draft_mapping"]["scalar_candidates"]
    assert payload["draft_mapping"]["table_candidates"]
    assert payload["draft_mapping"]["field_references"]


def test_explain_draft_mapping_is_reviewer_readable(tmp_path: Path) -> None:
    lines = explain_calculix_result_dataset_draft_mapping(
        _mapping(_write_result_dir(tmp_path / "result"))
    )

    assert any("draft mapping status" in line.lower() for line in lines)
    assert any("resultdataset files written: false" in line.lower() for line in lines)
    assert any(
        "frd numerical field parser implemented: false" in line.lower()
        for line in lines
    )


def test_mapping_tests_use_tmp_path_not_tracked_result_fixtures() -> None:
    source = Path(__file__).read_text(encoding="utf-8")

    assert "tmp_path" in source
    assert "tests/" + "fixtures" not in source
    assert "fixtures/" + "calculix" not in source
