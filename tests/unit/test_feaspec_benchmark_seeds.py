from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_ROOT = REPO_ROOT / "tests" / "fixtures" / "feaspec" / "benchmark_seeds"
REQUIRED_FILES = {
    "prompt.txt",
    "source_metadata.json",
    "ground_truth_feaspec.json",
    "expected_metrics.json",
    "README.md",
}
REQUIRED_METRIC_FIELDS = {
    "schema_validity_required",
    "required_validation_state",
    "node_count",
    "edge_count",
    "bc_count",
    "load_count",
    "material_count",
    "dimension_count",
    "solver_compatibility_expected",
    "detection_metrics_later",
}
REQUIRED_DETECTION_METRICS = {
    "node_precision",
    "node_recall",
    "connectivity_f1",
    "bc_accuracy",
    "load_accuracy",
    "dimension_accuracy",
}


def _seed_dirs() -> list[Path]:
    return sorted(path for path in SEED_ROOT.iterdir() if path.is_dir())


def _load_json(path: Path) -> dict[str, Any]:
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


def test_benchmark_seed_directory_exists() -> None:
    assert SEED_ROOT.exists()


def test_at_least_six_seed_folders_exist() -> None:
    assert len(_seed_dirs()) >= 6


def test_each_seed_has_required_files() -> None:
    for seed_dir in _seed_dirs():
        assert REQUIRED_FILES <= {path.name for path in seed_dir.iterdir()}


def test_each_ground_truth_feaspec_parses_and_is_approved() -> None:
    for seed_dir in _seed_dirs():
        data = _load_json(seed_dir / "ground_truth_feaspec.json")
        assert data["spec_type"] == "approved"
        assert data["validation"]["state"] == "approved"
        assert data["human_review"]["action"] == "approved"


def test_expected_metrics_have_required_counts_and_detection_metrics() -> None:
    for seed_dir in _seed_dirs():
        metrics = _load_json(seed_dir / "expected_metrics.json")
        assert REQUIRED_METRIC_FIELDS <= set(metrics)
        assert metrics["schema_validity_required"] is True
        assert metrics["required_validation_state"] == "approved"
        assert REQUIRED_DETECTION_METRICS <= set(metrics["detection_metrics_later"])


def test_expected_metric_counts_match_ground_truth_counts() -> None:
    for seed_dir in _seed_dirs():
        spec = _load_json(seed_dir / "ground_truth_feaspec.json")
        metrics = _load_json(seed_dir / "expected_metrics.json")
        graph = spec["geometry"]["geometry_graph"]
        assert metrics["node_count"] == len(graph["nodes"])
        assert metrics["edge_count"] == len(graph["edges"])
        assert metrics["bc_count"] == len(spec["boundary_conditions"])
        assert metrics["load_count"] == len(spec["loads"])
        assert metrics["material_count"] == len(spec["materials"])
        assert metrics["dimension_count"] == len(spec["dimensions"])


def test_source_metadata_declares_synthetic_drawing_placeholder() -> None:
    for seed_dir in _seed_dirs():
        metadata = _load_json(seed_dir / "source_metadata.json")
        assert metadata["source_type"] == "synthetic_drawing_placeholder"
        assert metadata["image_file"] is None
        assert "No image generated in this gate" in metadata["note"]


def test_seed_solver_compatibility_is_planned_and_abaqus_non_default() -> None:
    for seed_dir in _seed_dirs():
        metrics = _load_json(seed_dir / "expected_metrics.json")
        compatibility = metrics["solver_compatibility_expected"]
        assert compatibility["calculix"] == "planned"
        assert compatibility["abaqus"] == "optional_non_default"


def test_no_seed_claims_real_image_vlm_or_solver_execution() -> None:
    forbidden_fragments = (
        "real image generated",
        "vlm was run",
        "vlm api integration exists",
        "solver was run",
        "solver has been run",
        "solver_execution_result",
        "abaqus_required",
        "requires abaqus",
        "abaqus is required",
    )
    for seed_dir in _seed_dirs():
        texts = []
        for path in seed_dir.iterdir():
            if path.suffix == ".json":
                texts.extend(_strings(_load_json(path)))
            else:
                texts.append(path.read_text(encoding="utf-8"))
        text = "\n".join(texts).lower()
        for fragment in forbidden_fragments:
            assert fragment not in text
