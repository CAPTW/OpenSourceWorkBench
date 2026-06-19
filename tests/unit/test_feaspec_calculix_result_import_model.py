from __future__ import annotations

import json
from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXResultArtifactKind,
    CalculiXResultImportDiagnosticCode,
    FEASpecCalculiXResultDatasetDraft,
    FEASpecCalculiXResultDirectoryInspection,
    FEASpecCalculiXResultImportPlan,
    FEASpecCalculiXResultImportStatus,
    build_calculix_result_dataset_draft,
    explain_calculix_result_import_plan,
    inspect_calculix_result_directory,
    plan_calculix_result_import,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_metadata_bundle(
    root: Path,
    *,
    solver_execution_performed: bool = True,
    timed_out: bool = False,
    exit_code: int | None = 0,
    primary_suffix: str | None = ".dat",
) -> Path:
    root.mkdir()
    _write_json(
        root / "run_metadata.json",
        {
            "status": "ran",
            "export_dir": str(root),
            "run_dir": str(root),
            "ccx_path": "ccx",
            "solver_execution_performed": solver_execution_performed,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "osw_version": "0.1.4rc1",
            "source_feaspec_id": "beam_candidate",
            "case_id": "beam_case",
            "scalar_summaries": {"source": "metadata-only"},
        },
    )
    _write_json(
        root / "beam_case.manifest.json",
        {
            "exporter_module": "osw.experimental.feaspec.calculix_exporter",
            "osw_version": "0.1.4rc1",
            "release_tag": "v0.1.4-rc1",
            "target_solver": "calculix",
            "source_feaspec_id": "beam_candidate",
            "case_id": "beam_case",
            "solver_execution_performed": False,
            "ready_for_solver_execution": False,
            "files": [],
        },
    )
    _write_json(root / "beam_case.diagnostics.json", {"status": "exported"})
    (root / "stdout.txt").write_text("stdout\n", encoding="utf-8")
    (root / "stderr.txt").write_text("stderr\n", encoding="utf-8")
    (root / "README_RUN_FIRST.txt").write_text("reviewed\n", encoding="utf-8")
    (root / "beam_case.inp").write_text("*NODE\n", encoding="utf-8")
    if primary_suffix is not None:
        (root / f"beam_case{primary_suffix}").write_text(
            "not parsed\n",
            encoding="utf-8",
        )
    return root


def _codes(
    plan_or_inspection: FEASpecCalculiXResultImportPlan
    | FEASpecCalculiXResultDirectoryInspection,
) -> set[CalculiXResultImportDiagnosticCode]:
    return {diagnostic.code for diagnostic in plan_or_inspection.diagnostics}


def _kinds(
    inspection: FEASpecCalculiXResultDirectoryInspection,
) -> set[CalculiXResultArtifactKind]:
    return {artifact.kind for artifact in inspection.artifacts}


def test_module_imports_and_public_api_exports_required_types() -> None:
    assert inspect_calculix_result_directory
    assert plan_calculix_result_import
    assert build_calculix_result_dataset_draft
    assert explain_calculix_result_import_plan
    assert FEASpecCalculiXResultDirectoryInspection
    assert FEASpecCalculiXResultImportPlan
    assert FEASpecCalculiXResultDatasetDraft


def test_missing_result_dir_is_blocked(tmp_path: Path) -> None:
    plan = plan_calculix_result_import(tmp_path / "missing")

    assert plan.status is FEASpecCalculiXResultImportStatus.BLOCKED
    assert CalculiXResultImportDiagnosticCode.FI_RESULT_DIR_MISSING in _codes(plan)


def test_file_path_instead_of_dir_is_blocked(tmp_path: Path) -> None:
    path = tmp_path / "result.dat"
    path.write_text("temporary test artifact\n", encoding="utf-8")

    plan = plan_calculix_result_import(path)

    assert plan.status is FEASpecCalculiXResultImportStatus.BLOCKED
    assert CalculiXResultImportDiagnosticCode.FI_RESULT_DIR_NOT_DIRECTORY in _codes(plan)


