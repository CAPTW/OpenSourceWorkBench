from __future__ import annotations

import json
from pathlib import Path

from osw.experimental.optional_solvers import (
    OptionalSolverManifestSourceType,
    OptionalSolverManifestTrustLabel,
    load_optional_solver_plugin_manifest_json,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "optional_solvers" / "plugin_manifests"


def _codes(report: object) -> set[str]:
    return {
        diagnostic.code
        for diagnostic in report.diagnostics
        if diagnostic.is_blocking
    }


def test_load_valid_manifest_from_json_file() -> None:
    report = load_optional_solver_plugin_manifest_json(
        FIXTURES / "valid_project_local_manifest.json"
    )

    assert len(report.accepted_manifests) == 1
    assert not report.rejected_manifests
    loaded = report.accepted_manifests[0]
    assert loaded.stack_id == "project_local_stack"
    assert loaded.source.source_type == OptionalSolverManifestSourceType.PROJECT_LOCAL
    assert loaded.source.trust_label == OptionalSolverManifestTrustLabel.REVIEWED_PROJECT


def test_fixture_files_parse_as_json() -> None:
    for fixture in FIXTURES.glob("*.json"):
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)


def test_network_urls_are_rejected_without_fetching() -> None:
    report = load_optional_solver_plugin_manifest_json(
        "https://example.invalid/optional_solver.json"
    )

    assert not report.accepted_manifests
    assert "OSPL_NETWORK_SOURCE_UNSUPPORTED" in _codes(report)


def test_directory_scanning_is_not_implemented(tmp_path: Path) -> None:
    report = load_optional_solver_plugin_manifest_json(tmp_path)

    assert not report.accepted_manifests
    assert "OSPL_DIRECTORY_SCAN_FORBIDDEN" in _codes(report)


def test_non_json_explicit_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "manifest.txt"
    path.write_text("{}", encoding="utf-8")

    report = load_optional_solver_plugin_manifest_json(path)

    assert not report.accepted_manifests
    assert "OSPL_JSON_EXTENSION_REQUIRED" in _codes(report)
