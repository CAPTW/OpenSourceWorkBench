from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.experimental import feaspec
from osw.experimental.feaspec import (
    FEASpec,
    FEASpecCandidate,
    FEASpecDiagnosticError,
    SpecType,
    ValidationState,
    check_feaspec_dict,
    dump_feaspec,
    load_feaspec,
    parse_feaspec_dict,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / "examples" / "feaspec"
SEED_ROOT = REPO_ROOT / "tests" / "fixtures" / "feaspec" / "benchmark_seeds"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_feaspec_package_imports_and_exports_public_api() -> None:
    assert feaspec.load_feaspec is load_feaspec
    assert feaspec.dump_feaspec is dump_feaspec
    assert feaspec.parse_feaspec_dict is parse_feaspec_dict
    assert feaspec.FEASpecCandidate is FEASpecCandidate
    assert feaspec.FEASpec is FEASpec


def test_candidate_example_loads_as_untrusted_candidate() -> None:
    spec = load_feaspec(EXAMPLES_DIR / "cantilever_beam_candidate.json")

    assert isinstance(spec, FEASpecCandidate)
    assert spec.spec_type is SpecType.CANDIDATE
    assert spec.validation.state is ValidationState.VALID_WITH_WARNINGS
    assert spec.is_candidate
    assert not spec.is_approved
    assert spec.approval_required_before_solver_case_generation is True


def test_approved_example_loads_as_approved_with_human_review() -> None:
    spec = load_feaspec(EXAMPLES_DIR / "cantilever_beam_approved.json")

    assert isinstance(spec, FEASpec)
    assert spec.spec_type is SpecType.APPROVED
    assert spec.validation.state is ValidationState.APPROVED
    assert spec.human_review is not None
    assert spec.human_review.action == "approved"
    assert spec.is_approved


def test_approved_spec_requires_human_review() -> None:
    payload = _load_json(EXAMPLES_DIR / "cantilever_beam_approved.json")
    payload.pop("human_review")

    with pytest.raises(FEASpecDiagnosticError) as exc_info:
        parse_feaspec_dict(payload)

    assert {diagnostic.code for diagnostic in exc_info.value.diagnostics} >= {
        "missing_human_review"
    }


def test_approved_spec_requires_approved_validation_state() -> None:
    payload = _load_json(EXAMPLES_DIR / "cantilever_beam_approved.json")
    payload["validation"]["state"] = "valid-with-warnings"

    with pytest.raises(FEASpecDiagnosticError) as exc_info:
        parse_feaspec_dict(payload)

    assert {diagnostic.code for diagnostic in exc_info.value.diagnostics} >= {
        "approved_requires_approved_state"
    }


def test_candidate_marked_approved_is_rejected() -> None:
    payload = _load_json(EXAMPLES_DIR / "cantilever_beam_candidate.json")
    payload["validation"]["state"] = "approved"

    with pytest.raises(FEASpecDiagnosticError) as exc_info:
        parse_feaspec_dict(payload)

    assert {diagnostic.code for diagnostic in exc_info.value.diagnostics} >= {
        "candidate_cannot_be_approved"
    }


def test_explicit_units_are_required() -> None:
    payload = _load_json(EXAMPLES_DIR / "cantilever_beam_candidate.json")
    payload.pop("units")

    with pytest.raises(FEASpecDiagnosticError) as exc_info:
        parse_feaspec_dict(payload)

    assert "missing_units" in {diagnostic.code for diagnostic in exc_info.value.diagnostics}


def test_geometry_node_ids_are_unique() -> None:
    payload = _load_json(EXAMPLES_DIR / "cantilever_beam_candidate.json")
    graph = payload["geometry"]["geometry_graph"]
    graph["nodes"].append(dict(graph["nodes"][0]))

    with pytest.raises(FEASpecDiagnosticError) as exc_info:
        parse_feaspec_dict(payload)

    assert "duplicate_geometry_id" in {
        diagnostic.code for diagnostic in exc_info.value.diagnostics
    }


def test_edge_endpoints_reference_known_nodes() -> None:
    payload = _load_json(EXAMPLES_DIR / "cantilever_beam_candidate.json")
    payload["geometry"]["geometry_graph"]["edges"][0]["node_refs"] = ["n_left", "n_missing"]

    with pytest.raises(FEASpecDiagnosticError) as exc_info:
        parse_feaspec_dict(payload)

    assert "invalid_edge_endpoint" in {
        diagnostic.code for diagnostic in exc_info.value.diagnostics
    }


@pytest.mark.parametrize(
    ("filename", "expected_code"),
    [
        ("invalid_missing_units.json", "missing_units"),
        ("invalid_unconnected_graph.json", "disconnected_graph"),
        ("invalid_load_target.json", "invalid_load_target"),
    ],
)
def test_invalid_examples_raise_expected_diagnostics(filename: str, expected_code: str) -> None:
    with pytest.raises(FEASpecDiagnosticError) as exc_info:
        load_feaspec(EXAMPLES_DIR / filename)

    codes = {diagnostic.code for diagnostic in exc_info.value.diagnostics}
    assert expected_code in codes

    invalid = load_feaspec(EXAMPLES_DIR / filename, allow_diagnostics=True)
    assert isinstance(invalid, FEASpecCandidate)
    assert not invalid.is_approved
    assert expected_code in {diagnostic.code for diagnostic in invalid.diagnostics}


def test_round_trip_json_preserves_key_fields(tmp_path: Path) -> None:
    source_path = EXAMPLES_DIR / "truss_2d_approved.json"
    spec = load_feaspec(source_path)
    output_path = tmp_path / "roundtrip.json"

    dump_feaspec(spec, output_path)
    round_tripped = load_feaspec(output_path)

    original = _load_json(source_path)
    restored = round_tripped.to_dict()
    for key in ("schema_version", "spec_type", "source", "units", "validation"):
        assert restored[key] == original[key]
    restored_nodes = restored["geometry"]["geometry_graph"]["nodes"]
    original_nodes = original["geometry"]["geometry_graph"]["nodes"]
    assert restored_nodes == original_nodes


def test_benchmark_seed_ground_truth_feaspec_files_load() -> None:
    seed_paths = sorted(SEED_ROOT.glob("*/ground_truth_feaspec.json"))
    assert seed_paths
    for seed_path in seed_paths:
        spec = load_feaspec(seed_path)
        assert isinstance(spec, FEASpec)
        assert spec.is_approved
        assert spec.human_review is not None


def test_benchmark_seed_metrics_remain_parseable() -> None:
    for metrics_path in sorted(SEED_ROOT.glob("*/expected_metrics.json")):
        metrics = _load_json(metrics_path)
        assert metrics["schema_validity_required"] is True
        assert metrics["required_validation_state"] == "approved"


def test_basic_checks_return_structured_diagnostics_without_raising() -> None:
    payload = _load_json(EXAMPLES_DIR / "invalid_load_target.json")

    diagnostics = check_feaspec_dict(payload)

    assert diagnostics
    assert all(diagnostic.severity for diagnostic in diagnostics)
    assert "invalid_load_target" in {diagnostic.code for diagnostic in diagnostics}