def test_empty_dir_reports_missing_metadata_and_primary_result(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()

    plan = plan_calculix_result_import(root)

    assert plan.status is FEASpecCalculiXResultImportStatus.UNSUPPORTED
    assert CalculiXResultImportDiagnosticCode.FI_RUN_METADATA_MISSING in _codes(plan)
    assert CalculiXResultImportDiagnosticCode.FI_EXPORT_MANIFEST_MISSING in _codes(plan)
    assert CalculiXResultImportDiagnosticCode.FI_NO_PRIMARY_RESULT in _codes(plan)


def test_run_metadata_only_is_inspected(tmp_path: Path) -> None:
    root = tmp_path / "metadata_only"
    root.mkdir()
    _write_json(
        root / "run_metadata.json",
        {
            "status": "ran",
            "solver_execution_performed": True,
            "exit_code": 0,
            "timed_out": False,
        },
    )

    inspection = inspect_calculix_result_directory(root)

    assert inspection.run_metadata_path == root / "run_metadata.json"
    assert inspection.run_metadata is not None
    assert CalculiXResultImportDiagnosticCode.FI_EXPORT_MANIFEST_MISSING in _codes(
        inspection
    )


def test_export_manifest_is_inspected(tmp_path: Path) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle")

    inspection = inspect_calculix_result_directory(root)

    assert inspection.export_manifest_path == root / "beam_case.manifest.json"
    assert inspection.export_manifest is not None


def test_stdout_stderr_are_classified(tmp_path: Path) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle")
    inspection = inspect_calculix_result_directory(root)

    assert CalculiXResultArtifactKind.STDOUT in _kinds(inspection)
    assert CalculiXResultArtifactKind.STDERR in _kinds(inspection)


def test_dat_frd_sta_and_cvg_are_classified_without_parsing(tmp_path: Path) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=None)
    for suffix in (".dat", ".frd", ".sta", ".cvg"):
        (root / f"beam_case{suffix}").write_text(
            f"{suffix} placeholder\n",
            encoding="utf-8",
        )

    inspection = inspect_calculix_result_directory(root)

    assert CalculiXResultArtifactKind.DAT in _kinds(inspection)
    assert CalculiXResultArtifactKind.FRD in _kinds(inspection)
    assert CalculiXResultArtifactKind.STA in _kinds(inspection)
    assert CalculiXResultArtifactKind.CVG in _kinds(inspection)
    assert CalculiXResultImportDiagnosticCode.FI_PARSE_NOT_IMPLEMENTED in _codes(
        inspection
    )


def test_sta_and_cvg_are_treated_as_primary_result_families(tmp_path: Path) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=None)
    (root / "beam_case.sta").write_text(
        "sta placeholder\n",
        encoding="utf-8",
    )
    (root / "beam_case.cvg").write_text(
        "cvg placeholder\n",
        encoding="utf-8",
    )

    plan = plan_calculix_result_import(root)

    assert plan.status is not FEASpecCalculiXResultImportStatus.UNSUPPORTED
    assert CalculiXResultArtifactKind.STA in {artifact.kind for artifact in plan.artifacts}
    assert CalculiXResultArtifactKind.CVG in {artifact.kind for artifact in plan.artifacts}
    assert plan.primary_artifacts


def test_unsupported_files_produce_warning(tmp_path: Path) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle")
    (root / "notes.tmp").write_text("unsupported\n", encoding="utf-8")

    plan = plan_calculix_result_import(root)

    assert CalculiXResultImportDiagnosticCode.FI_UNSUPPORTED_FILE in _codes(plan)


def test_run_metadata_solver_execution_false_produces_diagnostic(tmp_path: Path) -> None:
    root = _write_metadata_bundle(
        tmp_path / "bundle",
        solver_execution_performed=False,
    )

    plan = plan_calculix_result_import(root)

    assert CalculiXResultImportDiagnosticCode.FI_SOLVER_NOT_EXECUTED in _codes(plan)
    assert plan.status is FEASpecCalculiXResultImportStatus.PARTIAL


