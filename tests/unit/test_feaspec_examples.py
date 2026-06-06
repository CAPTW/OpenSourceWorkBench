from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / "examples" / "feaspec"

REQUIRED_EXAMPLES = {
    "cantilever_beam_candidate.json",
    "cantilever_beam_approved.json",
    "truss_2d_candidate.json",
    "truss_2d_approved.json",
    "plate_with_hole_candidate.json",
    "invalid_missing_units.json",
    "invalid_unconnected_graph.json",
    "invalid_load_target.json",
}

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "spec_type",
    "source",
    "problem_type",
    "units",
    "geometry",
    "materials",
    "sections",
    "boundary_conditions",
    "loads",
    "dimensions",
    "assumptions",
    "evidence",
    "confidence",
    "diagnostics",
    "validation",
    "solver_compatibility",
}


def _json_files() -> list[Path]:
    return sorted(EXAMPLES_DIR.glob("*.json"))


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def test_feaspec_examples_directory_exists() -> None:
    assert EXAMPLES_DIR.exists()


def test_required_feaspec_example_files_exist() -> None:
    assert REQUIRED_EXAMPLES <= {path.name for path in _json_files()}


def test_every_example_json_file_parses() -> None:
    assert _json_files()
    for path in _json_files():
        assert isinstance(_load(path), dict)


def test_every_example_has_required_design_fields() -> None:
    for path in _json_files():
        data = _load(path)
        assert REQUIRED_TOP_LEVEL_FIELDS <= set(data)


def test_valid_candidate_examples_have_candidate_spec_type() -> None:
    candidate_files = [
        path
        for path in _json_files()
        if "candidate" in path.name and not path.name.startswith("invalid_")
    ]
    assert candidate_files
    for path in candidate_files:
        data = _load(path)
        assert data["spec_type"] == "candidate"
        assert data["validation"]["state"] != "approved"
        assert data["validation"]["review_required"] is True


def test_approved_examples_have_human_review_and_approved_state() -> None:
    approved_files = [path for path in _json_files() if "approved" in path.name]
    assert approved_files
    for path in approved_files:
        data = _load(path)
        assert data["spec_type"] == "approved"
        assert data["validation"]["state"] == "approved"
        assert data["human_review"]["action"] == "approved"
        assert data["validation"]["approval_required_before_solver_case_generation"] is True


def test_every_example_has_explicit_units_and_evidence_confidence() -> None:
    for path in _json_files():
        data = _load(path)
        assert data["units"]["system"]
        assert data["units"]["length"]
        assert data["evidence"]
        assert isinstance(data["confidence"], dict)


def test_invalid_examples_are_named_invalid_and_not_approved() -> None:
    invalid_files = [path for path in _json_files() if path.name.startswith("invalid_")]
    assert len(invalid_files) == 3
    for path in invalid_files:
        data = _load(path)
        assert data["spec_type"] != "approved"
        assert data["validation"]["state"] == "invalid"
        assert data["expected_diagnostics"]


def test_examples_do_not_claim_solver_or_vlm_execution_results() -> None:
    forbidden_fragments = (
        "solver_execution_result",
        "solver was run",
        "solver has been run",
        "vlm api integration exists",
        "vlm was run",
        "openai_api_key",
        "anthropic_api_key",
        "gemini_api_key",
    )
    for path in _json_files():
        text = "\n".join(_strings(_load(path))).lower()
        for fragment in forbidden_fragments:
            assert fragment not in text


def test_examples_do_not_require_abaqus() -> None:
    for path in _json_files():
        data = _load(path)
        abaqus = data["solver_compatibility"]["abaqus"]
        assert abaqus["state"] == "optional_non_default"
        text = "\n".join(_strings(data)).lower()
        assert "requires abaqus" not in text
        assert "abaqus is required" not in text
