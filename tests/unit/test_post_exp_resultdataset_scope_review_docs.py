from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "roadmap" / "post_exp_resultdataset_scope_review.md"


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_scope_review_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_status_and_release_context_are_recorded() -> None:
    text = _normalized()

    assert "completed-with-open-validation" in text
    assert "public release: `v0.1.4-rc1`" in text
    assert "`develop` is newer than the public release tag" in text
    assert "version metadata still reports `0.1.4rc1`" in text


def test_completed_feaspec_resultdataset_scope_is_listed() -> None:
    text = _normalized()

    assert "completed feaspec/resultdataset scope" in text
    assert "feaspec models" in text
    assert "validator reports" in text
    assert "feaspec-to-projectschema bridge" in text
    assert "calculix case planning" in text
    assert "installed-only calculix run gate implementation" in text
    assert "result import model and preview cli" in text
    assert "resultdataset draft mapping" in text
    assert "result import write cli" in text
    assert "resultdataset write gui closure" in text


def test_live_calculix_validation_status_is_skipped_missing() -> None:
    text = _normalized()

    assert "osw-valid-004_live_calculix_run_gate_validation_if_installed" in text
    assert "result: `skipped-missing`" in text
    assert "calculix `ccx` was not discovered" in text
    assert "no installed-only run gate was executed" in text
    assert "no solver execution occurred" in text
    assert "issue `#8` remains open" in text


def test_open_optional_validation_issues_are_listed() -> None:
    text = _normalized()

    assert "issues `#6` through `#11` remain" in text
    assert "`#6` gmsh" in text
    assert "`#7` gnu octave" in text
    assert "`#8` calculix `ccx`" in text
    assert "`#9` openfoam" in text
    assert "`#10` coolprop / cantera" in text
    assert "`#11` pyvista / meshio" in text


def test_safety_and_release_boundary_are_explicit() -> None:
    text = _normalized()

    assert "no bundled solvers" in text
    assert "no certification claims" in text
    assert "no release mutation" in text
    assert "future release-boundary decision is required" in text
    assert "before publishing any new release assets" in text


def test_recommended_next_paths_are_recorded() -> None:
    text = _read()

    assert "OSW-PLAN-008_POST_EXP_RELEASE_BOUNDARY_DECISION" in text
    assert "OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED" in text
    assert "prepared machine with `ccx` already installed" in text
    assert "Future parser or visualization extensions only through separate" in text


def test_doc_does_not_claim_forbidden_state() -> None:
    text = _normalized()
    forbidden_claims = (
        "issue `#8` can close",
        "issue #8 can close",
        "live calculix validation passed",
        "live validation passed",
        "new release assets are ready",
        "industrial certification is provided",
        "solvers are bundled",
        "metadata is aligned for a new release version",
    )

    for claim in forbidden_claims:
        assert claim not in text
