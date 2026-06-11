from __future__ import annotations

import shutil
from pathlib import Path

from osw.experimental.feaspec import DiagnosticCode, validate_benchmark_seed

REPO_ROOT = Path(__file__).resolve().parents[2]
SEEDS = REPO_ROOT / "tests" / "fixtures" / "feaspec" / "benchmark_seeds"


def test_validate_benchmark_seed_loads_each_seed_folder() -> None:
    seed_dirs = sorted(path for path in SEEDS.iterdir() if path.is_dir())
    assert seed_dirs
    for seed_dir in seed_dirs:
        report = validate_benchmark_seed(seed_dir)
        assert report.is_valid
        assert not report.has_blockers
        assert report.benchmark_seed == seed_dir.name


def test_benchmark_seed_missing_expected_metrics_is_reported(tmp_path: Path) -> None:
    source = SEEDS / "cantilever_001"
    seed = tmp_path / "cantilever_missing_metrics"
    shutil.copytree(source, seed)
    (seed / "expected_metrics.json").unlink()

    report = validate_benchmark_seed(seed)

    assert DiagnosticCode.FS_BENCHMARK_METADATA_MISSING in report.diagnostic_codes
    assert report.has_errors