def test_run_metadata_timed_out_true_produces_diagnostic(tmp_path: Path) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", timed_out=True)

    plan = plan_calculix_result_import(root)

    assert CalculiXResultImportDiagnosticCode.FI_RUN_TIMED_OUT in _codes(plan)
    assert plan.status is FEASpecCalculiXResultImportStatus.PARTIAL


def test_run_metadata_nonzero_exit_produces_diagnostic(tmp_path: Path) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", exit_code=7)

    plan = plan_calculix_result_import(root)

    assert CalculiXResultImportDiagnosticCode.FI_RUN_FAILED in _codes(plan)
    assert plan.status is FEASpecCalculiXResultImportStatus.PARTIAL


def test_complete_metadata_with_primary_artifact_is_import_ready_with_warnings(
    tmp_path: Path,
) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=".frd")

    plan = plan_calculix_result_import(root)

    assert plan.status is FEASpecCalculiXResultImportStatus.IMPORT_READY_WITH_WARNINGS
    assert CalculiXResultImportDiagnosticCode.FI_PARSE_NOT_IMPLEMENTED in _codes(plan)
    assert plan.provenance.case_id == "beam_case"


def test_build_result_dataset_draft_contains_artifacts_provenance_limitations_and_diagnostics(
    tmp_path: Path,
) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=".frd")
    before = sorted(path.name for path in root.iterdir())

    plan = plan_calculix_result_import(root)
    draft = build_calculix_result_dataset_draft(plan)
    after = sorted(path.name for path in root.iterdir())

    assert before == after
    assert draft.writes_files is False
    assert draft.artifacts
    assert draft.provenance is not None
    assert draft.limitations
    assert draft.diagnostics
    assert draft.scalar_summaries == {"source": "metadata-only"}
    assert draft.field_references
    payload = draft.to_dict()
    assert payload["writes_files"] is False
    assert payload["artifacts"]


def test_build_result_dataset_draft_includes_deferred_frd_references(
    tmp_path: Path,
) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=None)
    (root / "beam_case.frd").write_text(
        "2C NODE COORDINATES\n1 0 0 0\n100C DISPLACEMENT FIELD\n1 1.0\n",
        encoding="utf-8",
    )

    plan = plan_calculix_result_import(root)
    draft = build_calculix_result_dataset_draft(plan)

    assert draft.writes_files is False
    assert draft.field_references
    assert {item["reference_kind"] for item in draft.field_references} >= {
        "node",
        "field",
    }
    assert all(item["status"] == "candidate-not-parsed" for item in draft.field_references)


def test_build_result_dataset_draft_includes_dat_minimal_candidates(
    tmp_path: Path,
) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=None)
    (root / "beam_case.dat").write_text(
        "TOTAL ENERGY SUMMARY\nmax displacement = 2.5 mm\n"
        "DISPLACEMENTS\nnode | ux\nunits | - | mm\n1 | 0.1\n",
        encoding="utf-8",
    )

    plan = plan_calculix_result_import(root)
    draft = build_calculix_result_dataset_draft(plan)
    payload = draft.to_dict()

    assert draft.writes_files is False
    assert "dat_minimal_candidates" in draft.scalar_summaries
    assert draft.scalar_summaries["dat_minimal_candidates"][0]["label"] == (
        "max displacement"
    )
    assert draft.tables
    assert payload["tables"][0]["section_heading"] == "DISPLACEMENTS"


def test_inspect_includes_metadata_scanner_snapshot(tmp_path: Path) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=".frd")
    before = sorted(path.name for path in root.iterdir())

    inspection = inspect_calculix_result_directory(root)
    artifact = next(
        item for item in inspection.artifacts if item.kind is CalculiXResultArtifactKind.FRD
    )
    parser_metadata = artifact.metadata["result_parser"]

    assert parser_metadata["artifact_kind"] == "frd"
    assert parser_metadata["byte_size"] == artifact.size_bytes
    assert parser_metadata["sha256"] == artifact.sha256
    assert parser_metadata["parse_not_implemented"] is True
    assert parser_metadata["parser_phase"] == "metadata-only"
    assert "first_line_snippets" in parser_metadata
    assert "last_line_snippets" in parser_metadata

    after = sorted(path.name for path in root.iterdir())
    assert before == after


