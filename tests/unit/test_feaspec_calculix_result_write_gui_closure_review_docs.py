from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_calculix_result_write_gui_closure_review.md"
)


def _read() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_closure_review_doc_exists() -> None:
    assert DOC_PATH.exists()


def test_status_preserves_gui_write_and_no_run_boundary() -> None:
    text = _normalized()

    assert (
        "gui write flow implemented for experimental resultdataset "
        "review-file persistence"
    ) in text
    assert "no solver execution" in text
    assert "no live `ccx` validation" in text


def test_completed_scope_and_user_workflow_are_recorded() -> None:
    text = _normalized()

    assert "completed scope" in text
    assert "write cli" in text
    assert "library resultdataset writer" in text
    assert "gui view-model" in text
    assert "output-directory chooser" in text
    assert "gui writer integration" in text
    assert "post-write polish" in text
    assert "user workflow" in text
    assert "choose an explicit output directory" in text
    assert "acknowledge parser/import limitations" in text
    assert "review written files and sha-256 hashes" in text


def test_safety_boundaries_and_validation_evidence_are_recorded() -> None:
    text = _normalized()

    assert "safety boundaries" in text
    assert "no calculix `ccx` invocation" in text
    assert "no solveradapter" in text
    assert "no runner" in text
    assert "no subprocess" in text
    assert "no artifact copying" in text
    assert "no projectschema mutation" in text
    assert "validation evidence" in text
    assert "focused cli write tests" in text
    assert "focused gui" in text
    assert "full unit suite" in text
    assert "qa guardrails" in text


def test_known_warnings_are_explicit() -> None:
    text = _normalized()

    assert "known warnings" in text
    assert "gui aggregate timeout is a known warning" in text
    assert "per-file gui fallback passes" in text
    assert "release remains prerelease" in text
    assert "external solvers are not bundled" in text


def test_issue_8_separation_and_closure_decision_are_recorded() -> None:
    text = _normalized()

    assert "relationship to #8" in text
    assert "gui write is not live calculix validation" in text
    assert "issue `#8` remains open" in text
    assert "does not validate live `ccx`" in text
    assert "closure decision" in text
    assert "resultdataset write gui experimental slice complete" in text


def test_next_recommended_actions_are_recorded() -> None:
    text = _read()

    assert "OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED" in text
    assert "OSW-PLAN-007_POST_EXP_RESULTDATASET_SCOPE_REVIEW" in text
    assert "optional release-boundary planning gate" in text


def test_doc_does_not_claim_forbidden_capabilities() -> None:
    text = _normalized()
    forbidden_claims = (
        "issue `#8` can close",
        "issue #8 can close",
        "solver execution is part of gui write",
        "external solvers are bundled",
        "solver is bundled",
        "industrial certification is provided",
        "live `ccx` validation passed",
        "live validation passed",
    )

    for claim in forbidden_claims:
        assert claim not in text