def test_inspect_includes_frd_block_summary_for_frd_artifacts(
    tmp_path: Path,
) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=None)
    (root / "beam_case.frd").write_text(
        "1C FRD HEADER\n"
        "2C NODE COORDINATES\n"
        "1 0 0 0\n"
        "100C DISPLACEMENT FIELD\n"
        "1 1.0\n",
        encoding="utf-8",
    )
    before = sorted(path.name for path in root.iterdir())

    inspection = inspect_calculix_result_directory(root)
    frd_artifact = next(
        artifact
        for artifact in inspection.artifacts
        if artifact.kind is CalculiXResultArtifactKind.FRD
    )
    after = sorted(path.name for path in root.iterdir())

    assert before == after
    assert "frd_block_summary" in frd_artifact.metadata
    assert "frd_block_scan" in frd_artifact.metadata
    assert frd_artifact.metadata["frd_block_summary"]["block_count"] == 3
    assert frd_artifact.metadata["frd_block_summary"]["field_reference_candidate_count"] == 1
    assert frd_artifact.metadata["frd_block_summary"]["mesh_reference_candidate_count"] == 1
    assert frd_artifact.metadata["frd_block_summary"]["numeric_tokens_not_parsed"]


def test_inspect_includes_status_summary_for_sta_cvg_artifacts(
    tmp_path: Path,
) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=None)
    (root / "beam_case.sta").write_text(
        "step 1 increment 2\nanalysis completed\n",
        encoding="utf-8",
    )
    (root / "beam_case.cvg").write_text(
        "convergence residual 1.0E-03\n",
        encoding="utf-8",
    )
    before = sorted(path.name for path in root.iterdir())

    inspection = inspect_calculix_result_directory(root)
    status_artifacts = [
        artifact
        for artifact in inspection.artifacts
        if artifact.kind in {CalculiXResultArtifactKind.STA, CalculiXResultArtifactKind.CVG}
    ]
    after = sorted(path.name for path in root.iterdir())

    assert before == after
    assert len(status_artifacts) == 2
    assert all("status_summary" in artifact.metadata for artifact in status_artifacts)
    assert all("status_scan" in artifact.metadata for artifact in status_artifacts)
    assert any(
        artifact.metadata["status_summary"]["numeric_tokens_not_parsed"]
        for artifact in status_artifacts
    )


def test_inspect_includes_dat_section_summary_for_dat_artifacts(
    tmp_path: Path,
) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=None)
    (root / "beam_case.dat").write_text(
        "CalculiX result file\nTOTAL ENERGY SUMMARY\nenergy text 1.0\n",
        encoding="utf-8",
    )
    before = sorted(path.name for path in root.iterdir())

    inspection = inspect_calculix_result_directory(root)
    dat_artifact = next(
        artifact
        for artifact in inspection.artifacts
        if artifact.kind is CalculiXResultArtifactKind.DAT
    )
    after = sorted(path.name for path in root.iterdir())

    assert before == after
    assert "dat_section_summary" in dat_artifact.metadata
    assert "dat_section_scan" in dat_artifact.metadata
    assert "dat_minimal_parse" in dat_artifact.metadata
    assert "dat_minimal_parse_summary" in dat_artifact.metadata
    assert dat_artifact.metadata["dat_section_summary"]["section_count"] == 2
    assert dat_artifact.metadata["dat_section_summary"]["numeric_tokens_not_parsed"]
    assert dat_artifact.metadata["dat_minimal_parse_summary"]["minimal_parser"] is True


def test_explain_result_import_plan_is_reviewer_readable(tmp_path: Path) -> None:
    root = _write_metadata_bundle(tmp_path / "bundle", primary_suffix=".dat")

    plan = plan_calculix_result_import(root)
    lines = explain_calculix_result_import_plan(plan)

    assert any("result import status" in line.lower() for line in lines)
    assert any(
        "broad numerical result parser implemented: false" in line.lower()
        for line in lines
    )
    assert any("minimal .dat parser available: true" in line.lower() for line in lines)
